# gui/views/customer_booking_view.py
import re
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QLineEdit, 
                             QStackedWidget, QMessageBox, QComboBox, QScrollArea, QDateEdit, QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from bll.booking_service import BookingService

# =======================================================
# 1. FLIGHT CARD WIDGET
# =======================================================
class FlightCardWidget(QFrame):
    def __init__(self, flight, parent_view):
        super().__init__()
        self.flight = flight
        self.parent_view = parent_view
        self.setFixedHeight(140)
        self.setStyleSheet("""
            QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QFrame:hover { border: 1px solid #3B82F6; background-color: #26354A; }
            QLabel { color: #F8FAFC; border: none; }
        """)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(15); shadow.setColor(QColor(0,0,0,80)); shadow.setOffset(0,4)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self); layout.setContentsMargins(24, 20, 24, 20)
        
        # Trái: Giờ bay
        v_lay = QVBoxLayout()
        v_lay.addWidget(QLabel(flight['departure_time'].strftime("%H:%M"), styleSheet="font-size:24px; font-weight:bold; color:#38BDF8;"))
        v_lay.addWidget(QLabel(flight['dep_city'], styleSheet="color:#94A3B8;"))
        
        arr_lbl = QLabel(" ─── ✈ ─── "); arr_lbl.setStyleSheet("font-size:18px; color:#475569;")
        
        v_lay2 = QVBoxLayout()
        v_lay2.addWidget(QLabel(flight['arrival_time'].strftime("%H:%M"), styleSheet="font-size:24px; font-weight:bold; color:#38BDF8;"))
        v_lay2.addWidget(QLabel(flight['arr_city'], styleSheet="color:#94A3B8;"))
        
        r_lay = QHBoxLayout(); r_lay.addLayout(v_lay); r_lay.addWidget(arr_lbl); r_lay.addLayout(v_lay2); r_lay.addStretch()
        layout.addLayout(r_lay, stretch=3)

        # Phải: Giá và Nút
        act = QVBoxLayout()
        act.addWidget(QLabel(f"✈ {flight['flight_number']}", styleSheet="color:#64748B; font-weight:bold;"), alignment=Qt.AlignmentFlag.AlignRight)
        act.addWidget(QLabel(f"Từ {float(flight['base_price']):,.0f} đ", styleSheet="font-size:20px; color:#10B981; font-weight:bold;"), alignment=Qt.AlignmentFlag.AlignRight)
        
        btn = QPushButton("CHỌN CHUYẾN"); btn.setFixedSize(140, 45)
        btn.setStyleSheet("background-color: #3B82F6; color: white; border-radius: 8px; font-weight: bold;")
        if flight['available_seats'] == 0:
            btn.setEnabled(False); btn.setText("HẾT VÉ"); btn.setStyleSheet("background-color: #475569; border-radius:8px;")
        else:
            btn.clicked.connect(lambda: self.parent_view.go_to_booking_detail(self.flight))
        act.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(act, stretch=2)

