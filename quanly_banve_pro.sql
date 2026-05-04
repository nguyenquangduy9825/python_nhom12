CREATE DATABASE IF NOT EXISTS quanly_banve_pro;
USE quanly_banve_pro;

-- Bảng Users (Quản trị & Phân quyền)
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    face_encoding JSON,
    role ENUM('ADMIN', 'STAFF', 'GUEST', 'USER') DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Airports (Sân bay)
CREATE TABLE Airports (
    airport_code CHAR(3) PRIMARY KEY, -- VD: HAN, SGN
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- Bảng Flights (Chuyến bay)
CREATE TABLE Flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(20) UNIQUE NOT NULL,
    departure_code CHAR(3) NOT NULL,
    arrival_code CHAR(3) NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    status ENUM('PENDING', 'DEPARTED', 'CANCELLED') DEFAULT 'PENDING',
    FOREIGN KEY (departure_code) REFERENCES Airports(airport_code),
    FOREIGN KEY (arrival_code) REFERENCES Airports(airport_code)
);

-- Bảng SeatClasses (Hạng ghế)
CREATE TABLE SeatClasses (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL, -- ECONOMY, BUSINESS, FIRST CLASS
    price_multiplier DECIMAL(5,2) DEFAULT 1.00
);

-- Bảng Seats (Ghế ngồi)
CREATE TABLE Seats (
    seat_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    class_id INT NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES SeatClasses(class_id)
);

-- Bảng Customers (Khách hàng)
CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE NOT NULL,
    id_card VARCHAR(20) UNIQUE NOT NULL
);

-- Bảng Vouchers (Mã giảm giá)
CREATE TABLE Vouchers (
    voucher_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    discount_percent DECIMAL(5,2) NOT NULL,
    max_discount DECIMAL(10,2),
    usage_limit INT NOT NULL,
    used_count INT DEFAULT 0,
    expiry_date DATETIME NOT NULL
);

-- Bảng Payments (Thanh toán)
CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    method ENUM('CASH', 'CREDIT_CARD', 'BANK_TRANSFER') NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    status ENUM('PENDING', 'COMPLETED', 'REFUNDED') DEFAULT 'PENDING',
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Tickets (Vé máy bay)
CREATE TABLE Tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    customer_id INT NOT NULL,
    seat_id INT NOT NULL UNIQUE, -- 1 ghế chỉ thuộc về 1 vé tại 1 thời điểm
    payment_id INT,
    voucher_id INT NULL,
    base_price DECIMAL(15,2) NOT NULL,
    final_price DECIMAL(15,2) NOT NULL,
    status ENUM('BOOKED', 'HELD', 'CANCELLED') DEFAULT 'BOOKED',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id),
    FOREIGN KEY (payment_id) REFERENCES Payments(payment_id),
    FOREIGN KEY (voucher_id) REFERENCES Vouchers(voucher_id)
);


CREATE INDEX idx_flight_search ON Flights(departure_code, arrival_code, departure_time);
CREATE INDEX idx_customer_phone ON Customers(phone);
CREATE INDEX idx_customer_id_card ON Customers(id_card);
CREATE INDEX idx_voucher_code ON Vouchers(code);

DELIMITER //

-- Khi đặt vé thành công sẽ Khóa ghế và Tăng lượt dùng voucher
CREATE TRIGGER after_ticket_insert
AFTER INSERT ON Tickets
FOR EACH ROW
BEGIN
    UPDATE Seats SET is_booked = TRUE WHERE seat_id = NEW.seat_id;
    IF NEW.voucher_id IS NOT NULL THEN
        UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = NEW.voucher_id;
    END IF;
END //

-- Khi hủy vé thì Nhả ghế trống
CREATE TRIGGER after_ticket_update_cancel
AFTER UPDATE ON Tickets
FOR EACH ROW
BEGIN
    IF NEW.status = 'CANCELLED' AND OLD.status != 'CANCELLED' THEN
        UPDATE Seats SET is_booked = FALSE WHERE seat_id = NEW.seat_id;
    END IF;
