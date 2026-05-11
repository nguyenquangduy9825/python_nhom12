# models/ticket.py
class Ticket:
    def __init__(self, ticket_id, flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status, booking_date):
        self.ticket_id = ticket_id
        self.flight_id = flight_id
        self.customer_id = customer_id
        self.seat_id = seat_id
        self.payment_id = payment_id
        self.voucher_id = voucher_id
        self.base_price = base_price
        self.final_price = final_price
        self.status = status
        self.booking_date = booking_date