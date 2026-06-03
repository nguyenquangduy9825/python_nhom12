# main.py
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QButtonGroup, QSizePolicy)
from PyQt6.QtCore import Qt

from config.database import DatabaseConnection 
from gui.animations import FadingStackedWidget 
from gui.theme import SAAS_DARK_THEME          

# Import các views
from gui.views.login_view import LoginScreen
from gui.views.dashboard_view import DashboardScreen
from gui.views.booking_view import BookingScreen
from gui.views.customer_view import CustomerScreen  
from gui.views.customer_booking_view import CustomerBookingView 
from gui.views.staff_profile_view import StaffProfileScreen  
from gui.views.admin_view import AdminScreen
from gui.views.flight_management_view import FlightManagementScreen
from gui.views.airport_management_view import AirportManagementScreen
from gui.views.voucher_management_view import VoucherManagementScreen
from gui.views.advanced_booking_views import TicketTypeManagerView, SeatSelectionView
from gui.views.aircraft_management_view import AircraftManagementScreen

try:
    from bll.hold_service import SeatHoldCleanerWorker
except ImportError:
    SeatHoldCleanerWorker = None

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Airline Reservation Management System (ARMS)")
        self.resize(1366, 820)
        
        extended_theme = SAAS_DARK_THEME + """
            QMessageBox { background-color: #1E293B; color: white; }
            QMessageBox QLabel { color: white; font-size: 14px; font-weight: bold; }
            QMessageBox QPushButton { background-color: #38BDF8; color: #0F172A; border-radius: 6px; padding: 6px 16px; font-weight: bold; }
            QMessageBox QPushButton:hover { background-color: #0284C7; color: white; }
            QPushButton#SidebarMenuBtn {
                text-align: left; padding: 16px 24px; font-size: 15px; font-weight: 600;
                background-color: transparent; border: none; color: #94A3B8; border-radius: 8px; margin: 2px 12px;
            }
            QPushButton#SidebarMenuBtn:hover { background-color: rgba(255,255,255,0.05); color: #F8FAFC; }
            QPushButton#SidebarMenuBtn:checked { background-color: #38BDF8; color: #0F172A; font-weight: bold; }
        """
        self.setStyleSheet(extended_theme) 
        
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainBackground")
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.current_user = None

        self.setup_sidebar()
        self.setup_content_area()

        # Khởi tạo các màn hình
        self.login_screen = LoginScreen()
        self.dashboard_screen = DashboardScreen(None)
        self.admin_group_booking_screen = BookingScreen(None)   
        self.admin_screen = AdminScreen(None) 
        self.customer_screen = CustomerScreen(None)             
        self.staff_profile_screen = StaffProfileScreen(None)    
        self.guest_booking_flow = CustomerBookingView(None)     
        
        self.flight_management_screen = FlightManagementScreen()
        self.ticket_type_view = TicketTypeManagerView()
        self.seat_selection_view = SeatSelectionView()
        self.airport_management_screen = AirportManagementScreen(None)
        self.voucher_management_screen = VoucherManagementScreen(None)
        self.aircraft_management_screen = AircraftManagementScreen(None)
        
        # Đưa vào stack
        self.stacked_widget.addWidget(self.login_screen)               # Index 0
        self.stacked_widget.addWidget(self.dashboard_screen)           # Index 1
        self.stacked_widget.addWidget(self.admin_group_booking_screen) # Index 2
        self.stacked_widget.addWidget(self.admin_screen)               # Index 3
        self.stacked_widget.addWidget(self.customer_screen)            # Index 4
        self.stacked_widget.addWidget(self.staff_profile_screen)       # Index 5
        self.stacked_widget.addWidget(self.guest_booking_flow)         # Index 6
        self.stacked_widget.addWidget(self.flight_management_screen)   # Index 7
        self.stacked_widget.addWidget(self.ticket_type_view)           # Index 8
        self.stacked_widget.addWidget(self.seat_selection_view)        # Index 9
        self.stacked_widget.addWidget(self.airport_management_screen)  # Index 10
        self.stacked_widget.addWidget(self.voucher_management_screen)  # Index 11
        self.stacked_widget.addWidget(self.aircraft_management_screen) # Index 12
        self.login_screen.login_success_signal.connect(self.on_login_success)
        self.login_screen.continue_as_guest_signal.connect(self.start_guest_mode)

        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        self.stacked_widget.setCurrentIndex(0)

        if SeatHoldCleanerWorker:
            self.cleaner_worker = SeatHoldCleanerWorker()

    def start_guest_mode(self):
        self.current_user = None
        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        self.stacked_widget.setCurrentIndex(6) # Khách vãng lai

    def setup_sidebar(self):
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("SidebarFrame")
        self.sidebar_frame.setFixedWidth(260)
        self.sidebar_frame.setStyleSheet("background-color: #1E293B; border-right: 1px solid #334155;")
        
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(4)

        lbl_logo = QLabel("✈️ AIRLINE SYSTEM")
        lbl_logo.setObjectName("SidebarLogo")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("font-size: 20px; font-weight: 900; color: #38BDF8; margin-bottom: 20px; border:none;")
        sidebar_layout.addWidget(lbl_logo)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        # Khai báo các index
        self.btn_nav_dash = self.create_nav_button("📊 Dashboard Điều hành", 1, "Theo dõi doanh thu, sản lượng vé, hiệu suất khai thác.")
        self.btn_nav_book = self.create_nav_button("🎟️ Quản lý Đặt vé", 2, "Thực hiện đặt chỗ, giữ chỗ, thanh toán tại quầy.")
        self.btn_nav_user_book = self.create_nav_button("🛫 Đặt vé Cá nhân", 6, "Trải nghiệm Đặt vé Trực tuyến")
        self.btn_nav_history = self.create_nav_button("📋 Quản lý Hành khách", 4, "Tra cứu, cập nhật lịch sử đặt vé của hành khách.")
        self.btn_nav_flight_mgt = self.create_nav_button("✈️ Quản lý Chuyến bay", 7, "Cập nhật lịch trình, trạng thái chuyến bay.")
        self.btn_nav_airport_mgt = self.create_nav_button("🗺️ Danh mục Sân bay", 10, "Quản lý mã IATA, địa điểm sân bay.")
        self.btn_nav_aircraft = self.create_nav_button("🛩️ Danh mục Tàu bay", 12, "Cấu hình đội tàu bay và sơ đồ ghế.")
        self.btn_nav_tkt_type = self.create_nav_button("🏷️ Hạng ghế & Giá", 8, "Cấu hình hệ số giá các hạng ghế.")
        self.btn_nav_voucher = self.create_nav_button("🎟️ Khuyến mãi & Voucher", 11, "Phát hành mã giảm giá, chương trình ưu đãi.")
        self.btn_nav_admin = self.create_nav_button("🛡️ Quản lý Người dùng", 3, "Phân quyền tài khoản hệ thống.")
        self.btn_nav_profile = self.create_nav_button("⏰ Hồ sơ & Chấm công", 5, "Ca làm việc & Mật khẩu cá nhân.")

        nav_buttons = [
            self.btn_nav_dash, self.btn_nav_book, self.btn_nav_user_book, 
            self.btn_nav_history, self.btn_nav_flight_mgt, self.btn_nav_airport_mgt,
            self.btn_nav_aircraft, self.btn_nav_tkt_type, self.btn_nav_voucher, 
            self.btn_nav_admin, self.btn_nav_profile
        ]

        for btn in nav_buttons:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        btn_logout = QPushButton("🚪 Đăng xuất")
        btn_logout.setStyleSheet("""
            QPushButton { background-color: transparent; color: #EF4444; font-weight: bold; padding: 15px 24px; text-align: left; border: none; }
            QPushButton:hover { background-color: rgba(239, 68, 68, 0.1); }
        """)
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
        self.header_frame.setStyleSheet("background-color: #0F172A; border-bottom: 1px solid #334155;")
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(32, 0, 32, 0)
        
        self.lbl_page_title = QLabel("Dashboard")
        self.lbl_page_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #F8FAFC; border: none;") 
        
        self.lbl_user_info = QLabel("👤 Hệ thống")
        self.lbl_user_info.setStyleSheet("font-size: 14px; font-weight: 600; color: #94A3B8; border: none;")

        header_layout.addWidget(self.lbl_page_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_user_info)

        self.stacked_widget = FadingStackedWidget()
        content_layout.addWidget(self.header_frame)
        content_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.content_area)

    def navigate_to(self, index, title):
        self.stacked_widget.setCurrentIndex(index)
        self.lbl_page_title.setText(title)

    def on_login_success(self, user_obj):
        self.current_user = user_obj
        
        raw_role = getattr(user_obj, 'role', 'USER') if not isinstance(user_obj, dict) else user_obj.get('role', 'USER')
        role = str(raw_role).upper().strip() if raw_role else 'USER'
        if role not in ['ADMIN', 'STAFF', 'USER']: role = 'USER'
            
        username = getattr(user_obj, 'username', 'Unknown') if not isinstance(user_obj, dict) else user_obj.get('username', 'Unknown')
        
        role_vn = {"ADMIN": "Quản trị viên", "STAFF": "Nhân viên", "USER": "Thành viên"}
        self.lbl_user_info.setText(f"👤 {username} ({role_vn[role]})")

        self.admin_screen.current_user = user_obj
        self.airport_management_screen.current_user = user_obj
        self.voucher_management_screen.current_user = user_obj

        for btn in self.nav_group.buttons():
            btn.setVisible(False)

        if role == 'ADMIN':
            self.sidebar_frame.setVisible(True)
            self.header_frame.setVisible(True)
            for btn in self.nav_group.buttons(): 
                btn.setVisible(True)
            self.btn_nav_user_book.setVisible(False) 
            
            self.btn_nav_dash.setChecked(True) 
            self.navigate_to(1, "Báo cáo Doanh thu & Thống kê")
            
        elif role == 'STAFF':
            self.sidebar_frame.setVisible(True)
            self.header_frame.setVisible(True)
            
            self.btn_nav_book.setVisible(True)       
            self.btn_nav_history.setVisible(True)    
            self.btn_nav_profile.setVisible(True)    
            
            self.btn_nav_book.setChecked(True) 
            self.navigate_to(2, "Nghiệp vụ Đặt vé Nhân viên")
            
        elif role == 'USER':
            self.sidebar_frame.setVisible(False)
            self.header_frame.setVisible(False)
            self.navigate_to(6, "Trải nghiệm Đặt vé trực tuyến")

        if hasattr(self.dashboard_screen, 'apply_role_permissions'):
            self.dashboard_screen.apply_role_permissions(user_obj)
        self.admin_group_booking_screen.apply_role_permissions(user_obj)   
        self.customer_screen.apply_role_permissions(user_obj)  
        self.guest_booking_flow.current_user = user_obj
        self.staff_profile_screen.apply_role_permissions(user_obj)

    def handle_logout(self):
        self.current_user = None
        self.sidebar_frame.setVisible(False)
        self.header_frame.setVisible(False)
        
        if self.nav_group.checkedButton():
            self.nav_group.setExclusive(False)
            self.nav_group.checkedButton().setChecked(False)
            self.nav_group.setExclusive(True)
            
        self.navigate_to(0, "Đăng nhập")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    DatabaseConnection.initialize_pool()
    window = MainAppWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()