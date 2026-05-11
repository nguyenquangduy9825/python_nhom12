import cv2
import face_recognition
import numpy as np

class FaceAuthenticator:
    def __init__(self, user_dao):
        self.user_dao = user_dao

    def scan_and_login(self):
        users_data = self.user_dao.get_all_face_encodings()
        if not users_data:
            return False, "Chưa có dữ liệu khuôn mặt"

        known_encodings = [np.frombuffer(u['face_encoding'], dtype=np.float64) for u in users_data]
        # Logic nhận diện (giữ nguyên từ demo_giao_dien.py của bạn)
        # ... (Phần code OpenCV và face_recognition)