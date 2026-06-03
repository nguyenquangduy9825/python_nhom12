class FlightRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_all_available_flights(self):
        query = """
            SELECT f.flight_id, f.flight_number, f.departure_code, f.arrival_code, 
                   f.departure_time, f.arrival_time, f.base_price,
                   COUNT(CASE WHEN s.seat_status = 'AVAILABLE' THEN 1 END) AS available_seats,
                   COUNT(s.seat_id) AS total_seats
            FROM Flights f
            LEFT JOIN Seats s ON f.flight_id = s.flight_id
            WHERE f.departure_time > NOW() AND f.status = 'PENDING'
            GROUP BY f.flight_id;
        """
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()

    def get_booking_details(self, phone, pnr):
        query = """
            SELECT t.ticket_id, b.booking_code, f.flight_number, c.full_name, 
                   s.seat_number, t.status AS ticket_status, 
                   p.status AS payment_status, t.final_price
            FROM BoardingPasses b
            JOIN Tickets t ON b.ticket_id = t.ticket_id
            JOIN Customers c ON t.customer_id = c.customer_id
            JOIN Flights f ON t.flight_id = f.flight_id
            JOIN Seats s ON t.seat_id = s.seat_id
            LEFT JOIN Payments p ON t.payment_id = p.payment_id
            WHERE c.phone = %s AND b.booking_code = %s
        """
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(query, (phone, pnr))
        return cursor.fetchone()