# gui/views/admin_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QTabWidget, QComboBox, QFormLayout, QDateTimeEdit, QGroupBox)
from PyQt6.QtCore import Qt, QDateTime
from bll.admin_service import AdminService

class AdminScreen(QWidget):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.admin_service = AdminService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lbl_title = QLabel("🛡️ HỆ THỐNG QUẢN TRỊ (ADMIN PANEL)")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        self.tabs = QTabWidget()
        
        self.user_tab = QWidget(); self.setup_user_tab()
        self.tabs.addTab(self.user_tab, "👤 Quản lý User")

        self.flight_tab = QWidget(); self.setup_flight_tab()
        self.tabs.addTab(self.flight_tab, "✈️ Chuyến bay")

        self.airport_tab = QWidget(); self.setup_airport_tab()
        self.tabs.addTab(self.airport_tab, "🛫 Sân bay")

        self.voucher_tab = QWidget(); self.setup_voucher_tab()
        self.tabs.addTab(self.voucher_tab, "🎟️ Voucher")

        layout.addWidget(self.tabs)

    # ==========================================
    # PHẦN 1: QUẢN LÝ USER
    # ==========================================
    def setup_user_tab(self):
        layout = QVBoxLayout(self.user_tab)
        layout.setContentsMargins(16, 24, 16, 16)
        
        self.table_users = QTableWidget(0, 4)
        self.table_users.setHorizontalHeaderLabels(["ID", "Username", "Role", "Created At"])
        self.table_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_users.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_users.verticalHeader().setVisible(False)
        self.table_users.setShowGrid(False)
        layout.addWidget(self.table_users)

        control_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Tải lại dữ liệu")
        btn_refresh.setObjectName("BtnOutline")
        btn_refresh.clicked.connect(self.load_users)
        control_layout.addWidget(btn_refresh); control_layout.addSpacing(20)
        
        self.cb_role = QComboBox()
        self.cb_role.addItems(["ADMIN", "STAFF", "USER", "GUEST"])
        
        btn_update_role = QPushButton("Cập nhật Role")
        btn_update_role.setObjectName("BtnPrimary")
        btn_update_role.clicked.connect(self.handle_update_role)
        
        btn_delete_user = QPushButton("Xóa User")
        btn_delete_user.setObjectName("BtnDanger")
        btn_delete_user.clicked.connect(self.handle_delete_user)

        control_layout.addWidget(QLabel("Chọn Role mới:")); control_layout.addWidget(self.cb_role)
        control_layout.addWidget(btn_update_role); control_layout.addStretch(); control_layout.addWidget(btn_delete_user)
        layout.addLayout(control_layout)
        self.load_users()

    def load_users(self):
        users = self.admin_service.get_all_users()
        self.table_users.setRowCount(0)
        for row, u in enumerate(users):
            self.table_users.insertRow(row)
            self.table_users.setItem(row, 0, QTableWidgetItem(str(u['user_id'])))
            self.table_users.setItem(row, 1, QTableWidgetItem(u['username']))
            self.table_users.setItem(row, 2, QTableWidgetItem(u['role']))
            self.table_users.setItem(row, 3, QTableWidgetItem(str(u['created_at'])))

    def handle_update_role(self):
        selected = self.table_users.currentRow()
        if selected < 0: return QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 tài khoản!")
        user_id = self.table_users.item(selected, 0).text()
        success, msg = self.admin_service.update_user_role(user_id, self.cb_role.currentText())
        if success: self.load_users()
        QMessageBox.information(self, "Thông báo", msg)

    def handle_delete_user(self):
        selected = self.table_users.currentRow()
        if selected < 0: return QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 tài khoản để xóa!")
        user_id = self.table_users.item(selected, 0).text()
        
        if QMessageBox.question(self, "Xác nhận", f"Xóa user ID {user_id}?") == QMessageBox.StandardButton.Yes:
            current_admin_id = self.current_user.user_id if self.current_user else -1
            success, msg = self.admin_service.delete_user(user_id, current_admin_id)
            if success: self.load_users()
            QMessageBox.information(self, "Thông báo", msg)

    # ==========================================
    # PHẦN 2: QUẢN LÝ CHUYẾN BAY
    # ==========================================
    def setup_flight_tab(self):
        layout = QVBoxLayout(self.flight_tab)
        layout.setContentsMargins(16, 24, 16, 16)
        
        self.table_flights = QTableWidget(0, 7)
        self.table_flights.setHorizontalHeaderLabels(["ID", "Mã Chuyến", "Từ", "Đến", "Giờ Cất Cánh", "Giờ Hạ Cánh", "Trạng Thái"])
        self.table_flights.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_flights.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_flights.verticalHeader().setVisible(False) 
        self.table_flights.setShowGrid(False)
        self.table_flights.itemSelectionChanged.connect(self.on_flight_table_click)
        layout.addWidget(self.table_flights, stretch=2)

        form_layout = QHBoxLayout()
        form_left = QFormLayout()
        form_right = QFormLayout()

        self.lbl_f_id = QLabel("Auto (Mới)")
        self.txt_f_number = QLineEdit(); self.txt_f_number.setPlaceholderText("VD: VN999")
        self.txt_f_from = QLineEdit(); self.txt_f_from.setPlaceholderText("VD: HAN")
        self.txt_f_to = QLineEdit(); self.txt_f_to.setPlaceholderText("VD: PQC")
        
        self.date_f_dep = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_f_dep.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.date_f_arr = QDateTimeEdit(QDateTime.currentDateTime().addSecs(7200))
        self.date_f_arr.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        self.cb_f_status = QComboBox()
        self.cb_f_status.addItems(["PENDING", "DEPARTED", "CANCELLED"])

        form_left.addRow("ID:", self.lbl_f_id)
        form_left.addRow("Mã chuyến:", self.txt_f_number)
        form_left.addRow("Từ (Mã sân bay):", self.txt_f_from)
        form_left.addRow("Đến (Mã sân bay):", self.txt_f_to)
        
        form_right.addRow("Giờ đi:", self.date_f_dep)
        form_right.addRow("Giờ đến:", self.date_f_arr)
        form_right.addRow("Trạng thái:", self.cb_f_status)
        
        form_layout.addLayout(form_left); form_layout.addLayout(form_right)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Tải lại")
        btn_refresh.setObjectName("BtnOutline")
        btn_refresh.clicked.connect(self.load_flights)
        
        btn_clear = QPushButton("Làm Mới Form")
        btn_add = QPushButton("➕ Thêm Mới")
        btn_add.setObjectName("BtnSuccess")
        btn_update = QPushButton("✏️ Cập Nhật")
        btn_update.setStyleSheet("background-color: #F59E0B;")
        btn_delete = QPushButton("❌ Xóa")
        btn_delete.setObjectName("BtnDanger")

        btn_clear.clicked.connect(self.clear_flight_form)
        btn_add.clicked.connect(self.handle_add_flight)
        btn_update.clicked.connect(self.handle_update_flight)
        btn_delete.clicked.connect(self.handle_delete_flight)

        btn_layout.addWidget(btn_refresh); btn_layout.addWidget(btn_clear); btn_layout.addStretch()
        btn_layout.addWidget(btn_add); btn_layout.addWidget(btn_update); btn_layout.addWidget(btn_delete)
        layout.addLayout(btn_layout)
        self.load_flights()

    def load_flights(self):
        flights = self.admin_service.get_all_flights()
        self.table_flights.setRowCount(0)
        for row, f in enumerate(flights):
            self.table_flights.insertRow(row)
            self.table_flights.setItem(row, 0, QTableWidgetItem(str(f['flight_id'])))
            self.table_flights.setItem(row, 1, QTableWidgetItem(f['flight_number']))
            self.table_flights.setItem(row, 2, QTableWidgetItem(f['departure_code']))
            self.table_flights.setItem(row, 3, QTableWidgetItem(f['arrival_code']))
            self.table_flights.setItem(row, 4, QTableWidgetItem(str(f['departure_time'])))
            self.table_flights.setItem(row, 5, QTableWidgetItem(str(f['arrival_time'])))
            self.table_flights.setItem(row, 6, QTableWidgetItem(f['status']))

    def on_flight_table_click(self):
        row = self.table_flights.currentRow()
        if row < 0: return
        self.lbl_f_id.setText(self.table_flights.item(row, 0).text())
        self.txt_f_number.setText(self.table_flights.item(row, 1).text())
        self.txt_f_from.setText(self.table_flights.item(row, 2).text())
        self.txt_f_to.setText(self.table_flights.item(row, 3).text())
        self.cb_f_status.setCurrentText(self.table_flights.item(row, 6).text())
        
        time_format = "yyyy-MM-dd HH:mm:ss"
        dep_str = self.table_flights.item(row, 4).text()
        arr_str = self.table_flights.item(row, 5).text()
        self.date_f_dep.setDateTime(QDateTime.fromString(dep_str, time_format))
        self.date_f_arr.setDateTime(QDateTime.fromString(arr_str, time_format))

    def clear_flight_form(self):
        self.lbl_f_id.setText("Auto (Mới)")
        self.txt_f_number.clear(); self.txt_f_from.clear(); self.txt_f_to.clear()
        self.cb_f_status.setCurrentIndex(0)

    def handle_add_flight(self):
        if not self.txt_f_number.text().strip(): return QMessageBox.warning(self, "Lỗi", "Nhập Mã chuyến bay!")
        data = {
            'flight_number': self.txt_f_number.text().strip().upper(),
            'departure_code': self.txt_f_from.text().strip().upper(),
            'arrival_code': self.txt_f_to.text().strip().upper(),
            'departure_time': self.date_f_dep.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'arrival_time': self.date_f_arr.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'status': self.cb_f_status.currentText()
        }
        success, msg = self.admin_service.create_flight(data)
        if success: 
            self.load_flights(); self.clear_flight_form()
            QMessageBox.information(self, "Thành công", msg)
        else:
            QMessageBox.warning(self, "Thất bại", msg)

    def handle_update_flight(self):
        f_id = self.lbl_f_id.text()
        if f_id == "Auto (Mới)": return QMessageBox.warning(self, "Lỗi", "Chọn 1 chuyến bay để sửa!")
        data = {
            'flight_number': self.txt_f_number.text().strip().upper(),
            'departure_code': self.txt_f_from.text().strip().upper(),
            'arrival_code': self.txt_f_to.text().strip().upper(),
            'departure_time': self.date_f_dep.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'arrival_time': self.date_f_arr.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'status': self.cb_f_status.currentText()
        }
        success, msg = self.admin_service.update_flight(int(f_id), data)
        if success: self.load_flights()
        QMessageBox.information(self, "Kết quả", msg)

    def handle_delete_flight(self):
        f_id = self.lbl_f_id.text()
        if f_id == "Auto (Mới)": return QMessageBox.warning(self, "Lỗi", "Chọn 1 chuyến bay để xóa!")
        if QMessageBox.question(self, "Cảnh báo", "Chắc chắn muốn xóa?") == QMessageBox.StandardButton.Yes:
            success, msg = self.admin_service.delete_flight(int(f_id))
            if success: self.load_flights(); self.clear_flight_form()
            QMessageBox.information(self, "Kết quả", msg)

    # ==========================================
    # PHẦN 3: QUẢN LÝ SÂN BAY
    # ==========================================
    def setup_airport_tab(self):
        layout = QVBoxLayout(self.airport_tab)
        layout.setContentsMargins(16, 24, 16, 16)
        
        self.table_airports = QTableWidget(0, 4)
        self.table_airports.setHorizontalHeaderLabels(["Mã Sân Bay", "Tên Sân Bay", "Thành Phố", "Quốc Gia"])
        self.table_airports.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_airports.verticalHeader().setVisible(False)
        self.table_airports.setShowGrid(False)
        layout.addWidget(self.table_airports)

        form = QFormLayout()
        self.txt_a_code = QLineEdit(); self.txt_a_code.setPlaceholderText("VD: HAN")
        self.txt_a_name = QLineEdit(); self.txt_a_name.setPlaceholderText("VD: Nội Bài")
        self.txt_a_city = QLineEdit(); self.txt_a_city.setPlaceholderText("VD: Hà Nội")
        self.txt_a_country = QLineEdit(); self.txt_a_country.setText("Việt Nam")
        
        form.addRow("Mã Sân Bay (3 ký tự):", self.txt_a_code)
        form.addRow("Tên Sân Bay:", self.txt_a_name)
        form.addRow("Thành Phố:", self.txt_a_city)
        form.addRow("Quốc Gia:", self.txt_a_country)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Tải lại")
        btn_refresh.setObjectName("BtnOutline")
        btn_refresh.clicked.connect(self.load_airports)

        btn_add = QPushButton("➕ Thêm Sân Bay")
        btn_add.setObjectName("BtnSuccess")
        btn_add.clicked.connect(self.handle_add_airport)
        
        btn_del = QPushButton("❌ Xóa Sân Bay")
        btn_del.setObjectName("BtnDanger")
        btn_del.clicked.connect(self.handle_del_airport)
        
        btn_layout.addWidget(btn_refresh); btn_layout.addStretch()
        btn_layout.addWidget(btn_add); btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)
        self.load_airports()

    def load_airports(self):
        data = self.admin_service.get_all_airports()
        self.table_airports.setRowCount(0)
        for row, a in enumerate(data):
            self.table_airports.insertRow(row)
            self.table_airports.setItem(row, 0, QTableWidgetItem(a['airport_code']))
            self.table_airports.setItem(row, 1, QTableWidgetItem(a['name']))
            self.table_airports.setItem(row, 2, QTableWidgetItem(a['city']))
            self.table_airports.setItem(row, 3, QTableWidgetItem(a['country']))

    def handle_add_airport(self):
        success, msg = self.admin_service.add_airport(
            self.txt_a_code.text().strip(), self.txt_a_name.text().strip(), 
            self.txt_a_city.text().strip(), self.txt_a_country.text().strip()
        )
        if success: self.load_airports(); self.txt_a_code.clear()
        QMessageBox.information(self, "Kết quả", msg)

    def handle_del_airport(self):
        row = self.table_airports.currentRow()
        if row < 0: return QMessageBox.warning(self, "Lỗi", "Chọn 1 sân bay để xóa!")
        code = self.table_airports.item(row, 0).text()
        
        success, msg = self.admin_service.delete_airport(code)
        if success: self.load_airports()
        QMessageBox.information(self, "Kết quả", msg)

    # ==========================================
    # PHẦN 4: QUẢN LÝ VOUCHER (Bổ sung Bảng Thống kê)
    # ==========================================
    def setup_voucher_tab(self):
        layout = QVBoxLayout(self.voucher_tab)
        layout.setContentsMargins(16, 24, 16, 16)
        
        # 1. Bảng thống kê Voucher cho Admin
        self.table_vouchers = QTableWidget(0, 6)
        self.table_vouchers.setHorizontalHeaderLabels(["Mã Voucher", "% Giảm", "Giảm Tối Đa", "Lượt dùng / Tổng", "Tỷ lệ %", "Hạn Sử Dụng"])
        self.table_vouchers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_vouchers.verticalHeader().setVisible(False)
        self.table_vouchers.setShowGrid(False)
        layout.addWidget(self.table_vouchers, stretch=1)

        # 2. Form Tạo Voucher mới
        form_group = QGroupBox("Tạo Mã Khuyến Mãi Mới")
        form = QFormLayout(form_group)
        
        self.txt_v_code = QLineEdit(); self.txt_v_code.setPlaceholderText("VD: SIEUSALE50")
        self.txt_v_discount = QLineEdit(); self.txt_v_discount.setPlaceholderText("VD: 15 (Tương đương 15%)")
        self.txt_v_max_discount = QLineEdit(); self.txt_v_max_discount.setPlaceholderText("VD: 500000 (VND)")
        self.txt_v_limit = QLineEdit(); self.txt_v_limit.setPlaceholderText("VD: 100 (lượt)")
        
        # Lịch có Giờ/Phút chuẩn
        self.date_v_expiry = QDateTimeEdit(QDateTime.currentDateTime().addDays(30))
        self.date_v_expiry.setCalendarPopup(True)
        self.date_v_expiry.setDisplayFormat("dd/MM/yyyy HH:mm") 
        
        calendar_v = self.date_v_expiry.calendarWidget()
        calendar_v.setGridVisible(True)
        calendar_v.setStyleSheet("""
            QCalendarWidget QWidget { background-color: #1E293B; color: #F8FAFC; }
            QCalendarWidget QToolButton { color: #F8FAFC; font-weight: bold; }
            QCalendarWidget QTableView { selection-background-color: #3B82F6; }
        """)
        
        form.addRow("Mã Voucher (*):", self.txt_v_code)
        form.addRow("% Giảm giá (*):", self.txt_v_discount)
        form.addRow("Giảm tối đa (VND):", self.txt_v_max_discount)
        form.addRow("Số lượt tối đa:", self.txt_v_limit)
        form.addRow("Ngày hết hạn:", self.date_v_expiry)
        
        btn_layout = QHBoxLayout()
        btn_refresh_v = QPushButton("🔄 Tải lại")
        btn_refresh_v.setObjectName("BtnOutline")
        btn_refresh_v.clicked.connect(self.load_vouchers)

        btn_add_v = QPushButton("🎟️ Tạo Voucher")
        btn_add_v.setObjectName("BtnSuccess")
        btn_add_v.clicked.connect(self.handle_add_voucher)
        
        btn_disable_v = QPushButton("🔒 Khóa Voucher")
        btn_disable_v.setStyleSheet("background-color: #F59E0B; color: white;")
        btn_disable_v.clicked.connect(self.handle_disable_voucher)
        
        btn_layout.addWidget(btn_refresh_v); btn_layout.addStretch()
        btn_layout.addWidget(btn_add_v); btn_layout.addWidget(btn_disable_v)
        form.addRow("", btn_layout)
        
        layout.addWidget(form_group)
        self.load_vouchers()

    def load_vouchers(self):
        # Tránh lỗi sập phần mềm nếu Service chưa kịp viết hàm get_all_vouchers
        if not hasattr(self.admin_service, 'get_all_vouchers'):
            self.table_vouchers.setRowCount(1)
            self.table_vouchers.setItem(0, 0, QTableWidgetItem("Cần bổ sung"))
            self.table_vouchers.setItem(0, 1, QTableWidgetItem("hàm get_all_vouchers()"))
            self.table_vouchers.setItem(0, 2, QTableWidgetItem("vào AdminService"))
            return

        vouchers = self.admin_service.get_all_vouchers()
        self.table_vouchers.setRowCount(0)
        if vouchers:
            for row, v in enumerate(vouchers):
                self.table_vouchers.insertRow(row)
                self.table_vouchers.setItem(row, 0, QTableWidgetItem(v.get('voucher_code', '')))
                self.table_vouchers.setItem(row, 1, QTableWidgetItem(f"{float(v.get('discount_percent', 0))}%"))
                
                max_disc = v.get('max_discount')
                max_disc_str = f"{float(max_disc):,.0f} VND" if max_disc else "Không giới hạn"
                self.table_vouchers.setItem(row, 2, QTableWidgetItem(max_disc_str))
                
                used = v.get('used_count', 0)
                limit = v.get('usage_limit', 0)
                self.table_vouchers.setItem(row, 3, QTableWidgetItem(f"{used} / {limit}"))
                
                ratio = (used / limit * 100) if limit > 0 else 0
                self.table_vouchers.setItem(row, 4, QTableWidgetItem(f"{ratio:.1f}%"))
                self.table_vouchers.setItem(row, 5, QTableWidgetItem(str(v.get('expiry_date', ''))))

    def handle_add_voucher(self):
        try:
            code = self.txt_v_code.text().strip()
            # Tự động convert lại thành chuẩn SQL (yyyy-MM-dd HH:mm:ss) để đẩy xuống DB
            sql_date_format = self.date_v_expiry.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            
            success, msg = self.admin_service.create_voucher(
                code, float(self.txt_v_discount.text() or 0), float(self.txt_v_max_discount.text() or 0), 
                sql_date_format, int(self.txt_v_limit.text() or 0)
            )
            if success: 
                self.txt_v_code.clear()
                self.load_vouchers()
            QMessageBox.information(self, "Kết quả", msg)
        except ValueError:
            QMessageBox.critical(self, "Lỗi", "Nhập sai định dạng số!")

    def handle_disable_voucher(self):
        code = self.txt_v_code.text().strip()
        if not code: return QMessageBox.warning(self, "Lỗi", "Nhập Mã Voucher cần khóa!")
        success, msg = self.admin_service.disable_voucher(code)
        if success: self.load_vouchers()
        QMessageBox.information(self, "Kết quả", msg)