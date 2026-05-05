import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, QTimer
from PyQt6.QtGui import QColor, QPalette

# Thêm thư mục gốc vào path để import
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.detection import roi_storage
except ImportError:
    # Fallback if run incorrectly
    roi_storage = None


# Đại diện một khung ROI có thể chỉnh trên overlay
class ROIBox(QFrame):
    def __init__(self, parent, name, rect, color="#00FF00"):
        super().__init__(parent)
        self.name = name
        self.color = color

        # Initial Geometry
        self.setGeometry(rect[0], rect[1], rect[2], rect[3])

        # Styling
        self.update_style(False)

        # Label
        self.label = QLabel(name, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 10px; background: rgba(0,0,0,100);"
        )
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.resize_label()

        # Interaction State
        self.dragging = False
        self.resizing = False
        self.drag_start_pos = QPoint()
        self.resize_margin = 15
        self.active = False

        # Resize Handle Indicator
        self.resize_handle = QLabel("┘", self)
        self.resize_handle.setStyleSheet(
            f"color: {self.color}; font-size: 14px; font-weight: bold;"
        )
        self.resize_handle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.update_handle_pos()

    def update_style(self, active):
        border_width = 3 if active else 2
        self.setStyleSheet(f"""
            QFrame {{
                border: {border_width}px solid {self.color};
                background-color: rgba(0, 0, 0, 20);
            }}
        """)

    def update_handle_pos(self):
        if hasattr(self, "resize_handle"):
            self.resize_handle.setGeometry(
                self.width() - 15, self.height() - 15, 15, 15
            )

    def resize_label(self):
        self.label.setGeometry(2, 2, self.width() - 4, 15)
        if hasattr(self, "resize_handle"):
            self.update_handle_pos()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.active = True
            self.update_style(True)
            self.raise_()

            # Check for resize vs drag
            pos = event.pos()
            if (
                pos.x() > self.width() - self.resize_margin
                and pos.y() > self.height() - self.resize_margin
            ):
                self.resizing = True
            else:
                self.dragging = True
                self.drag_start_pos = (
                    event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                )

            event.accept()

    def mouseMoveEvent(self, event):
        if self.resizing:
            new_size = QSize(event.pos().x(), event.pos().y())
            if new_size.width() > 20 and new_size.height() > 20:
                self.resize(new_size)
                self.resize_label()
        elif self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_pos)

        event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        # self.active = False
        # self.update_style(False)
        event.accept()

    def get_roi_list(self):
        geo = self.geometry()
        return [geo.x(), geo.y(), geo.width(), geo.height()]


