# dal/customer_repository.py
from typing import List, Dict, Tuple, Optional
from mysql.connector import Error
from config.database import DatabaseConnection
import uuid

class CustomerRepository:
    def get_airports(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT airport_code, city, name FROM Airports")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def search_flights(self, dep_code: str, arr_code: str, flight_date: str) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, 
                       1500000 AS base_price,
                       a1.city AS dep_city, a1.airport_code AS dep_code,
                       a2.city AS arr_city, a2.airport_code AS arr_code,
                       (SELECT COUNT(*) FROM Seats WHERE flight_id = f.flight_id AND seat_status = 'AVAILABLE') AS available_seats
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                WHERE f.departure_code = %s AND f.arrival_code = %s 
                  AND DATE(f.departure_time) = %s AND f.status = 'PENDING'
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query, (dep_code, arr_code, flight_date))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_seat_map(self, flight_id: int) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT s.seat_id, s.seat_number, s.seat_status, sc.class_name, sc.price_multiplier, s.hold_expired_at
                FROM Seats s
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s ORDER BY s.seat_id
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def hold_seat(self, seat_id: int) -> bool:
        """Khóa ghế chống người khác chọn cùng lúc khi đang điền form"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (seat_id,))
            seat = cursor.fetchone()
            if not seat or seat[0] != 'AVAILABLE': return False
                
            cursor.execute("UPDATE Seats SET seat_status = 'HELD', hold_expired_at = DATE_ADD(NOW(), INTERVAL 10 MINUTE) WHERE seat_id = %s", (seat_id,))
            conn.commit()
            return True
        except Error:
            conn.rollback()
            return False
        finally:
            if conn: conn.close()

    def release_seat(self, seat_id: int):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Seats SET seat_status = 'AVAILABLE', hold_expired_at = NULL WHERE seat_id = %s AND seat_status = 'HELD'", (seat_id,))
            conn.commit()
        finally:
            if conn: conn.close()

    def validate_voucher(self, voucher_code: str) -> Optional[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Vouchers WHERE code = %s", (voucher_code,))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def confirm_booking_transaction(self, data: Dict, is_hold: bool = False) -> Tuple[bool, str, Optional[int]]:
        """Giao dịch chung cho cả Giữ chỗ và Thanh toán"""
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            # 1. Đảm bảo 1 Khách hàng - N Vé (Tìm lại ID khách hàng nếu đã tồn tại)
            cursor.execute("SELECT customer_id FROM Customers WHERE id_card = %s", (data['id_card'],))
            customer = cursor.fetchone()
            if customer:
                customer_id = customer['customer_id']
                cursor.execute("UPDATE Customers SET full_name=%s, phone=%s, email=%s WHERE customer_id=%s", 
                               (data['full_name'], data['phone'], data['email'], customer_id))
            else:
                cursor.execute("INSERT INTO Customers (full_name, phone, email, id_card) VALUES (%s, %s, %s, %s)",
                               (data['full_name'], data['phone'], data['email'], data['id_card']))
                customer_id = cursor.lastrowid

            # 2. Xử lý Payment (Nếu Giữ chỗ thì payment_id = NULL theo đúng CSDL của bạn)
            payment_id = None
            if not is_hold:
                trans_code = f"{data['pay_method']}-{uuid.uuid4().hex[:8].upper()}"
                cursor.execute("INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, 'COMPLETED', %s)",
                               (data['pay_method'], data['final_price'], trans_code))
                payment_id = cursor.lastrowid

            # 3. Trừ lượt Voucher
            if data.get('voucher_id'):
                cursor.execute("UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = %s", (data['voucher_id'],))

            # 4. Xuất Vé (Status khác nhau dựa theo hành động)
            tkt_status = 'HELD' if is_hold else 'BOOKED'
            query_tkt = """
                INSERT INTO Tickets (flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_tkt, (
                data['flight_id'], customer_id, data['seat_id'], 
                payment_id, data.get('voucher_id'), data['base_price'], data['final_price'], tkt_status
            ))
            ticket_id = cursor.lastrowid

            # 5. Cập nhật Ghế (Nếu Hold thì gia hạn 24h, Nếu Paid thì khóa vĩnh viễn)
            if is_hold:
                cursor.execute("UPDATE Seats SET seat_status = 'HELD', is_booked = FALSE, hold_expired_at = DATE_ADD(NOW(), INTERVAL 24 HOUR) WHERE seat_id = %s", (data['seat_id'],))
            else:
                cursor.execute("UPDATE Seats SET seat_status = 'BOOKED', is_booked = TRUE, hold_expired_at = NULL WHERE seat_id = %s", (data['seat_id'],))

            conn.commit()
            return True, "Thành công!", ticket_id
        except Error as e:
            conn.rollback() 
            return False, f"SQL Error: {str(e)}", None
        finally:
            if conn: conn.close()

    def lookup_ticket(self, keyword: str) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.ticket_id, f.flight_number, f.departure_time, f.arrival_time, 
                       a1.city AS dep_city, a2.city AS arr_city,
                       c.full_name, s.seat_number, sc.class_name, t.final_price, t.status
                FROM Tickets t
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                JOIN Customers c ON t.customer_id = c.customer_id
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE CAST(t.ticket_id AS CHAR) = %s OR c.phone = %s OR c.id_card = %s
                ORDER BY t.created_at DESC
            """
            cursor.execute(query, (keyword, keyword, keyword))
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