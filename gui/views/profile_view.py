# gui/views/profile_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QFormLayout)
from bll.booking_service import BookingService

class ProfileScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.booking_service = BookingService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        lbl_title = QLabel("👤 TÀI KHOẢN & LỊCH TRÌNH CÁ NHÂN")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3B82F6;")
        layout.addWidget(lbl_title)

        # Thông tin
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1E293B; border-radius: 12px; padding: 10px;")
        info_layout = QFormLayout(info_frame)
        
        self.lbl_username = QLabel()
        self.lbl_username.setStyleSheet("font-weight: bold; color: #10B981; font-size: 16px;")
        self.txt_fullname = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_phone = QLineEdit()
        self.txt_idcard = QLineEdit()

        btn_update = QPushButton("💾 Cập nhật thông tin")
        btn_update.setObjectName("BtnSuccess")
        btn_update.clicked.connect(self.handle_update_profile)

        info_layout.addRow("Tên Đăng Nhập:", self.lbl_username)
        info_layout.addRow("Tra cứu bằng SĐT/CCCD:", self.txt_phone)
        info_layout.addRow("Họ và Tên:", self.txt_fullname)
        info_layout.addRow("Email:", self.txt_email)
        info_layout.addRow("CCCD (Kết quả):", self.txt_idcard)
        
        btn_layout = QHBoxLayout()
        btn_load = QPushButton("Tra cứu Lịch trình")
        btn_load.clicked.connect(lambda: self.handle_load_profile(self.txt_phone.text().strip()))
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_update)
        info_layout.addRow("", btn_layout)

        layout.addWidget(info_frame)
        layout.addSpacing(20)

        # Lịch sử
        lbl_history = QLabel("📜 Lịch sử Chuyến bay")
        lbl_history.setStyleSheet("font-size: 16px; font-weight: bold; color: #F59E0B;")
        layout.addWidget(lbl_history)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Mã Vé", "Chuyến bay", "Khởi hành", "Hạ cánh", "Ghế (Hạng)", "Giá cuối", "Trạng thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def refresh_user_info(self):
        if not self.current_user: return
        username = getattr(self.current_user, 'username', '') if not isinstance(self.current_user, dict) else self.current_user.get('username', '')
        self.lbl_username.setText(username)

    def handle_load_profile(self, keyword):
        if not keyword:
            return QMessageBox.warning(self, "Chú ý", "Vui lòng nhập SĐT hoặc CCCD của bạn để tra cứu lịch trình!")
            
        info, history = self.booking_service.search_customer(keyword)
        if info:
            self.txt_fullname.setText(info['full_name'])
            self.txt_email.setText(info.get('email', ''))
            self.txt_phone.setText(info['phone'])
            self.txt_idcard.setText(info['id_card'])
            self.current_customer_id = info['customer_id']
        else:
            self.current_customer_id = None
            self.table.setRowCount(0)
            return QMessageBox.information(self, "Không tìm thấy", "Không có lịch sử đặt vé nào với SĐT/CCCD này.")
        
        self.table.setRowCount(0)
        for r, t in enumerate(history):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(t['ticket_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(f"{t['flight_number']} ({t['departure_code']}->{t['arrival_code']})"))
            self.table.setItem(r, 2, QTableWidgetItem(str(t['departure_time'])))
            self.table.setItem(r, 3, QTableWidgetItem(str(t['arrival_time'])))
            self.table.setItem(r, 4, QTableWidgetItem(f"{t['seat_number']} ({t['class_name']})"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{t['final_price']:,.0f} đ"))
            self.table.setItem(r, 6, QTableWidgetItem(t['status']))

    def handle_update_profile(self):
        if not hasattr(self, 'current_customer_id') or not self.current_customer_id:
            return QMessageBox.warning(self, "Lỗi", "Vui lòng tra cứu hồ sơ trước khi cập nhật!")
        
        full_name = self.txt_fullname.text().strip()
        email = self.txt_email.text().strip()
        
        success, msg = self.booking_service.update_customer_info(self.current_customer_id, full_name, email)
        if success:
            QMessageBox.information(self, "Thành công", msg)
        else:
            QMessageBox.warning(self, "Lỗi", msg)