END //

-- Procedure Tìm chuyến bay
CREATE PROCEDURE search_flights(
    IN p_dep_code CHAR(3), 
    IN p_arr_code CHAR(3), 
    IN p_date DATE
)
BEGIN
    SELECT f.flight_number, f.departure_time, f.arrival_time, f.status,
           a1.city AS dep_city, a2.city AS arr_city
    FROM Flights f
    JOIN Airports a1 ON f.departure_code = a1.airport_code
    JOIN Airports a2 ON f.arrival_code = a2.airport_code
    WHERE f.departure_code = p_dep_code 
      AND f.arrival_code = p_arr_code 
      AND DATE(f.departure_time) = p_date
      AND f.status = 'PENDING';
END //

-- Procedure Đặt vé an toàn
CREATE PROCEDURE book_ticket(
    IN p_flight_id INT,
    IN p_customer_id INT,
    IN p_seat_id INT,
    IN p_voucher_id INT,
    IN p_base_price DECIMAL(15,2),
    IN p_final_price DECIMAL(15,2),
    IN p_pay_method VARCHAR(20),
    OUT p_ticket_id INT
)
BEGIN
    DECLARE v_is_booked BOOLEAN;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK;
        SET p_ticket_id = -1;
    END;

    START TRANSACTION;
    SELECT is_booked INTO v_is_booked FROM Seats WHERE seat_id = p_seat_id FOR UPDATE;
    
    IF v_is_booked = TRUE THEN
        ROLLBACK;
        SET p_ticket_id = -2; 
    ELSE
        INSERT INTO Payments (method, amount, status) 
        VALUES (p_pay_method, p_final_price, 'COMPLETED');
        SET @new_pay_id = LAST_INSERT_ID();
        
        INSERT INTO Tickets (flight_id, customer_id, seat_id, payment_id, voucher_id, base_price, final_price, status)
        VALUES (p_flight_id, p_customer_id, p_seat_id, @new_pay_id, p_voucher_id, p_base_price, p_final_price, 'BOOKED');
        SET p_ticket_id = LAST_INSERT_ID();
        
        COMMIT;
    END IF;
END //

DELIMITER ;

-- Users
INSERT INTO Users (username, password_hash, role) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'ADMIN'),
('staff1', '6ccb4b7c39a6e77f76ecfa935a855c6c46ad5611', 'STAFF');

-- Sân bay
INSERT INTO Airports (airport_code, name, city, country) VALUES
('HAN', 'Nội Bài', 'Hà Nội', 'Việt Nam'),
('SGN', 'Tân Sơn Nhất', 'Hồ Chí Minh', 'Việt Nam'),
('DAD', 'Đà Nẵng', 'Đà Nẵng', 'Việt Nam');

-- Hạng ghế
INSERT INTO SeatClasses (class_name, price_multiplier) VALUES
('ECONOMY', 1.00),
('BUSINESS', 2.00);

-- Chuyến bay
INSERT INTO Flights (flight_number, departure_code, arrival_code, departure_time, arrival_time, status) VALUES
('VN123', 'HAN', 'SGN', '2026-05-01 08:00:00', '2026-05-01 10:00:00', 'PENDING'),
('VJ456', 'SGN', 'DAD', '2026-05-02 14:00:00', '2026-05-02 15:30:00', 'PENDING');

-- Ghế ngồi
INSERT INTO Seats (flight_id, seat_number, class_id, is_booked) VALUES
(1, 'A1', 2, FALSE), 
(1, 'A2', 2, FALSE), 
(1, 'B1', 1, FALSE), 
(1, 'B2', 1, FALSE); 

-- Khách hàng
INSERT INTO Customers (full_name, email, phone, id_card) VALUES
('Nguyễn Văn A', 'nva@gmail.com', '0901234567', '001090123456'),
('Trần Thị B', 'ttb@gmail.com', '0912345678', '002091234567');

