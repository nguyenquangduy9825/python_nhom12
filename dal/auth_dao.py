# dal/auth_dao.py
from config.database import DatabaseConnection
from mysql.connector import Error

class AuthDAO:
    def get_user(self, username):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    # --- HÀM MỚI BỔ SUNG ĐỂ ĐỔI MẬT KHẨU ---
    def get_user_by_id(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def create_user(self, username, hashed_pw, role, customer_id=None):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Users (username, password_hash, role, customer_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (username, hashed_pw, role, customer_id))
            conn.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Lỗi DB create_user: {e}")
            return None
        finally:
            if conn: conn.close()

    def update_password(self, username, new_hashed_pw):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET password_hash = %s WHERE username = %s", (new_hashed_pw, username))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()

    # --- HÀM MỚI BỔ SUNG ĐỂ ĐỔI MẬT KHẨU ---
    def update_password_by_id(self, user_id, new_hashed_pw):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET password_hash = %s WHERE user_id = %s", (new_hashed_pw, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if conn: conn.close()

class OtpDAO:
    def save_otp(self, identifier, otp_code, expiry_time):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            query = "INSERT INTO OTPs (identifier, otp_code, expiry_time) VALUES (%s, %s, %s)"
            cursor.execute(query, (identifier, otp_code, expiry_time))
            conn.commit()
            return True
        finally:
            if conn: conn.close()

    def get_valid_otp(self, identifier, otp_code):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT * FROM OTPs 
                WHERE identifier = %s AND otp_code = %s AND is_used = FALSE AND expiry_time > NOW()
                ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query, (identifier, otp_code))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def mark_otp_used(self, otp_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE OTPs SET is_used = TRUE WHERE otp_id = %s", (otp_id,))
            conn.commit()
        finally:
            if conn: conn.close()