# Giao diện chỉnh sửa và lưu các vùng ROI
class ToolOverlayROI(QWidget):
    def __init__(self):
        super().__init__()

        # --- STREAM-PROOF (STEALTH CAPTURE) ---
        QTimer.singleShot(200, self.apply_stealth_layer)

        # 1. Window Config
        self.setWindowTitle("DI88 LIVE ROI OVERLAY")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Thêm màu nền mờ để xác nhận Tool có hiện lên
        self.setStyleSheet("background-color: rgba(255, 255, 255, 10);")

        # Full Screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.boxes = {}
        self.init_ui()

    def apply_stealth_layer(self):
        try:
            hwnd = self.winId().__int__()
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x11)
        except Exception:
            pass

    def init_ui(self):
        # Background Layout (Transparent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 2. Load ROIs
        import importlib

        if roi_storage:
            importlib.reload(roi_storage)

        res_key = f"{self.width()}x{self.height()}"
        print(f"[OVERLAY] Detecting ROIs for resolution: {res_key}")

        saved_rois = {}
        if roi_storage:
            saved_rois = roi_storage.get_roi(res_key) or {}

        # Targets & Defaults
        targets = [
            ("gun1_name", "G1 NAME", [1364, 92, 212, 38], "#00FF00"),
            ("gun1_scope", "G1 SCOPE", [1603, 114, 53, 51], "#00FF00"),
            ("gun1_grip", "G1 GRIP", [1434, 235, 53, 53], "#00FF00"),
            ("gun1_muzzle", "G1 MUZZLE", [1332, 235, 54, 52], "#00FF00"),
            ("gun2_name", "G2 NAME", [1364, 317, 222, 37], "#FFFF00"),
            ("gun2_scope", "G2 SCOPE", [1605, 338, 51, 52], "#FFFF00"),
            ("gun2_grip", "G2 GRIP", [1434, 462, 53, 51], "#FFFF00"),
            ("gun2_muzzle", "G2 MUZZLE", [1334, 462, 50, 51], "#FFFF00"),
            ("stance", "STANCE", [900, 900, 120, 120], "#00FFFF"),
            ("dieukien", "DK DETECT", [1300, 50, 100, 50], "#FF8800"),
        ]

        for key, label, def_rect, color in targets:
            rect = saved_rois.get(key, def_rect)
            box = ROIBox(self, label, rect, color)
            self.boxes[key] = box

        # 3. Control Panel (Top)
        self.panel = QFrame(self)
        self.panel.setGeometry(self.width() // 2 - 200, 20, 400, 60)
        self.panel.setStyleSheet(
            "background-color: #222; border: 2px solid #555; border-radius: 10px;"
        )

        p_layout = QHBoxLayout(self.panel)

        lbl_msg = QLabel(
            f"DI88 OVERLAY ROI TOOL ({self.width()}x{self.height()})\nDrag boxes, Resize at bottom-right corner",
            self.panel,
        )
        lbl_msg.setStyleSheet("color: white; font-size: 10px;")
        p_layout.addWidget(lbl_msg)

        btn_save = QPushButton("SAVE SETTINGS", self.panel)
        btn_save.setFixedSize(120, 35)
        btn_save.setStyleSheet("""
            QPushButton { background-color: #00AA00; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #00CC00; }
        """)
        btn_save.clicked.connect(self.save_rois)
        p_layout.addWidget(btn_save)

        btn_close = QPushButton("X", self.panel)
        btn_close.setFixedSize(30, 35)
        btn_close.setStyleSheet(
            "background-color: #AA0000; color: white; font-weight: bold; border-radius: 5px;"
        )
        btn_close.clicked.connect(self.close)
        p_layout.addWidget(btn_close)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def save_rois(self):
        new_data = {}
        for key, box in self.boxes.items():
            new_data[key] = box.get_roi_list()

        res_key = f"{self.width()}x{self.height()}"

        # --- LOGIC LƯU TRỰC TIẾP (Hệ thống sạch) ---
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, "src", "detection", "roi_storage.py")

            import ast
            import pprint

            # 1. Đọc dữ liệu hiện tại
            full_data = {}
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    import re

                    match = re.search(
                        r"DATA\s*=\s*(\{.*?\})\s*(\n\n|#|\Z)", content, re.DOTALL
                    )
                    if match:
                        try:
                            # Trim white spaces to avoid ast IndentationError
                            clean_data_str = match.group(1).strip()
                            full_data = ast.literal_eval(clean_data_str)
                        except:
                            full_data = {}

            # 2. Cập nhật dữ liệu mới
            if res_key in full_data:
                full_data[res_key].update(new_data)
            else:
                full_data[res_key] = new_data

            # 3. GHI ĐÈ TOÀN BỘ FILE (An toàn nhất)
            formatted_data = pprint.pformat(full_data, indent=4, width=120)

            template = f"""# KHO LƯU TRỮ TỌA ĐỘ (Cập nhật tự động bởi ToolOverlayROI)

DATA = {formatted_data}

# Helper Functions
def get_roi(resolution_key):
    return DATA.get(resolution_key, None)
"""
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(template)

            self.panel.findChildren(QLabel)[0].setText(
                f"SAVED [{res_key}] SUCCESSFULLY!\nRestart Macro to apply."
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"[ERROR] Save failed: {e}")
            self.panel.findChildren(QLabel)[0].setText(
                f"SAVE FAILED!\nError: {str(e)[:25]}..."
            )


if __name__ == "__main__":
    # DPI Awareness Fix
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    print("[OVERLAY] Initializing PyQt6 Application...")
    app = QApplication(sys.argv)

    print("[OVERLAY] Creating ToolOverlayROI instance...")
    tool = ToolOverlayROI()

    print(f"[OVERLAY] Window Geometry: {tool.geometry()}")
    print("[OVERLAY] Showing Window...")
    tool.show()

    print("[OVERLAY] Entering Event Loop.")
    sys.exit(app.exec())
