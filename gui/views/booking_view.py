# gui/views/booking_view.py
import re
import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QScrollArea, QDialog, QSizePolicy, QMenu)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QPixmap, QFont
from bll.booking_service import BookingService

class AdminQRPaymentPopup(QDialog):
    def __init__(self, amount, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thanh toán vé qua cổng QR")
        self.setFixedSize(380, 520)
        self.setStyleSheet("background-color: #1E293B; color: white; font-family: 'Segoe UI';")
        self.time_left = 900 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        layout.addWidget(QLabel("QUÉT MÃ QR THANH TOÁN", styleSheet="font-size:16px; font-weight:bold; color:#38BDF8;"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_qr = QLabel()
        
        # --- VŨ KHÍ TỐI THƯỢNG: LẤY GỐC TỪ MAIN.PY ---
        base_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        # Bắt cả 2 trường hợp: Tên chuẩn và Tên bị Windows lừa
        qr_path_1 = os.path.join(base_dir, "gui", "assets", "my_qr.png")
        qr_path_2 = os.path.join(base_dir, "gui", "assets", "my_qr.png.png")
        
        # Logic kiểm tra cực gắt
        if os.path.exists(qr_path_1):
            pixmap = QPixmap(qr_path_1)
            if not pixmap.isNull():
                self.lbl_qr.setPixmap(pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                self.lbl_qr.setText("[ ẢNH BỊ LỖI: Tìm thấy file my_qr.png nhưng không đọc được. Có thể bạn đã đổi đuôi file sai cách (JPG/WebP -> PNG). ]")
                self.lbl_qr.setStyleSheet("border: 2px dashed #F59E0B; color: #F59E0B; padding: 10px;")
        
        elif os.path.exists(qr_path_2):
            pixmap = QPixmap(qr_path_2)
            if not pixmap.isNull():
                self.lbl_qr.setPixmap(pixmap.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                self.lbl_qr.setText("[ ẢNH BỊ LỖI: Tìm thấy file my_qr.png.png nhưng không đọc được. ]")
                self.lbl_qr.setStyleSheet("border: 2px dashed #F59E0B; color: #F59E0B; padding: 10px;")
                
        else:
            # In thẳng đường dẫn ra để bạn dễ dàng debug
            self.lbl_qr.setText(f"[ CẢNH BÁO: Không tìm thấy ảnh ở đường dẫn:\n{qr_path_1} ]")
            self.lbl_qr.setStyleSheet("border: 2px dashed #EF4444; color: #EF4444; padding: 10px; font-size: 12px;")
            
        self.lbl_qr.setFixedSize(240, 240)
        self.lbl_qr.setWordWrap(True)
        self.lbl_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_qr, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(QLabel(f"Số tiền: <b>{amount:,.0f} VNĐ</b>", styleSheet="font-size:18px; color:#10B981;"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel(f"Nội dung chuyển khoản: {content}", styleSheet="font-size:14px; color:#94A3B8;"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_timer = QLabel("Thời gian giữ giao dịch: 15:00")
        self.lbl_timer.setStyleSheet("color:#EF4444; font-weight:bold; font-size:14px;")
        layout.addWidget(self.lbl_timer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn_confirm = QPushButton("✅ ĐÃ CHUYỂN KHOẢN")
        btn_confirm.setStyleSheet("background-color:#10B981; color:#0F172A; font-weight:bold; padding:12px; border-radius:8px;")
        btn_confirm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_confirm.clicked.connect(self.accept)
        layout.addWidget(btn_confirm)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_timer)
        self.timer.start(1000)

    def tick_timer(self):
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        self.lbl_timer.setText(f"Thời gian giữ giao dịch: {mins:02d}:{secs:02d}")
        if self.time_left <= 0:
            self.timer.stop()
            self.reject()

class BookingScreen(QWidget):
    def __init__(self, parent_main=None):
        super().__init__()
        self.service = BookingService()
        self.current_flight = None
        self.selected_seats = {} 
        self.dynamic_inputs = {} 
        self.setup_ui()
        self.load_vouchers()
        self.refresh_flights()

    def apply_role_permissions(self, user):
        pass

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
            QFrame#Card { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QLineEdit { padding: 10px 16px; border-radius: 8px; background-color: #0F172A; border: 1px solid #475569; color: white; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #38BDF8; }
            QTableWidget { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; gridline-color: #334155; outline: none; }
            QHeaderView::section { background-color: #0F172A; color: #94A3B8; padding: 12px 16px; font-weight: bold; border: none; text-align: left; }
            QTableWidget::item { padding: 8px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QPushButton { font-weight: bold; border-radius: 8px; padding: 10px 16px; font-size: 14px; }
            QPushButton#BtnTool { background: #1E293B; border: 1px solid #475569; color: #F8FAFC; }
            QPushButton#BtnTool:hover { background: #38BDF8; color: #0F172A; border-color: #38BDF8; }
            
            QScrollBar:vertical { background: #0F172A; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #475569; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar:horizontal { background: #0F172A; height: 10px; margin: 0px; }
            QScrollBar::handle:horizontal { background: #475569; min-width: 20px; border-radius: 5px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(24)

        left_widget = QWidget()
        left_widget.setMinimumWidth(450)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        
        toolbar_lay = QHBoxLayout()
        lbl_title = QLabel("🛫 LỊCH TRÌNH BAY KHAI THÁC")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 900; color: #38BDF8;")
        lbl_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar_lay.addWidget(lbl_title)
        
        btn_reload = QPushButton("🔄 Tải lại"); btn_reload.setObjectName("BtnTool")
        btn_reload.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reload.clicked.connect(self.refresh_flights)
        toolbar_lay.addWidget(btn_reload)
        left_layout.addLayout(toolbar_lay)
        
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Chuyến bay", "Khởi hành", "Hạ cánh", "Ghế trống", "Giá cơ bản"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) 
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_flight_double_clicked)
        left_layout.addWidget(self.table)
        
        main_layout.addWidget(left_widget, 5)

        right_panel = QFrame()
        right_panel.setObjectName("Card")
        right_panel.setMinimumWidth(500)
        self.r_lay = QVBoxLayout(right_panel)
        self.r_lay.setContentsMargins(24, 24, 24, 24)
        self.r_lay.setSpacing(16)
        
        self.lbl_flight_info = QLabel("Vui lòng Double-click chọn chuyến bay bên trái")
        self.lbl_flight_info.setStyleSheet("font-size: 16px; font-weight: bold; color: #10B981;")
        self.lbl_flight_info.setWordWrap(True)
        self.r_lay.addWidget(self.lbl_flight_info)

        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.sc_lay = QVBoxLayout(self.scroll_content)
        self.sc_lay.setContentsMargins(0, 0, 16, 0) 
        self.sc_lay.setSpacing(24)

        # KHU VỰC SƠ ĐỒ GHẾ
        self.seat_scroll = QScrollArea()
        self.seat_scroll.setWidgetResizable(True)
        self.seat_scroll.setStyleSheet("QScrollArea { border: 1px solid #334155; border-radius: 8px; background: rgba(0,0,0,0.15); }")
        self.seat_scroll.setMinimumHeight(240)
        
        self.w_seat_map = QWidget()
        self.w_seat_map.setStyleSheet("background: transparent;")
        self.grid_seats = QGridLayout(self.w_seat_map)
        self.grid_seats.setSpacing(8)
        self.grid_seats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.seat_scroll.setWidget(self.w_seat_map)
        self.sc_lay.addWidget(self.seat_scroll)

        # KHU VỰC VOUCHER
        v_box = QVBoxLayout(); v_box.setSpacing(12)
        v_box.addWidget(QLabel("🎟️ ÁP DỤNG VOUCHER KHUYẾN MÃI", styleSheet="color: #38BDF8; font-weight: bold; font-size: 14px;"))
        
        self.table_vouchers = QTableWidget(0, 3)
        self.table_vouchers.setHorizontalHeaderLabels(["Mã Code", "Giảm (%)", "Giảm Tối đa"])
        self.table_vouchers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_vouchers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_vouchers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_vouchers.doubleClicked.connect(self.apply_voucher_from_table)
        self.table_vouchers.setFixedHeight(120)
        v_box.addWidget(self.table_vouchers)

        self.in_global_voucher = QLineEdit()
        self.in_global_voucher.setPlaceholderText("Nhập hoặc click đúp mã trên bảng để áp dụng...")
        self.in_global_voucher.textChanged.connect(self.update_prices_only)
        v_box.addWidget(self.in_global_voucher)
        self.sc_lay.addLayout(v_box)

        # KHU VỰC LIÊN HỆ ĐOÀN
        self.contact_widget = QWidget()
        self.contact_widget.setStyleSheet("background: transparent;")
        c_lay = QVBoxLayout(self.contact_widget)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(12)
        c_lay.addWidget(QLabel("👤 NGƯỜI LIÊN HỆ ĐOÀN", styleSheet="color: #38BDF8; font-weight: bold; font-size: 14px;"))
        
        self.contact_box = QHBoxLayout(); self.contact_box.setSpacing(16)
        self.in_c_name = QLineEdit(); self.in_c_name.setPlaceholderText("Tên Trưởng đoàn (*)")
        self.in_c_phone = QLineEdit(); self.in_c_phone.setPlaceholderText("SĐT liên hệ đoàn (*)")
        self.contact_box.addWidget(self.in_c_name); self.contact_box.addWidget(self.in_c_phone)
        c_lay.addLayout(self.contact_box)
        self.sc_lay.addWidget(self.contact_widget)

        # KHU VỰC HÀNH KHÁCH
        p_box = QVBoxLayout(); p_box.setSpacing(12)
        p_box.addWidget(QLabel("👥 THÔNG TIN HÀNH KHÁCH CHUYẾN NÀY", styleSheet="color: #38BDF8; font-weight: bold; font-size: 14px;"))
        
        self.form_container = QWidget()
        self.form_container.setStyleSheet("background: transparent;")
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(16)
        self.form_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        p_box.addWidget(self.form_container)
        self.sc_lay.addLayout(p_box)
        
        self.sc_lay.addStretch()
        self.main_scroll.setWidget(self.scroll_content)
        self.r_lay.addWidget(self.main_scroll)

        bill_frame = QFrame()
        bill_frame.setStyleSheet("background-color: #0F172A; border-radius: 8px; border: 1px solid #334155; padding: 12px;")
        bill_lay = QVBoxLayout(bill_frame)
        bill_lay.setContentsMargins(16, 12, 16, 12)
        
        self.lbl_invoice = QLabel("Số ghế chọn: 0 | TỔNG TIỀN: 0 VNĐ")
        self.lbl_invoice.setStyleSheet("font-size: 16px; color: #F59E0B; font-weight: 900;")
        self.lbl_invoice.setAlignment(Qt.AlignmentFlag.AlignRight)
        bill_lay.addWidget(self.lbl_invoice)
        self.r_lay.addWidget(bill_frame)

        btn_box = QHBoxLayout(); btn_box.setSpacing(16)
        btn_hold = QPushButton("⏳ GIỮ CHỖ (15P)"); btn_hold.setStyleSheet("background-color: #F59E0B; color: #0F172A;")
        btn_cash = QPushButton("💵 TIỀN MẶT"); btn_cash.setStyleSheet("background-color: #38BDF8; color: #0F172A;")
        btn_qr = QPushButton("📲 QUÉT MÃ QR"); btn_qr.setStyleSheet("background-color: #10B981; color: #0F172A;")
        
        for b in [btn_hold, btn_cash, btn_qr]: 
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setFixedHeight(48) 
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            
        btn_hold.clicked.connect(lambda: self.execute_submit(is_hold=True, method='CASH'))
        btn_cash.clicked.connect(lambda: self.execute_submit(is_hold=False, method='CASH'))
        btn_qr.clicked.connect(lambda: self.execute_submit(is_hold=False, method='VNPAY'))
        
        btn_box.addWidget(btn_hold); btn_box.addWidget(btn_cash); btn_box.addWidget(btn_qr)
        self.r_lay.addLayout(btn_box)

        main_layout.addWidget(right_panel, 5)
        self.toggle_contact_section(False)

    def load_vouchers(self):
        vouchers = self.service.get_active_vouchers()
        self.table_vouchers.setRowCount(0)
        for r, v in enumerate(vouchers):
            self.table_vouchers.insertRow(r)
            self.table_vouchers.setItem(r, 0, QTableWidgetItem(v['code']))
            self.table_vouchers.setItem(r, 1, QTableWidgetItem(f"{float(v['discount_percent'])}%"))
            self.table_vouchers.setItem(r, 2, QTableWidgetItem(f"{float(v['max_discount']):,.0f} đ" if v['max_discount'] else "Không giới hạn"))

    def apply_voucher_from_table(self):
        row = self.table_vouchers.currentRow()
        if row >= 0:
            self.in_global_voucher.setText(self.table_vouchers.item(row, 0).text())

    def refresh_flights(self):
        self.flights_cache = self.service.get_all_active_flights()
        self.table.setRowCount(0)
        for r, f in enumerate(self.flights_cache):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(f['flight_id'])))
            flight_name = f.get('flight_number', 'N/A')
            dep = f.get('departure_code', '')
            arr = f.get('arrival_code', '')
            self.table.setItem(r, 1, QTableWidgetItem(f"{flight_name} ({dep}-{arr})"))
            self.table.setItem(r, 2, QTableWidgetItem(f['departure_time'].strftime('%d/%m %H:%M')))
            self.table.setItem(r, 3, QTableWidgetItem(f['arrival_time'].strftime('%d/%m %H:%M')))
            
            seat_item = QTableWidgetItem(str(f['available_seats']))
            if f['available_seats'] < 5: seat_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(r, 4, seat_item)
            self.table.setItem(r, 5, QTableWidgetItem(f"{float(f['base_price']):,.0f}"))

    def on_flight_double_clicked(self):
        r = self.table.currentRow()
        if r < 0: return
        f_id = int(self.table.item(r, 0).text())
        self.current_flight = next(f for f in self.flights_cache if f['flight_id'] == f_id)
        self.lbl_flight_info.setText(f"✈ {self.current_flight['flight_number']} ({self.current_flight['dep_city']} ➔ {self.current_flight['arr_city']})")
        
        # Reset hoàn toàn Form khi đổi chuyến
        self.selected_seats.clear()
        self.in_global_voucher.clear() 
        self.update_dynamic_passenger_forms()
        self.render_visual_seat_map(f_id)

    # =========================================================
    # RENDER SƠ ĐỒ GHẾ & PHÂN TÍCH MÀU SẮC ĐỘNG
    # =========================================================
    def get_seat_bg_color(self, class_name: str) -> str:
        """Hàm phân tích mã màu cho các hạng ghế mới do Admin tạo ra"""
        cls_upper = str(class_name).upper()
        if 'BUSINESS' in cls_upper or 'THƯƠNG GIA' in cls_upper:
            return "#3B82F6"  # Màu Xanh Lam (Thương gia chuẩn)
        elif 'ECONOMY' in cls_upper or 'PHỔ THÔNG' in cls_upper:
            return "#10B981"  # Màu Xanh Ngọc (Phổ thông chuẩn)
        else:
            return "#A855F7"  # Màu Tím Vương Giả (Dành riêng cho các Hạng cấu hình mới như CHÀO BẠN MỚI)

    def render_visual_seat_map(self, flight_id):
        while self.grid_seats.count():
            i = self.grid_seats.takeAt(0)
            if i.widget(): i.widget().deleteLater()
            
        seats = self.service.fetch_seat_map(flight_id)
        row_map, curr_row = {}, 0
        for s in seats:
            match = re.match(r"([A-Za-z]+)(\d+)", s['seat_number'])
            if not match: continue
            letter, num = match.groups()
            
            if letter not in row_map:
                row_map[letter] = curr_row
                row_lbl = QLabel(f"<b>{letter}</b>")
                row_lbl.setStyleSheet("color:#94A3B8; font-size:14px; padding: 4px;")
                row_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid_seats.addWidget(row_lbl, curr_row, 0)
                curr_row += 1

            btn = QPushButton(s['seat_number'])
            btn.setFixedSize(48, 48) 
            btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            
            # --- TÍNH NĂNG GIAI ĐOẠN 4: GẮN CONTEXT MENU CHUỘT PHẢI ---
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, seat_data=s, button=btn: self.show_seat_context_menu(pos, seat_data, button))

            # Nếu ghế đang có người chọn ở Form bên phải (Trường hợp Load lại sơ đồ do đổi hạng)
            if s['seat_id'] in self.selected_seats:
                btn.setStyleSheet("background-color: #F59E0B; color: #0F172A; border-radius: 6px;")
            elif s['seat_status'] == 'AVAILABLE':
                bg_color = self.get_seat_bg_color(s['class_name'])
                btn.setStyleSheet(f"background-color: {bg_color}; color: white; border-radius: 6px;")
                btn.clicked.connect(lambda _, seat=s, b=btn: self.on_seat_toggled(seat, b))
            else:
                btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 6px;")
                btn.setEnabled(False)

            col_index = int(num) if int(num) <= 2 else int(num) + 1
            self.grid_seats.addWidget(btn, row_map[letter], col_index)

    # =========================================================
    # MA THUẬT GIAI ĐOẠN 4: XỬ LÝ CONTEXT MENU (CHUỘT PHẢI)
    # =========================================================
    def show_seat_context_menu(self, pos, seat_data, button):
        """Bật popup menu đổi hạng ghế với giao diện mượt mà"""
        if seat_data['seat_status'] != 'AVAILABLE':
            QMessageBox.warning(self, "Cảnh báo bảo mật", "Chỉ có thể thay đổi cấu hình cho những ghế đang trống (AVAILABLE).")
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155; border-radius: 8px; padding: 6px; }
            QMenu::item { padding: 8px 24px; border-radius: 4px; font-weight: 600; font-size: 13px; }
            QMenu::item:selected { background-color: #38BDF8; color: #0F172A; }
        """)
        
        # Tiêu đề tĩnh
        title_action = menu.addAction(f"⚙️ ĐỔI HẠNG CHO GHẾ {seat_data['seat_number']}")
        title_action.setEnabled(False)
        menu.addSeparator()

        # Quét CSDL hiển thị các hạng ghế hiện có
        classes = self.service.get_all_seat_classes()
        for cls in classes:
            is_current = " (Hiện tại)" if cls['class_id'] == seat_data['class_id'] else ""
            action = menu.addAction(f"{cls['class_name']} - Hệ số x{cls['price_multiplier']}{is_current}")
            
            if not is_current:
                action.triggered.connect(lambda checked, s_id=seat_data['seat_id'], c_id=cls['class_id']: self.change_seat_class_trigger(s_id, c_id))
            else:
                action.setEnabled(False) # Không cho đổi sang chính hạng đang dùng
                
        menu.exec(button.mapToGlobal(pos))

    def change_seat_class_trigger(self, seat_id, class_id):
        """Kích hoạt Update DB và Tải lại màn hình"""
        success, msg = self.service.update_seat_class(seat_id, class_id)
        if success:
            # Hủy chọn ghế nếu đang chọn (để tránh sai lệch hóa đơn), sau đó tải lại sơ đồ ghế
            if seat_id in self.selected_seats:
                del self.selected_seats[seat_id]
                self.update_dynamic_passenger_forms()
                
            if self.current_flight:
                self.render_visual_seat_map(self.current_flight['flight_id'])
        else:
            QMessageBox.critical(self, "Lỗi Cấu Hình", msg)

    # =========================================================
    # TIẾN TRÌNH ĐẶT VÉ VÀ TÍNH HÓA ĐƠN
    # =========================================================
    def on_seat_toggled(self, seat_data, btn):
        s_id = seat_data['seat_id']
        if s_id in self.selected_seats:
            del self.selected_seats[s_id]
            # Trả lại màu nền động gốc theo hạng ghế khi khách bỏ chọn
            bg_color = self.get_seat_bg_color(seat_data['class_name'])
            btn.setStyleSheet(f"background-color: {bg_color}; color: white; border-radius: 6px;")
        else:
            self.selected_seats[s_id] = seat_data
            # Khi chọn thì tô màu vàng cam nổi bật
            btn.setStyleSheet("background-color: #F59E0B; color: #0F172A; border-radius: 6px;")
        self.update_dynamic_passenger_forms()

    def toggle_contact_section(self, visible):
        self.contact_widget.setVisible(visible)

    def update_dynamic_passenger_forms(self):
        while self.form_layout.count():
            i = self.form_layout.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        self.dynamic_inputs.clear()
        
        self.toggle_contact_section(len(self.selected_seats) > 1)
        
        if not self.selected_seats:
            self.form_layout.addWidget(QLabel("Vui lòng click chọn ghế trống trên sơ đồ...", styleSheet="color:#64748B;"))
            self.lbl_invoice.setText("Số ghế chọn: 0 | TỔNG TIỀN: 0 VNĐ")
            return

        for s_id, seat in self.selected_seats.items():
            box = QFrame()
            box.setStyleSheet("background-color: rgba(255,255,255,0.03); border: 1px solid #334155; border-radius: 8px; padding: 12px;")
            b_lay = QVBoxLayout(box)
            b_lay.setContentsMargins(12, 12, 12, 12)
            b_lay.setSpacing(12)
            
            lbl_price = QLabel()
            lbl_price.setStyleSheet("color:#38BDF8; font-size:14px; font-weight: bold;")
            b_lay.addWidget(lbl_price)
            
            inputs_box = QHBoxLayout(); inputs_box.setSpacing(16)
            in_name = QLineEdit(); in_name.setPlaceholderText("Họ và Tên (*)")
            in_phone = QLineEdit(); in_phone.setPlaceholderText("SĐT (*)")
            in_id = QLineEdit(); in_id.setPlaceholderText("CCCD (*)")
            
            inputs_box.addWidget(in_name); inputs_box.addWidget(in_phone); inputs_box.addWidget(in_id)
            b_lay.addLayout(inputs_box)
            
            self.form_layout.addWidget(box)
            self.dynamic_inputs[s_id] = {'name': in_name, 'phone': in_phone, 'id': in_id, 'seat': seat, 'price': 0, 'lbl_price': lbl_price, 'voucher_id': None}

        self.update_prices_only()

    def update_prices_only(self):
        if not self.selected_seats: return
        
        voucher_code = self.in_global_voucher.text().strip()
        voucher = None
        if voucher_code:
            ok, msg, voucher = self.service.validate_voucher(voucher_code)
            if not ok: voucher = None
        
        total_bill = 0
        for s_id, fields in self.dynamic_inputs.items():
            seat = fields['seat']
            pricing = self.service.calculate_final_price(
                float(self.current_flight['base_price']),
                float(seat['price_multiplier']),
                voucher
            )
            fields['price'] = pricing['final_price']
            fields['voucher_id'] = voucher['voucher_id'] if voucher else None
            
            fields['lbl_price'].setText(f"💺 Ghế: {seat['seat_number']} ({seat['class_name']}) | Giá: {pricing['final_price']:,.0f} đ (Giảm {pricing['discount_amount']:,.0f} đ)")
            total_bill += pricing['final_price']
        
        self.lbl_invoice.setText(f"Số ghế chọn: {len(self.selected_seats)} | TỔNG CỘNG: {total_bill:,.0f} VNĐ")

    def execute_submit(self, is_hold: bool, method: str):
        if not self.current_flight or not self.selected_seats:
            return QMessageBox.warning(self, "Lỗi nghiệp vụ", "Vui lòng chọn chuyến bay và click vị trí ghế ngồi trước!")

        contact_info = {'name': self.in_c_name.text().strip(), 'phone': self.in_c_phone.text().strip()}
        if len(self.selected_seats) == 1:
            first_item = list(self.dynamic_inputs.values())[0]
            contact_info['name'] = first_item['name'].text().strip()
            contact_info['phone'] = first_item['phone'].text().strip()

        passengers_list = []
        total_final_price = 0
        for s_id, fields in self.dynamic_inputs.items():
            price_val = fields['price']
            total_final_price += price_val
            passengers_list.append({
                'seat_id': s_id,
                'seat_number': fields['seat']['seat_number'],
                'base_price': float(self.current_flight['base_price']),
                'final_price': price_val,
                'voucher_id': fields['voucher_id'], 
                'name': fields['name'].text().strip(),
                'phone': fields['phone'].text().strip(),
                'id_card': fields['id'].text().strip()
            })

        if method == 'VNPAY' and not is_hold:
            popup = AdminQRPaymentPopup(total_final_price, f"DOAN_FLIGHT_{self.current_flight['flight_number']}")
            if popup.exec() != QDialog.DialogCode.Accepted:
                return QMessageBox.information(self, "Hủy giao dịch", "Giao dịch qua mã QR đã bị hủy bỏ từ nhân viên.")

        success, message = self.service.validate_and_process_admin_booking(
            self.current_flight['flight_id'], contact_info, passengers_list, is_hold, method
        )
        
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.in_c_name.clear(); self.in_c_phone.clear()
            self.on_flight_double_clicked()
            self.refresh_flights()
        else:
            QMessageBox.critical(self, "Thất bại", message)