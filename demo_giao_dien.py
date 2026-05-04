import warnings
# Tắt cảnh báo lỗi thời của thư viện AI để Terminal gọn gàng
warnings.filterwarnings("ignore", category=UserWarning, module="face_recognition_models")
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

import sys
import cv2
import face_recognition
import hashlib
import mysql.connector
from mysql.connector import Error
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QTableWidget, QTableWidgetItem, 
                             QComboBox, QHeaderView, QFrame, QMessageBox, QDialog, QFormLayout, QSpinBox, QDateTimeEdit)
from PyQt6.QtCore import Qt, QTimer, QDateTime
import qdarktheme

# =======================================================
# BACKEND 1: QUẢN LÝ DATABASE (OOP + BẢO MẬT USER)
# =======================================================
class DatabaseManager:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = "Dat1234566" 
        self.database = "FlightAgency"
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("✅ Đã kết nối thành công tới MySQL!")
            self.create_user_table_if_not_exists()
        except Error as e:
            print(f"❌ Lỗi kết nối Database: {e}")

    def create_user_table_if_not_exists(self):
        """Tự động tạo bảng Users nếu CSDL chưa có để tránh lỗi sập App"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('Admin', 'Staff') DEFAULT 'Staff',
                    face_encoding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            
            # Tạo sẵn 1 tài khoản Admin mặc định nếu bảng trống
            cursor.execute("SELECT COUNT(*) FROM Users")
            if cursor.fetchone()[0] == 0:
                self.register_user('admin', 'admin123', 'Admin')
        except Error as e:
            print(f"Lỗi tạo bảng Users: {e}")

    # --- NGHIỆP VỤ BẢO MẬT & TÀI KHOẢN ---
    def hash_password(self, password):
        """Băm mật khẩu 1 chiều bằng SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, role="Staff"):
        try:
            cursor = self.conn.cursor()
            hashed_pw = self.hash_password(password)
            cursor.execute("INSERT INTO Users (username, password_hash, role) VALUES (%s, %s, %s)", (username, hashed_pw, role))
            self.conn.commit()
            return True, "Đăng ký thành công!"
        except Error as e:
            return False, f"Tài khoản đã tồn tại hoặc lỗi CSDL!"

    def verify_password_login(self, username, password):
        try:
            cursor = self.conn.cursor(dictionary=True)
            hashed_pw = self.hash_password(password)
            cursor.execute("SELECT username, role FROM Users WHERE username=%s AND password_hash=%s", (username, hashed_pw))
            return cursor.fetchone()
        except Error as e:
            return None

    def update_face_encoding(self, username, encoding_array):
        """Lưu vector khuôn mặt 128 chiều vào BLOB MySQL"""
        try:
            cursor = self.conn.cursor()
            blob_data = encoding_array.tobytes()
            cursor.execute("UPDATE Users SET face_encoding = %s WHERE username = %s", (blob_data, username))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Lỗi lưu Face ID: {e}")
            return False

    def get_all_face_encodings(self):
        """Lấy tất cả Face ID đang có trong hệ thống để AI so sánh"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("SELECT username, role, face_encoding FROM Users WHERE face_encoding IS NOT NULL")
            users = cursor.fetchall()
            
            known_encodings = []
            known_users_info = []
            for u in users:
                encoding = np.frombuffer(u['face_encoding'], dtype=np.float64)
                known_encodings.append(encoding)
                known_users_info.append({"username": u['username'], "role": u['role']})
            return known_encodings, known_users_info
        except Error as e:
            return [], []

    # --- NGHIỆP VỤ CHUYẾN BAY & BÁN VÉ CHUẨN (CŨ) ---
    def get_all_flights(self):
        try:
            cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT ma_chuyen AS ma, diem_di AS di, diem_den AS den, 
                       DATE_FORMAT(gio_bay, '%H:%M %d-%m-%Y') AS gio, gia_goc AS gia 
                FROM ChuyenBay 
                ORDER BY gio_bay ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            return []

    def add_flight(self, ma, di, den, gio, gia):
        try:
            cursor = self.conn.cursor()
            query = "INSERT INTO ChuyenBay (ma_chuyen, diem_di, diem_den, gio_bay, gia_goc, tong_ghe, ghe_da_ban) VALUES (%s, %s, %s, %s, %s, 100, 0)"
            cursor.execute(query, (ma, di, den, gio, gia))
            self.conn.commit()
            return True
        except Error as e:
            return False

    def delete_flight(self, ma_chuyen):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM ChuyenBay WHERE ma_chuyen=%s", (ma_chuyen,))
            self.conn.commit()
            return True
        except Error as e:
            return False

    def book_ticket_safe(self, ma_chuyen, cccd, ho_ten, sdt, hang_ve, tong_tien):
        try:
            cursor = self.conn.cursor()
            args = (ma_chuyen, cccd, ho_ten, sdt, hang_ve, tong_tien, '')
            result_args = cursor.callproc('sp_DatVe', args)
            message = result_args[6]
            if "Thành công" in message:
                return True, message
            return False, message
        except Error as e:
            return False, f"Lỗi CSDL: {e}"

    def get_ticket_history(self):
        try:
            cursor = self.conn.cursor(dictionary=True)
            query = """
                SELECT k.ho_ten AS khach, v.cccd_khach AS cccd, v.ma_chuyen AS chuyen, 
                       v.hang_ve AS hang, v.tong_tien 
                FROM VeMayBay v 
                JOIN KhachHang k ON v.cccd_khach = k.cccd 
                ORDER BY v.id_ve DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            return []

