# config/database.py
import os
import mysql.connector
from mysql.connector import pooling, Error
from dotenv import load_dotenv

# Load biến môi trường từ file .env (đảm bảo đúng đường dẫn)
load_dotenv(dotenv_path=".env")

class DatabaseConnection:
    _pool = None

    @classmethod
    def initialize_pool(cls):
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="FlightAgencyPool",
                    pool_size=5,

                    host=os.getenv("DB_HOST", "localhost"),
                    port=int(os.getenv("DB_PORT", 3306)),
                    database=os.getenv("DB_NAME", "quanly_banve_pro"),
                    user=os.getenv("DB_USER", "root"),
                    password=os.getenv("DB_PASS", ""),

                    charset="utf8mb4",
                    autocommit=True
                )

                # ❌ bỏ emoji để tránh lỗi
                print("Ket noi Database thanh cong")

            except Error as e:
                print("Loi khoi tao connection pool:", e)

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize_pool()

        try:
            conn = cls._pool.get_connection()
            if conn.is_connected():
                return conn
        except Error as e:
            print("Loi khi lay connection:", e)

        return None

    @classmethod
    def close_connection(cls, conn):
        """Đóng connection sau khi dùng"""
        try:
            if conn and conn.is_connected():
                conn.close()
        except Error as e:
            print("Loi khi dong connection:", e)