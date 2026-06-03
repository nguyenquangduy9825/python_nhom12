# dal/admin_repositories.py
from mysql.connector import Error
from config.database import DatabaseConnection

class AdminUserRepository:
    def search_users(self, keyword):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            kw = f"%{keyword}%"
            query = """
                SELECT user_id, username, role, created_at 
                FROM Users
                WHERE CAST(user_id AS CHAR) LIKE %s OR username LIKE %s OR role LIKE %s
                ORDER BY user_id DESC
            """
            cursor.execute(query, (kw, kw, kw))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create(self, username, password_hash, role):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, %s)", 
                           (username, password_hash, role.upper()))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def update(self, user_id, password_hash, role):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            if password_hash:
                cursor.execute("UPDATE Users SET password_hash=%s, role=%s WHERE user_id=%s", (password_hash, role.upper(), user_id))
            else:
                cursor.execute("UPDATE Users SET role=%s WHERE user_id=%s", (role.upper(), user_id))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def delete(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def change_password(self, user_id, old_hash, new_hash):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT password_hash FROM Users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or user['password_hash'] != old_hash:
                return False, "Mật khẩu hiện tại không chính xác!"
            
            cursor.execute("UPDATE Users SET password_hash = %s WHERE user_id = %s", (new_hash, user_id))
            conn.commit()
            return True, "Đổi mật khẩu thành công!"
        except Error as e:
            return False, f"Lỗi CSDL: {e}"
        finally:
            if conn: conn.close()


class AdminAirportRepository:
    def get_all(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT airport_code, name, city, country FROM Airports ORDER BY airport_code ASC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create(self, code, name, city, country):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Airports (airport_code, name, city, country) VALUES (%s, %s, %s, %s)", 
                           (code.upper(), name, city, country))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def update(self, code, name, city, country):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Airports SET name=%s, city=%s, country=%s WHERE airport_code=%s", 
                           (name, city, country, code.upper()))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def delete(self, code):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Flights WHERE departure_code = %s OR arrival_code = %s", (code.upper(), code.upper()))
            if cursor.fetchone()[0] > 0: 
                return False 
            cursor.execute("DELETE FROM Airports WHERE airport_code = %s", (code.upper(),))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()


class AdminVoucherRepository:
    def get_all(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Vouchers ORDER BY expiry_date DESC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()
            
    def create(self, code, discount, max_disc, expiry, limit):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Vouchers (code, discount_percent, max_discount, usage_limit, expiry_date) VALUES (%s, %s, %s, %s, %s)", 
                           (code.upper(), discount, max_disc, limit, expiry))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def update(self, code, discount, max_disc, expiry, limit):
        """BỔ SUNG: Cập nhật Voucher"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                UPDATE Vouchers 
                SET discount_percent=%s, max_discount=%s, usage_limit=%s, expiry_date=%s 
                WHERE code=%s
            """
            cursor.execute(query, (discount, max_disc, limit, expiry, code.upper()))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()
            
    def deactivate(self, code):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Vouchers SET usage_limit = used_count WHERE code = %s", (code.upper(),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()


class AdminReportRepository:
    def get_revenue(self, from_date, to_date):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT DATE(created_at) as date, SUM(final_price) as total_revenue
                FROM Tickets 
                WHERE status = 'BOOKED' AND DATE(created_at) BETWEEN %s AND %s
                GROUP BY DATE(created_at) 
                ORDER BY date ASC
            """
            cursor.execute(query, (from_date, to_date))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_top_routes(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.departure_code, f.arrival_code, COUNT(t.ticket_id) as total_tickets
                FROM Tickets t
                JOIN Flights f ON t.flight_id = f.flight_id
                WHERE t.status != 'CANCELLED'
                GROUP BY f.departure_code, f.arrival_code
                ORDER BY total_tickets DESC 
                LIMIT 10
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()

class AdminAircraftRepository:
    def get_all_aircrafts(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM AircraftTypes ORDER BY aircraft_type_id DESC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create_aircraft(self, name, manufacturer, seats):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO AircraftTypes (type_name, manufacturer, total_seats) VALUES (%s, %s, %s)",
                           (name, manufacturer, seats))
            conn.commit()
            return True, "Thêm loại máy bay thành công!"
        except Error as e:
            return False, f"Lỗi cơ sở dữ liệu: {e}"
        finally:
            if conn: conn.close()

    def get_seat_templates(self, aircraft_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.template_id, t.seat_number, t.class_id, c.class_name
                FROM AircraftSeatTemplates t
                JOIN SeatClasses c ON t.class_id = c.class_id
                WHERE t.aircraft_type_id = %s
                ORDER BY t.seat_number
            """, (aircraft_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_all_seat_classes(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT class_id, class_name FROM SeatClasses ORDER BY class_id ASC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def save_seat_templates(self, aircraft_id, templates):
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM AircraftSeatTemplates WHERE aircraft_type_id = %s", (aircraft_id,))
            if templates:
                query = "INSERT INTO AircraftSeatTemplates (aircraft_type_id, seat_number, class_id) VALUES (%s, %s, %s)"
                data = [(aircraft_id, t['seat_number'], t['class_id']) for t in templates]
                cursor.executemany(query, data)
                cursor.execute("UPDATE AircraftTypes SET total_seats = %s WHERE aircraft_type_id = %s", (len(templates), aircraft_id))
            conn.commit()
            return True, "Đã lưu sơ đồ ghế vào hệ thống!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi lưu sơ đồ: {e}"
        finally:
            if conn: conn.close()

class AdminTimekeepingRepository:
    def check_in(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Timekeeping (user_id, check_in_time, work_date) VALUES (%s, NOW(), CURDATE())", (user_id,))
            conn.commit()
            return True, "Check-in thành công! Chúc bạn một ca làm việc hiệu quả."
        except Error as e:
            return False, f"Lỗi hệ thống: {e}"
        finally:
            if conn: conn.close()

    def check_out(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id FROM Timekeeping 
                WHERE user_id = %s AND work_date = CURDATE() AND check_out_time IS NULL 
                ORDER BY check_in_time DESC LIMIT 1
            """, (user_id,))
            record = cursor.fetchone()
            
            if not record:
                return False, "Bạn chưa Check-in hôm nay hoặc đã Check-out rồi!"
                
            cursor.execute("UPDATE Timekeeping SET check_out_time = NOW() WHERE id = %s", (record['id'],))
            conn.commit()
            return True, "Check-out thành công! Cảm ơn bạn đã hoàn thành ca làm việc."
        except Error as e:
            return False, f"Lỗi hệ thống: {e}"
        finally:
            if conn: conn.close()

    def get_history(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT check_in_time, check_out_time, work_date 
                FROM Timekeeping 
                WHERE user_id = %s 
                ORDER BY check_in_time DESC LIMIT 30
            """, (user_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()