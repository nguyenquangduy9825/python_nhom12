# gui/faceid/face_login_dialog.py
import cv2
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap
from bll.face_service import FaceRecognitionService

class FaceLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Face ID Scanner")
        self.setFixedSize(600, 500)
        self.setStyleSheet("background-color: #0f172a; color: white;")
        
        self.face_service = FaceRecognitionService()
        self.logged_in_user = None
        self.setup_ui()
        
        # Bật Camera
        self.capture = cv2.VideoCapture(0) # 0 là webcam mặc định
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30) # Cập nhật mỗi 30ms

        self.frame_count = 0

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Quét khuôn mặt để Đăng nhập")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        self.lbl_camera = QLabel("Đang tải Camera...")
        self.lbl_camera.setFixedSize(560, 380)
        self.lbl_camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camera.setStyleSheet("border: 2px dashed #3b82f6; border-radius: 12px;")
        layout.addWidget(self.lbl_camera)

        btn_cancel = QPushButton("Hủy bỏ")
        btn_cancel.setStyleSheet("background-color: #ef4444; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_cancel.clicked.connect(self.close)
        layout.addWidget(btn_cancel)

    def update_frame(self):
        ret, frame = self.capture.read()
        if not ret: return

        # Nhận diện khuôn mặt
        self.frame_count += 1
        if self.frame_count % 10 == 0:
            # Resize để AI xử lý
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            encoding = self.face_service.encode_face(small_frame)
            
            if encoding is not None:
                success, user = self.face_service.login_with_face(encoding)
                if success:
                    self.timer.stop()
                    self.capture.release()
                    self.logged_in_user = user
                    self.accept() 

        # Đẩy hình ảnh từ OpenCV (BGR) sang PyQt (RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.lbl_camera.setPixmap(QPixmap.fromImage(img).scaled(560, 380, Qt.AspectRatioMode.KeepAspectRatio))

    def closeEvent(self, event):
        """Tự động tắt đèn Camera khi bấm X"""
        self.timer.stop()
        if self.capture.isOpened():
            self.capture.release()
        event.accept()