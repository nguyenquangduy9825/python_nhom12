# bll/admin_service.py
import hashlib
from dal.admin_repositories import AdminUserRepository, AdminFlightRepository, AdminVoucherRepository, AdminReportRepository, AdminAirportRepository

class AdminService:
    def __init__(self):
        self.user_repo = AdminUserRepository()
        self.flight_repo = AdminFlightRepository()
        self.voucher_repo = AdminVoucherRepository()
        self.report_repo = AdminReportRepository()
        self.airport_repo = AdminAirportRepository() 

    def _verify_admin(self, current_user_obj):
        if not current_user_obj: return False
        role = current_user_obj.get('role', '').upper() if isinstance(current_user_obj, dict) else getattr(current_user_obj, 'role', '').upper()
        return role == 'ADMIN'

    # --- USER LOGIC ---
    def search_users(self, keyword=""):
        if not keyword: return self.user_repo.get_all()
        return self.user_repo.search_users(keyword)
    
    def create_user(self, username, password, role, current_user_obj):
        if not self._verify_admin(current_user_obj): 
            return False, "LỖI BẢO MẬT: Chỉ ADMIN mới được tạo tài khoản!"
        if not username or not password:
            return False, "Vui lòng nhập đầy đủ Username và Password!"
            
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if self.user_repo.create_user(username, password_hash, role.upper()):
            return True, f"Đã tạo thành công tài khoản: {username} ({role})!"
        return False, "Username đã tồn tại trong hệ thống!"
    
    def update_user_role(self, user_id, new_role, current_user_obj): 
        if not self._verify_admin(current_user_obj): return False, "⛔ LỖI BẢO MẬT: STAFF không được sửa quyền User!"
        return self.user_repo.update_role(user_id, new_role.upper()), "Cập nhật quyền thành công!"
        
    def delete_user(self, target_user_id, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI BẢO MẬT: STAFF không được xóa User!"
        current_admin_id = current_user_obj.get('user_id') if isinstance(current_user_obj, dict) else getattr(current_user_obj, 'user_id', -1)
        if str(target_user_id) == str(current_admin_id): 
            return False, "LỖI: Bạn không thể tự xóa tài khoản đang đăng nhập!"

        target_role = self.user_repo.get_role(target_user_id)
        if target_role == 'ADMIN' and self.user_repo.count_admins() <= 1:
            return False, "LỖI: Không thể xóa ADMIN duy nhất của hệ thống!"
            
        if self.user_repo.delete(target_user_id): return True, "Xóa tài khoản thành công!"
        return False, "Lỗi: Tài khoản này đang có dữ liệu ràng buộc!"

    # --- FLIGHT LOGIC & PHÁT HÀNH GHẾ ---
    def get_all_flights(self): 
        return self.flight_repo.get_all_flights()
    
    def create_flight(self, flight_data, current_user_obj, num_business=8, num_economy=60):
        if not self._verify_admin(current_user_obj): 
            return False, "LỖI: Chỉ ADMIN mới được tạo chuyến bay!"
        
        seats_data = []
        
        # Sinh ghế Thương gia (class_id=2): Quy tắc 4 ghế / hàng (A, B, C, D)
        b_rows = (num_business + 3) // 4 
        b_count = 0
        for r in range(1, b_rows + 1):
            for c in ['A', 'B', 'C', 'D']:
                if b_count < num_business:
                    seats_data.append({'seat_number': f'{c}{r}', 'class_id': 2})
                    b_count += 1

        # Sinh ghế Phổ thông (class_id=1): Quy tắc 6 ghế / hàng (A, B, C, D, E, F)
        start_e_row = b_rows + 1  
        e_rows = (num_economy + 5) // 6
        e_count = 0
        for r in range(start_e_row, start_e_row + e_rows):
            for c in ['A', 'B', 'C', 'D', 'E', 'F']:
                if e_count < num_economy:
                    seats_data.append({'seat_number': f'{c}{r}', 'class_id': 1})
                    e_count += 1

        if self.flight_repo.create_with_seats(flight_data, seats_data): 
            return True, f"Thêm chuyến bay và phát hành thành công {b_count + e_count} ghế tự động!"
        return False, "Trùng mã chuyến hoặc lỗi dữ liệu!"
        
    def update_flight(self, flight_id, data, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI: Chỉ ADMIN mới được sửa chuyến bay!"
        if self.flight_repo.update(flight_id, data): return True, "Cập nhật thành công!"
        return False, "Lỗi cập nhật!"
        
    def delete_flight(self, flight_id, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI BẢO MẬT: STAFF không được phép xóa chuyến!"
        if self.flight_repo.check_has_tickets(flight_id): return False, "Đã có người đặt vé, không thể xóa!"
        if self.flight_repo.delete(flight_id): return True, "Xóa thành công!"
        return False, "Lỗi khi xóa!"

    # --- AIRPORT & VOUCHER ---
    def get_all_airports(self): return self.airport_repo.get_all()
    
    def add_airport(self, code, name, city, country, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI BẢO MẬT: Chỉ ADMIN!"
        if len(code) != 3: return False, "Mã sân bay phải đúng 3 ký tự (VD: HAN)!"
        if self.airport_repo.add(code, name, city, country): return True, "Thêm sân bay thành công!"
        return False, "Mã sân bay đã tồn tại!"

    def delete_airport(self, code, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI BẢO MẬT: Chỉ ADMIN!"
        if self.airport_repo.delete(code): return True, "Xóa sân bay thành công!"
        return False, "Sân bay này đang có chuyến bay hoạt động, không thể xóa!"

    def get_all_vouchers(self): return self.voucher_repo.get_all()

    def create_voucher(self, code, discount, max_discount, expiry, limit, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI BẢO MẬT: Chỉ ADMIN!"
        if discount <= 0 or discount > 100: return False, "Giảm giá phải từ 1% - 100%!"
        if self.voucher_repo.create(code, discount, max_discount, expiry, limit): return True, "Tạo thành công!"
        return False, "Mã Voucher đã tồn tại!"
        
    def disable_voucher(self, code, current_user_obj):
        if not self._verify_admin(current_user_obj): return False, "LỖI BẢO MẬT: Chỉ ADMIN!"
        if self.voucher_repo.deactivate(code): return True, f"Đã khóa Voucher {code} thành công!"
        return False, "Không tìm thấy Voucher!"

    # --- REPORTS ---
    def get_revenue(self, from_date, to_date):
        if from_date > to_date: return False, "Ngày bắt đầu lớn hơn kết thúc!"
        return True, self.report_repo.get_revenue(from_date, to_date)

    def get_top_routes(self): 
        return self.report_repo.get_top_routes()