# dal/admin_repositories.py
from mysql.connector import Error
from config.database import DatabaseConnection

class AdminUserRepository:
    def get_all(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username, role, created_at FROM Users")
            return cursor.fetchall()
        finally:
            if conn: conn.close()
            
    def update_role(self, user_id, role):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET role = %s WHERE user_id = %s", (role, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()

    def delete(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()

class AdminFlightRepository:
    def get_all_flights(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Flights ORDER BY departure_time DESC")
            return cursor.fetchall()
        except Error as e:
            return []
        finally:
            if conn: conn.close()

    def check_has_tickets(self, flight_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Tickets WHERE flight_id = %s", (flight_id,))
            return cursor.fetchone()[0] > 0
        finally:
            if conn: conn.close()

    def create_with_seats(self, flight_data, seats_data):
        conn = DatabaseConnection.get_connection()
        if not conn: return False
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            query_flight = "INSERT INTO Flights (flight_number, departure_code, arrival_code, departure_time, arrival_time, status) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query_flight, (flight_data['flight_number'], flight_data['departure_code'], flight_data['arrival_code'], flight_data['departure_time'], flight_data['arrival_time'], flight_data.get('status', 'PENDING')))
            new_flight_id = cursor.lastrowid

            query_seat = "INSERT INTO Seats (flight_id, seat_number, class_id, is_booked) VALUES (%s, %s, %s, %s)"
            seat_records = [(new_flight_id, s['number'], s['class_id'], False) for s in seats_data]
            cursor.executemany(query_seat, seat_records)
            
            conn.commit()
            return True
        except Error as e:
            conn.rollback() 
            return False
        finally:
            if conn: conn.close()

    def update(self, flight_id, data):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            query = "UPDATE Flights SET flight_number=%s, departure_code=%s, arrival_code=%s, departure_time=%s, arrival_time=%s, status=%s WHERE flight_id=%s"
            cursor.execute(query, (data['flight_number'], data['departure_code'], data['arrival_code'], data['departure_time'], data['arrival_time'], data['status'], flight_id))
            conn.commit()
            return True
        except Error as e:
            return False
        finally:
            if conn: conn.close()

    def delete(self, flight_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Flights WHERE flight_id = %s", (flight_id,))
            conn.commit()
            return True
        except Error as e:
            return False
        finally:
            if conn: conn.close()


class AdminAirportRepository:
    def get_all(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Airports")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def add(self, code, name, city, country):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Airports (airport_code, name, city, country) VALUES (%s, %s, %s, %s)", (code.upper(), name, city, country))
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
            cursor.execute("DELETE FROM Airports WHERE airport_code=%s", (code.upper(),))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()


class AdminVoucherRepository:
    def get_all(self):
        """Lấy toàn bộ danh sách Voucher để hiển thị cho Admin"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Vouchers ORDER BY expiry_date DESC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create(self, code, discount, max_discount, expiry, limit):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Vouchers (code, discount_percent, max_discount, expiry_date, usage_limit, used_count) VALUES (%s, %s, %s, %s, %s, 0)"
            cursor.execute(query, (code.upper(), discount, max_discount, expiry, limit))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn: conn.close()

    def get_by_code(self, code):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Vouchers WHERE code = %s", (code.upper(),))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def deactivate(self, code):
        """Khóa voucher bằng cách gán số lượt đã dùng = giới hạn"""
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
                SELECT DATE(payment_date) as date, SUM(amount) as total_revenue
                FROM Payments WHERE status = 'COMPLETED' AND DATE(payment_date) BETWEEN %s AND %s
                GROUP BY DATE(payment_date) ORDER BY date ASC
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
                ORDER BY total_tickets DESC LIMIT 10
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()