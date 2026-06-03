# gui/views/admin_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QGridLayout, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from bll.admin_service import AdminService

class AdminScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.service = AdminService()
        self.current_selected_user_id = None
        self.setup_ui()
        self.load_users_data()

    def apply_role_permissions(self, user_obj):
        self.current_user = user_obj
        self.load_users_data()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: white; font-family: 'Segoe UI'; }
            QLineEdit, QComboBox { padding: 10px; border-radius: 6px; background: #1E293B; border: 1px solid #475569; color: white; font-size: 13px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #38BDF8; }
            QTableWidget { background: #1E293B; border-radius: 8px; border: 1px solid #334155; gridline-color: #334155; outline: none; }
            QHeaderView::section { background: #0F172A; color: #94A3B8; font-weight: bold; border: none; padding: 12px; text-align: left; }
            QTableWidget::item { padding: 8px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QPushButton { padding: 10px; border-radius: 6px; font-weight: bold; }
        """)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(24)

        # ==========================================
        # CỘT TRÁI (35%): FORM CẤP/SỬA TÀI KHOẢN
        # ==========================================
        form_frame = QFrame()
        form_frame.setFixedWidth(380)
        f_lay = QVBoxLayout(form_frame)
        f_lay.setContentsMargins(10, 0, 10, 0)
        
        f_lay.addWidget(QLabel("🛡️ QUẢN TRỊ TÀI KHOẢN", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold; margin-bottom:10px;"))
        
        self.in_username = QLineEdit()
        self.in_username.setPlaceholderText("Tên đăng nhập (Username)")
        
        self.in_password = QLineEdit()
        self.in_password.setPlaceholderText("Mật khẩu (Bỏ trống nếu giữ nguyên)")
        self.in_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.cb_role = QComboBox()
        self.cb_role.addItems(["ADMIN", "STAFF", "USER"])
        self.cb_role.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        f_lay.addWidget(QLabel("Tên đăng nhập (*):")); f_lay.addWidget(self.in_username)
        f_lay.addWidget(QLabel("Mật khẩu (*):")); f_lay.addWidget(self.in_password)
        f_lay.addWidget(QLabel("Quyền hạn (*):")); f_lay.addWidget(self.cb_role)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)
        self.btn_add = QPushButton("🟢 Cấp Tài Khoản", styleSheet="background:#10B981; color:#0F172A;")
        self.btn_upd = QPushButton("🟡 Cập Nhật", styleSheet="background:#F59E0B; color:#0F172A;")
        self.btn_del = QPushButton("🔴 Xóa Tài Khoản", styleSheet="background:#EF4444; color:white;")
        self.btn_clr = QPushButton("Hủy Bỏ", styleSheet="background:#334155; color: white;")
        
        for b in [self.btn_add, self.btn_upd, self.btn_del, self.btn_clr]: b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.btn_add.clicked.connect(self.action_add_user)
        self.btn_upd.clicked.connect(self.action_update_user)
        self.btn_del.clicked.connect(self.action_delete_user)
        self.btn_clr.clicked.connect(self.clear_form_fields)
        
        btn_grid.addWidget(self.btn_add, 0, 0)
        btn_grid.addWidget(self.btn_upd, 0, 1)
        btn_grid.addWidget(self.btn_del, 1, 0)
        btn_grid.addWidget(self.btn_clr, 1, 1)
        f_lay.addLayout(btn_grid); f_lay.addStretch()

        # ==========================================
        # CỘT PHẢI (65%): BẢNG DANH SÁCH NGƯỜI DÙNG
        # ==========================================
        right_frame = QFrame()
        right_lay = QVBoxLayout(right_frame)
        right_lay.setContentsMargins(0, 0, 0, 0)
        
        search_lay = QHBoxLayout()
        search_lay.addWidget(QLabel("📋 DANH SÁCH NGƯỜI DÙNG HỆ THỐNG", styleSheet="font-size:18px; color:#38BDF8; font-weight:bold;"))
        search_lay.addStretch()
        
        self.in_search = QLineEdit()
        self.in_search.setPlaceholderText("🔍 Tìm kiếm Username/ID...")
        self.in_search.setFixedWidth(250)
        self.in_search.textChanged.connect(self.load_users_data)
        search_lay.addWidget(self.in_search)
        right_lay.addLayout(search_lay)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Tên Đăng Nhập", "Quyền Hạn", "Ngày Tạo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_table_row_selected)
        right_lay.addWidget(self.table)
        
        main_layout.addWidget(form_frame, 3)
        main_layout.addWidget(right_frame, 7)
        
        self.clear_form_fields()

    # ==========================================
    # CÁC HÀM XỬ LÝ LOGIC
    # ==========================================
    def load_users_data(self):
        keyword = self.in_search.text().strip()
        users = self.service.search_users(keyword)
        self.table.setRowCount(0)
        for row_idx, user in enumerate(users):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(user['user_id'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(user['username']))
            
            # Tô màu phân biệt Quyền hạn cho dễ nhìn
            role_item = QTableWidgetItem(user['role'])
            if user['role'] == 'ADMIN': role_item.setForeground(Qt.GlobalColor.red)
            elif user['role'] == 'STAFF': role_item.setForeground(Qt.GlobalColor.yellow)
            else: role_item.setForeground(Qt.GlobalColor.green)
            
            self.table.setItem(row_idx, 2, role_item)
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(user['created_at'])))

    def on_table_row_selected(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.current_selected_user_id = int(self.table.item(row, 0).text())
            self.in_username.setText(self.table.item(row, 1).text())
            self.in_username.setEnabled(False) # Username là khóa định danh, không cho sửa
            self.cb_role.setCurrentText(self.table.item(row, 2).text())
            self.in_password.clear() # Để trống, chỉ nhập khi muốn đổi pass
            
            self.btn_add.setEnabled(False); self.btn_add.setStyleSheet("background:#334155; color:#64748B;")
            self.btn_upd.setEnabled(True)
            self.btn_del.setEnabled(True)

    def clear_form_fields(self):
        self.current_selected_user_id = None
        self.in_username.clear()
        self.in_password.clear()
        self.cb_role.setCurrentIndex(0)
        self.in_username.setEnabled(True)
        self.table.clearSelection()
        
        self.btn_add.setEnabled(True); self.btn_add.setStyleSheet("background:#10B981; color:#0F172A;")
        self.btn_upd.setEnabled(False)
        self.btn_del.setEnabled(False)

    def action_add_user(self):
        username = self.in_username.text().strip()
        password = self.in_password.text().strip()
        role = self.cb_role.currentText()
        
        success, message = self.service.create_user(username, password, role, self.current_user)
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.load_users_data()
            self.clear_form_fields()
        else:
            QMessageBox.warning(self, "Lỗi", message)

    def action_update_user(self):
        if not self.current_selected_user_id: return
        password = self.in_password.text().strip()
        role = self.cb_role.currentText()
        
        success, message = self.service.update_user(self.current_selected_user_id, password, role, self.current_user)
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.load_users_data()
            self.clear_form_fields()
        else:
            QMessageBox.warning(self, "Lỗi", message)

    def action_delete_user(self):
        if not self.current_selected_user_id: return
        confirm = QMessageBox.question(self, "Xác nhận", f"Bạn có chắc chắn muốn xóa tài khoản này vĩnh viễn?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.service.delete_user(self.current_selected_user_id, self.current_user)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.load_users_data()
                self.clear_form_fields()
            else:
                QMessageBox.warning(self, "Lỗi", message)