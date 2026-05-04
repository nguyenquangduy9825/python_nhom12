# gui/views/customer_booking_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QDateEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QFormLayout)
from PyQt6.QtCore import Qt, QDate
from gui.animations import FadingStackedWidget, AnimatedHoverCard
from bll.booking_service import BookingService
import datetime

BASE_PRICE = 1500000 # Giá vé cơ bản

# ==================================================
# BƯỚC 1: TỔNG QUAN CHUYẾN BAY
# ==================================================
class StepDashboard(QWidget):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl_title = QLabel("🛫 Chuyến bay đang mở bán")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F8FAFC; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Mã Chuyến", "Tuyến Bay", "Khởi hành", "Hạ cánh", "Ghế trống"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

        btn_search = QPushButton("🔍 Bắt đầu Tìm chuyến & Đặt vé")
        btn_search.setObjectName("BtnPrimary")
        btn_search.setFixedHeight(45)
        btn_search.clicked.connect(lambda: self.parent_view.navigate("search"))
        layout.addWidget(btn_search)

    def load_data(self):
        flights = self.parent_view.booking_service.get_all_available_flights()
        self.table.setRowCount(0)
        for i, f in enumerate(flights):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(f['flight_number']))
            self.table.setItem(i, 1, QTableWidgetItem(f"{f['departure_code']} ➔ {f['arrival_code']}"))
            self.table.setItem(i, 2, QTableWidgetItem(str(f['departure_time'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(f['arrival_time'])))
            self.table.setItem(i, 4, QTableWidgetItem(f"{f['available_seats']} ghế"))

# ==================================================
# BƯỚC 2: TÌM KIẾM 
# ==================================================
class StepSearch(QWidget):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        card = AnimatedHoverCard()
        f_layout = QHBoxLayout(card)
        
        self.cb_dep = QComboBox(); self.cb_dep.addItems(["HAN", "SGN", "DAD", "PQC", "CXR"])
        self.cb_dest = QComboBox(); self.cb_dest.addItems(["SGN", "HAN", "DAD", "PQC", "CXR"])
        
        self.date_picker = QDateEdit(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("dd/MM/yyyy") 
        
        calendar = self.date_picker.calendarWidget()
        calendar.setGridVisible(True)
        calendar.setStyleSheet("""
            QCalendarWidget QWidget { background-color: #1E293B; color: #F8FAFC; }
            QCalendarWidget QToolButton { color: #F8FAFC; font-weight: bold; }
            QCalendarWidget QTableView { selection-background-color: #3B82F6; }
        """)
        
        btn_search = QPushButton("Lọc Chuyến")
        btn_search.setObjectName("BtnSuccess")
        btn_search.clicked.connect(self.do_search)

        f_layout.addWidget(QLabel("Từ:")); f_layout.addWidget(self.cb_dep)
        f_layout.addWidget(QLabel("Đến:")); f_layout.addWidget(self.cb_dest)
        f_layout.addWidget(QLabel("Ngày:")); f_layout.addWidget(self.date_picker)
        f_layout.addWidget(btn_search); f_layout.addStretch()
        layout.addWidget(card)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Mã Chuyến", "Tuyến Bay", "Khởi hành", "Trạng thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_back = QPushButton("Trở lại")
        btn_back.clicked.connect(lambda: self.parent_view.navigate("dashboard"))
        btn_select = QPushButton("✈️ Chọn Chuyến Này")
        btn_select.setObjectName("BtnPrimary")
        btn_select.clicked.connect(self.do_select)
        btn_layout.addWidget(btn_back); btn_layout.addWidget(btn_select)
        layout.addLayout(btn_layout)

    def do_search(self):
        dep, dest = self.cb_dep.currentText(), self.cb_dest.currentText()
        date_sql_format = self.date_picker.date().toString("yyyy-MM-dd") 
        
        results = self.parent_view.booking_service.search_flights(dep, dest, date_sql_format)
        
        self.table.setRowCount(0)
        for i, f in enumerate(results):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(f['flight_id'])))
            self.table.setItem(i, 1, QTableWidgetItem(f['flight_number']))
            self.table.setItem(i, 2, QTableWidgetItem(f"{f['departure_code']} ➔ {f['arrival_code']}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(f['departure_time'])))
            
            status = "Còn vé" if f['available_seats'] > 0 else "Hết vé"
            item = QTableWidgetItem(status)
            item.setForeground(Qt.GlobalColor.green if status == "Còn vé" else Qt.GlobalColor.red)
            self.table.setItem(i, 4, item)

    def do_select(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Lỗi", "Vui lòng chọn 1 chuyến bay!")
        if self.table.item(row, 4).text() == "Hết vé":
            return QMessageBox.critical(self, "Rất tiếc", "Chuyến bay đã hết chỗ!")

        self.parent_view.state["flight_id"] = int(self.table.item(row, 0).text())
        self.parent_view.state["flight_code"] = self.table.item(row, 1).text()
        self.parent_view.navigate("seat")

# ==================================================
# BƯỚC 3: CHỌN GHẾ
# ==================================================
class StepSeat(QWidget):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.all_seats = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card = AnimatedHoverCard()
        card.setFixedSize(400, 300)
        c_layout = QVBoxLayout(card)
        
        self.lbl_title = QLabel("💺 Chọn Hạng & Vị trí Ghế")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3B82F6;")
        
        self.cb_class = QComboBox()
        self.cb_class.addItems(["Tất cả", "ECONOMY", "BUSINESS"])
        self.cb_class.currentTextChanged.connect(self.filter_seats)

        self.cb_seat = QComboBox()

        c_layout.addWidget(self.lbl_title)
        c_layout.addWidget(QLabel("Hạng Ghế:")); c_layout.addWidget(self.cb_class)
        c_layout.addWidget(QLabel("Sơ đồ Ghế trống:")); c_layout.addWidget(self.cb_seat)
        c_layout.addStretch()

        nav = QHBoxLayout()
        btn_back = QPushButton("Trở lại"); btn_back.clicked.connect(lambda: self.parent_view.navigate("search"))
        btn_next = QPushButton("Tiếp tục"); btn_next.setObjectName("BtnPrimary"); btn_next.clicked.connect(self.do_confirm)
        nav.addWidget(btn_back); nav.addWidget(btn_next)
        c_layout.addLayout(nav); layout.addWidget(card)

    def load_data(self):
        f_id = self.parent_view.state.get("flight_id")
        self.lbl_title.setText(f"💺 Chọn Ghế - Chuyến {self.parent_view.state.get('flight_code')}")
        self.all_seats = self.parent_view.booking_service.get_available_seats(f_id)
        self.filter_seats()

    def filter_seats(self):
        self.cb_seat.clear()
        selected_class = self.cb_class.currentText()
        for s in self.all_seats:
            if selected_class == "Tất cả" or s['class_name'].upper() == selected_class:
                price = BASE_PRICE * float(s['price_multiplier'])
                self.cb_seat.addItem(f"Ghế {s['seat_number']} ({s['class_name']}) - {price:,.0f} VND", s)

    def do_confirm(self):
        seat_data = self.cb_seat.currentData()
        if not seat_data: return QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ghế!")
        self.parent_view.state["seat"] = seat_data
        self.parent_view.navigate("info")

# ==================================================
# BƯỚC 4: THÔNG TIN KHÁCH HÀNG
# ==================================================
class StepInfo(QWidget):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = AnimatedHoverCard()
        card.setFixedSize(450, 400)
        c_layout = QVBoxLayout(card)

        lbl = QLabel("📝 Nhập Thông tin Hành khách")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981; margin-bottom: 16px;")
        
        self.txt_name = QLineEdit(); self.txt_name.setPlaceholderText("Họ và Tên (*)")
        self.txt_phone = QLineEdit(); self.txt_phone.setPlaceholderText("Số điện thoại (*)")
        self.txt_cccd = QLineEdit(); self.txt_cccd.setPlaceholderText("Số CCCD / Hộ chiếu (*)")
        self.txt_email = QLineEdit(); self.txt_email.setPlaceholderText("Email nhận vé (Tùy chọn)")
        
        current_user = self.parent_view.current_user
        if current_user and current_user.username != "Khách Vãng Lai":
            self.txt_name.setText(current_user.username)
        
        c_layout.addWidget(lbl)
        c_layout.addWidget(self.txt_name); c_layout.addWidget(self.txt_phone)
        c_layout.addWidget(self.txt_cccd); c_layout.addWidget(self.txt_email)
        c_layout.addStretch()

        nav = QHBoxLayout()
        btn_back = QPushButton("Trở lại"); btn_back.clicked.connect(lambda: self.parent_view.navigate("seat"))
        btn_next = QPushButton("Đến Thanh Toán"); btn_next.setObjectName("BtnPrimary"); btn_next.clicked.connect(self.do_confirm)
        nav.addWidget(btn_back); nav.addWidget(btn_next)
        c_layout.addLayout(nav); layout.addWidget(card)

    def do_confirm(self):
        n, p, c, e = self.txt_name.text().strip(), self.txt_phone.text().strip(), self.txt_cccd.text().strip(), self.txt_email.text().strip()
        if not all([n, p, c]): return QMessageBox.warning(self, "Lỗi", "Nhập đủ Tên, SĐT, CCCD!")
        self.parent_view.state["customer"] = {'full_name': n, 'phone': p, 'id_card': c, 'email': e}
        self.parent_view.navigate("payment")

# ==================================================
# BƯỚC 5: THANH TOÁN (CẬP NHẬT SELECT-OPTION VOUCHER)
# ==================================================
class StepPayment(QWidget):
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = AnimatedHoverCard()
        card.setFixedSize(550, 580) 
        c_layout = QVBoxLayout(card)

        lbl = QLabel("💳 Xác nhận Thanh toán")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #F59E0B; margin-bottom: 10px;")
        
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet("color: #94A3B8; line-height: 1.5; font-size: 15px;")
        
        lbl_v = QLabel("🎟️ Mã giảm giá dành cho bạn (Click đúp để chọn):")
        lbl_v.setStyleSheet("font-weight: bold; color: #10B981; margin-top: 15px;")
        
        self.table_vouchers = QTableWidget(0, 3)
        self.table_vouchers.setHorizontalHeaderLabels(["Mã Code", "Mức giảm", "HSD"])
        self.table_vouchers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_vouchers.verticalHeader().setVisible(False)
        self.table_vouchers.setShowGrid(False)
        self.table_vouchers.setFixedHeight(120) 
        self.table_vouchers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_vouchers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Sự kiện click đúp trên bảng
        self.table_vouchers.itemDoubleClicked.connect(self.auto_fill_voucher)

        v_layout = QHBoxLayout()
        # ĐỔI THÀNH QCOMBOBOX THAY VÌ QLINEEDIT
        self.cb_voucher = QComboBox()
        btn_apply = QPushButton("Áp dụng"); btn_apply.setObjectName("BtnOutline")
        btn_apply.clicked.connect(self.apply_voucher)
        v_layout.addWidget(self.cb_voucher); v_layout.addWidget(btn_apply)

        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet("font-size: 28px; font-weight: bold; color: #10B981; margin-top: 20px;")

        c_layout.addWidget(lbl)
        c_layout.addWidget(self.lbl_summary)
        c_layout.addWidget(lbl_v)
        c_layout.addWidget(self.table_vouchers)
        c_layout.addLayout(v_layout)
        c_layout.addWidget(self.lbl_total)
        c_layout.addStretch()

        nav = QHBoxLayout()
        btn_cancel = QPushButton("Hủy"); btn_cancel.setObjectName("BtnDanger")
        btn_cancel.clicked.connect(lambda: self.parent_view.navigate("dashboard"))
        
        btn_pay = QPushButton("Xác Nhận Xuất Vé"); btn_pay.setObjectName("BtnSuccess")
        btn_pay.clicked.connect(self.do_payment)
        nav.addWidget(btn_cancel); nav.addWidget(btn_pay)
        
        c_layout.addLayout(nav); layout.addWidget(card)

    def load_data(self):
        s = self.parent_view.state["seat"]
        c = self.parent_view.state["customer"]
        
        self.parent_view.state["base_price"] = BASE_PRICE * float(s['price_multiplier'])
        self.parent_view.state["final_price"] = self.parent_view.state["base_price"]
        self.parent_view.state["voucher_code"] = None
        
        sum_text = f"✈️ Chuyến bay: {self.parent_view.state['flight_code']} | Ghế: {s['seat_number']} ({s['class_name']})\n"
        sum_text += f"👤 Khách hàng: {c['full_name']} | CCCD: {c['id_card']}\n"
        sum_text += f"💵 Giá vé gốc: {self.parent_view.state['base_price']:,.0f} VND"
        
        self.lbl_summary.setText(sum_text)
        self.load_active_vouchers() 
        self.update_price()

    def load_active_vouchers(self):
        active_vouchers = self.parent_view.booking_service.get_active_vouchers()
        self.table_vouchers.setRowCount(0)
        
        # Reset Combobox và chèn mục mặc định
        self.cb_voucher.clear()
        self.cb_voucher.addItem("--- Chọn mã giảm giá ---", None)
        
        for row, v in enumerate(active_vouchers):
            self.table_vouchers.insertRow(row)
            self.table_vouchers.setItem(row, 0, QTableWidgetItem(v['code']))
            
            discount_text = f"{float(v['discount_percent'])}%"
            if v['max_discount']:
                discount_text += f" (Tối đa {float(v['max_discount']):,.0f}đ)"
            self.table_vouchers.setItem(row, 1, QTableWidgetItem(discount_text))
            
            expiry = v['expiry_date']
            if isinstance(expiry, datetime.datetime):
                expiry_str = expiry.strftime("%d/%m/%Y %H:%M")
            else:
                expiry_str = str(expiry)
            self.table_vouchers.setItem(row, 2, QTableWidgetItem(expiry_str))
            
            # Add vào Combobox kèm ID (code) làm data ẩn
            self.cb_voucher.addItem(f"{v['code']} - Giảm {discount_text}", v['code'])

    def auto_fill_voucher(self, item):
        """Logic: Lấy mã ở cột 0, tìm trong ComboBox và đặt index tương ứng"""
        row = item.row()
        code = self.table_vouchers.item(row, 0).text()
        
        # Tìm item nào trong cb_voucher chứa Data trùng với mã code
        index = self.cb_voucher.findData(code)
        if index != -1:
            self.cb_voucher.setCurrentIndex(index)

    def apply_voucher(self):
        code = self.cb_voucher.currentData()
        if not code:
            # Khôi phục giá nếu chọn "--- Chọn mã giảm giá ---"
            self.parent_view.state["final_price"] = self.parent_view.state["base_price"]
            self.parent_view.state["voucher_code"] = None
            self.update_price()
            return
        
        voucher = self.parent_view.booking_service.voucher_repo.get_by_code(code)
        if not voucher or voucher['expiry_date'] < datetime.datetime.now() or voucher['used_count'] >= voucher['usage_limit']:
            return QMessageBox.warning(self, "Lỗi", "Voucher không tồn tại hoặc đã hết hạn!")
        
        base = self.parent_view.state["base_price"]
        discount = base * (float(voucher['discount_percent']) / 100.0)
        if voucher['max_discount'] and discount > voucher['max_discount']:
            discount = voucher['max_discount']
            
        self.parent_view.state["final_price"] = base - discount
        self.parent_view.state["voucher_code"] = code
        QMessageBox.information(self, "Thành công", f"Áp dụng thành công! Giảm {discount:,.0f} VND")
        self.update_price()

    def update_price(self):
        self.lbl_total.setText(f"Thành tiền: {self.parent_view.state['final_price']:,.0f} VND")

    def do_payment(self):
        reply = QMessageBox.question(self, "Thanh Toán", f"Xác nhận thanh toán {self.parent_view.state['final_price']:,.0f} VND?")
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.parent_view.booking_service.process_booking(
                customer_info=self.parent_view.state["customer"],
                flight_id=self.parent_view.state["flight_id"],
                seat_id=self.parent_view.state["seat"]["seat_id"],
                base_price=self.parent_view.state["base_price"],
                voucher_code=self.parent_view.state["voucher_code"],
                is_hold=False
            )
            if success:
                QMessageBox.information(self, "Thành Công ✨", "Vé đã được xuất và lưu vào hệ thống!")
                self.parent_view.state.clear() 
                self.parent_view.navigate("dashboard") 
            else:
                QMessageBox.critical(self, "Thất bại", msg)

# ==================================================
# BỘ ĐIỀU PHỐI CHÍNH (ROUTER CONTAINER)
# ==================================================
class CustomerBookingView(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.booking_service = BookingService()
        self.state = {} 
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.wizard = FadingStackedWidget()
        self.s_dash = StepDashboard(self)
        self.s_search = StepSearch(self)
        self.s_seat = StepSeat(self)
        self.s_info = StepInfo(self)
        self.s_payment = StepPayment(self)

        self.wizard.addWidget(self.s_dash)
        self.wizard.addWidget(self.s_search)
        self.wizard.addWidget(self.s_seat)
        self.wizard.addWidget(self.s_info)
        self.wizard.addWidget(self.s_payment)

        layout.addWidget(self.wizard)
        self.navigate("dashboard")

    def navigate(self, step):
        if step == "dashboard": self.s_dash.load_data(); self.wizard.setCurrentIndex(0)
        elif step == "search": self.wizard.setCurrentIndex(1)
        elif step == "seat": self.s_seat.load_data(); self.wizard.setCurrentIndex(2)
        elif step == "info": self.wizard.setCurrentIndex(3)
        elif step == "payment": self.s_payment.load_data(); self.wizard.setCurrentIndex(4)