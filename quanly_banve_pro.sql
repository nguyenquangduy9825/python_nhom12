DROP DATABASE IF EXISTS quanly_banve_pro;
CREATE DATABASE quanly_banve_pro;
USE quanly_banve_pro;

-- Tạo các bảng
CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20) NOT NULL,
    id_card VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    face_encoding LONGTEXT NULL,
    role ENUM('ADMIN', 'STAFF', 'USER') DEFAULT 'USER',
    customer_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE SET NULL
);

CREATE TABLE Airports (
    airport_code CHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

CREATE TABLE Flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(20) UNIQUE NOT NULL,
    departure_code CHAR(3) NOT NULL,
    arrival_code CHAR(3) NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    base_price DECIMAL(15,2) DEFAULT 1500000.00,
    status ENUM('PENDING', 'DEPARTED', 'CANCELLED') DEFAULT 'PENDING',
    FOREIGN KEY (departure_code) REFERENCES Airports(airport_code),
    FOREIGN KEY (arrival_code) REFERENCES Airports(airport_code)
);

CREATE TABLE SeatClasses (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL UNIQUE, 
    price_multiplier DECIMAL(5,2) DEFAULT 1.00,
    description VARCHAR(255) NULL
);

CREATE TABLE Seats (
    seat_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    class_id INT NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    seat_status ENUM('AVAILABLE', 'BOOKED', 'HELD') DEFAULT 'AVAILABLE',
    hold_expired_at DATETIME NULL,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES SeatClasses(class_id)
);

CREATE TABLE Vouchers (
    voucher_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    discount_percent DECIMAL(5,2) NOT NULL,
    max_discount DECIMAL(10,2),
    usage_limit INT NOT NULL,
    used_count INT DEFAULT 0,
    expiry_date DATETIME NOT NULL
);

CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    method ENUM('CASH', 'CREDIT_CARD', 'BANK_TRANSFER', 'MOMO', 'VNPAY') NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    status ENUM('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED') DEFAULT 'PENDING',
    transaction_code VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Booking_Groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_code VARCHAR(30) UNIQUE NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(100),
    total_members INT DEFAULT 1,
    status ENUM('ACTIVE', 'CANCELLED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_code VARCHAR(20) UNIQUE NOT NULL, 
    flight_id INT NOT NULL,
    customer_id INT NOT NULL,
    group_id INT NULL,
    seat_id INT NOT NULL UNIQUE,
    payment_id INT NULL,
    voucher_id INT NULL,
    base_price DECIMAL(15,2) NOT NULL, -- Giá lúc mua (Lưu lịch sử, chuẩn 3NF ngữ cảnh hóa đơn)
    final_price DECIMAL(15,2) NOT NULL,
    status ENUM('BOOKED', 'HELD', 'CANCELLED') DEFAULT 'BOOKED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (group_id) REFERENCES BookingGroups(group_id) ON DELETE SET NULL,
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id),
    FOREIGN KEY (payment_id) REFERENCES Payments(payment_id),
    FOREIGN KEY (voucher_id) REFERENCES Vouchers(voucher_id)
);

CREATE TABLE BoardingPasses (
    pass_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT UNIQUE NOT NULL,
    booking_code VARCHAR(20) UNIQUE NOT NULL,
    qr_code_text TEXT NOT NULL,
    gate VARCHAR(10) NULL,
    boarding_time DATETIME NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id) ON DELETE CASCADE
);

-- Tạo các index giúp tối ưu tốc độ tra cứu
-- Tối ưu tra cứu khách hàng nhanh
CREATE INDEX idx_customers_phone ON Customers(phone);
CREATE INDEX idx_customers_idcard ON Customers(id_card);

-- Tối ưu lọc danh sách chuyến bay (Thường tìm theo ngày bay và trạng thái)
CREATE INDEX idx_flights_departure ON Flights(departure_time);
CREATE INDEX idx_flights_status ON Flights(status);

-- Tối ưu tải sơ đồ ghế (Truy vấn theo chuyến bay rất nhiều)
CREATE INDEX idx_seats_flight ON Seats(flight_id);
CREATE INDEX idx_seats_status ON Seats(seat_status);

-- Tối ưu tra cứu mã PNR và kiểm tra vé của khách
CREATE INDEX idx_tickets_code ON Tickets(ticket_code);
CREATE INDEX idx_tickets_customer ON Tickets(customer_id);

-- Tạo các view 
-- View 1: Danh sách chuyến bay kèm số ghế trống và tên thành phố (DAL khỏi JOIN)
CREATE VIEW vw_Flight_Search AS
SELECT 
    f.flight_id, f.flight_number, f.base_price, f.status,
    f.departure_time, f.arrival_time,
    dep.city AS dep_city, arr.city AS arr_city,
    (SELECT COUNT(*) FROM Seats s WHERE s.flight_id = f.flight_id AND s.seat_status = 'AVAILABLE') AS available_seats
FROM Flights f
JOIN Airports dep ON f.departure_code = dep.airport_code
JOIN Airports arr ON f.arrival_code = arr.airport_code;

-- View 2: Chi tiết vé (Phục vụ khách hàng tra cứu mã PNR và SĐT)
CREATE VIEW vw_Ticket_Details AS
SELECT 
    t.ticket_id, t.ticket_code, t.final_price, t.status AS ticket_status, t.created_at,
    c.full_name, c.phone, c.id_card,
    f.flight_number, f.departure_time, f.arrival_time,
    dep.city AS dep_city, arr.city AS arr_city,
    s.seat_number, sc.class_name
FROM Tickets t
JOIN Customers c ON t.customer_id = c.customer_id
JOIN Flights f ON t.flight_id = f.flight_id
JOIN Airports dep ON f.departure_code = dep.airport_code
JOIN Airports arr ON f.arrival_code = arr.airport_code
JOIN Seats s ON t.seat_id = s.seat_id
JOIN SeatClasses sc ON s.class_id = sc.class_id;

-- View 3: Dashboard Thống kê cho Admin (Tính doanh thu và số lượng vé bán ra)
CREATE VIEW vw_Dashboard_Stats AS
SELECT 
    DATE(t.created_at) AS sale_date,
    COUNT(t.ticket_id) AS total_tickets_sold,
    SUM(t.final_price) AS total_revenue
FROM Tickets t
WHERE t.status = 'BOOKED'
GROUP BY DATE(t.created_at);

-- Mock Data để test UI 
INSERT INTO Airports (airport_code, name, city, country) VALUES
('HAN', 'Nội Bài', 'Hà Nội', 'Việt Nam'), 
('SGN', 'Tân Sơn Nhất', 'Hồ Chí Minh', 'Việt Nam');

INSERT INTO SeatClasses (class_name, price_multiplier, description) VALUES
('ECONOMY', 1.00, 'Hạng phổ thông tiêu chuẩn'), 
('BUSINESS', 2.50, 'Hạng thương gia cao cấp');

INSERT INTO Flights (flight_number, departure_code, arrival_code, departure_time, arrival_time, base_price, status) VALUES
('VN123', 'HAN', 'SGN', '2026-05-15 08:00:00', '2026-05-15 10:00:00', 1500000.00, 'PENDING');

-- Insert 2 ghế mẫu
INSERT INTO Seats (flight_id, seat_number, class_id) VALUES
(1, 'A1', 2), (1, 'B1', 1);