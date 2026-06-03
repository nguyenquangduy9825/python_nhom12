# gui/views/customer_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QLineEdit, QHeaderView, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QColor, QFont
from bll.booking_service import BookingService

class CustomerScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.service = BookingService()
        self.setup_ui()

    def apply_role_permissions(self, user_obj):
        """Chỉ admin mới được hủy vé"""
        self.current_user = user_obj
        role = getattr(user_obj, 'role', '') if not isinstance(user_obj, dict) else user_obj.get('role', '')
        
        if role.upper() != 'ADMIN':
            self.btn_cancel.setVisible(False)
        else:
            self.btn_cancel.setVisible(True)

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
            QFrame#Card { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QLineEdit { padding: 12px; border-radius: 8px; background-color: #0F172A; border: 1px solid #475569; color: white; font-size: 14px; }
            QLineEdit:focus { border: 1px solid #38BDF8; }
            QPushButton { font-weight: bold; border-radius: 8px; padding: 12px 20px; font-size: 14px; }
            QPushButton#BtnSearch { background-color: #38BDF8; color: #0F172A; }
            QPushButton#BtnSearch:hover { background-color: #0284C7; color: white; }
            QPushButton#BtnCancel { background-color: transparent; border: 2px solid #EF4444; color: #EF4444; }
            QPushButton#BtnCancel:hover { background-color: #EF4444; color: white; }
            
            /* Table Styling */
            QTableWidget { background-color: transparent; border: none; gridline-color: transparent; selection-background-color: rgba(56,189,248,0.2); selection-color: #38BDF8; outline: none; }
            QHeaderView::section { background-color: #0F172A; color: #94A3B8; padding: 12px; font-weight: bold; border: none; border-bottom: 2px solid #334155; text-align: left; }
            QTableWidget::item { padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Tiêu đề
        lbl_title = QLabel("📋 QUẢN LÝ DANH SÁCH HÀNH KHÁCH")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: 900; color: #38BDF8;")
        layout.addWidget(lbl_title)

        # Thanh Công cụ & Tìm kiếm
        toolbar_card = QFrame(); toolbar_card.setObjectName("Card")
        toolbar_lay = QHBoxLayout(toolbar_card)
        toolbar_lay.setContentsMargins(20, 20, 20, 20)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Tra cứu nhanh theo Tên, SĐT, CCCD, Mã vé, Mã chuyến bay...")
        self.txt_search.returnPressed.connect(self.load_data)
        
        btn_search = QPushButton("Tìm Kiếm")
        btn_search.setObjectName("BtnSearch")
        btn_search.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_search.clicked.connect(self.load_data)
        
        toolbar_lay.addWidget(self.txt_search, stretch=4)
        toolbar_lay.addWidget(btn_search, stretch=1)
        layout.addWidget(toolbar_card)

        # Vùng chứa Bảng Dữ liệu
        table_card = QFrame(); table_card.setObjectName("Card")
        table_lay = QVBoxLayout(table_card)
        table_lay.setContentsMargins(10, 10, 10, 10)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Mã Vé", "Hành Khách", "Số ĐT", "CCCD", "Chuyến Bay", "Ghế (Hạng)", "Trạng Thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID cho vừa nội dung
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        table_lay.addWidget(self.table)
        layout.addWidget(table_card)

        # Khu vực Nút Hành động
        actions = QHBoxLayout()
        self.btn_cancel = QPushButton("❌ Hủy Vé Đã Chọn")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self.handle_cancel)
        self.btn_cancel.setVisible(False) # Ẩn mặc định

        actions.addStretch(); actions.addWidget(self.btn_cancel)
        layout.addLayout(actions)

        self.load_data()

    def load_data(self):
        """Lấy dữ liệu từ BLL và render lên bảng kèm màu sắc"""
        keyword = self.txt_search.text().strip()
        data = self.service.search_passengers(keyword)
        self.table.setRowCount(0)
        
        for r, item in enumerate(data):
            self.table.insertRow(r)
            
            # Đổ text thường
            self.table.setItem(r, 0, QTableWidgetItem(f"TKT-{item['ticket_id']}"))
            self.table.setItem(r, 1, QTableWidgetItem(item['full_name']))
            self.table.setItem(r, 2, QTableWidgetItem(item['phone']))
            self.table.setItem(r, 3, QTableWidgetItem(item['id_card']))
            self.table.setItem(r, 4, QTableWidgetItem(item['flight_number']))
            self.table.setItem(r, 5, QTableWidgetItem(f"{item['seat_number']} ({item['ticket_class']})"))
            
            # Tô màu Badge Trạng Thái
            status = item['ticket_status']
            color = "#10B981" if status == 'BOOKED' else "#F59E0B" if status == 'HELD' else "#EF4444"
            
            lbl_status = QTableWidgetItem(status)
            lbl_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl_status.setForeground(QColor(color))
            lbl_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 6, lbl_status)

    def handle_cancel(self):
        """Gọi BLL hủy vé, BLL sẽ gọi DAL có Transaction nhả ghế"""
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Lỗi", "Vui lòng click chọn một dòng vé trên bảng để hủy!")
        
        # Parse lại ID (Bỏ chữ TKT-)
        ticket_id = int(self.table.item(row, 0).text().replace("TKT-", ""))
        status = self.table.item(row, 6).text()
        
        if status == 'CANCELLED':
            return QMessageBox.information(self, "Thông báo", "Vé này đã bị hủy từ trước.")
            
        if QMessageBox.question(self, "Xác nhận Hủy", "Bạn có chắc chắn muốn hủy vé này?\nHệ thống sẽ tự động hoàn trả ghế trống.", 
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                                
            role = getattr(self.current_user, 'role', '') if not isinstance(self.current_user, dict) else self.current_user.get('role', '')
            
            success, msg = self.service.cancel_ticket(ticket_id, role.upper())
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data() # Reload lại bảng
            else:
                QMessageBox.critical(self, "Lỗi", msg)