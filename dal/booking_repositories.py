# dal/booking_repositories.py
"""
Repository cho Booking workflows.
Xử lý: Tìm khách, tra cứu chuyến bay, ghế, transaction ticket + payment.
"""
from mysql.connector import Error
from config.database import DatabaseConnection
from typing import Dict, List, Tuple, Optional
import uuid

class CustomerRepository:
    def get_or_create(self, full_name: str, phone: str, id_card: str, email: str = "") -> int:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT customer_id FROM Customers WHERE phone = %s AND id_card = %s", 
                (phone, id_card)
            )
            res = cursor.fetchone()
            if res: return res['customer_id']
            
            cursor.execute(
                "INSERT INTO Customers (full_name, phone, id_card, email) VALUES (%s, %s, %s, %s)", 
                (full_name, phone, id_card, email)
            )
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
                SELECT customer_id, full_name, phone, id_card, email 
                FROM Customers
                WHERE CAST(customer_id AS CHAR) LIKE %s 
                   OR LOWER(full_name) LIKE %s 
                   OR phone LIKE %s 
                   OR LOWER(email) LIKE %s 
                   OR id_card LIKE %s
                LIMIT 1
            """
            cursor.execute(query, (kw, kw, kw, kw, kw))
            customer = cursor.fetchone()
            if not customer: return None, []
            
            query_history = """
                SELECT t.ticket_id, t.ticket_code, f.flight_number, 
                       CONCAT(a1.city, ' → ', a2.city) as route,
                       sc.class_name, s.seat_number, f.departure_time, f.arrival_time, 
                       t.final_price, t.status as ticket_status, p.status as payment_status
                FROM Tickets t 
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                LEFT JOIN Payments p ON t.payment_id = p.payment_id
                WHERE t.customer_id = %s 
                ORDER BY t.created_at DESC
            """
            cursor.execute(query_history, (customer['customer_id'],))
            ticket_history = cursor.fetchall()
            return customer, ticket_history
        finally:
            if conn: conn.close()


class BookingRepository:
    def get_all_available_flights(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, 
                       f.departure_code, f.arrival_code,
                       a1.city as dep_city, a2.city as arr_city,
                       f.departure_time, f.arrival_time, 
                       f.base_price, f.status,
                       COUNT(CASE WHEN s.seat_status = 'AVAILABLE' THEN 1 END) as available_seats,
                       COUNT(s.seat_id) as total_seats
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                LEFT JOIN Seats s ON f.flight_id = s.flight_id
                WHERE f.status = 'PENDING'
                GROUP BY f.flight_id
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
                       f.base_price, COUNT(CASE WHEN s.seat_status = 'AVAILABLE' THEN 1 END) as available_seats
                FROM Flights f
                LEFT JOIN Seats s ON f.flight_id = s.flight_id
                WHERE f.departure_code = %s AND f.arrival_code = %s AND DATE(f.departure_time) = %s AND f.status = 'PENDING'
                GROUP BY f.flight_id
                ORDER BY f.departure_time ASC
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
                SELECT s.seat_id, s.seat_number, s.seat_status, 
                       sc.class_id, sc.class_name, sc.price_multiplier
                FROM Seats s
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s 
                ORDER BY s.seat_number
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
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
            ticket_code = f"PNR-{uuid.uuid4().hex[:6].upper()}" # Tạo mã vé tự động
            payment_id = None
            
            if not is_hold:
                trans_code = f"CASH-{uuid.uuid4().hex[:8].upper()}"
                cursor.execute(
                    "INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, %s, %s)",
                    ('CASH', ticket_data['final_price'], 'COMPLETED', trans_code)
                )
                payment_id = cursor.lastrowid

            
            cursor.execute("""
                INSERT INTO Tickets (ticket_code, flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_code, ticket_data['flight_id'], ticket_data['customer_id'], ticket_data['seat_id'], 
                payment_id, ticket_data.get('voucher_id'), ticket_data['base_price'], ticket_data['final_price'], ticket_status
            ))
            ticket_id = cursor.lastrowid

            if is_hold:
                cursor.execute("UPDATE Seats SET seat_status = 'HELD', hold_expired_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE seat_id = %s", (ticket_data['seat_id'],))
            else:
                cursor.execute("UPDATE Seats SET seat_status = 'BOOKED', is_booked = TRUE WHERE seat_id = %s", (ticket_data['seat_id'],))

            conn.commit()
            msg = f"Giữ chỗ thành công (15 phút)!\nMã đặt chỗ: {ticket_code}" if is_hold else f"Xuất vé thành công!\nMã vé PNR: {ticket_code}"
            return True, msg
        except Error as e:
            conn.rollback()
            return False, f"Lỗi hệ thống giao dịch: {str(e)}"
        finally:
            if conn: conn.close()

    def process_held_payment(self, ticket_id: int, pay_method: str) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT ticket_id, final_price, status FROM Tickets WHERE ticket_id = %s FOR UPDATE", (ticket_id,))
            ticket = cursor.fetchone()
            if not ticket:
                conn.rollback()
                return False, "Không tìm thấy vé!"
            if ticket['status'] != 'HELD':
                conn.rollback()
                return False, f"Vé này không ở trạng thái giữ chỗ!"
            
            trans_code = f"{pay_method}-{uuid.uuid4().hex[:8].upper()}"
            cursor.execute(
                "INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, %s, %s)",
                (pay_method, ticket['final_price'], 'COMPLETED', trans_code)
            )
            payment_id = cursor.lastrowid
            
            cursor.execute("UPDATE Tickets SET status = 'BOOKED', payment_id = %s WHERE ticket_id = %s", (payment_id, ticket_id))
            
            conn.commit()
            return True, f"Thanh toán thành công! Giao dịch: {trans_code}"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi thanh toán: {e}"
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