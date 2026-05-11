# bll/hold_service.py
from dal.seat_repository import SeatRepository
from PyQt6.QtCore import QTimer

class SeatHoldService:
    def __init__(self):
        self.seat_repo = SeatRepository()

    def hold_seat(self, seat_id):
        return self.seat_repo.hold_seat(seat_id)

class SeatHoldCleanerWorker:
    """Chạy nền mỗi 30s để nhả ghế hết hạn"""
    def __init__(self):
        self.repo = SeatRepository()
        self.timer = QTimer()
        self.timer.timeout.connect(self.clean_expired_holds)
        self.timer.start(30000) # 30s/lần

    def clean_expired_holds(self):
        released = self.repo.release_expired_holds()
        if released > 0:
            print(f"[Hệ thống] Đã tự động nhả {released} ghế hết thời gian giữ chỗ.")