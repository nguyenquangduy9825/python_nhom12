# gui/views/voucher_management_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from bll.admin_service import AdminService

class VoucherManagementScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.service = AdminService()
        self.selected_code = None
        self.setup_ui()
        self.load_vouchers_data()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; font-family: 'Segoe UI'; }
            QLineEdit { padding: 10px; border-radius: 6px; background: #1E293B; border: 1px solid #475569; color: white; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #38BDF8; }
            QLineEdit:disabled { background: #334155; color: #94A3B8; } /* Style khi disable ô Mã Code */
            QTableWidget { background: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; }
            QHeaderView::section { background: #0F172A; color: #94A3B8; font-weight: bold; border: none; padding: 10px; text-align: left; }
            QTableWidget::item { padding: 8px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }
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
        
        f_lay.addWidget(QLabel("🎟️ CẤU HÌNH MÃ GIẢM GIÁ", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold; margin-bottom:10px;"))
        
        self.in_code = QLineEdit(); self.in_code.setPlaceholderText("Mã Voucher (Ví dụ: SUMMER2026)")
        self.in_discount = QLineEdit(); self.in_discount.setPlaceholderText("Phần trăm giảm (1 - 100)")
        self.in_max_disc = QLineEdit(); self.in_max_disc.setPlaceholderText("Số tiền giảm tối đa (VNĐ)")
        self.in_limit = QLineEdit(); self.in_limit.setPlaceholderText("Giới hạn lượt sử dụng")
        self.in_expiry = QLineEdit(); self.in_expiry.setPlaceholderText("Ngày hết hạn (YYYY-MM-DD HH:MM:SS)")

        f_lay.addWidget(QLabel("Mã giảm giá (*):")); f_lay.addWidget(self.in_code)
        f_lay.addWidget(QLabel("Phần trăm chiết khấu (*):")); f_lay.addWidget(self.in_discount)
        f_lay.addWidget(QLabel("Mức giảm kịch trần (*):")); f_lay.addWidget(self.in_max_disc)
        f_lay.addWidget(QLabel("Tổng lượt phát hành (*):")); f_lay.addWidget(self.in_limit)
        f_lay.addWidget(QLabel("Hạn định đóng chương trình (*):")); f_lay.addWidget(self.in_expiry)

        # LƯỚI NÚT BẤM CRUD ĐÃ ĐƯỢC CẬP NHẬT
        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)
        self.btn_add = QPushButton("🟢 Kích Hoạt", styleSheet="background:#10B981; color:#0F172A;")
        self.btn_upd = QPushButton("🟡 Cập Nhật", styleSheet="background:#F59E0B; color:#0F172A;")
        self.btn_del = QPushButton("🔒 Khóa / Vô Hiệu", styleSheet="background:#EF4444; color:white;")
        self.btn_clr = QPushButton("Hủy Bỏ", styleSheet="background:#334155; color: white;")
        
        for b in [self.btn_add, self.btn_upd, self.btn_del, self.btn_clr]: b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.btn_add.clicked.connect(self.action_add_voucher)
        self.btn_upd.clicked.connect(self.action_update_voucher)
        self.btn_del.clicked.connect(self.action_disable_voucher)
        self.btn_clr.clicked.connect(self.clear_form_fields)
        
        btn_grid.addWidget(self.btn_add, 0, 0)
        btn_grid.addWidget(self.btn_upd, 0, 1)
        btn_grid.addWidget(self.btn_del, 1, 0)
        btn_grid.addWidget(self.btn_clr, 1, 1)
        f_lay.addLayout(btn_grid); f_lay.addStretch()

        # CỘT PHẢI (60%)
        right_lay = QVBoxLayout()
        right_lay.addWidget(QLabel("📊 CHƯƠNG TRÌNH ƯU ĐÃI TRÊN HỆ THỐNG", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold;"))
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Mã Code", "Giảm (%)", "Tối Đa", "Đã Dùng / Tổng", "Ngày Hết Hạn"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_row_selected)
        
        right_lay.addWidget(self.table)
        
        main_layout.addWidget(form_frame, 4)
        main_layout.addLayout(right_lay, 6)
        self.clear_form_fields()

    def load_vouchers_data(self):
        self.table.setRowCount(0)
        vouchers = self.service.get_all_vouchers()
        for r, v in enumerate(vouchers):
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(v['code']))
            self.table.setItem(r, 1, QTableWidgetItem(f"{float(v['discount_percent'])}%"))
            self.table.setItem(r, 2, QTableWidgetItem(f"{float(v['max_discount'] or 0):,.0f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{v['used_count']} / {v['usage_limit']}"))
            self.table.setItem(r, 4, QTableWidgetItem(str(v['expiry_date'])))

    def on_table_row_selected(self):
        """Bóc tách dữ liệu từ Bảng và nạp ngược lại lên Form"""
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            
            # Khóa mã Code không cho sửa
            self.selected_code = self.table.item(row, 0).text()
            self.in_code.setText(self.selected_code)
            self.in_code.setEnabled(False) 
            
            # Cắt bỏ dấu % để nạp lại vào input
            pct_str = self.table.item(row, 1).text().replace('%', '')
            self.in_discount.setText(pct_str)
            
            # Cắt bỏ dấu phẩy (,) để nạp lại vào input
            max_str = self.table.item(row, 2).text().replace(',', '')
            self.in_max_disc.setText(max_str)
            
            # Tách chuỗi "Đã dùng / Tổng" để lấy số lượng Tổng (limit)
            limit_str = self.table.item(row, 3).text().split(' / ')[1]
            self.in_limit.setText(limit_str)
            
            # Ngày hết hạn
            self.in_expiry.setText(self.table.item(row, 4).text())

            # Chuyển đổi trạng thái Nút bấm
            self.btn_add.setEnabled(False); self.btn_add.setStyleSheet("background:#334155; color:#64748B;")
            self.btn_upd.setEnabled(True)
            self.btn_del.setEnabled(True)

    def clear_form_fields(self):
        self.selected_code = None
        for w in [self.in_code, self.in_discount, self.in_max_disc, self.in_limit, self.in_expiry]: w.clear()
        self.in_code.setEnabled(True)
        self.table.clearSelection()
        
        self.btn_add.setEnabled(True); self.btn_add.setStyleSheet("background:#10B981; color:#0F172A;")
        self.btn_upd.setEnabled(False)
        self.btn_del.setEnabled(False)

    def action_add_voucher(self):
        code = self.in_code.text().strip()
        try:
            discount = float(self.in_discount.text().strip())
            max_disc = float(self.in_max_disc.text().strip())
            limit = int(self.in_limit.text().strip())
        except ValueError:
            return QMessageBox.warning(self, "Lỗi định dạng", "Tỷ lệ giảm, mức trần và giới hạn phải nhập số.")
            
        expiry = self.in_expiry.text().strip()
        success, msg = self.service.create_voucher(code, discount, max_disc, expiry, limit, self.current_user)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.load_vouchers_data(); self.clear_form_fields()
        else:
            QMessageBox.warning(self, "Lỗi nhập liệu", msg)

    def action_update_voucher(self):
        """Kích hoạt gọi hàm Sửa Voucher"""
        if not self.selected_code: return
        try:
            discount = float(self.in_discount.text().strip())
            max_disc = float(self.in_max_disc.text().strip())
            limit = int(self.in_limit.text().strip())
        except ValueError:
            return QMessageBox.warning(self, "Lỗi định dạng", "Tỷ lệ giảm, mức trần và giới hạn phải nhập số.")
            
        expiry = self.in_expiry.text().strip()
        success, msg = self.service.update_voucher(self.selected_code, discount, max_disc, expiry, limit, self.current_user)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.load_vouchers_data()
            self.clear_form_fields()
        else:
            QMessageBox.warning(self, "Lỗi", msg)

    def action_disable_voucher(self):
        if not self.selected_code: return
        confirm = QMessageBox.question(self, "Xác nhận", f"Bạn muốn khóa sớm / vô hiệu mã {self.selected_code}?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            success, msg = self.service.disable_voucher(self.selected_code, self.current_user)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_vouchers_data(); self.clear_form_fields()
            else:
                QMessageBox.warning(self, "Lỗi", msg)