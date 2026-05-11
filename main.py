# main.py
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QButtonGroup)
from PyQt6.QtCore import Qt

from config.database import DatabaseConnection 
from gui.animations import FadingStackedWidget 
from gui.theme import SAAS_DARK_THEME          

# Import Views
from gui.views.login_view import LoginScreen, RegisterScreen, ForgotPasswordScreen
from gui.views.dashboard_view import DashboardScreen
from gui.views.booking_view import BookingScreen
from gui.views.admin_view import AdminScreen
from gui.views.customer_view import CustomerScreen  
from gui.views.customer_booking_view import CustomerBookingView 
from gui.views.profile_view import ProfileScreen 
from gui.views.advanced_booking_views import FlightTicketsView, TicketTypeManagerView, SeatSelectionView

try:
    from bll.hold_service import SeatHoldCleanerWorker
except ImportError:
    SeatHoldCleanerWorker = None

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Airline System")
        self.resize(1280, 800)
        self.setStyleSheet(SAAS_DARK_THEME) 
        
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainBackground")
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.current_user = None

        self.setup_sidebar()
        self.setup_content_area()

        # Khởi tạo màn hình
        self.login_screen = LoginScreen()
        self.dashboard_screen = DashboardScreen()
        self.booking_screen = BookingScreen(None)   
        self.register_screen = RegisterScreen() 
        self.admin_screen = AdminScreen(None) 
        self.customer_screen = CustomerScreen(None) 
        self.profile_screen = ProfileScreen(None)
        self.forgot_pw_screen = ForgotPasswordScreen() 
        self.customer_booking_flow = CustomerBookingView(None) 
        
        self.flight_tickets_view = FlightTicketsView()
        self.ticket_type_view = TicketTypeManagerView()
        self.seat_selection_view = SeatSelectionView()
        
        # Thêm vào StackedWidget
        self.stacked_widget.addWidget(self.login_screen)            # 0
        self.stacked_widget.addWidget(self.dashboard_screen)        # 1
        self.stacked_widget.addWidget(self.booking_screen)          # 2
        self.stacked_widget.addWidget(self.register_screen)         # 3
        self.stacked_widget.addWidget(self.admin_screen)            # 4
        self.stacked_widget.addWidget(self.customer_screen)         # 5
        self.stacked_widget.addWidget(self.profile_screen)          # 6
        self.stacked_widget.addWidget(self.forgot_pw_screen)        # 7
        self.stacked_widget.addWidget(self.customer_booking_flow)   # 8
        self.stacked_widget.addWidget(self.flight_tickets_view)     # 9
        self.stacked_widget.addWidget(self.ticket_type_view)        # 10
        self.stacked_widget.addWidget(self.seat_selection_view)     # 11

        self.login_screen.login_success_signal.connect(self.on_login_success)
        self.login_screen.go_to_register_signal.connect(lambda: self.navigate_to(3, "Đăng ký tài khoản"))
        self.login_screen.go_to_forgot_pw_signal.connect(lambda: self.navigate_to(7, "Quên mật khẩu"))
        
        # Lắng nghe sự kiện khách bấm nút "Đặt vé nhanh"
        self.login_screen.continue_as_guest_signal.connect(self.start_guest_mode)
        
        self.register_screen.back_to_login_signal.connect(lambda: self.navigate_to(0, "Login"))
        self.forgot_pw_screen.back_to_login_signal.connect(lambda: self.navigate_to(0, "Login"))

        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        self.stacked_widget.setCurrentIndex(0)

        # Bot dọn dẹp ghế
        if SeatHoldCleanerWorker:
            self.cleaner_worker = SeatHoldCleanerWorker()

    def start_guest_mode(self):
        self.current_user = None
        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        self.stacked_widget.setCurrentIndex(8)

    def setup_sidebar(self):
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("SidebarFrame")
        self.sidebar_frame.setFixedWidth(260)
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        lbl_logo = QLabel("✈️ AIRLINE")
        lbl_logo.setObjectName("SidebarLogo")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_logo)
        sidebar_layout.addSpacing(10)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.btn_nav_dash = self.create_nav_button("📊 Tổng quan", 1, "Báo cáo Doanh thu & Thống kê")
        self.btn_nav_book = self.create_nav_button("🎟️ Đặt vé", 2, "Nghiệp vụ Đặt vé")
        self.btn_nav_seat = self.create_nav_button("💺 Sơ đồ chuyến bay", 11, "Quản lý Sơ đồ Ghế ngồi")
        self.btn_nav_flight_tkt = self.create_nav_button("📋 Danh sách Vé / Chuyến", 9, "Quản lý Danh sách Hành khách")
        self.btn_nav_tkt_type = self.create_nav_button("🏷️ Quản lý Loại vé", 10, "Thiết lập Hạng Vé & Giá")
        self.btn_nav_history = self.create_nav_button("📜 Quản lý Hành Khách", 5, "Tra cứu giao dịch Khách hàng")
        self.btn_nav_admin = self.create_nav_button("🛡️ Quản trị (Admin)", 4, "Quản trị Hệ thống Dữ liệu")
        self.btn_nav_profile = self.create_nav_button("👤 Tài khoản cá nhân", 6, "Quản lý thông tin & Lịch trình")

        nav_buttons = [
            self.btn_nav_dash, self.btn_nav_book, self.btn_nav_seat, 
            self.btn_nav_flight_tkt, self.btn_nav_tkt_type, 
            self.btn_nav_history, self.btn_nav_admin, self.btn_nav_profile
        ]

        for btn in nav_buttons:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        btn_logout = QPushButton("🚪 Đăng xuất")
        btn_logout.setStyleSheet("background-color: transparent; color: #EF4444; font-weight: bold; padding: 15px 24px; text-align: left;")
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
        self.header_frame.setFixedHeight(70)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(32, 0, 32, 0)
        
        self.lbl_page_title = QLabel("Dashboard")
        self.lbl_page_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC;") 
        
        self.lbl_user_info = QLabel("👤 Hệ thống")
        self.lbl_user_info.setStyleSheet("font-size: 14px; font-weight: 600; color: #94A3B8;")

        header_layout.addWidget(self.lbl_page_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_user_info)

        self.stacked_widget = FadingStackedWidget()
        content_layout.addWidget(self.header_frame)
        content_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.content_area)

    def navigate_to(self, index, title):
        if index == 2 and self.current_user:
            role = getattr(self.current_user, 'role', '') if not isinstance(self.current_user, dict) else self.current_user.get('role', '')
            if role.upper() == 'USER':
                index = 8
                title = "Trải nghiệm Đặt vé trực tuyến"

        self.stacked_widget.setCurrentIndex(index)
        self.lbl_page_title.setText(title)

    def on_login_success(self, user_obj):
        self.current_user = user_obj
        
        raw_role = getattr(user_obj, 'role', 'USER') if not isinstance(user_obj, dict) else user_obj.get('role', 'USER')
        role = str(raw_role).upper().strip() if raw_role else 'USER'
        
        if role not in ['ADMIN', 'STAFF', 'USER']:
            role = 'USER'
            
        username = getattr(user_obj, 'username', 'Unknown') if not isinstance(user_obj, dict) else user_obj.get('username', 'Unknown')
        
        role_vn = {"ADMIN": "Quản trị viên", "STAFF": "Nhân viên", "USER": "Thành viên"}
        self.lbl_user_info.setText(f"👤 {username} ({role_vn[role]})")

        self.sidebar_frame.setVisible(True)
        self.header_frame.setVisible(True)

        for btn in self.nav_group.buttons():
            btn.setVisible(False)

        if role == 'ADMIN':
            for btn in self.nav_group.buttons():
                btn.setVisible(True)
            self.btn_nav_dash.setChecked(True) 
            self.navigate_to(1, "Báo cáo Doanh thu & Thống kê")
            
        elif role == 'STAFF':
            self.btn_nav_book.setVisible(True)
            self.btn_nav_seat.setVisible(True)
            self.btn_nav_flight_tkt.setVisible(True)
            self.btn_nav_history.setVisible(True)
            self.btn_nav_profile.setVisible(True)
            self.btn_nav_book.setChecked(True) 
            self.navigate_to(2, "Nghiệp vụ Đặt vé & Tra cứu")
            
        elif role == 'USER':
            self.btn_nav_book.setVisible(True)
            self.btn_nav_profile.setVisible(True)
            
            try:
                self.btn_nav_book.clicked.disconnect()
            except TypeError:
                pass 
                
            self.btn_nav_book.clicked.connect(lambda: self.navigate_to(8, "Trải nghiệm Đặt vé trực tuyến"))
            self.btn_nav_book.setChecked(True)
            self.navigate_to(8, "Trải nghiệm Đặt vé trực tuyến")

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