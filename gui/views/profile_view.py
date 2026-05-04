# gui/views/profile_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QTabWidget, QFormLayout, QGroupBox)
from PyQt6.QtCore import Qt
from bll.auth_service import AuthService
from bll.booking_service import BookingService

class ProfileScreen(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.auth_service = AuthService()
        self.booking_service = BookingService()
        self.current_customer_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        self.tabs = QTabWidget()
        
        self.tab_account = QWidget(); self.setup_account_tab()
        self.tabs.addTab(self.tab_account, "🔐 Đổi Mật Khẩu")

        self.tab_profile = QWidget(); self.setup_profile_tab()
        self.tabs.addTab(self.tab_profile, "🎫 Lịch Trình Chuyến Bay")

        layout.addWidget(self.tabs)

    def setup_account_tab(self):
        layout = QVBoxLayout(self.tab_account)
        layout.setContentsMargins(24, 24, 24, 24)
        
        form = QFormLayout()
        
        self.lbl_username = QLabel()
        self.lbl_username.setStyleSheet("font-weight: bold; color: #10B981; font-size: 16px;")
        
        self.txt_old_pw = QLineEdit(); self.txt_old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new_pw = QLineEdit(); self.txt_new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm_pw = QLineEdit(); self.txt_confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Tên Đăng Nhập:", self.lbl_username)
        form.addRow("Mật khẩu hiện tại:", self.txt_old_pw)
        form.addRow("Mật khẩu mới:", self.txt_new_pw)
        form.addRow("Xác nhận MK mới:", self.txt_confirm_pw)

        btn_change_pw = QPushButton("Cập nhật Mật Khẩu")
        btn_change_pw.setStyleSheet("background-color: #F59E0B; color: white;")
        btn_change_pw.clicked.connect(self.handle_change_password)

        layout.addLayout(form); layout.addWidget(btn_change_pw); layout.addStretch()

    def setup_profile_tab(self):
        layout = QVBoxLayout(self.tab_profile)
        layout.setContentsMargins(16, 24, 16, 16)

        # Liên kết SĐT
        search_layout = QHBoxLayout()
        self.txt_search_phone = QLineEdit()
        self.txt_search_phone.setPlaceholderText("Nhập SĐT hoặc CCCD để liên kết hồ sơ vé của bạn...")
        btn_search = QPushButton("🔍 Liên kết & Tra cứu")
        btn_search.setObjectName("BtnPrimary")
        btn_search.clicked.connect(self.handle_load_profile)
        search_layout.addWidget(self.txt_search_phone); search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)

        # Cập nhật Thông tin
        group_info = QGroupBox("Cập nhật Thông tin Hành khách")
        form_info = QFormLayout(group_info)
        form_info.setContentsMargins(16, 24, 16, 16)
        
        self.txt_full_name = QLineEdit()
        self.txt_email = QLineEdit()
        self.lbl_id_card = QLabel("---") # CCCD không cho phép tự đổi
        
        btn_update_info = QPushButton("Lưu Thông Tin")
        btn_update_info.setObjectName("BtnSuccess")
        btn_update_info.clicked.connect(self.handle_update_info)

        form_info.addRow("Họ và Tên (*):", self.txt_full_name)
        form_info.addRow("Email:", self.txt_email)
        form_info.addRow("Số CCCD định danh:", self.lbl_id_card)
        form_info.addRow("", btn_update_info)
        layout.addWidget(group_info)

        # Bảng chi tiết chuyến bay
        self.table_tickets = QTableWidget(0, 8)
        self.table_tickets.setHorizontalHeaderLabels(["Mã Vé", "Mã Chuyến", "Tuyến", "Hạng Ghế", "Số Ghế", "Cất Cánh", "Hạ Cánh", "Trạng Thái"])
        self.table_tickets.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_tickets.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_tickets.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # --- FIX: Tắt cột đen và viền lưới ---
        self.table_tickets.verticalHeader().setVisible(False)
        self.table_tickets.setShowGrid(False)
        
        layout.addWidget(self.table_tickets)

    def refresh_user_info(self):
        if self.current_user:
            self.lbl_username.setText(self.current_user.username)
            self.txt_old_pw.clear(); self.txt_new_pw.clear(); self.txt_confirm_pw.clear()
            self.txt_search_phone.clear(); self.txt_full_name.clear(); self.txt_email.clear()
            self.lbl_id_card.setText("---")
            self.table_tickets.setRowCount(0)
            self.current_customer_id = None

    def handle_change_password(self):
        success, msg = self.auth_service.change_password(
            self.current_user.user_id, self.txt_old_pw.text(), self.txt_new_pw.text(), self.txt_confirm_pw.text()
        )
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.txt_old_pw.clear(); self.txt_new_pw.clear(); self.txt_confirm_pw.clear()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def handle_load_profile(self):
        keyword = self.txt_search_phone.text().strip()
        if not keyword: return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập SĐT/CCCD!")
        
        info, history = self.booking_service.search_customer(keyword)
        if not info: return QMessageBox.information(self, "Thông báo", "Không tìm thấy hồ sơ hành khách!")
            
        self.current_customer_id = info['customer_id']
        self.txt_full_name.setText(info['full_name'])
        self.txt_email.setText(info.get('email', ''))
        self.lbl_id_card.setText(info['id_card'])

        self.table_tickets.setRowCount(0)
        for row, t in enumerate(history):
            self.table_tickets.insertRow(row)
            self.table_tickets.setItem(row, 0, QTableWidgetItem(str(t['ticket_id'])))
            self.table_tickets.setItem(row, 1, QTableWidgetItem(t['flight_number']))
            self.table_tickets.setItem(row, 2, QTableWidgetItem(f"{t['departure_code']} ➔ {t['arrival_code']}"))
            self.table_tickets.setItem(row, 3, QTableWidgetItem(t['class_name']))
            self.table_tickets.setItem(row, 4, QTableWidgetItem(t['seat_number']))
            self.table_tickets.setItem(row, 5, QTableWidgetItem(str(t['departure_time'])))
            self.table_tickets.setItem(row, 6, QTableWidgetItem(str(t['arrival_time'])))
            
            status_item = QTableWidgetItem(t['status'])
            if t['status'] == 'CANCELLED': status_item.setForeground(Qt.GlobalColor.red)
            elif t['status'] == 'BOOKED': status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table_tickets.setItem(row, 7, status_item)

    def handle_update_info(self):
        if not self.current_customer_id: return QMessageBox.warning(self, "Lỗi", "Vui lòng tra cứu hồ sơ trước!")
        full_name = self.txt_full_name.text().strip()
        if not full_name: return QMessageBox.warning(self, "Lỗi", "Họ tên không được để trống!")
        
        success, msg = self.booking_service.update_customer_info(self.current_customer_id, full_name, self.txt_email.text().strip())
        if success: QMessageBox.information(self, "Thành công", msg)
        else: QMessageBox.warning(self, "Lỗi", msg)