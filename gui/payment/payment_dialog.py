# gui/payment/payment_dialog.py
"""
Dialog cho thanh toán QR + countdown.
Hiển thị: Flight info, passenger info, total, QR code, countdown timer.
"""
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QProgressBar, QMessageBox,
                             QComboBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont


class PaymentQRDialog(QDialog):
    """Dialog thanh toán với QR code + countdown 15 phút"""
    
    payment_completed = pyqtSignal(bool)  # True = thành công, False = timeout
    
    def __init__(self, ticket_info: dict, parent=None):
        """
        ticket_info dict phải có:
        - pnr: Mã PNR
        - flight_code: Mã chuyến
        - seat_number: Ghế
        - passenger_name: Tên hành khách
        - total_price: Tổng tiền
        - hold_minutes: Thời gian giữ (default 15 phút)
        """
        super().__init__(parent)
        self.ticket_info = ticket_info
        self.hold_time = ticket_info.get('hold_minutes', 15) * 60  # Convert to seconds
        self.time_remaining = self.hold_time
        self.setup_ui()
        
    def setup_ui(self):
        """Xây dựng giao diện"""
        self.setWindowTitle(f"💳 Thanh Toán - {self.ticket_info.get('pnr', 'N/A')}")
        self.setFixedSize(650, 800)
        self.setStyleSheet("""
            QDialog { background-color: #0F172A; color: #F8FAFC; }
            QLabel { color: #F8FAFC; background: transparent; }
            QPushButton { border-radius: 8px; font-weight: bold; padding: 12px; }
            QFrame { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QComboBox { background-color: #1E293B; color: #F8FAFC; border-radius: 8px; padding: 8px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # ========== PHẦN 1: Thông tin vé ==========
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(10)
        
        title_lbl = QLabel("📋 THÔNG TIN VÉ")
        title_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        info_layout.addWidget(title_lbl)
        
        info_layout.addWidget(QLabel(f"🎫 Mã PNR: <b>{self.ticket_info.get('pnr', 'N/A')}</b>"))
        info_layout.addWidget(QLabel(f"✈ Chuyến: {self.ticket_info.get('flight_code', 'N/A')}"))
        info_layout.addWidget(QLabel(f"💺 Ghế: {self.ticket_info.get('seat_number', 'N/A')}"))
        info_layout.addWidget(QLabel(f"👤 Hành khách: {self.ticket_info.get('passenger_name', 'N/A')}"))
        
        price_lbl = QLabel(f"💰 Tổng tiền: {self.ticket_info.get('total_price', 0):,.0f} VNĐ")
        price_lbl.setStyleSheet("color: #10B981; font-size: 16px; font-weight: bold;")
        info_layout.addWidget(price_lbl)
        
        layout.addWidget(info_frame)
        
        # ========== PHẦN 2: QR Code ==========
        qr_frame = QFrame()
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.setContentsMargins(20, 20, 20, 20)
        
        qr_label = QLabel("📱 MÃ QR THANH TOÁN")
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        qr_layout.addWidget(qr_label)
        
        # Load QR image
        qr_path = os.path.join(os.path.dirname(__file__), "..", "..", "my_qr.png")
        if os.path.exists(qr_path):
            qr_pixmap = QPixmap(qr_path).scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            qr_img = QLabel()
            qr_img.setPixmap(qr_pixmap)
            qr_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_layout.addWidget(qr_img)
        else:
            qr_layout.addWidget(QLabel("(Không tìm thấy file QR)"))
        
        instruction = QLabel("Quét mã QR bằng ứng dụng banking\nhoặc ứng dụng ví điện tử của bạn")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("color: #94A3B8; font-size: 13px;")
        qr_layout.addWidget(instruction)
        
        layout.addWidget(qr_frame)
        
        # ========== PHẦN 3: Countdown ==========
        countdown_frame = QFrame()
        countdown_layout = QVBoxLayout(countdown_frame)
        countdown_layout.setContentsMargins(20, 20, 20, 20)
        countdown_layout.setSpacing(12)
        
        countdown_title = QLabel("⏱ THỜI GIAN GIỮ CHỖ")
        countdown_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        countdown_layout.addWidget(countdown_title)
        
        self.time_label = QLabel(f"{self.hold_time // 60}:00")
        self.time_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #38BDF8;")
        countdown_layout.addWidget(self.time_label)
        
        self.progress = QProgressBar()
        self.progress.setMaximum(self.hold_time)
        self.progress.setValue(self.hold_time)
        self.progress.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; background-color: #334155; }
            QProgressBar::chunk { background-color: #10B981; }
        """)
        countdown_layout.addWidget(self.progress)
        
        layout.addWidget(countdown_frame)
        
        # ========== PHẦN 4: Nút hành động ==========
        btn_layout = QHBoxLayout()
        
        self.btn_confirm = QPushButton("✅ Đã Thanh Toán")
        self.btn_confirm.setStyleSheet("background-color: #10B981; color: #0F172A; font-size: 14px;")
        self.btn_confirm.clicked.connect(self.on_payment_confirmed)
        
        btn_cancel = QPushButton("❌ Huỷ")
        btn_cancel.setStyleSheet("background-color: #EF4444; color: white; font-size: 14px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        # Start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)
    
    def update_countdown(self):
        """Update countdown timer"""
        self.time_remaining -= 1
        self.progress.setValue(self.time_remaining)
        
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.time_label.setText(f"{minutes}:{seconds:02d}")
        
        # Color warning
        if self.time_remaining <= 60:
            self.time_label.setStyleSheet("color: #F59E0B;")
        if self.time_remaining <= 30:
            self.time_label.setStyleSheet("color: #EF4444;")
        
        # Timeout
        if self.time_remaining <= 0:
            self.timer.stop()
            self.on_timeout()
    
    def on_payment_confirmed(self):
        """User confirm đã thanh toán"""
        self.timer.stop()
        self.payment_completed.emit(True)
        self.accept()
    
    def on_timeout(self):
        """Hết thời gian"""
        self.btn_confirm.setEnabled(False)
        QMessageBox.warning(
            self, 
            "⏰ Hết Thời Gian", 
            "Thời gian giữ ghế đã hết. Ghế sẽ được hoàn trả và vé tự động hủy."
        )
        self.payment_completed.emit(False)
        self.reject()


class PaymentMethodDialog(QDialog):
    """Dialog chọn phương thức thanh toán cho vé HELD"""
    
    payment_confirmed = pyqtSignal(str, float)  # method, amount
    
    def __init__(self, ticket_info: dict, parent=None):
        super().__init__(parent)
        self.ticket_info = ticket_info
        self.setup_ui()
    
    def setup_ui(self):
        """Xây dựng giao diện chọn phương thức"""
        self.setWindowTitle("Chọn Phương Thức Thanh Toán")
        self.setFixedSize(500, 300)
        self.setStyleSheet("""
            QDialog { background-color: #0F172A; color: #F8FAFC; }
            QLabel { color: #F8FAFC; background: transparent; }
            QComboBox { background-color: #1E293B; color: #F8FAFC; border-radius: 8px; padding: 8px; }
            QPushButton { border-radius: 8px; font-weight: bold; padding: 10px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # Thông tin
        info_lbl = QLabel(f"💳 Thanh Toán: {self.ticket_info.get('total_price', 0):,.0f} VNĐ")
        info_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        info_lbl.setStyleSheet("color: #10B981;")
        layout.addWidget(info_lbl)
        
        # Chọn phương thức
        layout.addWidget(QLabel("Phương thức thanh toán:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "VNPAY - Ví Việt",
            "MOMO - Ứng dụng Momo",
            "BANK_TRANSFER - Chuyển khoản",
            "CREDIT_CARD - Thẻ tín dụng"
        ])
        layout.addWidget(self.method_combo)
        
        layout.addStretch()
        
        # Nút hành động
        btn_layout = QHBoxLayout()
        btn_pay = QPushButton("✅ Xác Nhận Thanh Toán")
        btn_pay.setStyleSheet("background-color: #10B981; color: #0F172A;")
        btn_pay.clicked.connect(self.confirm_payment)
        
        btn_cancel = QPushButton("❌ Huỷ")
        btn_cancel.setStyleSheet("background-color: #EF4444; color: white;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_pay)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def confirm_payment(self):
        """Confirm phương thức thanh toán"""
        method_text = self.method_combo.currentText()
        method = method_text.split(" ")[0]  # VNPAY, MOMO, etc
        
        self.payment_confirmed.emit(method, float(self.ticket_info.get('total_price', 0)))
        self.accept()
