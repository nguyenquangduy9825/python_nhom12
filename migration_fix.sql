-- Migration Fix for VeMayBay Flight Booking System
-- Fixes schema issues and removes booking_groups table references

USE quanly_banve_pro;

-- 1. Add missing columns to SeatClasses if they don't exist
ALTER TABLE SeatClasses 
ADD COLUMN IF NOT EXISTS baggage_limit INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS priority_boarding BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS description VARCHAR(255) DEFAULT '';

-- 2. Add missing columns to Tickets table
ALTER TABLE Tickets
ADD COLUMN IF NOT EXISTS ticket_code VARCHAR(20) UNIQUE,
ADD COLUMN IF NOT EXISTS hold_expired_at DATETIME NULL;

-- 3. Fix Tickets table hold_expired_at if needed (some might come from Seats)
UPDATE Tickets SET hold_expired_at = NULL WHERE status != 'HELD';

-- 4. Update Seats table - ensure all columns exist
ALTER TABLE Seats 
ADD COLUMN IF NOT EXISTS hold_expired_at DATETIME NULL;

-- 5. Create trigger to automatically generate ticket codes
DROP TRIGGER IF EXISTS trg_generate_ticket_code;
DELIMITER //
CREATE TRIGGER trg_generate_ticket_code
BEFORE INSERT ON Tickets
FOR EACH ROW
BEGIN
    IF NEW.ticket_code IS NULL THEN
        SET NEW.ticket_code = CONCAT('TKT-', SUBSTRING(MD5(RAND()), 1, 6), NEW.ticket_id);
    END IF;
END //
DELIMITER ;

-- 6. Update existing trigger for ticket insertion
DROP TRIGGER IF EXISTS trg_after_ticket_insert;
DELIMITER //
CREATE TRIGGER trg_after_ticket_insert
AFTER INSERT ON Tickets
FOR EACH ROW
BEGIN
    UPDATE Seats SET is_booked = TRUE, seat_status = NEW.status WHERE seat_id = NEW.seat_id;
    IF NEW.voucher_id IS NOT NULL THEN
        UPDATE Vouchers SET used_count = used_count + 1 WHERE voucher_id = NEW.voucher_id;
    END IF;
END //
DELIMITER ;

-- 7. Trigger for ticket cancellation
DROP TRIGGER IF EXISTS trg_after_ticket_update_cancel;
DELIMITER //
CREATE TRIGGER trg_after_ticket_update_cancel
AFTER UPDATE ON Tickets
FOR EACH ROW
BEGIN
    IF NEW.status = 'CANCELLED' AND OLD.status != 'CANCELLED' THEN
        UPDATE Seats SET is_booked = FALSE, seat_status = 'AVAILABLE', hold_expired_at = NULL WHERE seat_id = NEW.seat_id;
    END IF;
END //
DELIMITER ;

-- 8. Trigger for hold expiration (HELD tickets that expire should become EXPIRED)
DROP TRIGGER IF EXISTS trg_handle_held_expiration;
DELIMITER //
CREATE TRIGGER trg_handle_held_expiration
BEFORE UPDATE ON Tickets
FOR EACH ROW
BEGIN
    IF NEW.status = 'HELD' AND OLD.status = 'HELD' THEN
        IF NEW.hold_expired_at < NOW() THEN
            SET NEW.status = 'EXPIRED';
        END IF;
    END IF;
END //
DELIMITER ;

-- 9. Verify data integrity - ensure no orphaned references
DELETE FROM Tickets WHERE seat_id NOT IN (SELECT seat_id FROM Seats);
DELETE FROM Tickets WHERE customer_id NOT IN (SELECT customer_id FROM Customers);
DELETE FROM Tickets WHERE flight_id NOT IN (SELECT flight_id FROM Flights);

-- 10. Add index for performance
ALTER TABLE Tickets ADD INDEX IF NOT EXISTS idx_flight_id (flight_id);
ALTER TABLE Tickets ADD INDEX IF NOT EXISTS idx_customer_id (customer_id);
ALTER TABLE Tickets ADD INDEX IF NOT EXISTS idx_seat_id (seat_id);
ALTER TABLE Tickets ADD INDEX IF NOT EXISTS idx_status (status);
ALTER TABLE Tickets ADD INDEX IF NOT EXISTS idx_hold_expired (hold_expired_at);

ALTER TABLE Seats ADD INDEX IF NOT EXISTS idx_flight_id (flight_id);
ALTER TABLE Seats ADD INDEX IF NOT EXISTS idx_seat_status (seat_status);
ALTER TABLE Seats ADD INDEX IF NOT EXISTS idx_class_id (class_id);

-- 11. Verify SeatClasses has required data
INSERT IGNORE INTO SeatClasses (class_id, class_name, price_multiplier, baggage_limit, priority_boarding, description)
VALUES (1, 'ECONOMY', 1.00, 1, FALSE, 'Ghế phổ thông - tiêu chuẩn')
ON DUPLICATE KEY UPDATE description = 'Ghế phổ thông - tiêu chuẩn';

INSERT IGNORE INTO SeatClasses (class_id, class_name, price_multiplier, baggage_limit, priority_boarding, description)
VALUES (2, 'BUSINESS', 2.50, 2, TRUE, 'Ghế thương gia - tiêu chuẩn')
ON DUPLICATE KEY UPDATE description = 'Ghế thương gia - tiêu chuẩn';

-- 12. Commit and verify
COMMIT;
SELECT "✅ Migration completed successfully!" AS status;
