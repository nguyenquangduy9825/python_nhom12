# bll/customer_service.py
import re
from datetime import datetime
from typing import Tuple, List, Dict, Optional
from dal.customer_repository import CustomerRepository

class CustomerService:
    def __init__(self):
        self.repo = CustomerRepository()

    def get_airports_for_combo(self) -> List[str]:
        airports = self.repo.get_airports()
        return [f"{a['city']} ({a['airport_code']})" for a in airports]

    def extract_code(self, text: str) -> str:
        match = re.search(r'\(([A-Z]{3})\)', text)
        return match.group(1) if match else text

    def search_flights(self, dep_text: str, arr_text: str, date_str: str) -> Tuple[bool, str, List[Dict]]:
        dep_code = self.extract_code(dep_text)
        arr_code = self.extract_code(arr_text)
        if dep_code == arr_code: 
            return False, "Điểm đi và điểm đến không được trùng nhau!", []
        
        flights = self.repo.search_flights(dep_code, arr_code, date_str)
        if not flights: 
            return False, "Không tìm thấy chuyến bay phù hợp. Vui lòng thử ngày khác.", []
        return True, "Thành công", flights

    def fetch_seat_map(self, flight_id: int) -> List[Dict]:
        seats = self.repo.get_seat_map(flight_id)
        now = datetime.now()
        for s in seats:
            if s['seat_status'] == 'HELD' and s['hold_expired_at'] and s['hold_expired_at'] < now:
                self.repo.release_seat(s['seat_id'])
                s['seat_status'] = 'AVAILABLE'
        return seats

    def calculate_price(self, base: float, mult: float, disc_percent: float = 0, max_disc: float = 0) -> Tuple[float, float, float]:
        raw_price = float(base) * float(mult)
        discount = raw_price * (float(disc_percent) / 100.0)
        if max_disc > 0 and discount > max_disc:
            discount = max_disc
        return raw_price, discount, raw_price - discount

    def apply_voucher(self, code: str, raw_total: float) -> Tuple[bool, str, Dict]:
        v = self.repo.validate_voucher(code)
        if not v: return False, "Mã Voucher không tồn tại!", {}
        if v['used_count'] >= v['usage_limit']: return False, "Voucher đã hết lượt sử dụng!", {}
        if v['expiry_date'] < datetime.now(): return False, "Voucher đã hết hạn!", {}
        return True, "Áp dụng thành công!", v

    def validate_and_hold_seat(self, data: Dict) -> Tuple[bool, str]:
        if not data.get('full_name') or not data.get('phone') or not data.get('id_card'):
            return False, "Vui lòng nhập đủ Họ tên, SĐT, CCCD (*)"
        if not re.match(r"^\d{9,11}$", data['phone']): return False, "SĐT không hợp lệ."
        if not data.get('seat_id'): return False, "Bạn chưa chọn ghế trên sơ đồ!"

        if not self.repo.hold_seat(data['seat_id']):
            return False, "Ghế này vừa bị khách khác chọn, vui lòng chọn ghế khác!"
        return True, "OK"

    def confirm_booking(self, data: Dict, is_hold: bool = False) -> Tuple[bool, str]:
        success, msg, tkt_id = self.repo.confirm_booking_transaction(data, is_hold)
        if success:
            act_msg = "GIỮ CHỖ THÀNH CÔNG" if is_hold else "THANH TOÁN THÀNH CÔNG"
            return True, f"{act_msg}!\nMã PNR của bạn là: TKT-{tkt_id}"
        return False, msg

    def lookup_tickets(self, keyword: str) -> Tuple[bool, str, List[Dict], Dict]:
        if not keyword: return False, "Vui lòng nhập Mã vé (PNR), SĐT hoặc CCCD.", [], {}
        kw = keyword.upper().replace("TKT-", "").strip()
        tkts = self.repo.lookup_ticket(kw)
        if not tkts: return False, "Không tìm thấy thông tin vé nào khớp với dữ liệu.", [], {}
            
        stats = {'total': len(tkts), 'spent': 0, 'cancelled': 0}
        for t in tkts:
            t['ticket_code'] = f"TKT-{t['ticket_id']}"
            if t['status'] == 'BOOKED': stats['spent'] += float(t['final_price'])
            elif t['status'] == 'CANCELLED': stats['cancelled'] += 1
                
        return True, "Thành công", tkts, stats

    def cancel_ticket(self, ticket_id_str: str) -> Tuple[bool, str]:
        tkt_id = int(ticket_id_str.upper().replace("TKT-", "").strip())
        if self.repo.cancel_ticket(tkt_id):
            return True, f"Hủy vé TKT-{tkt_id} thành công. Ghế đã được nhả về hệ thống."
        return False, "Hủy vé thất bại."