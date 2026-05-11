# dal/auth_repository.py
import json
from mysql.connector import Error
from config.database import DatabaseConnection

class AuthRepository:
    def get_all_face_encodings(self):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, username, role, face_encoding FROM Users WHERE face_encoding IS NOT NULL")
            return cursor.fetchall()
        finally:
            if conn: conn.close()

    def save_face_encoding(self, user_id, encoding_list):
        conn = DatabaseConnection.get_connection()
        try:
            cursor = conn.cursor()
            encoding_json = json.dumps(encoding_list)
            cursor.execute("UPDATE Users SET face_encoding = %s WHERE user_id = %s", (encoding_json, user_id))
            conn.commit()
            return True
        except Error: return False
        finally:
            if conn: conn.close()