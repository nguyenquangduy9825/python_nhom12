# dal/group_booking_repository.py
from mysql.connector import Error
from config.database import DatabaseConnection
from typing import Dict, List, Tuple
import uuid

class GroupBookingRepository:
    def get_active_flights(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.base_price, f.status,
                       f.departure_time, f.arrival_time, f.departure_code, f.arrival_code,
                       a1.city as dep_city, a2.city as arr_city,
                       (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id AND s.seat_status = 'AVAILABLE') as available_seats
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                WHERE f.status = 'PENDING'
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_all_flights_admin(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.base_price, f.status,
                       f.departure_time, f.arrival_time, f.departure_code, f.arrival_code,
                       a1.city as dep_city, a2.city as arr_city
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                ORDER BY f.flight_id DESC
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
                SELECT s.seat_id, s.seat_number, s.seat_status, sc.class_id, sc.class_name, sc.price_multiplier
                FROM Seats s
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s
                ORDER BY s.seat_id ASC
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_all_seat_classes(self) -> List[Dict]:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT class_id, class_name, price_multiplier FROM SeatClasses ORDER BY price_multiplier ASC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def update_seat_class(self, seat_id: int, class_id: int) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (seat_id,))
            seat = cursor.fetchone()
            if not seat or seat['seat_status'] != 'AVAILABLE':
                conn.rollback()
                return False, "Chỉ có thể cấu hình lại hạng ghế cho những ghế đang trống (AVAILABLE)."
            
            cursor.execute("UPDATE Seats SET class_id = %s WHERE seat_id = %s", (class_id, seat_id))
            conn.commit()
            return True, "Đã cập nhật cấu hình hạng ghế mới xuống hệ thống thành công!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi đồng bộ cơ sở dữ liệu: {e}"
        finally:
            if conn: conn.close()

    def process_admin_booking_flow(self, flight_id: int, contact_info: Dict, passengers: List[Dict], is_hold: bool, method: str) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            group_id = None
            group_code = ""
            ticket_status = 'HELD' if is_hold else 'BOOKED'

            if len(passengers) > 1:
                group_code = f"GRP-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute("INSERT INTO BookingGroups (group_code, contact_name, contact_phone, total_members, status) VALUES (%s, %s, %s, %s, 'ACTIVE')", 
                               (group_code, contact_info['name'], contact_info['phone'], len(passengers)))
                group_id = cursor.lastrowid

            for p in passengers:
                cursor.execute("SELECT customer_id FROM Customers WHERE phone = %s AND id_card = %s", (p['phone'], p['id_card']))
                cust = cursor.fetchone()
                if cust:
                    c_id = cust['customer_id']
                else:
                    cursor.execute("INSERT INTO Customers (full_name, phone, id_card) VALUES (%s, %s, %s)", (p['name'], p['phone'], p['id_card']))
                    c_id = cursor.lastrowid

                cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (p['seat_id'],))
                seat = cursor.fetchone()
                if not seat or seat['seat_status'] != 'AVAILABLE':
                    conn.rollback()
                    return False, f"Ghế {p['seat_number']} đã có người nhanh tay đặt trước!"

                payment_id = None
                if not is_hold:
                    trans_code = f"{method}-{uuid.uuid4().hex[:6].upper()}"
                    cursor.execute("INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, 'COMPLETED', %s)", (method, p['final_price'], trans_code))
                    payment_id = cursor.lastrowid

                ticket_code = f"PNR-{uuid.uuid4().hex[:6].upper()}"
                
                cursor.execute("INSERT INTO Tickets (ticket_code, flight_id, customer_id, group_id, seat_id, payment_id, voucher_id, base_price, final_price, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                               (ticket_code, flight_id, c_id, group_id, p['seat_id'], payment_id, p.get('voucher_id'), p['base_price'], p['final_price'], ticket_status))

                if p.get('voucher_id'):
                    cursor.execute("UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = %s", (p['voucher_id'],))

                if is_hold:
                    cursor.execute("UPDATE Seats SET seat_status = 'HELD', hold_expired_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE seat_id = %s", (p['seat_id'],))
                else:
                    cursor.execute("UPDATE Seats SET seat_status = 'BOOKED', is_booked = TRUE WHERE seat_id = %s", (p['seat_id'],))

            conn.commit()
            action = "Giữ chỗ" if is_hold else "Xuất vé"
            if len(passengers) > 1: return True, f"{action} thành công cho đoàn! Mã đặt đoàn: {group_code}"
            else: return True, f"{action} cá nhân thành công! Mã vé PNR: {ticket_code}"

        except Error as e:
            conn.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {e}"
        finally:
            if conn: conn.close()

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
            
    def cancel_ticket_admin(self, ticket_id: int) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT seat_id, status FROM Tickets WHERE ticket_id = %s FOR UPDATE", (ticket_id,))
            tkt = cursor.fetchone()
            if not tkt:
                conn.rollback(); return False, "Không tìm thấy vé trong hệ thống."
            if tkt['status'] == 'CANCELLED':
                conn.rollback(); return False, "Vé này đã bị hủy từ trước."
                
            cursor.execute("UPDATE Tickets SET status = 'CANCELLED' WHERE ticket_id = %s", (ticket_id,))
            cursor.execute("UPDATE Seats SET seat_status = 'AVAILABLE', hold_expired_at = NULL, is_booked = FALSE WHERE seat_id = %s", (tkt['seat_id'],))
            conn.commit()
            return True, "Hủy vé thành công. Chỗ ngồi đã được hoàn trả lại hệ thống."
        except Exception as e:
            conn.rollback(); return False, f"Lỗi hệ thống CSDL: {e}"
        finally:
            if conn: conn.close()

    # Nhận mã vé máy bay và tạo sơ đồ ghế tự động
    def insert_flight(self, f_num: str, dep_code: str, arr_code: str, dep_time: str, arr_time: str, price: float, status: str, aircraft_type_id: int = None) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            
            # Nếu quên chưa cấu hình loại máy bay, lấy tạm máy bay đầu tiên
            if not aircraft_type_id:
                cursor.execute("SELECT aircraft_type_id FROM AircraftTypes ORDER BY aircraft_type_id ASC LIMIT 1")
                ac = cursor.fetchone()
                if ac: aircraft_type_id = ac['aircraft_type_id']
            
            query = """
                INSERT INTO Flights (flight_number, departure_code, arrival_code, departure_time, arrival_time, base_price, status, aircraft_type_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (f_num.upper(), dep_code.upper(), arr_code.upper(), dep_time, arr_time, price, status, aircraft_type_id))
            flight_id = cursor.lastrowid
            
            # Lấy bản vẽ sơ đồ cấu hình ghế của máy bay này đắp sang
            if aircraft_type_id:
                cursor.execute("SELECT seat_number, class_id FROM AircraftSeatTemplates WHERE aircraft_type_id = %s", (aircraft_type_id,))
                templates = cursor.fetchall()
                if templates:
                    for t in templates:
                        cursor.execute("INSERT INTO Seats (flight_id, seat_number, class_id, seat_status) VALUES (%s, %s, %s, 'AVAILABLE')", 
                                       (flight_id, t['seat_number'], t['class_id']))
                else: # Fallback cơ bản
                    default_seats = [('A1', 2), ('A2', 2), ('B1', 1), ('B2', 1)]
                    for seat_num, class_id in default_seats:
                        cursor.execute("INSERT INTO Seats (flight_id, seat_number, class_id, seat_status) VALUES (%s, %s, %s, 'AVAILABLE')", (flight_id, seat_num, class_id))
            
            conn.commit()
            return True, "Thêm mới chuyến bay và khởi tạo sơ đồ ghế tự động từ cấu hình Tàu bay thành công!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi tạo chuyến bay: {e}"
        finally:
            if conn: conn.close()

    def update_flight(self, flight_id: int, f_num: str, dep_code: str, arr_code: str, dep_time: str, arr_time: str, price: float, status: str, aircraft_type_id: int = None) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            
            if aircraft_type_id:
                query = """
                    UPDATE Flights 
                    SET flight_number=%s, departure_code=%s, arrival_code=%s, departure_time=%s, arrival_time=%s, base_price=%s, status=%s, aircraft_type_id=%s
                    WHERE flight_id=%s
                """
                cursor.execute(query, (f_num.upper(), dep_code.upper(), arr_code.upper(), dep_time, arr_time, price, status, aircraft_type_id, flight_id))
            else:
                query = """
                    UPDATE Flights 
                    SET flight_number=%s, departure_code=%s, arrival_code=%s, departure_time=%s, arrival_time=%s, base_price=%s, status=%s
                    WHERE flight_id=%s
                """
                cursor.execute(query, (f_num.upper(), dep_code.upper(), arr_code.upper(), dep_time, arr_time, price, status, flight_id))
                
            conn.commit()
            return True, "Cập nhật thông tin chuyến bay thành công!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi cập nhật: {e}"
        finally:
            if conn: conn.close()

    def delete_flight(self, flight_id: int) -> Tuple[bool, str]:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Tickets WHERE flight_id = %s", (flight_id,))
            if cursor.fetchone()[0] > 0:
                conn.rollback(); return False, "Không thể xóa chuyến bay này vì đã có vé được đặt!"
            cursor.execute("DELETE FROM Flights WHERE flight_id = %s", (flight_id,))
            conn.commit()
            return True, "Xóa chuyến bay thành công khỏi hệ thống."
        except Error as e:
            conn.rollback(); return False, f"Lỗi hệ thống: {e}"
        finally:
            if conn: conn.close()