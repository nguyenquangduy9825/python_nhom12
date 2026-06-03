# gui/views/dashboard_view.py
import pandas as pd
import numpy as np
import csv
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QDateEdit, QGridLayout, 
                             QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QCursor, QTextDocument
from PyQt6.QtPrintSupport import QPrinter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from bll.admin_service import AdminService

class DashboardScreen(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.admin_service = AdminService()
        
        # Biến lưu trữ dữ liệu hiện tại để Export
        self.current_rev_data = []
        self.current_route_data = []
        
        self.setup_ui()
        self.load_report_data()

    def apply_role_permissions(self, user_obj):
        self.current_user = user_obj
        self.load_report_data()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
            QFrame#Card { background-color: #1E293B; border-radius: 12px; border: 1px solid #334155; }
            QLabel#ValueLabel { font-size: 28px; font-weight: 900; color: #10B981; }
            QLabel#TitleLabel { font-size: 14px; color: #94A3B8; font-weight: bold; }
            QDateEdit { padding: 8px; border-radius: 6px; background-color: #0F172A; border: 1px solid #475569; color: white; }
            QPushButton { background-color: #38BDF8; color: #0F172A; font-weight: bold; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background-color: #0284C7; color: white; }
            QPushButton#BtnExport { background-color: transparent; border: 1px solid #38BDF8; color: #38BDF8; }
            QPushButton#BtnExport:hover { background-color: #38BDF8; color: #0F172A; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)

        # 1. BỘ LỌC THỜI GIAN VÀ CÔNG CỤ EXPORT
        filter_card = QFrame(); filter_card.setObjectName("Card")
        filter_lay = QHBoxLayout(filter_card)
        filter_lay.setContentsMargins(16, 16, 16, 16)
        
        filter_lay.addWidget(QLabel("📅 LỌC BÁO CÁO TỪ:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        filter_lay.addWidget(self.date_from)
        
        filter_lay.addWidget(QLabel("ĐẾN:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        filter_lay.addWidget(self.date_to)
        
        btn_filter = QPushButton("Áp Dụng Lọc")
        btn_filter.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_filter.clicked.connect(self.load_report_data)
        filter_lay.addWidget(btn_filter)
        
        filter_lay.addStretch()
        
        # ĐÃ THÊM: Nút Xuất Báo Cáo
        self.btn_export_csv = QPushButton("📊 Xuất CSV")
        self.btn_export_csv.setObjectName("BtnExport")
        self.btn_export_csv.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_csv.clicked.connect(self.export_to_csv)
        
        self.btn_export_pdf = QPushButton("📄 Xuất PDF")
        self.btn_export_pdf.setObjectName("BtnExport")
        self.btn_export_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_export_pdf.clicked.connect(self.export_to_pdf)
        
        filter_lay.addWidget(self.btn_export_csv)
        filter_lay.addWidget(self.btn_export_pdf)
        
        main_layout.addWidget(filter_card)

        # 2. KHU VỰC TỔNG QUAN (KPI CARDS)
        kpi_lay = QHBoxLayout(); kpi_lay.setSpacing(24)
        
        self.card_rev = QFrame(); self.card_rev.setObjectName("Card")
        lay_rev = QVBoxLayout(self.card_rev)
        lay_rev.addWidget(QLabel("TỔNG DOANH THU KỲ", objectName="TitleLabel"))
        self.lbl_total_rev = QLabel("0 ₫", objectName="ValueLabel")
        lay_rev.addWidget(self.lbl_total_rev)
        kpi_lay.addWidget(self.card_rev)

        self.card_tkt = QFrame(); self.card_tkt.setObjectName("Card")
        lay_tkt = QVBoxLayout(self.card_tkt)
        lay_tkt.addWidget(QLabel("TỔNG VÉ ĐÃ BÁN", objectName="TitleLabel"))
        self.lbl_total_tkt = QLabel("0", objectName="ValueLabel")
        self.lbl_total_tkt.setStyleSheet("font-size: 28px; font-weight: 900; color: #38BDF8;")
        lay_tkt.addWidget(self.lbl_total_tkt)
        kpi_lay.addWidget(self.card_tkt)

        main_layout.addLayout(kpi_lay)

        # 3. KHU VỰC BIỂU ĐỒ (MATPLOTLIB)
        chart_lay = QHBoxLayout(); chart_lay.setSpacing(24)

        self.fig_rev = Figure(figsize=(6, 4), dpi=100); self.fig_rev.patch.set_facecolor('#1E293B')
        self.canvas_rev = FigureCanvas(self.fig_rev)
        chart_card_1 = QFrame(); chart_card_1.setObjectName("Card")
        lay_c1 = QVBoxLayout(chart_card_1); lay_c1.addWidget(self.canvas_rev)
        chart_lay.addWidget(chart_card_1, stretch=2)

        self.fig_pie = Figure(figsize=(4, 4), dpi=100); self.fig_pie.patch.set_facecolor('#1E293B')
        self.canvas_pie = FigureCanvas(self.fig_pie)
        chart_card_2 = QFrame(); chart_card_2.setObjectName("Card")
        lay_c2 = QVBoxLayout(chart_card_2); lay_c2.addWidget(self.canvas_pie)
        chart_lay.addWidget(chart_card_2, stretch=1)

        main_layout.addLayout(chart_lay)

    def load_report_data(self):
        f_date = self.date_from.date().toString("yyyy-MM-dd")
        t_date = self.date_to.date().toString("yyyy-MM-dd")

        ok_rev, rev_data = self.admin_service.get_revenue(f_date, t_date)
        ok_route, route_data = self.admin_service.get_top_routes()

        if not ok_rev or not ok_route: return
        
        # Lưu trữ lại để dành cho việc Export
        self.current_rev_data = rev_data
        self.current_route_data = route_data

        # VẼ BIỂU ĐỒ DOANH THU
        self.fig_rev.clear()
        ax1 = self.fig_rev.add_subplot(111)
        ax1.set_facecolor('#1E293B')
        ax1.tick_params(colors='white')
        ax1.spines['bottom'].set_color('#475569'); ax1.spines['left'].set_color('#475569')
        ax1.spines['top'].set_color('#1E293B'); ax1.spines['right'].set_color('#1E293B')

        self.total_rev_val = 0
        if rev_data:
            df_rev = pd.DataFrame(rev_data)
            df_rev['date'] = pd.to_datetime(df_rev['date'])
            df_rev['total_revenue'] = df_rev['total_revenue'].astype(float)
            self.total_rev_val = df_rev['total_revenue'].sum()

            ax1.plot(df_rev['date'], df_rev['total_revenue'], color='#10B981', marker='o', linewidth=2, markersize=6)
            ax1.fill_between(df_rev['date'], df_rev['total_revenue'], color='#10B981', alpha=0.2)
            ax1.set_title('Xu hướng Doanh thu (VNĐ)', color='white', pad=15)
            self.fig_rev.autofmt_xdate() 
        else:
            ax1.text(0.5, 0.5, 'Không có dữ liệu', color='white', ha='center', va='center')
        
        self.lbl_total_rev.setText(f"{self.total_rev_val:,.0f} ₫")
        self.canvas_rev.draw()

        # VẼ BIỂU ĐỒ TRÒN TOP TUYẾN BAY
        self.fig_pie.clear()
        ax2 = self.fig_pie.add_subplot(111)
        
        self.total_tkt_val = 0
        if route_data:
            df_route = pd.DataFrame(route_data)
            df_route['route_name'] = df_route['departure_code'] + "->" + df_route['arrival_code']
            df_route['total_tickets'] = df_route['total_tickets'].astype(int)
            self.total_tkt_val = df_route['total_tickets'].sum()

            if len(df_route) > 5:
                top5 = df_route.head(5)
                others = pd.DataFrame([{'route_name': 'Khác', 'total_tickets': df_route.iloc[5:]['total_tickets'].sum()}])
                df_route = pd.concat([top5, others], ignore_index=True)

            colors = ['#38BDF8', '#818CF8', '#34D399', '#FBBF24', '#F87171', '#94A3B8']
            ax2.pie(
                df_route['total_tickets'], labels=df_route['route_name'], autopct='%1.1f%%',
                colors=colors, startangle=90, textprops={'color': "white"}
            )
            ax2.set_title('Top Tuyến Bay Hot Nhất', color='white', pad=15)
        else:
            ax2.text(0.5, 0.5, 'Không có dữ liệu', color='white', ha='center', va='center')

        self.lbl_total_tkt.setText(f"{self.total_tkt_val:,}")
        self.canvas_pie.draw()

    # ==========================================
    # CÁC HÀM XUẤT DỮ LIỆU BÁO CÁO
    # ==========================================
    def export_to_csv(self):
        if not self.current_rev_data:
            return QMessageBox.warning(self, "Lỗi", "Không có dữ liệu doanh thu để xuất!")
            
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file CSV", "Bao_Cao_Doanh_Thu.csv", "CSV Files (*.csv)")
        if path:
            try:
                # Sử dụng sức mạnh của Pandas để xuất file 1 dòng lệnh
                df = pd.DataFrame(self.current_rev_data)
                df.columns = ["Ngày Giao Dịch", "Doanh Thu (VNĐ)"]
                df.to_csv(path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "Thành công", f"Đã xuất dữ liệu thành công tại:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {e}")

    def export_to_pdf(self):
        if not self.current_rev_data:
            return QMessageBox.warning(self, "Lỗi", "Không có dữ liệu báo cáo để xuất!")
            
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file PDF", "Bao_Cao_Tong_Hop.pdf", "PDF Files (*.pdf)")
        if not path: return
        
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(path)
            
            f_date = self.date_from.date().toString("dd/MM/yyyy")
            t_date = self.date_to.date().toString("dd/MM/yyyy")
            
            html = f"""
            <h1 style='text-align:center; color:#1E293B;'>BÁO CÁO KẾT QUẢ KINH DOANH HÀNG KHÔNG</h1>
            <p style='text-align:center; color:#64748B;'>Kỳ báo cáo: Từ {f_date} đến {t_date}</p>
            <hr>
            <h2>1. TỔNG QUAN HIỆU QUẢ HOẠT ĐỘNG</h2>
            <ul>
                <li><b>Tổng vé đã xuất:</b> {self.total_tkt_val:,} vé</li>
                <li><b>Tổng doanh thu đạt được:</b> {self.total_rev_val:,.0f} VNĐ</li>
            </ul>
            <h2>2. CHI TIẾT DOANH THU THEO NGÀY</h2>
            <table border='1' cellspacing='0' cellpadding='6' width='100%' style='border-collapse: collapse;'>
                <tr style='background-color:#E2E8F0;'>
                    <th>Ngày Giao Dịch</th>
                    <th>Doanh Thu (VNĐ)</th>
                </tr>
            """
            for row in self.current_rev_data:
                date_str = row['date'].strftime("%d/%m/%Y") if hasattr(row['date'], 'strftime') else str(row['date'])
                rev_val = f"{float(row['total_revenue']):,.0f}"
                html += f"<tr><td align='center'>{date_str}</td><td align='right'>{rev_val}</td></tr>"
                
            html += "</table>"
            
            doc = QTextDocument()
            doc.setHtml(html)
            doc.print(printer)
            QMessageBox.information(self, "Thành công", f"Báo cáo PDF đã được lưu tại:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất PDF", f"Đã xảy ra lỗi: {e}")