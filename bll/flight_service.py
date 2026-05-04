# bll/flight_service.py
from dal.flight_dao import FlightDAO

class FlightService:
    def __init__(self):
        self.flight_dao = FlightDAO()
        
    def get_available_flights(self, dep_code, arr_code, flight_date):
        # Có thể thêm logic kiểm tra dữ liệu đầu vào ở đây
        if dep_code == arr_code:
            raise ValueError("Điểm xuất phát và điểm đến không được trùng nhau!")
            
        # Gọi DAL để lấy dữ liệu
        flights = self.flight_dao.search_flights(dep_code, arr_code, flight_date)
        
        # Có thể thêm logic tính toán giá tiền cơ bản ở đây trước khi đẩy lên GUI
        return flights