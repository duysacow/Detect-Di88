import sys
import os
import cv2
import mss
import time
import numpy as np
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QRubberBand,
    QPushButton,
    QVBoxLayout,
    QLabel,
)
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer


# Vẽ vùng chọn crop trực tiếp trên ảnh màn hình
class CropCanvas(QWidget):
    """Cửa sổ toàn màn hình để sếp kéo chuột cắt ảnh"""

    def __init__(self, full_img_bgr, callback):
        super().__init__()
        self.full_img = full_img_bgr
        self.callback = callback
        self.w, self.h = full_img_bgr.shape[1], full_img_bgr.shape[0]

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setGeometry(0, 0, self.w, self.h)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setWindowOpacity(0.7)

        self.rubberBand = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = QPoint()

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            rect = self.rubberBand.geometry()
            if not rect.isEmpty():
                self.callback(rect)
                self.close()


# Giao diện hỗ trợ chọn và cắt vùng ảnh thủ công
class ToolCropUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Di88 - Cắt Template")
        self.setFixedSize(300, 150)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout()
        self.lbl = QLabel("Bấm nút xong có 3 giây để mở TAB game")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn = QPushButton("CHỤP HÒM ĐỒ (KHO ĐỒ)")
        self.btn.setMinimumHeight(50)
        self.btn.clicked.connect(self.start_timer)

        layout.addWidget(self.lbl)
        layout.addWidget(self.btn)
        self.setLayout(layout)

        self.countdown = 3
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

    def start_timer(self):
        self.btn.setEnabled(False)
        self.countdown = 3
        self.timer.start(1000)
        self.lbl.setText(f"ĐANG CHỜ: {self.countdown} GIÂY...")

    def update_timer(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.lbl.setText(f"ĐANG CHỜ: {self.countdown} GIÂY...")
        else:
            self.timer.stop()
            self.hide()  # Ẩn tool để không bị dính vào ảnh chụp
            QTimer.singleShot(200, self.capture_and_crop)

    def capture_and_crop(self):
        # 1. Chụp màn hình
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = np.array(sct_img)[:, :, :3]

        # 2. Hiện Canvas để sếp cắt
        self.canvas = CropCanvas(img, self.save_result)
        self.canvas.show()

    def save_result(self, rect):
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        crop = self.canvas.full_img[y : y + h, x : x + w]

        # Xác định đường dẫn lưu
        h_res = self.canvas.full_img.shape[0]
        res_folder = "2K" if h_res >= 1440 else "FullHD"
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(base_dir, res_folder, "ui")

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        save_path = os.path.join(target_dir, "inventory.png")
        cv2.imwrite(save_path, crop)

        print(f"\n[THÀNH CÔNG] Đã lưu: {save_path}")
        print(f" - Tọa độ inventory_tab: [{x}, {y}, {w}, {h}]")
        print(" - Sếp dán 4 số này vào roi_storage.py nhé!")

        self.show()
        self.lbl.setText("XONG! Sếp có thể chụp cái khác.")
        self.btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolCropUI()
    window.show()
    sys.exit(app.exec())
