# dal/seat_repository.py
from mysql.connector import Error
from config.database import DatabaseConnection

class SeatRepository:
    def hold_seat(self, seat_id):
        """Khóa ghế chống Double Booking và set Timer 5 phút"""
        conn = DatabaseConnection.get_connection()
        try:
            conn.start_transaction()
            cursor = conn.cursor()
            
            # Khóa ghế
            cursor.execute("SELECT seat_status FROM Seats WHERE seat_id = %s FOR UPDATE", (seat_id,))
            seat = cursor.fetchone()
            
            if not seat or seat[0] != 'AVAILABLE':
                conn.rollback()
                return False, "Ghế đã bị người khác đặt hoặc đang được giữ!"

            # Đổi trạng thái sang HELD và hẹn giờ 5 phút
            cursor.execute("""
                UPDATE Seats 
                SET seat_status = 'HELD', hold_expired_at = DATE_ADD(NOW(), INTERVAL 5 MINUTE) 
                WHERE seat_id = %s
            """, (seat_id,))
            
            conn.commit()
            return True, "Giữ ghế thành công!"
        except Error as e:
            conn.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {e}"
        finally:
            if conn: conn.close()

    def release_expired_holds(self):
        """Trả lại ghế nếu quá 5 phút không thanh toán"""
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            
            # Cập nhật các ghế HELD quá hạn thành AVAILABLE
            cursor.execute("""
                UPDATE Seats 
                SET seat_status = 'AVAILABLE', hold_expired_at = NULL 
                WHERE seat_status = 'HELD' AND hold_expired_at < NOW()
            """)
            conn.commit()
            return cursor.rowcount # Trả về số lượng ghế
        except Error:
            return 0
        finally:
            if conn: conn.close()