-- Voucher
INSERT INTO Vouchers (code, discount_percent, max_discount, usage_limit, used_count, expiry_date) VALUES
('SUMMER26', 10.00, 500000.00, 100, 0, '2026-12-31 23:59:59'),
('VIP20', 20.00, 1000000.00, 50, 0, '2026-12-31 23:59:59');
USE quanly_banve_pro;

-- Thêm các Sân bay mới
INSERT IGNORE INTO Airports (airport_code, name, city, country) VALUES
('PQC', 'Sân bay Phú Quốc', 'Kiên Giang', 'Việt Nam'),
('CXR', 'Sân bay Cam Ranh', 'Khánh Hòa', 'Việt Nam');

-- Thêm 4 chuyến bay với các khung giờ khác nhau
INSERT INTO Flights (flight_number, departure_code, arrival_code, departure_time, arrival_time, status) VALUES
('VN999', 'HAN', 'PQC', '2026-05-05 07:30:00', '2026-05-05 09:45:00', 'PENDING'),
('VJ888', 'SGN', 'HAN', '2026-05-05 15:00:00', '2026-05-05 17:10:00', 'PENDING'),
('QH777', 'HAN', 'DAD', '2026-05-06 10:00:00', '2026-05-06 11:20:00', 'PENDING'),
('VN555', 'DAD', 'CXR', '2026-05-07 14:00:00', '2026-05-07 15:15:00', 'PENDING');

-- Tạo sơ đồ ghế
-- Chuyến VN999 (Hà Nội -> Phú Quốc)
SET @f_vn999 = (SELECT flight_id FROM Flights WHERE flight_number = 'VN999' LIMIT 1);
INSERT INTO Seats (flight_id, seat_number, class_id, is_booked) VALUES
(@f_vn999, 'A1', 2, FALSE), (@f_vn999, 'A2', 2, FALSE), (@f_vn999, 'A3', 2, FALSE), -- Thương gia
(@f_vn999, 'B1', 1, FALSE), (@f_vn999, 'B2', 1, FALSE), (@f_vn999, 'B3', 1, FALSE), -- Phổ thông
(@f_vn999, 'B4', 1, FALSE), (@f_vn999, 'C1', 1, FALSE), (@f_vn999, 'C2', 1, FALSE);

-- Chuyến VJ888 (HCM -> Hà Nội)
SET @f_vj888 = (SELECT flight_id FROM Flights WHERE flight_number = 'VJ888' LIMIT 1);
INSERT INTO Seats (flight_id, seat_number, class_id, is_booked) VALUES
(@f_vj888, 'VIP1', 2, FALSE), (@f_vj888, 'VIP2', 2, FALSE), 
(@f_vj888, 'E1', 1, FALSE), (@f_vj888, 'E2', 1, FALSE), (@f_vj888, 'E3', 1, FALSE),
(@f_vj888, 'E4', 1, FALSE), (@f_vj888, 'E5', 1, FALSE), (@f_vj888, 'E6', 1, FALSE);

-- Chuyến QH777 (Hà Nội -> Đà Nẵng)
SET @f_qh777 = (SELECT flight_id FROM Flights WHERE flight_number = 'QH777' LIMIT 1);
INSERT INTO Seats (flight_id, seat_number, class_id, is_booked) VALUES
(@f_qh777, 'A1', 2, FALSE), (@f_qh777, 'B1', 1, FALSE), (@f_qh777, 'B2', 1, FALSE);

-- Thêm cột customer_id vào bảng Users
ALTER TABLE Users ADD COLUMN customer_id INT NULL;
ALTER TABLE Users ADD FOREIGN KEY (customer_id) REFERENCES Customers(customer_id);

-- Tạo bảng OTPs
CREATE TABLE OTPs (
    otp_id INT AUTO_INCREMENT PRIMARY KEY,
    identifier VARCHAR(100) NOT NULL, -- Email hoặc Username/Phone
    otp_code VARCHAR(6) NOT NULL,
    expiry_time DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);