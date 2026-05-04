# gui/views/dashboard_view.py
import pandas as pd
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QGroupBox, QDateEdit, QFileDialog, QFrame)
from PyQt6.QtCore import Qt, QDate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from bll.admin_service import AdminService
from gui.animations import AnimatedHoverCard

class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.admin_service = AdminService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24) 
        layout.setSpacing(24)

        # --- BỘ LỌC HEADER ---
        filter_layout = QHBoxLayout()
        
        self.date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_from.setCalendarPopup(True); self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setCalendarPopup(True); self.date_to.setDisplayFormat("yyyy-MM-dd")
        
        btn_filter = QPushButton("Lọc Dữ Liệu")
        btn_filter.setObjectName("BtnPrimary")
        btn_filter.clicked.connect(self.load_report_data)
        
        filter_layout.addWidget(QLabel("Từ ngày:")); filter_layout.addWidget(self.date_from)
        filter_layout.addSpacing(16)
        filter_layout.addWidget(QLabel("Đến ngày:")); filter_layout.addWidget(self.date_to)
        filter_layout.addSpacing(16)
        filter_layout.addWidget(btn_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # --- CARDS TỔNG QUAN (KPIs) ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24) 
        
        self.lbl_total_revenue = self.create_card("TỔNG DOANH THU", "0 VND", "#10B981", cards_layout)
        self.lbl_total_tickets = self.create_card("TỔNG VÉ ĐÃ BÁN", "0 vé", "#F59E0B", cards_layout)
        layout.addLayout(cards_layout)

        # --- BIỂU ĐỒ & BẢNG TOP ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # 1. Biểu đồ Matplotlib
        chart_card = AnimatedHoverCard()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 24, 16, 16)
        
        lbl_chart = QLabel("Biểu đồ Doanh thu")
        lbl_chart.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 8px;")
        chart_layout.addWidget(lbl_chart)

        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.figure.patch.set_facecolor('#1E293B') 
        self.ax.set_facecolor('#1E293B')
        self.ax.tick_params(colors='#94A3B8') 
        
        for spine in self.ax.spines.values():
            spine.set_color('#334155')

        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        content_layout.addWidget(chart_card, stretch=5)

        # 2. Bảng Top Tuyến Bay
        table_card = AnimatedHoverCard()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 24, 16, 16)
        
        lbl_table = QLabel("Top Tuyến Bay Bán Chạy")
        lbl_table.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 8px;")
        table_layout.addWidget(lbl_table)

        self.table_top = QTableWidget(0, 3)
        self.table_top.setHorizontalHeaderLabels(["Điểm Đi", "Điểm Đến", "Số Vé"])
        self.table_top.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_top.verticalHeader().setVisible(False)
        self.table_top.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_top.setShowGrid(False) 
        table_layout.addWidget(self.table_top)
        
        # Nút Export
        btn_export_layout = QHBoxLayout()
        btn_excel = QPushButton("📗 Xuất Excel")
        btn_excel.setObjectName("BtnSuccess")
        btn_excel.clicked.connect(self.export_excel)
        
        btn_pdf = QPushButton("📕 Xuất PDF")
        btn_pdf.setObjectName("BtnDanger")
        btn_pdf.clicked.connect(self.export_pdf)
        
        btn_export_layout.addWidget(btn_excel); btn_export_layout.addWidget(btn_pdf)
        table_layout.addLayout(btn_export_layout)
        
        content_layout.addWidget(table_card, stretch=3) 
        layout.addLayout(content_layout, stretch=1)

    def create_card(self, title, value, accent_color, parent_layout):
        card = AnimatedHoverCard()
        card.setStyleSheet(f"border-left: 4px solid {accent_color};")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: bold;")
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {accent_color}; font-size: 28px; font-weight: bold;")
        
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_value)
        card_layout.addStretch()
        
        parent_layout.addWidget(card)
        return lbl_value

    def load_report_data(self):
        from_date = self.date_from.date().toString("yyyy-MM-dd")
        to_date = self.date_to.date().toString("yyyy-MM-dd")

        success, revenue_data = self.admin_service.get_revenue(from_date, to_date)
        if success and revenue_data:
            dates = [str(item['date']) for item in revenue_data]
            revenues = [float(item['total_revenue']) for item in revenue_data]
            
            self.lbl_total_revenue.setText(f"{sum(revenues):,.0f} VND")
            
            self.ax.clear()
            self.ax.plot(dates, revenues, color='#3B82F6', marker='o', markersize=6, linewidth=2.5)
            self.ax.grid(True, linestyle='--', color='#334155', alpha=0.5)
            self.figure.autofmt_xdate()
            self.canvas.draw()
            self.current_revenue_data = revenue_data 
        else:
            self.ax.clear(); self.canvas.draw()
            self.lbl_total_revenue.setText("0 VND")
            self.current_revenue_data = []

        top_routes = self.admin_service.get_top_routes()
        self.table_top.setRowCount(0)
        total_tix = 0
        for row, item in enumerate(top_routes):
            self.table_top.insertRow(row)
            self.table_top.setItem(row, 0, QTableWidgetItem(item['departure_code']))
            self.table_top.setItem(row, 1, QTableWidgetItem(item['arrival_code']))
            self.table_top.setItem(row, 2, QTableWidgetItem(str(item['total_tickets'])))
            total_tix += item['total_tickets']
            
        self.lbl_total_tickets.setText(f"{total_tix} vé")

    def export_excel(self):
        if not hasattr(self, 'current_revenue_data') or not self.current_revenue_data:
            return QMessageBox.warning(self, "Lỗi", "Không có dữ liệu để xuất!")
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file Excel", "BaoCao_DoanhThu.xlsx", "Excel Files (*.xlsx)")
        if path:
            try:
                pd.DataFrame(self.current_revenue_data).to_excel(path, index=False)
                QMessageBox.information(self, "Thành công", f"Đã xuất dữ liệu Excel ra:\\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file Excel: {e}")

    def export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu biểu đồ PDF", "BaoCao_BieuDo.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                self.figure.savefig(path, format='pdf', facecolor='#1E293B')
                QMessageBox.information(self, "Thành công", f"Đã lưu biểu đồ thành PDF tại:\\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể lưu file PDF: {e}")

    def apply_role_permissions(self, user):
        if user.role.upper() == 'ADMIN':
            self.load_report_data()