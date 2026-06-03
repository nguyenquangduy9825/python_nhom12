# gui/views/staff_profile_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QCursor, QFont
from bll.admin_service import AdminService

class StaffProfileScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.service = AdminService()
        self.setup_ui()
        self.setup_clock()

    def apply_role_permissions(self, user_obj):
        self.current_user = user_obj
        if self.current_user:
            username = getattr(user_obj, 'username', 'Nhân viên') if not isinstance(user_obj, dict) else user_obj.get('username', 'Nhân viên')
            self.lbl_welcome.setText(f"👋 Xin chào, {username}!")
            self.load_history()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
            QFrame#Card { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QLineEdit { padding: 12px; border-radius: 8px; background-color: #0F172A; border: 1px solid #475569; color: white; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #38BDF8; }
            QPushButton { font-weight: bold; border-radius: 8px; padding: 12px; font-size: 14px; }
            QTableWidget { background-color: #0F172A; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; outline: none; }
            QHeaderView::section { background-color: #1E293B; color: #94A3B8; padding: 10px; font-weight: bold; border: none; text-align: left; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(32)

        # CỘT 1: CHẤM CÔNG HÀNG NGÀY
        time_card = QFrame(); time_card.setObjectName("Card")
        time_lay = QVBoxLayout(time_card)
        time_lay.setContentsMargins(32, 32, 32, 32)
        time_lay.setSpacing(20)

        self.lbl_welcome = QLabel("👋 Xin chào, Nhân viên!")
        self.lbl_welcome.setStyleSheet("font-size: 22px; font-weight: 900; color: #38BDF8;")
        time_lay.addWidget(self.lbl_welcome, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_clock = QLabel("00:00:00")
        self.lbl_clock.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        self.lbl_clock.setStyleSheet("color: #10B981;")
        time_lay.addWidget(self.lbl_clock, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_date = QLabel("Ngày --/--/----")
        self.lbl_date.setStyleSheet("font-size: 16px; color: #94A3B8; margin-bottom: 20px;")
        time_lay.addWidget(self.lbl_date, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_box = QHBoxLayout(); btn_box.setSpacing(16)
        btn_checkin = QPushButton("🟢 CHECK-IN (Vào ca)")
        btn_checkin.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_checkin.setStyleSheet("background-color: #10B981; color: #0F172A; font-size: 16px;")
        btn_checkin.clicked.connect(self.handle_checkin)
        
        btn_checkout = QPushButton("🔴 CHECK-OUT (Tan ca)")
        btn_checkout.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_checkout.setStyleSheet("background-color: #EF4444; color: white; font-size: 16px;")
        btn_checkout.clicked.connect(self.handle_checkout)

        btn_box.addWidget(btn_checkin); btn_box.addWidget(btn_checkout)
        time_lay.addLayout(btn_box)
        time_lay.addStretch()
        top_layout.addWidget(time_card, 1)

        # CỘT 2: ĐỔI MẬT KHẨU
        pass_card = QFrame(); pass_card.setObjectName("Card")
        pass_lay = QVBoxLayout(pass_card)
        pass_lay.setContentsMargins(32, 32, 32, 32)
        pass_lay.setSpacing(16)

        pass_title = QLabel("🔒 ĐỔI MẬT KHẨU CÁ NHÂN")
        pass_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #F59E0B;")
        pass_lay.addWidget(pass_title)
        pass_lay.addWidget(QLabel("Bảo mật: Nên đổi mật khẩu định kỳ 3 tháng/lần.", styleSheet="color: #94A3B8; margin-bottom: 10px;"))

        self.in_old_pw = QLineEdit(); self.in_old_pw.setPlaceholderText("Mật khẩu hiện tại"); self.in_old_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_new_pw = QLineEdit(); self.in_new_pw.setPlaceholderText("Mật khẩu mới"); self.in_new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_confirm_pw = QLineEdit(); self.in_confirm_pw.setPlaceholderText("Nhập lại mật khẩu mới"); self.in_confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)

        pass_lay.addWidget(QLabel("Mật khẩu cũ:")); pass_lay.addWidget(self.in_old_pw)
        pass_lay.addWidget(QLabel("Mật khẩu mới:")); pass_lay.addWidget(self.in_new_pw)
        pass_lay.addWidget(QLabel("Xác nhận mật khẩu:")); pass_lay.addWidget(self.in_confirm_pw)

        btn_change_pw = QPushButton("💾 LƯU MẬT KHẨU MỚI")
        btn_change_pw.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_change_pw.setStyleSheet("background-color: #F59E0B; color: #0F172A; margin-top: 10px;")
        btn_change_pw.clicked.connect(self.handle_change_password)
        pass_lay.addWidget(btn_change_pw)
        pass_lay.addStretch()
        top_layout.addWidget(pass_card, 1)

        main_layout.addLayout(top_layout)

        # PHẦN DƯỚI: BẢNG LỊCH SỬ CHẤM CÔNG
        history_card = QFrame(); history_card.setObjectName("Card")
        hist_lay = QVBoxLayout(history_card)
        hist_lay.addWidget(QLabel("📋 LỊCH SỬ VÀO/RA CA (30 NGÀY GẦN NHẤT)", styleSheet="font-size: 16px; font-weight: bold; color: #38BDF8;"))
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Ngày làm việc", "Giờ Check-in", "Giờ Check-out", "Tổng thời gian (Giờ)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        hist_lay.addWidget(self.table)
        
        main_layout.addWidget(history_card)

    def setup_clock(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        now = QDateTime.currentDateTime()
        self.lbl_clock.setText(now.toString("hh:mm:ss"))
        self.lbl_date.setText(now.toString("Ngày dd/MM/yyyy"))

    def _get_user_id(self):
        if not self.current_user: return None
        return getattr(self.current_user, 'user_id') if not isinstance(self.current_user, dict) else self.current_user.get('user_id')

    def handle_checkin(self):
        uid = self._get_user_id()
        if not uid: return
        ok, msg = self.service.record_check_in(uid)
        if ok:
            QMessageBox.information(self, "Thành công", msg)
            self.load_history()
        else: QMessageBox.warning(self, "Lỗi", msg)

    def handle_checkout(self):
        uid = self._get_user_id()
        if not uid: return
        ok, msg = self.service.record_check_out(uid)
        if ok:
            QMessageBox.information(self, "Thành công", msg)
            self.load_history()
        else: QMessageBox.warning(self, "Lỗi", msg)

    def load_history(self):
        uid = self._get_user_id()
        if not uid: return
        records = self.service.get_timekeeping_history(uid)
        
        self.table.setRowCount(0)
        for r, rec in enumerate(records):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(rec['work_date'].strftime("%d/%m/%Y")))
            
            c_in = rec['check_in_time'].strftime("%H:%M:%S") if rec['check_in_time'] else "--"
            self.table.setItem(r, 1, QTableWidgetItem(c_in))
            
            c_out = rec['check_out_time'].strftime("%H:%M:%S") if rec['check_out_time'] else "Chưa tan ca"
            self.table.setItem(r, 2, QTableWidgetItem(c_out))
            
            # Tính tổng giờ nếu đã checkout
            if rec['check_in_time'] and rec['check_out_time']:
                diff = rec['check_out_time'] - rec['check_in_time']
                hours = round(diff.total_seconds() / 3600, 2)
                self.table.setItem(r, 3, QTableWidgetItem(f"{hours}h"))
            else:
                self.table.setItem(r, 3, QTableWidgetItem("--"))

    def handle_change_password(self):
        uid = self._get_user_id()
        if not uid: return

        old_pw = self.in_old_pw.text().strip()
        new_pw = self.in_new_pw.text().strip()
        confirm = self.in_confirm_pw.text().strip()

        if not old_pw or not new_pw or not confirm:
            return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ các trường!")
        if new_pw != confirm:
            return QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp!")

        success, msg = self.service.change_my_password(uid, old_pw, new_pw)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.in_old_pw.clear(); self.in_new_pw.clear(); self.in_confirm_pw.clear()
        else:
            QMessageBox.warning(self, "Lỗi", msg)