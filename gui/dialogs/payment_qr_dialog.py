# gui/dialogs/payment_qr_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
import os

class QRPaymentDialog(QDialog):
    def __init__(self, booking_code, total_amount, parent=None):
        super().__init__(parent)
        self.booking_code = booking_code
        self.total_amount = total_amount
        self.time_left = 900  # 15 phút
        self.is_paid = False
        self.setup_ui()
        self.start_timer()

    def setup_ui(self):
        self.setWindowTitle("Thanh toán QR")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #0F172A; color: white; border-radius: 10px;")
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("💳 QUÉT MÃ QR", styleSheet="font-size: 22px; font-weight: bold; color: #38BDF8;"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Countdown
        self.lbl_timer = QLabel("⏳ Còn lại: 15:00")
        self.lbl_timer.setStyleSheet("font-size: 18px; color: #F59E0B; font-weight: bold;")
        layout.addWidget(self.lbl_timer, alignment=Qt.AlignmentFlag.AlignCenter)

        # QR Image (Load ảnh thật)
        qr_lbl = QLabel()
        qr_path = "assets/my_qr.png"
        if os.path.exists(qr_path):
            pixmap = QPixmap(qr_path).scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            qr_lbl.setPixmap(pixmap)
        else:
            qr_lbl.setText("[ Lỗi: Không tìm thấy assets/my_qr.png ]")
        qr_lbl.setStyleSheet("background-color: white; padding: 10px; border-radius: 8px;")
        layout.addWidget(qr_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Info
        info = QFrame()
        info.setStyleSheet("background-color: #1E293B; border-radius: 8px; padding: 15px;")
        i_lay = QVBoxLayout(info)
        i_lay.addWidget(QLabel(f"Mã Đặt Chỗ: {self.booking_code}", styleSheet="font-size:16px; font-weight:bold;"))
        i_lay.addWidget(QLabel(f"Tổng Tiền: {self.total_amount:,.0f} VNĐ", styleSheet="font-size:20px; color:#10B981; font-weight:bold;"))
        layout.addWidget(info)

        # Nút xác nhận
        btn_confirm = QPushButton("✅ TÔI ĐÃ CHUYỂN KHOẢN")
        btn_confirm.setFixedHeight(50)
        btn_confirm.setStyleSheet("background-color: #10B981; font-weight: bold; font-size: 16px; border-radius: 8px;")
        btn_confirm.clicked.connect(self.confirm_payment)
        layout.addWidget(btn_confirm)

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        self.lbl_timer.setText(f"⏳ Còn lại: {mins:02d}:{secs:02d}")
        if self.time_left <= 0:
            self.timer.stop()
            self.reject() # Hết giờ tự tắt form

    def confirm_payment(self):
        self.timer.stop()
        self.is_paid = True
        self.accept()