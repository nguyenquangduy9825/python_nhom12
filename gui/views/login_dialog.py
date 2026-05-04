from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
from bll.auth_service import AuthService

class LoginScreen(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.auth_service = AuthService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.user_input = QLineEdit()
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.btn_login = QPushButton("Đăng nhập")
        
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.btn_login)

    def handle_login(self):
        user, msg = self.auth_service.login(self.user_input.text(), self.pass_input.text())
        if user:
            QMessageBox.information(self, "Thành công", f"Chào {user['username']}")
            self.controller.setCurrentIndex(1) # Chuyển sang Dashboard
        else:
            QMessageBox.warning(self, "Lỗi", msg)