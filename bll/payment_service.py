# bll/payment_service.py
from dal.payment_repository import PaymentRepository

class PaymentService:
    def __init__(self):
        self.payment_repo = PaymentRepository()

    def process_payment(self, booking_info, payment_method):
        if booking_info['final_price'] < 0:
            return False, "Số tiền thanh toán không hợp lệ!"
        
        # Gọi Transaction từ DAL
        success, result = self.payment_repo.create_payment_transaction(booking_info, payment_method)
        if success:
            return True, f"Thanh toán thành công!\nMã giao dịch: {result}"
        return False, result