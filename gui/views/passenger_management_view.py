# gui/views/passenger_management_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QHeaderView, QMessageBox)
from bll.booking_service import BookingService

class PassengerManagementView(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.service = BookingService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("📋 QUẢN LÝ DANH SÁCH HÀNH KHÁCH")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #3B82F6;")
        layout.addWidget(lbl)

        # Toolbar
        toolbar = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Tra cứu theo Tên, SĐT, CCCD, Mã chuyến bay...")
        self.txt_search.returnPressed.connect(self.load_data)
        
        btn_search = QPushButton("Tìm Kiếm")
        btn_search.setStyleSheet("background-color: #1E293B; color: white;")
        btn_search.clicked.connect(self.load_data)
        
        toolbar.addWidget(self.txt_search); toolbar.addWidget(btn_search)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Mã Vé", "Hành Khách", "Số ĐT", "CCCD", "Chuyến Bay", "Ghế", "Trạng Thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Actions
        actions = QHBoxLayout()
        btn_cancel = QPushButton("❌ Hủy Vé (Chỉ Admin)")
        btn_cancel.setStyleSheet("background-color: #EF4444; color: white;")
        btn_cancel.clicked.connect(self.handle_cancel)
        
        # Ẩn nút hủy vé nếu là STAFF
        if self.current_user.get('role', '').upper() != 'ADMIN':
            btn_cancel.setVisible(False)

        actions.addStretch(); actions.addWidget(btn_cancel)
        layout.addLayout(actions)

        self.load_data()

    def load_data(self):
        data = self.service.search_passengers(self.txt_search.text().strip())
        self.table.setRowCount(0)
        for r, item in enumerate(data):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(item['ticket_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(item['full_name']))
            self.table.setItem(r, 2, QTableWidgetItem(item['phone']))
            self.table.setItem(r, 3, QTableWidgetItem(item['id_card']))
            self.table.setItem(r, 4, QTableWidgetItem(item['flight_number']))
            self.table.setItem(r, 5, QTableWidgetItem(f"{item['seat_number']} ({item['ticket_class']})"))
            self.table.setItem(r, 6, QTableWidgetItem(item['ticket_status']))

    def handle_cancel(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Lỗi", "Chọn một vé để hủy!")
        
        ticket_id = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Xác nhận", "Hủy vé này? Ghế sẽ được nhả ra hệ thống.") == QMessageBox.StandardButton.Yes:
            success, msg = self.service.cancel_ticket(ticket_id, self.current_user.get('role', '').upper())
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()
            else:
                QMessageBox.critical(self, "Lỗi", msg)