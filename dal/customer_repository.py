# dal/customer_repository.py
"""
Repository cho Customer Booking Flow.
Xử lý: Query flights, seat map, tạo ticket, tra cứu, hủy vé, thanh toán.
"""
import uuid
from mysql.connector import Error
from config.database import DatabaseConnection
from typing import Dict, List, Tuple, Optional

class CustomerBookingRepository:
    def get_active_flights(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.base_price,
                       a1.city as dep_city, a2.city as arr_city,
                       (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id AND s.seat_status = 'AVAILABLE') as available_seats,
                       (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id) as total_seats
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                WHERE f.status = 'PENDING' AND f.departure_time > NOW()
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_flight_seat_map(self, flight_id: int) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT s.seat_id, s.seat_number, s.seat_status, sc.class_name, sc.price_multiplier
                FROM Seats s
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s
                ORDER BY s.seat_number ASC
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create_group_booking(self, flight_id: int, contact_info: Dict, passengers: List[Dict], is_hold: bool) -> Tuple[bool, str]:
        """Tạo Group Booking với Transaction chặt chẽ cho cả khách lẻ và khách đoàn"""
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            # Tạo Group Code và Insert bảng BookingGroups
            group_code = f"GRP-{uuid.uuid4().hex[:6].upper()}"
            cursor.execute("""
                INSERT INTO BookingGroups (group_code, contact_name, contact_phone, contact_email, total_members)
                VALUES (%s, %s, %s, %s, %s)
            """, (group_code, contact_info['name'], contact_info['phone'], contact_info.get('email', ''), len(passengers)))
            group_id = cursor.lastrowid

            ticket_status = 'HELD' if is_hold else 'BOOKED'
            first_pnr = ""

            # Xử lý từng hành khách
            for idx, p in enumerate(passengers):
                # Upsert Customer
                cursor.execute("SELECT customer_id FROM Customers WHERE phone = %s AND id_card = %s", (p['phone'], p['id_card']))
                cust = cursor.fetchone()
                if cust:
                    c_id = cust['customer_id']
                else:
                    cursor.execute("INSERT INTO Customers (full_name, phone, id_card) VALUES (%s, %s, %s)", 
                                   (p['name'], p['phone'], p['id_card']))
                    c_id = cursor.lastrowid

                # Khóa ghế an toàn chống đụng độ
                cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (p['seat_id'],))
                seat = cursor.fetchone()
                if not seat or seat['seat_status'] != 'AVAILABLE':
                    conn.rollback()
                    return False, f"Ghế {p['seat_number']} vừa có người nhanh tay đặt trước. Vui lòng chọn ghế khác cho đoàn!"

                # Sinh mã vé PNR tự động
                ticket_code = f"PNR-{uuid.uuid4().hex[:6].upper()}"
                if idx == 0: first_pnr = ticket_code # Giữ lại mã PNR đầu tiên để show cho khách
                
                cursor.execute("""
                    INSERT INTO Tickets (ticket_code, flight_id, customer_id, group_id, seat_id, base_price, final_price, status, voucher_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (ticket_code, flight_id, c_id, group_id, p['seat_id'], p['base_price'], p['final_price'], ticket_status, p.get('voucher_id')))

                # Cập nhật trạng thái ghế
                if is_hold:
                    cursor.execute("UPDATE Seats SET seat_status = 'HELD', hold_expired_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE seat_id = %s", (p['seat_id'],))
                else:
                    cursor.execute("UPDATE Seats SET seat_status = 'BOOKED', is_booked = TRUE WHERE seat_id = %s", (p['seat_id'],))

            # 3. Tăng count voucher nếu có dùng
            if passengers[0].get('voucher_id'):
                cursor.execute("UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = %s", (passengers[0]['voucher_id'],))

            conn.commit()
            return True, f"{group_code}|{first_pnr}"
            
        except Error as e:
            conn.rollback()
            return False, f"Lỗi hệ thống CSDL: {e}"
        finally:
            if conn: conn.close()

    # Các hàm cơ bản
    def lookup_strict(self, ticket_code: str, phone: str) -> Optional[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.ticket_id, t.ticket_code, t.final_price, t.status as ticket_status, t.created_at,
                       c.full_name, c.phone, c.id_card,
                       f.flight_number, f.departure_time, f.arrival_time, a1.city as dep_city, a2.city as arr_city,
                       s.seat_number, sc.class_name
                FROM Tickets t
                JOIN Customers c ON t.customer_id = c.customer_id
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE t.ticket_code = %s AND c.phone = %s
            """
            cursor.execute(query, (ticket_code, phone))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def cancel_ticket_strict(self, ticket_code: str, phone: str) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.ticket_id, t.seat_id, t.status, t.payment_id
                FROM Tickets t 
                JOIN Customers c ON t.customer_id = c.customer_id 
                WHERE t.ticket_code = %s AND c.phone = %s FOR UPDATE
            """, (ticket_code, phone))
            ticket = cursor.fetchone()
            
            if not ticket:
                conn.rollback()
                return False, "Thông tin xác thực không khớp hoặc vé không tồn tại của bạn."
            if ticket['status'] == 'CANCELLED':
                conn.rollback()
                return False, "Vé này đã được hủy từ trước."

            cursor.execute("UPDATE Tickets SET status = 'CANCELLED' WHERE ticket_id = %s", (ticket['ticket_id'],))
            cursor.execute("UPDATE Seats SET seat_status = 'AVAILABLE', is_booked = FALSE, hold_expired_at = NULL WHERE seat_id = %s", (ticket['seat_id'],))
            if ticket['payment_id']:
                cursor.execute("UPDATE Payments SET status = 'REFUNDED' WHERE payment_id = %s", (ticket['payment_id'],))

            conn.commit()
            return True, "Hủy vé thành công. Chỗ ngồi đã được hoàn trả hệ thống."
        except Error as e:
            conn.rollback()
            return False, f"Lỗi hệ thống: {e}"
        finally:
            if conn: conn.close()

    def pay_held_ticket(self, ticket_code: str, amount: float, method: str = 'VNPAY') -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.ticket_id, t.seat_id, t.final_price, t.status 
                FROM Tickets t WHERE t.ticket_code = %s FOR UPDATE
            """, (ticket_code,))
            ticket = cursor.fetchone()
            
            if not ticket:
                conn.rollback()
                return False, "Không tìm thấy vé."
            if ticket['status'] != 'HELD':
                conn.rollback()
                return False, f"Vé này không ở trạng thái HELD (hiện tại: {ticket['status']})."
            
            transaction_code = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            cursor.execute("""
                INSERT INTO Payments (method, amount, status, transaction_code)
                VALUES (%s, %s, %s, %s)
            """, (method, amount, 'COMPLETED', transaction_code))
            payment_id = cursor.lastrowid
            
            cursor.execute("""
                UPDATE Tickets SET payment_id = %s, status = 'BOOKED'
                WHERE ticket_id = %s
            """, (payment_id, ticket['ticket_id']))
            cursor.execute("""
                UPDATE Seats SET seat_status = 'BOOKED', is_booked = TRUE, hold_expired_at = NULL
                WHERE seat_id = %s
            """, (ticket['seat_id'],))
            
            conn.commit()
            return True, f"Thanh toán thành công. Transaction ID: {transaction_code}"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi thanh toán: {e}"
        finally:
            if conn: conn.close()

    def get_voucher(self, code: str) -> Optional[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT voucher_id, code, discount_percent, max_discount, usage_limit, used_count, expiry_date
                FROM Vouchers
                WHERE UPPER(code) = UPPER(%s) AND is_active = TRUE AND expiry_date > NOW() AND used_count < usage_limit
            """, (code,))
            return cursor.fetchone()
        finally:
            if conn: conn.close()