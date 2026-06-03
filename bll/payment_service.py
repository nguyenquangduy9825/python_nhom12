# bll/payment_service.py
"""
Service layer cho Payment workflows.
Xử lý: payment validation, processing, status updates.
"""
from typing import Tuple
from dal.customer_repository import CustomerBookingRepository


class PaymentService:
    """Xử lý payment logic"""
    
    def __init__(self):
        self.repo = CustomerBookingRepository()

    def process_held_payment(self, ticket_code: str, amount: float, 
                           method: str = 'VNPAY') -> Tuple[bool, str]:
        """
        Thanh toán vé HELD:
        - Validate amount
        - Gọi repo để update ticket + tạo payment record
        """
        if not ticket_code or not ticket_code.strip():
            return False, "Mã PNR không hợp lệ"
        
        if amount <= 0:
            return False, "Số tiền thanh toán phải lớn hơn 0"
        
        if method not in ['VNPAY', 'MOMO', 'CASH', 'BANK_TRANSFER', 'CREDIT_CARD']:
            return False, "Phương thức thanh toán không hỗ trợ"
        
        return self.repo.pay_held_ticket(ticket_code, amount, method)

    def validate_qr_payment(self, qr_data: str) -> Tuple[bool, str]:
        """Validate QR payment data (mock)"""
        if not qr_data or len(qr_data) < 10:
            return False, "Dữ liệu QR không hợp lệ"
        
        return True, "QR hợp lệ"