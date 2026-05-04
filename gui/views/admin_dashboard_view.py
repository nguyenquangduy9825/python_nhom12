# gui/views/admin_dashboard_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QTableWidget
from bll.admin_service import AdminService

class AdminDashboardScreen(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user # Đối tượng User (Lấy từ lúc Login)
        self.admin_service = AdminService()
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Ví dụ 1: Button XÓA USER
        self.btn_del_user = QPushButton("Xóa Tài Khoản")
        self.btn_del_user.clicked.connect(self.on_delete_user_click)
        layout.addWidget(self.btn_del_user)

        # Ví dụ 2: Button TẠO CHUYẾN BAY (KÈM AUTO GHẾ)
        self.btn_add_flight = QPushButton("Tạo Chuyến Bay & Auto Sơ đồ Ghế")
        self.btn_add_flight.clicked.connect(self.on_create_flight_click)
        layout.addWidget(self.btn_add_flight)

    # ========================================================
    # XỬ LÝ SỰ KIỆN CLICK THEO CHUẨN CLEAN CODE
    # ========================================================
    def on_delete_user_click(self):
        target_id_to_delete = 5 # Giả sử bạn lấy ID này từ 1 QTableWidget đang được chọn
        
        # Gọi xuống Service, truyền ID cần xóa VÀ ID của Admin đang dùng máy (để chặn tự sát)
        success, message = self.admin_service.delete_user(target_id_to_delete, self.current_user.user_id)
        
        if success:
            QMessageBox.information(self, "Thành công", message)
            # self.reload_table()
        else:
            QMessageBox.critical(self, "Bảo mật & Cảnh báo", message)


    def on_create_flight_click(self):
        # Gom dữ liệu từ các ô QLineEdit, QDateTimeEdit trên Form
        new_flight = {
            'flight_number': 'VN-456',
            'departure_code': 'HAN',
            'arrival_code': 'SGN',
            'departure_time': '2026-10-01 08:00:00',
            'arrival_time': '2026-10-01 10:00:00'
        }
        
        # Service sẽ tự động sinh 100 ghế đính kèm theo chuyến bay này
        success, message = self.admin_service.create_flight(new_flight)
        
        if success:
            QMessageBox.information(self, "Thành công", message)
        else:
            QMessageBox.warning(self, "Lỗi tạo chuyến", message)