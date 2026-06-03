# gui/views/airport_management_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from bll.admin_service import AdminService

class AirportManagementScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.service = AdminService()
        self.selected_code = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; font-family: 'Segoe UI'; }
            QLineEdit { padding: 10px; border-radius: 6px; background: #1E293B; border: 1px solid #475569; color: white; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #38BDF8; }
            QTableWidget { background: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; }
            QHeaderView::section { background: #0F172A; color: #94A3B8; font-weight: bold; border: none; padding: 10px; }
            QPushButton { padding: 10px; border-radius: 6px; font-weight: bold; }
        """)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # CỘT TRÁI (40%)
        form_frame = QFrame()
        form_frame.setFixedWidth(380)
        f_lay = QVBoxLayout(form_frame)
        f_lay.setContentsMargins(10, 0, 10, 0)
        
        f_lay.addWidget(QLabel("✈️ CẤU HÌNH DANH MỤC SÂN BAY", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold; margin-bottom:10px;"))
        
        self.in_code = QLineEdit(); self.in_code.setPlaceholderText("Mã sân bay (3 ký tự - Ví dụ: HAN)")
        self.in_name = QLineEdit(); self.in_name.setPlaceholderText("Tên sân bay (Ví dụ: Nội Bài)")
        self.in_city = QLineEdit(); self.in_city.setPlaceholderText("Thành phố / Tỉnh")
        self.in_country = QLineEdit(); self.in_country.setPlaceholderText("Quốc gia")

        f_lay.addWidget(QLabel("Mã sân bay (*):")); f_lay.addWidget(self.in_code)
        f_lay.addWidget(QLabel("Tên sân bay (*):")); f_lay.addWidget(self.in_name)
        f_lay.addWidget(QLabel("Thành phố (*):")); f_lay.addWidget(self.in_city)
        f_lay.addWidget(QLabel("Quốc gia (*):")); f_lay.addWidget(self.in_country)

        # Lưới 4 nút chuẩn CRUD
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)
        self.btn_add = QPushButton("🟢 Thêm Mới", styleSheet="background:#10B981; color:#0F172A;")
        self.btn_upd = QPushButton("🟡 Cập Nhật", styleSheet="background:#F59E0B; color:#0F172A;")
        self.btn_del = QPushButton("🔴 Xóa Sân Bay", styleSheet="background:#EF4444; color:white;")
        self.btn_clr = QPushButton("Hủy Bỏ", styleSheet="background:#334155; color: white;")
        
        for b in [self.btn_add, self.btn_upd, self.btn_del, self.btn_clr]: b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.btn_add.clicked.connect(self.action_add_airport)
        self.btn_upd.clicked.connect(self.action_update_airport)
        self.btn_del.clicked.connect(self.action_delete_airport)
        self.btn_clr.clicked.connect(self.clear_form_fields)
        
        btn_grid.addWidget(self.btn_add, 0, 0); btn_grid.addWidget(self.btn_upd, 0, 1)
        btn_grid.addWidget(self.btn_del, 1, 0); btn_grid.addWidget(self.btn_clr, 1, 1)
        f_lay.addLayout(btn_grid); f_lay.addStretch()

        # CỘT PHẢI (60%)
        right_lay = QVBoxLayout()
        right_lay.addWidget(QLabel("🗺️ MẠNG LƯỚI SÂN BAY ĐANG KHAI THÁC", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold;"))
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mã Code", "Tên Sân Bay", "Thành Phố", "Quốc Gia"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_row_selected)
        
        right_lay.addWidget(self.table)
        main_layout.addWidget(form_frame, 4)
        main_layout.addLayout(right_lay, 6)
        self.load_airports_data()
        self.clear_form_fields()

    def load_airports_data(self):
        self.table.setRowCount(0)
        airports = self.service.get_all_airports() 
        for r, a in enumerate(airports):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(a['airport_code'])) 
            self.table.setItem(r, 1, QTableWidgetItem(a['name'])) 
            self.table.setItem(r, 2, QTableWidgetItem(a['city'])) 
            self.table.setItem(r, 3, QTableWidgetItem(a['country'])) 

    def on_table_row_selected(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.selected_code = self.table.item(row, 0).text()
            self.in_code.setText(self.selected_code); self.in_code.setEnabled(False)
            self.in_name.setText(self.table.item(row, 1).text())
            self.in_city.setText(self.table.item(row, 2).text())
            self.in_country.setText(self.table.item(row, 3).text())
            self.btn_add.setEnabled(False); self.btn_add.setStyleSheet("background:#334155; color:#64748B;")
            self.btn_upd.setEnabled(True); self.btn_del.setEnabled(True)

    def clear_form_fields(self):
        self.selected_code = None
        for w in [self.in_code, self.in_name, self.in_city, self.in_country]: w.clear()
        self.in_code.setEnabled(True)
        self.table.clearSelection()
        self.btn_add.setEnabled(True); self.btn_add.setStyleSheet("background:#10B981; color:#0F172A;")
        self.btn_upd.setEnabled(False); self.btn_del.setEnabled(False)

    def action_add_airport(self):
        success, msg = self.service.create_airport(
            self.in_code.text().strip(), self.in_name.text().strip(), 
            self.in_city.text().strip(), self.in_country.text().strip(), self.current_user) 
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.load_airports_data(); self.clear_form_fields()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def action_update_airport(self):
        if not self.selected_code: return
        success, msg = self.service.update_airport(
            self.selected_code, self.in_name.text().strip(), 
            self.in_city.text().strip(), self.in_country.text().strip(), self.current_user) 
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.load_airports_data(); self.clear_form_fields()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def action_delete_airport(self):
        if not self.selected_code: return
        confirm = QMessageBox.question(self, "Xác nhận", f"Xóa vĩnh viễn mã sân bay {self.selected_code}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = self.service.delete_airport(self.selected_code, self.current_user) 
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_airports_data(); self.clear_form_fields()
            else:
                QMessageBox.warning(self, "Lỗi ràng buộc", msg)