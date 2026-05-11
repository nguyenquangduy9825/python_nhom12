# models/flight.py
class Flight:
    def __init__(self, flight_id, flight_number, departure_code, arrival_code, departure_time, arrival_time, status):
        self.flight_id = flight_id
        self.flight_number = flight_number
        self.departure_code = departure_code  # VD: 'HAN'
        self.arrival_code = arrival_code      # VD: 'SGN'
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.status = status                  # 'PENDING', 'DEPARTED', 'CANCELLED'