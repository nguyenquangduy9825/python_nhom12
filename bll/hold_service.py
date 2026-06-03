# bll/hold_service.py
from PyQt6.QtCore import QThread
import time
from config.database import DatabaseConnection

class SeatHoldCleanerWorker(QThread):
    """Tiến trình chạy ngầm dọn dẹp các ghế hết hạn giữ chỗ"""
    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        while self.is_running:
            self.release_expired_holds()
            time.sleep(60) # Quét mỗi 1 phút

    def release_expired_holds(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            # Cập nhật trạng thái vé và nhả ghế khi quá 15 phút
            cursor.execute("""
                UPDATE Tickets t
                JOIN Seats s ON t.seat_id = s.seat_id
                SET t.status = 'CANCELLED', s.seat_status = 'AVAILABLE', s.hold_expired_at = NULL, s.is_booked = FALSE
                WHERE t.status = 'HELD' AND s.hold_expired_at IS NOT NULL AND s.hold_expired_at <= NOW()
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            if conn: conn.close()

    def stop(self):
        self.is_running = False