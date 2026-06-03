# models/ticket_model.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Customer:
    customer_id: Optional[int]
    full_name: str
    phone: str
    id_card: str
    email: Optional[str] = ""

@dataclass
class Ticket:
    ticket_id: Optional[int]
    ticket_code: str
    flight_id: int
    customer_id: int
    seat_id: int
    payment_id: Optional[int]
    voucher_id: Optional[int]
    base_price: float
    final_price: float
    status: str 
    created_at: Optional[datetime] = None

@dataclass
class Flight:
    flight_id: int
    flight_number: str
    departure_time: datetime
    arrival_time: datetime
    dep_city: str
    arr_city: str
    base_price: float
    available_seats: int

@dataclass
class Seat:
    seat_id: int
    seat_number: str
    seat_status: str
    class_id: int
    class_name: str
    price_multiplier: float