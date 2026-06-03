# gui/views/aircraft_management_view.py
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from bll.admin_service import AdminService

class AircraftManagementScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.service = AdminService()
        self.current_aircraft_id = None
        self.seat_templates = []
        self.setup_ui()
        self.load_aircrafts()
        self.load_classes()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
            QFrame#Card { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QLineEdit, QSpinBox, QComboBox { padding: 8px 12px; border-radius: 6px; background-color: #0F172A; border: 1px solid #475569; color: white; }
            QTableWidget { background-color: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; outline: none; }
            QHeaderView::section { background-color: #0F172A; color: #94A3B8; padding: 10px; font-weight: bold; border: none; }
            QPushButton { font-weight: bold; border-radius: 6px; padding: 8px 16px; }
        """)
        
        # Đã cập nhật tên biến cực kỳ rõ ràng
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # ==========================================
        # CỘT TRÁI: DANH SÁCH TÀU BAY
        # ==========================================
        left_frame = QFrame()
        left_frame.setObjectName("Card")
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(QLabel("🛩️ DANH MỤC TÀU BAY", styleSheet="font-size:16px; color:#38BDF8; font-weight:bold;"))
        
        self.table_aircrafts = QTableWidget(0, 4)
        self.table_aircrafts.setHorizontalHeaderLabels(["ID", "Tên Tàu Bay", "Hãng SX", "Tổng Ghế"])
        self.table_aircrafts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_aircrafts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_aircrafts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_aircrafts.itemSelectionChanged.connect(self.on_aircraft_selected)
        left_layout.addWidget(self.table_aircrafts)

        add_layout = QHBoxLayout()
        self.txt_aircraft_name = QLineEdit()
        self.txt_aircraft_name.setPlaceholderText("VD: Airbus A321")
        
        self.txt_manufacturer = QLineEdit()
        self.txt_manufacturer.setPlaceholderText("VD: Airbus")
        
        btn_add_aircraft = QPushButton("Thêm Tàu Bay")
        btn_add_aircraft.setStyleSheet("background-color: #10B981; color: #0F172A;")
        btn_add_aircraft.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add_aircraft.clicked.connect(self.add_aircraft)
        
        add_layout.addWidget(self.txt_aircraft_name)
        add_layout.addWidget(self.txt_manufacturer)
        add_layout.addWidget(btn_add_aircraft)
        left_layout.addLayout(add_layout)
        
        main_layout.addWidget(left_frame, 4)

        # ==========================================
        # CỘT PHẢI: GIAO DIỆN CẤU HÌNH GHẾ
        # ==========================================
        right_frame = QFrame()
        right_frame.setObjectName("Card")
        right_layout = QVBoxLayout(right_frame)
        
        self.lbl_aircraft_name = QLabel("⚙️ CẤU HÌNH SƠ ĐỒ GHẾ: Vui lòng chọn Tàu bay")
        self.lbl_aircraft_name.setStyleSheet("font-size:16px; color:#F59E0B; font-weight:bold;")
        right_layout.addWidget(self.lbl_aircraft_name)

        # Bộ công cụ Auto-Generate (Sinh ghế nhanh)
        tools_layout = QHBoxLayout()
        
        self.txt_row_prefix = QLineEdit()
        self.txt_row_prefix.setPlaceholderText("Ký hiệu hàng (VD: VIP)")
        self.txt_row_prefix.setFixedWidth(140)
        
        self.spin_from = QSpinBox()
        self.spin_from.setRange(1, 100)
        self.spin_from.setPrefix("Từ số: ")
        
        self.spin_to = QSpinBox()
        self.spin_to.setRange(1, 100)
        self.spin_to.setPrefix("Đến số: ")
        
        self.combo_seat_class = QComboBox()
        
        btn_generate = QPushButton("⚡ Sinh Ghế")
        btn_generate.setStyleSheet("background-color: #38BDF8; color: #0F172A;")
        btn_generate.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_generate.clicked.connect(self.generate_seats)

        for widget in [self.txt_row_prefix, self.spin_from, self.spin_to, self.combo_seat_class, btn_generate]: 
            tools_layout.addWidget(widget)
            
        right_layout.addLayout(tools_layout)

        # Bảng hiển thị ghế
        self.table_seats = QTableWidget(0, 3)
        self.table_seats.setHorizontalHeaderLabels(["Mã Ghế", "Hạng Mặc Định", "Thao tác"])
        self.table_seats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_seats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.table_seats)

        btn_save = QPushButton("💾 LƯU CẤU HÌNH SƠ ĐỒ VÀO CSDL")
        btn_save.setStyleSheet("background-color: #10B981; color: #0F172A; padding: 12px; font-size: 14px;")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self.save_seat_config)
        right_layout.addWidget(btn_save)

        main_layout.addWidget(right_frame, 5) # <--- ĐÃ FIX LỖI Ở ĐÂY CHUẨN XÁC!

    # ==========================================
    # CÁC HÀM XỬ LÝ DỮ LIỆU
    # ==========================================
    def load_classes(self):
        classes = self.service.get_all_seat_classes()
        for cls in classes: 
            self.combo_seat_class.addItem(cls['class_name'], cls['class_id'])

    def load_aircrafts(self):
        aircrafts = self.service.get_all_aircrafts()
        self.table_aircrafts.setRowCount(0)
        for row_idx, aircraft in enumerate(aircrafts):
            self.table_aircrafts.insertRow(row_idx)
            self.table_aircrafts.setItem(row_idx, 0, QTableWidgetItem(str(aircraft['aircraft_type_id'])))
            self.table_aircrafts.setItem(row_idx, 1, QTableWidgetItem(aircraft['type_name']))
            self.table_aircrafts.setItem(row_idx, 2, QTableWidgetItem(aircraft['manufacturer']))
            self.table_aircrafts.setItem(row_idx, 3, QTableWidgetItem(str(aircraft['total_seats'])))

    def add_aircraft(self):
        name = self.txt_aircraft_name.text().strip()
        manufacturer = self.txt_manufacturer.text().strip()
        
        if not name or not manufacturer: 
            return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đủ Tên và Hãng Sản Xuất!")
            
        success, message = self.service.create_aircraft(name, manufacturer, 0)
        if success:
            self.txt_aircraft_name.clear()
            self.txt_manufacturer.clear()
            self.load_aircrafts()
        else: 
            QMessageBox.critical(self, "Lỗi", message)

    def on_aircraft_selected(self):
        selected_row = self.table_aircrafts.currentRow()
        if selected_row < 0: return
        
        self.current_aircraft_id = int(self.table_aircrafts.item(selected_row, 0).text())
        aircraft_name = self.table_aircrafts.item(selected_row, 1).text()
        self.lbl_aircraft_name.setText(f"⚙️ CẤU HÌNH SƠ ĐỒ GHẾ: {aircraft_name}")
        
        templates = self.service.get_seat_templates(self.current_aircraft_id)
        self.seat_templates = [{'seat_number': t['seat_number'], 'class_id': t['class_id'], 'class_name': t['class_name']} for t in templates]
        self.render_seat_table()

    def generate_seats(self):
        if not self.current_aircraft_id: 
            return QMessageBox.warning(self, "Lỗi", "Vui lòng chọn tàu bay bên trái trước!")
            
        prefix = self.txt_row_prefix.text().strip().upper()
        if not prefix: 
            return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Ký hiệu hàng ghế (VD: A hoặc VIP)!")
            
        start_num = self.spin_from.value()
        end_num = self.spin_to.value()
        
        if start_num > end_num: return
        
        class_id = self.combo_seat_class.currentData()
        class_name = self.combo_seat_class.currentText()
        
        # Thêm hàng loạt ghế vào bộ nhớ tạm
        for i in range(start_num, end_num + 1):
            seat_num = f"{prefix}{i}"
            exists = False
            for template in self.seat_templates:
                if template['seat_number'] == seat_num:
                    template['class_id'] = class_id
                    template['class_name'] = class_name
                    exists = True
                    break
            if not exists:
                self.seat_templates.append({'seat_number': seat_num, 'class_id': class_id, 'class_name': class_name})
                
        self.render_seat_table()

    def render_seat_table(self):
        self.table_seats.setRowCount(0)
        
        # Regex sắp xếp thông minh: Phân tách rõ phần chữ và phần số
        def sort_key(seat_data):
            match = re.match(r"([A-Za-z]+)(\d+)", seat_data['seat_number'])
            if match:
                return (match.group(1), int(match.group(2)))
            return (seat_data['seat_number'], 0)
            
        self.seat_templates.sort(key=sort_key)
        
        for row_idx, template in enumerate(self.seat_templates):
            self.table_seats.insertRow(row_idx)
            self.table_seats.setItem(row_idx, 0, QTableWidgetItem(template['seat_number']))
            self.table_seats.setItem(row_idx, 1, QTableWidgetItem(template['class_name']))
            
            btn_delete = QPushButton("❌ Xóa")
            btn_delete.setStyleSheet("background: transparent; color: #EF4444; border: none;")
            btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_delete.clicked.connect(lambda checked, s_num=template['seat_number']: self.remove_seat(s_num))
            self.table_seats.setCellWidget(row_idx, 2, btn_delete)

    def remove_seat(self, seat_number):
        self.seat_templates = [t for t in self.seat_templates if t['seat_number'] != seat_number]
        self.render_seat_table()

    def save_seat_config(self):
        if not self.current_aircraft_id: return
        success, message = self.service.save_seat_templates(self.current_aircraft_id, self.seat_templates)
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.load_aircrafts() 
        else: 
            QMessageBox.critical(self, "Lỗi", message)