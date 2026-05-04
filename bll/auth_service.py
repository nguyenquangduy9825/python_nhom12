# bll/auth_service.py
import hashlib
from dal.auth_dao import AuthDAO
from dal.booking_repositories import CustomerRepository
from models.user import User

class AuthService:
    def __init__(self):
        self.auth_dao = AuthDAO()
        self.customer_repo = CustomerRepository()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # ==========================================
    # 1. LOGIN & REGISTER
    # ==========================================
    def login(self, username, password):
        user_data = self.auth_dao.get_user(username)
        if not user_data:
            return None, "Tài khoản không tồn tại!"
            
        if user_data['password_hash'] != self.hash_password(password):
            return None, "Sai mật khẩu!"
            
        logged_user = User(
            user_id=user_data['user_id'], 
            username=user_data['username'], 
            role=user_data['role'],
            customer_id=user_data.get('customer_id')
        )
        return logged_user, "Đăng nhập thành công!"

    def register(self, username, password, phone, id_card):
        if self.auth_dao.get_user(username):
            return False, "Username đã được sử dụng!"
            
        hashed_pw = self.hash_password(password)
        new_id = self.auth_dao.create_user(username, hashed_pw, role='GUEST', customer_id=None)
        
        if new_id:
            return True, "Đăng ký thành công! Bạn đang ở quyền GUEST."
        return False, "Lỗi hệ thống!"

    # ==========================================
    # 2. GUEST MODE
    # ==========================================
    def login_guest(self):
        guest_session = User(
            user_id=None, 
            username="Khách Vãng Lai", 
            role="GUEST", 
            customer_id=None
        )
        return guest_session, "Bạn đang truy cập với tư cách Khách!"

    # ==========================================
    # 3. UPGRADE GUEST -> USER
    # ==========================================
    def upgrade_guest_to_user(self, username, password, full_name, phone, id_card):
        if self.auth_dao.get_user(username):
            return False, "Username đã tồn tại, vui lòng chọn tên khác!"

        customer_id = self.customer_repo.get_or_create_customer(full_name, "", phone, id_card)
        if not customer_id:
            return False, "Lỗi xử lý dữ liệu định danh!"

        hashed_pw = self.hash_password(password)
        new_user_id = self.auth_dao.create_user(username, hashed_pw, role='USER', customer_id=customer_id)
        
        if new_user_id:
            return True, "Nâng cấp thành công! Toàn bộ lịch sử vé đã được đồng bộ vào tài khoản của bạn."
        return False, "Lỗi khi tạo tài khoản!"

    # ==========================================
    # 4. ĐỔI MẬT KHẨU TẠI PROFILE (HÀM ĐÃ BỔ SUNG LẠI)
    # ==========================================
    def change_password(self, user_id, old_pw, new_pw, confirm_pw):
        """Xử lý đổi mật khẩu cho user đang đăng nhập"""
        if not old_pw or not new_pw or not confirm_pw:
            return False, "Vui lòng điền đầy đủ thông tin!"
            
        if new_pw != confirm_pw:
            return False, "Mật khẩu mới và mật khẩu xác nhận không khớp!"
            
        # Lấy thông tin user hiện tại để đối chiếu mật khẩu cũ
        user = self.auth_dao.get_user_by_id(user_id)
        if not user or user['password_hash'] != self.hash_password(old_pw):
            return False, "Mật khẩu cũ không chính xác!"
            
        # Cập nhật mật khẩu mới xuống CSDL
        if self.auth_dao.update_password_by_id(user_id, self.hash_password(new_pw)):
            return True, "Cập nhật mật khẩu thành công!"
            
        return False, "Lỗi khi cập nhật cơ sở dữ liệu!"