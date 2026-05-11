# bll/face_service.py
import json
import numpy as np
from dal.auth_repository import AuthRepository

try:
    import cv2
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False

class FaceRecognitionService:
    def __init__(self):
        self.auth_repo = AuthRepository()

    def encode_face(self, frame):
        """Xử lý ảnh từ camera OpenCV sang ma trận 128 chiều"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_frame)
        if not locations: return None
        encodings = face_recognition.face_encodings(rgb_frame, locations)
        return encodings[0]

    def register_face(self, user_id, frame):
        encoding = self.encode_face(frame)
        if encoding is None: return False, "Không tìm thấy khuôn mặt!"
        if self.auth_repo.save_face_encoding(user_id, encoding.tolist()): return True, "Đăng ký thành công!"
        return False, "Lỗi Database!"

    def login_with_face(self, current_encoding):
        if not FACE_REC_AVAILABLE: return False, None
        db_users = self.auth_repo.get_all_face_encodings()
        if not db_users: return False, None
        
        known_encodings = [np.array(json.loads(u['face_encoding'])) for u in db_users]
        matches = face_recognition.compare_faces(known_encodings, current_encoding, tolerance=0.45)
        face_distances = face_recognition.face_distance(known_encodings, current_encoding)
        
        if len(face_distances) > 0:
            best_match_idx = np.argmin(face_distances)
            if matches[best_match_idx]:
                return True, db_users[best_match_idx]
        return False, None