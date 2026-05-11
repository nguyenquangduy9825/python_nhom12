# gui/payment/payment_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from bll.payment_service import PaymentService

class PaymentDialog(QDialog):
    def __init__(self, booking_info, parent=None):
        super().__init__(parent)
        self.booking_info = booking_info
        self.payment_service = PaymentService()
        self.setup_ui()

        # Đếm ngược 5 phút (300 giây)
        self.time_left = 300 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def setup_ui(self):
        self.setWindowTitle("Thanh toán & Xuất vé")
        self.setFixedSize(450, 350)
        self.setStyleSheet("background-color: #1e293b; color: white;")
        layout = QVBoxLayout(self)

        self.lbl_timer = QLabel("⏳ Ghế đang giữ. Hết hạn sau: 05:00")
        self.lbl_timer.setStyleSheet("color: #f59e0b; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.lbl_timer, alignment=Qt.AlignmentFlag.AlignCenter)

        # Thông tin thanh toán
        lbl_price = QLabel(f"Tổng thanh toán: {self.booking_info['final_price']:,.0f} VND")
        lbl_price.setStyleSheet("font-size: 24px; font-weight: bold; color: #22c55e; margin: 20px 0;")
        layout.addWidget(lbl_price, alignment=Qt.AlignmentFlag.AlignCenter)

        self.cb_method = QComboBox()
        self.cb_method.addItems(["CASH (Tiền mặt)", "CREDIT_CARD (Thẻ tín dụng)", "BANK_TRANSFER (Chuyển khoản)", "MOMO", "VNPAY"])
        self.cb_method.setStyleSheet("padding: 10px; border-radius: 5px; background: #0f172a;")
        layout.addWidget(QLabel("Chọn phương thức thanh toán:"))
        layout.addWidget(self.cb_method)

        layout.addStretch()
        
        btn_pay = QPushButton("💳 XÁC NHẬN THANH TOÁN")
        btn_pay.setStyleSheet("background-color: #3b82f6; font-size: 16px; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_pay.clicked.connect(self.process_payment)
        layout.addWidget(btn_pay)

    def update_timer(self):
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        self.lbl_timer.setText(f"⏳ Ghế đang giữ. Hết hạn sau: {mins:02d}:{secs:02d}")
        
        if self.time_left <= 0:
            self.timer.stop()
            QMessageBox.warning(self, "Hết giờ", "Đã hết thời gian giữ chỗ. Hệ thống sẽ nhả ghế!")
            self.reject() # Đóng dialog

    def process_payment(self):
        method = self.cb_method.currentText().split()[0] # Lấy phương thức thanh toán
        success, msg = self.payment_service.process_payment(self.booking_info, method)
        
        if success:
            self.timer.stop()
            QMessageBox.information(self, "Boarding Pass", f"🎉 {msg}\n\nVé điện tử đã được gửi qua Email!")
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi Thanh Toán", msg)
            self.reject()