# =======================================================
# 2. TICKET CARD WIDGET (Hiển thị Lookup)
# =======================================================
class TicketCardWidget(QFrame):
    def __init__(self, tkt, parent_view):
        super().__init__()
        self.setStyleSheet("background-color: #1E293B; border-radius: 8px; border: 1px solid #334155;")
        self.setFixedHeight(120)
        layout = QHBoxLayout(self)
        
        info = QVBoxLayout()
        info.addWidget(QLabel(f"🎫 MÃ PNR: {tkt['ticket_code']}", styleSheet="color:#38BDF8; font-weight:bold; font-size:16px;"))
        info.addWidget(QLabel(f"Chuyến: {tkt['flight_number']} | Khởi hành: {tkt['departure_time'].strftime('%d/%m/%Y %H:%M')}", styleSheet="color:#94A3B8;"))
        info.addWidget(QLabel(f"Hành khách: {tkt['full_name']} | Ghế: {tkt['seat_number']} ({tkt['ticket_class']})"))
        layout.addLayout(info, stretch=2)
        
        right_info = QVBoxLayout()
        color = "#10B981" if tkt['ticket_status'] == 'BOOKED' else "#F59E0B" if tkt['ticket_status'] == 'HELD' else "#EF4444"
        right_info.addWidget(QLabel(f"Trạng thái: {tkt['ticket_status']}", styleSheet=f"color:{color}; font-weight:bold; font-size: 14px;"), alignment=Qt.AlignmentFlag.AlignRight)
        right_info.addWidget(QLabel(f"Giá vé: {float(tkt['final_price']):,.0f} đ", styleSheet="color:#10B981; font-weight:bold; font-size:16px;"), alignment=Qt.AlignmentFlag.AlignRight)
        
        if tkt['ticket_status'] in ['BOOKED', 'HELD']:
            btn_cancel = QPushButton("Hủy Vé")
            btn_cancel.setFixedSize(100, 30)
            btn_cancel.setStyleSheet("background-color: #EF4444; color: white; border-radius: 4px; font-weight: bold;")
            btn_cancel.clicked.connect(lambda: parent_view.cancel_my_ticket(tkt['ticket_id']))
            right_info.addWidget(btn_cancel, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(right_info, stretch=1)

# =======================================================
# 3. QR PAYMENT DIALOG
# =======================================================
class QRPaymentDialog(QDialog):
    def __init__(self, booking_code, total_amount, service, parent=None):
        super().__init__(parent)
        self.booking_code = booking_code
        self.total_amount = total_amount
        self.service = service
        self.time_left = 900  # 15 phút
        self.is_paid = False
        self.setup_ui()
        self.start_timer()

    def setup_ui(self):
        self.setWindowTitle("Thanh toán QR Code")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #0F172A; color: white; border-radius: 10px;")
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("💳 QUÉT MÃ QR ĐỂ THANH TOÁN", styleSheet="font-size: 20px; font-weight: bold; color: #10B981;"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_timer = QLabel("⏳ Thời gian giữ ghế: 15:00")
        self.lbl_timer.setStyleSheet("font-size: 18px; color: #F59E0B; font-weight: bold;")
        layout.addWidget(self.lbl_timer, alignment=Qt.AlignmentFlag.AlignCenter)

        qr_lbl = QLabel()
        qr_path = "my_qr.png"
        if os.path.exists(qr_path):
            pixmap = QPixmap(qr_path).scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            qr_lbl.setPixmap(pixmap)
        else:
            qr_lbl.setText("[ Lỗi: Không tìm thấy my_qr.png ]")
        qr_lbl.setStyleSheet("background-color: white; padding: 10px; border-radius: 8px;")
        layout.addWidget(qr_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        info = QFrame()
        info.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 15px;")
        i_lay = QVBoxLayout(info)
        i_lay.addWidget(QLabel(f"Mã Đặt Chỗ: {self.booking_code}", styleSheet="font-size:16px; font-weight:bold;"))
        i_lay.addWidget(QLabel(f"Tổng Tiền: {self.total_amount:,.0f} VNĐ", styleSheet="font-size:20px; color:#10B981; font-weight:bold;"))
        layout.addWidget(info)

        btn_confirm = QPushButton("✅ TÔI ĐÃ CHUYỂN KHOẢN")
        btn_confirm.setFixedHeight(50)
        btn_confirm.setStyleSheet("background-color: #10B981; font-weight: bold; font-size: 16px; border-radius: 8px;")
        btn_confirm.clicked.connect(self.confirm_payment)
        layout.addWidget(btn_confirm)

    def start_timer(self):
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_timer); self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        self.lbl_timer.setText(f"⏳ Thời gian giữ ghế: {mins:02d}:{secs:02d}")
        if self.time_left <= 0:
            self.timer.stop(); self.reject()

    def confirm_payment(self):
        self.timer.stop()
        if self.service.confirm_payment_for_held(self.booking_code):
            self.is_paid = True
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể xác nhận thanh toán!")

    def closeEvent(self, event):
        if not self.is_paid:
            self.service.repo.release_seat(self.data['seat_id']) 
        super().closeEvent(event)

# =======================================================
# MAIN VIEW: GUEST PORTAL
# =======================================================
class CustomerBookingView(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.service = BookingService()
        self.current_flight = None
        
        self.selected_seats_dict = {} 
        self.booking_state = {}        
        self.discount_amount = 0
        self.voucher_id = None
        
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; }
            QLineEdit, QComboBox, QDateEdit { padding: 10px; border-radius: 6px; background-color: #1E293B; border: 1px solid #475569; }
            QPushButton#SeatAVAILABLE { background-color: #10B981; border-radius: 6px; font-weight: bold; }
            QPushButton#SeatBUSINESS { background-color: #3B82F6; border-radius: 6px; font-weight: bold; }
            QPushButton#SeatBOOKED { background-color: #EF4444; border-radius: 6px; }
            QPushButton#SeatHELD { background-color: #F59E0B; border-radius: 6px; }
            QPushButton#SeatSELECTED { background-color: #8B5CF6; border-radius: 6px; border: 3px solid white; }
            QTableWidget { background-color: #1E293B; gridline-color: #334155; }
        """)
        self.main_layout = QHBoxLayout(self); self.main_layout.setContentsMargins(0,0,0,0)
        
        sidebar = QFrame(); sidebar.setFixedWidth(240); sidebar.setStyleSheet("background-color: #1E293B; border-right: 1px solid #334155;")
        s_lay = QVBoxLayout(sidebar)
        s_lay.addWidget(QLabel("✈ AIRLINE GUEST", styleSheet="font-size:20px; font-weight:bold; color:#38BDF8; margin: 20px 0;"))
        
        b1 = QPushButton("🔍 Tìm & Đặt vé"); b2 = QPushButton("🎫 Tra cứu vé")
        for b in [b1, b2]:
            b.setStyleSheet("text-align: left; padding: 15px; background: transparent; font-size: 16px;")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        
        b1.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        b2.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        s_lay.addWidget(b1); s_lay.addWidget(b2); s_lay.addStretch()
        self.main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.page_search = self.build_search_page()
        self.page_detail = self.build_booking_detail_page()
        self.page_lookup = self.build_lookup_page()
        
        self.stack.addWidget(self.page_search)
        self.stack.addWidget(self.page_detail)
        self.stack.addWidget(self.page_lookup)
        self.main_layout.addWidget(self.stack)

    # ------------------ BƯỚC 1: TÌM CHUYẾN ------------------
    def build_search_page(self):
        p = QWidget(); l = QVBoxLayout(p); l.setContentsMargins(40,40,40,40)
        
        sb = QFrame(); sb.setStyleSheet("background-color: #1E293B; border-radius: 12px;"); sb.setFixedHeight(100)
        sl = QHBoxLayout(sb); sl.setContentsMargins(20,20,20,20)
        
        self.cb_dep = QComboBox(); self.cb_arr = QComboBox()
        ports = self.service.get_airports_combo()
        self.cb_dep.addItems([""] + ports); self.cb_arr.addItems([""] + ports)
        self.dt = QDateEdit(QDate.currentDate()); self.dt.setCalendarPopup(True); self.dt.setDisplayFormat("yyyy-MM-dd")
        
        btn_search = QPushButton("🔍 TÌM CHUYẾN BAY")
        btn_search.setStyleSheet("background-color: #3B82F6; padding: 12px; border-radius: 8px; font-weight: bold;")
        btn_search.clicked.connect(self.action_search)

        sl.addWidget(self.cb_dep, 2); sl.addWidget(QLabel(" ➔ ")); sl.addWidget(self.cb_arr, 2); sl.addWidget(self.dt, 2); sl.addWidget(btn_search, 2)
        l.addWidget(sb)

        ql = QHBoxLayout(); ql.addWidget(QLabel("🔥 Tuyến phổ biến: "))
        for d,a in [("HAN", "SGN"), ("SGN", "HAN"), ("HAN", "DAD")]:
            btn = QPushButton(f"{d} ➔ {a}")
            btn.setStyleSheet("background: transparent; color: #38BDF8; border: 1px solid #38BDF8; border-radius: 15px; padding: 5px 15px;")
            btn.clicked.connect(lambda _, _d=d, _a=a: self.quick_search(_d, _a))
            ql.addWidget(btn)
        ql.addStretch(); l.addLayout(ql); l.addSpacing(20)

        self.scr = QScrollArea(); self.scr.setWidgetResizable(True); self.scr.setStyleSheet("border:none;")
        self.scr_w = QWidget(); self.scr_w.setStyleSheet("background:transparent;")
        self.flight_ly = QVBoxLayout(self.scr_w); self.flight_ly.setAlignment(Qt.AlignmentFlag.AlignTop); self.flight_ly.setSpacing(15)
        self.scr.setWidget(self.scr_w)
        l.addWidget(self.scr)
        
        self.action_search()
        return p

    def quick_search(self, d_code, a_code):
        for i in range(self.cb_dep.count()):
            if d_code in self.cb_dep.itemText(i): self.cb_dep.setCurrentIndex(i)
        for i in range(self.cb_arr.count()):
            if a_code in self.cb_arr.itemText(i): self.cb_arr.setCurrentIndex(i)
        self.action_search()

    def action_search(self):
        ok, msg, data = self.service.search_flights(self.cb_dep.currentText(), self.cb_arr.currentText(), self.dt.date().toString("yyyy-MM-dd"))
        while self.flight_ly.count():
            item = self.flight_ly.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not ok:
            self.flight_ly.addWidget(QLabel(msg, styleSheet="color:#EF4444; font-size:16px;"), alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            for f in data: self.flight_ly.addWidget(FlightCardWidget(f, self))

    # ------------------ BƯỚC 2: BOOKING NHÓM 1-N ------------------
    def go_to_booking_detail(self, flight):
        self.current_flight = flight
        self.selected_seats_dict.clear()
        self.booking_state.clear()  
        self.discount_amount = 0
        self.voucher_id = None
        
        self.lbl_title.setText(f"✈ {flight['flight_number']} | {flight['dep_city']} ➔ {flight['arr_city']}")
        self.render_seat_map(flight['flight_id'])
        self.rebuild_passenger_table()
        self.stack.setCurrentIndex(1)

    def render_seat_map(self, flight_id):
        while self.seat_grid.count():
            child = self.seat_grid.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        seats = self.service.fetch_seat_map(flight_id)
        row_map, curr_r = {}, 0
        for s in seats:
            match = re.match(r"([A-Za-z]+)(\d+)", s['seat_number'])
            if not match: continue
            letter, num = match.groups()
            
            if letter not in row_map:
                row_map[letter] = curr_r
                self.seat_grid.addWidget(QLabel(f"<b>{letter}</b>", styleSheet="color:#94A3B8; font-size:18px;"), curr_r, 0)
                curr_r += 1

            btn = QPushButton(s['seat_number']); btn.setFixedSize(45, 45)
            
            if s['seat_status'] == 'AVAILABLE': 
                btn.setObjectName("SeatBUSINESS" if s['class_name'] == 'BUSINESS' else "SeatAVAILABLE")
            else:
                btn.setObjectName(f"Seat{s['seat_status']}")
                btn.setEnabled(False)

            btn.setProperty("seat_data", s)
            btn.clicked.connect(lambda _, b=btn: self.on_seat_toggle(b))
            self.seat_grid.addWidget(btn, row_map[letter], int(num) if int(num) <= 2 else int(num)+1)

    def build_booking_detail_page(self):
        page = QWidget(); layout = QHBoxLayout(page); layout.setContentsMargins(20,20,20,20)
        
        # TRÁI: SEAT MAP
        left = QFrame(); left.setStyleSheet("background-color: #1E293B; border-radius: 12px;")
        l_lay = QVBoxLayout(left)
        self.lbl_title = QLabel("", styleSheet="font-size:20px; font-weight:bold; color:#38BDF8;")
        l_lay.addWidget(self.lbl_title)
        l_lay.addWidget(QLabel("🟩 Phổ thông | 🟦 Thương gia | 🟥 Đã bán | 🟧 Đang giữ"))
        
        scr_seat = QScrollArea(); scr_seat.setWidgetResizable(True); scr_seat.setStyleSheet("border:none;")
        w_seat = QWidget(); w_seat.setStyleSheet("background:transparent;")
        self.seat_grid = QGridLayout(w_seat); self.seat_grid.setSpacing(5)
        scr_seat.setWidget(w_seat)
        l_lay.addWidget(scr_seat); layout.addWidget(left, 4)

        # PHẢI: FORM CẢI TIẾN
        right = QFrame(); right.setStyleSheet("background-color: #1E293B; border-radius: 12px;")
        r_lay = QVBoxLayout(right)
        
        # --- KHU VỰC NGƯỜI ĐẠI DIỆN (Tự động Ẩn/Hiện) ---
        self.frame_contact = QFrame()
        fc_lay = QVBoxLayout(self.frame_contact)
        fc_lay.setContentsMargins(0, 0, 0, 0)
        fc_lay.addWidget(QLabel("👤 NGƯỜI ĐẠI DIỆN (Đặt theo Nhóm)", styleSheet="font-size:16px; font-weight:bold; color:#10B981;"))
        h1 = QHBoxLayout()
        self.in_cname = QLineEdit(); self.in_cname.setPlaceholderText("Họ và tên người đặt (*)")
        self.in_cphone = QLineEdit(); self.in_cphone.setPlaceholderText("Số điện thoại (*)")
        h1.addWidget(self.in_cname); h1.addWidget(self.in_cphone)
        fc_lay.addLayout(h1)
        self.in_cemail = QLineEdit(); self.in_cemail.setPlaceholderText("Email (Tùy chọn)")
        fc_lay.addWidget(self.in_cemail)
        r_lay.addWidget(self.frame_contact)
        self.frame_contact.setVisible(False) # Ẩn mặc định khi chưa chọn ghế

        # --- BẢNG DANH SÁCH HÀNH KHÁCH ---
        self.lbl_pax_title = QLabel("📝 THÔNG TIN HÀNH KHÁCH", styleSheet="font-size:16px; font-weight:bold; color:#F59E0B; margin-top:10px;")
        r_lay.addWidget(self.lbl_pax_title)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ghế", "Họ Tên (*)", "CCCD (*)", "SĐT (* Mặc định làm Đại diện)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        r_lay.addWidget(self.table)

        # Voucher & Thanh toán
        v_lay = QHBoxLayout()
        self.in_v = QLineEdit(); self.in_v.setPlaceholderText("Mã Voucher")
        btn_v = QPushButton("Áp dụng"); btn_v.setStyleSheet("background-color: #38BDF8; font-weight:bold; padding:8px;")
        btn_v.clicked.connect(self.action_apply_voucher)
        v_lay.addWidget(self.in_v); v_lay.addWidget(btn_v)
        
        self.cb_pay = QComboBox()
        self.cb_pay.addItems(["VNPAY", "MOMO", "BANK_TRANSFER", "CASH"])
        v_lay.addWidget(QLabel("TT qua:")); v_lay.addWidget(self.cb_pay)
        r_lay.addLayout(v_lay)

        # Bill
        bill = QFrame(); bill.setStyleSheet("background-color: #0F172A; border-radius: 8px; padding: 10px;")
        b_lay = QVBoxLayout(bill)
        self.lbl_t_seat = QLabel("Số lượng vé: 0")
        self.lbl_t_price = QLabel("Tạm tính: 0 đ")
        self.lbl_t_disc = QLabel("Giảm giá: 0 đ", styleSheet="color:#F59E0B;")
        self.lbl_t_final = QLabel("TỔNG TIỀN: 0 đ", styleSheet="font-size:22px; font-weight:bold; color:#10B981;")
        for x in [self.lbl_t_seat, self.lbl_t_price, self.lbl_t_disc, self.lbl_t_final]: b_lay.addWidget(x)
        r_lay.addWidget(bill)

        # Nút
        act = QHBoxLayout()
        btn_back = QPushButton("⬅ Trở lại"); btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_hold = QPushButton("⏳ GIỮ CHỖ"); btn_hold.setStyleSheet("background-color:#F59E0B; font-weight:bold; padding:12px;")
        btn_hold.clicked.connect(lambda: self.action_submit(is_hold=True))
        btn_pay = QPushButton("💳 THANH TOÁN QR"); btn_pay.setStyleSheet("background-color:#10B981; font-weight:bold; padding:12px;")
        btn_pay.clicked.connect(lambda: self.action_submit(is_hold=False))
        
        act.addWidget(btn_back); act.addWidget(btn_hold); act.addWidget(btn_pay)
        r_lay.addLayout(act)
        
        layout.addWidget(right, 6)
        return page

    def on_seat_toggle(self, btn):
        data = btn.property("seat_data")
        sid = data['seat_id']
        
        if sid in self.selected_seats_dict:
            del self.selected_seats_dict[sid]
            btn.setObjectName("SeatBUSINESS" if data['class_name'] == 'BUSINESS' else "SeatAVAILABLE")
        else:
            data['calc_price'] = self.current_flight['base_price'] * float(data['price_multiplier'])
            self.selected_seats_dict[sid] = data
            btn.setObjectName("SeatSELECTED")

        btn.style().unpolish(btn); btn.style().polish(btn)
        self.rebuild_passenger_table()

    def rebuild_passenger_table(self):
        seats = list(self.selected_seats_dict.values())
        num_seats = len(seats)
        
        # LOGIC UX THÔNG MINH: Ẩn hiện tùy số ghế
        if num_seats > 1:
            self.frame_contact.setVisible(True)
            self.lbl_pax_title.setText("📝 DANH SÁCH HÀNH KHÁCH")
        else:
            self.frame_contact.setVisible(False)
            self.lbl_pax_title.setText("📝 THÔNG TIN HÀNH KHÁCH")

        self.table.setRowCount(num_seats)
        
        raw_total = 0
        for row, s in enumerate(seats):
            raw_total += s['calc_price']
            
            it = QTableWidgetItem(f"{s['seat_number']} ({s['class_name']})")
            it.setFlags(it.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, it)
            
            self.table.setCellWidget(row, 1, QLineEdit())
            self.table.setCellWidget(row, 2, QLineEdit())
            self.table.setCellWidget(row, 3, QLineEdit())

        self.booking_state['raw_total'] = raw_total
        self.lbl_t_seat.setText(f"Số lượng vé: {num_seats}")
        self.lbl_t_price.setText(f"Tạm tính: {raw_total:,.0f} đ")
        self.recalc_total()

    def action_apply_voucher(self):
        if not self.selected_seats_dict: return QMessageBox.warning(self, "Lỗi", "Hãy chọn ít nhất 1 ghế!")
        code = self.in_v.text().strip()
        ok, msg, disc, vid = self.service.apply_voucher(code, self.booking_state.get('raw_total', 0))
        if ok:
            self.discount_amount = disc
            self.voucher_id = vid
            QMessageBox.information(self, "Thành công", msg)
        else:
            self.discount_amount = 0
            self.voucher_id = None
            QMessageBox.warning(self, "Lỗi Voucher", msg)
        self.recalc_total()

    def recalc_total(self):
        raw = self.booking_state.get('raw_total', 0)
        final = max(0, raw - self.discount_amount)
        self.booking_state['final_amount'] = final
        self.lbl_t_disc.setText(f"Giảm giá: -{self.discount_amount:,.0f} đ")
        self.lbl_t_final.setText(f"TỔNG TIỀN: {final:,.0f} đ")

    def action_submit(self, is_hold: bool):
        seats = list(self.selected_seats_dict.values())
        if len(seats) == 0: return QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ghế trên sơ đồ!")

        pax_list = []
        for row, s in enumerate(seats):
            w_name = self.table.cellWidget(row, 1)
            w_cccd = self.table.cellWidget(row, 2)
            w_phone = self.table.cellWidget(row, 3)
            
            pax_list.append({
                'seat_id': s['seat_id'], 
                'seat_number': s['seat_number'], 
                'base_price': self.current_flight['base_price'], 
                'final_price': s['calc_price'],
                'name': w_name.text().strip() if w_name else "",
                'id_card': w_cccd.text().strip() if w_cccd else "",
                'phone': w_phone.text().strip() if w_phone else ""
            })

        # LOGIC UX THÔNG MINH: Tự bóc tách dữ liệu người đại diện
        if len(seats) == 1:
            contact_name = pax_list[0]['name']
            contact_phone = pax_list[0]['phone']
            contact_email = "" # Đặt cá nhân không bắt ép email
        else:
            contact_name = self.in_cname.text().strip()
            contact_phone = self.in_cphone.text().strip()
            contact_email = self.in_cemail.text().strip()

        grp = {
            'flight_id': self.current_flight['flight_id'],
            'contact_name': contact_name,
            'contact_phone': contact_phone,
            'contact_email': contact_email,
            'total_amount': self.booking_state.get('final_amount', 0),
            'payment_method': 'PAY_LATER' if is_hold else self.cb_pay.currentText(),
            'voucher_id': self.voucher_id
        }

        ok, msg, bk_code = self.service.validate_and_book_group(grp, pax_list, is_hold)
        if not ok: return QMessageBox.warning(self, "Lỗi Nhập Liệu", msg)

        if is_hold or self.cb_pay.currentText() == "CASH":
            QMessageBox.information(self, "THÀNH CÔNG", f"Thao tác hoàn tất!\nMã Booking: {bk_code}\nVui lòng thanh toán hoặc ra quầy trong 15 phút.")
            self.stack.setCurrentIndex(0); self.action_search()
        else:
            dialog = QRPaymentDialog(bk_code, grp['total_amount'], self.service, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "XUẤT VÉ", f"Thanh toán thành công!\nMã Booking: {bk_code}")
            else:
                QMessageBox.warning(self, "Hủy QR", f"Chưa thanh toán.\nVé đã chuyển sang trạng thái GIỮ CHỖ 15 Phút.\nMã Booking: {bk_code}")
            self.stack.setCurrentIndex(0); self.action_search()

    # ---------------------------------------------------------
    # MÀN HÌNH 3: TICKET LOOKUP & REPORT
    # ---------------------------------------------------------
    def build_lookup_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(40,40,40,40)
        
        search_box = QHBoxLayout()
        self.in_lookup = QLineEdit(); self.in_lookup.setPlaceholderText("Nhập Mã PNR (TKT-...), SĐT hoặc CCCD...")
        btn_look = QPushButton("🔍 Tra Cứu Vé")
        btn_look.setStyleSheet("background-color: #F59E0B; padding: 12px; font-weight:bold;")
        btn_look.clicked.connect(self.action_lookup)
        search_box.addWidget(self.in_lookup); search_box.addWidget(btn_look)
        layout.addLayout(search_box)
        
        self.stats_frame = QFrame(); self.stats_frame.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        s_layout = QHBoxLayout(self.stats_frame)
        self.lbl_stat_total = QLabel("🎫 Tổng vé: 0")
        self.lbl_stat_spent = QLabel("💰 Tổng chi: 0đ")
        self.lbl_stat_cancel = QLabel("❌ Đã hủy: 0")
        for l in [self.lbl_stat_total, self.lbl_stat_spent, self.lbl_stat_cancel]:
            l.setStyleSheet("font-size: 16px; font-weight: bold;"); s_layout.addWidget(l)
        layout.addWidget(self.stats_frame)
        self.stats_frame.setVisible(False)

        self.scroll_tkt = QScrollArea(); self.scroll_tkt.setWidgetResizable(True); self.scroll_tkt.setStyleSheet("border:none; background:transparent;")
        self.tkt_content = QWidget(); self.tkt_content.setStyleSheet("background:transparent;")
        self.tkt_layout = QVBoxLayout(self.tkt_content); self.tkt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_tkt.setWidget(self.tkt_content)
        layout.addWidget(self.scroll_tkt)
        return page

    def action_lookup(self):
        ok, msg, tkts, stats = self.service.lookup_tickets(self.in_lookup.text().strip())
        while self.tkt_layout.count():
            i = self.tkt_layout.takeAt(0)
            if i.widget(): i.widget().deleteLater()
            
        if not ok:
            self.stats_frame.setVisible(False)
            self.tkt_layout.addWidget(QLabel(msg, styleSheet="color:#EF4444; font-size:16px;"), alignment=Qt.AlignmentFlag.AlignCenter)
            return

        self.stats_frame.setVisible(True)
        self.lbl_stat_total.setText(f"🎫 Tổng vé: {stats['total']}")
        self.lbl_stat_spent.setText(f"💰 Tổng chi: {stats['spent']:,.0f} đ")
        self.lbl_stat_cancel.setText(f"❌ Đã hủy: {stats['cancelled']}")

        for t in tkts: self.tkt_layout.addWidget(TicketCardWidget(t, self))

    def cancel_my_ticket(self, ticket_id):
        if QMessageBox.question(self, "Cảnh báo", "Bạn chắc chắn muốn hủy vé? Tiền sẽ được hoàn lại sau 24h.") == QMessageBox.StandardButton.Yes:
            ok, msg = self.service.cancel_ticket(ticket_id, role="ADMIN") 
            QMessageBox.information(self, "Thông báo", msg)
            self.action_lookup()