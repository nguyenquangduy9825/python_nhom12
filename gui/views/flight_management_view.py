# gui/views/flight_management_view.py
import csv
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, 
                             QGridLayout, QComboBox, QDateTimeEdit, QFileDialog)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QCursor, QTextDocument
from PyQt6.QtPrintSupport import QPrinter

from bll.booking_service import BookingService
from bll.admin_service import AdminService # Import để gọi CSDL Máy bay

class FlightManagementScreen(QWidget):
    def __init__(self, parent_main=None):
        super().__init__()
        self.service = BookingService()
        self.admin_service = AdminService() # Khởi tạo kết nối Service Máy bay
        self.current_flight_id = None
        
        self.setup_ui()
        self.load_aircraft_combobox() # Load máy bay lên Form
        self.load_flights_data()

    def setup_ui(self):
        # Tối ưu hóa giao diện chuẩn UI/UX Deep Ocean
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; font-family: 'Segoe UI'; }
            QLineEdit, QComboBox, QDateTimeEdit { 
                padding: 10px 14px; border-radius: 8px; background: #1E293B; 
                border: 1px solid #475569; color: white; font-size: 14px; 
            }
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus { border: 1px solid #38BDF8; }
            QDateTimeEdit::drop-down { border: none; width: 32px; }
            QDateTimeEdit::down-arrow { image: none; }
            
            QCalendarWidget QWidget { alternate-background-color: #1E293B; background-color: #0F172A; }
            QCalendarWidget QToolButton { color: white; background-color: transparent; font-weight: bold; border-radius: 4px; }
            QCalendarWidget QToolButton:hover { background-color: #38BDF8; color: #0F172A; }
            QCalendarWidget QMenu { background-color: #1E293B; color: white; }
            QCalendarWidget QSpinBox { background-color: #1E293B; color: white; }
            QCalendarWidget QAbstractItemView:enabled { color: white; selection-background-color: #38BDF8; selection-color: #0F172A; }
            
            QTableWidget { background: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; outline: none; }
            QHeaderView::section { background: #0F172A; color: #94A3B8; font-weight: bold; border: none; padding: 12px 16px; text-align: left; }
            QTableWidget::item { padding: 8px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            
            QPushButton { padding: 10px 16px; border-radius: 8px; font-weight: bold; font-size: 14px; }
            QPushButton#BtnTool { background: #1E293B; border: 1px solid #475569; color: #F8FAFC; }
            QPushButton#BtnTool:hover { background: #38BDF8; color: #0F172A; border-color: #38BDF8; }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # =========================================================
        # CỘT TRÁI (40%): FORM CẤU HÌNH DẠNG GRID GỌN GÀNG
        # =========================================================
        form_frame = QFrame()
        form_frame.setFixedWidth(420)
        f_lay = QVBoxLayout(form_frame)
        f_lay.setContentsMargins(0, 0, 16, 0)
        f_lay.setSpacing(16)
        
        f_lay.addWidget(QLabel("✈️ TẠO CHUYẾN BAY MỚI", styleSheet="font-size: 20px; color: #38BDF8; font-weight: 900; margin-bottom: 10px;"))
        
        # Grid Form Layout (Thẳng thớm và đều tắp)
        grid_form = QGridLayout()
        grid_form.setSpacing(16)
        
        self.in_num = QLineEdit(); self.in_num.setPlaceholderText("VD: VN123")
        self.cb_aircraft = QComboBox() # THÊM NÚT CHỌN MÁY BAY
        self.in_dep = QLineEdit(); self.in_dep.setPlaceholderText("Mã ĐI (VD: HAN)")
        self.in_arr = QLineEdit(); self.in_arr.setPlaceholderText("Mã ĐẾN (VD: SGN)")
        self.in_price = QLineEdit(); self.in_price.setPlaceholderText("Giá gốc (VNĐ)")
        
        self.in_time_dep = QDateTimeEdit(); self.in_time_dep.setCalendarPopup(True); self.in_time_dep.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.in_time_arr = QDateTimeEdit(); self.in_time_arr.setCalendarPopup(True); self.in_time_arr.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.cb_status = QComboBox(); self.cb_status.addItems(["PENDING", "DEPARTED", "CANCELLED"])
        
        # Add to Grid (Label -> Input)
        grid_form.addWidget(QLabel("Số hiệu chuyến bay:"), 0, 0)
        grid_form.addWidget(self.in_num, 0, 1)
        grid_form.addWidget(QLabel("Tàu bay khai thác:"), 1, 0)
        grid_form.addWidget(self.cb_aircraft, 1, 1)
        grid_form.addWidget(QLabel("Mã Sân bay ĐI:"), 2, 0)
        grid_form.addWidget(self.in_dep, 2, 1)
        grid_form.addWidget(QLabel("Mã Sân bay ĐẾN:"), 3, 0)
        grid_form.addWidget(self.in_arr, 3, 1)
        grid_form.addWidget(QLabel("Giờ cất cánh:"), 4, 0)
        grid_form.addWidget(self.in_time_dep, 4, 1)
        grid_form.addWidget(QLabel("Giờ hạ cánh:"), 5, 0)
        grid_form.addWidget(self.in_time_arr, 5, 1)
        grid_form.addWidget(QLabel("Giá gốc:"), 6, 0)
        grid_form.addWidget(self.in_price, 6, 1)
        grid_form.addWidget(QLabel("Trạng thái:"), 7, 0)
        grid_form.addWidget(self.cb_status, 7, 1)

        f_lay.addLayout(grid_form)

        # Lưới nút bấm CRUD
        btn_grid = QGridLayout(); btn_grid.setSpacing(12)
        self.btn_add = QPushButton("🟢 Thêm Mới", styleSheet="background:#10B981; color:#0F172A;")
        self.btn_upd = QPushButton("🟡 Cập Nhật", styleSheet="background:#F59E0B; color:#0F172A;")
        self.btn_del = QPushButton("🔴 Xóa Chuyến", styleSheet="background:#EF4444; color:white;")
        self.btn_clr = QPushButton("Làm Mới Form", styleSheet="background:#334155; color: white;")
        
        for b in [self.btn_add, self.btn_upd, self.btn_del, self.btn_clr]: b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.btn_add.clicked.connect(self.action_add_flight)
        self.btn_upd.clicked.connect(self.action_update_flight)
        self.btn_del.clicked.connect(self.action_delete_flight)
        self.btn_clr.clicked.connect(self.clear_form_fields)
        
        btn_grid.addWidget(self.btn_add, 0, 0); btn_grid.addWidget(self.btn_upd, 0, 1)
        btn_grid.addWidget(self.btn_del, 1, 0); btn_grid.addWidget(self.btn_clr, 1, 1)
        f_lay.addLayout(btn_grid); f_lay.addStretch()

        # =========================================================
        # CỘT PHẢI (60%): BẢNG LƯỚI QUẢN LÝ TỔNG THỂ
        # =========================================================
        right_lay = QVBoxLayout()
        right_lay.setSpacing(16)
        
        toolbar_lay = QHBoxLayout()
        toolbar_lay.addWidget(QLabel("🗺️ DANH SÁCH CHUYẾN BAY HỆ THỐNG", styleSheet="font-size: 20px; color: #38BDF8; font-weight: 900;"))
        toolbar_lay.addStretch()
        
        btn_reload = QPushButton("🔄 Tải lại"); btn_reload.setObjectName("BtnTool")
        btn_excel = QPushButton("📊 Xuất Excel"); btn_excel.setObjectName("BtnTool")
        btn_pdf = QPushButton("📄 Xuất PDF"); btn_pdf.setObjectName("BtnTool")
        
        for btn in [btn_reload, btn_excel, btn_pdf]: btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        btn_reload.clicked.connect(self.load_flights_data)
        btn_excel.clicked.connect(self.action_export_excel)
        btn_pdf.clicked.connect(self.action_export_pdf)
        
        toolbar_lay.addWidget(btn_reload); toolbar_lay.addWidget(btn_excel); toolbar_lay.addWidget(btn_pdf)
        right_lay.addLayout(toolbar_lay)
        
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Số Hiệu", "Tuyến Bay", "Giờ Khởi Hành", "Giờ Hạ Cánh", "Giá Gốc", "Trạng Thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_row_selected)
        
        right_lay.addWidget(self.table)
        
        main_layout.addWidget(form_frame, 4)
        main_layout.addLayout(right_lay, 6)
        self.clear_form_fields()

    # ==========================================
    # CÁC HÀM XỬ LÝ NGHIỆP VỤ & RENDER DỮ LIỆU
    # ==========================================
    def load_aircraft_combobox(self):
        """Kéo danh sách Máy bay từ CSDL đổ vào Form chọn"""
        self.cb_aircraft.clear()
        acs = self.admin_service.get_all_aircrafts()
        for ac in acs:
            self.cb_aircraft.addItem(f"{ac['type_name']} ({ac['manufacturer']})", ac['aircraft_type_id'])

    def load_flights_data(self):
        self.table.setRowCount(0)
        self.flights_list = self.service.get_all_flights_management()
        for r, f in enumerate(self.flights_list):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(f['flight_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(f['flight_number']))
            self.table.setItem(r, 2, QTableWidgetItem(f"{f.get('departure_code', '')} ➔ {f.get('arrival_code', '')}"))
            self.table.setItem(r, 3, QTableWidgetItem(f['departure_time'].strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(r, 4, QTableWidgetItem(f['arrival_time'].strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(r, 5, QTableWidgetItem(f"{float(f['base_price']):,.0f}"))
            
            status_item = QTableWidgetItem(f['status'])
            if f['status'] == 'PENDING': status_item.setForeground(Qt.GlobalColor.green)
            elif f['status'] == 'CANCELLED': status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(r, 6, status_item)

    def on_table_row_selected(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            f_id = int(self.table.item(row, 0).text())
            self.current_flight_id = f_id
            
            flight = next(f for f in self.flights_list if f['flight_id'] == f_id)
            self.in_num.setText(flight['flight_number'])
            self.in_dep.setText(flight.get('departure_code', ''))
            self.in_arr.setText(flight.get('arrival_code', ''))
            
            dt_dep = QDateTime.fromString(flight['departure_time'].strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss")
            self.in_time_dep.setDateTime(dt_dep)
            
            dt_arr = QDateTime.fromString(flight['arrival_time'].strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd HH:mm:ss")
            self.in_time_arr.setDateTime(dt_arr)
            
            self.in_price.setText(str(int(flight['base_price'])))
            self.cb_status.setCurrentText(flight['status'])
            
            self.btn_add.setEnabled(False); self.btn_add.setStyleSheet("background:#334155; color:#64748B;")
            self.btn_upd.setEnabled(True); self.btn_del.setEnabled(True)

    def clear_form_fields(self):
        self.current_flight_id = None
        self.in_num.clear(); self.in_dep.clear(); self.in_arr.clear(); self.in_price.clear()
        self.in_time_dep.setDateTime(QDateTime.currentDateTime())
        self.in_time_arr.setDateTime(QDateTime.currentDateTime().addSecs(7200))
        self.cb_status.setCurrentIndex(0)
        self.cb_aircraft.setCurrentIndex(0) # Reset combobox máy bay
        self.table.clearSelection()
        
        self.btn_add.setEnabled(True); self.btn_add.setStyleSheet("background:#10B981; color:#0F172A;")
        self.btn_upd.setEnabled(False); self.btn_del.setEnabled(False)

    def pack_form_data(self) -> dict:
        return {
            'flight_number': self.in_num.text().strip(),
            'aircraft_type_id': self.cb_aircraft.currentData(), # ĐÃ CẬP NHẬT TRUYỀN ID XUỐNG DB
            'departure_code': self.in_dep.text().strip(),
            'arrival_code': self.in_arr.text().strip(),
            'departure_time': self.in_time_dep.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'arrival_time': self.in_time_arr.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'base_price': self.in_price.text().strip(),
            'status': self.cb_status.currentText()
        }

    # Các hàm CRUD  
    def action_add_flight(self):
        success, msg = self.service.create_new_flight(self.pack_form_data())
        if success:
            QMessageBox.information(self, "Thành công", msg); self.load_flights_data(); self.clear_form_fields()
        else: QMessageBox.warning(self, "Lỗi nhập liệu", msg)

    def action_update_flight(self):
        if not self.current_flight_id: return
        success, msg = self.service.update_existing_flight(self.current_flight_id, self.pack_form_data())
        if success:
            QMessageBox.information(self, "Thành công", msg); self.load_flights_data(); self.clear_form_fields()
        else: QMessageBox.warning(self, "Lỗi", msg)

    def action_delete_flight(self):
        if not self.current_flight_id: return
        confirm = QMessageBox.question(self, "Xác nhận", "Xóa vĩnh viễn chuyến bay này?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = self.service.delete_existing_flight(self.current_flight_id)
            if success:
                QMessageBox.information(self, "Xác nhận", msg); self.load_flights_data(); self.clear_form_fields()
            else: QMessageBox.warning(self, "Lỗi", msg)

    # Xuất excel & pdf
    def action_export_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file Excel", "", "CSV Files (*.csv);;All Files (*)")
        if not path: return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(self.table.columnCount())]
                    writer.writerow(row_data)
            QMessageBox.information(self, "Thành công", f"Đã xuất dữ liệu Excel thành công tại:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất file", f"Không thể lưu file Excel: {e}")

    def action_export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file PDF", "", "PDF Files (*.pdf);;All Files (*)")
        if not path: return
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            html = "<h1 style='text-align:center; color:#1E293B;'>BÁO CÁO LỊCH TRÌNH CHUYẾN BAY</h1>"
            html += "<table border='1' cellspacing='0' cellpadding='6' width='100%' style='border-collapse: collapse;'>"
            html += "<tr style='background-color:#E2E8F0;'>"
            for i in range(self.table.columnCount()): html += f"<th>{self.table.horizontalHeaderItem(i).text()}</th>"
            html += "</tr>"
            for row in range(self.table.rowCount()):
                html += "<tr>"
                for col in range(self.table.columnCount()):
                    text = self.table.item(row, col).text() if self.table.item(row, col) else ""
                    html += f"<td>{text}</td>"
                html += "</tr>"
            html += "</table>"
            doc = QTextDocument(); doc.setHtml(html); doc.print(printer)
            QMessageBox.information(self, "Thành công", f"Đã xuất báo cáo PDF thành công tại:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất file", f"Vui lòng kiểm tra lại thư viện QtPrintSupport: {e}")