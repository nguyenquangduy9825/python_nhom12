# bll/booking_service.py
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dal.group_booking_repository import GroupBookingRepository
from dal.admin_repositories import AdminVoucherRepository

class BookingService:
    def __init__(self):
        self.repo = GroupBookingRepository()
        self.voucher_repo = AdminVoucherRepository()

    def get_all_active_flights(self) -> List[Dict]:
        return self.repo.get_active_flights()

    def get_all_flights_management(self) -> List[Dict]:
        return self.repo.get_all_flights_admin()

    def fetch_seat_map(self, flight_id: int) -> List[Dict]:
        return self.repo.get_flight_seat_map(flight_id)

    def get_active_vouchers(self) -> List[Dict]:
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

    def calculate_final_price(self, base_price: float, seat_multiplier: float, voucher_info: Dict = None) -> Dict:
        ticket_price = float(base_price) * float(seat_multiplier)
        discount_amount = 0.0
        discount_percent = 0.0 
        if voucher_info and voucher_info.get('valid'):
            discount_percent = voucher_info['discount_percent']
            raw_discount = ticket_price * (discount_percent / 100.0)
            discount_amount = min(raw_discount, voucher_info['max_discount'])
        final_price = ticket_price - discount_amount
        return {
            "ticket_price": ticket_price, "discount_amount": discount_amount,
            "discount_percent": discount_percent, "final_price": max(final_price, 0) 
        }

    def get_all_seat_classes(self) -> List[Dict]: return self.repo.get_all_seat_classes()
    def update_seat_class(self, seat_id: int, class_id: int) -> Tuple[bool, str]: return self.repo.update_seat_class(seat_id, class_id)

    def validate_and_process_admin_booking(self, flight_id: int, contact_info: Dict, passengers: List[Dict], is_hold: bool, method: str) -> Tuple[bool, str]:
        if not passengers: return False, "Vui lòng click chọn ít nhất 1 ghế trên sơ đồ máy bay!"
        if len(passengers) > 1:
            if not contact_info.get('name') or not contact_info.get('phone'): return False, "Đặt vé đoàn yêu cầu nhập đầy đủ thông tin Người liên hệ đoàn!"
        for p in passengers:
            if not p.get('name') or not p.get('phone') or not p.get('id_card'): return False, f"Ghế {p['seat_number']} bị thiếu thông tin bắt buộc (*)."
            if not re.match(r"^\d{9,11}$", p['phone']): return False, f"Số điện thoại tại ghế {p['seat_number']} không hợp lệ (yêu cầu 9-11 chữ số)."
        return self.repo.process_admin_booking_flow(flight_id, contact_info, passengers, is_hold, method)

    def search_passengers(self, keyword: str = "") -> List[Dict]: return self.repo.search_passengers(keyword)
    def cancel_ticket(self, ticket_id: int, role: str) -> Tuple[bool, str]:
        if role != 'ADMIN': return False, "Cảnh báo: Chỉ Quản trị viên (ADMIN) mới có quyền hủy vé trực tiếp từ hệ thống!"
        return self.repo.cancel_ticket_admin(ticket_id)

    # Truyền dữ liệu đến chuyến bay
    def create_new_flight(self, data: Dict) -> Tuple[bool, str]:
        if not data['flight_number'] or not data['departure_code'] or not data['arrival_code'] or not data.get('aircraft_type_id'):
            return False, "Vui lòng nhập đầy đủ Số hiệu chuyến bay, Mã sân bay và Loại tàu bay khai thác."
        if len(data['departure_code']) != 3 or len(data['arrival_code']) != 3: return False, "Mã sân bay đi/đến bắt buộc phải gồm đúng 3 ký tự."
        if data['departure_code'].upper() == data['arrival_code'].upper(): return False, "Sân bay cất cánh không được trùng với sân bay hạ cánh!"
        try:
            price = float(data['base_price'])
            if price <= 0: return False, "Giá vé cơ bản phải lớn hơn 0 VNĐ."
        except ValueError: return False, "Giá vé cơ bản không đúng định dạng số lẻ."
        
        return self.repo.insert_flight(
            data['flight_number'], data['departure_code'], data['arrival_code'], 
            data['departure_time'], data['arrival_time'], price, data['status'], 
            int(data['aircraft_type_id']) # Đã cập nhật
        )

    def update_existing_flight(self, flight_id: int, data: Dict) -> Tuple[bool, str]:
        if len(data['departure_code']) != 3 or len(data['arrival_code']) != 3: return False, "Mã sân bay đi/đến bắt buộc phải gồm đúng 3 ký tự."
        try: price = float(data['base_price'])
        except ValueError: return False, "Giá vé không hợp lệ."
        
        ac_id = int(data['aircraft_type_id']) if data.get('aircraft_type_id') else None
        return self.repo.update_flight(
            flight_id, data['flight_number'], data['departure_code'], data['arrival_code'], 
            data['departure_time'], data['arrival_time'], price, data['status'], ac_id
        )

    def delete_existing_flight(self, flight_id: int) -> Tuple[bool, str]:
        return self.repo.delete_flight(flight_id)