# =======================================================
# BACKEND 2: BỘ XÁC THỰC AI (FACE AUTHENTICATOR)
# =======================================================
class FaceAuthenticator:
    def __init__(self, db_manager):
        self.db = db_manager

    def register_face(self):
        video_capture = cv2.VideoCapture(0)
        face_encoding_result = None
        
        for _ in range(50):
            ret, frame = video_capture.read()
            if not ret: continue

            cv2.imshow('Dang ky Face ID (Nhin thang vao camera, an Q de huy)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            if face_locations:
                encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                if encodings:
                    face_encoding_result = encodings[0]
                    break

        video_capture.release()
        cv2.destroyAllWindows()

        if face_encoding_result is not None:
            return True, face_encoding_result
        return False, "Không nhận diện được khuôn mặt. Thử lại nơi đủ sáng!"

    def scan_and_login(self):
        known_encodings, known_users = self.db.get_all_face_encodings()
        if not known_encodings:
            return False, "Chưa có Face ID nào được lưu trong hệ thống!"

        video_capture = cv2.VideoCapture(0)
        login_success = False
        logged_in_user = None

        for _ in range(30):
            ret, frame = video_capture.read()
            if not ret: continue

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.45)
                if True in matches:
                    first_match_index = matches.index(True)
                    logged_in_user = known_users[first_match_index]
                    login_success = True
                    break
            
            if login_success: break

        video_capture.release()
        cv2.destroyAllWindows()

        if login_success:
            return True, logged_in_user
        return False, "Khuôn mặt không khớp với tài khoản nào!"


# KHỞI TẠO BIẾN TOÀN CỤC CỐT LÕI
db = DatabaseManager()
ai_auth = FaceAuthenticator(db)

# =======================================================
# FRONTEND: GUI STYLES VÀ CÁC MÀN HÌNH
# =======================================================
STYLE_GLASS = """
    QWidget { font-family: 'Segoe UI', sans-serif; }
    QLineEdit, QSpinBox, QDateTimeEdit { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 8px; padding: 8px; color: white; }
    QPushButton { border-radius: 8px; padding: 10px; font-weight: bold; }
    #Sidebar { background-color: rgba(0, 0, 0, 0.2); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    #NavBtn { text-align: left; background-color: transparent; color: #d1d5db; border-radius: 5px; padding: 8px 15px; }
    #NavBtn:hover { background-color: rgba(255, 255, 255, 0.1); color: white; }
    #ClockLabel { color: #10b981; font-weight: bold; font-size: 14px; }
"""

class LoginScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("✈️ HỆ THỐNG ĐẠI LÝ BÁN VÉ AI")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #3b82f6; margin-bottom: 30px;")
        
        self.user = QLineEdit(); self.user.setPlaceholderText("Tên đăng nhập (VD: admin)"); self.user.setFixedWidth(320)
        self.password = QLineEdit(); self.password.setPlaceholderText("Mật khẩu (VD: admin123)"); self.password.setEchoMode(QLineEdit.EchoMode.Password); self.password.setFixedWidth(320)

        btn_login = QPushButton("🔑 ĐĂNG NHẬP")
        btn_login.setStyleSheet("background-color: #3b82f6; color: white;")
        btn_login.clicked.connect(self.dang_nhap_bang_mat_khau)

        btn_face = QPushButton("📷 ĐĂNG NHẬP BẰNG FACE ID")
        btn_face.setStyleSheet("background-color: #10b981; color: white;")
        btn_face.clicked.connect(self.dang_nhap_bang_face_id)

        btn_register = QPushButton("📝 ĐĂNG KÝ MỚI (KÈM FACE ID)")
        btn_register.setStyleSheet("background-color: #f59e0b; color: white;")
        btn_register.clicked.connect(self.dang_ky_tai_khoan)

        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.user, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.password, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_login, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btn_face, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(btn_register, alignment=Qt.AlignmentFlag.AlignCenter)

    def dang_nhap_bang_mat_khau(self):
        u = self.user.text()
        p = self.password.text()
        if not u or not p: return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Username và Password!")
        
        user_info = db.verify_password_login(u, p)
        if user_info:
            QMessageBox.information(self, "Thành công", f"Chào {user_info['role']} {user_info['username']}!")
            self.controller.setCurrentIndex(1)
        else:
            QMessageBox.critical(self, "Lỗi", "Sai tài khoản hoặc mật khẩu!")

    def dang_nhap_bang_face_id(self):
        QMessageBox.information(self, "Chuẩn bị", "Vui lòng nhìn thẳng vào Camera trong 3 giây...")
        success, result = ai_auth.scan_and_login()
        if success:
            QMessageBox.information(self, "Thành công", f"Xác thực khuôn mặt thành công!\nXin chào {result['role']} {result['username']}")
            self.controller.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Từ chối", result)

    def dang_ky_tai_khoan(self):
        u = self.user.text()
        p = self.password.text()
        if not u or not p: return QMessageBox.warning(self, "Lỗi", "Nhập Username & Password cần tạo trước!")
        
        # 1. Tạo tài khoản vào Database
        success, msg = db.register_user(u, p, "Staff")
        if not success: return QMessageBox.warning(self, "Lỗi", msg)
        
        # 2. Quét Face ID
        reply = QMessageBox.question(self, 'Đăng ký Face ID', 'Tài khoản đã tạo. Bạn có muốn quét khuôn mặt luôn không?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            face_success, face_data = ai_auth.register_face()
            if face_success:
                db.update_face_encoding(u, face_data)
                QMessageBox.information(self, "Hoàn tất", f"Đã lưu Face ID cho tài khoản '{u}'!")
            else:
                QMessageBox.warning(self, "Lỗi Camera", face_data)

class AddFlightDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thêm Chuyến Bay Mới")
        self.resize(350, 250)
        
        layout = QFormLayout(self)
        self.txt_ma = QLineEdit(); self.txt_di = QLineEdit(); self.txt_den = QLineEdit()
        
        # Lịch DatePicker UI
        self.txt_gio = QDateTimeEdit(self)
        self.txt_gio.setCalendarPopup(True)
        self.txt_gio.setDisplayFormat("dd-MM-yyyy HH:mm")
        self.txt_gio.setDateTime(QDateTime.currentDateTime())
        
        self.txt_gia = QSpinBox(); self.txt_gia.setRange(100000, 10000000); self.txt_gia.setSingleStep(50000); self.txt_gia.setValue(1000000)

        layout.addRow("Mã chuyến:", self.txt_ma); layout.addRow("Điểm đi:", self.txt_di); layout.addRow("Điểm đến:", self.txt_den)
        layout.addRow("Giờ bay:", self.txt_gio); layout.addRow("Giá vé (VNĐ):", self.txt_gia)

        btn_save = QPushButton("Lưu Chuyến Bay")
        btn_save.setStyleSheet("background-color: #10b981; color: white;")
        btn_save.clicked.connect(self.accept)
        layout.addRow(btn_save)

    def get_data(self):
        gio_bay_sql = self.txt_gio.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        return { "ma": self.txt_ma.text(), "di": self.txt_di.text(), "den": self.txt_den.text(), "gio": gio_bay_sql, "gia": self.txt_gia.value() }

class DashboardScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = QFrame(); sidebar.setObjectName("Sidebar"); sidebar.setFixedWidth(200)
        side_layout = QVBoxLayout(sidebar)
        
        menus = [("📊 Quản lý Lịch bay", 1), ("✈️ Bán vé mới", 2), ("📋 Lịch sử Bán vé", 3), ("📈 Báo cáo Thống kê", 4), ("⚙️ Cài đặt", 5)]
        for name, idx in menus:
            btn = QPushButton(name); btn.setObjectName("NavBtn")
            btn.clicked.connect(lambda checked, i=idx: controller.setCurrentIndex(i))
            side_layout.addWidget(btn)
        
        side_layout.addStretch()
        btn_logout = QPushButton("🔒 Đăng xuất"); btn_logout.setObjectName("NavBtn"); btn_logout.clicked.connect(lambda: controller.setCurrentIndex(0))
        side_layout.addWidget(btn_logout)

        content = QWidget(); content_layout = QVBoxLayout(content)
        header_layout = QHBoxLayout(); header = QLabel("QUẢN LÝ CHUYẾN BAY"); header.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.lbl_clock = QLabel(); self.lbl_clock.setObjectName("ClockLabel")
        header_layout.addWidget(header); header_layout.addStretch(); header_layout.addWidget(self.lbl_clock)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm Chuyến"); btn_add.setStyleSheet("background-color: #10b981; color: white; padding: 5px 15px;"); btn_add.clicked.connect(self.them_chuyen_bay)
        btn_delete = QPushButton("🗑 Xóa Chuyến"); btn_delete.setStyleSheet("background-color: #ef4444; color: white; padding: 5px 15px;"); btn_delete.clicked.connect(self.xoa_chuyen_bay)
        toolbar.addWidget(btn_add); toolbar.addWidget(btn_delete); toolbar.addStretch()

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Mã", "Điểm Đi", "Điểm Đến", "Giờ", "Giá Gốc"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        content_layout.addLayout(header_layout); content_layout.addLayout(toolbar); content_layout.addWidget(self.table)
        main_layout.addWidget(sidebar); main_layout.addWidget(content)

        self.timer = QTimer(self); self.timer.timeout.connect(self.update_time); self.timer.start(1000) 

    def update_time(self): self.lbl_clock.setText(f"🕒 {QDateTime.currentDateTime().toString('dd/MM/yyyy hh:mm:ss')}")

    def load_data(self):
        flights = db.get_all_flights()
        self.table.setRowCount(len(flights))
        for row, f in enumerate(flights):
            self.table.setItem(row, 0, QTableWidgetItem(f["ma"]))
            self.table.setItem(row, 1, QTableWidgetItem(f["di"]))
            self.table.setItem(row, 2, QTableWidgetItem(f["den"]))
            self.table.setItem(row, 3, QTableWidgetItem(str(f["gio"])))
            self.table.setItem(row, 4, QTableWidgetItem(f"{f['gia']:,} đ"))

    def them_chuyen_bay(self):
        dialog = AddFlightDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_f = dialog.get_data()
            if not new_f["ma"]: return QMessageBox.warning(self, "Lỗi", "Nhập Mã chuyến bay!")
            if db.add_flight(new_f["ma"], new_f["di"], new_f["den"], new_f["gio"], new_f["gia"]):
                self.load_data(); QMessageBox.information(self, "Thành công", "Đã thêm chuyến bay mới!")
            else: QMessageBox.critical(self, "Lỗi", "Mã chuyến bay đã tồn tại hoặc CSDL có vấn đề!")

    def xoa_chuyen_bay(self):
        row = self.table.currentRow()
        if row < 0: return QMessageBox.warning(self, "Lỗi", "Chọn một chuyến bay để xóa.")
        reply = QMessageBox.question(self, 'Xác nhận xóa', 'Bạn có chắc chắn muốn xóa chuyến bay này?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if db.delete_flight(self.table.item(row, 0).text()): self.load_data()
            else: QMessageBox.warning(self, "Lỗi", "Chuyến bay đã có vé bán ra, không thể xóa!")

class BookingScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        btn_back = QPushButton("⬅ Quay lại"); btn_back.clicked.connect(lambda: controller.setCurrentIndex(1))
        header_layout.addWidget(btn_back); header_layout.addStretch()
        
        title = QLabel("NGHIỆP VỤ XUẤT VÉ & THANH TOÁN"); title.setStyleSheet("font-size: 22px; font-weight: bold; color: #3b82f6;")
        form_layout = QHBoxLayout(); col_left = QVBoxLayout()
        
        self.flight_sel = QComboBox(); self.flight_sel.setMinimumHeight(40)
        self.class_sel = QComboBox(); self.class_sel.addItems(["Phổ thông (x1.0)", "Thương gia (x2.0)"]); self.class_sel.setMinimumHeight(40)

        self.name = QLineEdit(); self.name.setPlaceholderText("Tên hành khách")
        self.id_card = QLineEdit(); self.id_card.setPlaceholderText("Số CCCD/HC")
        self.phone = QLineEdit(); self.phone.setPlaceholderText("Số điện thoại (SĐT)") 
        self.voucher = QLineEdit(); self.voucher.setPlaceholderText("Mã Voucher (Nhập 'VIP' giảm 20%)")
        self.voucher.setStyleSheet("border: 1px solid #eab308;") 

        col_left.addWidget(QLabel("Chọn chuyến bay:")); col_left.addWidget(self.flight_sel)
        col_left.addWidget(QLabel("Chọn hạng vé:")); col_left.addWidget(self.class_sel)
        col_left.addWidget(self.name); col_left.addWidget(self.id_card); col_left.addWidget(self.phone); col_left.addWidget(self.voucher)
        col_left.addStretch()

        col_right = QVBoxLayout(); receipt_frame = QFrame()
        receipt_frame.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-radius: 10px; padding: 15px;")
        receipt_layout = QVBoxLayout(receipt_frame)
        
        self.lbl_calc_detail = QLabel("Đang chờ dữ liệu..."); self.lbl_calc_detail.setStyleSheet("line-height: 1.5; color: #9ca3af;")
        self.lbl_total_price = QLabel("TỔNG: 0 VNĐ"); self.lbl_total_price.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981; margin-top: 15px;")
        
        btn_confirm = QPushButton("XUẤT VÉ & THANH TOÁN")
        btn_confirm.setStyleSheet("background-color: #3b82f6; color: white; padding: 15px; font-size: 16px;")
        btn_confirm.clicked.connect(self.kiem_tra_va_xuat_ve)

        receipt_layout.addWidget(QLabel("TẠM TÍNH HÓA ĐƠN")); receipt_layout.addWidget(self.lbl_calc_detail)
        receipt_layout.addWidget(self.lbl_total_price); receipt_layout.addStretch()
        col_right.addWidget(receipt_frame); col_right.addWidget(btn_confirm)

        form_layout.addLayout(col_left, stretch=2); form_layout.addLayout(col_right, stretch=1)

        self.flight_sel.currentIndexChanged.connect(self.tinh_tien)
        self.class_sel.currentIndexChanged.connect(self.tinh_tien)
        self.voucher.textChanged.connect(self.tinh_tien)

        layout.addLayout(header_layout); layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20); layout.addLayout(form_layout)

    def load_flights(self):
        self.flight_sel.clear()
        for f in db.get_all_flights(): self.flight_sel.addItem(f"{f['ma']} ({f['di']} - {f['den']})", f['gia'])
        self.tinh_tien()

    def tinh_tien(self):
        if self.flight_sel.count() == 0: return
        gia_goc = self.flight_sel.currentData()
        he_so = self.class_sel.currentData()
        tong = gia_goc * he_so
        giam = tong * 0.2 if self.voucher.text().strip().upper() == "VIP" else 0
        tong -= giam
        self.lbl_calc_detail.setText(f"Giá vé gốc: {int(gia_goc):,} đ\nHệ số hạng: x{he_so}\nGiảm giá: -{int(giam):,} đ")
        self.lbl_total_price.setText(f"TỔNG: {int(tong):,} VNĐ")

    def kiem_tra_va_xuat_ve(self):
        if not self.name.text() or not self.id_card.text(): return QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ Tên và CCCD!")
            
        ma_chuyen = self.flight_sel.currentText().split(" ")[0]
        sdt = self.phone.text() if self.phone.text() else "0000000000"
        hang_ve = "Phổ thông" if "Phổ thông" in self.class_sel.currentText() else "Thương gia"
        tong_tien = int(self.lbl_total_price.text().replace("TỔNG: ", "").replace(" VNĐ", "").replace(",", ""))

        success, msg = db.book_ticket_safe(ma_chuyen, self.id_card.text(), self.name.text(), sdt, hang_ve, tong_tien)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            self.name.clear(); self.id_card.clear(); self.phone.clear(); self.voucher.clear()
        else: QMessageBox.critical(self, "Thất bại", msg)

class HistoryScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        btn_back = QPushButton("⬅ Quay lại Dashboard"); btn_back.clicked.connect(lambda: controller.setCurrentIndex(1))
        header_layout.addWidget(btn_back); header_layout.addStretch()

        title = QLabel("📋 DANH SÁCH VÉ ĐÃ XUẤT"); title.setStyleSheet("font-size: 22px; font-weight: bold; color: #10b981;")
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Hành Khách", "CCCD", "Chuyến Bay", "Hạng", "Thanh Toán"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addLayout(header_layout); layout.addWidget(title); layout.addWidget(self.table)

    def load_history(self):
        tickets = db.get_ticket_history()
        self.table.setRowCount(len(tickets))
        for row, t in enumerate(tickets):
            self.table.setItem(row, 0, QTableWidgetItem(t["khach"])); self.table.setItem(row, 1, QTableWidgetItem(t["cccd"]))
            self.table.setItem(row, 2, QTableWidgetItem(t["chuyen"])); self.table.setItem(row, 3, QTableWidgetItem(t["hang"]))
            self.table.setItem(row, 4, QTableWidgetItem(f"{t['tong_tien']:,} đ"))

class ReportScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout(); btn_back = QPushButton("⬅ Quay lại Dashboard"); btn_back.clicked.connect(lambda: controller.setCurrentIndex(1))
        header_layout.addWidget(btn_back); header_layout.addStretch()
        
        title = QLabel("📊 BÁO CÁO THỐNG KÊ KINH DOANH"); title.setStyleSheet("font-size: 22px; font-weight: bold; color: #a855f7;")
        plt.style.use('dark_background'); self.figure = Figure(figsize=(10, 5)); self.canvas = FigureCanvas(self.figure); self.figure.patch.set_facecolor('#202124') 

        ax1 = self.figure.add_subplot(1, 2, 1); ax1.bar(np.array(['T1', 'T2', 'T3', 'T4', 'T5', 'T6']), np.random.randint(50, 200, size=6), color='#3b82f6', edgecolor='white')
        ax1.set_title("Doanh thu 6 tháng đầu năm (Triệu VNĐ)", fontsize=12, pad=10); ax1.set_ylabel("Triệu VNĐ")

        ax2 = self.figure.add_subplot(1, 2, 2); ax2.pie(np.array([65.5, 20.0, 14.5]), explode=(0.05, 0, 0), labels=['Phổ thông', 'Thương gia', 'Khuyến mãi'], colors=['#10b981', '#f59e0b', '#ef4444'], autopct='%1.1f%%', shadow=False, startangle=140)
        ax2.set_title("Cơ cấu Hạng vé bán ra", fontsize=12, pad=10)

        self.figure.tight_layout(); layout.addLayout(header_layout); layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.canvas)

class SettingScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        layout = QVBoxLayout(self); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout = QHBoxLayout(); btn_back = QPushButton("⬅ Quay lại Dashboard"); btn_back.clicked.connect(lambda: controller.setCurrentIndex(1))
        header_layout.addWidget(btn_back); header_layout.addStretch()

        info = QLabel("⚙️ CẤU HÌNH HỆ THỐNG"); info.setStyleSheet("font-size: 24px; font-weight: bold; color: #9ca3af;")
        detail = QLabel("Phần mềm Quản lý Đại lý Vé Máy bay\nBảo mật: Xác thực AI (Face Recognition)\nTác giả: Nhóm 12"); detail.setAlignment(Qt.AlignmentFlag.AlignCenter); detail.setStyleSheet("color: #6b7280; font-size: 14px; margin-top: 20px;")
        layout.addLayout(header_layout); layout.addStretch(); layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter); layout.addWidget(detail, alignment=Qt.AlignmentFlag.AlignCenter); layout.addStretch()

# =======================================================
# KHỞI TẠO ỨNG DỤNG
# =======================================================
class FlightApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Quản lý Bán vé Máy bay AI - Version 4")
        self.resize(1050, 650)
        self.setStyleSheet(STYLE_GLASS)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.page_login = LoginScreen(self.stacked_widget)
        self.page_dash = DashboardScreen(self.stacked_widget)
        self.page_book = BookingScreen(self.stacked_widget)
        self.page_history = HistoryScreen(self.stacked_widget)
        self.page_report = ReportScreen(self.stacked_widget)
        self.page_setting = SettingScreen(self.stacked_widget)

        for p in [self.page_login, self.page_dash, self.page_book, self.page_history, self.page_report, self.page_setting]: self.stacked_widget.addWidget(p)

        self.stacked_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        if index == 1: self.page_dash.load_data()      
        elif index == 2: self.page_book.load_flights()   
        elif index == 3: self.page_history.load_history()

if __name__ == "__main__":
    app = QApplication(sys.argv) 
    window = FlightApp()
    window.show()
    sys.exit(app.exec())