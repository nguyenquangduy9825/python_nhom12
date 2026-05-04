# gui/views/booking_view_logic.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox, QLineEdit
from bll.booking_service import BookingService

class BookingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.booking_service = BookingService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # ... (Giả sử bạn có các ô nhập liệu được đặt tên như bên dưới)
        self.txt_name = QLineEdit()
        self.txt_phone = QLineEdit()
        self.txt_cccd = QLineEdit()
        self.txt_voucher = QLineEdit()
        
        # Nút bấm xuất vé và giữ vé
        self.btn_confirm = QPushButton("✅ Xác nhận Đặt Vé (Thu tiền ngay)")
        self.btn_confirm.clicked.connect(lambda: self.on_booking_click(is_hold=False))
        
        self.btn_hold = QPushButton("⏳ Giữ Chỗ (Thanh toán sau 24h)")
        self.btn_hold.clicked.connect(lambda: self.on_booking_click(is_hold=True))
        
        layout.addWidget(self.btn_confirm)
        layout.addWidget(self.btn_hold)

    def on_booking_click(self, is_hold):
        # 1. Gom dữ liệu từ giao diện
        customer_info = {
            'full_name': self.txt_name.text().strip(),
            'phone': self.txt_phone.text().strip(),
            'id_card': self.txt_cccd.text().strip(),
            'email': 'khachhang@email.com' # Tùy chọn
        }
        
        voucher_code = self.txt_voucher.text().strip()
        
        # Giả định lấy từ Combobox đang được chọn
        selected_flight_id = 1 
        selected_seat_id = 10 
        base_price = 1500000 
        
        # 2. Gọi BLL xử lý nghiệp vụ
        success, message = self.booking_service.process_booking(
            customer_info=customer_info,
            flight_id=selected_flight_id,
            seat_id=selected_seat_id,
            base_price=base_price,
            voucher_code=voucher_code if voucher_code else None,
            is_hold=is_hold # True nếu bấm nút Giữ vé
        )
        
        # 3. Hiển thị kết quả ra UI
        if success:
            QMessageBox.information(self, "Hoàn tất", message)
            # Reset Form
            self.txt_name.clear()
            self.txt_phone.clear()
            self.txt_cccd.clear()
        else:
            QMessageBox.warning(self, "Lỗi Giao Dịch", message)