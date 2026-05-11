# gui/theme.py

SAAS_DARK_THEME = """
    /* =========================================================
       NGUYÊN TẮC MÀU 60-30-10
       60% Nền (Background): #0F172A
       30% Khối (Surface/Card): #1E293B
       10% Điểm nhấn (Accent): #3B82F6 (Xanh), #10B981 (Xanh lá), #EF4444 (Đỏ)
       ========================================================= */
       
    * {
        font-family: 'Inter', 'Segoe UI', sans-serif;
        color: #E2E8F0;
    }

    /* 60% NỀN CHÍNH */
    QMainWindow, #MainBackground, QStackedWidget, #ContentArea {
        background-color: #0F172A;
    }

    /* 30% KHỐI & BẢNG ĐIỀU KHIỂN */
    #HeaderFrame, #SidebarFrame {
        background-color: #1E293B;
        border: none;
    }
    #HeaderFrame { border-bottom: 1px solid #334155; }
    #SidebarFrame { border-right: 1px solid #334155; }
    
    #SidebarLogo {
        color: #F8FAFC;
        font-size: 20px;
        font-weight: 800;
        padding: 24px 16px; /* Grid: 24, 16 */
    }

    /* CARDS & GROUPBOX (GRID 8-POINT) */
    #SaaSCard, QGroupBox {
        background-color: #1E293B;
        border-radius: 8px; /* Grid: 8 */
        border: 1px solid #334155;
        margin-top: 16px;   /* Grid: 16 */
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;     /* Grid: 8 */
        color: #94A3B8;
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* =========================================================
       NÚT BẤM (BUTTONS) - ÁP DỤNG 8-POINT GRID
       Padding chuẩn: 8px dọc, 16px ngang
       ========================================================= */
    QPushButton {
        background-color: #334155;
        color: #F8FAFC;
        border-radius: 8px;
        padding: 8px 16px; /* Grid: 8, 16 */
        font-weight: bold;
        border: none;
    }
    QPushButton:hover { background-color: #475569; }
    
    /* 10% ĐIỂM NHẤN (ACCENT COLORS) */
    QPushButton#BtnPrimary { background-color: #3B82F6; color: white; }
    QPushButton#BtnPrimary:hover { background-color: #2563EB; }
    
    QPushButton#BtnSuccess { background-color: #10B981; color: white; }
    QPushButton#BtnSuccess:hover { background-color: #059669; }
    
    QPushButton#BtnDanger { background-color: #EF4444; color: white; }
    QPushButton#BtnDanger:hover { background-color: #DC2626; }
    
    QPushButton#BtnOutline {
        background-color: transparent;
        color: #3B82F6;
        border: 1px solid #3B82F6;
    }
    QPushButton#BtnOutline:hover { background-color: rgba(59, 130, 246, 0.1); }

    /* MENU SIDEBAR BUTTONS */
    QPushButton#SidebarMenuBtn {
        background-color: transparent;
        color: #94A3B8;
        text-align: left;
        padding: 16px 24px; /* Grid: 16, 24 */
        font-size: 14px;
        font-weight: bold;
        border-radius: 0px;
        border-left: 4px solid transparent;
    }
    QPushButton#SidebarMenuBtn:hover {
        background-color: rgba(255, 255, 255, 0.03);
        color: #E2E8F0;
    }
    QPushButton#SidebarMenuBtn:checked {
        background-color: rgba(59, 130, 246, 0.1); 
        color: #3B82F6; 
        border-left: 4px solid #3B82F6;
    }

    /* INPUTS & COMBOBOX */
    QLineEdit, QComboBox, QDateEdit, QDateTimeEdit {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px; /* Grid: 8 */
        padding: 8px 16px;  /* Grid: 8, 16 */
        color: #F8FAFC;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus {
        border: 1px solid #3B82F6;
    }

    /* BẢNG WIDGET (TABLE) */
    QTableWidget {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        gridline-color: #334155;
        selection-background-color: rgba(59, 130, 246, 0.2);
    }
    QHeaderView::section {
        background-color: #0F172A;
        color: #94A3B8;
        padding: 12px 16px; /* Grid: 12, 16 */
        font-weight: bold;
        border: none;
        border-bottom: 2px solid #334155;
    }

    /* =========================================================
       CUSTOM DIALOG (QMESSAGEBOX) - GIAO DIỆN HIỆN ĐẠI
       ========================================================= */
    QMessageBox {
        background-color: #1E293B; /* Tone màu 30% Surface */
        border: 1px solid #334155;
    }
    QMessageBox QLabel {
        color: #F8FAFC;
        font-size: 14px;
        padding: 8px 0px; /* Grid: 8 */
    }
    /* Style lại nút bấm trong hộp thoại cho rộng rãi dễ bấm */
    QMessageBox QPushButton {
        min-width: 88px;
        min-height: 24px;
        padding: 8px 16px;
    }
"""