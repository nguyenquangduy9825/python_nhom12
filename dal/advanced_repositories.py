# dal/advanced_repositories.py
from mysql.connector import Error
from config.database import DatabaseConnection
from typing import Dict, List, Tuple
import uuid

class SeatClassRepository:
    def get_all(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT class_id, class_name, price_multiplier, description FROM SeatClasses ORDER BY class_id ASC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create(self, name: str, multiplier: float, description: str) -> bool:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO SeatClasses (class_name, price_multiplier, description) VALUES (%s, %s, %s)", 
                           (name.upper(), multiplier, description))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def update(self, class_id: int, name: str, multiplier: float, description: str) -> bool:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE SeatClasses SET class_name=%s, price_multiplier=%s, description=%s WHERE class_id=%s", 
                           (name.upper(), multiplier, description, class_id))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def delete(self, class_id: int) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            
            # KIỂM TRA RÀNG BUỘC: Hạng ghế có đang được dùng cho ghế nào trên máy bay không?
            cursor.execute("SELECT COUNT(*) FROM Seats WHERE class_id = %s", (class_id,))
            if cursor.fetchone()[0] > 0:
                conn.rollback()
                return False, "Không thể xóa hạng vé này vì đang có ghế trên chuyến bay sử dụng nó."
            
            cursor.execute("DELETE FROM SeatClasses WHERE class_id = %s", (class_id,))
            conn.commit()
            return True, "Xóa hạng vé thành công."
        except Error as e:
            conn.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {e}"
        finally:
            if conn: conn.close()

class AdminBookingRepository:
    def get_all_flights(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, f.base_price,
                       a1.city as dep_city, a2.city as arr_city, f.status,
                       (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id AND s.seat_status = 'AVAILABLE') as available_seats
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_seat_map(self, flight_id: int) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT s.seat_id, s.seat_number, s.seat_status, sc.class_name, sc.price_multiplier
                FROM Seats s JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s ORDER BY s.seat_id ASC
            """, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create_booking(self, flight_id: int, seat_id: int, customer_data: Dict, pricing: Dict, is_hold: bool, method: str) -> Tuple[bool, str]:
        """Tạo booking. Trạng thái phụ thuộc vào nút (Giữ chỗ/Thanh toán tiền mặt/Thanh toán QR)"""
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            # 1. Tìm hoặc tạo dữ liệu khách hàng
            cursor.execute("SELECT customer_id FROM Customers WHERE phone=%s AND id_card=%s", (customer_data['phone'], customer_data['id_card']))
            c_res = cursor.fetchone()
            if c_res:
                c_id = c_res['customer_id']
            else:
                cursor.execute("INSERT INTO Customers (full_name, phone, id_card, email) VALUES (%s, %s, %s, %s)", 
                               (customer_data['name'], customer_data['phone'], customer_data['id_card'], customer_data.get('email', '')))
                c_id = cursor.lastrowid

            # 2. Khóa dòng (FOR UPDATE) để chống người khác nẫng tay trên
            cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (seat_id,))
            seat = cursor.fetchone()
            if not seat or seat['seat_status'] != 'AVAILABLE':
                conn.rollback()
                return False, "Rất tiếc, ghế này vừa bị nhân viên/khách hàng khác đặt."

            # 3. Thiết lập thông số Ticket
            ticket_code = f"PNR-{uuid.uuid4().hex[:6].upper()}"
            ticket_status = 'HELD' if is_hold else 'BOOKED'
            payment_id = None

            # 4. Xử lý Payment (Nếu khách thanh toán ngay bằng Tiền mặt / QR)
            if not is_hold:
                trans_code = f"{method}-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute("INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, 'COMPLETED', %s)",
                               (method, pricing['final_price'], trans_code))
                payment_id = cursor.lastrowid

            # 5. Lưu Ticket
            cursor.execute("""
                INSERT INTO Tickets (ticket_code, flight_id, customer_id, seat_id, base_price, final_price, status, payment_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ticket_code, flight_id, c_id, seat_id, pricing['base_price'], pricing['final_price'], ticket_status, payment_id))

            # 6. Cập nhật trạng thái Ghế
            if is_hold:
                cursor.execute("UPDATE Seats SET seat_status='HELD', hold_expired_at=DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE seat_id=%s", (seat_id,))
            else:
                cursor.execute("UPDATE Seats SET seat_status='BOOKED', is_booked=TRUE WHERE seat_id=%s", (seat_id,))

            conn.commit()
            return True, ticket_code
        except Error as e:
            conn.rollback()
            return False, f"Lỗi hệ thống CSDL: {e}"
        finally:
            if conn: conn.close()