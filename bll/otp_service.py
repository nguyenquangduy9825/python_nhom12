import random
import datetime
from dal.auth_dao import AuthDAO, OtpDAO
import hashlib

class OTPService:
    def __init__(self):
        self.auth_dao = AuthDAO()
        self.otp_dao = OtpDAO()

    def generate_otp(self):
        """Tạo mã 6 số random"""
        return str(random.randint(100000, 999999))

    def request_reset_password(self, identifier):
        """Yêu cầu cấp mã OTP cho username/email"""
        # Kiểm tra user có tồn tại không
        user = self.auth_dao.get_user(identifier)
        if not user:
            return False, "Tài khoản không tồn tại trong hệ thống!"

        # Tạo mã và set hạn 5 phút
        otp_code = self.generate_otp()
        expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        if self.otp_dao.save_otp(identifier, otp_code, expiry):
            # Trong thực tế: Code gửi Email/SMS sẽ nằm ở đây
            print(f"[MÔ PHỎNG GỬI EMAIL] Mã OTP của {identifier} là: {otp_code}")
            return True, "Mã OTP đã được gửi đến email/sđt của bạn!"
            
        return False, "Không thể tạo mã OTP!"

    def verify_otp(self, identifier, otp_code):
        """Kiểm tra OTP có hợp lệ không"""
        otp_record = self.otp_dao.get_valid_otp(identifier, otp_code)
        if not otp_record:
            return False, "Mã OTP không chính xác, đã sử dụng hoặc đã hết hạn!"
        return True, "Xác thực OTP thành công!"

    def reset_password(self, identifier, otp_code, new_password):
        """Đổi mật khẩu nếu OTP chuẩn"""
        # Xác thực lại lần cuối cho chắc chắn
        otp_record = self.otp_dao.get_valid_otp(identifier, otp_code)
        if not otp_record:
            return False, "Giao dịch không hợp lệ!"

        # Đổi mật khẩu
        hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()
        success = self.auth_dao.update_password(identifier, hashed_pw)

        if success:
            # Hủy hiệu lực của OTP này
            self.otp_dao.mark_otp_used(otp_record['otp_id'])
            return True, "Khôi phục mật khẩu thành công!"
            
        return False, "Đổi mật khẩu thất bại!"