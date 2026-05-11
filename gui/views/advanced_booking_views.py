# gui/views/advanced_booking_views.py
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QFrame, 
                             QGridLayout, QComboBox, QHeaderView, QFormLayout, QMessageBox)
from PyQt6.QtCore import Qt
from bll.advanced_service import AdvancedService

# Quản lý hành khách có trong chuyến bay
class FlightTicketsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = AdvancedService()
        self.setup_ui()
        self.load_flights_into_combobox()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Quản lý Danh sách Hành khách")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        layout.addWidget(lbl_title)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Chọn Chuyến Bay:"))
        
        self.cb_flights = QComboBox()
        self.cb_flights.setFixedWidth(300)
        self.cb_flights.setStyleSheet("padding: 8px; border-radius: 4px; background-color: #1E293B; color: white;")
        self.cb_flights.currentIndexChanged.connect(self.load_tickets_for_selected_flight)
        filter_layout.addWidget(self.cb_flights)
        
        btn_refresh = QPushButton("🔄 Tải lại dữ liệu")
        btn_refresh.setObjectName("BtnPrimary")
        btn_refresh.clicked.connect(self.load_tickets_for_selected_flight)
        filter_layout.addWidget(btn_refresh)
        filter_layout.addStretch()
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Mã Vé (ID)", "Hành Khách", "Hạng Vé", "Số Ghế", "Trạng Thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addLayout(filter_layout)
        layout.addWidget(self.table)

    def load_flights_into_combobox(self):
        self.cb_flights.blockSignals(True)
        self.cb_flights.clear()
        flights = self.service.get_flights_for_combobox()
        for f in flights:
            display_text = f"{f['flight_number']} ({f['departure_code']} ➔ {f['arrival_code']}) - {f['status']}"
            self.cb_flights.addItem(display_text, f['flight_id']) 
        self.cb_flights.blockSignals(False)
        self.load_tickets_for_selected_flight()

    def load_tickets_for_selected_flight(self):
        flight_id = self.cb_flights.currentData()
        if not flight_id: return
        
        tickets = self.service.get_tickets_by_flight(flight_id)
        self.table.setRowCount(0)
        for row, t in enumerate(tickets):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f"TKT-{t['ticket_id']}"))
            self.table.setItem(row, 1, QTableWidgetItem(t['full_name']))
            self.table.setItem(row, 2, QTableWidgetItem(t['class_name']))
            self.table.setItem(row, 3, QTableWidgetItem(t['seat_number']))
            
            status_item = QTableWidgetItem(t['status'])
            if t['status'] == 'CANCELLED': status_item.setForeground(Qt.GlobalColor.red)
            elif t['status'] == 'BOOKED': status_item.setForeground(Qt.GlobalColor.green)
            elif t['status'] == 'HELD': status_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 4, status_item)

