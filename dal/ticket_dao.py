# dal/ticket_dao.py
from config.database import DatabaseConnection

class TicketDAO:
    def book_ticket(self, flight_id, customer_id, seat_id, voucher_id, base_price, final_price, pay_method):
        conn = DatabaseConnection.get_connection()
        if not conn:
            return -1 # Lỗi kết nối
            
        cursor = conn.cursor()
        ticket_id = -1
        try:
            # Gọi Stored Procedure (OUT parameter được xử lý bằng biến session trong MySQL)
            args = (flight_id, customer_id, seat_id, voucher_id, base_price, final_price, pay_method, 0)
            result_args = cursor.callproc('book_ticket', args)
            
            # Tham số OUT là tham số cuối cùng (index 7)
            ticket_id = result_args[7]
            
            # Commit transaction nếu procedure không tự commit
            conn.commit()
        except Exception as e:
            print(f"Lỗi DAL - book_ticket: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close() # Trả về pool
            
        return ticket_id