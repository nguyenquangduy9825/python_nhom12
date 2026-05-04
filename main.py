# main.py
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QButtonGroup)
from PyQt6.QtCore import Qt

from config.database import DatabaseConnection 
from gui.animations import FadingStackedWidget 
from gui.theme import SAAS_DARK_THEME          

from gui.views.login_view import LoginScreen, RegisterScreen, ForgotPasswordScreen, UpgradeScreen
from gui.views.dashboard_view import DashboardScreen
from gui.views.booking_view import BookingScreen
from gui.views.admin_view import AdminScreen
from gui.views.customer_view import CustomerScreen
from gui.views.customer_booking_view import CustomerBookingView 
from gui.views.profile_view import ProfileScreen 

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Airline System - SaaS Professional")
        self.resize(1200, 750)
        
        self.setStyleSheet(SAAS_DARK_THEME) 
        
        # --- CẤU TRÚC LAYOUT CHÍNH ---
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainBackground")
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Biến lưu trữ người dùng hiện tại
        self.current_user = None

        self.setup_sidebar()
        self.setup_content_area()

        # --- KHỞI TẠO CÁC MÀN HÌNH (VIEWS) ---
        self.login_screen = LoginScreen()
        self.dashboard_screen = DashboardScreen()
        self.booking_screen = BookingScreen()       # Dành cho Staff (Index 2)
        self.register_screen = RegisterScreen() 
        self.admin_screen = AdminScreen(None) 
        self.customer_screen = CustomerScreen()
        self.profile_screen = ProfileScreen(None)
        self.forgot_pw_screen = ForgotPasswordScreen() 
        self.upgrade_screen = UpgradeScreen()          
        self.customer_booking_flow = CustomerBookingView(None) # Dành cho User/Guest (Index 9)
        
        self.stacked_widget.addWidget(self.login_screen)            # Index 0
        self.stacked_widget.addWidget(self.dashboard_screen)        # Index 1
        self.stacked_widget.addWidget(self.booking_screen)          # Index 2
        self.stacked_widget.addWidget(self.register_screen)         # Index 3
        self.stacked_widget.addWidget(self.admin_screen)            # Index 4
        self.stacked_widget.addWidget(self.customer_screen)         # Index 5
        self.stacked_widget.addWidget(self.profile_screen)          # Index 6
        self.stacked_widget.addWidget(self.forgot_pw_screen)        # Index 7
        self.stacked_widget.addWidget(self.upgrade_screen)          # Index 8
        self.stacked_widget.addWidget(self.customer_booking_flow)   # Index 9

        # --- TÍN HIỆU TỪ MÀN HÌNH LOGIN ---
        self.login_screen.login_success_signal.connect(self.on_login_success)
        self.login_screen.go_to_register_signal.connect(lambda: self.navigate_to(3, "Đăng ký tài khoản"))
        self.login_screen.go_to_forgot_pw_signal.connect(lambda: self.navigate_to(7, "Quên mật khẩu"))
        self.login_screen.go_to_upgrade_signal.connect(lambda: self.navigate_to(8, "Nâng cấp tài khoản"))
        
        self.register_screen.back_to_login_signal.connect(lambda: self.navigate_to(0, "Login"))
        self.forgot_pw_screen.back_to_login_signal.connect(lambda: self.navigate_to(0, "Login"))
        self.upgrade_screen.back_to_login_signal.connect(lambda: self.navigate_to(0, "Login"))

        # Khởi động ẩn Sidebar
        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        self.stacked_widget.setCurrentIndex(0)

    # ========================================================
    # XÂY DỰNG KHUNG GIAO DIỆN (SIDEBAR & HEADER)
    # ========================================================
    def setup_sidebar(self):
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("SidebarFrame")
        self.sidebar_frame.setFixedWidth(240)
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(5)

        lbl_logo = QLabel("✈️ AIRLINE SAAS")
        lbl_logo.setObjectName("SidebarLogo")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_logo)
        sidebar_layout.addSpacing(20)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_nav_dash = self.create_nav_button("📊 Tổng quan", 1, "Báo cáo Doanh thu & Thống kê")
        self.btn_nav_book = self.create_nav_button("🎟️ Đặt vé", 2, "Tìm kiếm và Đặt vé máy bay")
        self.btn_nav_history = self.create_nav_button("📜 Lịch sử Khách hàng", 5, "Tra cứu giao dịch Khách hàng")
        self.btn_nav_profile = self.create_nav_button("👤 Tài khoản cá nhân", 6, "Quản lý thông tin & Lịch trình")
        self.btn_nav_admin = self.create_nav_button("🛡️ Quản trị (Admin)", 4, "Quản trị Hệ thống Dữ liệu")

        for btn in [self.btn_nav_dash, self.btn_nav_book, self.btn_nav_history, self.btn_nav_profile, self.btn_nav_admin]:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        btn_logout = QPushButton("🚪 Đăng xuất")
        btn_logout.setStyleSheet("background-color: transparent; color: #EF4444; font-weight: bold; padding: 15px; text-align: left; font-size: 14px;")
        btn_logout.clicked.connect(self.handle_logout)
        sidebar_layout.addWidget(btn_logout)

        self.main_layout.addWidget(self.sidebar_frame)

    def create_nav_button(self, text, index, page_title):
        btn = QPushButton(text)
        btn.setObjectName("SidebarMenuBtn")
        btn.setCheckable(True)
        self.nav_group.addButton(btn)
        btn.clicked.connect(lambda: self.navigate_to(index, page_title))
        return btn

    def setup_content_area(self):
        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        self.header_frame.setFixedHeight(65)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        self.lbl_page_title = QLabel("Dashboard")
        self.lbl_page_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC;") 
        
        self.lbl_user_info = QLabel("👤 Khách vãng lai")
        self.lbl_user_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #94A3B8;")

        header_layout.addWidget(self.lbl_page_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_user_info)

        self.stacked_widget = FadingStackedWidget()
        content_layout.addWidget(self.header_frame)
        content_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.content_area)

    # ========================================================
    # XỬ LÝ ĐIỀU HƯỚNG & PHÂN QUYỀN (RBAC)
    # ========================================================
    def navigate_to(self, index, title):
        """Hệ thống tự động chuyển luồng nếu User bấm vào nút Đặt Vé"""
        if index == 2 and self.current_user:
            if self.current_user.role.upper() in ['USER', 'GUEST']:
                index = 9
                title = "Trải nghiệm Đặt vé trực tuyến"

        self.stacked_widget.setCurrentIndex(index)
        self.lbl_page_title.setText(title)

    def on_login_success(self, user_obj):
        self.current_user = user_obj
        self.sidebar_frame.setVisible(True)
        self.header_frame.setVisible(True)
        
        role_vn = {"ADMIN": "Quản trị viên", "STAFF": "Nhân viên", "USER": "Thành viên", "GUEST": "Khách"}
        self.lbl_user_info.setText(f"👤 {user_obj.username} ({role_vn.get(user_obj.role, '')})")

        self.btn_nav_dash.setVisible(False)
        self.btn_nav_admin.setVisible(False)
        self.btn_nav_history.setVisible(False)
        self.btn_nav_profile.setVisible(False)

        role = user_obj.role.upper()
        if role == 'ADMIN':
            self.btn_nav_dash.setVisible(True)
            self.btn_nav_admin.setVisible(True)
            self.btn_nav_history.setVisible(True)
            self.btn_nav_profile.setVisible(True)
            self.btn_nav_dash.setChecked(True) 
            self.navigate_to(1, "Báo cáo Doanh thu & Thống kê")
            
        elif role == 'STAFF':
            self.btn_nav_history.setVisible(True)
            self.btn_nav_profile.setVisible(True)
            self.btn_nav_book.setChecked(True) 
            self.navigate_to(2, "Nghiệp vụ Đặt vé & Tra cứu")
            
        elif role == 'USER':
            self.btn_nav_profile.setVisible(True)
            self.btn_nav_book.setChecked(True)
            self.navigate_to(9, "Trải nghiệm Đặt vé trực tuyến")
            
        elif role == 'GUEST':
            self.btn_nav_book.setChecked(True)
            self.navigate_to(9, "Trải nghiệm Đặt vé trực tuyến")

        # Cập nhật context cho các màn hình
        self.dashboard_screen.apply_role_permissions(user_obj)
        self.admin_screen.current_user = user_obj 
        self.booking_screen.apply_role_permissions(user_obj)   
        self.customer_screen.apply_role_permissions(user_obj)  
        self.customer_booking_flow.current_user = user_obj
        
        self.profile_screen.current_user = user_obj
        self.profile_screen.refresh_user_info()

    def handle_logout(self):
        self.current_user = None
        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        self.stacked_widget.setCurrentIndex(0) 

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    DatabaseConnection.initialize_pool()
    window = MainAppWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()