# bll/ticket_service.py
from dal.ticket_dao import TicketDAO

class TicketService:
    def __init__(self):
        self.ticket_dao = TicketDAO()
        
    def process_booking(self, flight_id, customer_id, seat_id, base_price, discount_amount, pay_method, voucher_id=None):
        # 1. Logic tính toán giá cuối cùng
        final_price = base_price - discount_amount
        if final_price < 0:
            final_price = 0
            
        # 2. Ràng buộc nghiệp vụ: Kiểm tra phương thức thanh toán hợp lệ
        valid_methods = ['CASH', 'CREDIT_CARD', 'BANK_TRANSFER']
        if pay_method not in valid_methods:
            raise ValueError("Phương thức thanh toán không hợp lệ!")
            
        # 3. Đẩy xuống DB
        ticket_id = self.ticket_dao.book_ticket(
            flight_id, customer_id, seat_id, voucher_id, base_price, final_price, pay_method
        )
        
        if ticket_id == -2:
            raise Exception("Ghế này đã có người đặt. Vui lòng chọn ghế khác!")
        elif ticket_id == -1:
            raise Exception("Lỗi hệ thống khi đặt vé. Vui lòng thử lại!")
            
        return ticket_id