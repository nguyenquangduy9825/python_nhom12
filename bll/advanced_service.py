# bll/advanced_service.py
from dal.advanced_repositories import SeatClassRepository, AdminBookingRepository
from typing import List, Dict, Tuple
import re

class AdvancedService:
    def __init__(self):
        self.seat_repo = SeatClassRepository()
        self.booking_repo = AdminBookingRepository()

    # 1. nghiệp vụ bán vé
    def get_all_seat_classes(self) -> List[Dict]:
        return self.seat_repo.get_all()

    def create_seat_class(self, data: Dict) -> Tuple[bool, str]:
        if not data.get('name'): return False, "Tên hạng vé không được bỏ trống."
        try: 
            multiplier = float(data['multiplier'])
        except ValueError: 
            return False, "Hệ số giá không hợp lệ (VD: 1.0, 2.5)."
        
        ok = self.seat_repo.create(data['name'], multiplier, data.get('desc', ''))
        return (True, "Thêm hạng vé thành công!") if ok else (False, "Lỗi thêm hạng vé (Có thể trùng tên).")

    def update_seat_class(self, class_id: int, data: Dict) -> Tuple[bool, str]:
        if not data.get('name'): return False, "Tên hạng vé không được bỏ trống."
        try: 
            multiplier = float(data['multiplier'])
        except ValueError: 
            return False, "Hệ số giá không hợp lệ."

        ok = self.seat_repo.update(class_id, data['name'], multiplier, data.get('desc', ''))
        return (True, "Cập nhật thành công!") if ok else (False, "Lỗi cập nhật hạng vé.")

    def delete_seat_class(self, class_id: int) -> Tuple[bool, str]:
        """Tầng DAL sẽ chịu trách nhiệm kiểm tra xem hạng vé này có đang được dùng bởi ghế nào không"""
        return self.seat_repo.delete(class_id)

    # 2. Quản lý / Nhân viên sẽ đặt vé cho khách qua sơ đồ ghế
    def get_flights_for_admin(self) -> List[Dict]:
        """Hàm chuẩn cấp dữ liệu đầy đủ cho Table và Sơ đồ ghế động"""
        return self.booking_repo.get_all_flights()

    def get_flights_for_combobox(self) -> List[Dict]:
        """Hàm dự phòng tương thích ngược"""
        return self.booking_repo.get_all_flights()

    def get_seat_map(self, flight_id: int) -> List[Dict]:
        return self.booking_repo.get_seat_map(flight_id)

    def process_admin_booking(self, flight_id: int, seat_id: int, cust_data: Dict, pricing: Dict, is_hold: bool, method: str = 'CASH') -> Tuple[bool, str]:
        if not cust_data.get('name') or not cust_data.get('phone') or not cust_data.get('id_card'):
            return False, "Vui lòng nhập đầy đủ Họ Tên, SĐT và CCCD."
        if not re.match(r"^\d{9,11}$", cust_data['phone']):
            return False, "Số điện thoại không hợp lệ (Phải từ 9-11 số)."
            
        return self.booking_repo.create_booking(flight_id, seat_id, cust_data, pricing, is_hold, method)