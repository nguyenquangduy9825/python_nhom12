# gui/views/login_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox, QFormLayout)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from bll.auth_service import AuthService
from bll.otp_service import OTPService

# ==========================================
# 1. MÀN HÌNH ĐĂNG NHẬP (LOGIN & GUEST)
# ==========================================
class LoginScreen(QWidget):
    login_success_signal = pyqtSignal(object) 
    go_to_register_signal = pyqtSignal()
    go_to_forgot_pw_signal = pyqtSignal()
    go_to_upgrade_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.setup_ui()
        self.setup_clock()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        clock_layout = QHBoxLayout(); clock_layout.addStretch()
        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("font-size: 14px; font-weight: bold; color: #94A3B8; padding: 10px;")
        clock_layout.addWidget(self.lbl_clock); main_layout.addLayout(clock_layout)

        center_layout = QVBoxLayout(); center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        frame = QFrame()
        frame.setObjectName("SaaSCard") # Bắt CSS từ theme.py
        frame.setFixedWidth(420)
        form_layout = QVBoxLayout(frame)
        form_layout.setContentsMargins(32, 32, 32, 32)
        form_layout.setSpacing(16)

        lbl_title = QLabel("✈️ AIRLINE SYSTEM")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #E2E8F0; margin-bottom: 10px;")
        
        self.txt_user = QLineEdit(); self.txt_user.setPlaceholderText("Tên đăng nhập")
        
        # --- KHUNG PASSWORD CÓ NÚT MẮT ---
        pass_frame = QFrame()
        pass_frame.setObjectName("PasswordFrame")
        pass_layout = QHBoxLayout(pass_frame)
        pass_layout.setContentsMargins(0, 0, 8, 0)
        
        self.txt_pass = QLineEdit(); self.txt_pass.setPlaceholderText("Mật khẩu"); self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet("border: none; background: transparent;") # Xóa viền mặc định
        
        self.btn_eye = QPushButton("👁")
        self.btn_eye.setFixedWidth(30); self.btn_eye.setCheckable(True)
        self.btn_eye.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #94A3B8;")
        self.btn_eye.clicked.connect(lambda: self.txt_pass.setEchoMode(QLineEdit.EchoMode.Normal if self.btn_eye.isChecked() else QLineEdit.EchoMode.Password))
        
        pass_layout.addWidget(self.txt_pass); pass_layout.addWidget(self.btn_eye)

        # Nút Đăng nhập & Đăng nhập Khách
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("🔑 Đăng Nhập")
        self.btn_login.setObjectName("BtnPrimary")
        self.btn_login.clicked.connect(self.handle_login)

        self.btn_guest = QPushButton("🚶 Đăng Nhập Khách")
        self.btn_guest.clicked.connect(self.handle_guest_login)
        
        btn_layout.addWidget(self.btn_login); btn_layout.addWidget(self.btn_guest)

        # Các Link điều hướng
        links_layout = QVBoxLayout()
        self.btn_register = QPushButton("📝 Chưa có tài khoản? Đăng ký ngay")
        self.btn_register.setObjectName("BtnLink")
        self.btn_forgot = QPushButton("❓ Quên mật khẩu?")
        self.btn_forgot.setObjectName("BtnLink")
        self.btn_forgot.setStyleSheet("color: #EF4444;") # Highlight đỏ
        self.btn_upgrade = QPushButton("🌟 Khách hàng cũ? Nâng cấp lên Tài khoản")
        self.btn_upgrade.setObjectName("BtnLink")
        self.btn_upgrade.setStyleSheet("color: #F59E0B;") # Highlight cam
        
        self.btn_register.clicked.connect(self.go_to_register_signal.emit)
        self.btn_forgot.clicked.connect(self.go_to_forgot_pw_signal.emit)
        self.btn_upgrade.clicked.connect(self.go_to_upgrade_signal.emit)

        links_layout.addWidget(self.btn_forgot); links_layout.addWidget(self.btn_register); links_layout.addWidget(self.btn_upgrade)

        form_layout.addWidget(lbl_title)
        form_layout.addWidget(QLabel("Username:")); form_layout.addWidget(self.txt_user)
        form_layout.addWidget(QLabel("Password:")); form_layout.addWidget(pass_frame)
        form_layout.addSpacing(10); form_layout.addLayout(btn_layout); form_layout.addSpacing(10); form_layout.addLayout(links_layout)

        center_layout.addWidget(frame); main_layout.addLayout(center_layout)
        
        main_layout.addStretch()
        lbl_student = QLabel("Nguyễn Quốc Khánh - 20233456")
        lbl_student.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_student.setStyleSheet("color: #475569; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(lbl_student)

    def setup_clock(self):
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_time); self.timer.start(1000); self.update_time()

    def update_time(self):
        self.lbl_clock.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy  hh:mm:ss"))

    def handle_login(self):
        user_obj, message = self.auth_service.login(self.txt_user.text().strip(), self.txt_pass.text().strip())
        if user_obj:
            QMessageBox.information(self, "Thành công", message)
            self.txt_pass.clear() 
            self.login_success_signal.emit(user_obj) 
        else:
            QMessageBox.warning(self, "Lỗi Đăng Nhập", message)

    def handle_guest_login(self):
        guest_obj, message = self.auth_service.login_guest()
        QMessageBox.information(self, "Chế độ Khách", message)
        self.login_success_signal.emit(guest_obj)

