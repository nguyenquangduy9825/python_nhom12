# gui/animations.py
from PyQt6.QtWidgets import QStackedWidget, QFrame, QGraphicsDropShadowEffect
from PyQt6.QtCore import QPropertyAnimation, QVariantAnimation, Qt, QEasingCurve
from PyQt6.QtGui import QColor

class FadingStackedWidget(QStackedWidget):
    """QStackedWidget với hiệu ứng Fade-in khi chuyển trang"""
    def __init__(self, parent=None):
        super().__init__(parent)

    def setCurrentIndex(self, index):
        self.fader_widget = self.widget(index)
        super().setCurrentIndex(index)
        
        # Tạo hiệu ứng mờ dần (Fade in)
        self.animation = QPropertyAnimation(self.fader_widget, b"windowOpacity")
        self.fader_widget.setWindowOpacity(0.0)
        self.animation.setDuration(300) # 300ms
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()

class AnimatedHoverCard(QFrame):
    """Thẻ Card phóng to và tăng bóng đổ khi đưa chuột vào"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SaaSCard")
        
        # Bóng đổ ban đầu
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

        # Animation cho bóng đổ
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(200)
        self.anim.valueChanged.connect(self.update_shadow)

    def update_shadow(self, radius):
        self.shadow.setBlurRadius(radius)
        self.shadow.setOffset(0, int(radius/2.5))

    def enterEvent(self, event):
        self.anim.setStartValue(10)
        self.anim.setEndValue(25) # Tăng độ nhòe và bóng
        self.anim.start()
        self.setStyleSheet("border: 1px solid #475569;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.setStartValue(25)
        self.anim.setEndValue(10)
        self.anim.start()
        self.setStyleSheet("border: 1px solid #334155;")
        super().leaveEvent(event)