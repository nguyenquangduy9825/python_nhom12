# gui/views/login_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from PyQt6.QtGui import QCursor, QFont
from bll.auth_service import AuthService

class LoginScreen(QWidget):
    login_success_signal = pyqtSignal(object) 
    continue_as_guest_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.setup_ui()
        self.setup_clock()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; font-family: 'Segoe UI'; }
            QFrame#LoginCard { 
                background-color: #1E293B; 
                border-radius: 16px; 
                border: 1px solid #334155; 
            }
            QLineEdit { 
                padding: 14px 16px; 
                border-radius: 8px; 
                background-color: #0F172A; 
                border: 1px solid #475569; 
                color: white; 
                font-size: 14px; 
            }
            QLineEdit:focus { border: 2px solid #38BDF8; }
            QPushButton#BtnPrimary { 
                background-color: #38BDF8; 
                color: #0F172A; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 14px; 
                font-size: 15px; 
            }
            QPushButton#BtnPrimary:hover { background-color: #0284C7; color: white; }
            QPushButton#BtnFace { 
                background-color: #8B5CF6; 
                color: white; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 14px; 
                font-size: 14px; 
            }
            QPushButton#BtnFace:hover { background-color: #7C3AED; }
            QPushButton#BtnGuest { 
                background-color: transparent; 
                border: 2px solid #10B981; 
                color: #10B981; 
                border-radius: 8px; 
                padding: 14px; 
                font-weight: bold; 
                font-size: 15px; 
            }
            QPushButton#BtnGuest:hover { background-color: #10B981; color: #0F172A; }
        """)

        main_layout = QVBoxLayout(self)
        
        # Đồng hồ ở góc
        clock_layout = QHBoxLayout()
        clock_layout.addStretch()
        self.lbl_clock = QLabel()
        self.lbl_clock.setStyleSheet("font-size: 14px; font-weight: bold; color: #94A3B8; padding: 10px;")
        clock_layout.addWidget(self.lbl_clock)
        main_layout.addLayout(clock_layout)

        # Căn giữa Form
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_frame = QFrame()
        card_frame.setObjectName("LoginCard")
        card_frame.setFixedSize(420, 520)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        lbl_icon = QLabel("✈️")
        lbl_icon.setFont(QFont("Arial", 40))
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("background: transparent;")
        card_layout.addWidget(lbl_icon)

        lbl_title = QLabel("HỆ THỐNG QUẢN TRỊ")
        lbl_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #F8FAFC; background: transparent; letter-spacing: 2px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_title)
        card_layout.addSpacing(10)

        # Form Đăng nhập nội bộ
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Tên đăng nhập nội bộ")
        card_layout.addWidget(self.txt_username)

        # Khung chứa Mật khẩu + Nút xem
        password_frame = QFrame()
        password_layout = QHBoxLayout(password_frame)
        password_layout.setContentsMargins(0, 0, 8, 0)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Mật khẩu")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setStyleSheet("border: none; background: transparent;")
        self.txt_password.returnPressed.connect(self.handle_login)
        
        self.btn_toggle_eye = QPushButton("👁")
        self.btn_toggle_eye.setFixedWidth(30)
        self.btn_toggle_eye.setCheckable(True)
        self.btn_toggle_eye.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #94A3B8;")
        self.btn_toggle_eye.clicked.connect(self.toggle_password_visibility)
        
        password_layout.addWidget(self.txt_password)
        password_layout.addWidget(self.btn_toggle_eye)
        
        # Bọc CSS cho khung password để nó giống QLineEdit
        password_frame.setStyleSheet("""
            QFrame { border-radius: 8px; background-color: #0F172A; border: 1px solid #475569; }
            QFrame:focus-within { border: 2px solid #38BDF8; }
        """)
        card_layout.addWidget(password_frame)

        btn_login = QPushButton("🔑 Đăng Nhập")
        btn_login.setObjectName("BtnPrimary")
        btn_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_login.clicked.connect(self.handle_login)
        card_layout.addWidget(btn_login)

        btn_face_id = QPushButton("📷 Face ID Khu vực")
        btn_face_id.setObjectName("BtnFace")
        btn_face_id.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_face_id.clicked.connect(self.handle_face_login)
        card_layout.addWidget(btn_face_id)

        card_layout.addSpacing(10)
        card_layout.addWidget(QLabel("─── HOẶC ───", styleSheet="color: #475569; background: transparent; font-weight:bold; font-size: 12px;"), alignment=Qt.AlignmentFlag.AlignCenter)

        # Nút Đặt vé nhanh cho Khách hàng
        btn_guest_booking = QPushButton("🚶 ĐẶT VÉ TRỰC TUYẾN NGAY")
        btn_guest_booking.setObjectName("BtnGuest")
        btn_guest_booking.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_guest_booking.clicked.connect(self.continue_as_guest_signal.emit)
        card_layout.addWidget(btn_guest_booking)

        center_layout.addWidget(card_frame)
        main_layout.addLayout(center_layout)

    def toggle_password_visibility(self):
        if self.btn_toggle_eye.isChecked():
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)

    def setup_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        self.lbl_clock.setText(QDateTime.currentDateTime().toString("dd/MM/yyyy  hh:mm:ss"))

    def handle_login(self):
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        
        if not username or not password:
            return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!")
            
        user_obj, message = self.auth_service.login(username, password)
        if user_obj:
            self.txt_password.clear() 
            self.login_success_signal.emit(user_obj) 
        else:
            QMessageBox.critical(self, "Đăng nhập thất bại", message)

    def handle_face_login(self):
        try:
            from gui.faceid.face_login_dialog import FaceLoginDialog
            dialog = FaceLoginDialog(self)
            if dialog.exec() == 1: 
                self.login_success_signal.emit(dialog.logged_in_user)
        except ImportError as e:
            QMessageBox.warning(self, "Chưa cài đặt AI", f"Hệ thống thiếu thư viện AI: {e}\nVui lòng chạy lệnh: pip install opencv-python face-recognition numpy")