# ==========================================
# 2. MÀN HÌNH ĐĂNG KÝ (REGISTER)
# ==========================================
class RegisterScreen(QWidget):
    back_to_login_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.btn_back = QPushButton("⬅ Quay lại Login")
        self.btn_back.setObjectName("BtnLink")
        self.btn_back.clicked.connect(self.back_to_login_signal.emit)
        top_layout.addWidget(self.btn_back); top_layout.addStretch(); main_layout.addLayout(top_layout)

        center_layout = QVBoxLayout(); center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame = QFrame()
        frame.setObjectName("SaaSCard")
        frame.setFixedWidth(420)
        form_layout = QFormLayout(frame)
        form_layout.setContentsMargins(32, 32, 32, 32)
        form_layout.setSpacing(16)

        lbl_title = QLabel("📝 ĐĂNG KÝ TÀI KHOẢN")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #10B981; margin-bottom: 15px;")
        
        self.txt_user = QLineEdit()
        
        pass_frame = QFrame()
        pass_frame.setObjectName("PasswordFrame")
        pass_layout = QHBoxLayout(pass_frame)
        pass_layout.setContentsMargins(0, 0, 8, 0)
        self.txt_pass = QLineEdit(); self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet("border: none; background: transparent;")
        self.btn_eye_reg = QPushButton("👁"); self.btn_eye_reg.setFixedWidth(30); self.btn_eye_reg.setCheckable(True)
        self.btn_eye_reg.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #94A3B8;")
        self.btn_eye_reg.clicked.connect(lambda: self.txt_pass.setEchoMode(QLineEdit.EchoMode.Normal if self.btn_eye_reg.isChecked() else QLineEdit.EchoMode.Password))
        pass_layout.addWidget(self.txt_pass); pass_layout.addWidget(self.btn_eye_reg)

        self.txt_phone = QLineEdit(); self.txt_cccd = QLineEdit()

        self.btn_register = QPushButton("✅ Xác nhận Đăng Ký")
        self.btn_register.setObjectName("BtnSuccess")
        self.btn_register.clicked.connect(self.handle_register)

        form_layout.addRow(lbl_title)
        form_layout.addRow("Username (*):", self.txt_user)
        form_layout.addRow("Password (*):", pass_frame)
        form_layout.addRow("Số Điện Thoại:", self.txt_phone)
        form_layout.addRow("CCCD:", self.txt_cccd)
        form_layout.addRow(self.btn_register)

        center_layout.addWidget(frame); main_layout.addLayout(center_layout); main_layout.addStretch()

    def handle_register(self):
        u, p = self.txt_user.text().strip(), self.txt_pass.text().strip()
        phone, cccd = self.txt_phone.text().strip(), self.txt_cccd.text().strip()

        success, message = self.auth_service.register(u, p, phone, cccd)
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.txt_user.clear(); self.txt_pass.clear(); self.txt_phone.clear(); self.txt_cccd.clear()
            self.back_to_login_signal.emit()
        else:
            QMessageBox.warning(self, "Lỗi Đăng Ký", message)


