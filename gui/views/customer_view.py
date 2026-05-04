# gui/views/customer_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt
from bll.booking_service import BookingService

class CustomerScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.booking_service = BookingService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập Số điện thoại hoặc CCCD...")
        btn_search = QPushButton("🔍 Tìm kiếm")
        btn_search.setObjectName("BtnPrimary")
        btn_search.clicked.connect(self.handle_search_customer)

        search_layout.addWidget(self.txt_search); search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)

        group_info = QGroupBox("Thông tin cá nhân")
        info_layout = QFormLayout(group_info)
        info_layout.setContentsMargins(16, 24, 16, 16)
        
        self.lbl_name = QLabel("---"); self.lbl_phone = QLabel("---")
        self.lbl_email = QLabel("---"); self.lbl_cccd = QLabel("---")
        
        info_layout.addRow("Họ và Tên:", self.lbl_name); info_layout.addRow("Số Điện Thoại:", self.lbl_phone)
        info_layout.addRow("Email:", self.lbl_email); info_layout.addRow("CCCD:", self.lbl_cccd)
        layout.addWidget(group_info)

        group_history = QGroupBox("Lịch sử Đặt vé Chi tiết")
        history_layout = QVBoxLayout(group_history)
        history_layout.setContentsMargins(16, 24, 16, 16)
        
        self.table_history = QTableWidget(0, 9)
        self.table_history.setHorizontalHeaderLabels(["Mã Vé", "Chuyến", "Tuyến", "Hạng", "Ghế", "Cất Cánh", "Hạ Cánh", "Giá", "Trạng Thái"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # --- FIX: Tắt cột đen và viền lưới ---
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setShowGrid(False)
        
        history_layout.addWidget(self.table_history)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel_ticket = QPushButton("❌ Hủy Vé Đã Chọn")
        self.btn_cancel_ticket.setObjectName("BtnDanger")
        self.btn_cancel_ticket.clicked.connect(self.handle_cancel_ticket)
        btn_layout.addWidget(self.btn_cancel_ticket)
        
        history_layout.addLayout(btn_layout); layout.addWidget(group_history)

    def apply_role_permissions(self, user):
        """Giấu nút hủy vé đi nếu là GUEST hoặc USER"""
        if user.role.upper() in ['USER', 'GUEST']: 
            self.btn_cancel_ticket.setVisible(False)
        else: 
            self.btn_cancel_ticket.setVisible(True)

    def handle_search_customer(self):
        keyword = self.txt_search.text().strip()
        if not keyword: return QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập từ khóa!")
        
        customer_info, ticket_history = self.booking_service.search_customer(keyword)
        if not customer_info:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy khách hàng!")
            self.table_history.setRowCount(0)
            return

        self.lbl_name.setText(customer_info['full_name']); self.lbl_phone.setText(customer_info['phone'])
        self.lbl_email.setText(customer_info.get('email', 'Không có')); self.lbl_cccd.setText(customer_info['id_card'])

        self.table_history.setRowCount(0)
        for row, t in enumerate(ticket_history):
            self.table_history.insertRow(row)
            self.table_history.setItem(row, 0, QTableWidgetItem(str(t['ticket_id'])))
            self.table_history.setItem(row, 1, QTableWidgetItem(t['flight_number']))
            self.table_history.setItem(row, 2, QTableWidgetItem(f"{t['departure_code']} ➔ {t['arrival_code']}"))
            self.table_history.setItem(row, 3, QTableWidgetItem(t['class_name']))
            self.table_history.setItem(row, 4, QTableWidgetItem(t['seat_number']))
            self.table_history.setItem(row, 5, QTableWidgetItem(str(t['departure_time'])))
            self.table_history.setItem(row, 6, QTableWidgetItem(str(t['arrival_time'])))
            self.table_history.setItem(row, 7, QTableWidgetItem(f"{t['final_price']:,.0f} VND"))
            
            status_item = QTableWidgetItem(t['status'])
            if t['status'] == 'CANCELLED': status_item.setForeground(Qt.GlobalColor.red)
            elif t['status'] == 'BOOKED': status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.table_history.setItem(row, 8, status_item)

    def handle_cancel_ticket(self):
        row = self.table_history.currentRow()
        if row < 0: return QMessageBox.warning(self, "Chú ý", "Chọn 1 vé để hủy!")
        ticket_id = self.table_history.item(row, 0).text()
        
        if QMessageBox.question(self, 'Xác nhận', f"Hủy vé mã {ticket_id}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            success, msg = self.booking_service.cancel_ticket(ticket_id)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.handle_search_customer() 
            else:
                QMessageBox.critical(self, "Lỗi", msg)