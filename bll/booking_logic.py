# bll/booking_logic.py

class BookingLogic:
    def __init__(self):
        # MÔ PHỎNG DATABASE (MOCK DB)
        self.flights = [
            {"id": 1, "code": "VN123", "dep": "HAN", "dest": "SGN", "date": "2026-05-05", "time": "08:00", "status": "Đang mở bán"},
            {"id": 2, "code": "VJ456", "dep": "HAN", "dest": "DAD", "date": "2026-05-05", "time": "14:00", "status": "Đang mở bán"},
            {"id": 3, "code": "QH789", "dep": "SGN", "dest": "HAN", "date": "2026-05-05", "time": "19:30", "status": "Hết vé"}
        ]
        
        self.seats = {
            1: [
                {"id": 101, "class": "Economy", "name": "12A", "price": 1500000},
                {"id": 102, "class": "Economy", "name": "12B", "price": 1500000},
                {"id": 103, "class": "Business", "name": "02A", "price": 3500000}
            ],
            2: [{"id": 201, "class": "Economy", "name": "15C", "price": 1200000}],
            3: [] # Mô phỏng chuyến bay đã hết ghế
        }

        self.vouchers = {"VIP20": 200000, "SALE50": 50000}

    def get_all_active_flights(self):
        return [f for f in self.flights if f["status"] == "Đang mở bán"]

    def search_flights(self, dep, dest, date_str):
        # Lọc chuyến bay theo tiêu chí
        results = [f for f in self.flights if f["dep"] == dep and f["dest"] == dest and f["date"] == date_str]
        
        # Ánh xạ thêm tình trạng ghế (Còn / Hết)
        for f in results:
            available_seats = len(self.seats.get(f["id"], []))
            f["seat_status"] = "Còn vé" if available_seats > 0 else "Hết vé"
        return results

    def get_seats_by_flight(self, flight_id, seat_class):
        seats = self.seats.get(flight_id, [])
        return [s for s in seats if s["class"] == seat_class]

    def validate_voucher(self, code):
        return self.vouchers.get(code.upper(), 0)