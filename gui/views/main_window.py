# gui/views/main_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from bll.flight_service import FlightService # Bạn đã tạo ở bước trước

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Quản lý Bán vé máy bay")
        self.setGeometry(100, 100, 900, 600)
        
        # Khởi tạo Service
        self.flight_service = FlightService()
        
        # Cài đặt giao diện chính
        self.setup_ui()

    def setup_ui(self):
        # Widget trung tâm
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính (Dọc: Trền Form, Dưới Bảng)
        main_layout = QVBoxLayout(central_widget)
        
        # --- PHẦN 1: FORM TÌM KIẾM ---
        search_layout = QHBoxLayout()
        
        # Cụm Điểm đi
        search_layout.addWidget(QLabel("Điểm đi (Mã):"))
        self.txt_departure = QLineEdit()
        self.txt_departure.setPlaceholderText("VD: HAN")
        search_layout.addWidget(self.txt_departure)
        
        # Cụm Điểm đến
        search_layout.addWidget(QLabel("Điểm đến (Mã):"))
        self.txt_arrival = QLineEdit()
        self.txt_arrival.setPlaceholderText("VD: SGN")
        search_layout.addWidget(self.txt_arrival)
        
        # Cụm Ngày bay
        search_layout.addWidget(QLabel("Ngày bay:"))
        self.date_flight = QDateEdit()
        self.date_flight.setDate(QDate.currentDate())
        self.date_flight.setCalendarPopup(True)
        self.date_flight.setDisplayFormat("yyyy-MM-dd")
        search_layout.addWidget(self.date_flight)
        
        # Nút Tìm kiếm
        self.btn_search = QPushButton("Tìm Chuyến Bay")
        self.btn_search.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 5px;")
        self.btn_search.clicked.connect(self.handle_search_flights) # Nối Event
        search_layout.addWidget(self.btn_search)
        
        main_layout.addLayout(search_layout)
        
        # --- PHẦN 2: BẢNG KẾT QUẢ ---
        self.table_flights = QTableWidget()
        self.table_flights.setColumnCount(6)
        self.table_flights.setHorizontalHeaderLabels([
            "Mã Chuyến", "Từ", "Đến", "Giờ Cất Cánh", "Giờ Hạ Cánh", "Trạng Thái"
        ])
        
        # Cho header tự giãn đều
        header = self.table_flights.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Chặn edit trực tiếp trên bảng
        self.table_flights.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_flights.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.table_flights)
        
        # --- PHẦN 3: NÚT ĐẶT VÉ (Bottom) ---
        bottom_layout = QHBoxLayout()
        self.btn_book = QPushButton("Tiến Hành Đặt Vé Chuyến Đã Chọn")
        self.btn_book.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_book.clicked.connect(self.open_booking_dialog)
        bottom_layout.addStretch() # Đẩy nút sang phải
        bottom_layout.addWidget(self.btn_book)
        
        main_layout.addLayout(bottom_layout)

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN (SLOTS) ---
    def handle_search_flights(self):
        dep = self.txt_departure.text().strip().upper()
        arr = self.txt_arrival.text().strip().upper()
        date_str = self.date_flight.date().toString("yyyy-MM-dd")
        
        if not dep or not arr:
            QMessageBox.warning(self, "Lỗi Nhập Liệu", "Vui lòng nhập mã điểm đi và điểm đến!")
            return
            
        try:
            # Gọi Logic (BLL)
            flights = self.flight_service.get_available_flights(dep, arr, date_str)
            self.load_data_to_table(flights)
        except ValueError as ve:
            QMessageBox.warning(self, "Lỗi Logic", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Hệ Thống", f"Đã xảy ra lỗi: {str(e)}")

    def load_data_to_table(self, flights_data):
        # Xóa dữ liệu cũ
        self.table_flights.setRowCount(0)
        
        if not flights_data:
            QMessageBox.information(self, "Thông báo", "Không tìm thấy chuyến bay nào phù hợp.")
            return
            
        # Đổ dữ liệu mới
        for row_idx, flight in enumerate(flights_data):
            self.table_flights.insertRow(row_idx)
            self.table_flights.setItem(row_idx, 0, QTableWidgetItem(str(flight['flight_number'])))
            self.table_flights.setItem(row_idx, 1, QTableWidgetItem(str(flight['dep_city'])))
            self.table_flights.setItem(row_idx, 2, QTableWidgetItem(str(flight['arr_city'])))
            self.table_flights.setItem(row_idx, 3, QTableWidgetItem(str(flight['departure_time'])))
            self.table_flights.setItem(row_idx, 4, QTableWidgetItem(str(flight['arrival_time'])))
            self.table_flights.setItem(row_idx, 5, QTableWidgetItem(str(flight['status'])))

    def open_booking_dialog(self):
        # Lấy dòng đang được chọn
        selected_row = self.table_flights.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn 1 chuyến bay trên bảng để đặt vé!")
            return
            
        flight_number = self.table_flights.item(selected_row, 0).text()
        QMessageBox.information(self, "Tiếp tục", f"Mở form đặt vé cho chuyến {flight_number}...\n(Bạn sẽ tạo thêm một Dialog ở đây)")