# ==========================================
# 3. QUÊN MẬT KHẨU & OTP
# ==========================================
class ForgotPasswordScreen(QWidget):
    back_to_login_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.otp_service = OTPService()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.btn_back = QPushButton("⬅ Quay lại Login")
        self.btn_back.setObjectName("BtnLink")
        self.btn_back.clicked.connect(self.back_to_login_signal.emit)
        top_layout.addWidget(self.btn_back); top_layout.addStretch(); main_layout.addLayout(top_layout)

        center_layout = QVBoxLayout(); center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame = QFrame()
        frame.setObjectName("SaaSCard")
        frame.setFixedWidth(420)
        form_layout = QVBoxLayout(frame)
        form_layout.setContentsMargins(32, 32, 32, 32)
        form_layout.setSpacing(16)

        lbl_title = QLabel("🔒 QUÊN MẬT KHẨU")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #EF4444; margin-bottom: 15px;")
        
        step1_layout = QHBoxLayout()
        self.txt_identifier = QLineEdit(); self.txt_identifier.setPlaceholderText("Nhập Username của bạn")
        self.btn_req_otp = QPushButton("Gửi OTP")
        self.btn_req_otp.setObjectName("BtnPrimary")
        self.btn_req_otp.clicked.connect(self.handle_request_otp)
        step1_layout.addWidget(self.txt_identifier); step1_layout.addWidget(self.btn_req_otp)

        self.txt_otp = QLineEdit(); self.txt_otp.setPlaceholderText("Nhập mã OTP 6 số"); self.txt_otp.setEnabled(False)
        
        pass_frame = QFrame()
        pass_frame.setObjectName("PasswordFrame")
        pass_layout = QHBoxLayout(pass_frame)
        pass_layout.setContentsMargins(0, 0, 8, 0)
        self.txt_new_pass = QLineEdit(); self.txt_new_pass.setPlaceholderText("Mật khẩu mới"); self.txt_new_pass.setEchoMode(QLineEdit.EchoMode.Password); self.txt_new_pass.setEnabled(False)
        self.txt_new_pass.setStyleSheet("border: none; background: transparent;")
        
        self.btn_eye_forgot = QPushButton("👁"); self.btn_eye_forgot.setFixedWidth(30); self.btn_eye_forgot.setCheckable(True); self.btn_eye_forgot.setEnabled(False)
        self.btn_eye_forgot.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #94A3B8;")
        self.btn_eye_forgot.clicked.connect(lambda: self.txt_new_pass.setEchoMode(QLineEdit.EchoMode.Normal if self.btn_eye_forgot.isChecked() else QLineEdit.EchoMode.Password))
        
        pass_layout.addWidget(self.txt_new_pass); pass_layout.addWidget(self.btn_eye_forgot)
        
        self.btn_reset = QPushButton("✅ Xác nhận Đổi Mật Khẩu")
        self.btn_reset.setObjectName("BtnSuccess")
        self.btn_reset.setEnabled(False)
        self.btn_reset.clicked.connect(self.handle_reset_password)

        form_layout.addWidget(lbl_title)
        form_layout.addWidget(QLabel("Bước 1: Lấy mã xác thực")); form_layout.addLayout(step1_layout)
        form_layout.addSpacing(10)
        form_layout.addWidget(QLabel("Bước 2: Xác nhận OTP")); form_layout.addWidget(self.txt_otp); form_layout.addWidget(pass_frame)
        form_layout.addWidget(self.btn_reset)

        center_layout.addWidget(frame); main_layout.addLayout(center_layout); main_layout.addStretch()

    def handle_request_otp(self):
        ident = self.txt_identifier.text().strip()
        if not ident: return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Username!")
        
        success, msg = self.otp_service.request_reset_password(ident)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.txt_otp.setEnabled(True); self.txt_new_pass.setEnabled(True); self.btn_eye_forgot.setEnabled(True); self.btn_reset.setEnabled(True)
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def handle_reset_password(self):
        ident = self.txt_identifier.text().strip()
        otp = self.txt_otp.text().strip()
        new_pw = self.txt_new_pass.text().strip()

        if not otp or not new_pw: return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ mã OTP và Mật khẩu mới!")

        success, msg = self.otp_service.reset_password(ident, otp, new_pw)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.txt_identifier.clear(); self.txt_otp.clear(); self.txt_new_pass.clear()
            self.txt_otp.setEnabled(False); self.txt_new_pass.setEnabled(False); self.btn_eye_forgot.setEnabled(False); self.btn_reset.setEnabled(False)
            self.back_to_login_signal.emit()
        else:
            QMessageBox.critical(self, "Lỗi", msg)