# Trang Sơ đồ ghế của Admin/Staff
class SeatSelectionView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = AdvancedService()
        self.setup_ui()
        self.apply_styles()
        self.load_flights_into_combobox()

    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton#SeatAVAILABLE { background-color: #10B981; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton#SeatBUSINESS { background-color: #3B82F6; color: white; border-radius: 8px; font-weight: bold; }
            QPushButton#SeatBOOKED { background-color: #EF4444; color: white; border-radius: 8px; }
            QPushButton#SeatHELD { background-color: #F59E0B; color: white; border-radius: 8px; }
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl_title = QLabel("Quản lý Sơ đồ Ghế ngồi")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        layout.addWidget(lbl_title)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Xem sơ đồ máy bay chuyến:"))
        self.cb_flights = QComboBox()
        self.cb_flights.setFixedWidth(400)
        self.cb_flights.setStyleSheet("padding: 8px; border-radius: 4px; background-color: #1E293B; color: white;")
        self.cb_flights.currentIndexChanged.connect(self.render_seat_map)
        top_layout.addWidget(self.cb_flights)
        
        btn_refresh = QPushButton("🔄 Làm mới")
        btn_refresh.clicked.connect(self.render_seat_map)
        top_layout.addWidget(btn_refresh)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        legend_layout = QHBoxLayout()
        legend_layout.addWidget(self.create_legend_item("Trống (Phổ thông)", "SeatAVAILABLE"))
        legend_layout.addWidget(self.create_legend_item("Trống (Thương gia)", "SeatBUSINESS"))
        legend_layout.addWidget(self.create_legend_item("Đã Bán", "SeatBOOKED"))
        legend_layout.addWidget(self.create_legend_item("Đang Giữ Chỗ", "SeatHELD"))
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        layout.addSpacing(20)

        self.plane_frame = QFrame()
        self.plane_frame.setObjectName("SaaSCard")
        self.grid_layout = QGridLayout(self.plane_frame)
        self.grid_layout.setSpacing(10)
        layout.addWidget(self.plane_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def load_flights_into_combobox(self):
        self.cb_flights.blockSignals(True)
        self.cb_flights.clear()
        flights = self.service.get_flights_for_combobox()
        for f in flights:
            display_text = f"{f['flight_number']} ({f['departure_code']} ➔ {f['arrival_code']})"
            self.cb_flights.addItem(display_text, f['flight_id'])
        self.cb_flights.blockSignals(False)
        self.render_seat_map()

    def render_seat_map(self):
        flight_id = self.cb_flights.currentData()
        if not flight_id: return
        
        seats = self.service.get_seat_map(flight_id)

        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        if not seats: return

        row_map = {} 
        current_row_idx = 0

        for seat in seats:
            seat_num = seat['seat_number']
            match = re.match(r"([A-Za-z]+)(\d+)", seat_num)
            if not match: continue
            
            letter_part, number_part = match.groups()
            
            if letter_part not in row_map:
                row_map[letter_part] = current_row_idx
                lbl_row = QLabel(f"<b>Hàng {letter_part}</b>")
                lbl_row.setStyleSheet("color: #94A3B8;")
                self.grid_layout.addWidget(lbl_row, current_row_idx, 0)
                current_row_idx += 1

            r = row_map[letter_part]
            c = int(number_part)

            btn_seat = QPushButton(seat_num)
            btn_seat.setFixedSize(50, 50)
            btn_seat.setToolTip(f"Hạng: {seat['class_name']}") 
            
            if seat['seat_status'] == 'BOOKED': btn_seat.setObjectName("SeatBOOKED")
            elif seat['seat_status'] == 'HELD': btn_seat.setObjectName("SeatHELD")
            elif seat['class_name'] == 'BUSINESS': btn_seat.setObjectName("SeatBUSINESS")
            else: btn_seat.setObjectName("SeatAVAILABLE")

            btn_seat.setEnabled(False)

            display_col = c if c <= 2 else c + 1
            self.grid_layout.addWidget(btn_seat, r, display_col)

    def create_legend_item(self, text, obj_name):
        lbl = QLabel(text)
        btn = QPushButton()
        btn.setFixedSize(20, 20)
        btn.setObjectName(obj_name)
        h = QHBoxLayout(); h.addWidget(btn); h.addWidget(lbl); h.setContentsMargins(0,0,15,0)
        w = QWidget(); w.setLayout(h)
        return w

# Trang quản lý loại vé
class TicketTypeManagerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = AdvancedService()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Thiết lập Hạng Vé & Giá")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        layout.addWidget(lbl_title)

        form_frame = QFrame()
        form_frame.setObjectName("SaaSCard")
        form_layout = QFormLayout(form_frame)
        
        self.lbl_id = QLabel("Auto (Mới)")
        self.lbl_id.setStyleSheet("color: #94A3B8;")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("VD: FIRST CLASS, PREMIUM ECONOMY...")
        self.txt_multiplier = QLineEdit()
        self.txt_multiplier.setPlaceholderText("Hệ số giá (VD: 1.5, 3.0)")
        
        form_layout.addRow("Mã Hạng Vé:", self.lbl_id)
        form_layout.addRow("Tên Hạng Vé:", self.txt_name)
        form_layout.addRow("Hệ số Giá (*):", self.txt_multiplier)
        
        btn_layout = QHBoxLayout()
        btn_clear = QPushButton("Làm mới Form")
        btn_clear.clicked.connect(self.clear_form)
        
        btn_add = QPushButton("➕ Thêm Mới")
        btn_add.setObjectName("BtnSuccess")
        btn_add.clicked.connect(self.handle_add)
        
        btn_update = QPushButton("✏️ Cập Nhật")
        btn_update.setStyleSheet("background-color: #F59E0B; color: white;")
        btn_update.clicked.connect(self.handle_update)
        
        btn_delete = QPushButton("❌ Xóa")
        btn_delete.setObjectName("BtnDanger")
        btn_delete.clicked.connect(self.handle_delete)
        
        btn_layout.addWidget(btn_clear); btn_layout.addStretch()
        btn_layout.addWidget(btn_add); btn_layout.addWidget(btn_update); btn_layout.addWidget(btn_delete)
        form_layout.addRow("", btn_layout)

        layout.addWidget(form_frame)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Tên Hạng Vé", "Hệ số Giá (Multiplier)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_table_click)
        layout.addWidget(self.table)

    def load_data(self):
        classes = self.service.get_all_seat_classes()
        self.table.setRowCount(0)
        for row, c in enumerate(classes):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(c['class_id'])))
            self.table.setItem(row, 1, QTableWidgetItem(c['class_name']))
            self.table.setItem(row, 2, QTableWidgetItem(str(c['price_multiplier'])))

    def on_table_click(self):
        row = self.table.currentRow()
        if row < 0: return
        self.lbl_id.setText(self.table.item(row, 0).text())
        self.txt_name.setText(self.table.item(row, 1).text())
        self.txt_multiplier.setText(self.table.item(row, 2).text())

    def clear_form(self):
        self.lbl_id.setText("Auto (Mới)")
        self.txt_name.clear()
        self.txt_multiplier.clear()

    def handle_add(self):
        success, msg = self.service.create_seat_class(self.txt_name.text().strip(), self.txt_multiplier.text().strip())
        if success:
            self.load_data(); self.clear_form()
            QMessageBox.information(self, "Thành công", msg)
        else: QMessageBox.warning(self, "Lỗi", msg)

    def handle_update(self):
        c_id = self.lbl_id.text()
        if "Auto" in c_id: return QMessageBox.warning(self, "Lỗi", "Chọn 1 hạng vé bên dưới để sửa!")
        success, msg = self.service.update_seat_class(int(c_id), self.txt_name.text().strip(), self.txt_multiplier.text().strip())
        if success:
            self.load_data(); self.clear_form()
            QMessageBox.information(self, "Thành công", msg)
        else: QMessageBox.warning(self, "Lỗi", msg)

    def handle_delete(self):
        c_id = self.lbl_id.text()
        if "Auto" in c_id: return QMessageBox.warning(self, "Lỗi", "Chọn 1 hạng vé bên dưới để xóa!")
        if QMessageBox.question(self, "Xác nhận", "Xóa hạng vé này?") == QMessageBox.StandardButton.Yes:
            success, msg = self.service.delete_seat_class(int(c_id))
            if success:
                self.load_data(); self.clear_form()
                QMessageBox.information(self, "Thành công", msg)
            else: QMessageBox.critical(self, "Lỗi", msg)