# gui/views/booking_view.py
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QFrame, 
                             QGridLayout, QLineEdit, QFormLayout, QMessageBox, QHeaderView, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from bll.booking_service import BookingService

class BookingScreen(QWidget): 
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.service = BookingService()
        self.selected_flight_id = None
        self.selected_seat = None
        self.setup_ui()
        self.apply_styles()
        
        # Lấy dữ liệu khi vừa mở tab
        self.load_all_flights()

    def apply_role_permissions(self, user_obj):
        self.current_user = user_obj

    def apply_styles(self):
        self.setStyleSheet("""
            QFrame#Panel { background-color: #1E293B; border-radius: 12px; }
            QLabel { color: #E2E8F0; font-size: 14px; }
            QPushButton#SeatAVAILABLE { background-color: #10B981; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton#SeatBUSINESS { background-color: #3B82F6; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton#SeatBOOKED { background-color: #EF4444; color: white; border-radius: 8px; }
            QPushButton#SeatHELD { background-color: #F59E0B; color: white; border-radius: 8px; }
            QPushButton#SeatSELECTED { background-color: #F59E0B; color: white; border-radius: 8px; border: 2px solid white; }
            QLineEdit, QDateEdit { background-color: #0B1220; border: 1px solid #334155; border-radius: 6px; padding: 8px; color: white;}
            QCalendarWidget QWidget { background-color: #1E293B; color: #F8FAFC; }
        """)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        left_panel = QFrame(); left_panel.setObjectName("Panel")
        left_layout = QVBoxLayout(left_panel)
        
        lbl_left = QLabel("✈️ 1. DANH SÁCH CHUYẾN BAY"); lbl_left.setStyleSheet("font-size: 18px; font-weight: bold; color: #3B82F6;")
        left_layout.addWidget(lbl_left)

        search_form = QHBoxLayout()
        self.txt_dep = QLineEdit(); self.txt_dep.setPlaceholderText("Từ (HAN)")
        self.txt_arr = QLineEdit(); self.txt_arr.setPlaceholderText("Đến (SGN)")
        
        self.txt_date = QDateEdit(QDate.currentDate())
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDisplayFormat("yyyy-MM-dd")
        
        btn_search = QPushButton("Tìm Lọc"); btn_search.setStyleSheet("background-color: #3B82F6; color: white; padding: 8px;")
        btn_search.clicked.connect(self.handle_search_click)
        
        btn_clear = QPushButton("Tải Lại"); btn_clear.setStyleSheet("background-color: #64748B; color: white; padding: 8px;")
        btn_clear.clicked.connect(self.load_all_flights)

        search_form.addWidget(self.txt_dep); search_form.addWidget(self.txt_arr)
        search_form.addWidget(self.txt_date); search_form.addWidget(btn_search); search_form.addWidget(btn_clear)
        left_layout.addLayout(search_form)

        self.table_flights = QTableWidget(0, 4)
        self.table_flights.setHorizontalHeaderLabels(["ID", "Chuyến bay", "Giờ đi", "Ghế trống"])
        
        # ĐÃ FIX: Sửa lại đúng tên biến self.table_flights và chống cảnh báo setGeometry
        self.table_flights.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_flights.horizontalHeader().setStretchLastSection(True) 
        
        self.table_flights.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_flights.itemSelectionChanged.connect(self.on_flight_selected)
        left_layout.addWidget(self.table_flights)
        
        layout.addWidget(left_panel, 4) 

        right_panel = QFrame(); right_panel.setObjectName("Panel")
        right_layout = QVBoxLayout(right_panel)

        lbl_right = QLabel("💺 2. CHỌN GHẾ & THANH TOÁN"); lbl_right.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
        right_layout.addWidget(lbl_right)

        self.seat_map_frame = QFrame()
        self.seat_grid = QGridLayout(self.seat_map_frame)
        self.seat_grid.setSpacing(5)
        right_layout.addWidget(self.seat_map_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        form = QFormLayout()
        self.lbl_selected_seat = QLabel("Chưa chọn"); self.lbl_selected_seat.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 16px;")
        self.txt_name = QLineEdit()
        self.txt_phone = QLineEdit()
        self.txt_idcard = QLineEdit()
        self.txt_voucher = QLineEdit(); self.txt_voucher.setPlaceholderText("Nhập mã giảm giá (nếu có)")
        
        form.addRow("Ghế đang chọn:", self.lbl_selected_seat)
        form.addRow("Họ và Tên:", self.txt_name)
        form.addRow("Số ĐT:", self.txt_phone)
        form.addRow("CCCD:", self.txt_idcard)
        form.addRow("Voucher:", self.txt_voucher)
        right_layout.addLayout(form)

        action_layout = QHBoxLayout()
        btn_hold = QPushButton("⏳ GIỮ CHỖ (15 PHÚT)")
        btn_hold.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        btn_hold.clicked.connect(lambda: self.process_booking(is_hold=True))
        
        btn_book = QPushButton("💳 THANH TOÁN TIỀN MẶT")
        btn_book.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; font-size: 14px; padding: 10px;")
        btn_book.clicked.connect(lambda: self.process_booking(is_hold=False))
        
        action_layout.addWidget(btn_hold); action_layout.addWidget(btn_book)
        right_layout.addLayout(action_layout)

        layout.addWidget(right_panel, 6)

    def load_all_flights(self):
        self.txt_dep.clear()
        self.txt_arr.clear()
        flights = self.service.get_all_available_flights()
        self.populate_flight_table(flights)

    def handle_search_click(self):
        dep = self.txt_dep.text().strip().upper()
        arr = self.txt_arr.text().strip().upper()
        dt = self.txt_date.date().toString("yyyy-MM-dd")
        if not dep or not arr:
            self.load_all_flights()
            return
            
        # ĐỒNG BỘ: Sử dụng hàm search_flights của tầng BLL mới
        ok, msg, flights = self.service.search_flights(dep, arr, dt)
        if ok:
            self.populate_flight_table(flights)
        else:
            self.table_flights.setRowCount(0)
            QMessageBox.information(self, "Thông báo", msg)

    def populate_flight_table(self, flights):
        self.table_flights.setRowCount(0)
        for row, f in enumerate(flights):
            self.table_flights.insertRow(row)
            self.table_flights.setItem(row, 0, QTableWidgetItem(str(f['flight_id'])))
            self.table_flights.setItem(row, 1, QTableWidgetItem(f['flight_number']))
            self.table_flights.setItem(row, 2, QTableWidgetItem(str(f['departure_time'])))
            self.table_flights.setItem(row, 3, QTableWidgetItem(str(f['available_seats'])))

    def on_flight_selected(self):
        row = self.table_flights.currentRow()
        if row < 0: return
        self.selected_flight_id = int(self.table_flights.item(row, 0).text())
        self.render_seat_map()

    def render_seat_map(self):
        while self.seat_grid.count():
            child = self.seat_grid.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        self.selected_seat = None
        self.lbl_selected_seat.setText("Chưa chọn")

        seats = self.service.get_flight_seats(self.selected_flight_id)
        if not seats: return

        row_map = {}
        current_row = 0

        for seat in seats:
            seat_num = seat['seat_number']
            
            match = re.match(r"([A-Za-z]+)(\d+)", seat_num)
            if not match: continue
            
            letter_part, number_part = match.groups()
            
            if letter_part not in row_map:
                row_map[letter_part] = current_row
                lbl = QLabel(f"<b>Hàng {letter_part}</b>")
                lbl.setStyleSheet("color: #94A3B8;")
                self.seat_grid.addWidget(lbl, current_row, 0)
                current_row += 1

            r = row_map[letter_part]
            c = int(number_part)

            btn = QPushButton(seat_num)
            btn.setFixedSize(45, 45)
            
            if seat['seat_status'] == 'BOOKED':
                btn.setObjectName("SeatBOOKED")
                btn.setEnabled(False)
            elif seat['seat_status'] == 'HELD':
                btn.setObjectName("SeatHELD")
                btn.setEnabled(False)
            elif seat['class_name'] == 'BUSINESS':
                btn.setObjectName("SeatBUSINESS")
            else:
                btn.setObjectName("SeatAVAILABLE")

            btn.setProperty("seat_data", seat)
            btn.clicked.connect(lambda checked, b=btn: self.on_seat_click(b))

            grid_col = c if c <= 2 else c + 1
            self.seat_grid.addWidget(btn, r, grid_col)

    def on_seat_click(self, btn):
        if self.selected_seat:
            old_btn = self.selected_seat['btn']
            status_obj = "SeatBUSINESS" if self.selected_seat['data']['class_name'] == 'BUSINESS' else "SeatAVAILABLE"
            old_btn.setObjectName(status_obj)
            old_btn.style().unpolish(old_btn); old_btn.style().polish(old_btn)

        btn.setObjectName("SeatSELECTED")
        btn.style().unpolish(btn); btn.style().polish(btn)
        
        seat_data = btn.property("seat_data")
        self.selected_seat = {'btn': btn, 'data': seat_data}
        self.lbl_selected_seat.setText(f"{seat_data['seat_number']} - Hạng: {seat_data['class_name']}")

    def process_booking(self, is_hold):
        if not self.selected_flight_id or not self.selected_seat:
            return QMessageBox.warning(self, "Lỗi", "Vui lòng chọn Chuyến bay và Ghế!")

        seat_data = self.selected_seat['data']
        multiplier = self.service.get_class_multiplier(seat_data['class_name'])
        base_price = 1500000 * multiplier 

        # ĐỒNG BỘ: Sử dụng hệ thống 1-N mạnh mẽ của BLL
        group_info = {
            'flight_id': self.selected_flight_id,
            'contact_name': self.txt_name.text().strip(),
            'contact_phone': self.txt_phone.text().strip(),
            'contact_email': "",
            'total_amount': base_price,
            'payment_method': 'PAY_LATER' if is_hold else 'CASH', # Admin thu tiền mặt trực tiếp
            'voucher_id': None
        }

        passengers = [{
            'seat_id': seat_data['seat_id'],
            'seat_number': seat_data['seat_number'],
            'base_price': 1500000,
            'final_price': base_price,
            'name': self.txt_name.text().strip(),
            'id_card': self.txt_idcard.text().strip(),
            'phone': self.txt_phone.text().strip()
        }]

        success, msg, bk_code = self.service.validate_and_book_group(group_info, passengers, is_hold)
        
        if success:
            QMessageBox.information(self, "Thành công", f"Giao dịch hoàn tất!\nMã PNR: {bk_code}\nTổng tiền: {base_price:,.0f} VND")
            self.txt_name.clear(); self.txt_phone.clear(); self.txt_idcard.clear(); self.txt_voucher.clear()
            self.load_all_flights() 
            self.render_seat_map() 
        else:
            QMessageBox.critical(self, "Thất bại", msg)