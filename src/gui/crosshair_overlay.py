import ctypes

import win32api
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget


# Hiển thị tâm ảo nổi trên màn hình
class CrosshairOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Cấu hình cửa sổ trong suốt, xuyên thấu
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Kích thước toàn màn hình
        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        self.setGeometry(0, 0, w, h)

        self.active = False
        self.style = "Style 1"
        self.color = QColor(255, 255, 255)
        self.size = 4

        # ADS Hide Logic
        self.ads_mode = "HOLD"  # Default to HOLD
        self.ads_active = False  # State for TOGGLE mode
        self.rmb_prev = False  # For edge detection

        self.timer_ads = QTimer(self)
        self.timer_ads.timeout.connect(self.check_ads)
        self.timer_ads.start(50)  # Fast check

        if self.active:
            self.show()  # Show immediately

        # Bật tàng hình mức 1 duy nhất 1 lần để lách ShadowPlay
        QTimer.singleShot(500, lambda: self.set_capture_invisible(int(self.winId())))

    def set_capture_invisible(self, hwnd_int):
        """TẮT Tàng hình cho Tâm theo yêu cầu (WDA=0)"""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
            user32.SetWindowDisplayAffinity(wintypes.HWND(hwnd_int), wintypes.DWORD(0))
        except Exception:
            pass

    def showEvent(self, event):
        """Đảm bảo Tâm luôn hiện (không tàng hình)"""
        super().showEvent(event)
        # Không gọi tàng hình ở đây

    def check_ads(self):
        if not self.active:
            return
        if self.ads_mode == "OFF":
            if not self.isVisible():
                self.show()
            return

        rmb_down = win32api.GetKeyState(0x02) < 0

        if self.ads_mode == "HOLD":
            # Hold RMB -> Hide. Release -> Show.
            if rmb_down:
                if self.isVisible():
                    self.hide()
            else:
                if not self.isVisible():
                    self.show()

        elif self.ads_mode == "TOGGLE":
            # Toggle on Press
            if rmb_down and not self.rmb_prev:  # On Press
                self.ads_active = not self.ads_active
                if self.ads_active:
                    self.hide()
                else:
                    self.show()
            self.rmb_prev = rmb_down

    def set_ads_mode(self, mode):
        self.ads_mode = mode
        self.ads_active = False  # Reset state
        if self.active:
            self.show()

    def reset_toggle_state(self):
        """Gọi sau reload để tâm hiện lại — chỉ dùng khi TOGGLE mode"""
        if self.ads_mode == "TOGGLE":
            self.ads_active = False
            if self.active:
                self.show()

    def set_active(self, active):
        self.active = active
        self.update()  # Trigger repaint
        if active:
            self.show()
        else:
            self.hide()

    def set_style(self, style):
        self.style = style
        self.update()

    def set_color(self, color_name):
        colors = {
            "Đỏ": QColor(255, 30, 30),
            "Đỏ Cam": QColor(255, 69, 0),
            "Cam": QColor(255, 140, 0),
            "Vàng": QColor(255, 255, 0),
            "Xanh Lá": QColor(0, 255, 0),
            "Xanh Ngọc": QColor(0, 255, 255),
            "Xanh Dương": QColor(0, 180, 255),
            "Tím": QColor(180, 0, 255),
            "Tím Hồng": QColor(255, 60, 255),
            "Hồng": QColor(255, 105, 180),
            "Trắng": QColor(255, 255, 255),
            "Bạc": QColor(192, 192, 192),
        }
        self.color = colors.get(color_name, QColor(255, 30, 30))
        self.update()

    def paintEvent(self, event):
        if not self.active:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center Point (Vẽ ở giữa cửa sổ 100x100)
        cx = self.width() // 2
        cy = self.height() // 2

        # --- DRAWING HELPER ---
        def draw_shape(p, style, size):
            if style == "1: Gap Cross":
                gap = 4
                l = 8
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy - gap - l, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)
            elif style == "2: T-Shape":
                gap = 4
                l = 8
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)
            elif style == "3: Circle Dot":
                p.drawEllipse(QPoint(cx, cy), size, size)
                p.drawEllipse(QPoint(cx, cy), 1, 1)
            elif style == "5: Classic":
                l = 10
                p.drawLine(cx - l, cy, cx + l, cy)
                p.drawLine(cx, cy - l, cx, cy + l)
            elif style == "6: Micro Dot":
                p.drawEllipse(QPoint(cx, cy), 2, 2)
            elif style == "7: Hollow Box":
                p.drawRect(cx - 3, cy - 3, 6, 6)
            elif style == "8: Cross + Dot":
                gap = 4
                l = 8
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy - gap - l, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)
                p.drawEllipse(QPoint(cx, cy), 1, 1)
            elif style == "9: Chevron":
                p.drawLine(cx - 6, cy + 6, cx, cy)
                p.drawLine(cx + 6, cy + 6, cx, cy)
            elif style == "10: X-Shape":
                l = 6
                gap = 3
                p.drawLine(cx - gap - l, cy - gap - l, cx - gap, cy - gap)
                p.drawLine(cx + gap + l, cy + gap + l, cx + gap, cy + gap)
                p.drawLine(cx - gap - l, cy + gap + l, cx - gap, cy + gap)
                p.drawLine(cx + gap + l, cy - gap - l, cx + gap, cy - gap)
            elif style == "11: Diamond":
                p.drawLine(cx, cy - 6, cx + 6, cy)
                p.drawLine(cx + 6, cy, cx, cy + 6)
                p.drawLine(cx, cy + 6, cx - 6, cy)
                p.drawLine(cx - 6, cy, cx, cy - 6)
            elif style == "13: Triangle":
                p.drawLine(cx, cy - 6, cx - 6, cy + 4)
                p.drawLine(cx - 6, cy + 4, cx + 6, cy + 4)
                p.drawLine(cx + 6, cy + 4, cx, cy - 6)
            elif style == "14: Square Dot":
                p.drawRect(cx - 2, cy - 2, 4, 4)
            elif style == "17: Bracket Dot":
                p.drawEllipse(QPoint(cx, cy), 1, 1)
                p.drawArc(cx - 6, cy - 6, 12, 12, 135 * 16, 90 * 16)
                p.drawArc(cx - 6, cy - 6, 12, 12, -45 * 16, 90 * 16)
            elif style == "18: Shuriken":
                l = 8
                offset = 2
                p.drawLine(cx - offset, cy - offset, cx - offset, cy - offset - l)
                p.drawLine(cx + offset, cy + offset, cx + offset, cy + offset + l)
                p.drawLine(cx - offset - l, cy + offset, cx - offset, cy + offset)
                p.drawLine(cx + offset, cy - offset, cx + offset + l, cy - offset)
                p.drawEllipse(QPoint(cx, cy), 1, 1)
            elif style == "19: Center Gap":
                gap = 6
                l = 6
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy - gap - l, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)
                p.drawEllipse(QPoint(cx, cy), 2, 2)
            elif style == "22: Plus Dot":
                p.drawEllipse(QPoint(cx, cy), 2, 2)
                p.drawLine(cx - 5, cy, cx + 5, cy)
                p.drawLine(cx, cy - 5, cx, cy + 5)
            elif style == "23: V-Shape":
                p.drawLine(cx - 6, cy - 6, cx, cy)
                p.drawLine(cx + 6, cy - 6, cx, cy)
            elif style == "24: Star":
                l = 6
                p.drawLine(cx - l, cy, cx + l, cy)
                p.drawLine(cx, cy - l, cx, cy + l)
                p.drawLine(cx - l + 2, cy - l + 2, cx + l - 2, cy + l - 2)
                p.drawLine(cx - l + 2, cy + l - 2, cx + l - 2, cy - l + 2)
            else:
                # Default fallback
                gap = 4
                l = 8
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy - gap - l, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)

        base_size = 10
        if self.style == "6: Micro Dot":
            base_size = 2

        solid_brush_styles = [
            "6: Micro Dot",
            "14: Square Dot",
            "19: Center Gap",
            "22: Plus Dot",
        ]

        # 1. OUTLINE (Black, 4px)
        pen_outline = QPen(QColor(0, 0, 0, 255))
        pen_outline.setWidth(4)
        pen_outline.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_outline)
        if self.style in solid_brush_styles:
            painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)

        draw_shape(painter, self.style, base_size)

        # 2. CORE (Solid, 2px)
        pen_core = QPen(self.color)
        pen_core.setWidth(2)
        pen_core.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_core)
        if self.style in solid_brush_styles:
            painter.setBrush(QBrush(self.color))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)

        draw_shape(painter, self.style, base_size)
