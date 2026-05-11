DROP DATABASE IF EXISTS quanly_banve_pro;
CREATE DATABASE quanly_banve_pro;
USE quanly_banve_pro;

# Tạo các bảng
CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20) NOT NULL,
    id_card VARCHAR(20) NOT NULL
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
    status ENUM('PENDING', 'DEPARTED', 'CANCELLED') DEFAULT 'PENDING',
    FOREIGN KEY (departure_code) REFERENCES Airports(airport_code),
    FOREIGN KEY (arrival_code) REFERENCES Airports(airport_code)
);

CREATE TABLE SeatClasses (
    class_id INT AUTO_INCREMENT PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL UNIQUE, 
    price_multiplier DECIMAL(5,2) DEFAULT 1.00
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

CREATE TABLE Tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    customer_id INT NOT NULL,
    seat_id INT NOT NULL UNIQUE,
    payment_id INT NULL,
    voucher_id INT NULL,
    base_price DECIMAL(15,2) NOT NULL,
    final_price DECIMAL(15,2) NOT NULL,
    status ENUM('BOOKED', 'HELD', 'CANCELLED') DEFAULT 'BOOKED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id),
    FOREIGN KEY (payment_id) REFERENCES Payments(payment_id),
    FOREIGN KEY (voucher_id) REFERENCES Vouchers(voucher_id)
);

-- Cập nhật thêm các bảng mới
-- Bảng Thẻ lên máy bay / Thông tin tra cứu vé (Lưu Mã Tra Cứu và QR Code)
CREATE TABLE BoardingPasses (
    pass_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT UNIQUE NOT NULL,
    booking_code VARCHAR(20) UNIQUE NOT NULL,  -- Mã tra cứu vé (PNR)
    qr_code_text TEXT NOT NULL,                -- Dữ liệu mã QR
    gate VARCHAR(10) NULL,                     -- Cổng ra máy bay (Điền sau)
    boarding_time DATETIME NULL,               -- Giờ có mặt lên máy bay
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id) ON DELETE CASCADE
);

-- Bảng Gói hành lý mua thêm
CREATE TABLE BaggagePackages (
    baggage_id INT AUTO_INCREMENT PRIMARY KEY,
    weight_kg INT NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    description VARCHAR(255)
);

-- Bảng Khách hàng mua thêm Hành lý (Nối Ticket và Baggage)
CREATE TABLE TicketBaggage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    baggage_id INT NOT NULL,
    quantity INT DEFAULT 1,
    FOREIGN KEY (ticket_id) REFERENCES Tickets(ticket_id) ON DELETE CASCADE,
    FOREIGN KEY (baggage_id) REFERENCES BaggagePackages(baggage_id)
);

-- Bảng Hệ thống Thông báo cho khách hàng
CREATE TABLE Notifications (
    notify_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);


-- Trigger
DELIMITER //

-- Trigger cũ: Cập nhật ghế và voucher
CREATE TRIGGER trg_after_ticket_insert
AFTER INSERT ON Tickets
FOR EACH ROW
BEGIN
    UPDATE Seats SET is_booked = TRUE, seat_status = NEW.status WHERE seat_id = NEW.seat_id;
    IF NEW.voucher_id IS NOT NULL THEN
        UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = NEW.voucher_id;
    END IF;
END //

-- Trigger mới: Tự động phát hành Mã tra cứu và Mã QR khi có vé mới được đặt
CREATE TRIGGER trg_generate_boarding_pass
AFTER INSERT ON Tickets
FOR EACH ROW
BEGIN
    DECLARE v_booking_code VARCHAR(20);
    DECLARE v_qr_text TEXT;
    
    -- Sinh mã code ngẫu nhiên gồm 6 ký tự chữ số + ID Vé
    SET v_booking_code = CONCAT(SUBSTRING(MD5(RAND()), 1, 6), NEW.ticket_id);
    SET v_qr_text = CONCAT('{"ticket_id":', NEW.ticket_id, ',"booking_code":"', UPPER(v_booking_code), '"}');
    
    -- Tạo sẵn Boarding Pass rỗng
    INSERT INTO BoardingPasses (ticket_id, booking_code, qr_code_text) 
    VALUES (NEW.ticket_id, UPPER(v_booking_code), v_qr_text);
END //

-- Trigger cũ: Nhả ghế khi hủy vé
CREATE TRIGGER trg_after_ticket_update_cancel
AFTER UPDATE ON Tickets
FOR EACH ROW
BEGIN
    IF NEW.status = 'CANCELLED' AND OLD.status != 'CANCELLED' THEN
        UPDATE Seats SET is_booked = FALSE, seat_status = 'AVAILABLE', hold_expired_at = NULL WHERE seat_id = NEW.seat_id;
    END IF;
END //
DELIMITER ;

-- Mock data để test
INSERT INTO Users (username, password_hash, role) VALUES 
('admin123', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'ADMIN');

INSERT INTO Airports (airport_code, name, city, country) VALUES
('HAN', 'Nội Bài', 'Hà Nội', 'Việt Nam'), ('SGN', 'Tân Sơn Nhất', 'Hồ Chí Minh', 'Việt Nam'),
('DAD', 'Đà Nẵng', 'Đà Nẵng', 'Việt Nam'), ('PQC', 'Phú Quốc', 'Kiên Giang', 'Việt Nam');

INSERT INTO SeatClasses (class_id, class_name, price_multiplier) VALUES
(1, 'ECONOMY', 1.00), (2, 'BUSINESS', 2.50);

INSERT INTO Vouchers (code, discount_percent, max_discount, usage_limit, used_count, expiry_date) VALUES
('SUMMER2026', 10.00, 500000.00, 100, 0, '2026-12-31 23:59:59');

INSERT INTO BaggagePackages (weight_kg, price, description) VALUES 
(15, 250000, 'Gói hành lý ký gửi cơ bản 15kg'),
(25, 400000, 'Gói hành lý ký gửi tiêu chuẩn 25kg');

INSERT INTO Flights (flight_id, flight_number, departure_code, arrival_code, departure_time, arrival_time, status) VALUES
(1, 'VN123', 'HAN', 'SGN', '2026-05-15 08:00:00', '2026-05-15 10:00:00', 'PENDING'),
(2, 'VJ456', 'SGN', 'DAD', '2026-05-16 14:00:00', '2026-05-16 15:30:00', 'PENDING');

-- Sinh ghế cho VN123
INSERT INTO Seats (flight_id, seat_number, class_id) VALUES
(1, 'A1', 2), (1, 'A2', 2), (1, 'A3', 2), (1, 'A4', 2),
(1, 'B1', 1), (1, 'B2', 1), (1, 'B3', 1), (1, 'B4', 1);

-- Khách hàng thực tế
INSERT INTO Customers (customer_id, full_name, phone, id_card) VALUES 
(1, 'Nguyễn Quốc Khánh', '0987654321', '0192837465'),
(2, 'Trần Nóc Nhà', '0912345678', '0987654321');

-- Giao dịch 1: Khách hàng thanh toán VNPAY (Ghế A1 - BUSINESS)
INSERT INTO Payments (payment_id, method, amount, status, transaction_code) VALUES (1, 'VNPAY', 3750000, 'COMPLETED', 'VNPAY-XYZ123');
-- Khi insert lệnh Tickets dưới đây, Trigger trg_generate_boarding_pass sẽ TỰ ĐỘNG chạy và sinh QR Code
INSERT INTO Tickets (flight_id, customer_id, seat_id, payment_id, base_price, final_price, status) VALUES 
(1, 1, 1, 1, 3750000, 3750000, 'BOOKED');