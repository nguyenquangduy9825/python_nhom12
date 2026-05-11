# dal/advanced_repositories.py
from mysql.connector import Error
from config.database import DatabaseConnection

class SeatClassRepository:
    def get_all(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT class_id, class_name, price_multiplier FROM SeatClasses ORDER BY class_id ASC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def create(self, name, multiplier):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO SeatClasses (class_name, price_multiplier) VALUES (%s, %s)", (name, multiplier))
            conn.commit()
            return True
        except Error: return False
        finally:
            if conn: conn.close()

class FlightOperationsRepository:
    def get_flights_for_combobox(self):
        """Lấy danh sách chuyến bay đổ vào Dropdown Menu"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT flight_id, flight_number, departure_code, arrival_code, status FROM Flights ORDER BY departure_time DESC")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_flight_ticket_list(self, flight_id):
        """Lấy danh sách hành khách KÈM TÊN HẠNG VÉ của 1 chuyến cụ thể"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.ticket_id, c.full_name, sc.class_name, s.seat_number, t.status 
                FROM Tickets t
                JOIN Customers c ON t.customer_id = c.customer_id
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE t.flight_id = %s
                ORDER BY s.seat_number ASC
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_flight_seat_map(self, flight_id):
        """Đổ dữ liệu Sơ đồ ghế động"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT s.seat_id, s.seat_number, sc.class_name, s.seat_status 
                FROM Seats s
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s
                ORDER BY s.seat_number ASC
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()