# ==========================================
# 4. NÂNG CẤP GUEST -> USER
# ==========================================
class UpgradeScreen(QWidget):
    back_to_login_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.btn_back = QPushButton("⬅ Quay lại Login")
        self.btn_back.setObjectName("BtnLink")
        self.btn_back.clicked.connect(self.back_to_login_signal.emit)
        top_layout.addWidget(self.btn_back); top_layout.addStretch(); main_layout.addLayout(top_layout)

        center_layout = QVBoxLayout(); center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame = QFrame()
        frame.setObjectName("SaaSCard")
        frame.setFixedWidth(450)
        form_layout = QFormLayout(frame)
        form_layout.setContentsMargins(32, 32, 32, 32)
        form_layout.setSpacing(16)

        lbl_title = QLabel("🌟 NÂNG CẤP TÀI KHOẢN")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F59E0B; margin-bottom: 10px;")
        lbl_desc = QLabel("Nhập đúng SĐT/CCCD bạn từng đặt vé để đồng bộ lịch sử!")
        lbl_desc.setStyleSheet("color: #94A3B8; font-style: italic; margin-bottom: 15px;")
        
        self.txt_user = QLineEdit()
        
        pass_frame = QFrame()
        pass_frame.setObjectName("PasswordFrame")
        pass_layout = QHBoxLayout(pass_frame)
        pass_layout.setContentsMargins(0, 0, 8, 0)
        self.txt_pass = QLineEdit(); self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet("border: none; background: transparent;")
        self.btn_eye_upg = QPushButton("👁"); self.btn_eye_upg.setFixedWidth(30); self.btn_eye_upg.setCheckable(True)
        self.btn_eye_upg.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #94A3B8;")
        self.btn_eye_upg.clicked.connect(lambda: self.txt_pass.setEchoMode(QLineEdit.EchoMode.Normal if self.btn_eye_upg.isChecked() else QLineEdit.EchoMode.Password))
        pass_layout.addWidget(self.txt_pass); pass_layout.addWidget(self.btn_eye_upg)

        self.txt_fullname = QLineEdit(); self.txt_phone = QLineEdit(); self.txt_cccd = QLineEdit()

        self.btn_upgrade = QPushButton("🚀 Nâng cấp & Đồng bộ vé")
        self.btn_upgrade.setStyleSheet("background-color: #F59E0B; color: white;")
        self.btn_upgrade.clicked.connect(self.handle_upgrade)

        form_layout.addRow(lbl_title); form_layout.addRow(lbl_desc)
        form_layout.addRow("Username mới (*):", self.txt_user)
        form_layout.addRow("Password (*):", pass_frame)
        form_layout.addRow("Họ và Tên (*):", self.txt_fullname)
        form_layout.addRow("SĐT từng đặt vé (*):", self.txt_phone)
        form_layout.addRow("CCCD từng đặt vé (*):", self.txt_cccd)
        form_layout.addRow(self.btn_upgrade)

        center_layout.addWidget(frame); main_layout.addLayout(center_layout); main_layout.addStretch()

    def handle_upgrade(self):
        u, p = self.txt_user.text().strip(), self.txt_pass.text().strip()
        name, phone, cccd = self.txt_fullname.text().strip(), self.txt_phone.text().strip(), self.txt_cccd.text().strip()

        if not all([u, p, name, phone, cccd]):
            return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin để đối chiếu lịch sử!")

        success, msg = self.auth_service.upgrade_guest_to_user(u, p, name, phone, cccd)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.txt_user.clear(); self.txt_pass.clear(); self.txt_fullname.clear(); self.txt_phone.clear(); self.txt_cccd.clear()
            self.back_to_login_signal.emit()
        else:
            QMessageBox.warning(self, "Thất bại", msg)