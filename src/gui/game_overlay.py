import ctypes
from ctypes import wintypes

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QWidget

# --- KHAI BÁO WIN32 API CHUẨN (FIX LỖI 0) ---
user32 = ctypes.windll.user32

# Cấu hình SetWindowDisplayAffinity
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.SetWindowDisplayAffinity.restype = wintypes.BOOL

# Cấu hình SetWindowLongW và GetWindowLongW
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = wintypes.LONG
user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
user32.SetWindowLongW.restype = wintypes.LONG


# Hiển thị overlay trạng thái súng và macro trong game
class GameOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)

        # Thiết lập Window Flags cho Overlay Top-Level (Xuyên thấu, Luôn nổi)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Geometry: Cạnh đáy màn hình
        screen = QApplication.primaryScreen().geometry()
        self.w, self.h = 300, 26
        self.x_pos = (screen.width() - self.w) // 2
        self.y_pos = screen.height() - self.h
        self.setGeometry(self.x_pos, self.y_pos, self.w, self.h)

        # UI: Khung nền (Frame)
        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, self.w, self.h)
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(10, 10, 10, 160);
                border: 1px solid #444444;
                border-radius: 6px;
            }
        """)

        # UI: Nhãn văn bản (Label)
        self.lbl = QLabel(self.frame)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setGeometry(0, 0, self.w, self.h)
        self.lbl.setText("Di88-VP MACRO")
        self.lbl.setStyleSheet(
            "color: #00FF00; font-weight: 900; font-family: 'Segoe UI'; font-size: 10px; border: none; background: transparent;"
        )

        self.last_color = None
        self.last_full_text = ""

        # HIỆU ỨNG CHỚP XANH DƯƠNG (THEO Ý SẾP)
        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(100)
        self.flash_timer.timeout.connect(self._do_flash)
        self.flash_colors = ["#0080FF", "#0000FF"]  # Deep Blue, Blue
        self.color_idx = 0

        # Thêm Timer cho nháy Cam (Detect)
        self.detect_timer = QTimer(self)
        self.detect_timer.setInterval(200)  # Nháy nhanh hơn chút
        self.detect_timer.timeout.connect(self._do_detect_flash)
        self.detect_idx = 0

        self.show()  # Render trước
        self._adjust_to_content("Di88-VP MACRO")

    def _do_flash(self):
        """Hàm xử lý chớp xanh dương khi đang bắn"""
        # Chuyển đổi giữa Xanh dương và màu Tối cho chữ
        color = "#00FFFF" if self.color_idx % 2 == 0 else "#001a1a"
        self.lbl.setStyleSheet(
            f"color: {color}; font-weight: 900; font-family: 'Segoe UI'; font-size: 10px; border: none; background: transparent;"
        )
        # VIỀN GIỮ NGUYÊN (Theo ý sếp)
        self.frame.setStyleSheet(
            "QFrame { background-color: rgba(10, 10, 10, 160); border: 1px solid #444444; border-radius: 6px; }"
        )
        self.color_idx += 1

    def _do_detect_flash(self):
        """Hàm xử lý chớp cam khi AI đang ACTIVE"""
        if self.flash_timer.isActive():
            return  # Đang bắn thì không nháy cam đè lên

        color = "#FFA500" if self.detect_idx % 2 == 0 else "#331a00"
        self.lbl.setStyleSheet(
            f"color: {color}; font-weight: 900; font-family: 'Segoe UI'; font-size: 10px; border: none; background: transparent;"
        )
        self.frame.setStyleSheet(
            "QFrame { background-color: rgba(10, 10, 10, 160); border: 1px solid #444444; border-radius: 6px; }"
        )
        self.detect_idx += 1

    def _adjust_to_content(self, text):
        """Hàm dùng chung để co giãn khung ôm sát nội dung chữ"""
        width = self.lbl.fontMetrics().horizontalAdvance(text) + 40
        self.w = width
        # Centering horizontally
        screen_w = QApplication.primaryScreen().geometry().width()
        self.setGeometry((screen_w - self.w) // 2, self.y_pos, self.w, self.h)
        self.frame.setGeometry(0, 0, self.w, self.h)
        self.lbl.setGeometry(0, 0, self.w, self.h)

    def update_status(
        self,
        gun_name,
        scope,
        stance,
        grip="NONE",
        muzzle="NONE",
        is_paused=False,
        is_firing=False,
        ai_status="HIBERNATE",
    ):
        # Cập nhật trạng thái bắn toàn cục cho Overlay
        self.is_firing = is_firing

        if is_paused:
            text, color = "TẠM DỪNG", "#FF0000"
        elif gun_name == "NONE":
            text, color = "CHƯA CÓ SÚNG", "#FFFF00"
        else:
            scope_raw = str(scope).lower()
            sc_val = "X1"
            if "2" in scope_raw:
                sc_val = "X2"
            elif "3" in scope_raw:
                sc_val = "X3"
            elif "4" in scope_raw:
                sc_val = "X4"
            elif "6" in scope_raw:
                sc_val = "X6"
            elif "8" in scope_raw:
                sc_val = "X8"

            if "kh" in scope_raw:
                sc_val = f"KH {sc_val}"

            vn_stance = stance
            if "STAND" in stance.upper():
                vn_stance = "ĐỨNG"
            elif "CROUCH" in stance.upper():
                vn_stance = "NGỒI"
            elif "PRONE" in stance.upper():
                vn_stance = "NẰM"

            parts = [str(gun_name).upper(), sc_val]
            if str(grip).upper() != "NONE":
                parts.append("TAY")
            if str(muzzle).upper() != "NONE":
                parts.append("NÒNG")
            parts.append(vn_stance)

            text = " | ".join(parts)
            color = "#00FF00"

        # ====== ÁP DỤNG TRẠNG THÁI AI (CAM) THEO Ý SẾP ======
        if ai_status == "ACTIVE":
            if not self.detect_timer.isActive():
                self.detect_timer.start()
            # ÉP MÀU CAM TỨC THÌ (Instant Paint)
            color = "#FFA500"
        else:
            if self.detect_timer.isActive():
                self.detect_timer.stop()
                self.last_color = None

        # Xử lý text thay đổi
        if self.last_full_text != text:
            self.lbl.setText(text)
            self.last_full_text = text
            self.show()
            self._adjust_to_content(text)

        # XỬ LÝ MÀU VÀ HIỆU ỨNG CHỚP (Firing > Detect > Normal)
        if is_firing:
            if not self.flash_timer.isActive():
                self.flash_timer.start()
            if self.detect_timer.isActive():
                self.detect_timer.stop()
        else:
            if self.flash_timer.isActive():
                self.flash_timer.stop()
                self.last_color = None

            # Nếu KHÔNG bắn và KHÔNG detect -> Trả về màu tĩnh
            if not self.detect_timer.isActive():
                if self.last_color != color:
                    self.lbl.setStyleSheet(
                        f"color: {color}; font-weight: 900; font-family: 'Segoe UI'; font-size: 10px; border: none; background: transparent;"
                    )
                    self.frame.setStyleSheet(
                        "QFrame { background-color: rgba(10, 10, 10, 160); border: 1px solid #444444; border-radius: 6px; }"
                    )
                    self.last_color = color
