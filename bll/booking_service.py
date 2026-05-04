# bll/booking_service.py
from dal.booking_repositories import CustomerRepository, TicketRepository
from dal.admin_repositories import AdminVoucherRepository
import datetime

class BookingService:
    def __init__(self):
        self.customer_repo = CustomerRepository()
        self.ticket_repo = TicketRepository()
        self.voucher_repo = AdminVoucherRepository()

    def get_all_available_flights(self):
        return self.ticket_repo.get_all_pending_flights_with_seats()

    def search_flights(self, departure_code, arrival_code, flight_date):
        if not departure_code or not arrival_code or not flight_date:
            return []
        return self.ticket_repo.search_flights_with_seats(departure_code, arrival_code, flight_date)

    def get_available_seats(self, flight_id):
        if not flight_id or flight_id <= 0:
            return []
        return self.ticket_repo.get_available_seats_by_flight(flight_id)

    def search_customer(self, keyword):
        if not keyword:
            return None, []
        return self.customer_repo.search_customer_info_and_history(keyword)

    def update_customer_info(self, customer_id, full_name, email):
        if self.customer_repo.update_customer_info(customer_id, full_name, email):
            return True, "Cập nhật thông tin cá nhân thành công!"
        return False, "Lỗi khi cập nhật vào hệ thống."

    def get_active_vouchers(self):
        all_vouchers = self.voucher_repo.get_all()
        active_vouchers = []
        now = datetime.datetime.now()
        for v in all_vouchers:
            if v['expiry_date'] > now and v['used_count'] < v['usage_limit']:
                active_vouchers.append(v)
        return active_vouchers

    def process_booking(self, customer_info, flight_id, seat_id, base_price, voucher_code=None, is_hold=False):
        req_fields = ['full_name', 'phone', 'id_card']
        if not all(customer_info.get(field) for field in req_fields):
            return False, "Vui lòng nhập đủ Tên, SĐT và CCCD khách hàng!"

        final_price = base_price
        voucher_id = None
        
        if voucher_code:
            voucher = self.voucher_repo.get_by_code(voucher_code)
            if not voucher: return False, "Mã giảm giá không tồn tại!"
            if voucher['expiry_date'] < datetime.datetime.now(): return False, "Mã giảm giá đã hết hạn!"
            if voucher['used_count'] >= voucher['usage_limit']: return False, "Mã giảm giá đã hết số lượng sử dụng!"
            
            discount_amount = base_price * (float(voucher['discount_percent']) / 100.0)
            if voucher['max_discount'] and discount_amount > voucher['max_discount']:
                discount_amount = voucher['max_discount']
                
            final_price = base_price - discount_amount
            voucher_id = voucher['voucher_id']

        customer_id = self.customer_repo.get_or_create_customer(
            customer_info['full_name'], customer_info.get('email'), customer_info['phone'], customer_info['id_card']
        )
        if not customer_id: return False, "Lỗi khi lưu thông tin khách hàng!"

        return self.ticket_repo.book_ticket_transaction(
            flight_id, customer_id, seat_id, voucher_id, base_price, final_price, is_hold
        )

    def cancel_ticket(self, ticket_id):
        return self.ticket_repo.cancel_ticket(ticket_id)

    def process_payment(self, ticket_id, pay_method):
        return self.ticket_repo.process_held_payment(ticket_id, pay_method)