# dal/booking_repositories.py
from mysql.connector import Error
from config.database import DatabaseConnection
from typing import Dict, List, Tuple, Optional
import uuid

class CustomerRepository:
    def get_or_create(self, full_name: str, phone: str, id_card: str, email: str = "") -> int:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            # Tối ưu hóa: Tìm khách hàng khớp cả SĐT và CCCD. Không dùng OR để tránh nhận nhầm người
            cursor.execute("SELECT customer_id FROM Customers WHERE phone = %s AND id_card = %s", (phone, id_card))
            res = cursor.fetchone()
            if res: return res['customer_id']
            
            # Nếu khách mới, chèn vào vô tư vì đã bỏ ràng buộc UNIQUE trong Database
            cursor.execute("INSERT INTO Customers (full_name, phone, id_card, email) VALUES (%s, %s, %s, %s)", 
                           (full_name, phone, id_card, email))
            conn.commit()
            return cursor.lastrowid
        finally:
            if conn: conn.close()

    def search_customer_info_and_history(self, keyword: str) -> Tuple[Optional[Dict], List[Dict]]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            kw = f"%{keyword.lower()}%"
            query = """
                SELECT * FROM Customers
                WHERE CAST(customer_id AS CHAR) LIKE %s OR LOWER(full_name) LIKE %s
                   OR phone LIKE %s OR LOWER(email) LIKE %s OR id_card LIKE %s
            """
            cursor.execute(query, (kw, kw, kw, kw, kw))
            customers = cursor.fetchall()
            if not customers: return None, []
            
            customer_info = customers[0]
            query_history = """
                SELECT t.ticket_id, f.flight_number, f.departure_code, f.arrival_code, 
                       sc.class_name, s.seat_number, f.departure_time, f.arrival_time, 
                       t.final_price, t.status as ticket_status 
                FROM Tickets t 
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE t.customer_id = %s ORDER BY t.created_at DESC
            """
            cursor.execute(query_history, (customer_info['customer_id'],))
            ticket_history = cursor.fetchall()
            return customer_info, ticket_history
        finally:
            if conn: conn.close()

    def update_customer_info(self, customer_id: int, full_name: str, email: str) -> bool:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Customers SET full_name=%s, email=%s WHERE customer_id=%s", (full_name, email, customer_id))
            conn.commit()
            return True
        except Error: return False
        finally:
            if conn: conn.close()

class BookingRepository:
    def get_all_available_flights(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_code, f.arrival_code,
                       f.departure_time, f.arrival_time,
                       (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id AND s.seat_status = 'AVAILABLE') as available_seats
                FROM Flights f
                WHERE f.status = 'PENDING'
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def search_flights(self, dep_code: str, arr_code: str, date_str: str) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, 
                       (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id AND s.seat_status = 'AVAILABLE') as available_seats
                FROM Flights f
                WHERE f.departure_code = %s AND f.arrival_code = %s AND DATE(f.departure_time) = %s AND f.status = 'PENDING'
            """
            cursor.execute(query, (dep_code, arr_code, date_str))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_seat_map(self, flight_id: int) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT s.seat_id, s.seat_number, s.seat_status, sc.class_name
                FROM Seats s
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s 
                ORDER BY s.seat_id
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()
            
    def get_class_multiplier(self, class_name: str) -> float:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT price_multiplier FROM SeatClasses WHERE class_name = %s", (class_name.upper(),))
            res = cursor.fetchone()
            return float(res['price_multiplier']) if res else 1.0
        finally:
            if conn: conn.close()

    def process_ticket_transaction(self, ticket_data: Dict, is_hold: bool = False) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (ticket_data['seat_id'],))
            seat = cursor.fetchone()
            if not seat or seat['seat_status'] != 'AVAILABLE':
                conn.rollback()
                return False, "Rất tiếc! Ghế này vừa được người khác đặt."

            if ticket_data.get('voucher_id'):
                cursor.execute("UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = %s", (ticket_data['voucher_id'],))

            ticket_status = 'HELD' if is_hold else 'BOOKED'
            payment_id = None
            
            if not is_hold:
                trans_code = f"CASH-{uuid.uuid4().hex[:8].upper()}"
                query_pay = "INSERT INTO Payments (method, amount, status, transaction_code) VALUES ('CASH', %s, 'COMPLETED', %s)"
                cursor.execute(query_pay, (ticket_data['final_price'], trans_code))
                payment_id = cursor.lastrowid

            query_tkt = """
                INSERT INTO Tickets (flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_tkt, (
                ticket_data['flight_id'], ticket_data['customer_id'], ticket_data['seat_id'], 
                payment_id, ticket_data.get('voucher_id'), ticket_data['base_price'],
                ticket_data['final_price'], ticket_status
            ))

            if is_hold:
                cursor.execute("UPDATE Seats SET hold_expired_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE) WHERE seat_id = %s", (ticket_data['seat_id'],))

            conn.commit()
            return True, "Giữ chỗ thành công! Ghế sẽ bị nhả nếu không thanh toán trong 5 phút." if is_hold else "Xuất vé điện tử thành công!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi hệ thống: {str(e)}"
        finally:
            if conn: conn.close()

    def process_held_payment(self, ticket_id: int, pay_method: str) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("UPDATE Tickets SET status = 'BOOKED' WHERE ticket_id = %s AND status = 'HELD'", (ticket_id,))
            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Vé này không ở trạng thái giữ chỗ hoặc đã hết hạn!"
            
            cursor.execute("SELECT final_price FROM Tickets WHERE ticket_id = %s", (ticket_id,))
            res = cursor.fetchone()
            
            trans_code = f"{pay_method}-{uuid.uuid4().hex[:8].upper()}"
            query_pay = "INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, 'COMPLETED', %s)"
            cursor.execute(query_pay, (pay_method, res['final_price'], trans_code))
            payment_id = cursor.lastrowid
            
            cursor.execute("UPDATE Tickets SET payment_id = %s WHERE ticket_id = %s", (payment_id, ticket_id))
            
            conn.commit()
            return True, "Thanh toán thành công. Vé đã được xuất!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi: {e}"
        finally:
            if conn: conn.close()

class PassengerRepository:
    def search_passengers(self, keyword: str) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            kw = f"%{keyword}%"
            query = """
                SELECT t.ticket_id, c.full_name, c.phone, c.id_card, f.flight_number, 
                       s.seat_number, sc.class_name as ticket_class, t.status as ticket_status
                FROM Tickets t
                JOIN Customers c ON t.customer_id = c.customer_id
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE c.full_name LIKE %s OR c.phone LIKE %s OR c.id_card LIKE %s OR f.flight_number LIKE %s
                ORDER BY t.created_at DESC
            """
            cursor.execute(query, (kw, kw, kw, kw))
            return cursor.fetchall()
        finally:
            if conn: conn.close()
            
    def cancel_ticket(self, ticket_id: int) -> bool:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Tickets SET status = 'CANCELLED' WHERE ticket_id = %s", (ticket_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()