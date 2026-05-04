# dal/user_dao.py
from config.database import DatabaseConnection

class UserDAO:
    def verify_login(self, username, hashed_pw):
        conn = DatabaseConnection.get_connection()
        if not conn: return None
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT user_id, username, role FROM Users WHERE username = %s AND password_hash = %s"
            cursor.execute(query, (username, hashed_pw))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def add_user(self, username, hashed_pw, role='GUEST'):
        """Đăng ký mặc định là GUEST"""
        conn = DatabaseConnection.get_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            query = "INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, hashed_pw, role))
            conn.commit()
            return True
        except Exception: 
            return False
        finally:
            if conn: conn.close()
            
    def get_user_by_id(self, user_id):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
        finally:
            if conn: conn.close()

    def update_password(self, user_id, new_hashed_pw):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE Users SET password_hash = %s WHERE user_id = %s", (new_hashed_pw, user_id))
            conn.commit()
            return True
        except Exception: 
            return False
        finally:
            if conn: conn.close()