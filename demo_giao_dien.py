import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView)
from PyQt6.QtCore import Qt

class LoginScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window 
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        title = QLabel("ĐẠI LÝ BÁN VÉ MÁY BAY")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Nhập tài khoản")
        self.txt_user.setFixedWidth(300)

        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Nhập mật khẩu")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setFixedWidth(300)

        btn_login = QPushButton("Đăng nhập")
        btn_login.setFixedWidth(300)

        # Chuyển sang trang chủ
        btn_login.clicked.connect(self.chuyen_sang_dashboard)

        btn_face_id = QPushButton("Đăng nhập bằng Face ID 📷")
        btn_face_id.setStyleSheet("background-color: #10b981; color: white; padding: 5px;")
        btn_face_id.setFixedWidth(300)

        layout.addWidget(title)
        layout.addWidget(self.txt_user)
        layout.addWidget(self.txt_pass)
        layout.addWidget(btn_login)
        layout.addWidget(btn_face_id)
        
        self.setLayout(layout)

    def chuyen_sang_dashboard(self):
        
        self.main_window.stacked_widget.setCurrentIndex(1)

# Trang chủ
class DashboardScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        layout = QVBoxLayout()

        # Thanh Menu ngang ở trên cùng
        menu_layout = QHBoxLayout()
        title = QLabel("TRANG CHỦ - QUẢN LÝ CHUYẾN BAY")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        btn_ban_ve = QPushButton("✈️ Chuyển sang Màn hình Bán vé")
        btn_ban_ve.setStyleSheet("background-color: #eab308; color: black; font-weight: bold;")
        btn_ban_ve.clicked.connect(self.chuyen_sang_ban_ve)

        btn_dang_xuat = QPushButton("Đăng xuất")
        btn_dang_xuat.clicked.connect(lambda: self.main_window.stacked_widget.setCurrentIndex(0))

        menu_layout.addWidget(title)
        menu_layout.addStretch() # các nút về bên phải
        menu_layout.addWidget(btn_ban_ve)
        menu_layout.addWidget(btn_dang_xuat)

        # Bảng dữ liệu chuyến bay
        table = QTableWidget(3, 4) # 3 hàng, 4 cột
        table.setHorizontalHeaderLabels(["Mã Chuyến", "Điểm Đi", "Điểm Đến", "Giờ Bay"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Cột tự giãn đều
        
        # Demo dữ liệu
        table.setItem(0, 0, QTableWidgetItem("VN213"))
        table.setItem(0, 1, QTableWidgetItem("Hà Nội"))
        table.setItem(0, 2, QTableWidgetItem("TP.HCM"))
        table.setItem(0, 3, QTableWidgetItem("08:00 20/04"))

        layout.addLayout(menu_layout)
        layout.addWidget(table)
        self.setLayout(layout)

    def chuyen_sang_ban_ve(self):
        self.main_window.stacked_widget.setCurrentIndex(2)

# Trang bán vé
class BookingScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        layout = QVBoxLayout()

        # Thanh điều hướng
        nav_layout = QHBoxLayout()
        btn_back = QPushButton("⬅ Quay lại Trang chủ")
        btn_back.clicked.connect(lambda: self.main_window.stacked_widget.setCurrentIndex(1))
        nav_layout.addWidget(btn_back)
        nav_layout.addStretch()

        title = QLabel("NGHIỆP VỤ XUẤT VÉ")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        # Form nhập liệu
        self.combo_chuyen_bay = QComboBox()
        self.combo_chuyen_bay.addItems(["Chọn chuyến bay...", "VN213 (HAN-SGN)", "VJ122 (DAD-HAN)"])

        self.txt_ten_khach = QLineEdit()
        self.txt_ten_khach.setPlaceholderText("Họ và tên hành khách...")

        self.txt_cccd = QLineEdit()
        self.txt_cccd.setPlaceholderText("Số CCCD / Passport...")

        self.txt_voucher = QLineEdit()
        self.txt_voucher.setPlaceholderText("Nhập Mã Voucher Giảm Giá (nếu có)...")
        self.txt_voucher.setStyleSheet("border: 1px solid #eab308;")

        btn_xac_nhan = QPushButton("XÁC NHẬN ĐẶT VÉ")
        btn_xac_nhan.setStyleSheet("background-color: #3b82f6; color: white; font-weight: bold; font-size: 16px; padding: 10px;")

        # Đẩy vào layout
        layout.addLayout(nav_layout)
        layout.addWidget(title)
        layout.addWidget(self.combo_chuyen_bay)
        layout.addWidget(self.txt_ten_khach)
        layout.addWidget(self.txt_cccd)
        layout.addWidget(self.txt_voucher)
        layout.addSpacing(20)
        layout.addWidget(btn_xac_nhan)
        layout.addStretch()

        self.setLayout(layout)

# Quản lý các trang
class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phần mềm Quản lý Đại lý Vé Máy bay")
        self.resize(800, 500)

        # QStackedWidget để chứa nhiều trang
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Khởi tạo 3 trang, nhét vào Stack
        self.page_login = LoginScreen(self)
        self.page_dashboard = DashboardScreen(self)
        self.page_booking = BookingScreen(self)

        self.stacked_widget.addWidget(self.page_login)     # Index 0
        self.stacked_widget.addWidget(self.page_dashboard) # Index 1
        self.stacked_widget.addWidget(self.page_booking)   # Index 2

        # Khi mở app thì hiện trang đăng nhập (0)
        self.stacked_widget.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainAppWindow()
    window.show()
    sys.exit(app.exec())