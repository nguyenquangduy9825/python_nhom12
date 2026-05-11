# dal/group_booking_repository.py
from config.database import DatabaseConnection
from mysql.connector import Error
import uuid

class GroupBookingRepository:
    def get_airports(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT airport_code, city FROM Airports")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_all_available_flights(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, 1500000 AS base_price,
                       a1.city AS dep_city, a1.airport_code AS dep_code,
                       a2.city AS arr_city, a2.airport_code AS arr_code,
                       (SELECT COUNT(*) FROM Seats WHERE flight_id = f.flight_id AND seat_status = 'AVAILABLE') AS available_seats
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

    def search_flights(self, dep_code, arr_code, flight_date):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT f.flight_id, f.flight_number, f.departure_time, f.arrival_time, 1500000 AS base_price,
                       a1.city AS dep_city, a2.city AS arr_city,
                       (SELECT COUNT(*) FROM Seats WHERE flight_id = f.flight_id AND seat_status = 'AVAILABLE') AS available_seats
                FROM Flights f
                JOIN Airports a1 ON f.departure_code = a1.airport_code
                JOIN Airports a2 ON f.arrival_code = a2.airport_code
                WHERE f.departure_code = %s AND f.arrival_code = %s AND DATE(f.departure_time) = %s AND f.status = 'PENDING'
                ORDER BY f.departure_time ASC
            """
            cursor.execute(query, (dep_code, arr_code, flight_date))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def get_seat_map(self, flight_id: int):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT s.seat_id, s.seat_number, s.seat_status, sc.class_name, sc.price_multiplier, s.hold_expired_at
                FROM Seats s JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE s.flight_id = %s ORDER BY s.seat_id
            """, (flight_id,))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def validate_voucher(self, voucher_code: str):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Vouchers WHERE code = %s", (voucher_code,))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def commit_group_booking(self, group_info: dict, passengers: list, is_hold: bool):
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            seat_ids = [p['seat_id'] for p in passengers]
            format_strings = ','.join(['%s'] * len(seat_ids))
            cursor.execute(f"SELECT seat_id, seat_status FROM Seats WHERE seat_id IN ({format_strings}) FOR UPDATE", tuple(seat_ids))
            locked_seats = cursor.fetchall()

            for s in locked_seats:
                if s['seat_status'] != 'AVAILABLE':
                    conn.rollback()
                    return False, f"Ghế ID {s['seat_id']} vừa bị khách khác chọn!", ""

            booking_code = f"BK-{uuid.uuid4().hex[:6].upper()}"
            status = 'HELD' if is_hold else 'PAID'
            
            q_group = """
                INSERT INTO booking_groups (booking_code, contact_name, contact_phone, contact_email, 
                                            total_passengers, total_amount, booking_status, payment_method, hold_expired_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 15 MINUTE))
            """
            cursor.execute(q_group, (
                booking_code, group_info['contact_name'], group_info['contact_phone'], group_info['contact_email'],
                len(passengers), group_info['total_amount'], status, group_info['payment_method']
            ))
            group_id = cursor.lastrowid

            payment_id = None
            if not is_hold:
                trans_code = f"QR-{uuid.uuid4().hex[:8].upper()}"
                cursor.execute("INSERT INTO Payments (method, amount, status, transaction_code) VALUES (%s, %s, 'COMPLETED', %s)",
                               (group_info['payment_method'], group_info['total_amount'], trans_code))
                payment_id = cursor.lastrowid

            if group_info.get('voucher_id'):
                cursor.execute("UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = %s", (group_info['voucher_id'],))

            for pax in passengers:
                cursor.execute("SELECT customer_id FROM Customers WHERE id_card = %s", (pax['id_card'],))
                cust = cursor.fetchone()
                if cust:
                    c_id = cust['customer_id']
                    cursor.execute("UPDATE Customers SET full_name=%s, phone=%s WHERE customer_id=%s", (pax['name'], pax['phone'], c_id))
                else:
                    cursor.execute("INSERT INTO Customers (full_name, phone, id_card) VALUES (%s, %s, %s)", (pax['name'], pax['phone'], pax['id_card']))
                    c_id = cursor.lastrowid

                tkt_code = f"TK-{uuid.uuid4().hex[:6].upper()}"
                tkt_status = 'HELD' if is_hold else 'BOOKED'
                q_tkt = """
                    INSERT INTO Tickets (ticket_code, booking_group_id, flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status, hold_expired_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 15 MINUTE))
                """
                cursor.execute(q_tkt, (tkt_code, group_id, group_info['flight_id'], c_id, pax['seat_id'], payment_id, group_info.get('voucher_id'), pax['base_price'], pax['final_price'], tkt_status))

                seat_status = 'HELD' if is_hold else 'BOOKED'
                is_booked = 0 if is_hold else 1
                cursor.execute("UPDATE Seats SET seat_status = %s, is_booked = %s, hold_expired_at = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE seat_id = %s", 
                               (seat_status, is_booked, pax['seat_id']))

            conn.commit()
            return True, "Thành công", booking_code

        except Error as e:
            conn.rollback()
            return False, f"Database Error: {str(e)}", ""
        finally:
            if conn: conn.close()

    def confirm_payment_for_held(self, booking_code: str) -> bool:
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            cursor.execute("UPDATE booking_groups SET booking_status = 'PAID', hold_expired_at = NULL WHERE booking_code = %s", (booking_code,))
            cursor.execute("UPDATE Tickets SET status = 'BOOKED', hold_expired_at = NULL WHERE booking_group_id = (SELECT id FROM booking_groups WHERE booking_code = %s)", (booking_code,))
            cursor.execute("""
                UPDATE Seats SET seat_status = 'BOOKED', is_booked = TRUE, hold_expired_at = NULL 
                WHERE seat_id IN (SELECT seat_id FROM Tickets WHERE booking_group_id = (SELECT id FROM booking_groups WHERE booking_code = %s))
            """, (booking_code,))
            conn.commit()
            return True
        except Error:
            conn.rollback()
            return False
        finally:
            if conn: conn.close()

    def search_passengers(self, keyword: str):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.ticket_id, c.full_name, c.phone, c.id_card,
                       f.flight_number, s.seat_number, sc.class_name AS ticket_class,
                       t.status AS ticket_status
                FROM Tickets t
                JOIN Customers c ON t.customer_id = c.customer_id
                JOIN Flights f ON t.flight_id = f.flight_id
                JOIN Seats s ON t.seat_id = s.seat_id
                JOIN SeatClasses sc ON s.class_id = sc.class_id
                WHERE c.full_name LIKE %s OR c.phone LIKE %s OR c.id_card LIKE %s OR f.flight_number LIKE %s
                ORDER BY t.created_at DESC
            """
            search_pattern = f"%{keyword}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def cancel_ticket(self, ticket_id: int):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Tickets SET status = 'CANCELLED' WHERE ticket_id = %s", (ticket_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()

    def get_class_multiplier(self, class_name: str) -> float:
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT price_multiplier FROM SeatClasses WHERE class_name = %s", (class_name,))
            row = cursor.fetchone()
            return float(row['price_multiplier']) if row else 1.0
        except Exception:
            return 1.0
        finally:
            if conn: conn.close()

    def lookup_ticket(self, keyword: str):
        """Khôi phục hàm tra cứu vé cho Khách Hàng"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT t.ticket_id, f.flight_number, f.departure_time, f.arrival_time, 
                       a1.city AS dep_city, a2.city AS arr_city,
                       c.full_name, s.seat_number, sc.class_name AS ticket_class, t.final_price, t.status AS ticket_status
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