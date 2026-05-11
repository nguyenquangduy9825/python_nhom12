# bll/booking_service.py
import re
from datetime import datetime
from dal.group_booking_repository import GroupBookingRepository

class BookingService:
    def __init__(self):
        self.repo = GroupBookingRepository()

    def get_airports_combo(self):
        return [f"{a['city']} ({a['airport_code']})" for a in self.repo.get_airports()]

    def search_flights(self, dep_text, arr_text, date_str):
        d_code = re.search(r'\(([A-Z]{3})\)', dep_text).group(1) if '(' in dep_text else (dep_text if dep_text.strip() else None)
        a_code = re.search(r'\(([A-Z]{3})\)', arr_text).group(1) if '(' in arr_text else (arr_text if arr_text.strip() else None)
        
        if d_code and a_code and d_code == a_code: return False, "Điểm đi và đến trùng nhau!", []
        
        flights = self.repo.search_flights(d_code, a_code, date_str if date_str.strip() else None)
        if flights: return True, "OK", flights
        return False, "Chưa có chuyến bay nào được mở bán.", []

    def fetch_seat_map(self, flight_id):
        return self.repo.get_seat_map(flight_id)

    def apply_voucher(self, code, raw_total):
        v = self.repo.validate_voucher(code)
        if not v: return False, "Voucher không tồn tại!", 0, None
        if v['used_count'] >= v['usage_limit']: return False, "Voucher hết lượt!", 0, None
        if v['expiry_date'] < datetime.now(): return False, "Voucher hết hạn!", 0, None
        
        disc = raw_total * (float(v['discount_percent']) / 100.0)
        if v['max_discount'] and disc > float(v['max_discount']): disc = float(v['max_discount'])
        return True, "Áp dụng thành công", disc, v['voucher_id']

    def validate_and_book_group(self, group_info: dict, passengers: list, is_hold: bool):
        if not group_info['contact_name'] or not group_info['contact_phone']:
            return False, "Thiếu thông tin người liên hệ!", ""
        
        if len(passengers) == 0: return False, "Chưa chọn ghế nào!", ""
        for p in passengers:
            if not p['name'] or not p['id_card']:
                return False, f"Hành khách ghế {p['seat_number']} thiếu Tên hoặc CCCD (*)", ""
            if len(p['id_card']) < 9:
                return False, f"CCCD ghế {p['seat_number']} không hợp lệ!", ""

        return self.repo.commit_group_booking(group_info, passengers, is_hold)

    def confirm_payment_for_held(self, booking_code):
        return self.repo.confirm_payment_for_held(booking_code)

    def get_all_available_flights(self):
        return self.repo.get_all_available_flights()

    def get_flight_seats(self, flight_id):
        return self.repo.get_seat_map(flight_id)

    def search_passengers(self, keyword: str):
        return self.repo.search_passengers(keyword)

    def cancel_ticket(self, ticket_id: int, role: str):
        if role.upper() != 'ADMIN':
            return False, "Bạn không có quyền! Chỉ Admin mới được phép hủy vé."
        if self.repo.cancel_ticket(ticket_id):
            return True, "Hủy vé thành công! Ghế trống đã được trả lại sơ đồ."
        return False, "Lỗi: Không thể hủy vé này."

    def get_class_multiplier(self, class_name: str) -> float:
        return self.repo.get_class_multiplier(class_name)

    def lookup_tickets(self, keyword: str):
        """Logic Tra cứu vé & báo cáo số liệu cho Guest"""
        if not keyword: 
            return False, "Vui lòng nhập Mã vé (PNR), SĐT hoặc CCCD.", [], {}
        
        kw = keyword.upper().replace("TKT-", "").strip()
        tkts = self.repo.lookup_ticket(kw)
        
        if not tkts: 
            return False, "Không tìm thấy thông tin vé nào khớp với dữ liệu.", [], {}
            
        stats = {'total': len(tkts), 'spent': 0, 'cancelled': 0}
        
        for t in tkts:
            t['ticket_code'] = f"TKT-{t['ticket_id']}"
            if t['ticket_status'] == 'BOOKED': 
                stats['spent'] += float(t['final_price'])
            elif t['ticket_status'] == 'CANCELLED': 
                stats['cancelled'] += 1
                
        return True, "Thành công", tkts, stats