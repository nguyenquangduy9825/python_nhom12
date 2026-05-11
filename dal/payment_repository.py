# dal/payment_repository.py
from mysql.connector import Error
from config.database import DatabaseConnection
import uuid

class PaymentRepository:
    def create_payment_transaction(self, info, method):
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()

            # Kiểm tra trạng thái ghế
            cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (info['seat_id'],))
            seat = cursor.fetchone()
            if not seat or seat[0] != 'HELD':
                conn.rollback()
                return False, "Ghế đã hết thời gian giữ chỗ. Vui lòng chọn lại!"

            # Sinh mã giao dịch
            trans_code = f"{method}-{uuid.uuid4().hex[:8].upper()}"

            # Insert Ticket
            query_ticket = """
                INSERT INTO Tickets (flight_id, customer_id, seat_id, voucher_id, ticket_class, 
                                     base_price, discount_amount, final_price, payment_status, ticket_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PAID', 'BOOKED')
            """
            cursor.execute(query_ticket, (
                info['flight_id'], info['customer_id'], info['seat_id'], info.get('voucher_id'),
                info['ticket_class'], info['base_price'], info['discount_amount'], info['final_price']
            ))
            ticket_id = cursor.lastrowid

            # Insert Payment
            query_pay = """
                INSERT INTO Payments (ticket_id, payment_method, amount, payment_status, transaction_code)
                VALUES (%s, %s, %s, 'PAID', %s)
            """
            cursor.execute(query_pay, (ticket_id, method, info['final_price'], trans_code))

            # Khóa trạng thái ghế
            cursor.execute("UPDATE Seats SET seat_status = 'BOOKED', hold_expired_at = NULL WHERE seat_id = %s", (info['seat_id'],))

            conn.commit()
            return True, trans_code
        except Error as e:
            conn.rollback()
            return False, str(e)
        finally:
            if conn: conn.close()