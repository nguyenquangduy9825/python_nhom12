# bll/admin_service.py
from dal.admin_repositories import AdminUserRepository, AdminFlightRepository, AdminVoucherRepository, AdminReportRepository, AdminAirportRepository

class AdminService:
    def __init__(self):
        self.user_repo = AdminUserRepository()
        self.flight_repo = AdminFlightRepository()
        self.voucher_repo = AdminVoucherRepository()
        self.report_repo = AdminReportRepository()
        self.airport_repo = AdminAirportRepository() 

    # --- USER, FLIGHT ---
    def get_all_users(self): return self.user_repo.get_all()
    
    def update_user_role(self, user_id, new_role): 
        return self.user_repo.update_role(user_id, new_role.upper()), "Thành công"
        
    def delete_user(self, target_user_id, current_admin_id):
        if str(target_user_id) == str(current_admin_id): return False, "Không thể tự xóa tài khoản Admin đang đăng nhập!"
        if self.user_repo.delete(target_user_id): return True, "Xóa tài khoản thành công!"
        return False, "Không thể xóa, tài khoản đang có ràng buộc dữ liệu."
    
    def get_all_flights(self): return self.flight_repo.get_all_flights()
    
    def create_flight(self, flight_data):
        seats_data = [{'number': f'A{i}', 'class_id': 2} for i in range(1, 21)] + [{'number': f'B{i}', 'class_id': 1} for i in range(1, 81)]
        if self.flight_repo.create_with_seats(flight_data, seats_data): return True, "Thành công!"
        return False, "Trùng mã chuyến hoặc lỗi dữ liệu!"
        
    def update_flight(self, flight_id, data):
        if self.flight_repo.update(flight_id, data): return True, "Cập nhật thành công!"
        return False, "Lỗi cập nhật!"
        
    def delete_flight(self, flight_id):
        if self.flight_repo.check_has_tickets(flight_id): return False, "Đã có người đặt vé, không thể xóa!"
        if self.flight_repo.delete(flight_id): return True, "Xóa thành công!"
        return False, "Lỗi khi xóa!"

    # --- AIRPORT ---
    def get_all_airports(self):
        return self.airport_repo.get_all()
    
    def add_airport(self, code, name, city, country):
        if len(code) != 3: return False, "Mã sân bay phải đúng 3 ký tự (VD: HAN)!"
        if self.airport_repo.add(code, name, city, country): return True, "Thêm sân bay thành công!"
        return False, "Mã sân bay đã tồn tại!"

    def delete_airport(self, code):
        if self.airport_repo.delete(code): return True, "Xóa sân bay thành công!"
        return False, "Sân bay này đang có chuyến bay hoạt động, không thể xóa!"

    # --- VOUCHER ---
    def get_all_vouchers(self):
        return self.voucher_repo.get_all()

    def create_voucher(self, code, discount, max_discount, expiry, limit):
        if discount <= 0 or discount > 100: return False, "Giảm giá phải từ 1% - 100%!"
        if self.voucher_repo.create(code, discount, max_discount, expiry, limit): return True, "Tạo thành công!"
        return False, "Mã Voucher đã tồn tại!"
        
    def disable_voucher(self, code):
        if self.voucher_repo.deactivate(code): return True, f"Đã khóa Voucher {code} thành công!"
        return False, "Không tìm thấy Voucher hoặc lỗi hệ thống!"

    # --- REPORTS ---
    def get_revenue(self, from_date, to_date):
        if from_date > to_date: return False, "Ngày bắt đầu không được lớn hơn ngày kết thúc!"
        return True, self.report_repo.get_revenue(from_date, to_date)

    def get_top_routes(self):
        return self.report_repo.get_top_routes()