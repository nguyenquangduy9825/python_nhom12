# config/database.py
import os
import mysql.connector
from mysql.connector import pooling
from mysql.connector import Error
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class DatabaseConnection:
    _pool = None

    @classmethod
    def initialize_pool(cls):
        if cls._pool is None:
            try:
                cls._pool = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="FlightAgencyPool",
                    pool_size=5, # Giữ sẵn 5 connection trong pool
                    host=os.getenv("DB_HOST", "localhost"),
                    database=os.getenv("DB_NAME", "quanly_banve_pro"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASS", "Dat1234566")
                )
                print("Đã kết nối Database thành công.")
            except Error as e:
                print(f"Lỗi khởi tạo connection pool: {e}")

    @classmethod
    def get_connection(cls):
        """Lấy một connection từ Pool để sử dụng"""
        if cls._pool is None:
            cls.initialize_pool()
        try:
            return cls._pool.get_connection()
        except Error as e:
            print(f"Lỗi khi lấy connection: {e}")
            return None


# Function wrapper để hỗ trợ API cũ
def get_connection():
    """Wrapper function để khôi phục API cũ"""
    return DatabaseConnection.get_connection()