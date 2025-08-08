from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtCore import Qt, QSize

# Add this new class for the indicator
class StatusIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(20, 20)  # Set minimum size for the indicator
        self.status = False  # False = red, True = green
        
    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the circle
        if self.status:
            color = QColor("green")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, 16, 16)
        else:
            color = QColor("red")
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, 16, 16)

    def setStatus(self, status: bool):
        self.status = status
        self.update()  # Trigger a repaint