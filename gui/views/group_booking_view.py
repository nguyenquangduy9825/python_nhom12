# gui/views/group_booking_view.py
import re
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
                             QGridLayout, QLineEdit, QStackedWidget, QMessageBox, QComboBox, 
                             QScrollArea, QDateEdit, QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from bll.booking_service import BookingService

# ==========================================
# 1. DIALOG THANH TOÁN QR THẬT CÓ COUNTDOWN
# ==========================================
class QRPaymentDialog(QDialog):
    def __init__(self, booking_code, total_amount, service, parent=None):
        super().__init__(parent)
        self.booking_code = booking_code
        self.total_amount = total_amount
        self.service = service
        self.time_left = 900 # 15 Phút
        self.is_paid = False
        self.setup_ui()
        self.start_timer()

    def setup_ui(self):
        self.setWindowTitle("Thanh Toán Bằng Mã QR")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #0F172A; color: white; border-radius: 12px;")
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("💳 QUÉT MÃ QR ĐỂ THANH TOÁN", styleSheet="font-size:20px; font-weight:bold; color:#10B981;"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.lbl_timer = QLabel("⏳ Giữ ghế còn: 15:00")
        self.lbl_timer.setStyleSheet("font-size: 18px; color: #F59E0B; font-weight: bold;")
        layout.addWidget(self.lbl_timer, alignment=Qt.AlignmentFlag.AlignCenter)

        # Load QR thật
        qr_lbl = QLabel()
        if os.path.exists("my_qr.png"):
            pix = QPixmap("my_qr.png").scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            qr_lbl.setPixmap(pix)
        else:
            qr_lbl.setText("[ LỖI: Không tìm thấy file my_qr.png ]")
        qr_lbl.setStyleSheet("background-color: white; padding: 10px; border-radius: 10px;")
        layout.addWidget(qr_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        info = QFrame(); info.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 15px;")
        i_lay = QVBoxLayout(info)
        i_lay.addWidget(QLabel(f"Mã Booking: {self.booking_code}", styleSheet="font-weight:bold; font-size:16px;"))
        i_lay.addWidget(QLabel(f"TỔNG TIỀN: {self.total_amount:,.0f} VNĐ", styleSheet="font-size:20px; color:#10B981; font-weight:bold;"))
        layout.addWidget(info)

        btn_paid = QPushButton("✅ TÔI ĐÃ CHUYỂN KHOẢN")
        btn_paid.setFixedHeight(50)
        btn_paid.setStyleSheet("background-color: #3B82F6; font-size: 16px; font-weight: bold; border-radius: 8px;")
        btn_paid.clicked.connect(self.process_payment)
        layout.addWidget(btn_paid)

    def start_timer(self):
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_timer); self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        self.lbl_timer.setText(f"⏳ Giữ ghế còn: {mins:02d}:{secs:02d}")
        if self.time_left <= 0:
            self.timer.stop(); self.reject()

    def process_payment(self):
        self.timer.stop()
        if self.service.confirm_payment_for_held(self.booking_code):
            self.is_paid = True
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể xác nhận thanh toán trên hệ thống!")


# ==========================================
# 2. FLIGHT CARD WIDGET
# ==========================================
class FlightCardWidget(QFrame):
    def __init__(self, flight, parent_view):
        super().__init__()
        self.flight = flight; self.parent_view = parent_view
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
            btn.clicked.connect(lambda: self.parent_view.go_to_booking(self.flight))
        act.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(act, stretch=2)


# ==========================================
# 3. MAIN VIEW (Khách hàng)
# ==========================================
class GroupBookingView(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.service = BookingService()
        self.current_flight = None
        self.selected_seats_dict = {} # Lưu ghế đang chọn {seat_id: seat_data}
        self.discount_amount = 0
        self.voucher_id = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; }
            QLineEdit, QComboBox, QDateEdit { padding: 12px; border-radius: 6px; background-color: #1E293B; border: 1px solid #475569; }
            QPushButton#SeatAVAILABLE { background-color: #10B981; border-radius: 6px; font-weight: bold; }
            QPushButton#SeatBUSINESS { background-color: #3B82F6; border-radius: 6px; font-weight: bold; }
            QPushButton#SeatBOOKED { background-color: #EF4444; border-radius: 6px; }
            QPushButton#SeatHELD { background-color: #F59E0B; border-radius: 6px; }
            QPushButton#SeatSELECTED { background-color: #8B5CF6; border-radius: 6px; border: 3px solid white; }
            QTableWidget { background-color: #1E293B; gridline-color: #334155; }
        """)
        self.main_layout = QHBoxLayout(self); self.main_layout.setContentsMargins(0,0,0,0)
        
        # Sidebar mini
        sidebar = QFrame(); sidebar.setFixedWidth(240); sidebar.setStyleSheet("background-color: #1E293B; border-right: 1px solid #334155;")
        s_lay = QVBoxLayout(sidebar)
        s_lay.addWidget(QLabel("✈ AIRLINE GUEST", styleSheet="font-size:20px; font-weight:bold; color:#38BDF8; margin: 20px 0;"))
        b1 = QPushButton("🔍 Tìm & Đặt vé Nhóm"); b1.setStyleSheet("text-align: left; padding: 15px; background: transparent; font-size: 16px;")
        b1.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        s_lay.addWidget(b1); s_lay.addStretch()
        self.main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.page_search = self.build_search_page()
        self.page_detail = self.build_detail_page()
        self.stack.addWidget(self.page_search); self.stack.addWidget(self.page_detail)
        self.main_layout.addWidget(self.stack)

    # -------- PAGE 1: TÌM CHUYẾN --------
    def build_search_page(self):
        p = QWidget(); l = QVBoxLayout(p); l.setContentsMargins(40,40,40,40)
        
        sb = QFrame(); sb.setStyleSheet("background-color: #1E293B; border-radius: 12px;"); sb.setFixedHeight(100)
        sl = QHBoxLayout(sb); sl.setContentsMargins(20,20,20,20)
        self.cb_dep = QComboBox(); self.cb_arr = QComboBox()
        ports = self.service.get_airports_combo()
        self.cb_dep.addItems(ports); self.cb_arr.addItems(ports)
        self.dt = QDateEdit(QDate.currentDate()); self.dt.setCalendarPopup(True); self.dt.setDisplayFormat("yyyy-MM-dd")
        
        btn_search = QPushButton("🔍 TÌM CHUYẾN BAY"); btn_search.setStyleSheet("background-color: #3B82F6; padding: 12px; border-radius: 8px; font-weight: bold;")
        btn_search.clicked.connect(self.action_search)
        sl.addWidget(self.cb_dep, 2); sl.addWidget(QLabel(" ➔ ")); sl.addWidget(self.cb_arr, 2); sl.addWidget(self.dt, 2); sl.addWidget(btn_search, 2)
        l.addWidget(sb); l.addSpacing(20)

        self.scr = QScrollArea(); self.scr.setWidgetResizable(True); self.scr.setStyleSheet("border:none;")
        self.scr_w = QWidget(); self.scr_w.setStyleSheet("background:transparent;")
        self.flight_ly = QVBoxLayout(self.scr_w); self.flight_ly.setAlignment(Qt.AlignmentFlag.AlignTop); self.flight_ly.setSpacing(15)
        self.scr.setWidget(self.scr_w)
        l.addWidget(self.scr)
        return p

    def action_search(self):
        ok, msg, data = self.service.search_flights(self.cb_dep.currentText(), self.cb_arr.currentText(), self.dt.date().toString("yyyy-MM-dd"))
        while self.flight_ly.count():
            item = self.flight_ly.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not ok:
            self.flight_ly.addWidget(QLabel(msg, styleSheet="color:#EF4444; font-size:16px;"), alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            for f in data: self.flight_ly.addWidget(FlightCardWidget(f, self))

    # -------- PAGE 2: BOOKING NHÓM 1-N --------
    def go_to_booking(self, flight):
        self.current_flight = flight
        self.selected_seats_dict.clear()
        self.discount_amount = 0; self.voucher_id = None
        self.lbl_title.setText(f"✈ {flight['flight_number']} | {flight['dep_city']} ➔ {flight['arr_city']}")
        self.render_seat_map(flight['flight_id'])
        self.rebuild_passenger_table()
        self.stack.setCurrentIndex(1)

    def build_detail_page(self):
        p = QWidget(); l = QHBoxLayout(p); l.setContentsMargins(20,20,20,20)
        
        # TRÁI: SEAT MAP
        left = QFrame(); left.setStyleSheet("background-color: #1E293B; border-radius: 12px;")
        l_lay = QVBoxLayout(left)
        self.lbl_title = QLabel("", styleSheet="font-size:18px; font-weight:bold; color:#38BDF8;")
        l_lay.addWidget(self.lbl_title)
        l_lay.addWidget(QLabel("🟩 Phổ thông | 🟦 Thương gia | 🟥 Đã bán | 🟧 Đang giữ"))
        
        scr_s = QScrollArea(); scr_s.setWidgetResizable(True); scr_s.setStyleSheet("border:none;")
        w_s = QWidget(); w_s.setStyleSheet("background:transparent;")
        self.seat_grid = QGridLayout(w_s); self.seat_grid.setSpacing(8)
        scr_s.setWidget(w_s); l_lay.addWidget(scr_s)
        l.addWidget(left, 4)

        # PHẢI: FORM NHÓM + THANH TOÁN
        right = QFrame(); right.setStyleSheet("background-color: #1E293B; border-radius: 12px;")
        r_lay = QVBoxLayout(right)
        r_lay.addWidget(QLabel("👤 NGƯỜI ĐẠI DIỆN", styleSheet="font-weight:bold; color:#10B981;"))
        
        h1 = QHBoxLayout(); self.in_cname = QLineEdit(); self.in_cname.setPlaceholderText("Họ và tên (*)")
        self.in_cphone = QLineEdit(); self.in_cphone.setPlaceholderText("SĐT (*)")
        h1.addWidget(self.in_cname); h1.addWidget(self.in_cphone); r_lay.addLayout(h1)
        self.in_cemail = QLineEdit(); self.in_cemail.setPlaceholderText("Email (Tùy chọn)"); r_lay.addWidget(self.in_cemail)

        r_lay.addWidget(QLabel("📝 DANH SÁCH HÀNH KHÁCH", styleSheet="font-weight:bold; color:#F59E0B; margin-top:10px;"))
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ghế", "Họ Tên (*)", "CCCD (*)", "SĐT"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        r_lay.addWidget(self.table)

        # Thanh toán & Voucher
        v_lay = QHBoxLayout()
        self.in_v = QLineEdit(); self.in_v.setPlaceholderText("Mã Voucher")
        btn_v = QPushButton("Áp dụng"); btn_v.setStyleSheet("background-color: #38BDF8; font-weight:bold; padding:8px;")
        btn_v.clicked.connect(self.action_voucher)
        v_lay.addWidget(self.in_v); v_lay.addWidget(btn_v)
        
        self.cb_pay = QComboBox(); self.cb_pay.addItems(["VNPAY_QR", "MOMO_QR", "BANK_TRANSFER", "CASH"])
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
        btn_hold.clicked.connect(lambda: self.action_submit(True))
        btn_pay = QPushButton("💳 THANH TOÁN QR"); btn_pay.setStyleSheet("background-color:#10B981; font-weight:bold; padding:12px;")
        btn_pay.clicked.connect(lambda: self.action_submit(False))
        
        act.addWidget(btn_back); act.addWidget(btn_hold); act.addWidget(btn_pay)
        r_lay.addLayout(act); l.addWidget(right, 6)
        return p

    def render_seat_map(self, flight_id):
        seats = self.service.fetch_seat_map(flight_id)
        row_map, curr_r = {}, 0
        for s in seats:
            match = re.match(r"([A-Za-z]+)(\d+)", s['seat_number'])
            if not match: continue
            letter, num = match.groups()
            
            if letter not in row_map:
                row_map[letter] = curr_r
                self.seat_grid.addWidget(QLabel(f"<b>{letter}</b>"), curr_r, 0)
                curr_r += 1

            btn = QPushButton(s['seat_number']); btn.setFixedSize(50, 50)
            if s['seat_status'] == 'AVAILABLE': 
                btn.setObjectName("SeatBUSINESS" if s['class_name'] == 'BUSINESS' else "SeatAVAILABLE")
            else:
                btn.setObjectName(f"Seat{s['seat_status']}")
                btn.setEnabled(False)

            btn.setProperty("seat_data", s)
            btn.clicked.connect(lambda _, b=btn: self.on_seat_toggle(b))
            self.seat_grid.addWidget(btn, row_map[letter], int(num))

    def on_seat_toggle(self, btn):
        data = btn.property("seat_data")
        sid = data['seat_id']
        
        if sid in self.selected_seats_dict: # Đang chọn -> Bỏ chọn
            del self.selected_seats_dict[sid]
            btn.setObjectName("SeatBUSINESS" if data['class_name'] == 'BUSINESS' else "SeatAVAILABLE")
        else: # Chưa chọn -> Chọn
            data['calc_price'] = self.current_flight['base_price'] * float(data['price_multiplier'])
            self.selected_seats_dict[sid] = data
            btn.setObjectName("SeatSELECTED")

        btn.style().unpolish(btn); btn.style().polish(btn)
        self.rebuild_passenger_table()

    def rebuild_passenger_table(self):
        seats = list(self.selected_seats_dict.values())
        self.table.setRowCount(len(seats))
        raw_total = 0
        
        for row, s in enumerate(seats):
            raw_total += s['calc_price']
            
            # Cột ghế Readonly
            it = QTableWidgetItem(f"{s['seat_number']} ({s['class_name']})")
            it.setFlags(it.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, it)
            
            # Form động
            self.table.setCellWidget(row, 1, QLineEdit())
            self.table.setCellWidget(row, 2, QLineEdit())
            self.table.setCellWidget(row, 3, QLineEdit())

        # Update Bill
        self.lbl_t_seat.setText(f"Số lượng vé: {len(seats)}")
        self.lbl_t_price.setText(f"Tạm tính: {raw_total:,.0f} đ")
        self.booking_state['raw_total'] = raw_total
        self.recalc_bill()

    def action_voucher(self):
        if not self.selected_seats_dict: return QMessageBox.warning(self, "Lỗi", "Chọn ít nhất 1 ghế trước!")
        ok, msg, disc, vid = self.service.apply_voucher(self.in_v.text().strip(), self.booking_state['raw_total'])
        if ok:
            self.discount_amount = disc; self.voucher_id = vid
            QMessageBox.information(self, "Thành công", msg)
        else:
            self.discount_amount = 0; self.voucher_id = None
            QMessageBox.warning(self, "Lỗi", msg)
        self.recalc_bill()

    def recalc_bill(self):
        raw = self.booking_state.get('raw_total', 0)
        final = max(0, raw - self.discount_amount)
        self.booking_state['final_amount'] = final
        self.lbl_t_disc.setText(f"Giảm giá: -{self.discount_amount:,.0f} đ")
        self.lbl_t_final.setText(f"TỔNG TIỀN: {final:,.0f} đ")

    def action_submit(self, is_hold):
        # 1. Thu thập Info Nhóm
        grp = {
            'flight_id': self.current_flight['flight_id'],
            'contact_name': self.in_cname.text().strip(),
            'contact_phone': self.in_cphone.text().strip(),
            'contact_email': self.in_cemail.text().strip(),
            'total_amount': self.booking_state.get('final_amount', 0),
            'payment_method': 'PAY_LATER' if is_hold else self.cb_pay.currentText(),
            'voucher_id': self.voucher_id
        }

        # 2. Thu thập N Hành Khách
        pax_list = []
        seats = list(self.selected_seats_dict.values())
        for row, s in enumerate(seats):
            w_name = self.table.cellWidget(row, 1); w_cccd = self.table.cellWidget(row, 2); w_phone = self.table.cellWidget(row, 3)
            pax_list.append({
                'seat_id': s['seat_id'], 'seat_number': s['seat_number'], 
                'base_price': self.current_flight['base_price'], 'final_price': s['calc_price'],
                'name': w_name.text().strip() if w_name else "",
                'id_card': w_cccd.text().strip() if w_cccd else "",
                'phone': w_phone.text().strip() if w_phone else ""
            })

        ok, msg, bk_code = self.service.validate_and_book_group(grp, pax_list, is_hold)
        if not ok: return QMessageBox.warning(self, "Lỗi", msg)

        if is_hold or self.cb_pay.currentText() == "CASH":
            QMessageBox.information(self, "THÀNH CÔNG", f"Đặt vé thành công!\nMã Booking của bạn: {bk_code}\nVui lòng thanh toán hoặc ra quầy.")
            self.stack.setCurrentIndex(0); self.action_search()
        else:
            # Hiện QR Dialog
            dialog = QRPaymentDialog(bk_code, grp['total_amount'], self.service, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "XUẤT VÉ", f"Thanh toán thành công!\nMã Booking: {bk_code}")
            else:
                QMessageBox.warning(self, "Hủy QR", f"Chưa thanh toán.\nVé đã chuyển sang trạng thái GIỮ CHỖ 15 Phút.\nMã Booking: {bk_code}")
            self.stack.setCurrentIndex(0); self.action_search()