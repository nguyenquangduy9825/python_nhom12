# gui/views/customer_booking_view.py
import re
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QLineEdit, 
                             QStackedWidget, QMessageBox, QScrollArea, QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QFont, QPixmap
from bll.customer_service import CustomerService

# =======================================================
# POPUP QUÉT MÃ QR THANH TOÁN (Tích hợp sẵn)
# =======================================================
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
        qr_path = os.path.join("assets", "my_qr.png")
        if os.path.exists(qr_path):
            self.lbl_qr.setPixmap(QPixmap(qr_path).scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.lbl_qr.setText("[ Đặt file my_qr.png vào folder assets ]")
            self.lbl_qr.setFixedSize(240, 240)
            self.lbl_qr.setStyleSheet("border: 2px dashed #475569; color: #64748B;")
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

class ModernFlightCard(QFrame):
    def __init__(self, flight, parent_view):
        super().__init__()
        self.flight = flight
        self.parent_view = parent_view
        
        self.setStyleSheet("""
            QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; padding: 0px; }
            QFrame:hover { border: 2px solid #38BDF8; background-color: #26354A; }
            QLabel { color: #F8FAFC; border: none; background: transparent; }
        """)
        self.setFixedHeight(140)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(20)
        
        time_dep = QVBoxLayout()
        lbl_time = QLabel(flight['departure_time'].strftime("%H:%M"))
        lbl_time.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl_time.setStyleSheet("color: #38BDF8;")
        time_dep.addWidget(lbl_time)
        time_dep.addWidget(QLabel(flight['dep_city'], font=QFont("Arial", 11)))
        layout.addLayout(time_dep)
        
        mid = QVBoxLayout()
        mid.addWidget(QLabel(f"✈ {flight['flight_number']}", styleSheet="font-weight: bold;"), alignment=Qt.AlignmentFlag.AlignCenter)
        mid.addWidget(QLabel(f"─── {flight.get('duration_str', '')} ───", styleSheet="color: #475569;"), alignment=Qt.AlignmentFlag.AlignCenter)
        mid.addWidget(QLabel(f"Ghế còn: {flight['available_seats']}/{flight['total_seats']}", styleSheet="color: #94A3B8; font-size: 12px;"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(mid, stretch=1)
        
        time_arr = QVBoxLayout()
        lbl_arr = QLabel(flight['arrival_time'].strftime("%H:%M"))
        lbl_arr.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        lbl_arr.setStyleSheet("color: #38BDF8;")
        time_arr.addWidget(lbl_arr)
        time_arr.addWidget(QLabel(flight['arr_city'], font=QFont("Arial", 11)))
        layout.addLayout(time_arr)
        
        action = QVBoxLayout()
        price_lbl = QLabel(f"Từ {float(flight['base_price']):,.0f} ₫")
        price_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        price_lbl.setStyleSheet("color: #10B981;")
        action.addWidget(price_lbl)
        
        badge = QLabel(flight.get('badge', ''))
        badge_color = flight.get('badge_color', '#38BDF8')
        badge.setStyleSheet(f"background-color: {badge_color}20; color: {badge_color}; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        action.addWidget(badge)
        
        btn = QPushButton("CHỌN GHẾ →")
        btn.setFixedHeight(36)
        
        if flight['available_seats'] == 0:
            btn.setEnabled(False)
            btn.setStyleSheet("background-color: #475569; color: #94A3B8; border-radius: 6px; font-weight: bold;")
        else:
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("background-color: #38BDF8; color: #0F172A; border-radius: 6px; font-weight: bold;")
            btn.clicked.connect(lambda: parent_view.open_seat_map(self.flight))
        
        action.addWidget(btn)
        layout.addLayout(action)

class TicketResultCard(QFrame):
    def __init__(self, tkt, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.tkt = tkt
        
        self.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }")
        self.setMinimumHeight(200)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        info = QVBoxLayout()
        pnr_lbl = QLabel(f"🎫 PNR: {tkt.get('ticket_code', 'N/A')}")
        pnr_lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        pnr_lbl.setStyleSheet("color: #38BDF8;")
        info.addWidget(pnr_lbl)
        info.addWidget(QLabel(f"👤 {tkt.get('full_name', 'N/A')} | 📱 {tkt.get('phone', 'N/A')}", styleSheet="color: white;"))
        info.addWidget(QLabel(f"✈ {tkt.get('flight_number', 'N/A')} ({tkt.get('dep_city', '?')} → {tkt.get('arr_city', '?')})", styleSheet="color: white;"))
        info.addWidget(QLabel(f"💺 {tkt.get('seat_number', 'N/A')} ({tkt.get('class_name', 'N/A')})", styleSheet="color: white;"))
        info.addWidget(QLabel(f"📅 Khởi hành: {tkt.get('departure_time', 'N/A')}", styleSheet="color: white;"))
        layout.addLayout(info, stretch=2)
        
        actions = QVBoxLayout()
        status = tkt.get('ticket_status', 'UNKNOWN')
        status_colors = {'BOOKED': '#10B981', 'HELD': '#F59E0B', 'CANCELLED': '#EF4444'}
        
        status_lbl = QLabel(f"📊 {status}")
        status_lbl.setStyleSheet(f"color: {status_colors.get(status, '#94A3B8')}; font-weight: bold; font-size: 14px;")
        actions.addWidget(status_lbl)
        
        price_lbl = QLabel(f"💰 {float(tkt.get('final_price', 0)):,.0f} ₫")
        price_lbl.setStyleSheet("color: #10B981; font-weight: bold; font-size: 14px;")
        actions.addWidget(price_lbl)
        
        if status == 'HELD':
            btn_pay = QPushButton("💳 Thanh Toán")
            btn_pay.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_pay.setStyleSheet("background-color: #10B981; color: #0F172A; padding: 10px; border-radius: 6px; font-weight: bold;")
            btn_pay.clicked.connect(self.process_payment)
            actions.addWidget(btn_pay)
        
        if status in ['BOOKED', 'HELD']:
            btn_cancel = QPushButton("❌ Hủy Vé")
            btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_cancel.setStyleSheet("background-color: transparent; border: 2px solid #EF4444; color: #EF4444; padding: 8px; border-radius: 6px; font-weight: bold;")
            btn_cancel.clicked.connect(self.cancel_ticket)
            actions.addWidget(btn_cancel)
        
        actions.addStretch()
        layout.addLayout(actions, stretch=1)
    
    def process_payment(self):
        msgBox = QMessageBox(self.parent_view)
        msgBox.setWindowTitle("Chọn phương thức thanh toán")
        msgBox.setText(f"Thanh toán vé: {self.tkt.get('ticket_code')}\nSố tiền: {float(self.tkt.get('final_price', 0)):,.0f} VNĐ")
        
        btn_cash = msgBox.addButton("💵 Tiền mặt", QMessageBox.ButtonRole.ActionRole)
        btn_qr = msgBox.addButton("📲 Quét mã QR", QMessageBox.ButtonRole.ActionRole)
        msgBox.addButton("Hủy bỏ", QMessageBox.ButtonRole.RejectRole)
        msgBox.exec()
        
        method = 'CASH' if msgBox.clickedButton() == btn_cash else 'VNPAY' if msgBox.clickedButton() == btn_qr else None
        if not method: return
            
        if method == 'VNPAY':
            popup = AdminQRPaymentPopup(float(self.tkt['final_price']), f"THANH TOAN {self.tkt['ticket_code']}", self.parent_view)
            if popup.exec() != QDialog.DialogCode.Accepted:
                return QMessageBox.information(self.parent_view, "Đã hủy", "Giao dịch QR bị hủy.")
                
        service = CustomerService()
        ok, msg = service.process_payment(self.tkt['ticket_id'], method)
        if ok:
            QMessageBox.information(self.parent_view, "Thành công", msg)
            self.parent_view.action_lookup()
        else:
            QMessageBox.critical(self.parent_view, "Lỗi", msg)
    
    def cancel_ticket(self):
        reply = QMessageBox.question(self.parent_view, "❓ Xác Nhận Hủy Vé", "Bạn chắc chắn muốn hủy vé này?\nGhế sẽ được hoàn trả.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            service = CustomerService()
            ok, msg = service.cancel_my_ticket(self.tkt['ticket_code'], self.tkt['phone'])
            QMessageBox.information(self.parent_view, "Kết Quả", msg)
            if ok: self.parent_view.action_lookup()

class CustomerBookingView(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.service = CustomerService()
        self.current_flight = None
        self.selected_seat = None
        self.setup_ui()
        self.load_flight_list()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
            QLineEdit { padding: 12px; border-radius: 8px; background-color: #1E293B; border: 1px solid #334155; font-size: 14px; color: white; }
            QLineEdit:focus { border: 2px solid #38BDF8; }
            QScrollArea { border: none; background: transparent; }
            QTableWidget { background-color: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; outline: none; }
            QHeaderView::section { background-color: #0F172A; color: #94A3B8; padding: 10px; font-weight: bold; border: none; text-align: left; }
        """)
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("QFrame { background-color: #1E293B; border-right: 1px solid #334155; }")
        s_lay = QVBoxLayout(sidebar)
        s_lay.setContentsMargins(20, 20, 20, 20)
        s_lay.setSpacing(10)
        
        logo = QLabel("✈️ AIRLINE\nGUEST")
        logo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("color: #38BDF8; margin-bottom: 20px;")
        s_lay.addWidget(logo)
        
        btn_book = QPushButton("🎟️ Đặt Vé Mới")
        btn_book.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_book.setStyleSheet("text-align: left; padding: 12px; background: transparent; font-size: 13px; font-weight: bold; color: white;")
        btn_book.clicked.connect(self.load_flight_list)
        
        btn_lookup = QPushButton("🔍 Tra Cứu Vé")
        btn_lookup.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_lookup.setStyleSheet("text-align: left; padding: 12px; background: transparent; font-size: 13px; font-weight: bold; color: white;")
        btn_lookup.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        
        s_lay.addWidget(btn_book); s_lay.addWidget(btn_lookup); s_lay.addStretch()
        self.main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.page_flights = self.build_flight_list_page()
        self.page_seatmap = self.build_seat_map_page()
        self.page_lookup = self.build_lookup_page()
        
        self.stack.addWidget(self.page_flights)
        self.stack.addWidget(self.page_seatmap)
        self.stack.addWidget(self.page_lookup)
        self.stack.setCurrentIndex(0)
        
        self.main_layout.addWidget(self.stack)

    def build_flight_list_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        title = QLabel("✈️ DANH SÁCH CHUYẾN BAY")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title)
        
        scr = QScrollArea()
        scr.setWidgetResizable(True)
        self.flight_list_container = QWidget()
        self.flight_list_layout = QVBoxLayout(self.flight_list_container)
        self.flight_list_layout.setSpacing(16)
        self.flight_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scr.setWidget(self.flight_list_container)
        layout.addWidget(scr)
        
        return page

    def load_flight_list(self):
        self.stack.setCurrentIndex(0)
        while self.flight_list_layout.count():
            item = self.flight_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        flights = self.service.get_formatted_flights()
        if not flights:
            empty = QLabel("📭 Hiện không có chuyến bay nào.\nVui lòng quay lại sau.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #94A3B8; font-size: 16px; padding: 40px;")
            self.flight_list_layout.addWidget(empty)
        else:
            for flight in flights:
                card = ModernFlightCard(flight, self)
                self.flight_list_layout.addWidget(card)

    def build_seat_map_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        left = QFrame()
        left.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 16px; border: 1px solid #334155; }")
        l_lay = QVBoxLayout(left)
        l_lay.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_flight_info = QLabel("Chọn chuyến bay")
        self.lbl_flight_info.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.lbl_flight_info.setStyleSheet("color: #38BDF8;")
        self.lbl_flight_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_lay.addWidget(self.lbl_flight_info)
        
        legend = QHBoxLayout()
        for text, _ in [("🟦 Thương gia", "#3B82F6"), ("🟩 Phổ thông", "#10B981"), ("🟨 Đang giữ", "#F59E0B"), ("🟥 Đã bán", "#EF4444")]:
            legend.addWidget(QLabel(text, styleSheet="color: #94A3B8; font-size: 12px;"))
        legend.addStretch()
        l_lay.addLayout(legend)
        
        scr_seat = QScrollArea()
        scr_seat.setWidgetResizable(True)
        self.seat_grid_container = QWidget()
        self.seat_grid = QGridLayout(self.seat_grid_container)
        self.seat_grid.setSpacing(8)
        self.seat_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scr_seat.setWidget(self.seat_grid_container)
        l_lay.addWidget(scr_seat)
        layout.addWidget(left, 5)
        
        right = QFrame()
        right.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 16px; border: 1px solid #334155; }")
        r_lay = QVBoxLayout(right)
        r_lay.setContentsMargins(24, 24, 24, 24)
        r_lay.setSpacing(16)
        
        form_title = QLabel("📝 THÔNG TIN HÀNH KHÁCH")
        form_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        form_title.setStyleSheet("color: #10B981;")
        r_lay.addWidget(form_title)
        
        self.in_name = QLineEdit(); self.in_name.setPlaceholderText("Họ và tên (*)")
        self.in_phone = QLineEdit(); self.in_phone.setPlaceholderText("Số điện thoại (*)")
        self.in_id = QLineEdit(); self.in_id.setPlaceholderText("CCCD / Passport (*)")
        self.in_email = QLineEdit(); self.in_email.setPlaceholderText("Email (tùy chọn)")
        
        for w in [self.in_name, self.in_phone, self.in_id, self.in_email]: r_lay.addWidget(w)
        
        # BẢNG VOUCHERS
        r_lay.addWidget(QLabel("🎟️ MÃ GIẢM GIÁ KHẢ DỤNG", styleSheet="color: #38BDF8; font-weight: bold; margin-top: 5px;"))
        self.table_vouchers = QTableWidget(0, 3)
        self.table_vouchers.setHorizontalHeaderLabels(["Mã Code", "Giảm (%)", "Tối đa"])
        self.table_vouchers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_vouchers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_vouchers.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_vouchers.doubleClicked.connect(self.apply_voucher_from_table)
        self.table_vouchers.setFixedHeight(100)
        r_lay.addWidget(self.table_vouchers)

        self.in_voucher = QLineEdit()
        self.in_voucher.setPlaceholderText("Nhập hoặc double-click mã ở trên...")
        self.in_voucher.textChanged.connect(self.update_price_display)
        r_lay.addWidget(self.in_voucher)

        bill = QFrame()
        bill.setStyleSheet("QFrame { background-color: #0F172A; border-radius: 8px; border: 1px solid #334155; padding: 16px; }")
        b_lay = QVBoxLayout(bill)
        
        self.lbl_sel_seat = QLabel("💺 Ghế: Chưa chọn"); self.lbl_sel_seat.setStyleSheet("color: #94A3B8;")
        self.lbl_base_price = QLabel("Giá cơ bản: 0 ₫"); self.lbl_base_price.setStyleSheet("color: #94A3B8;")
        self.lbl_discount = QLabel("Giảm giá: 0 ₫ (0%)"); self.lbl_discount.setStyleSheet("color: #F59E0B;")
        self.lbl_total = QLabel("TỔNG TIỀN: 0 ₫")
        self.lbl_total.setFont(QFont("Arial", 16, QFont.Weight.Bold)); self.lbl_total.setStyleSheet("color: #10B981;")
        
        for lbl in [self.lbl_sel_seat, self.lbl_base_price, self.lbl_discount, self.lbl_total]: b_lay.addWidget(lbl)
        r_lay.addWidget(bill); r_lay.addStretch()
        
        self.btn_pay = QPushButton("💳 ĐẶT VÉ & THANH TOÁN")
        self.btn_pay.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pay.setStyleSheet("background-color: #10B981; color: #0F172A; padding: 14px; font-weight: bold; border-radius: 8px;")
        self.btn_pay.clicked.connect(lambda: self.submit_booking(is_hold=False))
        
        self.btn_hold = QPushButton("⏳ GIỮ CHỖ TRẢ SAU (15 PHÚT)")
        self.btn_hold.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_hold.setStyleSheet("background-color: #F59E0B; color: #0F172A; padding: 14px; font-weight: bold; border-radius: 8px;")
        self.btn_hold.clicked.connect(lambda: self.submit_booking(is_hold=True))
        
        btn_back = QPushButton("⬅️ QUAY LẠI")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.setStyleSheet("background: transparent; border: 1px solid #475569; color: #94A3B8; padding: 12px; border-radius: 8px; font-weight:bold;")
        btn_back.clicked.connect(self.load_flight_list)
        
        for btn in [self.btn_pay, self.btn_hold, btn_back]: r_lay.addWidget(btn)
        layout.addWidget(right, 4)
        
        return page

    def load_vouchers(self):
        """Load danh sách vouchers đang hoạt động lên bảng UI"""
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
            self.in_voucher.setText(self.table_vouchers.item(row, 0).text())

    def open_seat_map(self, flight):
        self.current_flight = flight
        self.selected_seat = None
        self.lbl_flight_info.setText(f"✈ {flight['flight_number']} | {flight['dep_city']} → {flight['arr_city']}")
        for w in [self.in_name, self.in_phone, self.in_id, self.in_email, self.in_voucher]: w.clear()
        
        self.lbl_sel_seat.setText("💺 Ghế: Chưa chọn")
        self.load_vouchers() # Gọi load danh sách Vouchers lên Bảng
        self.update_price_display()
        
        while self.seat_grid.count():
            item = self.seat_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        seats = self.service.get_seat_map(flight['flight_id'])
        row_map = {}; current_row = 0
        
        for seat in sorted(seats, key=lambda s: (s['seat_number'][0], int(s['seat_number'][1:]))):
            match = re.match(r"([A-Za-z]+)(\d+)", seat['seat_number'])
            if not match: continue
            
            letter, num = match.groups()
            if letter not in row_map:
                row_map[letter] = current_row
                row_lbl = QLabel(f"<b style='font-size:14px;'>{letter}</b>")
                row_lbl.setStyleSheet("color: #94A3B8; padding: 8px;")
                row_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.seat_grid.addWidget(row_lbl, current_row, 0)
                current_row += 1
            
            btn = QPushButton(seat['seat_number'])
            btn.setFixedSize(50, 50)
            btn.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            
            if seat['seat_status'] == 'AVAILABLE':
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                bg_color = "#3B82F6" if seat['class_name'].upper() == 'BUSINESS' else "#10B981"
                btn.setStyleSheet(f"background-color: {bg_color}; color: white; border-radius: 6px;")
                btn.clicked.connect(lambda checked, s=seat: self.select_seat(s))
            elif seat['seat_status'] == 'HELD':
                btn.setStyleSheet("background-color: #F59E0B; color: #0F172A; border-radius: 6px; font-weight: bold;")
                btn.setEnabled(False)
            else:
                btn.setStyleSheet("background-color: #EF4444; color: white; border-radius: 6px; font-weight: bold;")
                btn.setEnabled(False)
            
            col = int(num) if int(num) <= 2 else int(num) + 1
            self.seat_grid.addWidget(btn, row_map[letter], col)
        
        self.stack.setCurrentIndex(1)

    def select_seat(self, seat):
        self.selected_seat = seat
        self.lbl_sel_seat.setText(f"💺 Ghế: <b>{seat['seat_number']}</b> ({seat['class_name']})")
        self.update_price_display()

    def update_price_display(self):
        if not self.current_flight or not self.selected_seat:
            self.lbl_base_price.setText("Giá cơ bản: 0 ₫")
            self.lbl_discount.setText("Giảm giá: 0 ₫ (0%)")
            self.lbl_total.setText("TỔNG TIỀN: 0 ₫")
            return
        
        voucher_code = self.in_voucher.text().strip()
        voucher = None
        if voucher_code:
            ok, msg, voucher = self.service.validate_voucher(voucher_code)
            if not ok: voucher = None
        
        pricing = self.service.calculate_final_price(
            float(self.current_flight['base_price']),
            float(self.selected_seat['price_multiplier']),
            0.0,
            voucher
        )
        
        self.lbl_base_price.setText(f"Giá cơ bản: {pricing['price_after_class']:,.0f} ₫")
        self.lbl_discount.setText(f"Giảm giá: {pricing['discount_amount']:,.0f} ₫ ({pricing['discount_percent']:.0f}%)")
        self.lbl_total.setText(f"TỔNG TIỀN: {pricing['final_price']:,.0f} ₫")

    def submit_booking(self, is_hold: bool):
        if not self.selected_seat:
            return QMessageBox.warning(self, "⚠️ Lỗi", "Vui lòng chọn 1 ghế trên sơ đồ!")
        
        method = 'CASH'
        if not is_hold:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Chọn phương thức thanh toán")
            msgBox.setText("Vui lòng chọn phương thức thanh toán cho vé này:")
            btn_cash = msgBox.addButton("💵 Tiền mặt", QMessageBox.ButtonRole.ActionRole)
            btn_qr = msgBox.addButton("📲 Quét mã QR", QMessageBox.ButtonRole.ActionRole)
            msgBox.addButton("Hủy bỏ", QMessageBox.ButtonRole.RejectRole)
            msgBox.exec()
            
            if msgBox.clickedButton() == btn_cash: method = 'CASH'
            elif msgBox.clickedButton() == btn_qr: method = 'VNPAY'
            else: return 
                
            if method == 'VNPAY':
                total = float(self.lbl_total.text().split(": ")[1].split(" ")[0].replace(",", ""))
                popup = AdminQRPaymentPopup(total, f"MUA VE {self.current_flight['flight_number']}", self)
                if popup.exec() != QDialog.DialogCode.Accepted:
                    return QMessageBox.information(self, "Đã hủy", "Giao dịch QR bị hủy.")
        
        ok, msg = self.service.book_single_ticket(
            self.in_name.text().strip(),
            self.in_phone.text().strip(),
            self.in_id.text().strip(),
            self.in_email.text().strip(),
            self.current_flight,
            self.selected_seat,
            self.in_voucher.text().strip(),
            is_hold
        )
        
        if not ok: return QMessageBox.critical(self, "❌ Lỗi", msg)
        QMessageBox.information(self, "✅ Thành Công", msg)
        self.load_flight_list()

    # Tra cứu vé
    def build_lookup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(24)
        
        title = QLabel("🔍 TRA CỨU VÉ")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #38BDF8;")
        layout.addWidget(title)
        
        search_frame = QFrame()
        search_frame.setStyleSheet("QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; padding: 20px; }")
        s_lay = QHBoxLayout(search_frame)
        s_lay.setSpacing(16)
        
        self.in_lookup_phone = QLineEdit(); self.in_lookup_phone.setPlaceholderText("📱 Số điện thoại (*)"); self.in_lookup_phone.setMinimumHeight(40)
        self.in_lookup_pnr = QLineEdit(); self.in_lookup_pnr.setPlaceholderText("🎫 Mã PNR (*)"); self.in_lookup_pnr.setMinimumHeight(40)
        
        btn_search = QPushButton("Tra Cứu")
        btn_search.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_search.setStyleSheet("background-color: #38BDF8; color: #0F172A; padding: 10px 40px; font-weight: bold; border-radius: 8px;")
        btn_search.setMinimumHeight(40)
        btn_search.clicked.connect(self.action_lookup)
        
        s_lay.addWidget(self.in_lookup_phone, 2); s_lay.addWidget(self.in_lookup_pnr, 2); s_lay.addWidget(btn_search, 1)
        layout.addWidget(search_frame)
        
        self.lookup_result_container = QWidget()
        self.lookup_result_layout = QVBoxLayout(self.lookup_result_container)
        self.lookup_result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lookup_result_layout.setSpacing(16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.lookup_result_container)
        layout.addWidget(scroll)
        
        return page

    def action_lookup(self):
        while self.lookup_result_layout.count():
            item = self.lookup_result_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        phone = self.in_lookup_phone.text().strip()
        pnr = self.in_lookup_pnr.text().strip()
        
        if not phone or not pnr:
            err_lbl = QLabel("⚠️ Vui lòng nhập đầy đủ SĐT và Mã PNR")
            err_lbl.setStyleSheet("color: #EF4444; font-size: 14px; padding: 20px;")
            err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lookup_result_layout.addWidget(err_lbl)
            return
        
        ok, msg, ticket = self.service.lookup_my_ticket(pnr, phone)
        
        if not ok:
            err_lbl = QLabel(f"❌ {msg}")
            err_lbl.setStyleSheet("color: #EF4444; font-size: 14px; padding: 20px; background-color: #EF444420; border-radius: 8px;")
            err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lookup_result_layout.addWidget(err_lbl)
        else:
            card = TicketResultCard(ticket, self)
            self.lookup_result_layout.addWidget(card)