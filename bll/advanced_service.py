# bll/advanced_service.py
from dal.advanced_repositories import SeatClassRepository, FlightOperationsRepository

class AdvancedService:
    def __init__(self):
        self.seat_class_repo = SeatClassRepository()
        self.flight_ops_repo = FlightOperationsRepository()

    def get_all_seat_classes(self):
        return self.seat_class_repo.get_all()

    def create_seat_class(self, name, multiplier):
        try:
            mult_val = float(multiplier)
        except ValueError:
            return False, "Hệ số giá phải là một số hợp lệ!"
        if self.seat_class_repo.create(name, mult_val):
            return True, "Thêm hạng vé thành công!"
        return False, "Lỗi cập nhật CSDL!"

    def get_flights_for_combobox(self):
        return self.flight_ops_repo.get_flights_for_combobox()

    def get_tickets_by_flight(self, flight_id):
        if not flight_id: return []
        return self.flight_ops_repo.get_flight_ticket_list(flight_id)

    def get_seat_map(self, flight_id):
        if not flight_id: return []
        return self.flight_ops_repo.get_flight_seat_map(flight_id)