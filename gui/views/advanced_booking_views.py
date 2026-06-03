# gui/views/advanced_booking_views.py
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QGridLayout, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QColor
from bll.advanced_service import AdvancedService

# =======================================================
# 1. QUẢN LÝ HẠNG VÉ (CRUD SEAT CLASSES)
# =======================================================
class TicketTypeManagerView(QWidget):
    def __init__(self):
        super().__init__()
        self.service = AdvancedService()
        self.current_id = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; font-family: 'Segoe UI'; }
            QLineEdit { padding: 10px; border-radius: 6px; background: #1E293B; border: 1px solid #475569; color: white; }
            QLineEdit:focus { border: 1px solid #38BDF8; }
            QTableWidget { background: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; }
            QHeaderView::section { background: #0F172A; color: #94A3B8; font-weight: bold; border: none; padding: 10px; }
            QPushButton { padding: 10px; border-radius: 6px; font-weight: bold; }
        """)
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(30, 30, 30, 30)

        # Form Trái (40%)
        form_frame = QFrame(); form_frame.setFixedWidth(350)
        f_lay = QVBoxLayout(form_frame)
        f_lay.addWidget(QLabel("THIẾT LẬP HẠNG VÉ", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold;"))
        
        self.in_name = QLineEdit(); self.in_name.setPlaceholderText("Tên hạng (VD: BUSINESS)")
        self.in_multi = QLineEdit(); self.in_multi.setPlaceholderText("Hệ số giá (VD: 2.5)")
        self.in_desc = QLineEdit(); self.in_desc.setPlaceholderText("Mô tả thêm...")
        
        f_lay.addWidget(self.in_name); f_lay.addWidget(self.in_multi); f_lay.addWidget(self.in_desc)
        
        btn_grid = QGridLayout()
        self.btn_add = QPushButton("🟢 Thêm Mới", styleSheet="background:#10B981; color:#0F172A;")
        self.btn_upd = QPushButton("🟡 Cập Nhật", styleSheet="background:#F59E0B; color:#0F172A;")
        self.btn_del = QPushButton("🔴 Xóa Hạng", styleSheet="background:#EF4444; color:white;")
        self.btn_clr = QPushButton("Hủy Bỏ", styleSheet="background:#334155; color: white;")
        
        self.btn_add.clicked.connect(self.action_add)
        self.btn_upd.clicked.connect(self.action_update)
        self.btn_del.clicked.connect(self.action_delete)
        self.btn_clr.clicked.connect(self.clear_form)
        
        btn_grid.addWidget(self.btn_add, 0, 0); btn_grid.addWidget(self.btn_upd, 0, 1)
        btn_grid.addWidget(self.btn_del, 1, 0); btn_grid.addWidget(self.btn_clr, 1, 1)
        f_lay.addLayout(btn_grid); f_lay.addStretch()
        
        # Bảng Phải (60%)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Tên Hạng", "Hệ Số", "Mô tả"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_select)
        
        main_lay.addWidget(form_frame); main_lay.addWidget(self.table)
        self.clear_form()

    def load_data(self):
        self.table.setRowCount(0)
        for r, item in enumerate(self.service.get_all_seat_classes()):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(item['class_id'])))
            self.table.setItem(r, 1, QTableWidgetItem(item['class_name']))
            self.table.setItem(r, 2, QTableWidgetItem(str(item['price_multiplier'])))
            self.table.setItem(r, 3, QTableWidgetItem(item['description'] or ""))

    def on_select(self):
        rows = self.table.selectedItems()
        if rows:
            r = rows[0].row()
            self.current_id = int(self.table.item(r, 0).text())
            self.in_name.setText(self.table.item(r, 1).text())
            self.in_multi.setText(self.table.item(r, 2).text())
            self.in_desc.setText(self.table.item(r, 3).text())
            self.btn_add.setEnabled(False); self.btn_upd.setEnabled(True); self.btn_del.setEnabled(True)

    def clear_form(self):
        self.current_id = None
        for w in [self.in_name, self.in_multi, self.in_desc]: w.clear()
        self.table.clearSelection()
        self.btn_add.setEnabled(True); self.btn_upd.setEnabled(False); self.btn_del.setEnabled(False)

    def get_data(self):
        return {'name': self.in_name.text().strip(), 'multiplier': self.in_multi.text().strip(), 'desc': self.in_desc.text().strip()}

    def action_add(self):
        ok, msg = self.service.create_seat_class(self.get_data())
        QMessageBox.information(self, "Hệ thống", msg); self.load_data(); self.clear_form()

    def action_update(self):
        ok, msg = self.service.update_seat_class(self.current_id, self.get_data())
        QMessageBox.information(self, "Hệ thống", msg); self.load_data(); self.clear_form()

    def action_delete(self):
        if QMessageBox.question(self, "Xác nhận", "Xóa hạng vé này?") == QMessageBox.StandardButton.Yes:
            ok, msg = self.service.delete_seat_class(self.current_id)
            if ok: QMessageBox.information(self, "Thành công", msg)
            else: QMessageBox.warning(self, "Lỗi Xóa", msg)
            self.load_data(); self.clear_form()


# =======================================================
# 2. XEM DANH SÁCH HÀNH KHÁCH THEO CHUYẾN (FLIGHT TICKETS)
# =======================================================
class FlightTicketsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0F172A; color: white;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        lbl = QLabel("✈️ DANH SÁCH HÀNH KHÁCH THEO CHUYẾN")
        lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #38BDF8;")
        layout.addWidget(lbl)
        
        note = QLabel("Tính năng này đã được tích hợp tập trung vào màn hình **Quản lý Hành khách** để dễ dàng tra cứu tổng hợp.\\nVui lòng truy cập menu 'Danh sách Hành khách' ở thanh công cụ bên trái.")
        note.setStyleSheet("font-size: 16px; color: #94A3B8; margin-top: 20px;")
        layout.addWidget(note)
        layout.addStretch()


# =======================================================
# 3. CLASS BỊ THIẾU: XEM TRƯỚC SƠ ĐỒ GHẾ (SEAT SELECTION VIEW)
# =======================================================
class SeatSelectionView(QWidget):
    """Màn hình xem trước sơ đồ chuyến bay độc lập"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = AdvancedService()
        self.setup_ui()
        self.load_flights()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; font-family: 'Segoe UI'; }
            QComboBox { padding: 12px; border-radius: 6px; background: #1E293B; border: 1px solid #475569; color: white; font-size: 14px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("💺 XEM TRƯỚC SƠ ĐỒ CHUYẾN BAY")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #38BDF8; margin-bottom: 20px;")
        layout.addWidget(title)
        
        self.cb_flights = QComboBox()
        self.cb_flights.currentIndexChanged.connect(self.on_flight_changed)
        layout.addWidget(self.cb_flights)
        
        legend = QHBoxLayout()
        legend.addWidget(QLabel("🟦 Thương gia")); legend.addWidget(QLabel("🟩 Phổ thông"))
        legend.addWidget(QLabel("🟨 Đang giữ chỗ")); legend.addWidget(QLabel("🟥 Đã bán"))
        layout.addLayout(legend)

        # Lưới chứa sơ đồ ghế
        self.w_seats = QWidget()
        self.grid_seats = QGridLayout(self.w_seats)
        self.grid_seats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.w_seats)
        layout.addStretch()

    def load_flights(self):
        self.cb_flights.blockSignals(True)
        self.cb_flights.addItem("-- Chọn chuyến bay để xem sơ đồ --", None)
        for f in self.service.get_flights_for_admin():
            self.cb_flights.addItem(f"{f['flight_number']} | {f['dep_city']} -> {f['arr_city']}", f['flight_id'])
        self.cb_flights.blockSignals(False)

    def on_flight_changed(self):
        f_id = self.cb_flights.currentData()
        while self.grid_seats.count():
            item = self.grid_seats.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not f_id: return
        
        seats = self.service.get_seat_map(f_id)
        row_map, curr_r = {}, 0
        
        for s in seats:
            match = re.match(r"([A-Za-z]+)(\d+)", s['seat_number'])
            if not match: continue
            letter, num = match.groups()
            
            if letter not in row_map:
                row_map[letter] = curr_r
                lbl = QLabel(f"<b>{letter}</b>")
                lbl.setStyleSheet("color:#94A3B8; padding: 10px; font-size: 16px;")
                self.grid_seats.addWidget(lbl, curr_r, 0)
                curr_r += 1
                
            btn = QPushButton(s['seat_number'])
            btn.setFixedSize(50, 50)
            
            if s['seat_status'] == 'AVAILABLE':
                if s['class_name'] == 'BUSINESS': btn.setStyleSheet("background:#3B82F6; color:white; border-radius:8px; font-weight:bold;")
                else: btn.setStyleSheet("background:#10B981; color:white; border-radius:8px; font-weight:bold;")
            elif s['seat_status'] == 'HELD':
                btn.setStyleSheet("background:#F59E0B; color:black; border-radius:8px; font-weight:bold;")
            else:
                btn.setStyleSheet("background:#EF4444; color:white; border-radius:8px; font-weight:bold;")
                
            # Cắt lối đi ở giữa máy bay
            col = int(num) if int(num) <= 2 else int(num) + 1
            self.grid_seats.addWidget(btn, row_map[letter], col)