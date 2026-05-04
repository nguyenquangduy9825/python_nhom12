# gui/views/booking_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QComboBox, 
                             QDateEdit, QGroupBox, QFormLayout, QHeaderView, QMessageBox, QTableWidgetItem)
from PyQt6.QtCore import Qt, QDate
from bll.booking_service import BookingService

class BookingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.booking_service = BookingService()
        self.current_base_price = 1500000 
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # --- PHẦN 1: SEARCH & BẢNG FLIGHT ---
        group_search = QGroupBox("Danh sách Chuyến bay")
        search_layout = QVBoxLayout(group_search)
        search_layout.setContentsMargins(16, 24, 16, 16)
        
        filter_layout = QHBoxLayout()
        self.cb_from = QComboBox()
        self.cb_from.addItems(["Hà Nội (HAN)", "Hồ Chí Minh (SGN)", "Đà Nẵng (DAD)", "Phú Quốc (PQC)", "Cam Ranh (CXR)"])
        self.cb_from.setItemData(0, "HAN"); self.cb_from.setItemData(1, "SGN"); self.cb_from.setItemData(2, "DAD")
        self.cb_from.setItemData(3, "PQC"); self.cb_from.setItemData(4, "CXR")
        
        self.cb_to = QComboBox()
        self.cb_to.addItems(["Hồ Chí Minh (SGN)", "Hà Nội (HAN)", "Đà Nẵng (DAD)", "Phú Quốc (PQC)", "Cam Ranh (CXR)"])
        self.cb_to.setItemData(0, "SGN"); self.cb_to.setItemData(1, "HAN"); self.cb_to.setItemData(2, "DAD")
        self.cb_to.setItemData(3, "PQC"); self.cb_to.setItemData(4, "CXR")

        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate()) 
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        
        self.btn_search = QPushButton("🔍 Tìm kiếm")
        self.btn_search.setObjectName("BtnPrimary")
        self.btn_search.clicked.connect(self.handle_search_flights)

        self.btn_load_all = QPushButton("🔄 Hiển thị tất cả")
        self.btn_load_all.setObjectName("BtnOutline")
        self.btn_load_all.clicked.connect(self.load_all_flights)
        
        filter_layout.addWidget(QLabel("Từ:")); filter_layout.addWidget(self.cb_from)
        filter_layout.addWidget(QLabel("Đến:")); filter_layout.addWidget(self.cb_to)
        filter_layout.addWidget(QLabel("Ngày bay:")); filter_layout.addWidget(self.date_picker)
        filter_layout.addWidget(self.btn_search); filter_layout.addWidget(self.btn_load_all) 
        
        self.table_flights = QTableWidget(0, 6)
        self.table_flights.setHorizontalHeaderLabels(["ID", "Mã Chuyến", "Tuyến Bay", "Giờ Cất Cánh", "Số Ghế Trống", "Trạng Thái"])
        self.table_flights.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_flights.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_flights.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # --- FIX: Tắt cột đen và viền lưới cho thanh thoát ---
        self.table_flights.verticalHeader().setVisible(False)
        self.table_flights.setShowGrid(False)
        
        self.table_flights.itemSelectionChanged.connect(self.on_flight_selected)
        
        search_layout.addLayout(filter_layout)
        search_layout.addWidget(self.table_flights)
        layout.addWidget(group_search, stretch=1)

        # --- PHẦN 2: BOOKING PANEL ---
        self.group_book = QGroupBox("Thông tin Hành khách & Thanh toán")
        book_layout = QHBoxLayout(self.group_book)
        book_layout.setContentsMargins(16, 24, 16, 16)
        
        form_left = QFormLayout()
        self.txt_name = QLineEdit(); self.txt_phone = QLineEdit()
        self.txt_email = QLineEdit(); self.txt_cccd = QLineEdit()
        
        form_left.addRow("Họ và Tên (*):", self.txt_name)
        form_left.addRow("Số Điện Thoại (*):", self.txt_phone)
        form_left.addRow("Email:", self.txt_email)
        form_left.addRow("CCCD (*):", self.txt_cccd)
        
        form_right = QVBoxLayout()
        seat_layout = QHBoxLayout()
        self.cb_seat = QComboBox() 
        self.cb_seat.currentIndexChanged.connect(self.update_price_display) 
        
        seat_layout.addWidget(QLabel("Chọn Ghế:")); seat_layout.addWidget(self.cb_seat)
        
        voucher_layout = QHBoxLayout()
        self.txt_voucher = QLineEdit(); self.txt_voucher.setPlaceholderText("Nhập mã Voucher (VD: VIP20)")
        btn_apply = QPushButton("Áp dụng")
        btn_apply.setObjectName("BtnOutline")
        
        voucher_layout.addWidget(self.txt_voucher); voucher_layout.addWidget(btn_apply)
        
        self.lbl_total = QLabel(f"Tạm tính: {self.current_base_price:,.0f} VND")
        self.lbl_total.setStyleSheet("font-size: 20px; font-weight: bold; color: #10B981; margin: 10px 0;")
        
        btn_action_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("✅ Xuất Vé Ngay (Thanh toán)")
        self.btn_confirm.setObjectName("BtnSuccess")
        self.btn_hold = QPushButton("⏳ Giữ Chỗ (24h)")
        self.btn_hold.setStyleSheet("background-color: #F59E0B; color: white;")
        
        self.btn_confirm.clicked.connect(lambda: self.handle_booking_action(is_hold=False))
        self.btn_hold.clicked.connect(lambda: self.handle_booking_action(is_hold=True))
        
        btn_action_layout.addWidget(self.btn_confirm); btn_action_layout.addWidget(self.btn_hold)
        
        form_right.addLayout(seat_layout); form_right.addLayout(voucher_layout)
        form_right.addWidget(self.lbl_total); form_right.addLayout(btn_action_layout)
        
        book_layout.addLayout(form_left); book_layout.addLayout(form_right)
        layout.addWidget(self.group_book, stretch=1)

        self.load_all_flights()

    def apply_role_permissions(self, user):
        """Nếu là GUEST (Khách vãng lai), ẩn form đặt vé đi, chỉ cho xem chuyến bay"""
        if user.role.upper() == 'GUEST':
            self.group_book.setVisible(False)
        else:
            self.group_book.setVisible(True)

    def populate_flight_table(self, flights):
        self.table_flights.setRowCount(0) 
        self.cb_seat.clear() 
        self.lbl_total.setText(f"Tạm tính: {self.current_base_price:,.0f} VND")
        if not flights: return QMessageBox.information(self, "Thông báo", "Không có chuyến bay nào phù hợp!")
        for row_idx, f in enumerate(flights):
            self.table_flights.insertRow(row_idx)
            self.table_flights.setItem(row_idx, 0, QTableWidgetItem(str(f['flight_id'])))
            self.table_flights.setItem(row_idx, 1, QTableWidgetItem(f['flight_number']))
            self.table_flights.setItem(row_idx, 2, QTableWidgetItem(f"{f['departure_code']} ➔ {f['arrival_code']}"))
            self.table_flights.setItem(row_idx, 3, QTableWidgetItem(str(f['departure_time'])))
            self.table_flights.setItem(row_idx, 4, QTableWidgetItem(f"{f['available_seats']} ghế"))
            self.table_flights.setItem(row_idx, 5, QTableWidgetItem("Đang mở bán"))

    def load_all_flights(self):
        self.populate_flight_table(self.booking_service.get_all_available_flights())

    def handle_search_flights(self):
        self.populate_flight_table(self.booking_service.search_flights(self.cb_from.currentData(), self.cb_to.currentData(), self.date_picker.date().toString("yyyy-MM-dd")))

    def on_flight_selected(self):
        row = self.table_flights.currentRow()
        if row < 0: return
        seats = self.booking_service.get_available_seats(int(self.table_flights.item(row, 0).text()))
        self.cb_seat.clear()
        if not seats: return self.cb_seat.addItem("Hết ghế trống!", None)
        for s in seats: self.cb_seat.addItem(f"Ghế {s['seat_number']} - {s['class_name']}", (s['seat_id'], float(s['price_multiplier'])))

    def update_price_display(self):
        if self.cb_seat.currentIndex() == -1 or not self.cb_seat.currentData(): return 
        self.lbl_total.setText(f"Tạm tính: {self.current_base_price * self.cb_seat.currentData()[1]:,.0f} VND")

    def handle_booking_action(self, is_hold):
        row = self.table_flights.currentRow()
        if row < 0: return QMessageBox.warning(self, "Chú ý", "Chọn chuyến bay!")
        if not self.cb_seat.currentData(): return QMessageBox.warning(self, "Chú ý", "Hết ghế trống!")

        info = {'full_name': self.txt_name.text().strip(), 'phone': self.txt_phone.text().strip(), 'id_card': self.txt_cccd.text().strip(), 'email': self.txt_email.text().strip()}
        success, msg = self.booking_service.process_booking(info, int(self.table_flights.item(row, 0).text()), self.cb_seat.currentData()[0], self.current_base_price * self.cb_seat.currentData()[1], self.txt_voucher.text().strip() or None, is_hold)
        
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.txt_name.clear(); self.txt_phone.clear(); self.txt_cccd.clear(); self.txt_email.clear(); self.txt_voucher.clear()
            self.load_all_flights() 
        else:
            QMessageBox.critical(self, "Lỗi", msg)