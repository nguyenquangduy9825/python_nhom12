# bll/customer_service.py
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dal.booking_repositories import BookingRepository, CustomerRepository
from dal.admin_repositories import AdminVoucherRepository
from dal.customer_repository import CustomerBookingRepository

class CustomerService:
    def __init__(self):
        self.booking_repo = BookingRepository()
        self.customer_repo = CustomerRepository()
        self.voucher_repo = AdminVoucherRepository()
        self.customer_booking_repo = CustomerBookingRepository()

    def get_available_flights(self) -> List[Dict]:
        return self.booking_repo.get_all_available_flights()

    def get_formatted_flights(self) -> List[Dict]:
        flights = self.booking_repo.get_all_available_flights()
        for f in flights:
            dep = f.get('dep_city', f.get('departure_code', ''))
            arr = f.get('arr_city', f.get('arrival_code', ''))
            f['route_str'] = f"{dep} ➔ {arr}"
            f['time_str'] = f"{f['departure_time'].strftime('%H:%M')} - {f['arrival_time'].strftime('%H:%M')}"
            f['date_str'] = f['departure_time'].strftime('%d/%m/%Y')
            
            delta = f['arrival_time'] - f['departure_time']
            hours = delta.seconds // 3600
            minutes = (delta.seconds // 60) % 60
            f['duration_str'] = f"{hours}h {minutes}m"
            
            if f['available_seats'] <= 5:
                f['badge'] = "🔥 Sắp hết vé"
                f['badge_color'] = "#EF4444"
            elif float(f['base_price']) <= 1600000:
                f['badge'] = "⭐ Giá tốt"
                f['badge_color'] = "#10B981"
            else:
                f['badge'] = "✈️ Phổ thông"
                f['badge_color'] = "#38BDF8"
                
        return flights

    def search_flights(self, dep_code: str, arr_code: str, date_str: str) -> List[Dict]:
        return self.booking_repo.search_flights(dep_code, arr_code, date_str)

    def get_seat_map(self, flight_id: int) -> List[Dict]:
        return self.booking_repo.get_seat_map(flight_id)

    # Quản lý voucher và trừ tiền tự động
    def get_active_vouchers(self) -> List[Dict]:
        """Cung cấp bảng Vouchers khả dụng lên UI Khách hàng"""
        vouchers = self.voucher_repo.get_all()
        active = []
        now = datetime.now()
        for v in vouchers:
            if v['used_count'] < v['usage_limit'] and v['expiry_date'] > now:
                active.append(v)
        return active

    def validate_voucher(self, voucher_code: str) -> Tuple[bool, str, Optional[Dict]]:
        if not voucher_code: return False, "Vui lòng nhập mã giảm giá!", None
        vouchers = self.voucher_repo.get_all()
        for v in vouchers:
            if v['code'].upper() == voucher_code.strip().upper():
                if v['used_count'] >= v['usage_limit']: return False, "Mã giảm giá đã hết lượt sử dụng!", None
                if v['expiry_date'] < datetime.now(): return False, "Mã giảm giá đã hết hạn!", None
                return True, f"Áp dụng giảm {float(v['discount_percent'])}% thành công!", {
                    "valid": True, "voucher_id": v['voucher_id'],
                    "discount_percent": float(v['discount_percent']),
                    "max_discount": float(v['max_discount']) if v['max_discount'] else float('inf')
                }
        return False, "Mã giảm giá không tồn tại hoặc sai cú pháp!", None

    def calculate_final_price(self, base_price: float, seat_multiplier: float, 
                              baggage_price: float = 0.0, voucher_info: Dict = None) -> Dict:
        if baggage_price is None: baggage_price = 0.0
            
        ticket_price = float(base_price) * float(seat_multiplier)
        total_before_discount = ticket_price + float(baggage_price)
        
        discount_amount = 0.0
        discount_percent = 0.0 
        
        if voucher_info and voucher_info.get('valid'):
            discount_percent = voucher_info['discount_percent']
            raw_discount = ticket_price * (discount_percent / 100.0)
            discount_amount = min(raw_discount, voucher_info['max_discount'])
        
        final_price = total_before_discount - discount_amount
        return {
            "ticket_price": ticket_price,
            "price_after_class": ticket_price, 
            "baggage_price": baggage_price,
            "discount_amount": discount_amount,
            "discount_percent": discount_percent, 
            "final_price": max(final_price, 0) 
        }

    # ==========================================
    # GIAO DỊCH VÀ TRA CỨU
    # ==========================================
    def book_single_ticket(self, name: str, phone: str, id_card: str, email: str, 
                           flight: Dict, seat: Dict, voucher_code: str, is_hold: bool) -> Tuple[bool, str]:
        voucher_info = None
        voucher_id = None
        if voucher_code:
            ok, _, v_info = self.validate_voucher(voucher_code)
            if ok and v_info:
                voucher_info = v_info
                voucher_id = v_info['voucher_id']

        pricing = self.calculate_final_price(float(flight['base_price']), float(seat['price_multiplier']), 0.0, voucher_info)
        booking_data = {
            'flight_id': flight['flight_id'], 'full_name': name, 'phone': phone, 'id_card': id_card,
            'email': email, 'seat_id': seat['seat_id'], 'base_price': float(flight['base_price']),
            'final_price': pricing['final_price'], 'voucher_id': voucher_id
        }
        return self.process_customer_booking(booking_data, is_hold)

    def process_customer_booking(self, booking_data: Dict, is_hold: bool = False) -> Tuple[bool, str]:
        req_keys = ['full_name', 'phone', 'id_card', 'flight_id', 'seat_id', 'base_price', 'final_price']
        for k in req_keys:
            if k not in booking_data or not booking_data[k]: return False, f"Vui lòng điền đầy đủ thông tin bắt buộc (*)."
        customer_id = self.customer_repo.get_or_create(booking_data['full_name'], booking_data['phone'], booking_data['id_card'], booking_data.get('email', ''))
        booking_data['customer_id'] = customer_id
        return self.booking_repo.process_ticket_transaction(booking_data, is_hold)

    def process_payment(self, ticket_id: int, pay_method: str) -> Tuple[bool, str]:
        return self.booking_repo.process_held_payment(ticket_id, pay_method)

    def lookup_my_ticket(self, pnr: str, phone: str) -> Tuple[bool, str, Optional[Dict]]:
        ticket = self.customer_booking_repo.lookup_strict(pnr, phone)
        if ticket: return True, "Thành công", ticket
        return False, "Không tìm thấy vé! Vui lòng kiểm tra lại mã PNR và SĐT.", None

    def cancel_my_ticket(self, pnr: str, phone: str) -> Tuple[bool, str]:
        return self.customer_booking_repo.cancel_ticket_strict(pnr, phone)