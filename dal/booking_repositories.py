# dal/booking_repositories.py
from mysql.connector import Error
from config.database import DatabaseConnection

class CustomerRepository:
    def get_or_create_customer(self, full_name, email, phone, id_card):
        conn = DatabaseConnection.get_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT customer_id FROM Customers WHERE phone = %s OR id_card = %s", (phone, id_card))
            existing_customers = cursor.fetchall()
            if existing_customers: 
                return existing_customers[0]['customer_id']
            
            query = "INSERT INTO Customers (full_name, email, phone, id_card) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (full_name, email, phone, id_card))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            return None
        finally:
            if conn: conn.close()

    def search_customer_info_and_history(self, keyword):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT * FROM Customers WHERE phone = %s OR id_card = %s", (keyword, keyword))
            customers = cursor.fetchall()
            if not customers: 
                return None, []
            
            customer_info = customers[0]
            
            query_history = """
                SELECT t.ticket_id, f.flight_number, f.departure_code, f.arrival_code, 
                       sc.class_name, s.seat_number, f.departure_time, f.arrival_time, 
                       t.final_price, t.status 
                FROM Tickets t 
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE t.customer_id = %s ORDER BY t.booking_date DESC
            """
            cursor.execute(query_history, (customer_info['customer_id'],))
            ticket_history = cursor.fetchall()
            return customer_info, ticket_history
        finally:
            if conn: conn.close()

    def update_customer_info(self, customer_id, full_name, email):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Customers SET full_name=%s, email=%s WHERE customer_id=%s", (full_name, email, customer_id))
            conn.commit()
            return True
        except Error: return False
        finally:
            if conn: conn.close()

class TicketRepository:
    def get_all_pending_flights_with_seats(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_code, f.arrival_code, 
                       f.departure_time, f.arrival_time, COUNT(s.seat_id) as available_seats
                FROM Flights f
                LEFT JOIN Seats s ON f.flight_id = s.flight_id AND s.is_booked = FALSE
                WHERE f.status = 'PENDING'
                GROUP BY f.flight_id
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_available_seats_by_flight(self, flight_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT s.seat_id, s.seat_number, c.class_name, c.price_multiplier
                FROM Seats s
                JOIN SeatClasses c ON s.class_id = c.class_id
                WHERE s.flight_id = %s AND s.is_booked = FALSE
                ORDER BY s.class_id DESC, s.seat_number ASC
            """
            cursor.execute(query, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def search_flights_with_seats(self, dep_code, arr_code, flight_date):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_code, f.arrival_code,
                       f.departure_time, f.arrival_time, COUNT(s.seat_id) as available_seats
                FROM Flights f
                LEFT JOIN Seats s ON f.flight_id = s.flight_id AND s.is_booked = FALSE
                WHERE f.departure_code = %s AND f.arrival_code = %s AND DATE(f.departure_time) = %s
                  AND f.status = 'PENDING'
                GROUP BY f.flight_id
            """
            cursor.execute(query, (dep_code, arr_code, flight_date))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def book_ticket_transaction(self, flight_id, customer_id, seat_id, voucher_id, base_price, final_price, is_hold=False):
        conn = DatabaseConnection.get_connection()
        if not conn: return False, "Lỗi kết nối CSDL"
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute("SELECT is_booked FROM Seats WHERE seat_id = %s FOR UPDATE", (seat_id,))
            seat = cursor.fetchone()
            if not seat or seat[0]:
                conn.rollback()
                return False, "Ghế đã có người đặt!"
            if voucher_id:
                cursor.execute("UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = %s", (voucher_id,))
            pay_status = 'PENDING' if is_hold else 'COMPLETED'
            cursor.execute("INSERT INTO Payments (method, amount, status) VALUES (%s, %s, %s)", ('CASH', final_price, pay_status))
            payment_id = cursor.lastrowid
            ticket_status = 'HELD' if is_hold else 'BOOKED'
            query_ticket = """
                INSERT INTO Tickets (flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_ticket, (flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, ticket_status))
            cursor.execute("UPDATE Seats SET is_booked = TRUE WHERE seat_id = %s", (seat_id,))
            conn.commit()
            return True, "Thành công!"
        except Error as e:
            conn.rollback()
            return False, "Lỗi hệ thống CSDL"
        finally:
            if conn: conn.close()

    def cancel_ticket(self, ticket_id):
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute("SELECT seat_id FROM Tickets WHERE ticket_id = %s", (ticket_id,))
            result = cursor.fetchone()
            if not result:
                return False, "Không tìm thấy mã vé!"
            seat_id = result[0]
            cursor.execute("UPDATE Tickets SET status = 'CANCELLED' WHERE ticket_id = %s", (ticket_id,))
            cursor.execute("UPDATE Seats SET is_booked = FALSE WHERE seat_id = %s", (seat_id,))
            conn.commit()
            return True, "Đã hủy vé và nhả ghế thành công!"
        except Error as e:
            conn.rollback()
            return False, "Lỗi khi hủy vé."
        finally:
            if conn: conn.close()

    def process_held_payment(self, ticket_id, pay_method):
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute("UPDATE Tickets SET status = 'BOOKED' WHERE ticket_id = %s AND status = 'HELD'", (ticket_id,))
            if cursor.rowcount == 0:
                conn.rollback()
                return False, "Vé này không ở trạng thái chờ thanh toán hoặc đã quá hạn!"
            cursor.execute("SELECT payment_id FROM Tickets WHERE ticket_id = %s", (ticket_id,))
            payment_id = cursor.fetchone()[0]
            cursor.execute("UPDATE Payments SET status = 'COMPLETED', method = %s WHERE payment_id = %s", (pay_method, payment_id))
            conn.commit()
            return True, "Thanh toán thành công. Vé đã được xuất!"
        except Error as e:
            conn.rollback()
            return False, "Lỗi thanh toán vé."
        finally:
            if conn: conn.close()