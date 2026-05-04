# gui/theme.py

SAAS_DARK_THEME = """
    /* ==========================================
       BẢNG MÀU CHUNG (MIDNIGHT BLUE THEME)
       ========================================== */
    QWidget {
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 14px;
        color: #E2E8F0; 
    }

    /* VÙNG NỘI DUNG CHÍNH */
    QMainWindow, QStackedWidget, #ContentArea {
        background-color: #0F172A;
    }

    /* HEADER & SIDEBAR */
    #HeaderFrame {
        background-color: #1E293B;
        border-bottom: 1px solid #334155;
    }
    #SidebarFrame {
        background-color: #1E293B;
        border-right: 1px solid #334155;
    }
    #SidebarLogo {
        color: #F8FAFC;
        font-size: 20px;
        font-weight: bold;
        padding: 24px 16px;
    }
    
    /* NÚT BẤM SIDEBAR */
    QPushButton#SidebarMenuBtn {
        background-color: transparent;
        color: #94A3B8;
        text-align: left;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: bold;
        border: none;
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

    /* CARDS & GROUPBOX */
    #SaaSCard, QGroupBox {
        background-color: #1E293B;
        border-radius: 8px;
        border: 1px solid #334155;
        margin-top: 16px; 
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: #94A3B8;
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* COMBOBOX & INPUTS */
    QLineEdit, QComboBox, QDateEdit, QDateTimeEdit {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 8px 12px;
        color: #F8FAFC;
    }
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus {
        border: 1px solid #3B82F6;
        background-color: #0F172A;
    }
    
    /* KHUNG PASSWORD CÓ NÚT MẮT */
    #PasswordFrame {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    #PasswordFrame:focus-within {
        border: 1px solid #3B82F6;
        background-color: #1E293B;
    }
    #PasswordFrame QLineEdit {
        border: none;
        background: transparent;
        padding: 10px 8px 10px 16px;
    }

    /* BUTTONS TỔNG QUÁT */
    QPushButton {
        background-color: #334155;
        color: #F8FAFC;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover { background-color: #475569; }
    
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

    QPushButton#BtnLink {
        background-color: transparent;
        color: #3B82F6;
        padding: 0px;
        text-align: left;
    }
    QPushButton#BtnLink:hover { text-decoration: underline; color: #60A5FA; }

    /* BẢNG WIDGET (TABLE) */
    QTableWidget {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        gridline-color: #334155;
        color: #E2E8F0;
        selection-background-color: rgba(59, 130, 246, 0.2);
        selection-color: #F8FAFC;
    }
    QTableWidget::item {
        padding: 4px;
        border-bottom: 1px solid #334155;
    }
    QHeaderView::section {
        background-color: #0F172A;
        color: #94A3B8;
        padding: 12px 8px;
        font-weight: bold;
        border: none;
        border-bottom: 2px solid #334155;
        border-right: 1px solid #334155;
    }
    QScrollBar:vertical {
        background: #0F172A;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #334155;
        min-height: 20px;
        border-radius: 5px;
    }

    /* QTABWIDGET (LÀM ĐẸP CÁC TAB ADMIN) */
    QTabWidget::pane {
        border: 1px solid #334155;
        border-radius: 8px;
        background-color: #1E293B;
        margin-top: -1px;
    }
    QTabBar::tab {
        background-color: #0F172A;
        color: #94A3B8;
        padding: 10px 20px;
        border: 1px solid #334155;
        border-bottom: none;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 4px;
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: #3B82F6;
        color: white;
        border: 1px solid #3B82F6;
    }
    QTabBar::tab:hover:!selected {
        background-color: #1E293B;
    }
"""