# dal/flight_dao.py
from config.database import DatabaseConnection

class FlightDAO:
    def search_flights(self, dep_code, arr_code, flight_date):
        conn = DatabaseConnection.get_connection()
        if not conn:
            return []
            
        cursor = conn.cursor(dictionary=True) # Trả về kết quả dạng Dictionary (Key-Value)
        results = []
        try:
            # Gọi Stored Procedure search_flights
            cursor.callproc('search_flights', (dep_code, arr_code, flight_date))
            
            # Lấy kết quả từ Procedure
            for result in cursor.stored_results():
                results = result.fetchall()
                
        except Exception as e:
            print(f"Lỗi DAL - search_flights: {e}")
        finally:
            cursor.close()
            conn.close() # Rất quan trọng: Trả connection lại cho Pool thay vì đóng hẳn
            
        return results