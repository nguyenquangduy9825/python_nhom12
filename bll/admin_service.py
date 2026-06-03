# bll/admin_service.py
import hashlib
from dal.admin_repositories import (
    AdminUserRepository, 
    AdminAirportRepository, 
    AdminVoucherRepository, 
    AdminReportRepository,
    AdminAircraftRepository,
    AdminTimekeepingRepository
)

class AdminService:
    def __init__(self):
        self.user_repo = AdminUserRepository()
        self.airport_repo = AdminAirportRepository() 
        self.voucher_repo = AdminVoucherRepository()
        self.report_repo = AdminReportRepository() 
        self.aircraft_repo = AdminAircraftRepository() 
        self.timekeeping_repo = AdminTimekeepingRepository()

    def _is_authorized_admin(self, current_user):
        if not current_user: return False
        role = current_user.get('role', '').upper() if isinstance(current_user, dict) else getattr(current_user, 'role', '').upper()
        return role == 'ADMIN'

    # ==========================================
    # QUẢN LÝ NGƯỜI DÙNG
    # ==========================================
    def search_users(self, keyword=""): return self.user_repo.search_users(keyword)
    def create_user(self, username, password, role, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT: Chỉ ADMIN mới được tạo tài khoản!"
        if not username or not password: return False, "Vui lòng nhập đầy đủ Username và Password!"
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if self.user_repo.create(username, password_hash, role): return True, f"Đã tạo tài khoản {username} thành công!"
        return False, "Username đã tồn tại!"
    def update_user(self, user_id, password, role, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT: Chỉ ADMIN mới được cập nhật!"
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest() if password else None
        if self.user_repo.update(user_id, password_hash, role): return True, "Cập nhật tài khoản thành công!"
        return False, "Lỗi cập nhật CSDL."
    def delete_user(self, user_id, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT: Chỉ ADMIN!"
        current_id = current_user.get('user_id') if isinstance(current_user, dict) else getattr(current_user, 'user_id', None)
        if str(current_id) == str(user_id): return False, "Không thể tự xóa chính tài khoản bạn đang đăng nhập!"
        if self.user_repo.delete(user_id): return True, "Đã xóa tài khoản vĩnh viễn!"
        return False, "Lỗi: Người dùng này đang liên kết với dữ liệu hệ thống."

    # ==========================================
    # QUẢN LÝ SÂN BAY
    # ==========================================
    def get_all_airports(self): return self.airport_repo.get_all()
    def create_airport(self, airport_code, name, city, country, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT!"
        if self.airport_repo.create(airport_code, name, city, country): return True, "Thêm sân bay thành công!"
        return False, "Mã sân bay đã tồn tại!"
    def update_airport(self, airport_code, name, city, country, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT!"
        if self.airport_repo.update(airport_code, name, city, country): return True, "Cập nhật thành công!"
        return False, "Lỗi cập nhật CSDL."
    def delete_airport(self, airport_code, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT!"
        if self.airport_repo.delete(airport_code): return True, "Xóa sân bay thành công!"
        return False, "Sân bay này đang hoạt động, không thể xóa!"

    # ==========================================
    # QUẢN LÝ VOUCHER & THỐNG KÊ
    # ==========================================
    def get_all_vouchers(self): return self.voucher_repo.get_all()
    
    def create_voucher(self, code, discount_percent, max_discount, expiry_date, usage_limit, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT!"
        if float(discount_percent) <= 0 or float(discount_percent) > 100: return False, "Giảm giá phải từ 1% - 100%!"
        if self.voucher_repo.create(code, discount_percent, max_discount, expiry_date, usage_limit): return True, "Tạo Voucher thành công!"
        return False, "Mã Voucher đã tồn tại!"
        
    def update_voucher(self, code, discount_percent, max_discount, expiry_date, usage_limit, current_user):
        """BỔ SUNG: Xử lý cập nhật Voucher"""
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT!"
        if float(discount_percent) <= 0 or float(discount_percent) > 100: return False, "Giảm giá phải từ 1% - 100%!"
        if self.voucher_repo.update(code, discount_percent, max_discount, expiry_date, usage_limit): return True, "Cập nhật Voucher thành công!"
        return False, "Lỗi cập nhật CSDL!"
        
    def disable_voucher(self, code, current_user):
        if not self._is_authorized_admin(current_user): return False, "LỖI BẢO MẬT!"
        if self.voucher_repo.deactivate(code): return True, f"Đã khóa Voucher {code} thành công!"
        return False, "Lỗi hệ thống."

    def get_revenue(self, from_date, to_date): return True, self.report_repo.get_revenue(from_date, to_date)
    def get_top_routes(self): return True, self.report_repo.get_top_routes()

    # ==========================================
    # QUẢN LÝ MÁY BAY & SƠ ĐỒ GHẾ
    # ==========================================
    def get_all_aircrafts(self): return self.aircraft_repo.get_all_aircrafts()
    def create_aircraft(self, name, manufacturer, total_seats): return self.aircraft_repo.create_aircraft(name, manufacturer, total_seats)
    def get_all_seat_classes(self): return self.aircraft_repo.get_all_seat_classes()
    def get_seat_templates(self, aircraft_id): return self.aircraft_repo.get_seat_templates(aircraft_id)
    def save_seat_templates(self, aircraft_id, templates): return self.aircraft_repo.save_seat_templates(aircraft_id, templates)

    # ==========================================
    # CHỨC NĂNG CÁ NHÂN (CHẤM CÔNG & ĐỔI MK)
    # ==========================================
    def change_password(self, user_id, old_password, new_password):
        old_hash = hashlib.sha256(old_password.encode('utf-8')).hexdigest()
        new_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        return self.user_repo.change_password(user_id, old_hash, new_hash)
    def record_check_in(self, user_id): return self.timekeeping_repo.check_in(user_id)
    def record_check_out(self, user_id): return self.timekeeping_repo.check_out(user_id)
    def get_timekeeping_history(self, user_id): return self.timekeeping_repo.get_history(user_id)