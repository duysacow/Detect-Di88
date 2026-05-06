from __future__ import annotations

import ctypes
import encodings.cp1252
import logging
import os
import sys
import threading
from pathlib import Path

import win32api
import win32gui

try:
    import winsound
except Exception:
    winsound = None

from PyQt6.QtCore import QEvent, QPoint, QRect, QRectF, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QFontMetrics, QIcon, QKeySequence, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStylePainter,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from src.core.path_utils import get_resource_path
from src.core.settings import SettingsManager
import src.core.utils as Utils
from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame)
from PyQt6.QtCore import Qt

APP_STYLE_QSS = ""
logger = logging.getLogger(__name__)

def create_panel(title, color_hex, obj_name):
    """Helper tạo panel cài đặt."""
    panel = QFrame()
    panel.setObjectName(obj_name)
    panel.setProperty("class", "PanelFrame")
    p_layout = QVBoxLayout(panel)
    p_layout.setContentsMargins(8, 8, 8, 8)
    p_layout.setSpacing(4)
    
    # Title Label
    lbl = QLabel(title)
    lbl.setProperty("class", "PanelHeader")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    # Dynamic color based on weapon slot
    lbl.setStyleSheet(f"color: {color_hex};")
    p_layout.addWidget(lbl)
    
    return panel, p_layout

def add_setting_row(parent_layout, label_text, value_text):
    """Helper thêm một dòng cài đặt."""
    row_layout = QHBoxLayout()
    
    lbl = QLabel(label_text)
    lbl.setFixedWidth(100)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setProperty("class", "SettingLabel")
    
    btn = QPushButton(value_text)
    btn.setProperty("class", "SettingBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(25)
    
    row_layout.addWidget(lbl)
    row_layout.addWidget(btn)
    parent_layout.addLayout(row_layout)
    
    return btn

def create_data_row(grid, row, label):
    """Helper tạo một dòng dữ liệu."""
    l = QLabel(f"{label}")
    l.setProperty("role", "row-label")
    l.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    l.setFixedHeight(20)
    l.setStyleSheet(
        "color: #87909a; font-size: 11px; font-weight: 600; "
        "background: transparent; border: none; padding: 1px 0;"
    )
    
    val = QLabel("NONE")
    val.setProperty("role", "value-label")
    val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    val.setFixedHeight(20)
    val.setStyleSheet(
        "color: #eef2f6; font-size: 12px; font-weight: 600; "
        "background: transparent; border: none; padding: 1px 0;"
    )
    
    grid.addWidget(l, row, 0)
    grid.addWidget(val, row, 1)
    
    return val


# ===== GUI/TrayManager.py =====

from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QApplication)
from PyQt6.QtGui import QIcon, QAction

class TrayManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon(self.main_window)
        
        # Load Icon
        icon_path = get_resource_path("di88vp.ico")
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("Macro By Di88")
        
        # Setup Menu
        self.setup_menu()
        
        # Connect Actions
        self.tray_icon.activated.connect(self.on_tray_activated)
        
    def setup_menu(self):
        menu = QMenu()
        
        # Restore Action
        action_show = QAction("Show", self.main_window)
        action_show.triggered.connect(self.main_window.restore_window)
        menu.addAction(action_show)
        
        # Exit Action
        action_exit = QAction("Exit", self.main_window)
        action_exit.triggered.connect(self.main_window.request_app_exit)
        menu.addAction(action_exit)
        
        self.tray_icon.setContextMenu(menu)
        
    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.main_window.restore_window()
            
    def show(self):
        self.tray_icon.show()
        
    def hide(self):
        self.tray_icon.hide()


class ResolutionNoticeDialog(QDialog):
    def __init__(self, resolution_text: str, parent=None):
        super().__init__(parent)
        self._drag_offset: QPoint | None = None
        self.setWindowTitle("Macro & Aim By Di88")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(432)

        icon_path = get_resource_path("di88vp.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(
            """
            QDialog {
                background: transparent;
                border: none;
            }
            QFrame#Card {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #1c2128,
                    stop: 0.55 #171c23,
                    stop: 1 #14181e
                );
                border: 1px solid #43515e;
                border-radius: 14px;
            }
            QLabel#HeaderTitle {
                color: #f5f8fc;
                font-size: 13px;
                font-weight: 800;
                background: transparent;
            }
            QLabel#Title {
                color: #ffffff;
                font-size: 17px;
                font-weight: 900;
                background: transparent;
            }
            QLabel#Body {
                color: #dde8f4;
                font-size: 12px;
                font-weight: 700;
                background: transparent;
            }
            QLabel#Badge {
                background: qradialgradient(
                    cx: 0.42, cy: 0.35, radius: 1.0,
                    stop: 0 #1e6c96,
                    stop: 0.58 #124e73,
                    stop: 1 #0d3855
                );
                color: #eff9ff;
                border: 1px solid #6fcff4;
                border-radius: 26px;
                font-size: 27px;
                font-weight: 800;
                min-width: 52px;
                max-width: 52px;
                min-height: 52px;
                max-height: 52px;
            }
            QPushButton#CloseBtn {
                background: transparent;
                color: #f0f4f8;
                border: none;
                font-size: 17px;
                font-weight: 800;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton#CloseBtn:hover {
                color: #ff8f8f;
            }
            QPushButton#PrimaryBtn {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2a323b,
                    stop: 1 #242b33
                );
                color: #ffffff;
                border: 1px solid #6f808d;
                border-radius: 8px;
                padding: 9px 18px;
                font-size: 12px;
                font-weight: 800;
                min-width: 128px;
            }
            QPushButton#PrimaryBtn:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #32404d,
                    stop: 1 #2a3641
                );
                border: 1px solid #8db3d1;
            }
            QPushButton#PrimaryBtn:pressed {
                background: #23303a;
                border: 1px solid #78a6c9;
            }
            QFrame#AccentLine {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #184f7e,
                    stop: 0.5 #2fb6ee,
                    stop: 1 #184f7e
                );
                border: none;
                border-radius: 1px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("Card")
        root.addWidget(card)

        card_shadow = QGraphicsDropShadowEffect(card)
        card_shadow.setBlurRadius(32)
        card_shadow.setOffset(0, 10)
        card_shadow.setColor(QColor(0, 0, 0, 155))
        card.setGraphicsEffect(card_shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 18)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        header_icon = QLabel()
        header_icon.setPixmap(QIcon(icon_path).pixmap(16, 16))
        header_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_row.addWidget(header_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        header_title = QLabel("Macro & Aim By Di88")
        header_title.setObjectName("HeaderTitle")
        header_row.addWidget(header_title, 1, Qt.AlignmentFlag.AlignVCenter)

        close_button = QPushButton("\u00D7")
        close_button.setObjectName("CloseBtn")
        close_button.clicked.connect(self.reject)
        header_row.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(header_row)

        accent = QFrame()
        accent.setObjectName("AccentLine")
        accent.setFixedHeight(2)
        layout.addWidget(accent)

        badge = QLabel("i")
        badge.setObjectName("Badge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(2)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignCenter)

        title = QLabel("\u0110\u1ed9\u0020\u0050\u0068\u00e2\u006e\u0020\u0047\u0069\u1ea3\u0069")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        body = QLabel(
            f"\u0110\u0061\u006e\u0067\u0020\u0073\u1eed\u0020\u0064\u1ee5\u006e\u0067\u0020\u0111\u1ed9\u0020\u0070\u0068\u00e2\u006e\u0020\u0067\u0069\u1ea3\u0069\u003a\u0020{resolution_text}"
        )
        body.setObjectName("Body")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        body.setContentsMargins(12, 0, 12, 0)
        layout.addWidget(body)

        ok_button = QPushButton("OK")
        ok_button.setObjectName("PrimaryBtn")
        ok_button.clicked.connect(self.accept)
        layout.addSpacing(2)
        layout.addWidget(ok_button, 0, Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()
        self.setFixedHeight(self.sizeHint().height())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class ModernDialog(QDialog):
    def __init__(self, parent, title, message, buttons=("Yes", "No"), is_question=True):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.result_value = None
        
        # Ensure focus and activation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.activateWindow()
        self.raise_()
        
        # Main Container
        self.container = QFrame(self)
        self.container.setObjectName("DialogContainer")
        self.container.setStyleSheet("""
            QFrame#DialogContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b2b2b, stop:1 #1a1a1a);
                border: 2px solid #444;
                border-radius: 12px;
            }
            QLabel#DialogTitle {
                color: #ff6b6b;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                background-color: rgba(0,0,0,0.2);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QLabel#DialogMessage {
                color: #ddd;
                font-size: 13px;
                padding: 20px;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #444;
                border: 1px solid #ff6b6b;
            }
            QPushButton#PrimaryBtn {
                background-color: #ff6b6b;
                border: none;
            }
            QPushButton#PrimaryBtn:hover {
                background-color: #ff5252;
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(0)
        
        # Title
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("DialogTitle")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title)
        
        # Message
        self.lbl_msg = QLabel(message)
        self.lbl_msg.setObjectName("DialogMessage")
        self.lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_msg.setWordWrap(True)
        layout.addWidget(self.lbl_msg)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(15, 0, 15, 0)
        btn_layout.setSpacing(12)
        
        btn_layout.addStretch()
        for i, btn_text in enumerate(buttons):
            btn = QPushButton(btn_text)
            if i == 0 and is_question:
                btn.setObjectName("PrimaryBtn")
            
            # Using a more reliable way to connect buttons
            btn.clicked.connect(self.make_callback(btn_text))
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
            
        layout.addLayout(btn_layout)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        
        self.setFixedSize(420, 190)

    def make_callback(self, text):
        # Handle the 'checked' argument from clicked signal to avoid TypeError
        return lambda checked=False: self.on_click(text)

    def on_click(self, value):
        self.result_value = value
        self.done(1)

class AppNoticeDialog:
    @staticmethod
    def question(parent, title, message, buttons=("Có", "Không")):
        dlg = ModernDialog(parent, title, message, buttons=buttons, is_question=True)
        dlg.exec()
        return dlg.result_value == buttons[0]

    @staticmethod
    def information(parent, title, message):
        dlg = ModernDialog(parent, title, message, buttons=("OK",), is_question=False)
        dlg.exec()

    @staticmethod
    def warning(parent, title, message):
        dlg = ModernDialog(parent, title, message, buttons=("Hiểu rồi",), is_question=False)
        dlg.exec()

    @staticmethod
    def custom_choice(parent, title, message, buttons=("Tắt", "Xuống Tray", "Hủy")):
        dlg = ModernDialog(parent, title, message, buttons=buttons, is_question=True)
        dlg.exec()
        return dlg.result_value

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class HomePanelBuilder:
    def __init__(self, owner):
        self.owner = owner

    def build(self):
        owner = self.owner

        owner.home_page = QWidget()
        owner.home_page.setObjectName("HomePage")

        layout = QVBoxLayout(owner.home_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        owner.home_content_panel = QFrame()
        owner.home_content_panel.setObjectName("HomeContentPanel")
        owner.home_content_panel.setStyleSheet(
            """
            QFrame#HomeContentPanel {
                background: #171717;
                border: 1px solid #343434;
                border-radius: 14px;
            }
            """
        )

        panel_layout = QVBoxLayout(owner.home_content_panel)
        panel_layout.setContentsMargins(14, 14, 14, 14)
        panel_layout.setSpacing(14)

        panel_layout.addWidget(self._build_metric_row())

        summaries_row = QHBoxLayout()
        summaries_row.setContentsMargins(0, 0, 0, 0)
        summaries_row.setSpacing(12)
        summaries_row.addWidget(
            self._build_summary_card(
                object_name="HomeMacroSummary",
                title="MACRO STATUS",
                title_color="#ff8f8f",
                rows=[
                    ("Tư thế", "home_macro_stance_value", "ĐỨNG", "#f2f2f2"),
                    ("ADS", "home_macro_ads_value", "HOLD", "#66ffc2"),
                    ("Chế Độ Chụp", "home_macro_capture_value", "DXCAM", "#89d4ff"),
                ],
                toggle_attr="home_macro_toggle_btn",
                toggle_handler=getattr(owner, "toggle_home_macro", None),
            ),
            1,
        )
        summaries_row.addWidget(
            self._build_summary_card(
                object_name="HomeAimSummary",
                title="AIM STATUS",
                title_color="#73f0ff",
                rows=[
                    ("Model", "home_aim_model_value", "N/A", "#f2f2f2"),
                    ("Backend", "home_aim_backend_value", "Chưa nạp", "#f2f2f2"),
                    ("Chế Độ Chụp", "home_aim_capture_value", "DirectX", "#89d4ff"),
                ],
                toggle_attr="home_aim_toggle_btn",
                toggle_handler=getattr(owner, "toggle_home_aim", None),
            ),
            1,
        )
        panel_layout.addLayout(summaries_row)

        layout.addWidget(owner.home_content_panel)
        layout.addStretch(1)
        return owner.home_page

    def _build_metric_card(
        self,
        title: str,
        value_attr: str,
        text: str,
        color: str,
        unit_text: str,
        *,
        badge_text: str = "",
        badge_color: str = "#79ff9f",
        badge_attr: str | None = None,
        helper_text: str = "",
        tone: str = "#101010",
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("HomeMetricCard")
        card.setStyleSheet(
            f"""
            QFrame#HomeMetricCard {{
                background: {tone};
                border: 1px solid #2f2f2f;
                border-radius: 11px;
            }}
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
            """
        )

        badge_label = QLabel(badge_text)
        badge_label.setStyleSheet(
            f"""
            QLabel {{
                color: {badge_color};
                font-size: 10px;
                font-weight: 900;
                background: transparent;
                border: none;
            }}
            """
        )
        badge_label.setVisible(bool(badge_text))
        if badge_attr:
            setattr(self.owner, badge_attr, badge_label)

        title_row.addWidget(title_label, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch(1)
        title_row.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignVCenter)

        value_row = QHBoxLayout()
        value_row.setContentsMargins(0, 0, 0, 0)
        value_row.setSpacing(6)

        value_label = QLabel(text)
        value_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 19px;
                font-weight: 900;
                background: transparent;
                border: none;
            }}
            """
        )
        value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        setattr(self.owner, value_attr, value_label)

        unit_label = QLabel(unit_text)
        unit_label.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            """
        )
        unit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        value_row.addWidget(value_label, 0, Qt.AlignmentFlag.AlignVCenter)
        value_row.addWidget(unit_label, 0, Qt.AlignmentFlag.AlignVCenter)
        value_row.addStretch(1)

        helper_label = QLabel(helper_text)
        helper_label.setStyleSheet(
            """
            QLabel {
                color: #6f767e;
                font-size: 9px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """
        )
        helper_label.setVisible(bool(helper_text))

        status_label = QLabel("")
        status_label.setStyleSheet(
            """
            QLabel {
                color: #79ff9f;
                font-size: 9px;
                font-weight: 800;
                background: transparent;
                border: none;
            }
            """
        )
        status_label.hide()
        setattr(self.owner, f"{value_attr}_hint", status_label)

        layout.addLayout(title_row)
        layout.addLayout(value_row)
        layout.addWidget(helper_label)
        layout.addWidget(status_label)
        layout.addStretch(1)
        return card

    def _build_metric_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(
            self._build_metric_card(
                title="FPS",
                value_attr="home_metric_fps_value",
                text="0",
                color="#8dffb1",
                unit_text="FPS",
                badge_text="\u2022 T\u1ea1m D\u1eebng",
                badge_color="#ff7e7e",
                badge_attr="home_metric_fps_badge",
                helper_text="Khung hình thời gian thực",
                tone="#101612",
            ),
            1,
        )
        layout.addWidget(
            self._build_metric_card(
                title="Độ Trễ",
                value_attr="home_metric_inf_value",
                text="0",
                color="#ffd7a1",
                unit_text="MS",
                badge_text="\u2022 T\u1ea1m D\u1eebng",
                badge_color="#ff7e7e",
                badge_attr="home_metric_inf_badge",
                helper_text="Độ trễ suy luận hiện tại",
                tone="#17130f",
            ),
            1,
        )
        return row

    def _summary_row_frame(
        self,
        label_text: str,
        value_attr: str,
        value_text: str,
        value_color: str,
    ) -> QFrame:
        row = QFrame()
        row.setStyleSheet(
            """
            QFrame {
                background: #121212;
                border: 1px solid #2f2f2f;
                border-radius: 9px;
            }
            """
        )

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        label = QLabel(label_text)
        label.setStyleSheet(
            """
            QLabel {
                color: #a7a7a7;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                border: none;
            }
            """
        )

        value = QLabel(value_text)
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        value.setStyleSheet(
            f"""
            QLabel {{
                color: {value_color};
                font-size: 12px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}
            """
        )
        setattr(self.owner, value_attr, value)

        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(value)
        return row

    def _build_summary_card(
        self,
        object_name: str,
        title: str,
        title_color: str,
        rows: list[tuple[str, str, str, str]],
        *,
        toggle_attr: str | None = None,
        toggle_handler=None,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName(object_name)
        card.setStyleSheet(
            """
            QFrame {
                background: #151515;
                border: 1px solid #343434;
                border-radius: 12px;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)

        accent_dot = QFrame()
        accent_dot.setFixedSize(8, 8)
        accent_dot.setStyleSheet(f"background: {title_color}; border: none; border-radius: 4px;")

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"""
            QLabel {{
                color: {title_color};
                font-size: 12px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
            """
        )

        title_row.addWidget(accent_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addWidget(title_label)
        title_row.addStretch(1)

        if toggle_attr:
            toggle_btn = QPushButton("OFF")
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle_btn.setFixedSize(52, 24)
            toggle_btn.setStyleSheet(
                """
                QPushButton {
                    color: #ff7b7b;
                    background: #1a1111;
                    border: 1px solid #5a2525;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 900;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    border-color: #7a3434;
                }
                """
            )
            if callable(toggle_handler):
                toggle_btn.clicked.connect(toggle_handler)
            setattr(self.owner, toggle_attr, toggle_btn)
            title_row.addWidget(toggle_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(title_row)

        for label_text, value_attr, value_text, value_color in rows:
            layout.addWidget(self._summary_row_frame(label_text, value_attr, value_text, value_color))

        return card

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class AimPanelBuilder:
    def __init__(self, owner, section_header_cls):
        self.owner = owner
        self.section_header_cls = section_header_cls

    def build(self):
        owner = self.owner

        owner.aim_workspace = QWidget()
        owner.aim_workspace.setObjectName("AimWorkspace")
        owner.aim_workspace.setStyleSheet("background: transparent; border: none;")

        aim_layout = QVBoxLayout(owner.aim_workspace)
        aim_layout.setContentsMargins(0, 0, 0, 0)
        aim_layout.setSpacing(6)

        self._build_runtime_bindings()
        self._build_display_box()
        self._build_model_box()
        self._build_capture_box()
        self._build_shortcuts_box()
        self._build_settings_box()
        self._build_smoothing_box()
        self._build_listing_box()
        self._build_advanced_toggles_box()

        # Giữ control để không gãy save/load, nhưng ẩn các block AIM chi tiết khỏi tab.
        for widget in (
            owner.aim_shortcuts_box,
            owner.aim_settings_box,
            owner.aim_smoothing_box,
            owner.aim_display_box,
            owner.aim_listing_box,
            owner.aim_advanced_box,
        ):
            widget.hide()

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(6)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)
        left_col.addWidget(owner.aim_model_box)
        left_col.addStretch(1)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)
        right_col.addWidget(owner.aim_capture_box)
        right_col.addStretch(1)

        main_row.addLayout(left_col, 1)
        main_row.addLayout(right_col, 1)

        aim_layout.addLayout(main_row)
        aim_layout.addStretch()

        return owner.aim_workspace

    def _group_box(self, attr_name, object_name):
        owner = self.owner
        box = MacroTitledBox("", object_name)
        setattr(owner, attr_name, box)
        return box

    def _header(self, attr_name, text, parent):
        if isinstance(parent, MacroTitledBox):
            parent.set_title(text)
            header = QWidget(parent)
            header.setFixedHeight(0)
            header.hide()
        else:
            header = self.section_header_cls(text, parent)
        setattr(self.owner, attr_name, header)
        return header

    def _create_button_row(self, label_attr, btn_attr, label_text, button_text, target_key):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        label = QLabel(label_text)
        label.setFixedWidth(126)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        button = QPushButton(button_text)
        button.setProperty("role", "setting-btn")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(24)
        owner.style_setting_button(button)
        button.clicked.connect(lambda: owner.start_keybind_listening(button, target_key))

        setattr(owner, label_attr, label)
        setattr(owner, btn_attr, button)

        row.addWidget(label)
        row.addWidget(button, stretch=1)
        return row

    def _create_slider_row(
        self,
        label_attr,
        slider_attr,
        value_attr,
        label_text,
        value_text,
        minimum,
        maximum,
        value,
        callback,
        *,
        value_width=44,
        step=1,
        page_step=1,
        label_width=104,
    ):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setFixedWidth(label_width)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setSingleStep(step)
        slider.setPageStep(page_step)
        slider.setValue(value)
        slider.setFixedHeight(20)
        slider.setMinimumWidth(120)
        slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        owner.style_scope_slider(slider)

        value_label = QLabel(value_text)
        value_label.setFixedWidth(value_width)
        value_label.setFixedHeight(24)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owner.style_scope_value_label(value_label)

        slider.valueChanged.connect(callback)

        setattr(owner, label_attr, label)
        setattr(owner, slider_attr, slider)
        setattr(owner, value_attr, value_label)

        row.addWidget(label)
        row.addWidget(slider, stretch=1)
        row.addWidget(value_label)
        return row

    def _create_combo_row(self, label_attr, combo_attr, label_text, options, default_text, callback=None):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setFixedWidth(118)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        combo = QComboBox()
        combo.setFixedHeight(24)
        combo.setCursor(Qt.CursorShape.PointingHandCursor)
        combo.addItems(list(options))
        combo.setCurrentText(default_text)
        combo.setStyleSheet(
            """
            QComboBox {
                background-color: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                selection-background-color: #2a2a2a;
            }
            """
        )
        if callback is not None:
            combo.currentTextChanged.connect(callback)

        setattr(owner, label_attr, label)
        setattr(owner, combo_attr, combo)

        row.addWidget(label)
        row.addWidget(combo, stretch=1)
        return row

    def _create_two_column_slider_block(self, left_rows, right_rows):
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent; border: none;")

        content = QHBoxLayout(wrapper)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(12)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(6)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(6)

        for row in left_rows:
            left_col.addLayout(row)
        left_col.addStretch(1)

        for row in right_rows:
            right_col.addLayout(row)
        right_col.addStretch(1)

        content.addLayout(left_col, 1)
        content.addLayout(right_col, 1)
        return wrapper

    def _build_runtime_bindings(self):
        owner = self.owner
        owner.btn_aim_status = QPushButton("AIM : OFF")
        owner.btn_aim_status.setCursor(Qt.CursorShape.ForbiddenCursor)
        owner.update_aim_status_style(False)
        owner.btn_aim_status.hide()

        owner.lbl_aim_fps = QLabel("FPS : --")
        owner.lbl_aim_fps.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owner.update_aim_metric_style(owner.lbl_aim_fps, "FPS : --", "#8dffb1")
        owner.lbl_aim_fps.hide()

        owner.lbl_aim_inf = QLabel("INF : --")
        owner.lbl_aim_inf.setAlignment(Qt.AlignmentFlag.AlignCenter)
        owner.update_aim_metric_style(owner.lbl_aim_inf, "INF : --", "#ffd7a1")
        owner.lbl_aim_inf.hide()

    def _build_display_box(self):
        owner = self.owner
        owner.aim_display_box = self._group_box("aim_display_box", "AimDisplayBox")
        layout = owner.aim_display_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_display", "Hiển Thị", owner.aim_display_box))

        display_toggle_row = QHBoxLayout()
        display_toggle_row.setContentsMargins(0, 0, 0, 0)
        display_toggle_row.setSpacing(18)

        owner.aim_chk_show_fov = QCheckBox("Hiển Thị FOV")
        owner.aim_chk_show_detect = QCheckBox("Hiển Thị Khung Detect")

        for checkbox in (owner.aim_chk_show_fov, owner.aim_chk_show_detect):
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #e6e6e6;
                    font-size: 11px;
                    font-weight: 700;
                    spacing: 6px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #5a5a5a;
                    background: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background: #ff7070;
                    border: 1px solid #ff9c9c;
                }
                """
            )
            checkbox.stateChanged.connect(owner.on_aim_display_toggle_changed)
            display_toggle_row.addWidget(checkbox)
        display_toggle_row.addStretch(1)
        layout.addLayout(display_toggle_row)

    def _build_model_box(self):
        owner = self.owner
        owner.aim_model_box = self._group_box("aim_model_box", "AimModelBox")
        owner.aim_model_box.setFixedHeight(62)
        layout = owner.aim_model_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 6)
        layout.setSpacing(4)
        layout.addWidget(self._header("header_aim_model", "Model", owner.aim_model_box))

        owner.combo_aim_model = QComboBox()
        owner.combo_aim_model.setFixedHeight(26)
        owner.combo_aim_model.setCursor(Qt.CursorShape.PointingHandCursor)
        owner.combo_aim_model.setStyleSheet(
            """
            QComboBox {
                background-color: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                selection-background-color: #2a2a2a;
            }
            """
        )
        owner.combo_aim_model.currentIndexChanged.connect(owner.on_aim_model_changed_safe)
        layout.addWidget(owner.combo_aim_model)

        owner.aim_model_status_row = QWidget()
        status_row_layout = QHBoxLayout(owner.aim_model_status_row)
        status_row_layout.setContentsMargins(2, 0, 2, 0)
        status_row_layout.setSpacing(6)
        owner.lbl_aim_model_title = QLabel("Models")
        owner.lbl_aim_model_sep = QLabel(":")
        owner.lbl_aim_model_status = QLabel("Chưa tải")
        for widget in (owner.lbl_aim_model_title, owner.lbl_aim_model_sep, owner.lbl_aim_model_status):
            widget.setStyleSheet(
                """
                QLabel {
                    color: #cfcfcf;
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }
                """
            )
            status_row_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        status_row_layout.addStretch(1)
        layout.addWidget(owner.aim_model_status_row)

        owner.lbl_aim_mode_info = QLabel("Chế Độ: Tăng Tốc")
        owner.lbl_aim_mode_info.setStyleSheet(
            """
            QLabel {
                color: #d7d7d7;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                padding-left: 2px;
            }
            """
        )
        layout.addWidget(owner.lbl_aim_mode_info)

        owner.lbl_aim_backend_info = QLabel("Backend: Chưa nạp")
        owner.lbl_aim_backend_info.setStyleSheet(
            """
            QLabel {
                color: #d7d7d7;
                font-size: 11px;
                font-weight: 700;
                background: transparent;
                padding-left: 2px;
            }
            """
        )
        layout.addWidget(owner.lbl_aim_backend_info)
        owner.aim_model_status_row.hide()
        owner.lbl_aim_mode_info.hide()
        owner.lbl_aim_backend_info.hide()

        owner.aim_model_meta_row = QWidget()
        meta_layout = QHBoxLayout(owner.aim_model_meta_row)
        meta_layout.setContentsMargins(2, 0, 2, 0)
        meta_layout.setSpacing(8)

        owner.lbl_aim_model_status_meta = QLabel("Runtime: Native DLL chờ")
        owner.lbl_aim_runtime_meta = QLabel("Backend: Chưa nạp")

        for widget, color in (
            (owner.lbl_aim_model_status_meta, "#cfcfcf"),
            (owner.lbl_aim_runtime_meta, "#d7d7d7"),
        ):
            widget.setStyleSheet(
                f"""
                QLabel {{
                    color: {color};
                    font-size: 10px;
                    font-weight: 700;
                    background: #1b1b1b;
                    border: 1px solid #3a3a3a;
                    border-radius: 5px;
                    padding: 2px 6px;
                }}
                """
            )
            meta_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        meta_layout.addStretch(1)
        owner.aim_model_meta_row.hide()
        layout.addWidget(owner.aim_model_meta_row)

    def _build_capture_box(self):
        owner = self.owner
        owner.aim_capture_box = self._group_box("aim_capture_box", "AimCaptureBox")
        owner.aim_capture_box.setFixedHeight(62)
        layout = owner.aim_capture_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 6)
        layout.setSpacing(4)
        layout.addWidget(self._header("header_aim_capture", "Phương Thức Chụp", owner.aim_capture_box))

        owner.combo_aim_capture = QComboBox()
        owner.combo_aim_capture.setFixedHeight(26)
        owner.combo_aim_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        owner.combo_aim_capture.setStyleSheet(
            """
            QComboBox {
                background-color: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #f2f2f2;
                border: 1px solid #3a3a3a;
                selection-background-color: #2a2a2a;
            }
            """
        )
        owner.combo_aim_capture.addItems(["DirectX", "GDI+"])
        owner.combo_aim_capture.currentTextChanged.connect(owner.set_aim_capture_mode_ui)
        layout.addWidget(owner.combo_aim_capture)

    def _build_shortcuts_box(self):
        owner = self.owner
        owner.aim_shortcuts_box = self._group_box("aim_shortcuts_box", "AimShortcutsBox")
        layout = owner.aim_shortcuts_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_shortcuts", "Phím Tắt", owner.aim_shortcuts_box))

        layout.addLayout(
            self._create_button_row(
                "aim_lbl_emergency_stop",
                "aim_btn_emergency_stop",
                "Bật/Tắt Aim",
                "F8",
                "aim_emergency_stop_key",
            )
        )
        layout.addLayout(
            self._create_button_row(
                "aim_lbl_primary",
                "aim_btn_primary",
                "Phím Aim",
                "RIGHT MOUSE",
                "aim_primary_key",
            )
        )
        layout.addLayout(
            self._create_button_row(
                "aim_lbl_secondary",
                "aim_btn_secondary",
                "Phím Aim Phụ",
                "LEFT CTRL",
                "aim_secondary_key",
            )
        )
        layout.addLayout(
            self._create_button_row(
                "aim_lbl_trigger",
                "aim_btn_trigger",
                "Bật/Tắt Trigger",
                "F7",
                "aim_trigger_key",
            )
        )

    def _build_settings_box(self):
        owner = self.owner
        owner.aim_settings_box = self._group_box("aim_settings_box", "AimSettingsBox")
        layout = owner.aim_settings_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_settings", "Cài Đặt", owner.aim_settings_box))

        for row in (
            self._create_slider_row(
                "aim_lbl_fov",
                "aim_slider_fov",
                "aim_fov_value_label",
                "Vùng FOV",
                "300",
                10,
                640,
                300,
                owner.update_aim_fov_label,
                page_step=10,
            ),
            self._create_slider_row(
                "aim_lbl_confidence",
                "aim_slider_confidence",
                "aim_confidence_value_label",
                "Ngưỡng Tin Cậy AI",
                "45%",
                1,
                100,
                45,
                owner.update_aim_confidence_label,
                page_step=5,
            ),
            self._create_slider_row(
                "aim_lbl_trigger_delay",
                "aim_slider_trigger_delay",
                "aim_trigger_delay_value_label",
                "Độ Trễ Tự Bắn",
                "100 ms",
                10,
                1000,
                100,
                owner.update_aim_trigger_delay_label,
                value_width=60,
                step=10,
                page_step=50,
            ),
            self._create_slider_row(
                "aim_lbl_capture_fps",
                "aim_slider_capture_fps",
                "aim_capture_fps_value_label",
                "Tốc Độ Chụp (FPS)",
                "144",
                1,
                240,
                144,
                owner.update_aim_capture_fps_label,
                page_step=10,
            ),
            self._create_combo_row(
                "aim_lbl_target_priority",
                "combo_aim_target_priority",
                "Ưu Tiên",
                ("Body -> Head", "Head -> Body"),
                "Body -> Head",
            ),
        ):
            layout.addLayout(row)

    def _build_smoothing_box(self):
        owner = self.owner
        owner.aim_smoothing_box = self._group_box("aim_smoothing_box", "AimSmoothingBox")
        layout = owner.aim_smoothing_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_smoothing", "Độ Nhạy / Độ Mượt", owner.aim_smoothing_box))

        for row in (
            self._create_slider_row(
                "aim_lbl_sensitivity",
                "aim_slider_sensitivity",
                "aim_sensitivity_value_label",
                "Độ Nhạy Chuột",
                "0.80",
                1,
                100,
                80,
                owner.update_aim_sensitivity_label,
            ),
            self._create_slider_row(
                "aim_lbl_ema",
                "aim_slider_ema",
                "aim_ema_value_label",
                "Độ Mượt",
                "0.50",
                1,
                100,
                50,
                owner.update_aim_ema_label,
            ),
            self._create_slider_row(
                "aim_lbl_jitter",
                "aim_slider_jitter",
                "aim_jitter_value_label",
                "Độ Rung Chuột",
                "4",
                0,
                15,
                4,
                owner.update_aim_jitter_label,
            ),
            self._create_slider_row(
                "aim_lbl_primary_position",
                "aim_slider_primary_position",
                "aim_primary_position_value_label",
                "Vị Trí Aim Chính",
                "50",
                0,
                100,
                50,
                owner.update_aim_primary_position_label,
                page_step=5,
            ),
            self._create_slider_row(
                "aim_lbl_secondary_position",
                "aim_slider_secondary_position",
                "aim_secondary_position_value_label",
                "Vị Trí Aim Phụ",
                "50",
                0,
                100,
                50,
                owner.update_aim_secondary_position_label,
                page_step=5,
            ),
        ):
            layout.addLayout(row)

    def _build_listing_box(self):
        owner = self.owner
        owner.aim_listing_box = self._group_box("aim_listing_box", "AimListingBox")
        owner.aim_listing_box.setFixedHeight(238)
        layout = owner.aim_listing_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_listing", "Danh Sách Liệt Kê", owner.aim_listing_box))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #151515;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #ff9fb0;
                border-radius: 3px;
                min-height: 22px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
                border: none;
            }
            """
        )

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 2, 0)
        content_layout.setSpacing(6)

        owner.aim_listing_controls = {}
        for spec in self._listing_slider_specs():
            callback = lambda value, key=spec["key"]: owner.update_aim_listing_slider_label(key, value)
            row = self._create_slider_row(
                spec["label_attr"],
                spec["slider_attr"],
                spec["value_attr"],
                spec["label"],
                spec["value_text"],
                spec["min"],
                spec["max"],
                spec["slider_default"],
                callback,
                value_width=spec.get("value_width", 44),
                step=spec.get("step", 1),
                page_step=spec.get("page_step", 5),
                label_width=108,
            )
            content_layout.addLayout(row)
            owner.aim_listing_controls[spec["key"]] = {
                "spec": spec,
                "slider": getattr(owner, spec["slider_attr"]),
                "value_label": getattr(owner, spec["value_attr"]),
            }

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _build_advanced_toggles_box(self):
        owner = self.owner
        owner.aim_advanced_box = self._group_box("aim_advanced_box", "AimAdvancedBox")
        owner.aim_advanced_box.setFixedHeight(238)
        layout = owner.aim_advanced_box.content_layout()
        layout.setContentsMargins(8, 18, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self._header("header_aim_advanced", "Tùy Chọn Nâng Cao", owner.aim_advanced_box))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #151515;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #66f0ff;
                border-radius: 3px;
                min-height: 22px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
                background: transparent;
                border: none;
            }
            """
        )

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 6, 0)
        content_layout.setSpacing(7)

        owner.aim_toggle_controls = {}
        for key, label in self._advanced_toggle_specs():
            checkbox = QCheckBox(label)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #e6e6e6;
                    font-size: 11px;
                    font-weight: 700;
                    spacing: 7px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #5a5a5a;
                    background: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background: #66f0ff;
                    border: 1px solid #9af7ff;
                }
                """
            )
            checkbox.stateChanged.connect(owner.on_aim_advanced_toggle_changed)
            content_layout.addWidget(checkbox)
            owner.aim_toggle_controls[key] = checkbox

        owner.aim_dropdown_controls = {}
        for spec in self._advanced_dropdown_specs():
            row = self._create_combo_row(
                spec["label_attr"],
                spec["combo_attr"],
                spec["label"],
                spec["options"],
                spec["default"],
                owner.on_aim_advanced_dropdown_changed,
            )
            content_layout.addLayout(row)
            owner.aim_dropdown_controls[spec["key"]] = {
                "spec": spec,
                "combo": getattr(owner, spec["combo_attr"]),
            }

        owner.aim_color_controls = {}
        for key, label, default_value in self._advanced_color_specs():
            row = self._create_action_row(
                f"aim_lbl_color_{key.replace(' ', '_').lower()}",
                f"aim_btn_color_{key.replace(' ', '_').lower()}",
                label,
                default_value,
                lambda _checked=False, color_key=key: owner.choose_aim_color(color_key),
            )
            content_layout.addLayout(row)
            owner.aim_color_controls[key] = getattr(owner, f"aim_btn_color_{key.replace(' ', '_').lower()}")

        owner.aim_file_controls = {}
        for key, label in self._advanced_file_specs():
            row = self._create_action_row(
                f"aim_lbl_file_{key.replace(' ', '_').lower()}",
                f"aim_btn_file_{key.replace(' ', '_').lower()}",
                label,
                "Chọn DLL",
                lambda _checked=False, file_key=key: owner.choose_aim_file_location(file_key),
            )
            content_layout.addLayout(row)
            owner.aim_file_controls[key] = getattr(owner, f"aim_btn_file_{key.replace(' ', '_').lower()}")

        owner.aim_minimize_controls = {}
        for key, label in self._advanced_minimize_specs():
            checkbox = QCheckBox(label)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #bfc6cf;
                    font-size: 11px;
                    font-weight: 700;
                    spacing: 7px;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #5a5a5a;
                    background: #1e1e1e;
                }
                QCheckBox::indicator:checked {
                    background: #a98cff;
                    border: 1px solid #c4b4ff;
                }
                """
            )
            checkbox.stateChanged.connect(owner.on_aim_advanced_toggle_changed)
            content_layout.addWidget(checkbox)
            owner.aim_minimize_controls[key] = checkbox

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

    def _create_action_row(self, label_attr, button_attr, label_text, button_text, callback):
        owner = self.owner
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setFixedWidth(124)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setProperty("role", "setting-label")
        owner.style_setting_label(label)

        button = QPushButton(button_text)
        button.setProperty("role", "setting-btn")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(24)
        owner.style_setting_button(button)
        button.clicked.connect(callback)

        setattr(owner, label_attr, label)
        setattr(owner, button_attr, button)

        row.addWidget(label)
        row.addWidget(button, stretch=1)
        return row

    def _advanced_toggle_specs(self):
        return [
            ("Constant AI Tracking", "Tracking Liên Tục"),
            ("Sticky Aim", "Sticky Aim"),
            ("Predictions", "Dự Đoán"),
            ("Enable Model Switch Keybind", "Bật Phím Đổi Model"),
            ("FOV", "Logic FOV"),
            ("Dynamic FOV", "FOV Động"),
            ("Third Person Support", "Góc Nhìn Thứ 3"),
            ("Masking", "Masking"),
            ("Cursor Check", "Cursor Check"),
            ("Spray Mode", "Spray Mode"),
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            ("Collect Data While Playing", "Thu Data Khi Chơi"),
            ("Auto Label Data", "Auto Label Data"),
            ("LG HUB Mouse Movement", "LG HUB Mouse"),
            # Đã làm sạch chú thích lỗi mã hóa.
            ("Debug Mode", "Debug Mode"),
            ("UI TopMost", "UI Luôn Trên Cùng"),
            ("StreamGuard", "StreamGuard"),
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
        ]

    def _advanced_dropdown_specs(self):
        return [
            {
                "key": "Prediction Method",
                "label": "Kiểu Dự Đoán",
                "label_attr": "aim_lbl_prediction_method",
                "combo_attr": "combo_aim_prediction_method",
                "default": "Kalman Filter",
                "options": ("Kalman Filter", "Shall0e's Prediction", "wisethef0x's EMA Prediction"),
            },
            {
                "key": "Detection Area Type",
                "label": "Vùng Detect",
                "label_attr": "aim_lbl_detection_area_type",
                "combo_attr": "combo_aim_detection_area_type",
                "default": "Closest to Center Screen",
                "options": ("Closest to Center Screen", "Closest to Mouse"),
            },
            {
                "key": "Aiming Boundaries Alignment",
                "label": "Căn Biên Aim",
                "label_attr": "aim_lbl_aiming_boundaries",
                "combo_attr": "combo_aim_aiming_boundaries",
                "default": "Center",
                "options": ("Center", "Top", "Bottom"),
            },
            {
                "key": "Mouse Movement Method",
                "label": "Kiểu Di Chuột",
                "label_attr": "aim_lbl_mouse_movement_method",
                "combo_attr": "combo_aim_mouse_movement_method",
                "default": "Mouse Event",
                "options": ("Mouse Event", "SendInput", "LG HUB", "Razer Synapse (Require Razer Peripheral)", "ddxoft Virtual Input Driver"),
            },
            {
                "key": "Tracer Position",
                "label": "Vị Trí Tracer",
                "label_attr": "aim_lbl_tracer_position",
                "combo_attr": "combo_aim_tracer_position",
                "default": "Bottom",
                "options": ("Top", "Middle", "Bottom"),
            },
            {
                "key": "Movement Path",
                "label": "Đường Aim",
                "label_attr": "aim_lbl_movement_path",
                "combo_attr": "combo_aim_movement_path",
                "default": "Cubic Bezier",
                "options": ("Cubic Bezier", "Exponential", "Linear", "Adaptive", "Perlin Noise"),
            },
            {
                "key": "Image Size",
                "label": "Image Size",
                "label_attr": "aim_lbl_image_size",
                "combo_attr": "combo_aim_image_size",
                "default": "640",
                "options": ("640", "512", "416", "320", "256", "160"),
            },
            {
                "key": "Target Class",
                "label": "Class Mục Tiêu",
                "label_attr": "aim_lbl_target_class",
                "combo_attr": "combo_aim_target_class",
                "default": "Best Confidence",
                "options": ("Best Confidence", "body", "head", "enemy"),
            },
        ]

    def _advanced_color_specs(self):
        return [
            ("FOV Color", "Màu FOV", "#FF8080FF"),
            ("Detected Player Color", "Màu ESP", "#FF00FFFF"),
            ("Theme Color", "Màu Theme", "#FF722ED1"),
        ]

    def _advanced_file_specs(self):
        return [
            ("ddxoft DLL Location", "ddxoft DLL"),
        ]

    def _advanced_minimize_specs(self):
        return [
            ("Aim Assist", "Panel Aim Assist"),
            ("Aim Config", "Panel Aim Config"),
            ("Predictions", "Panel Predictions"),
            ("Auto Trigger", "Panel Auto Trigger"),
            ("FOV Config", "Panel FOV Config"),
            ("ESP Config", "Panel ESP Config"),
            ("Model Settings", "Panel Model Settings"),
            ("Settings Menu", "Panel Settings Menu"),
            ("X/Y Percentage Adjustment", "Panel X/Y %"),
            ("Theme Settings", "Panel Theme"),
            ("Screen Settings", "Panel Screen"),
        ]

    def _listing_slider_specs(self):
        return [
            {
                "key": "Dynamic FOV Size",
                "label": "Kích Thước FOV Động",
                "label_attr": "aim_lbl_dynamic_fov",
                "slider_attr": "aim_slider_dynamic_fov",
                "value_attr": "aim_dynamic_fov_value_label",
                "min": 10,
                "max": 640,
                "slider_default": 10,
                "default": 10,
                "value_text": "10",
                "format": "int",
                "scale": 1,
                "page_step": 10,
            },
            {
                "key": "Sticky Aim Threshold",
                "label": "Ngưỡng Bám Mục Tiêu",
                "label_attr": "aim_lbl_sticky_threshold",
                "slider_attr": "aim_slider_sticky_threshold",
                "value_attr": "aim_sticky_threshold_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Y Offset (Up/Down)",
                "label": "Lệch Y",
                "label_attr": "aim_lbl_y_offset",
                "slider_attr": "aim_slider_y_offset",
                "value_attr": "aim_y_offset_value_label",
                "min": -150,
                "max": 150,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Y Offset (%)",
                "label": "Lệch Y %",
                "label_attr": "aim_lbl_y_offset_percent",
                "slider_attr": "aim_slider_y_offset_percent",
                "value_attr": "aim_y_offset_percent_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 50,
                "default": 50,
                "value_text": "50%",
                "format": "percent",
                "scale": 1,
            },
            {
                "key": "X Offset (Left/Right)",
                "label": "Lệch X",
                "label_attr": "aim_lbl_x_offset",
                "slider_attr": "aim_slider_x_offset",
                "value_attr": "aim_x_offset_value_label",
                "min": -150,
                "max": 150,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "X Offset (%)",
                "label": "Lệch X %",
                "label_attr": "aim_lbl_x_offset_percent",
                "slider_attr": "aim_slider_x_offset_percent",
                "value_attr": "aim_x_offset_percent_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 50,
                "default": 50,
                "value_text": "50%",
                "format": "percent",
                "scale": 1,
            },
            {
                "key": "Kalman Lead Time",
                "label": "Kalman Lead",
                "label_attr": "aim_lbl_kalman_lead",
                "slider_attr": "aim_slider_kalman_lead",
                "value_attr": "aim_kalman_lead_value_label",
                "min": 2,
                "max": 30,
                "slider_default": 10,
                "default": 0.10,
                "value_text": "0.10",
                "format": "float2",
                "scale": 100,
            },
            {
                "key": "WiseTheFox Lead Time",
                "label": "Wise Lead",
                "label_attr": "aim_lbl_wise_lead",
                "slider_attr": "aim_slider_wise_lead",
                "value_attr": "aim_wise_lead_value_label",
                "min": 2,
                "max": 30,
                "slider_default": 15,
                "default": 0.15,
                "value_text": "0.15",
                "format": "float2",
                "scale": 100,
            },
            {
                "key": "Shalloe Lead Multiplier",
                "label": "Shalloe Lead",
                "label_attr": "aim_lbl_shalloe_lead",
                "slider_attr": "aim_slider_shalloe_lead",
                "value_attr": "aim_shalloe_lead_value_label",
                "min": 2,
                "max": 20,
                "slider_default": 6,
                "default": 3.0,
                "value_text": "3.0",
                "format": "float1",
                "scale": 2,
            },
            {
                "key": "AI Confidence Font Size",
                "label": "Font Detect",
                "label_attr": "aim_lbl_conf_font_size",
                "slider_attr": "aim_slider_conf_font_size",
                "value_attr": "aim_conf_font_size_value_label",
                "min": 1,
                "max": 30,
                "slider_default": 20,
                "default": 20,
                "value_text": "20",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Corner Radius",
                "label": "Bo Góc ESP",
                "label_attr": "aim_lbl_corner_radius",
                "slider_attr": "aim_slider_corner_radius",
                "value_attr": "aim_corner_radius_value_label",
                "min": 0,
                "max": 100,
                "slider_default": 0,
                "default": 0,
                "value_text": "0",
                "format": "int",
                "scale": 1,
            },
            {
                "key": "Border Thickness",
                "label": "Dày Viền",
                "label_attr": "aim_lbl_border_thickness",
                "slider_attr": "aim_slider_border_thickness",
                "value_attr": "aim_border_thickness_value_label",
                "min": 1,
                "max": 100,
                "slider_default": 10,
                "default": 1.0,
                "value_text": "1.0",
                "format": "float1",
                "scale": 10,
            },
            {
                "key": "Opacity",
                "label": "Độ Trong",
                "label_attr": "aim_lbl_opacity",
                "slider_attr": "aim_slider_opacity",
                "value_attr": "aim_opacity_value_label",
                "min": 0,
                "max": 10,
                "slider_default": 10,
                "default": 1.0,
                "value_text": "1.0",
                "format": "float1",
                "scale": 10,
            },
        ]

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFrame, QGridLayout, QGroupBox, QComboBox, QSizePolicy, QSlider, QCheckBox,
                             QStackedWidget, QGraphicsDropShadowEffect, QMessageBox, QSystemTrayIcon, QMenu, QStyledItemDelegate,
                             QStylePainter, QStyleOptionComboBox, QStyle, QColorDialog, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QSize, QEvent, QRect
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QBrush, QKeySequence, QPixmap
import ctypes
import win32api
import winsound
import sys
import os
from pathlib import Path

# IMPORT LOCAL COMPONENTS



# IMPORT HELPERS & MANAGERS (STEP 6)

class BevelLine(QWidget):
    def __init__(self, side: str, color: str = "#333333", parent=None):
        super().__init__(parent)
        self.side = side
        self.color = QColor(color)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))

        width = self.width()
        height = self.height()
        center_y = 0
        thickness = 1
        cut = min(5, max(2, width // 8))

        if self.side == "left":
            points = [
                QPoint(0, center_y + thickness),
                QPoint(cut, center_y - thickness),
                QPoint(width, center_y - thickness),
                QPoint(width, center_y + thickness),
            ]
        else:
            points = [
                QPoint(0, center_y - thickness),
                QPoint(width - cut, center_y - thickness),
                QPoint(width, center_y + thickness),
                QPoint(0, center_y + thickness),
            ]

        painter.drawPolygon(*points)
        painter.end()


class FlatLine(QWidget):
    def __init__(self, color: str = "#333333", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.color))
        center_y = self.height() // 2
        painter.drawRect(0, center_y - 1, self.width(), 2)
        painter.end()


class SectionHeader(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionHeader")
        self._text = text
        self.title_label = self
        self.setFixedHeight(16)

    def setText(self, text: str):
        self._text = text
        self.update()

    def text(self) -> str:
        return self._text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        font = painter.font()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(self._text)
        pad_x = 12
        bg_w = text_w + (pad_x * 2)
        bg_h = fm.height()
        bg_x = max(0, (self.width() - bg_w) // 2)
        line_y = 0
        bg_y = line_y - (bg_h // 2) + 1

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1b1b1b"))
        painter.drawRect(bg_x, bg_y, bg_w, bg_h)

        painter.setPen(QColor("#e5e5e5"))
        painter.drawText(QRect(bg_x, bg_y, bg_w, bg_h), int(Qt.AlignmentFlag.AlignCenter), self._text)
        painter.end()


class MacroTitledBox(QFrame):
    def __init__(self, title: str, object_name: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        if object_name:
            self.setObjectName(object_name)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._content_layout = QVBoxLayout(self)
        self._content_layout.setContentsMargins(10, 16, 10, 8)
        self._content_layout.setSpacing(6)

    def content_layout(self):
        return self._content_layout

    def set_title(self, title: str):
        self._title = title
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        border_rect = self.rect().adjusted(0, 6, -1, -1)
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.setBrush(QBrush(QColor("#1b1b1b")))
        painter.drawRoundedRect(border_rect, 10, 10)

        font = painter.font()
        font.setFamily("Segoe UI")
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        title_w = fm.horizontalAdvance(self._title) + 22
        title_h = max(18, fm.height() + 2)
        title_x = max(12, (self.width() - title_w) // 2)
        title_y = border_rect.top() - (title_h // 2) - 1
        title_rect = QRect(title_x, title_y, title_w, title_h)

        painter.fillRect(title_rect, QColor("#1b1b1b"))
        shadow_rect = title_rect.adjusted(0, 1, 0, 1)
        painter.setPen(QColor(0, 0, 0, 140))
        painter.drawText(shadow_rect, int(Qt.AlignmentFlag.AlignCenter), self._title)
        painter.setPen(QColor("#e5e5e5"))
        painter.drawText(title_rect, int(Qt.AlignmentFlag.AlignCenter), self._title)
        painter.end()


class MobileSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = bool(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(52, 28)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        checked = bool(checked)
        if self._checked == checked:
            return
        self._checked = checked
        self.update()
        self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect().adjusted(1, 3, -1, -3)
        track_color = QColor("#8a56ff") if self._checked else QColor("#3a3a3a")
        track_border = QColor("#b088ff") if self._checked else QColor("#565656")

        painter.setPen(QPen(track_border, 1))
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)

        knob_size = rect.height() - 4
        knob_y = rect.y() + 2
        knob_x = rect.right() - knob_size - 2 if self._checked else rect.x() + 2
        knob_rect = QRectF(knob_x, knob_y, knob_size, knob_size)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(knob_rect)
        painter.end()


class SplitSectionHeader(QWidget):
    def __init__(self, left_text: str, right_text: str, separator_width: int = 1, separator_gap: int = 10, parent=None):
        super().__init__(parent)
        self.setObjectName("SplitSectionHeader")
        self.setFixedHeight(14)
        self.left_text = left_text
        self.right_text = right_text
        self.separator_width = separator_width
        self.separator_gap = separator_gap
        self.center_gap_width = max(1, ((separator_gap * 2) + separator_width) - 2)
        self.line_color = QColor("#333333")
        self.left_text_color = QColor("#eefbff")
        self.right_text_color = QColor("#fff1f8")
        self.text_gap = 6
        self.outer_margin = 8
        self.font = QFont()
        self.font.setPixelSize(12)
        self.font.setBold(True)

    def _draw_flat_line(self, painter: QPainter, x1: int, x2: int, center_y: int):
        if x2 <= x1:
            return
        painter.drawRect(x1, center_y - 1, x2 - x1, 2)

    def _draw_bevel_left(self, painter: QPainter, x1: int, x2: int, center_y: int):
        if x2 <= x1:
            return
        cut = min(5, max(2, (x2 - x1) // 8))
        painter.drawPolygon(
            QPoint(x1, center_y + 1),
            QPoint(x1 + cut, center_y - 1),
            QPoint(x2, center_y - 1),
            QPoint(x2, center_y + 1),
        )

    def _draw_bevel_right(self, painter: QPainter, x1: int, x2: int, center_y: int):
        if x2 <= x1:
            return
        cut = min(5, max(2, (x2 - x1) // 8))
        painter.drawPolygon(
            QPoint(x1, center_y - 1),
            QPoint(x2 - cut, center_y - 1),
            QPoint(x2, center_y + 1),
            QPoint(x1, center_y + 1),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.line_color))

        rect = self.rect()
        center_y = rect.height() // 2
        total_width = rect.width()
        center_x = total_width // 2
        half_width = center_x - self.outer_margin
        right_half_width = total_width - self.outer_margin - center_x

        painter.setFont(self.font)
        metrics = painter.fontMetrics()

        left_text_width = metrics.horizontalAdvance(self.left_text)
        left_text_x = self.outer_margin + max(0, (half_width - left_text_width) // 2)
        left_text_y = (rect.height() + metrics.ascent() - metrics.descent()) // 2 - 1

        right_text_width = metrics.horizontalAdvance(self.right_text)
        right_text_x = center_x + max(0, (right_half_width - right_text_width) // 2)
        right_text_y = left_text_y

        self._draw_bevel_left(painter, self.outer_margin, max(self.outer_margin, left_text_x - self.text_gap), center_y)
        self._draw_flat_line(painter, left_text_x + left_text_width + self.text_gap, max(left_text_x + left_text_width + self.text_gap, right_text_x - self.text_gap), center_y)
        self._draw_bevel_right(painter, right_text_x + right_text_width + self.text_gap, total_width - self.outer_margin, center_y)

        painter.setPen(self.left_text_color)
        painter.drawText(left_text_x, left_text_y, self.left_text)
        painter.setPen(self.right_text_color)
        painter.drawText(right_text_x, right_text_y, self.right_text)
        painter.end()


class MarqueeLabel(QLabel):
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._source_text = ""
        self._display_text = ""
        self._timer = QTimer(self)
        self._timer.setInterval(140)
        self._timer.timeout.connect(self._tick)
        self.set_source_text(text)

    def set_source_text(self, text: str):
        self._source_text = (text or "").strip()
        if not self._source_text:
            self._display_text = ""
            self.setText("")
            self._timer.stop()
            return
        self._display_text = f"   {self._source_text}   "
        self.setText(self._display_text)
        if not self._timer.isActive():
            self._timer.start()

    def _tick(self):
        if not self._display_text:
            return
        self._display_text = self._display_text[1:] + self._display_text[0]
        self.setText(self._display_text)


class CenteredComboBox(QComboBox):
    def __init__(self, parent=None, center_mode: str = "field"):
        super().__init__(parent)
        self.setEditable(False)
        self.setIconSize(QSize(28, 14))
        self.center_mode = center_mode

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = ""
        option.currentIcon = QIcon()
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)

        if self.center_mode == "full":
            text_rect = self.rect().adjusted(2, 0, -2, 0)
        else:
            text_rect = self.style().subControlRect(
                QStyle.ComplexControl.CC_ComboBox,
                option,
                QStyle.SubControl.SC_ComboBoxEditField,
                self,
            )
            text_rect.adjust(2, 0, -2, 0)
        icon = self.itemIcon(self.currentIndex()) if self.currentIndex() >= 0 else QIcon()
        if not icon.isNull():
            pixmap = icon.pixmap(self.iconSize())
            x = text_rect.center().x() - (pixmap.width() // 2)
            y = text_rect.center().y() - (pixmap.height() // 2)
            painter.drawPixmap(x, y, pixmap)
        else:
            painter.setPen(QColor("#f2f2f2"))
            painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter), self.currentText())
        painter.end()


class IconOnlyComboDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.save()

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#232323"))
        else:
            painter.fillRect(option.rect, QColor("#1b1b1b"))

        icon = index.data(Qt.ItemDataRole.DecorationRole)
        if isinstance(icon, QIcon) and not icon.isNull():
            pixmap = icon.pixmap(36, 18)
            x = option.rect.center().x() - (pixmap.width() // 2)
            y = option.rect.center().y() - (pixmap.height() // 2)
            painter.drawPixmap(x, y, pixmap)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(48, 24)


class CrosshairOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        self.setGeometry(0, 0, w, h)

        self.active = False
        self.style = "x"
        self.color = QColor(255, 255, 255)
        self.ads_mode = "HOLD"
        self.ads_active = False
        self.rmb_prev = False

        self.timer_ads = QTimer(self)
        self.timer_ads.timeout.connect(self.check_ads)
        self.timer_ads.setInterval(100)
        QTimer.singleShot(500, lambda: self.set_capture_invisible(int(self.winId())))

    def set_capture_invisible(self, hwnd_int):
        try:
            ctypes.windll.user32.SetWindowDisplayAffinity(int(hwnd_int), 0)
        except Exception:
            pass

    def check_ads(self):
        if not self.active:
            return
        if not Utils.is_game_active():
            if not self.isVisible():
                self.show()
            return
        lmb_down = win32api.GetKeyState(0x01) < 0
        rmb_down = win32api.GetKeyState(0x02) < 0
        should_hide = lmb_down or rmb_down
        if should_hide:
            if self.isVisible():
                self.hide()
        else:
            if not self.isVisible():
                self.show()
        self.rmb_prev = rmb_down

    def set_ads_mode(self, mode):
        self.ads_mode = str(mode or "HOLD").upper()
        self.ads_active = False
        self.rmb_prev = False
        if self.active and self.ads_mode != "HOLD":
            self.show()

    def reset_toggle_state(self):
        if self.ads_mode == "TOGGLE":
            self.ads_active = False
            if self.active:
                self.show()

    def set_active(self, active):
        self.active = bool(active)
        if self.active:
            if not self.timer_ads.isActive():
                self.timer_ads.start()
            self.show()
        else:
            if self.timer_ads.isActive():
                self.timer_ads.stop()
            self.hide()
        self.update()

    def set_style(self, style):
        self.style = str(style or "x")
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
        self.color = colors.get(str(color_name), QColor(255, 255, 255))
        self.update()

    def paintEvent(self, event):
        if not self.active:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = self.width() // 2
        cy = self.height() // 2

        def draw_shape(p):
            if self.style == "dot":
                p.drawEllipse(QPoint(cx, cy), 2, 2)
            elif self.style == "plus":
                p.drawLine(cx - 6, cy, cx + 6, cy)
                p.drawLine(cx, cy - 6, cx, cy + 6)
            elif self.style == "x":
                p.drawLine(cx - 6, cy - 6, cx + 6, cy + 6)
                p.drawLine(cx - 6, cy + 6, cx + 6, cy - 6)
            elif self.style == "circle":
                p.drawEllipse(QPoint(cx, cy), 6, 6)
                p.drawEllipse(QPoint(cx, cy), 1, 1)
            elif self.style == "hollow_circle":
                p.drawEllipse(QPoint(cx, cy), 6, 6)
            elif self.style == "tactical":
                gap = 4
                p.drawLine(cx - 10, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + 10, cy)
                p.drawLine(cx, cy - 10, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + 10)
                p.drawEllipse(QPoint(cx, cy), 1, 1)
            elif self.style == "small_cross":
                gap = 3
                p.drawLine(cx - 6, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + 6, cy)
                p.drawLine(cx, cy - 6, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + 6)
            elif self.style == "thick_cross":
                p.drawLine(cx - 8, cy, cx + 8, cy)
                p.drawLine(cx, cy - 8, cx, cy + 8)
            elif self.style == "sniper":
                gap = 5
                p.drawLine(cx - 12, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + 12, cy)
                p.drawLine(cx, cy - 12, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + 12)
                p.drawEllipse(QPoint(cx, cy), 9, 9)
            elif self.style == "diamond":
                p.drawLine(cx, cy - 6, cx + 6, cy)
                p.drawLine(cx + 6, cy, cx, cy + 6)
                p.drawLine(cx, cy + 6, cx - 6, cy)
                p.drawLine(cx - 6, cy, cx, cy - 6)
            elif self.style == "triangle":
                p.drawLine(cx, cy - 7, cx - 6, cy + 4)
                p.drawLine(cx - 6, cy + 4, cx + 6, cy + 4)
                p.drawLine(cx + 6, cy + 4, cx, cy - 7)
            elif self.style == "minimal":
                p.drawLine(cx - 4, cy, cx - 1, cy)
                p.drawLine(cx + 1, cy, cx + 4, cy)
                p.drawLine(cx, cy - 4, cx, cy - 1)
                p.drawLine(cx, cy + 1, cx, cy + 4)
            else:
                gap = 4
                l = 8
                p.drawLine(cx - gap - l, cy, cx - gap, cy)
                p.drawLine(cx + gap, cy, cx + gap + l, cy)
                p.drawLine(cx, cy - gap - l, cx, cy - gap)
                p.drawLine(cx, cy + gap, cx, cy + gap + l)

        pen_outline = QPen(QColor(0, 0, 0, 255))
        pen_outline.setWidth(4)
        pen_outline.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_outline)
        if self.style == "dot":
            painter.setBrush(QBrush(QColor(0, 0, 0, 255)))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        draw_shape(painter)

        pen_core = QPen(self.color)
        pen_core.setWidth(2)
        pen_core.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_core)
        if self.style == "dot":
            painter.setBrush(QBrush(self.color))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        draw_shape(painter)


class GameOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        self.w, self.h = 300, 26
        self.x_pos = (screen.width() - self.w) // 2
        self.y_pos = screen.height() - self.h
        self.setGeometry(self.x_pos, self.y_pos, self.w, self.h)

        self.frame = QFrame(self)
        self.frame.setGeometry(0, 0, self.w, self.h)
        self._frame_qss = "QFrame { background-color: rgba(10, 10, 10, 180); border: 1px solid #444444; border-radius: 6px; }"
        self.frame.setStyleSheet(self._frame_qss)

        self.lbl = QLabel(self.frame)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl.setGeometry(0, 0, self.w, self.h)
        self.lbl.setText("Di88-VP MACRO")
        self._label_qss_tpl = "color: {color}; font-weight: 900; font-family: 'Segoe UI'; font-size: 10px; border: none; background: transparent;"
        self.lbl.setStyleSheet(self._label_qss_tpl.format(color="#00FF00"))

        self.last_color = None
        self.last_full_text = ""
        self.is_firing = False

        self.flash_timer = QTimer(self)
        self.flash_timer.setInterval(100)
        self.flash_timer.timeout.connect(self._do_flash)
        self.color_idx = 0

        self.detect_timer = QTimer(self)
        self.detect_timer.setInterval(200)
        self.detect_timer.timeout.connect(self._do_detect_flash)
        self.detect_idx = 0

        self.show()
        self._adjust_to_content("Di88-VP MACRO")

    def _do_flash(self):
        color = "#00FFFF" if self.color_idx % 2 == 0 else "#001a1a"
        self.lbl.setStyleSheet(self._label_qss_tpl.format(color=color))
        self.frame.setStyleSheet(self._frame_qss)
        self.color_idx += 1

    def _do_detect_flash(self):
        if self.flash_timer.isActive():
            return
        color = "#FFA500" if self.detect_idx % 2 == 0 else "#331a00"
        self.lbl.setStyleSheet(self._label_qss_tpl.format(color=color))
        self.frame.setStyleSheet(self._frame_qss)
        self.detect_idx += 1

    def _adjust_to_content(self, text):
        width = self.lbl.fontMetrics().horizontalAdvance(text) + 40
        self.w = width
        screen_w = QApplication.primaryScreen().geometry().width()
        self.setGeometry((screen_w - self.w) // 2, self.y_pos, self.w, self.h)
        self.frame.setGeometry(0, 0, self.w, self.h)
        self.lbl.setGeometry(0, 0, self.w, self.h)

    def update_status(self, gun_name, scope, stance, grip="NONE", muzzle="NONE", is_paused=False, is_firing=False, ai_status="HIBERNATE"):
        self.is_firing = bool(is_firing)
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
            elif "15" in scope_raw:
                sc_val = "X15"
            if "kh" in scope_raw:
                sc_val = f"KH {sc_val}"

            vn_stance = str(stance)
            if "STAND" in vn_stance.upper():
                vn_stance = "ĐỨNG"
            elif "CROUCH" in vn_stance.upper():
                vn_stance = "NGỒI"
            elif "PRONE" in vn_stance.upper():
                vn_stance = "NẰM"

            parts = [str(gun_name).upper(), sc_val]
            if str(grip).upper() != "NONE":
                parts.append("TAY")
            if str(muzzle).upper() != "NONE":
                parts.append("NÒNG")
            parts.append(vn_stance)
            text = " | ".join(parts)
            color = "#00FF00"

        if ai_status == "ACTIVE":
            if not self.detect_timer.isActive():
                self.detect_timer.start()
            color = "#FFA500"
        else:
            if self.detect_timer.isActive():
                self.detect_timer.stop()
                self.last_color = None

        if self.last_full_text != text:
            self.lbl.setText(text)
            self.last_full_text = text
            self.show()
            self._adjust_to_content(text)

        if self.is_firing:
            if not self.flash_timer.isActive():
                self.flash_timer.start()
            if self.detect_timer.isActive():
                self.detect_timer.stop()
        else:
            if self.flash_timer.isActive():
                self.flash_timer.stop()
                self.last_color = None
            if not self.detect_timer.isActive() and self.last_color != color:
                self.lbl.setStyleSheet(self._label_qss_tpl.format(color=color))
                self.frame.setStyleSheet(self._frame_qss)
                self.last_color = color

class MacroWindow(QMainWindow):
    signal_settings_changed = pyqtSignal() # Signal to notify Backend/InputBridge of config changes
    WINDOW_WIDTH = 930
    _MOJIBAKE_MARKER_CODES = (0x00C3, 0x00C2, 0x00C4, 0x00C5, 0x00C6, 0x2022)
    _CP1252_REVERSE = {
        ch: i for i, ch in enumerate(encodings.cp1252.decoding_table)
    }

    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self.WINDOW_WIDTH)
        icon_path = get_resource_path("di88vp.ico")
        self.setWindowIcon(QIcon(icon_path))
        
        # 3. Startup metadata
        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        self.detected_resolution = f"{w}x{h}"
        
        # 2. Logic Components (Connected via set_backend)
        self.backend = None
        self._runtime_starter = None
        self._runtime_started = False
        self.keyboard_listener = None
        self.mouse_listener = None
        self._runtime_timers = []
        self._shutdown_in_progress = False
        self._is_shutting_down = False
        self._last_macro_ui_signature = None
        self._last_macro_toggle_state = None
        self._last_stance_style_signature = None
        self._last_game_overlay_signature = None
        self._last_banner_signature = None
        self._last_home_snapshot_signature = None
        self._last_ads_status_signature = None
        self._overlay_enabled = False
        self._layout_sync_timer = QTimer(self)
        self._layout_sync_timer.setSingleShot(True)
        self._layout_sync_timer.timeout.connect(self.sync_window_height_to_content)
        
        # 3. Threads (PLACEHOLDER)
        
        # 4. Crosshair Overlay & Game HUD
        self.crosshair = None
        self.game_overlay = None

        # Temporary unsaved keybind values must exist before setup_ui_v2(),
        # because load_crosshair_settings() can trigger save_crosshair_settings()
        # through combo index change handlers during initial UI construction.
        self.temp_guitoggle_value = None
        self.temp_overlay_key_value = None
        self.temp_fast_loot_key_value = None
        self.temp_crosshair_toggle_key_value = None
        self.temp_aim_primary_key_value = None
        self.temp_aim_secondary_key_value = None
        self.temp_aim_trigger_key_value = None
        self.temp_aim_emergency_key_value = None

        # Keybind listener state must exist before setup_ui_v2(), because
        # child widgets install this window as an event filter while UI builds.
        self.listening_key = False
        self.target_key_btn = None
        self.target_setting_key = None
        self.temp_original_text = None
        
        # 5. UI Setup
        self.load_style()
        self.setup_ui_v2()
        self.sanitize_runtime_vietnamese_text()
        
        # 6. Tray Manager
        # Tray icon chỉ hiện khi người dùng thật sự đưa app xuống tray.
        self.tray_manager = TrayManager(self)
        
        self.dragPos = None
        self._crosshair_hidden_for_window = False
        
        # Enable keyboard events for arrow keys AND Keybinds
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        # Install Global Event Filter to catch clicks anywhere
        self.installEventFilter(self)
        

    def repolish(self, widget):
        """Forces Qt to re-read properties and apply QSS"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _repair_mojibake_text(self, text: str) -> str:
        if not text or not any(chr(code) in text for code in self._MOJIBAKE_MARKER_CODES):
            return text

        raw_bytes = bytearray()
        for ch in text:
            code = ord(ch)
            if code <= 255:
                raw_bytes.append(code)
                continue

            mapped = self._CP1252_REVERSE.get(ch)
            if mapped is None:
                return text
            raw_bytes.append(mapped)

        try:
            fixed = bytes(raw_bytes).decode("utf-8")
        except UnicodeDecodeError:
            return text

        return fixed if fixed != text else text

    def sanitize_runtime_vietnamese_text(self):
        # Vá text mojibake còn sót từ builder GUI cũ mà không đổi layout hay logic.
        title = self.windowTitle()
        if title:
            self.setWindowTitle(self._repair_mojibake_text(title))

        for widget in self.findChildren(QWidget):
            text_getter = getattr(widget, "text", None)
            text_setter = getattr(widget, "setText", None)
            if callable(text_getter) and callable(text_setter):
                original = text_getter()
                if isinstance(original, str):
                    fixed = self._repair_mojibake_text(original)
                    if fixed != original:
                        text_setter(fixed)

            if isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    original = widget.itemText(index)
                    fixed = self._repair_mojibake_text(original)
                    if fixed != original:
                        widget.setItemText(index, fixed)

    def normalize_crosshair_style_value(self, style: str) -> str:
        style_text = str(style or "").strip()
        legacy_map = {
            "1: Gap Cross": "small_cross",
            "2: T-Shape": "tactical",
            "3: Circle Dot": "circle",
            "5: Classic": "plus",
            "6: Micro Dot": "dot",
            "7: Hollow Box": "hollow_circle",
            "8: Cross + Dot": "tactical",
            "9: Chevron": "triangle",
            "10: X-Shape": "x",
            "11: Diamond": "diamond",
            "13: Triangle": "triangle",
            "14: Square Dot": "dot",
            "17: Bracket Dot": "minimal",
            "18: Shuriken": "tactical",
            "19: Center Gap": "minimal",
            "22: Plus Dot": "plus",
            "23: V-Shape": "triangle",
            "24: Star": "sniper",
        }
        valid_styles = {internal for _, internal in self.crosshair_style_options}
        if style_text in valid_styles:
            return style_text
        return legacy_map.get(style_text, "x")

    def style_setting_label(self, widget: QLabel):
        widget.setStyleSheet("""
            QLabel {
                color: #bcbcbc;
                background: transparent;
                border: none;
                padding: 0 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)

    def style_setting_button(self, widget: QPushButton):
        widget.setStyleSheet("""
            QPushButton {
                background-color: #1b1b1b;
                color: #d6d6d6;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background-color: #1b1b1b;
                border: 1px solid #666;
            }
            QPushButton:disabled {
                background-color: #1b1b1b;
                color: #bfbfbf;
                border: 1px solid #444;
            }
        """)

    def style_capture_button(self, widget: QPushButton, active: bool):
        if active:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #8a56ff;
                    color: #ffffff;
                    border: 1px solid #b088ff;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #9766ff;
                    border: 1px solid #c3a5ff;
                }
            """)
        else:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #1b1b1b;
                    color: #d0d0d0;
                    border: 1px solid #444;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #202020;
                    border: 1px solid #666;
                }
            """)

    def style_switch_button(self, widget: QPushButton, active: bool):
        if active:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #12341b;
                    color: #9dffb7;
                    border: 1px solid #2e9b50;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #174223;
                    border: 1px solid #41ba66;
                }
            """)
        else:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #242424;
                    color: #d0d0d0;
                    border: 1px solid #4a4a4a;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background-color: #2c2c2c;
                    border: 1px solid #666666;
                }
            """)

    def style_scope_value_label(self, widget: QLabel):
        widget.setStyleSheet("""
            QLabel {
                background-color: #181818;
                color: #ffffff;
                border: 1px solid #3f3f3f;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 0 6px;
            }
        """)

    def style_scope_slider(self, widget: QSlider):
        widget.setStyleSheet("""
            QSlider::groove:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2a2a2a, stop:1 #242424);
                height: 6px;
                border-radius: 3px;
                border: 1px solid #2f2f2f;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8457ef, stop:0.5 #9164fb, stop:1 #a57aff);
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #2a2a2a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qradialgradient(cx:0.45, cy:0.35, radius:0.95, stop:0 #fffefe, stop:0.55 #f1e6ff, stop:1 #dcc4ff);
                border: 1px solid #d2b0ff;
                width: 13px;
                height: 13px;
                margin: -5px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: qradialgradient(cx:0.45, cy:0.35, radius:1.0, stop:0 #ffffff, stop:0.5 #f7efff, stop:1 #e7d4ff);
                border: 1px solid #e6d0ff;
                width: 14px;
                height: 14px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:pressed {
                background: qradialgradient(cx:0.5, cy:0.45, radius:0.95, stop:0 #f7efff, stop:0.55 #ead8ff, stop:1 #cea7ff);
                border: 1px solid #bc8fff;
                width: 12px;
                height: 12px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a5df7, stop:0.5 #9b70ff, stop:1 #b085ff);
            }
        """)

    def style_action_button(self, widget: QPushButton, primary: bool):
        if primary:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #232629;
                    color: white;
                    border: 1px solid #50555a;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 0 18px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #363b40;
                    border: 1px solid #8a949e;
                    color: #ffffff;
                }
                QPushButton:focus {
                    outline: none;
                    border: 1px solid #8a949e;
                }
            """)
        else:
            widget.setStyleSheet("""
                QPushButton {
                    background-color: #232629;
                    color: white;
                    border: 1px solid #50555a;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 0 18px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: #31363b;
                    border: 1px solid #7b848d;
                    color: #ffffff;
                }
                QPushButton:focus {
                    outline: none;
                    border: 1px solid #7b848d;
                }
            """)

    def show_bottom_action_status(self, message: str, tone: str = "info", auto_hide_ms: int = 2200):
        if not hasattr(self, "bottom_action_status") or self.bottom_action_status is None:
            return
        palette = {
            "success": "#d8ffea",
            "error": "#ffd6d6",
            "info": "#d9e8ff",
        }
        fg = palette.get(tone, palette["info"])
        self.bottom_action_status.setText(f"! {message}")
        self.bottom_action_status.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background: transparent;
                border: none;
                font-size: 11px;
                font-weight: 800;
                padding: 2px 6px;
            }}
        """)
        self.bottom_action_status.show()
        self.bottom_action_status.raise_()
        if not hasattr(self, "_bottom_action_status_timer"):
            self._bottom_action_status_timer = QTimer(self)
            self._bottom_action_status_timer.setSingleShot(True)
            self._bottom_action_status_timer.timeout.connect(self.hide_bottom_action_status)
        self._bottom_action_status_timer.start(auto_hide_ms)

    def hide_bottom_action_status(self):
        if hasattr(self, "bottom_action_status") and self.bottom_action_status is not None:
            self.bottom_action_status.hide()

    def play_action_beep(self, action: str):
        try:
            if action == "save":
                winsound.Beep(1046, 80)
                winsound.Beep(1318, 90)
            elif action == "reset":
                winsound.Beep(880, 90)
                winsound.Beep(659, 130)
            else:
                winsound.MessageBeep()
        except Exception:
            QApplication.beep()

    def update_stance_status_style(self, stance_text: str, color: str = "#aaaaaa"):
        if not hasattr(self, 'lbl_stance') or self.lbl_stance is None:
            return
        signature = (stance_text, color)
        if self._last_stance_style_signature == signature:
            return
        self._last_stance_style_signature = signature
        self.lbl_stance.setText(stance_text)
        self.lbl_stance.setStyleSheet(f"""
            QLabel {{
                background-color: #1b1b1b;
                color: {color};
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 0 8px;
            }}
        """)
        self.update_home_snapshot()

    def update_aim_status_style(self, is_on: bool):
        if not hasattr(self, 'btn_aim_status') or self.btn_aim_status is None:
            return
        base = "font-size: 12px; font-weight: bold; letter-spacing: 2px; border-radius: 5px;"
        if is_on:
            self.btn_aim_status.setText("AIM : ON")
            self.btn_aim_status.setStyleSheet(
                f"QPushButton {{ color: #00FFFF; background: #1b1b1b; border: 1px solid #006666; {base} }}"
            )
        else:
            self.btn_aim_status.setText("AIM : OFF")
            self.btn_aim_status.setStyleSheet(
                f"QPushButton {{ color: #ff4444; background: #1b1b1b; border: 1px solid #441111; {base} }}"
            )
        self.update_home_snapshot()

    def update_aim_metric_style(self, widget: QLabel, text: str, color: str = "#d7d7d7"):
        if widget is None:
            return
        metric_signature = (text, color)
        if widget.property("_aim_metric_signature") == metric_signature:
            return
        if widget.text() != text:
            widget.setText(text)
        widget.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #1b1b1b;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 0 6px;
            }}
        """)
        widget.setProperty("_aim_metric_signature", metric_signature)

    def sync_crosshair_columns(self):
        if not hasattr(self, "crosshair_box"):
            return

        available = max(0, self.crosshair_box.contentsRect().width() - 16)
        gap_total = 3
        left_width = max(72, (available - gap_total) // 2)

        mapping = [
            ("lbl_cross_style", left_width),
            ("combo_style", left_width),
            ("lbl_cross_color", left_width),
            ("combo_color", left_width),
        ]
        for attr, width in mapping:
            widget = getattr(self, attr, None)
            if widget is None:
                continue
            widget.setMinimumWidth(0)
            widget.setMaximumWidth(width)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sync_window_height_to_content(self):
        if self.centralWidget() is None:
            return
        if self.centralWidget().layout():
            self.centralWidget().layout().activate()
        target_height = max(560, self.centralWidget().sizeHint().height() + 12)
        screen = self.screen()
        if screen is None:
            app = QApplication.instance()
            screen = app.primaryScreen() if app else None
        if screen is not None:
            available = screen.availableGeometry()
            target_height = min(target_height, max(560, available.height() - 24))
        if abs(self.height() - target_height) <= 2:
            return
        self.setFixedHeight(target_height)
        self.sync_window_width_to_frame()

    def fit_window_to_screen(self):
        self.sync_window_width_to_frame()
        self.sync_window_height_to_content()
        self.center_on_screen()

    def sync_window_width_to_frame(self):
        central = self.centralWidget()
        if central is None:
            return
        self.setFixedWidth(self.WINDOW_WIDTH)
        central.resize(self.width(), central.height())
        if hasattr(self, 'container') and self.container:
            self.container.setFixedWidth(max(0, self.width() - 10))
        self.sync_macro_box_heights()
        self.sync_crosshair_columns()

    def sync_macro_half_boxes(self):
        self.sync_crosshair_columns()

    def sync_macro_box_heights(self):
        pairs = [
            ("capture_box", "crosshair_box"),
        ]
        for left_attr, right_attr in pairs:
            left = getattr(self, left_attr, None)
            right = getattr(self, right_attr, None)
            if left is None or right is None:
                continue
            target = max(left.sizeHint().height(), right.sizeHint().height())
            left.setFixedHeight(target)
            right.setFixedHeight(target)

    def build_nav_button(self, text: str, page_name: str):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(42)
        button.clicked.connect(lambda: self.set_main_page(page_name))
        button.setProperty("page_name", page_name)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def update_nav_button_styles(self):
        buttons = getattr(self, "_nav_buttons", {})
        current = getattr(self, "_current_main_page", "home")
        for page_name, button in buttons.items():
            active = page_name == current
            accent = "#00d8ff" if active else "#343434"
            text_color = "#f2f2f2" if active else "#c6c6c6"
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #141414;
                    color: {text_color};
                    border: 1px solid #2e2e2e;
                    border-left: 3px solid {accent};
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: 800;
                    letter-spacing: 1px;
                    padding: 0 14px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: #1b1b1b;
                    border: 1px solid #414141;
                    border-left: 3px solid #5be6ff;
                }}
            """)

    def set_main_page(self, page_name: str):
        if not hasattr(self, "page_stack") or self.page_stack is None:
            return
        page_map = getattr(self, "_page_widgets", {})
        target = page_map.get(page_name)
        if target is None:
            return
        self._current_main_page = page_name
        self.page_stack.setCurrentWidget(target)
        self.update_nav_button_styles()
        self.update_main_page_banner()
        self._layout_sync_timer.start(120)

    def update_main_page_banner(self):
        if not hasattr(self, "page_banner_title"):
            return
        current = getattr(self, "_current_main_page", "home")

        macro_on = False
        if hasattr(self, "btn_macro") and self.btn_macro:
            macro_on = "ON" in self.btn_macro.text().upper()
        aim_on = False
        if hasattr(self, "btn_aim_status") and self.btn_aim_status:
            aim_on = "ON" in self.btn_aim_status.text().upper()

        banner_map = {
            "home": {
                "eyebrow": "DI88 CONTROL",
                "title": "TRUNG TÂM ĐIỀU KHIỂN",
                "subtitle": "Macro & Aim By Di88",
                "badge": "TỔNG HỢP",
                "gradient_start": "#0d1e33",
                "gradient_end": "#112944",
                "hover_start": "#123053",
                "hover_end": "#16385f",
                "border": "#2f3942",
                "hover_border": "#476586",
                "eyebrow_color": "#77dfff",
                "badge_color": "#00d8ff",
                "badge_bg": "rgba(3, 22, 34, 0.36)",
                "badge_border": "#00d8ff",
                "badge_hover_bg": "rgba(0, 216, 255, 0.18)",
                "badge_hover_border": "#56e8ff",
                "badge_shadow": (0, 216, 255, 0),
            },
            "macro": {
                "eyebrow": "DI88 MACRO",
                "title": "TRUNG TÂM MACRO",
                "subtitle": "Nhận diện súng, ADS và điều khiển recoil",
                "badge": "• ĐANG BẬT" if macro_on else "• ĐANG TẮT",
                "gradient_start": "#251112",
                "gradient_end": "#34181a",
                "hover_start": "#341618",
                "hover_end": "#432022",
                "border": "#4a2a2d",
                "hover_border": "#6b3b40",
                "eyebrow_color": "#ff9c9c",
                "badge_color": "#ffecec" if macro_on else "#ffb0b0",
                "badge_bg": "rgba(255, 86, 86, 0.30)" if macro_on else "rgba(28, 8, 10, 0.35)",
                "badge_border": "#ff6a6a" if macro_on else "#b96a6a",
                "badge_hover_bg": "rgba(255, 106, 106, 0.40)" if macro_on else "rgba(70, 22, 24, 0.48)",
                "badge_hover_border": "#ff8b8b" if macro_on else "#d68b8b",
                "badge_shadow": (255, 90, 90, 120) if macro_on else (0, 0, 0, 0),
            },
            "aim": {
                "eyebrow": "DI88 AIM",
                "title": "TRUNG TÂM AIM",
                "subtitle": "Theo dõi mục tiêu và điều khiển ngắm",
                "badge": "• ĐANG BẬT" if aim_on else "• ĐANG TẮT",
                "gradient_start": "#0d2417",
                "gradient_end": "#143121",
                "hover_start": "#12311f",
                "hover_end": "#19402a",
                "border": "#294536",
                "hover_border": "#3e6c54",
                "eyebrow_color": "#74ffc8",
                "badge_color": "#effff8" if aim_on else "#a6d7bf",
                "badge_bg": "rgba(0, 255, 170, 0.24)" if aim_on else "rgba(7, 22, 14, 0.35)",
                "badge_border": "#52ffd1" if aim_on else "#5b9077",
                "badge_hover_bg": "rgba(0, 255, 170, 0.34)" if aim_on else "rgba(18, 46, 31, 0.50)",
                "badge_hover_border": "#8affdf" if aim_on else "#79af96",
                "badge_shadow": (0, 255, 170, 110) if aim_on else (0, 0, 0, 0),
            },
        }
        banner = banner_map.get(current, banner_map["home"])
        banner_signature = (
            current,
            banner["eyebrow"],
            banner["title"],
            banner["subtitle"],
            banner["badge"],
            banner["gradient_start"],
            banner["gradient_end"],
            banner["hover_start"],
            banner["hover_end"],
            banner["border"],
            banner["hover_border"],
            banner["eyebrow_color"],
            banner["badge_color"],
            banner["badge_bg"],
            banner["badge_border"],
            banner["badge_hover_bg"],
            banner["badge_hover_border"],
            banner["badge_shadow"],
        )
        if self._last_banner_signature == banner_signature:
            return
        self._last_banner_signature = banner_signature
        title = banner["title"]
        subtitle = banner["subtitle"]
        badge = banner["badge"]
        if self.page_banner_title.text() != title:
            self.page_banner_title.setText(title)
        if self.page_banner_subtitle.text() != subtitle:
            self.page_banner_subtitle.setText(subtitle)
        if self.page_banner_badge.text() != badge:
            self.page_banner_badge.setText(badge)
        if self.page_banner_eyebrow.text() != banner["eyebrow"]:
            self.page_banner_eyebrow.setText(banner["eyebrow"])
        self.page_banner_eyebrow.setStyleSheet(f"""
            QLabel {{
                color: {banner["eyebrow_color"]};
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
        """)
        self.page_banner.setStyleSheet(f"""
            QFrame#MainPageBanner {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {banner["gradient_start"]},
                    stop: 1 {banner["gradient_end"]}
                );
                border: 1px solid {banner["border"]};
                border-radius: 14px;
            }}
            QFrame#MainPageBanner:hover {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {banner["hover_start"]},
                    stop: 1 {banner["hover_end"]}
                );
                border: 1px solid {banner["hover_border"]};
            }}
        """)
        self.page_banner_badge.setStyleSheet(f"""
            QLabel {{
                color: {banner["badge_color"]};
                border: 1px solid {banner["badge_border"]};
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 10px;
                font-weight: 900;
                background: {banner["badge_bg"]};
                letter-spacing: 1px;
            }}
            QLabel:hover {{
                background: {banner["badge_hover_bg"]};
                border: 1px solid {banner["badge_hover_border"]};
            }}
        """)
        badge_shadow = getattr(self, "_page_banner_badge_shadow", None)
        if badge_shadow is None:
            badge_shadow = QGraphicsDropShadowEffect(self.page_banner_badge)
            badge_shadow.setBlurRadius(22)
            badge_shadow.setOffset(0, 0)
            self.page_banner_badge.setGraphicsEffect(badge_shadow)
            self._page_banner_badge_shadow = badge_shadow
        shadow_r, shadow_g, shadow_b, shadow_a = banner["badge_shadow"]
        badge_shadow.setColor(QColor(shadow_r, shadow_g, shadow_b, shadow_a))

    def _update_home_toggle_button_style(self, button, is_on: bool, accent_color: str):
        if button is None:
            return
        if is_on:
            button.setText("ON")
            button.setStyleSheet(
                f"""
                QPushButton {{
                    color: {accent_color};
                    background: rgba(10, 28, 20, 0.95);
                    border: 1px solid {accent_color};
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 900;
                    padding: 0 8px;
                }}
                QPushButton:hover {{
                    background: rgba(14, 34, 25, 0.98);
                }}
                """
            )
        else:
            button.setText("OFF")
            button.setStyleSheet(
                """
                QPushButton {
                    color: #ff7b7b;
                    background: #1a1111;
                    border: 1px solid #5a2525;
                    border-radius: 8px;
                    font-size: 10px;
                    font-weight: 900;
                    padding: 0 8px;
                }
                QPushButton:hover {
                    border-color: #7a3434;
                }
                """
            )

    def _update_home_metric_badge(self, badge_label, is_on: bool, on_color: str):
        if badge_label is None:
            return
        if is_on:
            # Đã làm sạch chú thích lỗi mã hóa.
            badge_label.setStyleSheet(
                f"""
                QLabel {{
                    color: {on_color};
                    font-size: 10px;
                    font-weight: 900;
                    background: transparent;
                    border: none;
                }}
                """
            )
        else:
            # Đã làm sạch chú thích lỗi mã hóa.
            badge_label.setStyleSheet(
                """
                QLabel {
                    color: #ff7e7e;
                    font-size: 10px;
                    font-weight: 900;
                    background: transparent;
                    border: none;
                }
                """
            )

    def toggle_home_macro(self):
        if not self.ensure_runtime_started():
            return
        current_on = hasattr(self, "btn_macro") and self.btn_macro and "ON" in self.btn_macro.text().upper()
        next_on = not current_on
        try:
            self.backend.set_paused(not next_on)
            self.update_macro_style(next_on)
        except Exception:
            pass

    def toggle_home_aim(self):
        if not self.ensure_runtime_started():
            return
        try:
            if hasattr(self.backend, "toggle_aim_assist_direct"):
                self.backend.toggle_aim_assist_direct()
        except Exception:
            pass

    def update_home_snapshot(self):
        if not hasattr(self, "home_page"):
            return

        def _safe_float(raw_text: str) -> float:
            try:
                return float(str(raw_text).strip())
            except Exception:
                return 0.0

        macro_text = "OFF"
        if hasattr(self, "btn_macro") and self.btn_macro:
            macro_text = "ON" if "ON" in self.btn_macro.text().upper() else "OFF"
        aim_text = "OFF"
        if hasattr(self, "btn_aim_status") and self.btn_aim_status:
            aim_text = "ON" if "ON" in self.btn_aim_status.text().upper() else "OFF"

        fps_text = "0"
        if hasattr(self, "lbl_aim_fps") and self.lbl_aim_fps:
            fps_text = self.lbl_aim_fps.text().replace("FPS :", "").replace("FPS:", "").strip() or "0"
        if fps_text in ("--", "N/A"):
            fps_text = "0"
        inf_text = "0"
        if hasattr(self, "lbl_aim_inf") and self.lbl_aim_inf:
            inf_text = self.lbl_aim_inf.text().replace("INF :", "").replace("INF:", "").replace("MS", "").strip() or "0"
        if inf_text in ("--", "N/A"):
            inf_text = "0"
        runtime_active = (aim_text == "ON") and (_safe_float(fps_text) > 0.0)

        macro_color = "#00e0ff" if macro_text == "ON" else "#ff7070"
        aim_color = "#00ffaa" if aim_text == "ON" else "#ff7070"

        if hasattr(self, "home_metric_macro_value"):
            if self.home_metric_macro_value.text() != macro_text:
                self.home_metric_macro_value.setText(macro_text)
            self.home_metric_macro_value.setStyleSheet(f"QLabel {{ color: {macro_color}; font-size: 14px; font-weight: 900; background: transparent; border: none; }}")
        if hasattr(self, "home_metric_macro_value_hint"):
            # Đã làm sạch chú thích lỗi mã hóa.
            self.home_metric_macro_value_hint.setVisible(macro_text == "ON")
        if hasattr(self, "home_metric_aim_value"):
            if self.home_metric_aim_value.text() != aim_text:
                self.home_metric_aim_value.setText(aim_text)
            self.home_metric_aim_value.setStyleSheet(f"QLabel {{ color: {aim_color}; font-size: 14px; font-weight: 900; background: transparent; border: none; }}")
        if hasattr(self, "home_metric_aim_value_hint"):
            # Đã làm sạch chú thích lỗi mã hóa.
            self.home_metric_aim_value_hint.setVisible(aim_text == "ON")
        if hasattr(self, "home_metric_fps_value"):
            if self.home_metric_fps_value.text() != fps_text:
                self.home_metric_fps_value.setText(fps_text)
        if hasattr(self, "home_metric_inf_value"):
            if self.home_metric_inf_value.text() != inf_text:
                self.home_metric_inf_value.setText(inf_text)
        if hasattr(self, "home_metric_fps_badge"):
            self._update_home_metric_badge(self.home_metric_fps_badge, runtime_active, "#8dffb1")
        if hasattr(self, "home_metric_inf_badge"):
            self._update_home_metric_badge(self.home_metric_inf_badge, runtime_active, "#ffcf5a")

        if hasattr(self, "home_macro_status_value"):
            if self.home_macro_status_value.text() != macro_text:
                self.home_macro_status_value.setText(macro_text)
            self.home_macro_status_value.setStyleSheet(f"QLabel {{ color: {macro_color}; font-size: 12px; font-weight: 800; background: transparent; border: none; }}")
        if hasattr(self, "home_aim_status_value"):
            if self.home_aim_status_value.text() != aim_text:
                self.home_aim_status_value.setText(aim_text)
            self.home_aim_status_value.setStyleSheet(f"QLabel {{ color: {aim_color}; font-size: 12px; font-weight: 800; background: transparent; border: none; }}")

        if hasattr(self, "home_macro_toggle_btn"):
            self._update_home_toggle_button_style(self.home_macro_toggle_btn, macro_text == "ON", "#66ffc2")
        if hasattr(self, "home_aim_toggle_btn"):
            self._update_home_toggle_button_style(self.home_aim_toggle_btn, aim_text == "ON", "#73f0ff")

        stance_text = "ĐỨNG"
        if hasattr(self, "lbl_stance") and self.lbl_stance:
            stance_text = self.lbl_stance.text().split(":")[-1].strip() or stance_text
        ads_text = "HOLD"
        if hasattr(self, "lbl_ads_status") and self.lbl_ads_status:
            ads_text = self.lbl_ads_status.text().split(":")[-1].strip() or ads_text
        capture_text = getattr(self, "current_capture_mode", "DXCAM")
        model_text = "N/A"
        if hasattr(self, "combo_aim_model") and self.combo_aim_model and self.combo_aim_model.count():
            model_text = self.combo_aim_model.currentText().strip() or model_text
        aim_capture_text = getattr(self, "current_aim_capture_mode", "DirectX")
        backend_text = "Chưa nạp"
        runtime_source = ""
        if hasattr(self, "last_data") and isinstance(self.last_data, dict):
            aim_runtime_state = self.last_data.get("aim", {})
            runtime_backend = str(aim_runtime_state.get("inference_backend", "") or "").strip()
            runtime_source = str(aim_runtime_state.get("runtime_source", "") or "").strip()
            if runtime_backend and runtime_backend.lower() not in {"not loaded", "booting", "idle"}:
                backend_text = self._format_home_aim_backend_text(runtime_backend, runtime_source)
        elif hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
            backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text

        snapshot_signature = (
            macro_text,
            aim_text,
            fps_text,
            inf_text,
            runtime_active,
            stance_text,
            ads_text,
            capture_text,
            model_text,
            backend_text,
            aim_capture_text,
        )
        if self._last_home_snapshot_signature == snapshot_signature:
            return
        self._last_home_snapshot_signature = snapshot_signature

        for attr_name, text in (
            ("home_macro_stance_value", stance_text),
            ("home_macro_ads_value", ads_text),
            ("home_macro_capture_value", capture_text),
            ("home_aim_model_value", model_text),
            ("home_aim_backend_value", backend_text),
            ("home_aim_capture_value", aim_capture_text),
        ):
            label = getattr(self, attr_name, None)
            if label is not None and label.text() != text:
                label.setText(text)

        self.update_main_page_banner()

    def list_aim_models(self):
        model_dir = Path(__file__).resolve().parents[1] / "bin" / "models"
        if not model_dir.exists():
            return []
        return sorted([p.name for p in model_dir.glob("*.onnx") if p.is_file()])

    def _format_aim_runtime_source_text(self, runtime_source: str) -> str:
        text = str(runtime_source or "").strip()
        normalized = text.lower()
        if "error" in normalized or "lỗi" in normalized:
            return "Runtime: Native DLL lỗi"
        if "not ready" in normalized or "chưa" in normalized:
            return "Runtime: Native DLL chờ"
        if "native" in normalized:
            return "Runtime: Native DLL"
        return "Runtime: Chưa nạp"

    def _normalize_aim_backend_text(self, backend_text: str) -> str:
        text = str(backend_text or "").strip() or "Chưa nạp"
        if text.lower() in {"not loaded", "booting", "idle"}:
            return "Chưa nạp"
        for prefix in ("Native DLL /", "Native "):
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
                break
        if text.lower() in {"not ready", "none", "n/a"}:
            return "Chưa nạp"
        return text.upper() if text != "Chưa nạp" else text

    def _format_aim_backend_meta_text(self, backend_text: str, runtime_source: str = "") -> str:
        return f"Backend: {self._normalize_aim_backend_text(backend_text)}"

    def _format_home_aim_backend_text(self, backend_text: str, runtime_source: str = "") -> str:
        runtime = self._format_aim_runtime_source_text(runtime_source).replace("Runtime:", "").strip()
        backend = self._normalize_aim_backend_text(backend_text)
        if runtime and runtime != "Chưa nạp":
            return f"{runtime} / {backend}"
        return backend

    def set_aim_model_status(self, text: str, color: str = "#cfcfcf"):
        normalized = {
            "Không có model": "\u004b\u0068\u00f4\u006e\u0067 \u0063\u00f3 \u006d\u006f\u0064\u0065\u006c",
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
        }.get(text, text)
        if normalized == "\u0110\u00e3 \u0074\u1ea3\u0069":
            normalized = "\u0110\u00e3 \u004e\u1ea1\u0070"
        if hasattr(self, "lbl_aim_model_status") and self.lbl_aim_model_status:
            self.lbl_aim_model_status.setText(normalized)
            self.lbl_aim_model_title.setStyleSheet("""
                QLabel {
                    color: #cfcfcf;
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            self.lbl_aim_model_sep.setStyleSheet("""
                QLabel {
                    color: #cfcfcf;
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }
            """)
            self.lbl_aim_model_status.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    font-size: 11px;
                    font-weight: 700;
                    background: transparent;
                }}
            """)
        if hasattr(self, "lbl_aim_model_status_meta") and self.lbl_aim_model_status_meta:
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            self.lbl_aim_model_status_meta.setText(self._format_aim_runtime_source_text(runtime_source))
            self.lbl_aim_model_status_meta.setStyleSheet(f"""
                QLabel {{
                    color: #cfcfcf;
                    font-size: 10px;
                    font-weight: 700;
                    background: #1b1b1b;
                    border: 1px solid #3a3a3a;
                    border-radius: 5px;
                    padding: 2px 6px;
                }}
            """)
        if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
            backend_text = "Chưa nạp"
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text
            self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(backend_text, runtime_source))
        self.update_home_snapshot()

    def position_aim_model_notice(self):
        if not hasattr(self, "aim_model_notice") or self.aim_model_notice is None:
            return
        if not hasattr(self, "container") or self.container is None:
            return
        if not hasattr(self, "aim_workspace") or self.aim_workspace is None:
            return
        self.aim_model_notice.adjustSize()
        workspace_pos = self.aim_workspace.mapTo(self.container, QPoint(0, 0))
        workspace_width = self.aim_workspace.width()
        x = workspace_pos.x() + max(12, workspace_width - self.aim_model_notice.width() - 14)
        y = workspace_pos.y() + 18
        self.aim_model_notice.move(x, y)
        self.aim_model_notice.raise_()

    def show_aim_model_notice(self, model_name: str, duration_ms: int = 3000, error: bool = False):
        if not hasattr(self, "aim_model_notice") or self.aim_model_notice is None:
            return
        model_name = (model_name or "").strip()
        if model_name == "Không có model":
            return
        if not model_name or model_name in ("Không có model", "Khong co model"):
            return
        fg = "#ffb3b3" if error else "#f4f4f4"
        border = "#7a3a3a" if error else "#545454"
        # Đã làm sạch chú thích lỗi mã hóa.
        self.aim_model_notice.setText(
            f"\u004c\u1ed7\u0069 \u006e\u1ea1\u0070 \u006d\u006f\u0064\u0065\u006c: {model_name}"
            if error
            else f"\u0110\u00e3 \u006e\u1ea1\u0070 \u006d\u006f\u0064\u0065\u006c: {model_name}"
        )
        self.aim_model_notice.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(16, 16, 16, 238);
                color: {fg};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 700;
            }}
        """)
        self.aim_model_notice.setMinimumWidth(280)
        self.aim_model_notice.setMinimumHeight(44)
        self.aim_model_notice.show()
        self.aim_model_notice.raise_()
        if hasattr(self, "aim_model_notice_timer") and self.aim_model_notice_timer:
            self.aim_model_notice_timer.start(duration_ms)

    def on_aim_model_changed_safe(self, index: int):
        if index < 0 or not hasattr(self, "combo_aim_model"):
            return
        text = self.combo_aim_model.currentText().strip()
        if not text or text in (
            "Không có model",
            "Không có model",
            "\u004b\u0068\u00f4\u006e\u0067 \u0063\u00f3 \u006d\u006f\u0064\u0065\u006c",
        ):
            self.set_aim_model_status("\u004b\u0068\u00f4\u006e\u0067 \u0063\u00f3 \u006d\u006f\u0064\u0065\u006c", "#ff9c9c")
            return
        self.set_aim_model_status("\u0110\u00e3 \u0074\u1ea3\u0069", "#cfcfcf")

    def on_aim_display_toggle_changed(self, *_args):
        self.update_home_snapshot()
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def on_aim_advanced_toggle_changed(self, *_args):
        self.apply_aim_window_flags()
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def on_aim_advanced_dropdown_changed(self, *_args):
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def apply_aim_window_flags(self):
        toggles = getattr(self, "aim_toggle_controls", {})
        ui_topmost = bool(toggles.get("UI TopMost").isChecked()) if toggles.get("UI TopMost") is not None else False
        stream_guard = bool(toggles.get("StreamGuard").isChecked()) if toggles.get("StreamGuard") is not None else False

        try:
            flags = self.windowFlags()
            if ui_topmost:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            else:
                flags &= ~Qt.WindowType.WindowStaysOnTopHint
            was_visible = self.isVisible()
            was_hidden = self.isHidden()
            self.setWindowFlags(flags)
            if was_visible and not was_hidden:
                self.show()
        except Exception:
            pass

        for widget in (self, getattr(self, "game_overlay", None), getattr(self, "crosshair", None)):
            try:
                if widget is None:
                    continue
                hwnd = int(widget.winId())
                # WDA_EXCLUDEFROMCAPTURE on Windows 10 2004+, fallback uses WDA_MONITOR.
                affinity = 0x11 if stream_guard else 0x00
                if not ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, affinity) and stream_guard:
                    ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x01)
            except Exception:
                pass

    def load_aim_toggle_controls(self, aim_toggles: dict):
        for key, checkbox in getattr(self, "aim_toggle_controls", {}).items():
            if checkbox is None:
                continue
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(aim_toggles.get(key, checkbox.isChecked())))
            checkbox.blockSignals(False)
        self.apply_aim_window_flags()

    def save_aim_toggle_controls(self, aim_toggles: dict):
        for key, checkbox in getattr(self, "aim_toggle_controls", {}).items():
            if checkbox is not None:
                aim_toggles[key] = bool(checkbox.isChecked())

    def load_aim_dropdown_controls(self, aim_dropdowns: dict):
        for key, control in getattr(self, "aim_dropdown_controls", {}).items():
            combo = control.get("combo")
            spec = control.get("spec", {})
            if combo is None:
                continue
            value = str(aim_dropdowns.get(key, spec.get("default", "")))
            if combo.findText(value) < 0:
                value = str(spec.get("default", ""))
            combo.blockSignals(True)
            combo.setCurrentText(value)
            combo.blockSignals(False)

    def save_aim_dropdown_controls(self, aim_dropdowns: dict):
        for key, control in getattr(self, "aim_dropdown_controls", {}).items():
            combo = control.get("combo")
            if combo is not None:
                aim_dropdowns[key] = combo.currentText().strip()

    def _normalize_argb_hex(self, value: str, fallback: str = "#FFFFFFFF") -> str:
        text = str(value or "").strip()
        if text.startswith("#") and len(text) == 9:
            return text.upper()
        color = QColor(text)
        if not color.isValid():
            return fallback.upper()
        return f"#{color.alpha():02X}{color.red():02X}{color.green():02X}{color.blue():02X}"

    def _qcolor_from_argb_hex(self, value: str, fallback: str = "#FFFFFFFF") -> QColor:
        text = self._normalize_argb_hex(value, fallback)
        return QColor(int(text[3:5], 16), int(text[5:7], 16), int(text[7:9], 16), int(text[1:3], 16))

    def set_aim_color_button(self, key: str, value: str):
        button = getattr(self, "aim_color_controls", {}).get(key)
        if button is None:
            return
        normalized = self._normalize_argb_hex(value)
        button.setProperty("color_value", normalized)
        color = self._qcolor_from_argb_hex(normalized)
        button.setText(normalized)
        button.setStyleSheet(
            f"""
            QPushButton {{
                color: #f2f2f2;
                background: rgba({color.red()}, {color.green()}, {color.blue()}, 150);
                border: 1px solid rgba({color.red()}, {color.green()}, {color.blue()}, 230);
                border-radius: 6px;
                font-size: 10px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                border: 1px solid #ffffff;
            }}
            """
        )

    def choose_aim_color(self, key: str):
        button = getattr(self, "aim_color_controls", {}).get(key)
        current_value = button.property("color_value") if button is not None else "#FFFFFFFF"
        initial = self._qcolor_from_argb_hex(str(current_value or "#FFFFFFFF"))
        chosen = QColorDialog.getColor(initial, self, f"Chọn {key}", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if not chosen.isValid():
            return
        value = f"#{chosen.alpha():02X}{chosen.red():02X}{chosen.green():02X}{chosen.blue():02X}"
        self.set_aim_color_button(key, value)
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)
        self.signal_settings_changed.emit()

    def load_aim_color_controls(self, aim_colors: dict):
        defaults = {
            "FOV Color": "#FF8080FF",
            "Detected Player Color": "#FF00FFFF",
            "Theme Color": "#FF722ED1",
        }
        for key, button in getattr(self, "aim_color_controls", {}).items():
            self.set_aim_color_button(key, str(aim_colors.get(key, defaults.get(key, "#FFFFFFFF"))))

    def save_aim_color_controls(self, aim_colors: dict):
        for key, button in getattr(self, "aim_color_controls", {}).items():
            if button is not None:
                aim_colors[key] = self._normalize_argb_hex(str(button.property("color_value") or "#FFFFFFFF"))

    def choose_aim_file_location(self, key: str):
        button = getattr(self, "aim_file_controls", {}).get(key)
        current = str(button.property("file_value") or "") if button is not None else ""
        start_dir = str(Path(current).parent) if current else str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(self, f"Chọn {key}", start_dir, "DLL Files (*.dll);;All Files (*.*)")
        if not file_path:
            return
        self.set_aim_file_button(key, file_path)
        self.signal_settings_changed.emit()

    def set_aim_file_button(self, key: str, value: str):
        button = getattr(self, "aim_file_controls", {}).get(key)
        if button is None:
            return
        text = str(value or "").strip()
        button.setProperty("file_value", text)
        button.setText(Path(text).name if text else "Chọn DLL")

    def load_aim_file_controls(self, aim_file_locations: dict):
        for key, button in getattr(self, "aim_file_controls", {}).items():
            self.set_aim_file_button(key, str(aim_file_locations.get(key, "")))

    def save_aim_file_controls(self, aim_file_locations: dict):
        for key, button in getattr(self, "aim_file_controls", {}).items():
            if button is not None:
                aim_file_locations[key] = str(button.property("file_value") or "")

    def load_aim_minimize_controls(self, aim_minimize: dict):
        for key, checkbox in getattr(self, "aim_minimize_controls", {}).items():
            if checkbox is None:
                continue
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(aim_minimize.get(key, False)))
            checkbox.blockSignals(False)

    def save_aim_minimize_controls(self, aim_minimize: dict):
        for key, checkbox in getattr(self, "aim_minimize_controls", {}).items():
            if checkbox is not None:
                aim_minimize[key] = bool(checkbox.isChecked())

    def refresh_aim_model_list(self, selected_model: str | None = None):
        if not hasattr(self, "combo_aim_model") or self.combo_aim_model is None:
            return

        models = self.list_aim_models()
        self.combo_aim_model.blockSignals(True)
        self.combo_aim_model.clear()

        if not models:
            self.combo_aim_model.addItem("Không có model")
            self.combo_aim_model.setEnabled(False)
            self.set_aim_model_status("Không có model", "#ff9c9c")
            self.combo_aim_model.blockSignals(False)
            return

        self.combo_aim_model.setEnabled(True)
        self.combo_aim_model.addItems(models)

        target_model = selected_model if selected_model in models else models[0]
        self.combo_aim_model.setCurrentText(target_model)
        self.combo_aim_model.blockSignals(False)
        self.set_aim_model_status("Đã tải", "#74ffc8")

    def on_aim_model_changed(self, index: int):
        if index < 0 or not hasattr(self, "combo_aim_model"):
            return
        text = self.combo_aim_model.currentText().strip()
        if not text or text == "Không có model":
            self.set_aim_model_status("Không có model", "#ff9c9c")
        else:
            self.set_aim_model_status("Đã tải", "#74ffc8")

    def on_aim_model_changed(self, index: int):
        if index < 0 or not hasattr(self, "combo_aim_model"):
            return
        text = self.combo_aim_model.currentText().strip()
        if not text or text in ("Không có model", "Khong co model"):
            self.set_aim_model_status("Không có model", "#ff9c9c")
        else:
            self.set_aim_model_status("Đã tải", "#74ffc8")
            self.show_aim_model_notice(text)

    def update_scope_intensity_label(self, scope_key: str, value: int):
        label = getattr(self, "scope_value_labels", {}).get(scope_key)
        if label is not None:
            label.setText(f"{value}%")

    def update_aim_fov_label(self, value: int):
        if hasattr(self, "aim_fov_value_label") and self.aim_fov_value_label:
            self.aim_fov_value_label.setText(str(int(value)))

    def update_aim_confidence_label(self, value: int):
        if hasattr(self, "aim_confidence_value_label") and self.aim_confidence_value_label:
            self.aim_confidence_value_label.setText(f"{int(value)}%")

    def update_aim_trigger_delay_label(self, value: int):
        if hasattr(self, "aim_trigger_delay_value_label") and self.aim_trigger_delay_value_label:
            self.aim_trigger_delay_value_label.setText(f"{int(value)} ms")

    def update_aim_capture_fps_label(self, value: int):
        if hasattr(self, "aim_capture_fps_value_label") and self.aim_capture_fps_value_label:
            self.aim_capture_fps_value_label.setText(str(int(value)))

    def update_aim_jitter_label(self, value: int):
        if hasattr(self, "aim_jitter_value_label") and self.aim_jitter_value_label:
            self.aim_jitter_value_label.setText(str(int(value)))

    def update_aim_sensitivity_label(self, value: int):
        if hasattr(self, "aim_sensitivity_value_label") and self.aim_sensitivity_value_label:
            self.aim_sensitivity_value_label.setText(f"{float(value) / 100.0:.2f}")

    def update_aim_ema_label(self, value: int):
        if hasattr(self, "aim_ema_value_label") and self.aim_ema_value_label:
            self.aim_ema_value_label.setText(f"{float(value) / 100.0:.2f}")

    def update_aim_sticky_threshold_label(self, value: int):
        if hasattr(self, "aim_sticky_threshold_value_label") and self.aim_sticky_threshold_value_label:
            self.aim_sticky_threshold_value_label.setText(str(int(value)))

    def update_aim_dynamic_fov_label(self, value: int):
        if hasattr(self, "aim_dynamic_fov_value_label") and self.aim_dynamic_fov_value_label:
            self.aim_dynamic_fov_value_label.setText(str(int(value)))

    def update_aim_listing_slider_label(self, key: str, slider_value: int):
        control = getattr(self, "aim_listing_controls", {}).get(key)
        if not control:
            return
        actual_value = self.aim_test_slider_to_value(control["spec"], slider_value)
        control["value_label"].setText(self.format_aim_test_value(control["spec"], actual_value))

    def load_aim_listing_sliders(self, aim_sliders: dict):
        for key, control in getattr(self, "aim_listing_controls", {}).items():
            spec = control.get("spec", {})
            slider = control.get("slider")
            if slider is None:
                continue
            actual_value = aim_sliders.get(key, spec.get("default", 0))
            slider_value = self.aim_test_value_to_slider(spec, actual_value)
            slider_value = max(int(spec.get("min", slider.minimum())), min(int(spec.get("max", slider.maximum())), slider_value))
            slider.setValue(slider_value)
            self.update_aim_listing_slider_label(key, slider_value)

    def save_aim_listing_sliders(self, aim_sliders: dict):
        for key, control in getattr(self, "aim_listing_controls", {}).items():
            slider = control.get("slider")
            if slider is None:
                continue
            aim_sliders[key] = self.aim_test_slider_to_value(control["spec"], slider.value())

    def update_aim_primary_position_label(self, value: int):
        if hasattr(self, "aim_primary_position_value_label") and self.aim_primary_position_value_label:
            self.aim_primary_position_value_label.setText(str(int(value)))

    def update_aim_secondary_position_label(self, value: int):
        if hasattr(self, "aim_secondary_position_value_label") and self.aim_secondary_position_value_label:
            self.aim_secondary_position_value_label.setText(str(int(value)))

    def build_aim_test_slider_specs(self):
        return [
            {"key": "Dynamic FOV Size", "label": "FOV Động", "min": 10, "max": 640, "step": 1, "scale": 1, "default": 200, "format": "int"},
            {"key": "Mouse Sensitivity (+/-)", "label": "Độ Nhạy Chuột", "min": 1, "max": 100, "step": 1, "scale": 100, "default": 0.80, "format": "float2"},
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            # Đã làm sạch chú thích lỗi mã hóa.
            {"key": "EMA Smoothening", "label": "EMA Smooth", "min": 1, "max": 100, "step": 1, "scale": 100, "default": 0.5, "format": "float2"},
            {"key": "Kalman Lead Time", "label": "Kalman Lead", "min": 2, "max": 30, "step": 1, "scale": 100, "default": 0.10, "format": "float2"},
            {"key": "WiseTheFox Lead Time", "label": "Wise Lead", "min": 2, "max": 30, "step": 1, "scale": 100, "default": 0.15, "format": "float2"},
            {"key": "Shalloe Lead Multiplier", "label": "Shalloe Lead", "min": 2, "max": 20, "step": 1, "scale": 2, "default": 3.0, "format": "float1"},
            {"key": "AI Confidence Font Size", "label": "Font Detect", "min": 1, "max": 30, "step": 1, "scale": 1, "default": 20, "format": "int"},
            {"key": "Corner Radius", "label": "Bo Góc", "min": 0, "max": 100, "step": 1, "scale": 1, "default": 0, "format": "int"},
            {"key": "Border Thickness", "label": "Độ Dày Viền", "min": 1, "max": 100, "step": 1, "scale": 10, "default": 1.0, "format": "float1"},
            {"key": "Opacity", "label": "Độ Trong", "min": 0, "max": 10, "step": 1, "scale": 10, "default": 1.0, "format": "float1"},
        ]

    def aim_test_slider_to_value(self, spec: dict, slider_value: int):
        scale = spec.get("scale", 1)
        if scale == 1:
            return int(slider_value)
        return float(slider_value) / float(scale)

    def aim_test_value_to_slider(self, spec: dict, actual_value):
        scale = spec.get("scale", 1)
        if scale == 1:
            return int(round(float(actual_value)))
        return int(round(float(actual_value) * float(scale)))

    def format_aim_test_value(self, spec: dict, actual_value) -> str:
        fmt = spec.get("format", "int")
        value = float(actual_value)
        if fmt == "percent":
            return f"{int(round(value))}%"
        if fmt == "float2":
            return f"{value:.2f}"
        if fmt == "float1":
            return f"{value:.1f}"
        return str(int(round(value)))

    def update_aim_test_slider_label(self, key: str, slider_value: int):
        control = getattr(self, "aim_test_controls", {}).get(key)
        if not control:
            return
        actual_value = self.aim_test_slider_to_value(control["spec"], slider_value)
        control["value_label"].setText(self.format_aim_test_value(control["spec"], actual_value))

    def update_aim_test_row_enabled(self, key: str, enabled: bool):
        control = getattr(self, "aim_test_controls", {}).get(key)
        if not control:
            return
        control["slider"].setEnabled(enabled)
        control["value_label"].setEnabled(enabled)

    def setup_hover_hints(self):
        self.hover_hint = QLabel(self.container)
        self.hover_hint.setObjectName("HoverHint")
        self.hover_hint.setWordWrap(True)
        self.hover_hint.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.hover_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hover_hint.setStyleSheet("""
            QLabel#HoverHint {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(27, 31, 37, 248),
                    stop: 1 rgba(16, 19, 24, 248)
                );
                color: #f8fbff;
                border: 1px solid #576170;
                border-radius: 9px;
                padding: 8px 10px;
                font-size: 11px;
                font-weight: 600;
                line-height: 1.35em;
            }
        """)
        hover_shadow = QGraphicsDropShadowEffect(self.hover_hint)
        hover_shadow.setBlurRadius(22)
        hover_shadow.setOffset(0, 6)
        hover_shadow.setColor(QColor(0, 0, 0, 145))
        self.hover_hint.setGraphicsEffect(hover_shadow)
        self.hover_hint.hide()
        self._hover_hint_margin = QPoint(16, 18)
        self._hover_hint_anchor = None
        self._hover_hint_last_pos = None
        self._hover_hint_timer = QTimer(self)
        self._hover_hint_timer.setInterval(100)
        self._hover_hint_timer.timeout.connect(self._tick_hover_hint)

        self.hover_hint_targets = {}
        if hasattr(self, 'header_detection'):
            self._add_hover_widget(self.header_detection, "Thông tin vũ khí hiện tại.")
        if hasattr(self, 'header_settings'):
            self._add_hover_widget(self.header_settings, "Thiết lập các phím chức năng, chế độ chụp và các tùy chọn macro cơ bản.")
        if hasattr(self, 'header_crosshair'):
            self._add_hover_widget(self.header_crosshair, "Thiết lập tâm ngắm, kiểu hiển thị và màu hiển thị.")
        if hasattr(self, 'lbl_fastloot_row'):
            self._add_hover_widget(self.lbl_fastloot_row, "Tính năng nhặt đồ nhanh.")
        if hasattr(self, 'lbl_slide_row'):
            self._add_hover_widget(self.lbl_slide_row, "Giữ Shift + W + ( A hoặc D ) rồi bấm C để thực hiện thao tác lướt ngồi.")
        if hasattr(self, 'lbl_stopkeys_row'):
            self._add_hover_widget(self.lbl_stopkeys_row, "Danh sách phím dừng khẩn cấp.")
        if hasattr(self, 'lbl_adsmode_row'):
            self._add_hover_widget(self.lbl_adsmode_row, "Trạng thái chế độ ADS hiện tại.")
        if hasattr(self, 'lbl_guitoggle_row'):
            self._add_hover_widget(self.lbl_guitoggle_row, "Phím ẩn hoặc hiện cửa sổ app ngay lập tức.")
        if hasattr(self, 'lbl_overlay_row'):
            self._add_hover_widget(self.lbl_overlay_row, "Phím điều khiển lớp overlay hiển thị trong game.")
        if hasattr(self, 'lbl_capture_row'):
            self._add_hover_widget(self.lbl_capture_row, "Chọn backend chụp màn hình dùng cho detect và runtime.")

    def _add_hover_target(self, parent: QWidget, rect: QRect, text: str):
        anchor = QFrame(parent)
        anchor.setGeometry(rect)
        anchor.setStyleSheet("background: transparent; border: none;")
        anchor.setCursor(Qt.CursorShape.WhatsThisCursor)
        anchor.installEventFilter(self)
        self.hover_hint_targets[anchor] = (anchor, text)

    def _add_hover_widget(self, widget: QWidget, text: str):
        if widget is None:
            return
        widget.setCursor(Qt.CursorShape.WhatsThisCursor)
        widget.setMouseTracking(True)
        widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        widget.installEventFilter(self)
        self.hover_hint_targets[widget] = (widget, text)

    def show_hover_hint(self, anchor: QWidget, text: str):
        self._hover_hint_anchor = anchor
        self._hover_hint_last_pos = None
        self.hover_hint.setText(text)
        self.hover_hint.adjustSize()
        hint_width = min(max(self.hover_hint.sizeHint().width(), 220), 320)
        self.hover_hint.resize(hint_width, self.hover_hint.sizeHint().height() + 8)
        self.hover_hint.show()
        self.hover_hint.raise_()
        self._move_hover_hint(anchor)
        if not self._hover_hint_timer.isActive():
            self._hover_hint_timer.start()

    def _move_hover_hint(self, anchor: QWidget | None = None, local_pos: QPoint | None = None):
        if not hasattr(self, 'hover_hint') or not self.hover_hint or not self.hover_hint.isVisible():
            return
        if local_pos is not None:
            self._hover_hint_last_pos = QPoint(local_pos)
        if anchor is not None:
            if local_pos is None:
                local_pos = self._hover_hint_last_pos
            if local_pos is None:
                local_pos = anchor.mapFromGlobal(anchor.cursor().pos())
            mouse_pos = anchor.mapTo(self.container, local_pos)
        else:
            mouse_pos = self.container.mapFromGlobal(self.cursor().pos())
        x = mouse_pos.x() + self._hover_hint_margin.x()
        y = mouse_pos.y() + self._hover_hint_margin.y()
        max_x = self.container.width() - self.hover_hint.width() - 10
        max_y = self.container.height() - self.hover_hint.height() - 10
        x = max(10, min(x, max_x))
        y = max(36, min(y, max_y))
        self.hover_hint.move(x, y)

    def hide_hover_hint(self):
        if hasattr(self, 'hover_hint') and self.hover_hint:
            self.hover_hint.hide()
        self._hover_hint_anchor = None
        self._hover_hint_last_pos = None
        if hasattr(self, '_hover_hint_timer') and self._hover_hint_timer.isActive():
            self._hover_hint_timer.stop()

    def _tick_hover_hint(self):
        if not getattr(self, '_hover_hint_anchor', None):
            return
        self._move_hover_hint(self._hover_hint_anchor)

    def load_style(self):
        """Loads the external QSS stylesheet"""
        try:
            style_candidates = [
                get_resource_path("style.qss"),
                get_resource_path("GUI/style.qss"),
            ]
            style_path = next((path for path in style_candidates if os.path.exists(path)), None)
            if style_path:
                with open(style_path, "r", encoding="utf-8") as f:
                    qss = f.read()
                arrow_candidates = [
                    get_resource_path("assets/combo-arrow.svg"),
                    get_resource_path("GUI/assets/combo-arrow.svg"),
                ]
                combo_arrow_path = next((path for path in arrow_candidates if os.path.exists(path)), None)
                if combo_arrow_path:
                    combo_arrow = Path(combo_arrow_path).resolve().as_posix()
                    qss = qss.replace("__COMBO_ARROW__", f"\"{combo_arrow}\"")
                else:
                    qss = qss.replace("image: url(__COMBO_ARROW__);", "")
                if qss.strip():
                    self.setStyleSheet(qss)
                return
            if APP_STYLE_QSS.strip():
                self.setStyleSheet(APP_STYLE_QSS)
        except Exception as e:
            logger.warning("Could not load style.qss: %s", e)
            if APP_STYLE_QSS.strip():
                self.setStyleSheet(APP_STYLE_QSS)

    def build_crosshair_preview_icon(self, style_name: str) -> QIcon:
        pixmap = QPixmap(28, 14)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#f2f2f2"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = 14, 7

        def gap_cross(gap: int, arm: int):
            painter.drawLine(cx - gap - arm, cy, cx - gap, cy)
            painter.drawLine(cx + gap, cy, cx + gap + arm, cy)
            painter.drawLine(cx, cy - gap - arm, cx, cy - gap)
            painter.drawLine(cx, cy + gap, cx, cy + gap + arm)

        # Đồng bộ preview với renderer runtime của CrosshairOverlay để dropdown/current preview khớp nhau.
        if style_name == "dot":
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 2, 2)
        elif style_name == "plus":
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)
        elif style_name == "x":
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx - 4, cy + 4, cx + 4, cy - 4)
        elif style_name == "circle":
            painter.drawEllipse(QPoint(cx, cy), 4, 4)
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 1, 1)
        elif style_name == "hollow_circle":
            painter.drawEllipse(QPoint(cx, cy), 4, 4)
        elif style_name == "tactical":
            gap_cross(3, 5)
            painter.setBrush(QBrush(QColor("#f2f2f2")))
            painter.drawEllipse(QPoint(cx, cy), 1, 1)
        elif style_name == "small_cross":
            gap_cross(2, 3)
        elif style_name == "thick_cross":
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawLine(cx - 5, cy, cx + 5, cy)
            painter.drawLine(cx, cy - 5, cx, cy + 5)
        elif style_name == "sniper":
            gap_cross(3, 6)
            painter.drawEllipse(QPoint(cx, cy), 5, 5)
        elif style_name == "diamond":
            painter.drawLine(cx, cy - 4, cx + 4, cy)
            painter.drawLine(cx + 4, cy, cx, cy + 4)
            painter.drawLine(cx, cy + 4, cx - 4, cy)
            painter.drawLine(cx - 4, cy, cx, cy - 4)
        elif style_name == "triangle":
            painter.drawLine(cx, cy - 4, cx - 4, cy + 3)
            painter.drawLine(cx - 4, cy + 3, cx + 4, cy + 3)
            painter.drawLine(cx + 4, cy + 3, cx, cy - 4)
        elif style_name == "minimal":
            gap_cross(1, 2)
        else:
            gap_cross(2, 4)

        painter.end()
        return QIcon(pixmap)

    def build_color_preview_icon(self, color_value) -> QIcon:
        if isinstance(color_value, QColor):
            swatch = color_value
        else:
            color_map = {
                "Đỏ": QColor(255, 30, 30),
                "Đỏ Cam": QColor(255, 69, 0),
                "Cam": QColor(255, 140, 0),
                "Vàng": QColor(255, 215, 0),
                "Xanh Lá": QColor(0, 255, 0),
                "Xanh Ngọc": QColor(0, 255, 255),
                "Xanh Dương": QColor(0, 180, 255),
                "Tím": QColor(180, 0, 255),
                "Tím Hồng": QColor(255, 60, 255),
                "Hồng": QColor(255, 105, 180),
                "Trắng": QColor(255, 255, 255),
                "Bạc": QColor(192, 192, 192),
            }
            swatch = color_map.get(color_value, QColor(255, 30, 30))

        pixmap = QPixmap(22, 22)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor("#6a6a6a"), 1))
        painter.setBrush(QBrush(swatch))
        painter.drawEllipse(4, 4, 14, 14)
        painter.end()
        return QIcon(pixmap)

    def setup_ui_v2(self):
        root_widget = QWidget()
        root_widget.setStyleSheet("background: transparent;")
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root_widget)

        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        self.container.setStyleSheet("""
            QFrame#MainContainer {
                background: #1b1b1b;
                border: 1px solid #313131;
                border-radius: 14px;
            }
        """)
        self._setup_root_layout = root_layout
        self._setup_ui_shell_bootstrap = True
        self.style_crosshair_combo(QComboBox())

    def style_crosshair_combo(self, widget: QComboBox):
        widget.setStyleSheet("""
            QComboBox {
                background-color: #1b1b1b;
                color: #d6d6d6;
                border: 1px solid #444;
                border-radius: 6px;
                font-size: 11px;
                padding: 0 10px;
            }
            QComboBox:hover {
                background-color: #1b1b1b;
                border: 1px solid #666;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background: #1b1b1b;
                color: #d6d6d6;
                border: 1px solid #333333;
                outline: none;
                padding: 4px;
                selection-background-color: #232323;
            }
        """)

    def create_section_title_float(self, parent: QWidget, text: str):
        if "\\u" in text:
            try:
                text = text.encode("utf-8").decode("unicode_escape")
            except Exception:
                pass
        label = QLabel(text, parent)
        label.setObjectName("SectionTitleFloat")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        fm = QFontMetrics(label.font())
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        label.setFixedSize(text_width + 28, max(18, text_height + 4))
        label.raise_()
        return label

    def position_section_title_float(self, label: QLabel, parent: QWidget):
        if label is None or parent is None:
            return
        x = max(12, (parent.width() - label.width()) // 2)
        y = 1
        label.move(x, y)

    def position_all_macro_titles(self):
        title_pairs = (
            ("header_detection", "panel_detection"),
            ("header_settings", "group_settings"),
            ("header_capture", "capture_box"),
            ("header_scope", "scope_box"),
            ("header_crosshair", "crosshair_box"),
        )
        for label_attr, parent_attr in title_pairs:
            label = getattr(self, label_attr, None)
            parent = getattr(self, parent_attr, None)
            if isinstance(label, QLabel) and parent is not None:
                self.position_section_title_float(label, parent)
        if not getattr(self, "_setup_ui_shell_bootstrap", False):
            return
        self._setup_ui_shell_bootstrap = False
        root_layout = getattr(self, "_setup_root_layout", None)
        if root_layout is None:
            return
        root_layout.addWidget(self.container)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            QFrame#TitleBar {
                background: transparent;
                border: none;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
        """)
        header_layout = QHBoxLayout(self.title_bar)
        header_layout.setContentsMargins(10, 0, 10, 0)

        btn_min = QPushButton("-")
        btn_min.setObjectName("MinBtn")
        btn_min.setFixedSize(20, 20)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_min.setStyleSheet("""
            QPushButton#MinBtn {
                background: #2b2f33;
                color: #d6d9dc;
                border: 1px solid #3f454a;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 900;
            }
            QPushButton#MinBtn:hover {
                background: #353b40;
                color: #ffffff;
                border: 1px solid #5c656d;
            }
        """)
        btn_min.clicked.connect(self.minimize_to_taskbar)

        btn_close = QPushButton("X")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn_close.setStyleSheet("""
            QPushButton#CloseBtn {
                background: #2b2f33;
                color: #ff5d5d;
                border: 1px solid #3f454a;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 900;
            }
            QPushButton#CloseBtn:hover {
                background: #4a1e22;
                color: #ffffff;
                border: 1px solid #ff6f6f;
            }
        """)
        btn_close.clicked.connect(self.handle_close_action)

        self.app_title_label = QLabel("Macro & Aim By Di88")
        self.app_title_label.setObjectName("AppTitle")
        self.app_title_label.setStyleSheet("""
            QLabel#AppTitle {
                color: #e9edf2;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0px;
                background: transparent;
                border: none;
            }
        """)
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(4)
        glow.setColor(QColor(0, 0, 0, 200))
        glow.setOffset(1, 1)
        self.app_title_label.setGraphicsEffect(glow)

        self.app_logo = QLabel()
        icon_path = get_resource_path("di88vp.ico")
        logo_icon = QIcon(icon_path)
        self.app_logo.setPixmap(logo_icon.pixmap(22, 22))
        self.app_logo.setContentsMargins(0, 0, 5, 0)

        left_title_placeholder = QWidget()
        left_title_placeholder.setFixedWidth(45)
        left_title_placeholder.setStyleSheet("background: transparent; border: none;")

        title_center_wrap = QWidget()
        title_center_wrap.setStyleSheet("background: transparent; border: none;")
        title_center_layout = QHBoxLayout(title_center_wrap)
        title_center_layout.setContentsMargins(0, 0, 0, 0)
        title_center_layout.setSpacing(0)
        title_center_layout.addWidget(self.app_logo)
        title_center_layout.addWidget(self.app_title_label)

        right_controls_wrap = QWidget()
        right_controls_wrap.setFixedWidth(45)
        right_controls_wrap.setStyleSheet("background: transparent; border: none;")
        right_controls_layout = QHBoxLayout(right_controls_wrap)
        right_controls_layout.setContentsMargins(0, 0, 0, 0)
        right_controls_layout.setSpacing(5)
        right_controls_layout.addWidget(btn_min)
        right_controls_layout.addWidget(btn_close)

        header_layout.addWidget(left_title_placeholder, 0)
        header_layout.addStretch(1)
        header_layout.addWidget(title_center_wrap, 0, Qt.AlignmentFlag.AlignCenter)
        header_layout.addStretch(1)
        header_layout.addWidget(right_controls_wrap, 0)

        self.title_bar.mousePressEvent = self.mousePressEvent
        self.title_bar.mouseMoveEvent = self.mouseMoveEvent
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_widget.setObjectName("MainContentShell")
        content_widget.setStyleSheet("""
            QWidget#MainContentShell {
                background: #1b1b1b;
                border: none;
            }
        """)
        content_shell = QHBoxLayout(content_widget)
        content_shell.setContentsMargins(10, 10, 10, 10)
        content_shell.setSpacing(12)

        self.left_nav = QFrame()
        self.left_nav.setObjectName("MainSideNav")
        self.left_nav.setFixedWidth(160)
        self.left_nav.setStyleSheet("""
            QFrame#MainSideNav {
                background: #121212;
                border: 1px solid #313131;
                border-radius: 14px;
            }
        """)
        nav_layout = QVBoxLayout(self.left_nav)
        nav_layout.setContentsMargins(12, 14, 12, 14)
        nav_layout.setSpacing(10)

        nav_brand_card = QFrame()
        nav_brand_card.setObjectName("NavBrandCard")
        nav_brand_card.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        nav_brand_card.setMouseTracking(True)
        nav_brand_card.setStyleSheet("""
            QFrame#NavBrandCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1b212b,
                    stop:0.45 #151b23,
                    stop:1 #11161d
                );
                border: 1px solid #29313a;
                border-radius: 12px;
            }
            QFrame#NavBrandCard:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #202a37,
                    stop:0.45 #182330,
                    stop:1 #121c26
                );
                border: 1px solid #3d5166;
            }
        """)
        nav_brand_shadow = QGraphicsDropShadowEffect(nav_brand_card)
        nav_brand_shadow.setBlurRadius(20)
        nav_brand_shadow.setOffset(0, 6)
        nav_brand_shadow.setColor(QColor(0, 0, 0, 110))
        nav_brand_card.setGraphicsEffect(nav_brand_shadow)
        nav_brand_layout = QVBoxLayout(nav_brand_card)
        nav_brand_layout.setContentsMargins(12, 12, 12, 10)
        nav_brand_layout.setSpacing(4)

        nav_brand_title = QLabel("Di88 Control")
        nav_brand_title.setStyleSheet("""
            QLabel {
                color: #f4f7fb;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 0px;
                background: transparent;
                border: none;
            }
        """)

        nav_brand_title_shadow = QGraphicsDropShadowEffect(nav_brand_title)
        nav_brand_title_shadow.setBlurRadius(18)
        nav_brand_title_shadow.setOffset(0, 2)
        nav_brand_title_shadow.setColor(QColor(0, 0, 0, 150))
        nav_brand_title.setGraphicsEffect(nav_brand_title_shadow)

        nav_brand_subtitle = QLabel("Macro & Aim")
        nav_brand_subtitle.setStyleSheet("""
            QLabel {
                color: #78dfff;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
        """)

        nav_brand_line = QFrame()
        nav_brand_line.setFixedHeight(2)
        nav_brand_line.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #00d8ff,
                stop:1 #2f4dff
            );
            border: none;
            border-radius: 1px;
        """)

        nav_brand_layout.addWidget(nav_brand_title)
        nav_brand_layout.addWidget(nav_brand_subtitle)
        nav_brand_layout.addSpacing(2)
        nav_brand_layout.addWidget(nav_brand_line)
        nav_layout.addWidget(nav_brand_card)
        nav_layout.addSpacing(8)

        self.btn_nav_home = self.build_nav_button("HOME", "home")
        self.btn_nav_macro = self.build_nav_button("MACRO", "macro")
        self.btn_nav_aim = self.build_nav_button("AIM BOT", "aim")
        self._nav_buttons = {
            "home": self.btn_nav_home,
            "macro": self.btn_nav_macro,
            "aim": self.btn_nav_aim,
        }
        nav_layout.addWidget(self.btn_nav_home)
        nav_layout.addWidget(self.btn_nav_macro)
        nav_layout.addWidget(self.btn_nav_aim)
        nav_layout.addStretch(1)

        nav_version = QLabel("v2.0 DI88")
        nav_version.setStyleSheet("""
            QLabel {
                color: #6e6e6e;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
        """)
        nav_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(nav_version)

        content_shell.addWidget(self.left_nav, 0)

        page_area = QWidget()
        page_area.setObjectName("MainPageArea")
        page_area.setStyleSheet("""
            QWidget#MainPageArea {
                background: #1b1b1b;
                border: none;
                border-radius: 14px;
            }
        """)
        page_area_layout = QVBoxLayout(page_area)
        page_area_layout.setContentsMargins(0, 0, 0, 0)
        page_area_layout.setSpacing(10)

        self.page_banner = QFrame()
        self.page_banner.setObjectName("MainPageBanner")
        self.page_banner.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.page_banner.setStyleSheet("""
            QFrame#MainPageBanner {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #0d1e33,
                    stop: 1 #112944
                );
                border: 1px solid #2f3942;
                border-radius: 14px;
            }
        """)
        page_banner_layout = QHBoxLayout(self.page_banner)
        page_banner_layout.setContentsMargins(20, 16, 20, 16)
        page_banner_layout.setSpacing(14)

        banner_text_wrap = QWidget()
        banner_text_wrap.setStyleSheet("background: transparent; border: none;")
        banner_text_layout = QVBoxLayout(banner_text_wrap)
        banner_text_layout.setContentsMargins(0, 0, 0, 0)
        banner_text_layout.setSpacing(3)
        self.page_banner_eyebrow = QLabel("DI88 CONTROL")
        self.page_banner_eyebrow.setStyleSheet("""
            QLabel {
                color: #77dfff;
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
        """)
        self.page_banner_title = QLabel("TRUNG TÂM ĐIỀU KHIỂN")
        self.page_banner_title.setStyleSheet("color: #f3f6fb; font-size: 17px; font-weight: 900; letter-spacing: 1px; background: transparent; border: none;")
        self.page_banner_subtitle = QLabel("Macro & Aim By Di88")
        self.page_banner_subtitle.setStyleSheet("color: #a8ccef; font-size: 11px; font-weight: 700; letter-spacing: 0px; background: transparent; border: none;")
        banner_text_layout.addWidget(self.page_banner_eyebrow)
        banner_text_layout.addWidget(self.page_banner_title)
        banner_text_layout.addWidget(self.page_banner_subtitle)

        self.page_banner_badge = QLabel("TỔNG HỢP")
        self.page_banner_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_banner_badge.setMinimumWidth(122)
        self.page_banner_badge.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        page_banner_layout.addWidget(banner_text_wrap, 1)
        page_banner_layout.addWidget(self.page_banner_badge, 0, Qt.AlignmentFlag.AlignVCenter)

        page_area_layout.addWidget(self.page_banner)

        macro_column = QWidget()
        body_layout = QVBoxLayout(macro_column)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(2)

        panel_style = """
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        """

        self._macro_box_style = """
            QGroupBox {
                background-color: #1b1b1b;
                border: 1px solid #333;
                border-radius: 10px;
                margin-top: 0;
            }
            QGroupBox::indicator {
                width: 0;
                height: 0;
                border: none;
                background: transparent;
            }
        """

        self.panel_detection = MacroTitledBox("\u0054\u0068\u00f4\u006e\u0067\u0020\u0054\u0069\u006e\u0020\u0053\u00fa\u006e\u0067", "DetectionPanel")
        detection_layout = self.panel_detection.content_layout()
        detection_layout.setContentsMargins(10, 16, 10, 8)
        detection_layout.setSpacing(8)
        self.header_detection = None

        detection_row = QHBoxLayout()
        detection_row.setContentsMargins(0, 0, 0, 0)
        detection_row.setSpacing(10)

        self.panel_g1 = QFrame()
        self.panel_g1.setObjectName("P1")
        self.panel_g1.setStyleSheet(
            "QFrame#P1 { "
            "background: transparent; "
            "border: 1px solid rgba(255, 255, 255, 0.04); "
            "border-radius: 8px; }"
        )
        l_g1 = QVBoxLayout(self.panel_g1)
        l_g1.setContentsMargins(8, 6, 8, 7)
        l_g1.setSpacing(4)
        g1_title_row = QHBoxLayout()
        g1_title_row.setContentsMargins(0, 0, 0, 0)
        g1_title_row.setSpacing(4)
        self.lbl_g1_title = QLabel("S\u00fang 1")
        self.lbl_g1_title.setObjectName("Gun1Title")
        self.lbl_g1_title.setStyleSheet(
            "color: #f08c8c; font-size: 12px; font-weight: 700; "
            "background: transparent; border: none; letter-spacing: 0.3px;"
        )
        g1_title_dot = QFrame()
        g1_title_dot.setFixedSize(5, 5)
        g1_title_dot.setStyleSheet("background: rgba(240, 140, 140, 0.8); border: none; border-radius: 2px;")
        g1_title_row.addWidget(g1_title_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        g1_title_row.addWidget(self.lbl_g1_title)
        g1_title_row.addStretch(1)
        l_g1.addLayout(g1_title_row)
        g1_content_row = QHBoxLayout()
        g1_content_row.setContentsMargins(0, 0, 0, 0)
        g1_content_row.setSpacing(8)
        self.g1_accent_line = QFrame()
        self.g1_accent_line.setFixedWidth(1)
        self.g1_accent_line.setStyleSheet("background-color: rgba(240, 140, 140, 0.38); border: none; border-radius: 1px;")
        g1_content_row.addWidget(self.g1_accent_line)
        self.grid_g1 = QGridLayout()
        self.grid_g1.setContentsMargins(0, 1, 0, 0)
        self.grid_g1.setVerticalSpacing(4)
        self.grid_g1.setHorizontalSpacing(14)
        self.grid_g1.setColumnMinimumWidth(0, 54)
        self.grid_g1.setColumnStretch(1, 1)
        self.lbl_g1_name = create_data_row(self.grid_g1, 0, "Name")
        self.lbl_g1_scope = create_data_row(self.grid_g1, 1, "Scope")
        self.lbl_g1_grip = create_data_row(self.grid_g1, 2, "Grip")
        self.lbl_g1_muzzle = create_data_row(self.grid_g1, 3, "Muzzle")
        g1_content_row.addLayout(self.grid_g1, 1)
        l_g1.addLayout(g1_content_row)
        detection_row.addWidget(self.panel_g1, stretch=1)

        self.panel_g2 = QFrame()
        self.panel_g2.setObjectName("P2")
        self.panel_g2.setStyleSheet(
            "QFrame#P2 { "
            "background: transparent; "
            "border: 1px solid rgba(255, 255, 255, 0.04); "
            "border-radius: 8px; }"
        )
        l_g2 = QVBoxLayout(self.panel_g2)
        l_g2.setContentsMargins(8, 6, 8, 7)
        l_g2.setSpacing(4)
        g2_title_row = QHBoxLayout()
        g2_title_row.setContentsMargins(0, 0, 0, 0)
        g2_title_row.setSpacing(4)
        self.lbl_g2_title = QLabel("S\u00fang 2")
        self.lbl_g2_title.setObjectName("Gun2Title")
        self.lbl_g2_title.setStyleSheet(
            "color: #86d99a; font-size: 12px; font-weight: 700; "
            "background: transparent; border: none; letter-spacing: 0.3px;"
        )
        g2_title_dot = QFrame()
        g2_title_dot.setFixedSize(5, 5)
        g2_title_dot.setStyleSheet("background: rgba(134, 217, 154, 0.8); border: none; border-radius: 2px;")
        g2_title_row.addWidget(g2_title_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        g2_title_row.addWidget(self.lbl_g2_title)
        g2_title_row.addStretch(1)
        l_g2.addLayout(g2_title_row)
        g2_content_row = QHBoxLayout()
        g2_content_row.setContentsMargins(0, 0, 0, 0)
        g2_content_row.setSpacing(8)
        self.g2_accent_line = QFrame()
        self.g2_accent_line.setFixedWidth(1)
        self.g2_accent_line.setStyleSheet("background-color: rgba(134, 217, 154, 0.38); border: none; border-radius: 1px;")
        g2_content_row.addWidget(self.g2_accent_line)
        self.grid_g2 = QGridLayout()
        self.grid_g2.setContentsMargins(0, 1, 0, 0)
        self.grid_g2.setVerticalSpacing(4)
        self.grid_g2.setHorizontalSpacing(14)
        self.grid_g2.setColumnMinimumWidth(0, 54)
        self.grid_g2.setColumnStretch(1, 1)
        self.lbl_g2_name = create_data_row(self.grid_g2, 0, "Name")
        self.lbl_g2_scope = create_data_row(self.grid_g2, 1, "Scope")
        self.lbl_g2_grip = create_data_row(self.grid_g2, 2, "Grip")
        self.lbl_g2_muzzle = create_data_row(self.grid_g2, 3, "Muzzle")
        g2_content_row.addLayout(self.grid_g2, 1)
        l_g2.addLayout(g2_content_row)
        detection_row.addWidget(self.panel_g2, stretch=1)

        detection_layout.addLayout(detection_row)

        self.group_settings = MacroTitledBox("Hướng Dẫn Sử Dụng", "SettingsBox")
        self.group_settings.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        settings_layout = self.group_settings.content_layout()
        settings_layout.setSpacing(6)
        self.header_settings = None
        self.bind_box = MacroTitledBox("Bind Nút", "BindBox")
        self.bind_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bind_layout = self.bind_box.content_layout()
        bind_layout.setSpacing(6)
        self.header_bind = None
        self.toggle_box = MacroTitledBox("Bật/Tắt", "ToggleBox")
        self.toggle_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        toggle_layout = self.toggle_box.content_layout()
        toggle_layout.setSpacing(6)
        self.header_toggle = None

        def add_settings_grid_row(target_layout, label_text: str, value_widget: QWidget, side_widget: QWidget | None = None):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(label_text)
            label.setFixedWidth(122)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "setting-label")
            self.style_setting_label(label)

            value_widget.setSizePolicy(value_widget.sizePolicy().horizontalPolicy(), value_widget.sizePolicy().verticalPolicy())
            if hasattr(value_widget, "setFixedHeight"):
                value_widget.setFixedHeight(24)

            row.addWidget(label)
            row.addWidget(value_widget, stretch=1)

            if side_widget is not None:
                row.addWidget(side_widget)

            target_layout.addLayout(row)
            return label

        def add_toggle_row(target_layout, label_text: str, switch_widget: QWidget):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(label_text)
            label.setFixedWidth(122)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "setting-label")
            self.style_setting_label(label)

            switch_wrap = QWidget()
            switch_wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            switch_layout = QHBoxLayout(switch_wrap)
            switch_layout.setContentsMargins(0, 0, 0, 0)
            switch_layout.setSpacing(0)
            switch_layout.addStretch()
            switch_layout.addWidget(switch_widget)

            row.addWidget(label)
            row.addWidget(switch_wrap, stretch=1)
            target_layout.addLayout(row)
            return label

        self.btn_fastloot_key = QPushButton("caps_lock")
        self.btn_fastloot_key.setProperty("role", "setting-btn")
        self.btn_fastloot_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_key.setFixedHeight(24)
        self.style_setting_button(self.btn_fastloot_key)
        self.btn_fastloot_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_fastloot_key, "fast_loot_key"))
        self.btn_fastloot_toggle = QPushButton("OFF")
        self.btn_fastloot_toggle.setObjectName("FastLootToggleBtn")
        self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.btn_fastloot_toggle.clicked.connect(self.toggle_fast_loot)
        self.btn_fastloot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_toggle.setFixedSize(50, 24)
        self.btn_fastloot_toggle.hide()
        self.lbl_fastloot_row = add_settings_grid_row(bind_layout, "Nhặt Đồ Nhanh", self.btn_fastloot_key)
        self.btn_fastloot_switch = MobileSwitch(False)
        self.btn_fastloot_switch.toggled.connect(self.toggle_fast_loot)
        self.lbl_fastloot_toggle_row = add_toggle_row(toggle_layout, "Nhặt Đồ Nhanh", self.btn_fastloot_switch)
        self.lbl_fastloot_toggle_row.setFixedWidth(122)
        self.lbl_fastloot_toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_slide_hint = QPushButton("Shift + W + ( A or D ) + C")
        self.btn_slide_hint.setProperty("role", "setting-btn")
        self.btn_slide_hint.setEnabled(False)
        self.btn_slide_hint.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_slide_hint)
        self.lbl_slide_row = add_settings_grid_row(settings_layout, "Lướt Ngồi", self.btn_slide_hint)

        self.btn_slide_toggle = QPushButton("ON")
        self.btn_slide_toggle.setObjectName("SlideToggleBtn")
        self.btn_slide_toggle.setProperty("state", "ON")
        self.btn_slide_toggle.clicked.connect(self.toggle_slide_trick)
        self.btn_slide_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_slide_toggle.setFixedSize(50, 24)
        self.btn_slide_toggle.hide()
        self.btn_slide_switch = MobileSwitch(True)
        self.btn_slide_switch.toggled.connect(self.toggle_slide_trick)
        self.lbl_slide_toggle_row = add_toggle_row(toggle_layout, "Lướt Ngồi", self.btn_slide_switch)
        self.lbl_slide_toggle_row.setFixedWidth(122)
        self.lbl_slide_toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_slot1_hint = QPushButton("1")
        self.btn_slot1_hint.setProperty("role", "setting-btn")
        self.btn_slot1_hint.setEnabled(False)
        self.btn_slot1_hint.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_slot1_hint)
        self.lbl_slot1_row = add_settings_grid_row(settings_layout, "Phím Súng 1", self.btn_slot1_hint)

        self.btn_slot2_hint = QPushButton("2")
        self.btn_slot2_hint.setProperty("role", "setting-btn")
        self.btn_slot2_hint.setEnabled(False)
        self.btn_slot2_hint.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_slot2_hint)
        self.lbl_slot2_row = add_settings_grid_row(settings_layout, "Phím Súng 2", self.btn_slot2_hint)

        self.btn_stopkeys = QPushButton("X, G, 5")
        self.btn_stopkeys.setProperty("role", "setting-btn")
        self.btn_stopkeys.setEnabled(False)
        self.btn_stopkeys.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_stopkeys)
        self.lbl_stopkeys_row = add_settings_grid_row(settings_layout, "Phím Dừng Khẩn", self.btn_stopkeys)

        self.btn_adsmode = QPushButton("HOLD")
        self.btn_adsmode.setProperty("role", "setting-btn")
        self.btn_adsmode.setEnabled(False)
        self.btn_adsmode.setCursor(Qt.CursorShape.ArrowCursor)
        self.style_setting_button(self.btn_adsmode)
        self.lbl_adsmode_row = add_settings_grid_row(settings_layout, "Kiểu ADS", self.btn_adsmode)

        self.btn_guitoggle = QPushButton("F1")
        self.btn_guitoggle.setProperty("role", "setting-btn")
        self.btn_guitoggle.setEnabled(True)
        self.btn_guitoggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_setting_button(self.btn_guitoggle)
        self.btn_guitoggle.clicked.connect(lambda: self.start_keybind_listening(self.btn_guitoggle, "gui_toggle"))
        self.lbl_guitoggle_row = add_settings_grid_row(bind_layout, "Ẩn/Hiện APP", self.btn_guitoggle)

        self.btn_overlay_key = QPushButton("delete")
        self.btn_overlay_key.setProperty("role", "setting-btn")
        self.btn_overlay_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_key.setFixedHeight(24)
        self.style_setting_button(self.btn_overlay_key)
        self.btn_overlay_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_overlay_key, "overlay_key"))
        self.btn_overlay_toggle = QPushButton("OFF")
        self.btn_overlay_toggle.setObjectName("OverlayToggleBtn")
        self.btn_overlay_toggle.setProperty("state", "OFF")
        self.btn_overlay_toggle.setCheckable(False)
        self.btn_overlay_toggle.clicked.connect(self.toggle_overlay_visibility)
        self.btn_overlay_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_toggle.setFixedSize(50, 24)
        self.btn_overlay_toggle.hide()
        self.lbl_overlay_row = add_settings_grid_row(bind_layout, "Overlay", self.btn_overlay_key)

        self.capture_box = MacroTitledBox("\u0043\u0068\u1ebf\u0020\u0110\u1ed9\u0020\u0043\u0068\u1ee5\u0070", "CaptureBox")
        self.capture_box.setMinimumWidth(0)
        self.capture_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.capture_box.setFixedHeight(82)
        capture_layout = self.capture_box.content_layout()
        capture_layout.setSpacing(6)
        self.header_capture = None

        row_capture = QHBoxLayout()
        row_capture.setContentsMargins(0, 0, 0, 0)
        row_capture.setSpacing(3)
        self.lbl_capture_mode_auto = QLabel("DXCAM")
        self.lbl_capture_mode_auto.hide()
        self.btn_capture_native = QPushButton("DXGI")
        self.btn_capture_native.setFixedHeight(22)
        self.btn_capture_native.setMinimumWidth(72)
        self.btn_capture_native.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_capture_native.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_native.clicked.connect(lambda: self.set_capture_mode("DXGI"))
        self.btn_capture_dxcam = QPushButton("DXCAM")
        self.btn_capture_dxcam.setFixedHeight(22)
        self.btn_capture_dxcam.setMinimumWidth(72)
        self.btn_capture_dxcam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_capture_dxcam.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_dxcam.clicked.connect(lambda: self.set_capture_mode("DXCAM"))
        self.btn_capture_mss = QPushButton("MSS")
        self.btn_capture_mss.setFixedHeight(22)
        self.btn_capture_mss.setMinimumWidth(72)
        self.btn_capture_mss.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_capture_mss.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture_mss.clicked.connect(lambda: self.set_capture_mode("MSS"))
        self.btn_capture_native.hide()
        row_capture.addWidget(self.btn_capture_native, 1)
        row_capture.addWidget(self.btn_capture_dxcam, 1)
        row_capture.addWidget(self.btn_capture_mss, 1)
        capture_layout.addLayout(row_capture)

        self.scope_box = MacroTitledBox("\u0043\u01b0\u1edd\u006e\u0067\u0020\u0110\u1ed9\u0020\u0053\u0063\u006f\u0070\u0065", "ScopeIntensityBox")
        self.scope_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        scope_layout = self.scope_box.content_layout()
        scope_layout.setSpacing(6)
        self.header_scope = None

        self.scope_order = [
            ("normal", "Redot/Holo"),
            ("x2", "Scope X2"),
            ("x3", "Scope X3"),
            ("x4", "Scope X4"),
            ("x6", "Scope X6"),
        ]
        self.scope_sliders = {}
        self.scope_value_labels = {}

        for scope_key, scope_label in self.scope_order:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(8)

            label = QLabel(scope_label)
            label.setFixedWidth(82)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setProperty("role", "setting-label")
            self.style_setting_label(label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(50, 150)
            slider.setSingleStep(1)
            slider.setPageStep(5)
            slider.setValue(100)
            slider.setFixedHeight(20)
            self.style_scope_slider(slider)

            value_label = QLabel("100%")
            value_label.setFixedWidth(48)
            value_label.setFixedHeight(24)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.style_scope_value_label(value_label)

            slider.valueChanged.connect(lambda value, key=scope_key: self.update_scope_intensity_label(key, value))

            self.scope_sliders[scope_key] = slider
            self.scope_value_labels[scope_key] = value_label

            row.addWidget(label)
            row.addWidget(slider, stretch=1)
            row.addWidget(value_label)
            scope_layout.addLayout(row)

        self.crosshair_box = MacroTitledBox("\u0054\u00e2\u006d\u0020\u004e\u0067\u1eaf\u006d", "CrosshairBox")
        self.crosshair_box.setMinimumWidth(0)
        self.crosshair_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.crosshair_box.setFixedHeight(82)
        cross_layout = self.crosshair_box.content_layout()
        cross_layout.setContentsMargins(10, 16, 10, 8)
        cross_layout.setSpacing(6)
        self.header_crosshair = None

        cross_grid = QGridLayout()
        cross_grid.setContentsMargins(0, 0, 0, 0)
        cross_grid.setHorizontalSpacing(3)
        cross_grid.setVerticalSpacing(0)
        cross_grid.setColumnStretch(0, 1)
        cross_grid.setColumnStretch(1, 1)

        self.lbl_cross_style = QLabel("")
        self.lbl_cross_style.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cross_style.setStyleSheet("color: #c6c6c6; font-size: 8px; font-weight: bold;")
        self.lbl_cross_style.hide()

        self.lbl_cross_color = QLabel("")
        self.lbl_cross_color.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_cross_color.setStyleSheet("color: #c6c6c6; font-size: 8px; font-weight: bold;")
        self.lbl_cross_color.hide()
        self.btn_cross_toggle = QPushButton("ON")
        self.btn_cross_toggle.setObjectName("CrosshairToggleBtn")
        self.btn_cross_toggle.setProperty("checked", "true")
        self.btn_cross_toggle.setCheckable(True)
        self.btn_cross_toggle.setChecked(True)
        self.btn_cross_toggle.setFixedSize(42, 22)
        self.btn_cross_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_toggle.clicked.connect(self.toggle_crosshair)
        self.btn_cross_toggle.hide()

        self.crosshair_style_options = [
            ("Dot", "dot"),
            ("Plus", "plus"),
            ("X", "x"),
            ("Circle", "circle"),
            ("Hollow Circle", "hollow_circle"),
            ("Tactical", "tactical"),
            ("Small Cross", "small_cross"),
            ("Thick Cross", "thick_cross"),
            ("Sniper", "sniper"),
            ("Diamond", "diamond"),
            ("Triangle", "triangle"),
            ("Minimal", "minimal"),
        ]
        self.combo_style = CenteredComboBox(center_mode="full")
        self.combo_style.setObjectName("CrosshairStyleCombo")
        self.combo_style.setItemDelegate(IconOnlyComboDelegate(self.combo_style))
        self.combo_style.setIconSize(QSize(36, 18))
        self.combo_style.view().setStyleSheet("""
            QListView {
                background: #1b1b1b;
                border: 1px solid #333333;
                outline: none;
                padding: 4px;
            }
            QListView::item {
                border: none;
                margin: 1px 4px;
            }
            QListView::item:selected {
                background: #232323;
            }
        """)
        self.combo_style.addItems([display for display, _ in self.crosshair_style_options])
        self.combo_style.setCurrentText("X")
        for i in range(self.combo_style.count()):
            _, internal_style = self.crosshair_style_options[i]
            self.combo_style.setItemIcon(i, self.build_crosshair_preview_icon(internal_style))
            self.combo_style.setItemData(i, int(Qt.AlignmentFlag.AlignCenter), Qt.ItemDataRole.TextAlignmentRole)
        self.combo_style.setFixedHeight(22)
        self.combo_style.setMaximumWidth(16777215)
        self.combo_style.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.style_crosshair_combo(self.combo_style)
        self.combo_style.currentIndexChanged.connect(self.change_crosshair_style)

        self.combo_color = CenteredComboBox(center_mode="full")
        self.combo_color.setObjectName("CrosshairColorCombo")
        self.combo_color.setItemDelegate(IconOnlyComboDelegate(self.combo_color))
        self.combo_color.setIconSize(QSize(22, 22))
        self.combo_color.view().setStyleSheet("""
            QListView {
                background: #1b1b1b;
                border: 1px solid #333333;
                outline: none;
                padding: 4px;
            }
            QListView::item {
                border: none;
                margin: 1px 4px;
            }
            QListView::item:selected {
                background: #232323;
            }
        """)
        self.combo_color.addItems([
            "Đỏ", "Đỏ Cam", "Cam", "Vàng",
            "Xanh Lá", "Xanh Ngọc", "Xanh Dương",
            "Tím", "Tím Hồng", "Hồng",
            "Trắng", "Bạc"
        ])
        self.crosshair_color_swatches = [
            QColor(255, 30, 30),
            QColor(255, 69, 0),
            QColor(255, 140, 0),
            QColor(255, 215, 0),
            QColor(0, 255, 0),
            QColor(0, 255, 255),
            QColor(0, 180, 255),
            QColor(180, 0, 255),
            QColor(255, 60, 255),
            QColor(255, 105, 180),
            QColor(255, 255, 255),
            QColor(192, 192, 192),
        ]
        self.combo_color.setCurrentText("Đỏ")
        for i in range(self.combo_color.count()):
            self.combo_color.setItemIcon(i, self.build_color_preview_icon(self.crosshair_color_swatches[i]))
            self.combo_color.setItemData(i, int(Qt.AlignmentFlag.AlignCenter), Qt.ItemDataRole.TextAlignmentRole)
        self.combo_color.setFixedHeight(22)
        self.combo_color.setMaximumWidth(16777215)
        self.combo_color.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.style_crosshair_combo(self.combo_color)
        self.combo_color.currentIndexChanged.connect(self.change_crosshair_color)

        self.cross_toggle_buttons = QWidget()
        self.cross_toggle_buttons.hide()

        self.btn_cross_on = QPushButton("BẬT")
        self.btn_cross_on.hide()
        self.btn_cross_on.clicked.connect(lambda: self.toggle_crosshair(True))

        self.btn_cross_off = QPushButton("TẮT")
        self.btn_cross_off.hide()
        self.btn_cross_off.clicked.connect(lambda: self.toggle_crosshair(False))

        self.btn_cross_bind = QPushButton("HOME")
        self.btn_cross_bind.setObjectName("CrosshairBindBtn")
        self.btn_cross_bind.setProperty("role", "setting-btn")
        self.btn_cross_bind.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_bind.setFixedHeight(22)
        self.btn_cross_bind.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.style_setting_button(self.btn_cross_bind)
        self.btn_cross_bind.clicked.connect(lambda: self.start_keybind_listening(self.btn_cross_bind, "crosshair_toggle_key"))
        self.btn_cross_bind.hide()
        cross_grid.addWidget(self.combo_style, 0, 0)
        cross_grid.addWidget(self.combo_color, 0, 1)
        cross_layout.addLayout(cross_grid)
        self.btn_crosshair_switch = MobileSwitch(True)
        self.btn_crosshair_switch.toggled.connect(self.toggle_crosshair)
        self.lbl_cross_toggle_row = add_toggle_row(toggle_layout, "Tâm Ngắm", self.btn_crosshair_switch)
        self.lbl_cross_toggle_row.setFixedWidth(122)
        self.lbl_cross_toggle_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.footer = QFrame()
        self.footer.setObjectName("StatusPanel")
        f_layout = QHBoxLayout(self.footer)
        f_layout.setSpacing(8)
        f_layout.setContentsMargins(10, 10, 10, 10)

        self.btn_macro = QPushButton("MACRO : OFF")
        self.btn_macro.setObjectName("MacroStatusBtn")
        self.btn_macro.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.btn_macro.setFixedHeight(32)
        self.update_macro_style(False)

        self.lbl_stance = QLabel("TƯ THẾ : ĐỨNG")
        self.lbl_stance.setObjectName("StatusValueLabel")
        self.lbl_stance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stance.setFixedHeight(32)
        self.update_stance_status_style("TƯ THẾ : ĐỨNG")

        self.lbl_ads_status = QLabel("ADS : HOLD")
        self.lbl_ads_status.setObjectName("StatusValueLabel")
        self.lbl_ads_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ads_status.setFixedHeight(32)
        self.update_ads_status_style("HOLD")

        f_layout.addWidget(self.btn_macro, stretch=1)
        f_layout.addWidget(self.lbl_stance, stretch=1)
        f_layout.addWidget(self.lbl_ads_status, stretch=1)

        macro_columns = QHBoxLayout()
        macro_columns.setContentsMargins(0, 0, 0, 0)
        macro_columns.setSpacing(2)

        macro_left_col = QVBoxLayout()
        macro_left_col.setContentsMargins(0, 0, 0, 0)
        macro_left_col.setSpacing(5)
        macro_left_col.addWidget(self.capture_box)
        macro_left_col.addWidget(self.group_settings)
        macro_left_col.addWidget(self.toggle_box)

        macro_right_col = QVBoxLayout()
        macro_right_col.setContentsMargins(0, 0, 0, 0)
        macro_right_col.setSpacing(5)
        macro_right_col.addWidget(self.crosshair_box)
        macro_right_col.addWidget(self.bind_box)
        macro_right_col.addWidget(self.scope_box)

        macro_columns.addLayout(macro_left_col, 1)
        macro_columns.addLayout(macro_right_col, 1)
        macro_columns.setAlignment(macro_left_col, Qt.AlignmentFlag.AlignTop)
        macro_columns.setAlignment(macro_right_col, Qt.AlignmentFlag.AlignTop)

        body_layout.addWidget(self.footer)
        body_layout.addWidget(self.panel_detection)
        body_layout.addLayout(macro_columns)
        QTimer.singleShot(0, self.sync_macro_box_heights)
        QTimer.singleShot(0, self.position_all_macro_titles)

        action_box = QFrame()
        action_box.setObjectName("ActionBox")
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(10, 8, 10, 10)
        action_layout.setSpacing(8)
        row_btns = QHBoxLayout()
        row_btns.setContentsMargins(0, 0, 0, 0)
        row_btns.setSpacing(8)
        btn_default = QPushButton("Cài Đặt Gốc")
        btn_default.setObjectName("DefaultBtn")
        btn_default.setFixedHeight(32)
        btn_default.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_action_button(btn_default, primary=False)
        btn_default.clicked.connect(self.reset_to_defaults)
        btn_save = QPushButton("Lưu Cài Đặt")
        btn_save.setObjectName("SaveBtn")
        btn_save.setFixedHeight(32)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.style_action_button(btn_save, primary=True)
        btn_save.clicked.connect(self.save_config)
        row_btns.addWidget(btn_default)
        row_btns.addWidget(btn_save)
        action_layout.addLayout(row_btns)
        action_box.hide()
        body_layout.addWidget(action_box)
        body_layout.addStretch()

        self.aim_workspace = AimPanelBuilder(self, SectionHeader).build()
        self.home_page = HomePanelBuilder(self).build()
        self.home_page.setStyleSheet("background: #1b1b1b; border: none;")

        self.macro_page = QWidget()
        self.macro_page.setStyleSheet("background: #1b1b1b; border: none;")
        macro_page_layout = QVBoxLayout(self.macro_page)
        macro_page_layout.setContentsMargins(0, 0, 0, 0)
        macro_page_layout.setSpacing(0)
        macro_page_layout.addWidget(macro_column)

        self.aim_page = QWidget()
        self.aim_page.setStyleSheet("background: #1b1b1b; border: none;")
        aim_page_layout = QVBoxLayout(self.aim_page)
        aim_page_layout.setContentsMargins(0, 0, 0, 0)
        aim_page_layout.setSpacing(0)
        aim_page_layout.addWidget(self.aim_workspace)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("MainPageStack")
        self.page_stack.setStyleSheet("""
            QStackedWidget#MainPageStack {
                background: #1b1b1b;
                border: none;
            }
        """)
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.macro_page)
        self.page_stack.addWidget(self.aim_page)

        self._page_widgets = {
            "home": self.home_page,
            "macro": self.macro_page,
            "aim": self.aim_page,
        }
        self._current_main_page = "home"

        page_area_layout.addWidget(self.page_stack, 1)
        content_shell.addWidget(page_area, 1)

        main_layout.addWidget(content_widget)

        self.bottom_action_bar = QFrame()
        self.bottom_action_bar.setObjectName("BottomActionBar")
        self.bottom_action_bar.setStyleSheet("""
            QFrame#BottomActionBar {
                background: #272a2d;
                border-top: 1px solid #3c4044;
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
            }
        """)
        bottom_action_layout = QHBoxLayout(self.bottom_action_bar)
        bottom_action_layout.setContentsMargins(5, 10, 5, 10)
        bottom_action_layout.setSpacing(10)

        self.left_action_wrap = QWidget()
        self.left_action_wrap.setStyleSheet("background: transparent; border: none;")
        left_action_layout = QHBoxLayout(self.left_action_wrap)
        left_action_layout.setContentsMargins(0, 0, 0, 0)
        left_action_layout.setSpacing(0)
        self.btn_default_main = QPushButton("Cài Đặt Gốc")
        self.btn_default_main.setObjectName("DefaultBtn")
        self.btn_default_main.setText("Cài Đặt Gốc")
        self.btn_default_main.setFixedHeight(36)
        self.btn_default_main.setMinimumWidth(180)
        self.btn_default_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_default_main.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.style_action_button(self.btn_default_main, primary=False)
        self.btn_default_main.clicked.connect(self.reset_to_defaults)
        left_action_layout.addWidget(self.btn_default_main)
        left_action_layout.addStretch(1)

        self.center_action_wrap = QWidget()
        self.center_action_wrap.setStyleSheet("background: transparent; border: none;")
        center_action_layout = QHBoxLayout(self.center_action_wrap)
        center_action_layout.setContentsMargins(0, 0, 0, 0)
        center_action_layout.setSpacing(0)
        self.bottom_action_status = QLabel("")
        self.bottom_action_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_action_status.setMinimumWidth(220)
        self.bottom_action_status.hide()
        center_action_layout.addStretch(1)
        center_action_layout.addWidget(self.bottom_action_status)
        center_action_layout.addStretch(1)

        self.right_action_wrap = QWidget()
        self.right_action_wrap.setStyleSheet("background: transparent; border: none;")
        right_action_layout = QHBoxLayout(self.right_action_wrap)
        right_action_layout.setContentsMargins(0, 0, 0, 0)
        right_action_layout.setSpacing(0)
        self.btn_save_main = QPushButton("Lưu Cài Đặt")
        self.btn_save_main.setObjectName("SaveBtn")
        self.btn_save_main.setText("Lưu Cài Đặt")
        self.btn_save_main.setFixedHeight(36)
        self.btn_save_main.setMinimumWidth(180)
        self.btn_save_main.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_main.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.style_action_button(self.btn_save_main, primary=True)
        self.btn_save_main.clicked.connect(self.save_config)
        right_action_layout.addStretch(1)
        right_action_layout.addWidget(self.btn_save_main)

        bottom_action_layout.addWidget(self.left_action_wrap, 1)
        bottom_action_layout.addWidget(self.center_action_wrap, 1)
        bottom_action_layout.addWidget(self.right_action_wrap, 1)

        main_layout.addWidget(self.bottom_action_bar)
        self.setup_hover_hints()
        self.load_config()
        self.load_crosshair_settings()
        self.update_nav_button_styles()
        self.update_home_snapshot()
        self.update_main_page_banner()
        self.set_main_page("home")
        QTimer.singleShot(0, self.sync_crosshair_columns)
        QTimer.singleShot(0, self.sync_window_width_to_frame)
        QTimer.singleShot(0, self.sync_window_height_to_content)

    def setup_ui(self):
        # Container chính (Bo tròn, Gradient nền)
        self.container = QFrame(self)
        self.container.setObjectName("MainContainer")
        self.container.setGeometry(5, 5, 640, 490) # Adjusted for DropShadow
        
        # Đã làm sạch chú thích lỗi mã hóa.
        # Đã làm sạch chú thích lỗi mã hóa.
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(4) 
        # shadow.setOffset(0, 4)
        # self.container.setGraphicsEffect(shadow)

        
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TITLE BAR ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(30)
        header_layout = QHBoxLayout(self.title_bar)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        btn_min = QPushButton("-")
        btn_min.setObjectName("MinBtn")
        btn_min.setFixedSize(20, 20)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.clicked.connect(self.minimize_to_taskbar) 
        
        btn_close = QPushButton("X")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.handle_close_action)
        
        self.app_title_label = QLabel("Macro & Aim By Di88") 
        self.app_title_label.setObjectName("AppTitle")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(4)
        glow.setColor(QColor(0, 0, 0, 200))  # Đã làm sạch chú thích lỗi mã hóa.
        glow.setOffset(1, 1) 
        self.app_title_label.setGraphicsEffect(glow)

        # Đã làm sạch chú thích lỗi mã hóa.
        self.app_logo = QLabel()
        icon_path = get_resource_path("di88vp.ico")
        logo_icon = QIcon(icon_path)
        self.app_logo.setPixmap(logo_icon.pixmap(22, 22))
        self.app_logo.setContentsMargins(0, 0, 5, 0)

        header_layout.addStretch()
        header_layout.addWidget(self.app_logo)
        header_layout.addWidget(self.app_title_label) 
        header_layout.addStretch()
        header_layout.addWidget(btn_min)
        header_layout.addSpacing(5)
        header_layout.addWidget(btn_close)
        
        # Đã làm sạch chú thích lỗi mã hóa.
        self.title_bar.mousePressEvent = self.mousePressEvent
        self.title_bar.mouseMoveEvent = self.mouseMoveEvent
        
        main_layout.addWidget(self.title_bar)
        
        # --- BODY V-LAYOUT (TOP/BOTTOM) ---
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(5, 5, 5, 5)
        body_layout.setSpacing(10)
        
        # --- 1. TOP UNIFIED BOX (GUNS + SETTINGS) ---
        top_box = QFrame()
        top_box.setObjectName("TopUnifiedBox")
        top_box.setStyleSheet('''
            QFrame#TopUnifiedBox {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        ''')
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(10)
        
        # >>> LEFT PART (GUNS)
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        # Đã làm sạch chú thích lỗi mã hóa.
        left_column.setMinimumWidth(280)
        
        # GUN 1
        self.panel_g1, l_g1 = create_panel("GUN 1", "#FF4444", "P1")
        self.grid_g1 = QGridLayout()
        self.grid_g1.setSpacing(6)
        self.lbl_g1_name = create_data_row(self.grid_g1, 0, "Name")
        self.lbl_g1_scope = create_data_row(self.grid_g1, 1, "Scope")
        self.lbl_g1_grip = create_data_row(self.grid_g1, 2, "Grip")
        self.lbl_g1_muzzle = create_data_row(self.grid_g1, 3, "Muzz")
        l_g1.addLayout(self.grid_g1)
        left_layout.addWidget(self.panel_g1, stretch=1)
        
        # GUN 2
        self.panel_g2, l_g2 = create_panel("GUN 2", "#44FF44", "P2")
        self.grid_g2 = QGridLayout()
        self.grid_g2.setSpacing(6)
        self.lbl_g2_name = create_data_row(self.grid_g2, 0, "Name")
        self.lbl_g2_scope = create_data_row(self.grid_g2, 1, "Scope")
        self.lbl_g2_grip = create_data_row(self.grid_g2, 2, "Grip")
        self.lbl_g2_muzzle = create_data_row(self.grid_g2, 3, "Muzz")
        l_g2.addLayout(self.grid_g2)
        left_layout.addWidget(self.panel_g2, stretch=1)
        
        top_layout.addWidget(left_column, stretch=1)
        
        # >>> VERTICAL SEPARATOR
        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setStyleSheet("background: #3a3a3a; border: none;")
        top_layout.addWidget(v_sep)
        
        # >>> RIGHT COLUMN (SETTINGS)
        self.group_settings = QWidget()
        self.group_settings.setObjectName("SettingsBox")
        
        settings_layout = QVBoxLayout(self.group_settings)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(10)
        
        lbl_settings_title = QLabel("CÀI ĐẶT CHUNG")
        lbl_settings_title.setStyleSheet("color: #ffffff; font-weight: bold; letter-spacing: 1px;")
        lbl_settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(lbl_settings_title)
        settings_layout.addSpacing(5)
        
        # Overlay
        row_overlay = QHBoxLayout()
        lbl_overlay = QLabel("Overlay")
        lbl_overlay.setFixedWidth(100)
        lbl_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_overlay.setProperty("class", "SettingLabel")
        self.btn_overlay_key = QPushButton("delete")
        self.btn_overlay_key.setProperty("class", "SettingBtn")
        self.btn_overlay_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_key.setFixedHeight(25)
        self.btn_overlay_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_overlay_key, "overlay_key"))
        
        self.btn_overlay_toggle = QPushButton("OFF")
        self.btn_overlay_toggle.setObjectName("OverlayToggleBtn")
        self.btn_overlay_toggle.setProperty("state", "OFF")
        self.btn_overlay_toggle.setCheckable(False)
        self.btn_overlay_toggle.clicked.connect(self.toggle_overlay_visibility)
        self.btn_overlay_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_toggle.setFixedSize(50, 28)
        row_overlay.addWidget(lbl_overlay)
        row_overlay.addWidget(self.btn_overlay_key)
        row_overlay.addSpacing(5)
        row_overlay.addWidget(self.btn_overlay_toggle)
        settings_layout.addLayout(row_overlay)

        # FastLoot
        row_fastloot = QHBoxLayout()
        lbl_fastloot = QLabel("Fast Loot")
        lbl_fastloot.setFixedWidth(100)
        lbl_fastloot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_fastloot.setProperty("class", "SettingLabel")
        self.btn_fastloot_key = QPushButton("caps_lock")
        self.btn_fastloot_key.setProperty("class", "SettingBtn")
        self.btn_fastloot_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_key.setFixedHeight(25)
        self.btn_fastloot_key.clicked.connect(lambda: self.start_keybind_listening(self.btn_fastloot_key, "fast_loot_key"))
        
        self.btn_fastloot_toggle = QPushButton("OFF")
        self.btn_fastloot_toggle.setObjectName("FastLootToggleBtn")
        self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.btn_fastloot_toggle.clicked.connect(self.toggle_fast_loot)
        self.btn_fastloot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_toggle.setFixedSize(50, 28)
        row_fastloot.addWidget(lbl_fastloot)
        row_fastloot.addWidget(self.btn_fastloot_key)
        row_fastloot.addSpacing(5)
        row_fastloot.addWidget(self.btn_fastloot_toggle)
        settings_layout.addLayout(row_fastloot)

        # StopKeys
        self.btn_stopkeys = add_setting_row(settings_layout, "STOPKEYS", "X, G, 5")
        self.btn_stopkeys.setEnabled(False)
        self.btn_stopkeys.setCursor(Qt.CursorShape.ArrowCursor)
        
        # ADS Mode
        self.btn_adsmode = add_setting_row(settings_layout, "ADS MODE", "HOLD")
        self.btn_adsmode.setEnabled(False)
        self.btn_adsmode.setCursor(Qt.CursorShape.ArrowCursor)

        # GUI Toggle
        self.btn_guitoggle = add_setting_row(settings_layout, "BẬT/TẮt GUI", "F1")
        self.btn_guitoggle.setEnabled(False)
        self.btn_guitoggle.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Capture Mode
        row_capture = QHBoxLayout()
        lbl_cap = QLabel("CAPTURE")
        lbl_cap.setFixedWidth(100)
        lbl_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cap.setProperty("class", "SettingLabel")
        
        self.btn_mode_wgc = QPushButton("DXCAM")
        self.btn_mode_wgc.setObjectName("ModeWgcBtn")
        self.btn_mode_wgc.setProperty("class", "CaptureBtn")
        self.btn_mode_wgc.setFixedSize(65, 25)
        self.btn_mode_wgc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_wgc.clicked.connect(lambda: self.set_capture_mode("DXCAM"))

        self.btn_mode_dxgi = QPushButton("MSS")
        self.btn_mode_dxgi.setObjectName("ModeDxgiBtn")
        self.btn_mode_dxgi.setProperty("class", "CaptureBtn")
        self.btn_mode_dxgi.setFixedSize(65, 25)
        self.btn_mode_dxgi.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_dxgi.clicked.connect(lambda: self.set_capture_mode("MSS"))

        row_capture.addWidget(lbl_cap)
        
        btns_container = QWidget()
        btns_layout = QHBoxLayout(btns_container)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(5)
        btns_layout.addStretch()
        btns_layout.addWidget(self.btn_mode_wgc)
        btns_layout.addWidget(self.btn_mode_dxgi)
        btns_layout.addStretch()
        
        row_capture.addWidget(btns_container)
        settings_layout.addLayout(row_capture)
        
        settings_layout.addSpacing(5)

        
        settings_layout.addStretch()
        top_layout.addWidget(self.group_settings, stretch=1)
        body_layout.addWidget(top_box)
        
        # --- 2. BOTTOM CARDS ROW ---
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(15)
        
        # Left Bottom Card: Tư thế / Macro
        self.footer = QFrame()
        # Đã làm sạch chú thích lỗi mã hóa.
        self.footer.setFixedHeight(115)
        self.footer.setStyleSheet('''
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        ''')
        f_layout = QVBoxLayout(self.footer)
        f_layout.setSpacing(2)
        f_layout.setContentsMargins(8, 8, 8, 8)

        self.lbl_stance = QLabel("TƯ THẾ: ĐỨNG")
        self.lbl_stance.setObjectName("StanceLabel")
        self.lbl_stance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stance.setFixedHeight(30)
        self.lbl_stance.setStyleSheet('''
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #262626;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
        ''')
        f_layout.addWidget(self.lbl_stance)

        self.btn_macro = QPushButton("MACRO : OFF")
        self.btn_macro.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.btn_macro.setFixedHeight(30)
        self.btn_macro.setStyleSheet('''
            QPushButton {
                color: #ff4444;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
                background: #1a1010;
                border: 1px solid #441111;
                border-radius: 5px;
            }
        ''')
        self.update_macro_style(False)
        f_layout.addWidget(self.btn_macro)

        bottom_row.addWidget(self.footer)

        # Đã làm sạch chú thích lỗi mã hóa.
        cross_card = QFrame()
        cross_card.setFixedHeight(115)
        cross_card.setStyleSheet('''
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        ''')
        cross_card_layout = QVBoxLayout(cross_card)
        cross_card_layout.setSpacing(6)
        cross_card_layout.setContentsMargins(10, 8, 10, 8)

        # Đã làm sạch chú thích lỗi mã hóa.
        lbl_cross.setObjectName("CrosshairSectionTitle")
        cross_card_layout.addWidget(lbl_cross)

        row_cross = QHBoxLayout()
        self.btn_cross_toggle = QPushButton("ON")
        self.btn_cross_toggle.setObjectName("CrosshairToggleBtn")
        self.btn_cross_toggle.setProperty("checked", "true")
        self.btn_cross_toggle.setCheckable(True)
        self.btn_cross_toggle.setChecked(True)
        self.btn_cross_toggle.setFixedSize(40, 20)
        self.btn_cross_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_toggle.clicked.connect(self.toggle_crosshair)

        self.combo_style = QComboBox()
        self.combo_style.addItems([
            "1: Gap Cross", "2: T-Shape", "3: Circle Dot", "5: Classic",
            "6: Micro Dot", "7: Hollow Box", "8: Cross + Dot", "9: Chevron",
            "10: X-Shape", "11: Diamond", "13: Triangle", "14: Square Dot",
            "17: Bracket Dot", "18: Shuriken", "19: Center Gap", "22: Plus Dot",
            "23: V-Shape", "24: Star"
        ])
        self.combo_style.setCurrentText("Style 1")
        self.combo_style.setFixedHeight(20)
        self.combo_style.currentIndexChanged.connect(self.change_crosshair_style)

        self.combo_color = QComboBox()
        self.combo_color.addItems([
            "Đỏ", "Đỏ Cam", "Cam", "Vàng",
            "Xanh Lá", "Xanh Ngọc", "Xanh Dương",
            "Tím", "Tím Hồng", "Hồng",
            "Trắng", "Bạc"
        ])
        self.combo_color.setCurrentText("Đỏ")
        self.combo_color.setFixedHeight(20)
        self.combo_color.currentIndexChanged.connect(self.change_crosshair_color)

        row_cross.addWidget(self.btn_cross_toggle)
        row_cross.addWidget(self.combo_style)
        row_cross.addWidget(self.combo_color)
        cross_card_layout.addLayout(row_cross)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #3a3a3a; border: none;")
        sep.setFixedHeight(1)
        cross_card_layout.addWidget(sep)

        row_btns = QHBoxLayout()
        btn_default = QPushButton("CÀI ĐẶT GỐC")
        btn_default.setObjectName("DefaultBtn")
        btn_default.setFixedHeight(30)
        btn_default.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_default.clicked.connect(self.reset_to_defaults)

        btn_save = QPushButton("LƯU CÀI ĐẶT")
        btn_save.setObjectName("SaveBtn")
        btn_save.setFixedHeight(30)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_config)

        row_btns.addWidget(btn_default)
        row_btns.addWidget(btn_save)
        cross_card_layout.addLayout(row_btns)

        bottom_row.addWidget(cross_card)
        body_layout.addLayout(bottom_row)
        
        main_layout.addWidget(body_widget)

        
        
        # Load Settings (General)
        self.load_config()
        
        # Load Crosshair Settings
        self.load_crosshair_settings()


    # Đã làm sạch chú thích lỗi mã hóa.
    def toggle_overlay_visibility(self):
        if self._overlay_enabled:
            self._overlay_enabled = False
            self._dispose_overlay("game_overlay")
            self.btn_overlay_toggle.setText("OFF")
            self.btn_overlay_toggle.setProperty("state", "OFF")
        else:
            if not self.ensure_runtime_started():
                return
            self._overlay_enabled = True
            overlay = self._ensure_game_overlay()
            overlay.show()
            logger.info("game overlay shown")
            self._update_game_overlay_from_last_data()
            self.btn_overlay_toggle.setText("ON")
            self.btn_overlay_toggle.setProperty("state", "ON")
        self.repolish(self.btn_overlay_toggle)

    def toggle_fast_loot(self, checked=None):
        if checked is None:
            checked = self.btn_fastloot_toggle.text() != "ON"
        else:
            checked = bool(checked)

        if checked:
            self.btn_fastloot_toggle.setText("ON")
            self.btn_fastloot_toggle.setProperty("state", "ON")
        else:
            self.btn_fastloot_toggle.setText("OFF")
            self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.repolish(self.btn_fastloot_toggle)
        if hasattr(self, "btn_fastloot_switch") and self.btn_fastloot_switch:
            if self.btn_fastloot_switch.isChecked() != checked:
                self.btn_fastloot_switch.setChecked(checked)
        self.signal_settings_changed.emit()

    def toggle_slide_trick(self, checked=None):
        if checked is None:
            checked = self.btn_slide_toggle.text() != "ON"
        else:
            checked = bool(checked)

        if checked:
            self.btn_slide_toggle.setText("ON")
            self.btn_slide_toggle.setProperty("state", "ON")
        else:
            self.btn_slide_toggle.setText("OFF")
            self.btn_slide_toggle.setProperty("state", "OFF")
        self.repolish(self.btn_slide_toggle)
        if hasattr(self, "btn_slide_switch") and self.btn_slide_switch:
            if self.btn_slide_switch.isChecked() != checked:
                self.btn_slide_switch.setChecked(checked)
        self.signal_settings_changed.emit()

    def toggle_crosshair(self, checked):
        checked = bool(checked)
        if checked:
            if not self.ensure_runtime_started():
                return
            crosshair = self._ensure_crosshair_overlay()
            crosshair.set_active(True)
            crosshair.show()
            crosshair.raise_()
            self.btn_cross_toggle.setText("ON")
            self.btn_cross_toggle.setProperty("checked", "true")
        else:
            if self.crosshair is not None:
                self.crosshair.set_active(False)
            self._dispose_overlay("crosshair")
            self.btn_cross_toggle.setText("OFF")
            self.btn_cross_toggle.setProperty("checked", "false")
        self.repolish(self.btn_cross_toggle)
        if hasattr(self, "btn_cross_on") and self.btn_cross_on:
            self.style_capture_button(self.btn_cross_on, checked)
        if hasattr(self, "btn_cross_off") and self.btn_cross_off:
            self.style_capture_button(self.btn_cross_off, not checked)
        if hasattr(self, "btn_crosshair_switch") and self.btn_crosshair_switch:
            if self.btn_crosshair_switch.isChecked() != checked:
                self.btn_crosshair_switch.setChecked(checked)
        self.save_crosshair_settings() # Auto-save


    def change_crosshair_style(self, index):
        style_map = dict(self.crosshair_style_options)
        style = style_map.get(self.combo_style.currentText(), "x")
        if self.crosshair is not None:
            self.crosshair.set_style(style)
        self.save_crosshair_settings() # Auto-save

    def change_crosshair_color(self, index):
        color = self.combo_color.currentText()
        if self.crosshair is not None:
            self.crosshair.set_color(color)
        self.save_crosshair_settings() # Auto-save


    # --- KEYBIND LISTENER LOGIC ---
    def start_keybind_listening(self, btn, setting_key):
        self.listening_key = True
        self.target_key_btn = btn
        self.target_key_btn = btn
        self.target_setting_key = setting_key # "fastloot"
        # Store previous text to revert on cancel
        self.temp_original_text = btn.text()
        
        btn.setText("PRESS KEY...")
        btn.setStyleSheet("background-color: #FF00FF; color: white; border: 1px solid #fff;")
        self.setFocus() # Ensure Window gets key events

    def finish_keybind_capture(self, key_name):
        if not self.target_key_btn:
            return

        display_key = key_name.upper()
        if key_name == "right":
            display_key = "RIGHT MOUSE"
        elif key_name == "left":
            display_key = "LEFT MOUSE"
        elif self.target_setting_key == "aim_secondary_key" and key_name == "ctrl":
            display_key = "LEFT CTRL"
        self.target_key_btn.setText(display_key)
        self.target_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a; color: #ccc; 
                border: 1px solid #444; border-radius: 4px; font-size: 11px;
            }
            QPushButton:hover { border: 1px solid #666; background-color: #333; }
        """)

        if self.target_setting_key == "gui_toggle":
            self.temp_guitoggle_value = key_name
        elif self.target_setting_key == "overlay_key":
            self.temp_overlay_key_value = key_name
        elif self.target_setting_key == "fast_loot_key":
            self.temp_fast_loot_key_value = key_name
        elif self.target_setting_key == "crosshair_toggle_key":
            self.temp_crosshair_toggle_key_value = key_name
            self.save_crosshair_settings()
            self.signal_settings_changed.emit()
        elif self.target_setting_key == "aim_emergency_stop_key":
            self.temp_aim_emergency_key_value = key_name
        elif self.target_setting_key == "aim_primary_key":
            self.temp_aim_primary_key_value = key_name
        elif self.target_setting_key == "aim_secondary_key":
            self.temp_aim_secondary_key_value = key_name
        elif self.target_setting_key == "aim_trigger_key":
            self.temp_aim_trigger_key_value = key_name

        if self.target_setting_key in {"gui_toggle", "fast_loot_key"}:
            self.signal_settings_changed.emit()

        self.listening_key = False
        self.target_key_btn = None
        self.temp_original_text = None

    def keyPressEvent(self, event):
        # 1. Handle Keybind Listening
        if self.listening_key and self.target_key_btn:
            key = event.key()
            
            # Convert Qt Key to Pynput/Win32 friendly string
            key_name = QKeySequence(key).toString().lower()
            
            # Special mapping for Common Keys
            if key == Qt.Key.Key_CapsLock: key_name = "caps_lock"
            elif key == Qt.Key.Key_Shift: key_name = "shift"
            elif key == Qt.Key.Key_Control: key_name = "ctrl"
            elif key == Qt.Key.Key_Alt: key_name = "alt"
            
            # CLEAR KEY (Escape / Backspace / Delete) -> NONE
            elif key == Qt.Key.Key_Escape or key == Qt.Key.Key_Backspace or key == Qt.Key.Key_Delete:
                key_name = "NONE"

            self.finish_keybind_capture(key_name)
            return

        else:
            super().keyPressEvent(event)


    def eventFilter(self, obj, event):
        """Global Event Filter to handle clicking away"""
        if hasattr(self, 'hover_hint_targets') and obj in self.hover_hint_targets:
            anchor, text = self.hover_hint_targets[obj]
            if event.type() == QEvent.Type.Enter:
                enter_pos = event.position().toPoint() if hasattr(event, "position") else anchor.rect().bottomLeft()
                self.show_hover_hint(anchor, text)
                self._move_hover_hint(anchor, enter_pos)
            elif event.type() == QEvent.Type.MouseMove:
                move_pos = event.position().toPoint() if hasattr(event, "position") else None
                self._move_hover_hint(anchor, move_pos)
            elif event.type() == QEvent.Type.Leave:
                self.hide_hover_hint()

        if getattr(self, "listening_key", False) and event.type() == QEvent.Type.MouseButtonPress:
            target_key_btn = getattr(self, "target_key_btn", None)
            if target_key_btn and target_key_btn.underMouse():
                return super().eventFilter(obj, event)

            button_map = {
                Qt.MouseButton.LeftButton: "left",
                Qt.MouseButton.RightButton: "right",
                Qt.MouseButton.MiddleButton: "middle",
                Qt.MouseButton.XButton1: "xbutton1",
                Qt.MouseButton.XButton2: "xbutton2",
            }
            key_name = button_map.get(event.button())
            if key_name:
                self.finish_keybind_capture(key_name)
                return True

            self.cancel_listening()
            
        return super().eventFilter(obj, event)

    def cancel_listening(self):
        """Helper to cancel listening state"""
        if not self.listening_key: return
        
        if self.target_key_btn:
            # Revert Text (UPPERCASE!)
            if hasattr(self, 'temp_original_text') and self.temp_original_text:
                self.target_key_btn.setText(self.temp_original_text.upper())
            else:
                self.target_key_btn.setText("CAPS_LOCK")
                
            # Revert Style
            self.target_key_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a; color: #ccc; 
                    border: 1px solid #444; border-radius: 4px; font-size: 11px;
                }
                QPushButton:hover { border: 1px solid #666; background-color: #333; }
            """)
            
        self.listening_key = False
        self.target_key_btn = None
        self.temp_original_text = None
            
    def load_config(self):
        """Load settings from settings.json"""
        try:
            settings = self.settings_manager.load()
            
            # Load Mouse Mode (Legacy Support / Hidden)
            # mouse_mode = settings.get("mouse_mode", "Win32")
            # Default Win32 (No UI)
            
            # Load GUI Toggle Key
            gui_toggle_key = "F1"  # Default
            if "keybinds" in settings and isinstance(settings["keybinds"], dict):
                gui_toggle_key = settings["keybinds"].get("gui_toggle", "f1")
            
            self.btn_guitoggle.setText(gui_toggle_key.upper())

            # Load ADS Mode
            ads_mode = settings.get("ads_mode", "HOLD")
            self.btn_adsmode.setText(ads_mode.upper())
            self.update_ads_status_style(ads_mode.upper())

            # Load Capture Mode
            cap_mode = settings.get("capture_mode", "DXCAM")
            normalized_cap_mode = self.set_capture_mode_ui(cap_mode.upper())
            if str(cap_mode).upper() != normalized_cap_mode:
                settings["capture_mode"] = normalized_cap_mode
                self.settings_manager.save(settings)

            # Load FastLoot
            fast_loot = settings.get("fast_loot", True)
            self.btn_fastloot_toggle.setText("ON" if fast_loot else "OFF")
            self.btn_fastloot_toggle.setProperty("state", "ON" if fast_loot else "OFF")
            self.repolish(self.btn_fastloot_toggle)
            if hasattr(self, "btn_fastloot_switch") and self.btn_fastloot_switch:
                self.btn_fastloot_switch.setChecked(fast_loot)

            slide_trick = settings.get("slide_trick", True)
            self.btn_slide_toggle.setText("ON" if slide_trick else "OFF")
            self.btn_slide_toggle.setProperty("state", "ON" if slide_trick else "OFF")
            self.repolish(self.btn_slide_toggle)
            if hasattr(self, "btn_slide_switch") and self.btn_slide_switch:
                self.btn_slide_switch.setChecked(slide_trick)
            
            fl_key = settings.get("fast_loot_key", "caps_lock")
            self.btn_fastloot_key.setText(fl_key.upper())

            ov_key = settings.get("overlay_key", "delete")
            self.btn_overlay_key.setText(ov_key.upper())
            self._apply_overlay_enabled_ui(bool(settings.get("overlay_enabled", True)))

            scope_intensity = settings.get("scope_intensity", {})
            for scope_key, _ in getattr(self, "scope_order", []):
                value = int(scope_intensity.get(scope_key, 100))
                value = max(50, min(150, value))
                if scope_key in self.scope_sliders:
                    self.scope_sliders[scope_key].setValue(value)
                    self.update_scope_intensity_label(scope_key, value)

            aim_settings = settings.get("aim", {}) if isinstance(settings.get("aim", {}), dict) else {}
            aim_runtime = aim_settings.get("runtime", {}) if isinstance(aim_settings.get("runtime", {}), dict) else {}
            aim_meta = aim_settings.get("meta", {}) if isinstance(aim_settings.get("meta", {}), dict) else {}
            aim_bindings = aim_settings.get("bindings", {}) if isinstance(aim_settings.get("bindings", {}), dict) else {}
            aim_sliders = aim_settings.get("sliders", {}) if isinstance(aim_settings.get("sliders", {}), dict) else {}
            aim_toggles = aim_settings.get("toggles", {}) if isinstance(aim_settings.get("toggles", {}), dict) else {}
            aim_dropdowns = aim_settings.get("dropdowns", {}) if isinstance(aim_settings.get("dropdowns", {}), dict) else {}
            aim_colors = aim_settings.get("colors", {}) if isinstance(aim_settings.get("colors", {}), dict) else {}
            aim_file_locations = aim_settings.get("file_locations", {}) if isinstance(aim_settings.get("file_locations", {}), dict) else {}
            aim_minimize = aim_settings.get("minimize", {}) if isinstance(aim_settings.get("minimize", {}), dict) else {}
            aim_capture_mode = str(
                aim_runtime.get("capture_backend")
                or aim_dropdowns.get("Screen Capture Method")
                or "DirectX"
            )
            self.set_aim_capture_mode_ui(aim_capture_mode)
            if hasattr(self, "combo_aim_target_priority") and self.combo_aim_target_priority:
                priority_text = str(aim_dropdowns.get("Target Priority", "Body -> Head"))
                if priority_text not in ("Body -> Head", "Head -> Body"):
                    priority_text = "Body -> Head"
                self.combo_aim_target_priority.setCurrentText(priority_text)
            selected_model = (
                aim_runtime.get("model")
                or aim_meta.get("last_loaded_model")
                or ""
            )
            if str(selected_model).upper() == "N/A":
                selected_model = ""
            self.refresh_aim_model_list(str(selected_model))
            if hasattr(self, "aim_btn_primary") and self.aim_btn_primary:
                primary_key = str(aim_bindings.get("Aim Keybind", "right")).upper()
                self.aim_btn_primary.setText("RIGHT MOUSE" if primary_key == "RIGHT" else primary_key)
            if hasattr(self, "aim_btn_secondary") and self.aim_btn_secondary:
                secondary_key = str(aim_bindings.get("Second Aim Keybind", "ctrl")).upper()
                self.aim_btn_secondary.setText("LEFT CTRL" if secondary_key in ("LMENU", "LCONTROL", "CTRL") else secondary_key)
            if hasattr(self, "aim_btn_trigger") and self.aim_btn_trigger:
                self.aim_btn_trigger.setText(str(aim_bindings.get("Toggle Trigger Keybind", "f7")).upper())
            if hasattr(self, "aim_btn_emergency_stop") and self.aim_btn_emergency_stop:
                self.aim_btn_emergency_stop.setText(str(aim_bindings.get("Emergency Stop Keybind", "f8")).upper())
            if hasattr(self, "aim_slider_fov") and self.aim_slider_fov:
                fov_value = int(aim_sliders.get("FOV Size", 300))
                fov_value = max(10, min(640, fov_value))
                self.aim_slider_fov.setValue(fov_value)
                self.update_aim_fov_label(fov_value)
            if hasattr(self, "aim_slider_confidence") and self.aim_slider_confidence:
                confidence_value = int(aim_sliders.get("AI Minimum Confidence", 45))
                confidence_value = max(1, min(100, confidence_value))
                self.aim_slider_confidence.setValue(confidence_value)
                self.update_aim_confidence_label(confidence_value)
            if hasattr(self, "aim_slider_trigger_delay") and self.aim_slider_trigger_delay:
                raw_delay = aim_sliders.get("Auto Trigger Delay", 0.1)
                delay_ms = int(round(float(raw_delay) * 1000)) if float(raw_delay) <= 1.0 else int(round(float(raw_delay)))
                delay_ms = max(10, min(1000, delay_ms))
                self.aim_slider_trigger_delay.setValue(delay_ms)
                self.update_aim_trigger_delay_label(delay_ms)
            if hasattr(self, "aim_slider_capture_fps") and self.aim_slider_capture_fps:
                capture_fps_value = int(round(float(aim_sliders.get("Capture FPS", 144))))
                capture_fps_value = max(1, min(240, capture_fps_value))
                self.aim_slider_capture_fps.setValue(capture_fps_value)
                self.update_aim_capture_fps_label(capture_fps_value)
            if hasattr(self, "aim_slider_primary_position") and self.aim_slider_primary_position:
                primary_position_value = int(round(float(aim_sliders.get("Primary Aim Position", 50))))
                primary_position_value = max(0, min(100, primary_position_value))
                self.aim_slider_primary_position.setValue(primary_position_value)
                self.update_aim_primary_position_label(primary_position_value)
            if hasattr(self, "aim_slider_secondary_position") and self.aim_slider_secondary_position:
                secondary_position_value = int(round(float(aim_sliders.get("Secondary Aim Position", 50))))
                secondary_position_value = max(0, min(100, secondary_position_value))
                self.aim_slider_secondary_position.setValue(secondary_position_value)
                self.update_aim_secondary_position_label(secondary_position_value)
            if hasattr(self, "aim_slider_sensitivity") and self.aim_slider_sensitivity:
                sensitivity_value = float(aim_sliders.get("Mouse Sensitivity (+/-)", 0.80))
                sensitivity_slider = max(1, min(100, int(round(sensitivity_value * 100.0))))
                self.aim_slider_sensitivity.setValue(sensitivity_slider)
                self.update_aim_sensitivity_label(sensitivity_slider)
            if hasattr(self, "aim_slider_ema") and self.aim_slider_ema:
                ema_value = float(aim_sliders.get("EMA Smoothening", 0.50))
                ema_slider = max(1, min(100, int(round(ema_value * 100.0))))
                self.aim_slider_ema.setValue(ema_slider)
                self.update_aim_ema_label(ema_slider)
            if hasattr(self, "aim_slider_dynamic_fov") and self.aim_slider_dynamic_fov:
                dynamic_fov_value = int(round(float(aim_sliders.get("Dynamic FOV Size", 10))))
                dynamic_fov_value = max(10, min(640, dynamic_fov_value))
                self.aim_slider_dynamic_fov.setValue(dynamic_fov_value)
                self.update_aim_dynamic_fov_label(dynamic_fov_value)
            if hasattr(self, "aim_slider_sticky_threshold") and self.aim_slider_sticky_threshold:
                sticky_threshold_value = int(round(float(aim_sliders.get("Sticky Aim Threshold", 0))))
                sticky_threshold_value = max(0, min(100, sticky_threshold_value))
                self.aim_slider_sticky_threshold.setValue(sticky_threshold_value)
                self.update_aim_sticky_threshold_label(sticky_threshold_value)
            if hasattr(self, "aim_slider_jitter") and self.aim_slider_jitter:
                jitter_value = int(aim_sliders.get("Mouse Jitter", 4))
                jitter_value = max(0, min(15, jitter_value))
                self.aim_slider_jitter.setValue(jitter_value)
                self.update_aim_jitter_label(jitter_value)
            self.load_aim_listing_sliders(aim_sliders)
            if hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov:
                self.aim_chk_show_fov.setChecked(bool(aim_toggles.get("Show FOV", True)))
            if hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect:
                self.aim_chk_show_detect.setChecked(bool(aim_toggles.get("Show Detected Player", False)))
            self.load_aim_toggle_controls(aim_toggles)
            self.load_aim_dropdown_controls(aim_dropdowns)
            self.load_aim_color_controls(aim_colors)
            self.load_aim_file_controls(aim_file_locations)
            self.load_aim_minimize_controls(aim_minimize)
            current_model = ""
            if hasattr(self, "combo_aim_model") and self.combo_aim_model and self.combo_aim_model.isEnabled():
                current_model = self.combo_aim_model.currentText().strip()
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")

    def set_capture_mode(self, mode):
        self.set_capture_mode_ui(mode)
        try:
            self.settings_manager.set("capture_mode", getattr(self, "current_capture_mode", "DXCAM"))
            self.settings_manager.save()
        except Exception:
            pass
        try:
            if getattr(self, "backend", None) is not None and hasattr(self.backend, "apply_capture_mode"):
                self.backend.apply_capture_mode(getattr(self, "current_capture_mode", "DXCAM"))
        except Exception:
            pass

    def set_capture_mode_ui(self, mode):
        raw_mode = str(mode or "DXCAM").strip()
        mode_upper = raw_mode.upper()
        mode_map = {
            "DXCAM": "DXCAM",
            "DIRECTX": "DXCAM",
            "DXGI": "DXCAM",
            "MSS": "MSS",
            "NATIVE": "DXCAM",
            "GDI": "MSS",
            "GDI+": "MSS",
            "PIL": "MSS",
            "AUTO": "DXCAM",
        }
        mode = mode_map.get(mode_upper, "DXCAM")
        self.current_capture_mode = mode
        if hasattr(self, "lbl_capture_mode_auto") and self.lbl_capture_mode_auto:
            self.lbl_capture_mode_auto.setText(mode)
        if hasattr(self, "btn_capture_native") and self.btn_capture_native:
            self.btn_capture_native.hide()
        if hasattr(self, "btn_capture_dxcam") and self.btn_capture_dxcam:
            self.style_capture_button(self.btn_capture_dxcam, mode == "DXCAM")
        if hasattr(self, "btn_capture_mss") and self.btn_capture_mss:
            self.style_capture_button(self.btn_capture_mss, mode == "MSS")
        if hasattr(self, "btn_mode_wgc") and self.btn_mode_wgc:
            self.btn_mode_wgc.setProperty("active", "true" if mode == "DXCAM" else "false")
            self.repolish(self.btn_mode_wgc)
        if hasattr(self, "btn_mode_dxgi") and self.btn_mode_dxgi:
            self.btn_mode_dxgi.setProperty("active", "true" if mode == "MSS" else "false")
            self.repolish(self.btn_mode_dxgi)
        if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
            backend_text = "Chưa nạp"
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text
            self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(backend_text, runtime_source))
        self.update_home_snapshot()
        return mode

    def set_aim_capture_mode(self, mode):
        self.set_aim_capture_mode_ui(mode)

    def set_aim_capture_mode_ui(self, mode):
        raw_mode = str(mode or "DirectX").strip()
        mode_upper = raw_mode.upper()
        mode_map = {
            "DIRECTX": "DirectX",
            "DXCAM": "DirectX",
            "GDI+": "GDI+",
            "MSS": "GDI+",
            "PIL": "GDI+",
        }
        mode = mode_map.get(mode_upper, "DirectX")
        self.current_aim_capture_mode = mode
        if hasattr(self, "combo_aim_capture") and self.combo_aim_capture:
            target_index = self.combo_aim_capture.findText(mode)
            if target_index >= 0 and self.combo_aim_capture.currentIndex() != target_index:
                self.combo_aim_capture.blockSignals(True)
                self.combo_aim_capture.setCurrentIndex(target_index)
                self.combo_aim_capture.blockSignals(False)
        if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
            backend_text = "Chưa nạp"
            runtime_source = ""
            if hasattr(self, "last_data") and isinstance(self.last_data, dict):
                runtime_source = str(self.last_data.get("aim", {}).get("runtime_source", "") or "")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                backend_text = self.lbl_aim_backend_info.text().replace("Backend:", "").strip() or backend_text
            self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(backend_text, runtime_source))
        self.update_home_snapshot()

    def cycle_ads_mode(self):
        current = self.btn_adsmode.text().strip().upper()

        if current == "HOLD":
            new_mode = "CLICK"
        else:
            new_mode = "HOLD"

        self.btn_adsmode.setText(new_mode)
        self.update_ads_status_style(new_mode)
        if self.crosshair is not None:
            self.crosshair.set_ads_mode(new_mode)
        self.save_crosshair_settings()

    def load_crosshair_settings(self):
        try:
            data = self.settings_manager.get("crosshair", {})
            is_on = data.get("active", False)
            self.btn_cross_toggle.setChecked(is_on)
            self.btn_cross_toggle.setText("ON" if is_on else "OFF")
            self.btn_cross_toggle.setProperty("checked", "true" if is_on else "false")
            self.repolish(self.btn_cross_toggle)
            if hasattr(self, "btn_cross_on") and self.btn_cross_on:
                self.style_capture_button(self.btn_cross_on, is_on)
            if hasattr(self, "btn_cross_off") and self.btn_cross_off:
                self.style_capture_button(self.btn_cross_off, not is_on)
            if hasattr(self, "btn_crosshair_switch") and self.btn_crosshair_switch:
                self.btn_crosshair_switch.blockSignals(True)
                self.btn_crosshair_switch.setChecked(is_on)
                self.btn_crosshair_switch.blockSignals(False)
            style = self.normalize_crosshair_style_value(data.get("style", "x"))
            display_names = [display for display, internal in self.crosshair_style_options if internal == style]
            display_name = display_names[0] if display_names else "X"
            idx = self.combo_style.findText(display_name)
            self.combo_style.setCurrentIndex(idx if idx >= 0 else 0)
            saved_color_idx = data.get("color_index", None)
            if saved_color_idx is None:
                saved_color_name = data.get("color", "Đỏ")
                idx = self.combo_color.findText(saved_color_name)
                saved_color_idx = idx if idx >= 0 else 0
            self.combo_color.setCurrentIndex(saved_color_idx)
            ads_mode = data.get("ads_mode", "HOLD")
            if hasattr(self, "btn_adsmode") and self.btn_adsmode: self.btn_adsmode.setText(ads_mode)
            self.update_ads_status_style(ads_mode)
            toggle_key = data.get("toggle_key", "none")
            if hasattr(self, 'btn_cross_bind') and self.btn_cross_bind: self.btn_cross_bind.setText(toggle_key.upper())
        except Exception as e: print(f"[ERROR] Load Crosshair failed: {e}")

    def save_crosshair_settings(self):
        try:
            is_active = self.btn_cross_toggle.isChecked()
            style_map = dict(self.crosshair_style_options)
            style_val = style_map.get(self.combo_style.currentText(), "x")
            color_idx = self.combo_color.currentIndex()
            color_name = self.combo_color.itemText(color_idx) if color_idx >= 0 else "Đỏ"
            toggle_key = getattr(self, "temp_crosshair_toggle_key_value", None) or (self.btn_cross_bind.text().lower() if hasattr(self, 'btn_cross_bind') else "none")
            if hasattr(self, "btn_adsmode") and self.btn_adsmode: ads_mode = self.btn_adsmode.text().strip().upper() or "HOLD"
            elif hasattr(self, "lbl_ads_status") and self.lbl_ads_status: ads_mode = self.lbl_ads_status.text().replace("ADS :", "").strip().upper() or "HOLD"
            else: ads_mode = "HOLD"
            data = {"active": is_active, "style": style_val, "color": color_name, "color_index": color_idx, "toggle_key": toggle_key, "ads_mode": ads_mode}
            self.settings_manager.set("crosshair", data)
        except Exception as e: print(f"[ERROR] Save Crosshair failed: {e}")

    def reset_to_defaults(self):
        """Reset all settings to project defaults and update UI"""
        confirmed = AppNoticeDialog.question(
            self,
            "Xác Nhận Cài Đặt Gốc",
            "Bạn có chắc chắn muốn đặt lại toàn bộ cài đặt về mặc định không?\n(Lưu ý: Hành động này không thể hoàn tác)"
        )
        if not confirmed:
            return
        
        try:
            self.settings_manager.reset_to_defaults()
            self.refresh_ui_from_settings(force_reload=True, sync_runtime=True)
            self.play_action_beep("reset")
            self.show_bottom_action_status("Đã đưa cấu hình về mặc định.", tone="success")
        except Exception as e:
            print(f'[ERROR] reset_to_defaults failed: {e}')
            self.show_bottom_action_status("Reset thất bại.", tone="error", auto_hide_ms=3000)

    def refresh_ui_from_settings(self, force_reload=False, sync_runtime=False):
        if force_reload:
            self.settings_manager._cache = None

        self.load_config()
        self.load_crosshair_settings()
        self._load_overlay_enabled_setting()
        self._sync_game_overlay_startup()

        if hasattr(self, "last_data"):
            self.update_home_snapshot()
            self.update_aim_visual_overlay(self.last_data)
            self.update_ui_state(self.last_data)

        if sync_runtime:
            capture_mode = getattr(self, "current_capture_mode", "DXCAM")
            self.set_capture_mode(capture_mode)
            self.signal_settings_changed.emit()

    def save_config(self):
        """Manually Save All Settings (Triggered by Button)"""
        try:
            
            # 2. GUI Toggle Key (use temp value if changed, otherwise button text)
            if self.temp_guitoggle_value:
                guitoggle_key = self.temp_guitoggle_value
                self.temp_guitoggle_value = None  # Clear temp after saving
            else:
                guitoggle_key = self.btn_guitoggle.text().lower()
            
            capture_mode = getattr(self, 'current_capture_mode', 'DXCAM')
            aim_capture_mode = getattr(self, 'current_aim_capture_mode', 'DirectX')
                
            # Construct Data
            current_settings = self.settings_manager.load()
            
            # Update Keybinds (Standard Path)
            if "keybinds" not in current_settings or not isinstance(current_settings["keybinds"], dict):
                current_settings["keybinds"] = {}
            
            current_settings["keybinds"]["gui_toggle"] = guitoggle_key.lower()
            current_settings["capture_mode"] = capture_mode
            aim_settings = current_settings.setdefault("aim", {})
            aim_runtime = aim_settings.setdefault("runtime", {})
            aim_dropdowns = aim_settings.setdefault("dropdowns", {})
            aim_runtime["capture_backend"] = aim_capture_mode
            aim_dropdowns["Screen Capture Method"] = aim_capture_mode
            aim_dropdowns["Target Priority"] = (
                self.combo_aim_target_priority.currentText()
                if hasattr(self, "combo_aim_target_priority") and self.combo_aim_target_priority
                else "Body -> Head"
            )
            
            # Fast Loot
            if self.temp_fast_loot_key_value:
                current_settings["fast_loot_key"] = self.temp_fast_loot_key_value
                self.temp_fast_loot_key_value = None
            else:
                current_settings["fast_loot_key"] = self.btn_fastloot_key.text().lower()
            current_settings["fast_loot"] = self.btn_fastloot_toggle.text().upper() == "ON"
            current_settings["slide_trick"] = self.btn_slide_toggle.text().upper() == "ON"

            # Overlay Key
            if self.temp_overlay_key_value:
                current_settings["overlay_key"] = self.temp_overlay_key_value
                self.temp_overlay_key_value = None
            else:
                current_settings["overlay_key"] = self.btn_overlay_key.text().lower()
            current_settings["overlay_enabled"] = bool(
                self._overlay_enabled if hasattr(self, "_overlay_enabled") else True
            )

            current_settings["scope_intensity"] = {
                scope_key: slider.value()
                for scope_key, slider in getattr(self, "scope_sliders", {}).items()
            }

            if "aim" not in current_settings or not isinstance(current_settings["aim"], dict):
                current_settings["aim"] = {}
            if "runtime" not in current_settings["aim"] or not isinstance(current_settings["aim"]["runtime"], dict):
                current_settings["aim"]["runtime"] = {}
            if "meta" not in current_settings["aim"] or not isinstance(current_settings["aim"]["meta"], dict):
                current_settings["aim"]["meta"] = {}
            if "bindings" not in current_settings["aim"] or not isinstance(current_settings["aim"]["bindings"], dict):
                current_settings["aim"]["bindings"] = {}
            if "sliders" not in current_settings["aim"] or not isinstance(current_settings["aim"]["sliders"], dict):
                current_settings["aim"]["sliders"] = {}
            if "toggles" not in current_settings["aim"] or not isinstance(current_settings["aim"]["toggles"], dict):
                current_settings["aim"]["toggles"] = {}
            if "dropdowns" not in current_settings["aim"] or not isinstance(current_settings["aim"]["dropdowns"], dict):
                current_settings["aim"]["dropdowns"] = {}
            if "colors" not in current_settings["aim"] or not isinstance(current_settings["aim"]["colors"], dict):
                current_settings["aim"]["colors"] = {}
            if "file_locations" not in current_settings["aim"] or not isinstance(current_settings["aim"]["file_locations"], dict):
                current_settings["aim"]["file_locations"] = {}
            if "minimize" not in current_settings["aim"] or not isinstance(current_settings["aim"]["minimize"], dict):
                current_settings["aim"]["minimize"] = {}

            selected_model = ""
            if hasattr(self, "combo_aim_model") and self.combo_aim_model and self.combo_aim_model.isEnabled():
                selected_model = self.combo_aim_model.currentText().strip()
                if selected_model == "Không có model":
                    selected_model = ""
            current_settings["aim"]["runtime"]["model"] = selected_model
            current_settings["aim"]["meta"]["last_loaded_model"] = selected_model or "N/A"
            aim_primary_key = self.temp_aim_primary_key_value or (
                self.aim_btn_primary.text().lower().replace("right mouse", "right")
                if hasattr(self, "aim_btn_primary") and self.aim_btn_primary
                else "right"
            )
            aim_secondary_key = self.temp_aim_secondary_key_value or (
                self.aim_btn_secondary.text().lower().replace("left ctrl", "ctrl")
                if hasattr(self, "aim_btn_secondary") and self.aim_btn_secondary
                else "ctrl"
            )
            aim_trigger_key = self.temp_aim_trigger_key_value or (
                self.aim_btn_trigger.text().lower()
                if hasattr(self, "aim_btn_trigger") and self.aim_btn_trigger
                else "f7"
            )
            current_settings["aim"]["bindings"]["Aim Keybind"] = aim_primary_key
            current_settings["aim"]["bindings"]["Second Aim Keybind"] = aim_secondary_key
            current_settings["aim"]["bindings"]["Toggle Trigger Keybind"] = aim_trigger_key
            emergency_key = self.temp_aim_emergency_key_value or (
                self.aim_btn_emergency_stop.text().lower()
                if hasattr(self, "aim_btn_emergency_stop") and self.aim_btn_emergency_stop
                else "f8"
            )
            current_settings["aim"]["bindings"]["Emergency Stop Keybind"] = emergency_key
            current_settings["aim"]["sliders"]["FOV Size"] = (
                self.aim_slider_fov.value()
                if hasattr(self, "aim_slider_fov") and self.aim_slider_fov
                else 300
            )
            current_settings["aim"]["sliders"]["AI Minimum Confidence"] = (
                self.aim_slider_confidence.value()
                if hasattr(self, "aim_slider_confidence") and self.aim_slider_confidence
                else 45
            )
            current_settings["aim"]["sliders"]["Auto Trigger Delay"] = (
                round(self.aim_slider_trigger_delay.value() / 1000.0, 2)
                if hasattr(self, "aim_slider_trigger_delay") and self.aim_slider_trigger_delay
                else 0.1
            )
            current_settings["aim"]["sliders"]["Capture FPS"] = (
                self.aim_slider_capture_fps.value()
                if hasattr(self, "aim_slider_capture_fps") and self.aim_slider_capture_fps
                else 144
            )
            current_settings["aim"]["sliders"]["Primary Aim Position"] = (
                self.aim_slider_primary_position.value()
                if hasattr(self, "aim_slider_primary_position") and self.aim_slider_primary_position
                else 50
            )
            current_settings["aim"]["sliders"]["Secondary Aim Position"] = (
                self.aim_slider_secondary_position.value()
                if hasattr(self, "aim_slider_secondary_position") and self.aim_slider_secondary_position
                else 50
            )
            current_settings["aim"]["sliders"]["Mouse Sensitivity (+/-)"] = (
                round(self.aim_slider_sensitivity.value() / 100.0, 2)
                if hasattr(self, "aim_slider_sensitivity") and self.aim_slider_sensitivity
                else 0.80
            )
            current_settings["aim"]["sliders"]["EMA Smoothening"] = (
                round(self.aim_slider_ema.value() / 100.0, 2)
                if hasattr(self, "aim_slider_ema") and self.aim_slider_ema
                else 0.50
            )
            current_settings["aim"]["sliders"]["Dynamic FOV Size"] = (
                self.aim_slider_dynamic_fov.value()
                if hasattr(self, "aim_slider_dynamic_fov") and self.aim_slider_dynamic_fov
                else 10
            )
            current_settings["aim"]["sliders"]["Sticky Aim Threshold"] = (
                self.aim_slider_sticky_threshold.value()
                if hasattr(self, "aim_slider_sticky_threshold") and self.aim_slider_sticky_threshold
                else 0
            )
            current_settings["aim"]["sliders"]["Mouse Jitter"] = (
                self.aim_slider_jitter.value()
                if hasattr(self, "aim_slider_jitter") and self.aim_slider_jitter
                else 4
            )
            self.save_aim_listing_sliders(current_settings["aim"]["sliders"])
            current_settings["aim"]["toggles"]["Show FOV"] = (
                self.aim_chk_show_fov.isChecked()
                if hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov
                else True
            )
            current_settings["aim"]["toggles"]["Show Detected Player"] = (
                self.aim_chk_show_detect.isChecked()
                if hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect
                else False
            )
            self.save_aim_toggle_controls(current_settings["aim"]["toggles"])
            self.save_aim_dropdown_controls(current_settings["aim"]["dropdowns"])
            self.save_aim_color_controls(current_settings["aim"]["colors"])
            self.save_aim_file_controls(current_settings["aim"]["file_locations"])
            self.save_aim_minimize_controls(current_settings["aim"]["minimize"])
            self.temp_aim_primary_key_value = None
            self.temp_aim_secondary_key_value = None
            self.temp_aim_trigger_key_value = None
            self.temp_aim_emergency_key_value = None

            # Crosshair key/settings
            self.save_crosshair_settings()
            self.temp_crosshair_toggle_key_value = None

            # Save to File
            self.settings_manager.save(current_settings)
            
            # Notify Backend to reload config
            self.signal_settings_changed.emit()
            
            self.play_action_beep("save")
            self.show_bottom_action_status("Đã lưu cấu hình thành công.", tone="success")
            
        except Exception as e:
            print(f"[ERROR] Save Config Failed: {e}")
            self.show_bottom_action_status("Lỗi lưu cài đặt.", tone="error", auto_hide_ms=3000)





    def update_macro_style(self, is_on):
        if self._last_macro_toggle_state is is_on:
            return
        self._last_macro_toggle_state = is_on
        base = "font-size: 12px; font-weight: bold; letter-spacing: 2px; border-radius: 5px;"
        if is_on:
            self.btn_macro.setText("MACRO : ON")
            self.btn_macro.setStyleSheet(f"QPushButton {{ color: #00FFFF; background: #1b1b1b; border: 1px solid #006666; {base} }}")
        else:
            self.btn_macro.setText("MACRO : OFF")
            self.btn_macro.setStyleSheet(f"QPushButton {{ color: #ff4444; background: #1b1b1b; border: 1px solid #441111; {base} }}")
        self.update_home_snapshot()

    def update_ads_status_style(self, mode: str):
        if not hasattr(self, 'lbl_ads_status') or self.lbl_ads_status is None:
            return
        mode_upper = (mode or "HOLD").upper()
        display_mode = "TOGGLE" if mode_upper == "CLICK" else mode_upper
        color = "#00ffaa" if display_mode == "HOLD" else "#ffd166"
        ads_signature = (display_mode, color)
        if self._last_ads_status_signature == ads_signature:
            return
        self._last_ads_status_signature = ads_signature
        ads_text = f"ADS : {display_mode}"
        if self.lbl_ads_status.text() != ads_text:
            self.lbl_ads_status.setText(ads_text)
        self.lbl_ads_status.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #1b1b1b;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 0 6px;
            }}
        """)
        self.update_home_snapshot()
            


    def set_backend(self, backend):
        self.backend = backend
        self._runtime_started = backend is not None

    def set_runtime_starter(self, runtime_starter):
        self._runtime_starter = runtime_starter

    def ensure_runtime_started(self):
        if self.backend is not None and self._runtime_started:
            return True
        starter = getattr(self, "_runtime_starter", None)
        if starter is None:
            return False
        try:
            starter()
            self._sync_game_overlay_startup()
            return self.backend is not None
        except Exception:
            logger.exception("Failed to start runtime on demand")
            return False

    def set_runtime_handles(self, keyboard_listener=None, mouse_listener=None, native_input_worker=None, timers=None):
        self.keyboard_listener = keyboard_listener
        self.mouse_listener = mouse_listener
        self.native_input_worker = native_input_worker
        self._runtime_timers = list(timers or [])
        self._sync_game_overlay_startup()

    def _apply_overlay_enabled_ui(self, enabled: bool):
        self._overlay_enabled = bool(enabled)
        if hasattr(self, "btn_overlay_toggle") and self.btn_overlay_toggle:
            self.btn_overlay_toggle.setText("ON" if self._overlay_enabled else "OFF")
            self.btn_overlay_toggle.setProperty("state", "ON" if self._overlay_enabled else "OFF")
            self.repolish(self.btn_overlay_toggle)

    def _load_overlay_enabled_setting(self) -> bool:
        enabled = bool(self.settings_manager.get("overlay_enabled", True))
        self._apply_overlay_enabled_ui(enabled)
        return enabled

    def _ensure_game_overlay(self):
        if self.game_overlay is None:
            self.game_overlay = GameOverlay(None)
            logger.info("game overlay created")
        return self.game_overlay

    def _update_game_overlay_from_last_data(self):
        data = getattr(self, "last_data", None)
        if not isinstance(data, dict):
            return
        try:
            g1 = data.get("gun1", {}) or {}
            g2 = data.get("gun2", {}) or {}
            active_slot = data.get("active_slot", 1)
            active_gun = g1 if active_slot == 1 else g2
            weapon_name = "NONE" if str(active_gun.get("name", "NONE")) == "None" else str(active_gun.get("name", "NONE"))
            scope_name = "NONE" if str(active_gun.get("scope", "NONE")) == "None" else str(active_gun.get("scope", "NONE"))
            display_ai_status = data.get("ai_status", "HIBERNATE")
            overlay_signature = (
                weapon_name,
                scope_name,
                data.get("stance"),
                active_gun.get("grip", "NONE"),
                active_gun.get("accessories", "NONE"),
                bool(data.get("paused", False)),
                bool(data.get("firing", False)),
                display_ai_status,
            )
            overlay = self._ensure_game_overlay()
            overlay.update_status(
                weapon_name,
                scope_name,
                data.get("stance", "Stand"),
                grip=active_gun.get("grip", "NONE"),
                muzzle=active_gun.get("accessories", "NONE"),
                is_paused=data.get("paused", False),
                is_firing=data.get("firing", False),
                ai_status=display_ai_status,
            )
            self._last_game_overlay_signature = overlay_signature
            logger.info("game overlay updated")
        except Exception:
            logger.exception("Failed updating game overlay from last data")

    def _sync_game_overlay_startup(self):
        self._load_overlay_enabled_setting()
        if not self._overlay_enabled or self.backend is None or not self._runtime_started:
            return
        overlay = self._ensure_game_overlay()
        overlay.show()
        logger.info("game overlay shown")
        self._update_game_overlay_from_last_data()

    def _ensure_crosshair_overlay(self):
        if self.crosshair is None:
            self.crosshair = CrosshairOverlay(self)
            if hasattr(self, "combo_style") and self.combo_style:
                style_map = dict(self.crosshair_style_options)
                self.crosshair.set_style(
                    style_map.get(self.combo_style.currentText(), "x")
                )
            if hasattr(self, "combo_color") and self.combo_color:
                color_idx = self.combo_color.currentIndex()
                color_name = self.combo_color.itemText(color_idx) if color_idx >= 0 else "Đỏ"
                self.crosshair.set_color(color_name)
            if hasattr(self, "btn_adsmode") and self.btn_adsmode:
                self.crosshair.set_ads_mode(self.btn_adsmode.text().strip().upper() or "HOLD")
        return self.crosshair

    def _dispose_overlay(self, overlay_name: str):
        overlay = getattr(self, overlay_name, None)
        if overlay is None:
            return
        try:
            for timer_name in ("flash_timer", "detect_timer", "timer_ads"):
                overlay_timer = getattr(overlay, timer_name, None)
                if overlay_timer is not None:
                    overlay_timer.stop()
            overlay.hide()
            overlay.close()
            overlay.deleteLater()
        except Exception:
            logger.exception("Failed disposing overlay: %s", overlay_name)
        setattr(self, overlay_name, None)
        if overlay_name == "game_overlay":
            self._last_game_overlay_signature = None

    def _cleanup_dummy_threads(self, purge_stale: bool = False):
        active_threads = getattr(threading, "_active", None)
        for thread in list(threading.enumerate()):
            if thread.__class__.__name__ != "_DummyThread":
                continue
            if purge_stale and isinstance(active_threads, dict):
                active_threads.pop(thread.ident, None)
                logger.warning(
                    "Purged stale dummy thread record after listener shutdown: %s | source=pynput/native hook bookkeeping",
                    thread.name,
                )
                continue
            logger.warning(
                "Dummy thread still registered after listener stop: %s | source=native hook callback thread",
                thread.name,
            )

    def _log_listener_native_sources(self):
        for label, listener in (
            ("keyboard", getattr(self, "keyboard_listener", None)),
            ("mouse", getattr(self, "mouse_listener", None)),
        ):
            if listener is None or not hasattr(listener, "get_native_callback_source"):
                continue
            source = listener.get_native_callback_source()
            if source:
                logger.warning("%s listener native callback source detected: %s", label, source)

    def request_app_exit(self):
        self._perform_shutdown()

    def _listener_is_alive(self, listener) -> bool:
        if listener is None:
            return False
        running = bool(getattr(listener, "running", False))
        native_listener = getattr(listener, "listener", None)
        if native_listener is None:
            return running
        try:
            return running or bool(native_listener.is_alive())
        except Exception:
            return running

    def _timer_is_active(self, timer) -> bool:
        if timer is None:
            return False
        if hasattr(timer, "isActive"):
            try:
                return bool(timer.isActive())
            except Exception:
                return False
        return bool(getattr(timer, "active", False))

    def _collect_shutdown_snapshot(self) -> dict:
        timer_states = {}
        for timer_name in (
            "_layout_sync_timer",
            "_hover_hint_timer",
            "_bottom_action_status_timer",
        ):
            timer_states[timer_name] = self._timer_is_active(getattr(self, timer_name, None))

        runtime_timer_states = []
        for timer in getattr(self, "_runtime_timers", []):
            runtime_timer_states.append(
                f"{timer.__class__.__name__}:{'active' if self._timer_is_active(timer) else 'stopped'}"
            )

        overlay_states = {}
        for overlay_name in ("game_overlay", "crosshair"):
            overlay = getattr(self, overlay_name, None)
            overlay_states[overlay_name] = (
                overlay is not None and not overlay.isHidden() and overlay.isVisible()
            )

        alive_threads = []
        background_threads = []
        dummy_threads = []
        for thread in threading.enumerate():
            if not thread.is_alive():
                continue
            class_name = thread.__class__.__name__
            descriptor = f"{thread.name}(class={class_name},daemon={thread.daemon})"
            alive_threads.append(descriptor)
            if thread is not threading.main_thread() and class_name != "_DummyThread":
                background_threads.append(descriptor)
            if class_name == "_DummyThread":
                dummy_threads.append(descriptor)

        backend = getattr(self, "backend", None)
        native_input_worker = getattr(self, "native_input_worker", None)
        return {
            "backend_running": bool(backend is not None and backend.isRunning()),
            "native_input_worker_running": bool(
                native_input_worker is not None and native_input_worker.isRunning()
            )
            if native_input_worker is not None and hasattr(native_input_worker, "isRunning")
            else bool(getattr(native_input_worker, "running", False)),
            "keyboard_listener_alive": self._listener_is_alive(getattr(self, "keyboard_listener", None)),
            "mouse_listener_alive": self._listener_is_alive(getattr(self, "mouse_listener", None)),
            "timer_states": timer_states,
            "runtime_timers": runtime_timer_states,
            "overlay_visible": overlay_states,
            "alive_threads": alive_threads,
            "background_threads": background_threads,
            "dummy_threads": dummy_threads,
        }

    def _log_shutdown_snapshot(self, stage: str) -> dict:
        snapshot = self._collect_shutdown_snapshot()
        logger.info(
            "Shutdown %s | backend_running=%s native_input_worker_running=%s keyboard_listener_alive=%s mouse_listener_alive=%s",
            stage,
            snapshot["backend_running"],
            snapshot["native_input_worker_running"],
            snapshot["keyboard_listener_alive"],
            snapshot["mouse_listener_alive"],
        )
        logger.info(
            "Shutdown %s | timer_states=%s runtime_timers=%s overlay_visible=%s",
            stage,
            snapshot["timer_states"],
            snapshot["runtime_timers"],
            snapshot["overlay_visible"],
        )
        logger.info(
            "Shutdown %s | alive_threads=%s",
            stage,
            snapshot["alive_threads"],
        )
        if snapshot["dummy_threads"]:
            logger.warning(
                "Shutdown %s | dummy_threads=%s | source=alien/native callback thread, likely pynput or another native hook callback",
                stage,
                snapshot["dummy_threads"],
            )
        return snapshot

    def shutdown_application(self):
        if self._is_shutting_down:
            logger.info("Shutdown skipped: already in progress")
            return None
        self._is_shutting_down = True
        self._shutdown_in_progress = True
        logger.info("Shutdown started")
        try:
            self._log_shutdown_snapshot("pre-cleanup")
            timer_attrs = (
                "_layout_sync_timer",
                "_hover_hint_timer",
                "_bottom_action_status_timer",
            )
            for timer_name in timer_attrs:
                timer = getattr(self, timer_name, None)
                if timer is None:
                    continue
                try:
                    timer.stop()
                    logger.info("Stopped UI timer: %s", timer_name)
                except Exception:
                    logger.exception("Failed stopping UI timer: %s", timer_name)

            for timer in getattr(self, "_runtime_timers", []):
                try:
                    timer.stop()
                    logger.info("Stopped runtime handle: %s", timer.__class__.__name__)
                except Exception:
                    logger.exception("Failed stopping runtime handle: %s", timer)

            for listener in (getattr(self, "keyboard_listener", None), getattr(self, "mouse_listener", None)):
                try:
                    if listener is not None and hasattr(listener, "stop_listening"):
                        logger.info("Stopping listener: %s", listener.__class__.__name__)
                        listener.stop_listening()
                except Exception:
                    logger.exception("Failed stopping listener: %s", listener)
            self._log_listener_native_sources()
            self._cleanup_dummy_threads(purge_stale=True)
            native_input_worker = getattr(self, "native_input_worker", None)
            if native_input_worker is not None:
                try:
                    logger.info("Stopping native input worker")
                    if hasattr(native_input_worker, "running"):
                        native_input_worker.running = False
                    if hasattr(native_input_worker, "stop"):
                        native_input_worker.stop()
                    if hasattr(native_input_worker, "wait"):
                        native_input_worker.wait(75)
                except Exception:
                    logger.exception("Failed stopping native input worker")

            if getattr(self, "backend", None) is not None:
                try:
                    backend_wait_ms = 1200
                    logger.info("Stopping backend thread")
                    self.backend.stop()
                    logger.info("Waiting backend thread for %sms", backend_wait_ms)
                    self.backend.wait(backend_wait_ms)
                    if self.backend.isRunning():
                        logger.warning("backend thread did not stop within final timeout")
                    else:
                        logger.info("backend thread stopped")
                except Exception:
                    logger.exception("Failed stopping backend thread")

            if hasattr(self, "tray_manager") and self.tray_manager:
                try:
                    logger.info("Hiding tray icon")
                    self.tray_manager.hide()
                    if hasattr(self.tray_manager, "tray_icon") and self.tray_manager.tray_icon:
                        self.tray_manager.tray_icon.deleteLater()
                    self.tray_manager = None
                except Exception:
                    logger.exception("Failed hiding tray icon")

            for overlay_name in ("game_overlay", "crosshair"):
                self._dispose_overlay(overlay_name)
                logger.info("Closed overlay: %s", overlay_name)
            self._cleanup_dummy_threads(purge_stale=True)
            final_snapshot = self._log_shutdown_snapshot("post-cleanup")
            if final_snapshot["background_threads"]:
                logger.warning(
                    "Background threads still alive after cleanup timeout: %s",
                    final_snapshot["background_threads"],
                )
            else:
                logger.info("all threads exited")
            logger.info("Shutdown completed")
            return final_snapshot
        except Exception:
            logger.exception("Shutdown failed")
            return None

    def update_ads_display(self, mode: str):
        """Hiển thị trạng thái hành động ở thanh dưới."""
        if hasattr(self, 'btn_adsmode') and self.btn_adsmode:
            self.btn_adsmode.setText(mode.upper())
        self.update_ads_status_style(mode.upper())
        # Đã làm sạch chú thích lỗi mã hóa.
        # Đã làm sạch chú thích lỗi mã hóa.
        if hasattr(self, 'crosshair') and self.crosshair:
            self.crosshair.set_ads_mode(mode.upper())

    

    
    def toggle_ads_mode(self):
        """Toggle ADS Mode between HOLD and CLICK"""
        current = self.btn_adsmode.text()
        if current == "HOLD":
            new_mode = "CLICK"
        else:
            new_mode = "HOLD"
        
        self.btn_adsmode.setText(new_mode)
        self.update_ads_status_style(new_mode)
        
        # Save to settings
        try:
            settings = SettingsManager()
            settings.set("ads_mode", new_mode)
        except Exception as e:
            print(f"[ERROR] Failed to save ADS mode: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")






    def minimize_to_taskbar(self):
        self.hide_to_tray()

    def hide_to_tray(self):
        if not hasattr(self, "tray_manager") or self.tray_manager is None:
            self.tray_manager = TrayManager(self)
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.show()
        self.hide()
        QApplication.processEvents()
        logger.info("window minimized to tray")
        if hasattr(self, 'tray_manager') and self.tray_manager and self.tray_manager.tray_icon:
            self.tray_manager.tray_icon.showMessage(
                "Macro Di88",
                "Ứng dụng đã được đưa xuống khay hệ thống.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def handle_close_action(self):
        choice = AppNoticeDialog.custom_choice(
            self, 
            "Đóng ứng dụng", 
            "Bạn muốn đưa app xuống tray hay tắt hẳn?",
            buttons=("Tắt", "Xuống Tray", "Hủy")
        )
        
        if choice == "Xuống Tray":
            self.hide_to_tray()
        elif choice == "Tắt":
            self._perform_shutdown()

    def _perform_shutdown(self):
        logger.info("Close action: quit application")
        final_snapshot = self.shutdown_application()
        if final_snapshot and (
            final_snapshot["background_threads"]
            or final_snapshot["backend_running"]
            or final_snapshot["keyboard_listener_alive"]
            or final_snapshot["mouse_listener_alive"]
            or final_snapshot["native_input_worker_running"]
        ):
            logger.warning("Incomplete shutdown detected; force-exit fallback remains armed")
            fallback_timer = threading.Timer(2.0, lambda: os._exit(0))
            fallback_timer.daemon = True
            fallback_timer.start()
        app = QApplication.instance()
        if app:
            # Đóng mọi top-level Qt object trước khi thoát event loop để tránh treo app.exec().
            for widget in list(app.topLevelWidgets()):
                if widget is self:
                    continue
                try:
                    widget.hide()
                    widget.close()
                except Exception:
                    logger.exception("Failed closing top-level widget during shutdown: %s", widget)
            try:
                self.hide()
                app.processEvents()
            except Exception:
                logger.exception("Failed closing Qt windows during shutdown")
            logger.info("Requesting Qt application exit")
            app.exit(0)

    def showEvent(self, event):
        """Force UI update when window is shown"""
        super().showEvent(event)
        if not getattr(self, "_did_initial_center", False):
            QTimer.singleShot(0, self.fit_window_to_screen)
            self._did_initial_center = True
        if hasattr(self, 'crosshair') and self.crosshair and self.crosshair.isVisible():
            self.crosshair.hide()
            self._crosshair_hidden_for_window = True
        if hasattr(self, 'last_data') and self.last_data:
             self.update_ui_state(self.last_data)

    def hideEvent(self, event):
        super().hideEvent(event)
        if (
            getattr(self, "_crosshair_hidden_for_window", False)
            and hasattr(self, 'btn_cross_toggle')
            and self.btn_cross_toggle.isChecked()
            and hasattr(self, 'crosshair')
            and self.crosshair
        ):
            self.crosshair.show()
            self.crosshair.raise_()
        self._crosshair_hidden_for_window = False

    def update_ui_state(self, data):
        # Cache data for showEvent
        self.last_data = data

        aim_state = data.get("aim", {}) if isinstance(data, dict) else {}
        if hasattr(self, "btn_aim_status"):
            self.update_aim_status_style(bool(aim_state.get("aim_assist", False)))
            fps_raw = aim_state.get("fps")
            inf_raw = aim_state.get("inference_ms")
            inference_backend_raw = aim_state.get("inference_backend", "Not loaded")
            inference_backend = str(inference_backend_raw or "Not loaded")
            runtime_source = str(aim_state.get("runtime_source", "") or "")
            native_error = str(aim_state.get("native_error", "") or "")
            if inference_backend.strip().lower() in {"not loaded", "booting", "idle"}:
                inference_backend = "Chưa nạp"
            fps_text = "FPS : --" if fps_raw in (None, "", "N/A") else f"FPS : {float(fps_raw):.1f}"
            inf_text = "INF : --" if inf_raw in (None, "", "N/A") else f"INF : {float(inf_raw):.1f} MS"
            self.update_aim_metric_style(self.lbl_aim_fps, fps_text, "#8dffb1")
            self.update_aim_metric_style(self.lbl_aim_inf, inf_text, "#ffd7a1")
            if hasattr(self, "lbl_aim_backend_info") and self.lbl_aim_backend_info:
                self.lbl_aim_backend_info.setText(f"Backend: {inference_backend}")
            if hasattr(self, "lbl_aim_model_status_meta") and self.lbl_aim_model_status_meta:
                self.lbl_aim_model_status_meta.setText(self._format_aim_runtime_source_text(runtime_source))
                runtime_color = "#ff8080" if "error" in runtime_source.lower() else "#8dffb1"
                self.lbl_aim_model_status_meta.setStyleSheet(f"""
                    QLabel {{
                        color: {runtime_color};
                        font-size: 10px;
                        font-weight: 800;
                        background: #1b1b1b;
                        border: 1px solid #3a3a3a;
                        border-radius: 5px;
                        padding: 2px 6px;
                    }}
                """)
                self.lbl_aim_model_status_meta.setToolTip(native_error)
            if hasattr(self, "lbl_aim_runtime_meta") and self.lbl_aim_runtime_meta:
                self.lbl_aim_runtime_meta.setText(self._format_aim_backend_meta_text(inference_backend, runtime_source))
                self.lbl_aim_runtime_meta.setToolTip(native_error)
            if hasattr(self, "lbl_aim_fps") and self.lbl_aim_fps:
                capture_ms = aim_state.get("capture_ms", 0.0)
                source_fps = aim_state.get("source_fps", 0.0)
                preprocess_ms = aim_state.get("preprocess_ms", 0.0)
                inference_ms = aim_state.get("inference_ms", 0.0)
                postprocess_ms = aim_state.get("postprocess_ms", 0.0)
                loop_ms = aim_state.get("loop_ms", 0.0)
                tooltip = (
                    f"Source FPS: {float(source_fps):.1f}\n"
                    f"Capture: {float(capture_ms):.1f} ms\n"
                    f"Preprocess: {float(preprocess_ms):.1f} ms\n"
                    f"Inference: {float(inference_ms):.1f} ms\n"
                    f"Postprocess: {float(postprocess_ms):.1f} ms\n"
                    f"Loop: {float(loop_ms):.1f} ms"
                )
                self.lbl_aim_fps.setToolTip(tooltip)
                self.lbl_aim_inf.setToolTip(tooltip)
        self.update_home_snapshot()
        self.update_aim_visual_overlay(data)
        
        # ALWAYS UPDATE INTERNAL STATE
        # Helper: Clean Text (No brackets, UPPER None)
        def fmt(val):
            return "NONE" if val == "None" else val
            
        g1 = data["gun1"]
        g2 = data["gun2"]
        active_slot = data.get("active_slot", 1)
        active_gun = g1 if active_slot == 1 else g2
        display_ai_status = data.get("ai_status", "HIBERNATE")
        self.update_macro_style(not bool(data.get("paused", False)))

        macro_signature = (
            tuple(sorted(g1.items())) if isinstance(g1, dict) else g1,
            tuple(sorted(g2.items())) if isinstance(g2, dict) else g2,
            data.get("stance"),
            active_slot,
            bool(data.get("paused", False)),
            bool(data.get("firing", False)),
            display_ai_status,
        )

        weapon_name = fmt(active_gun["name"])
        scope_name = fmt(active_gun["scope"])
        overlay_signature = (
            weapon_name,
            scope_name,
            data["stance"],
            active_gun.get("grip", "NONE"),
            active_gun.get("accessories", "NONE"),
            bool(data.get("paused", False)),
            bool(data.get("firing", False)),
            display_ai_status,
        )
        
        # Map scope name to X1...X8 for Key lookup
        # Đã làm sạch chú thích lỗi mã hóa.
        def get_scope_display(s):
            s = str(s).lower()
            is_kh = "kh" in s
            digit = "1"
            if "8" in s: digit = "8"
            elif "6" in s: digit = "6"
            elif "4" in s: digit = "4"
            elif "3" in s: digit = "3"
            elif "2" in s: digit = "2"
            
            prefix = "ScopeKH" if is_kh else "Scope"
            return prefix + digit
            
        self.current_scope_key = get_scope_display(scope_name)
        self.current_weapon = weapon_name

        # OPTIMIZATION: If window is hidden, only update the overlay, skip main UI labels
        if not self.isVisible():
            if self._overlay_enabled and self._last_game_overlay_signature != overlay_signature:
                overlay = self._ensure_game_overlay()
                if not overlay.isVisible():
                    overlay.show()
                    logger.info("game overlay shown")
                self._last_game_overlay_signature = overlay_signature
                overlay.update_status(
                    weapon_name,
                    scope_name,
                    data["stance"],
                    grip=active_gun.get("grip", "NONE"),
                    muzzle=active_gun.get("accessories", "NONE"),
                    is_paused=data.get("paused", False),
                    is_firing=data.get("firing", False),
                    ai_status=display_ai_status
                )
                logger.info("game overlay updated")
            self._last_macro_ui_signature = macro_signature
            return

        if self._last_macro_ui_signature == macro_signature:
            return
        self._last_macro_ui_signature = macro_signature

        gun_widget_attrs = (
            "lbl_g1_name", "lbl_g1_scope", "lbl_g1_grip", "lbl_g1_muzzle",
            "lbl_g2_name", "lbl_g2_scope", "lbl_g2_grip", "lbl_g2_muzzle",
            "panel_g1", "panel_g2",
        )
        if not all(hasattr(self, attr) for attr in gun_widget_attrs):
            return


        # Update Gun 1 UI
        g1_name = fmt(g1["name"])
        g1_scope = fmt(g1["scope"])
        g1_grip = fmt(g1["grip"])
        g1_muzzle = fmt(g1["accessories"])
        if self.lbl_g1_name.text() != g1_name:
            self.lbl_g1_name.setText(g1_name)
        if self.lbl_g1_scope.text() != g1_scope:
            self.lbl_g1_scope.setText(g1_scope)
        if self.lbl_g1_grip.text() != g1_grip:
            self.lbl_g1_grip.setText(g1_grip)
        if self.lbl_g1_muzzle.text() != g1_muzzle:
            self.lbl_g1_muzzle.setText(g1_muzzle)
        
        # Update Gun 2 UI
        g2_name = fmt(g2["name"])
        g2_scope = fmt(g2["scope"])
        g2_grip = fmt(g2["grip"])
        g2_muzzle = fmt(g2["accessories"])
        if self.lbl_g2_name.text() != g2_name:
            self.lbl_g2_name.setText(g2_name)
        if self.lbl_g2_scope.text() != g2_scope:
            self.lbl_g2_scope.setText(g2_scope)
        if self.lbl_g2_grip.text() != g2_grip:
            self.lbl_g2_grip.setText(g2_grip)
        if self.lbl_g2_muzzle.text() != g2_muzzle:
            self.lbl_g2_muzzle.setText(g2_muzzle)

        # Remove active slot glow - Use static neutral colors
        if self.panel_g1.property("_macro_style") != "neutral":
            self.panel_g1.setStyleSheet(
                "QFrame#P1 { "
                "background: transparent; "
                "border: 1px solid rgba(255, 255, 255, 0.04); "
                "border-radius: 8px; }"
            )
            self.panel_g1.setProperty("_macro_style", "neutral")
        if self.panel_g2.property("_macro_style") != "neutral":
            self.panel_g2.setStyleSheet(
                "QFrame#P2 { "
                "background: transparent; "
                "border: 1px solid rgba(255, 255, 255, 0.04); "
                "border-radius: 8px; }"
            )
            self.panel_g2.setProperty("_macro_style", "neutral")

        def item_style(lbl, val):
            style_key = "none" if val == "NONE" else "value"
            if lbl.property("_macro_item_style") == style_key:
                return
            if style_key == "none":
                lbl.setStyleSheet(
                    "color: #727b86; font-size: 12px; font-weight: 600; "
                    "background: transparent; border: none; padding: 1px 0;"
                )
            else:
                lbl.setStyleSheet(
                    "color: #eef2f6; font-size: 12px; font-weight: 600; "
                    "background: transparent; border: none; padding: 1px 0;"
                )
            lbl.setProperty("_macro_item_style", style_key)

        item_style(self.lbl_g1_name, g1_name)
        item_style(self.lbl_g1_scope, g1_scope)
        item_style(self.lbl_g1_grip, g1_grip)
        item_style(self.lbl_g1_muzzle, g1_muzzle)
        
        item_style(self.lbl_g2_name, g2_name)
        item_style(self.lbl_g2_scope, g2_scope)
        item_style(self.lbl_g2_grip, g2_grip)
        item_style(self.lbl_g2_muzzle, g2_muzzle)
        
        # Update Overlay
        if self._overlay_enabled and self._last_game_overlay_signature != overlay_signature:
            overlay = self._ensure_game_overlay()
            if not overlay.isVisible():
                overlay.show()
                logger.info("game overlay shown")
            self._last_game_overlay_signature = overlay_signature
            overlay.update_status(
                weapon_name,
                scope_name,
                data["stance"],
                grip=active_gun.get("grip", "NONE"),
                muzzle=active_gun.get("accessories", "NONE"),
                is_paused=data.get("paused", False),
                is_firing=data.get("firing", False),
                ai_status=display_ai_status
            )
            logger.info("game overlay updated")

        stance = data["stance"]
        s_lower = str(stance).lower()
        
        # Đã làm sạch chú thích lỗi mã hóa.
        vn_stance = "Đứng"
        if "crouch" in s_lower: vn_stance = "Ngồi"
        elif "prone" in s_lower: vn_stance = "Nằm"
        elif "stand" in s_lower: vn_stance = "Đứng"
        else: vn_stance = stance 
        
        # The user requested No color change on stance depending on slot or stance type, just a fixed color
        color = "#aaaaaa"
        
        self.update_stance_status_style(f"TƯ THẾ : {(vn_stance or 'ĐỨNG').upper()}", color=color)



    # --- DRAG LOGIC (SMOOTH PYQT DRAG) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()
            # Đã làm sạch chú thích lỗi mã hóa.
            if hasattr(self, 'container'):
                 self.container.setGraphicsEffect(None)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'dragPos') and self.dragPos is not None:
            # Đã làm sạch chú thích lỗi mã hóa.
            new_pos = self.pos() + event.globalPosition().toPoint() - self.dragPos
            self.move(new_pos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        # Đã làm sạch chú thích lỗi mã hóa.
        if hasattr(self, 'container'):
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0, 5)
            self.container.setGraphicsEffect(shadow)
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_window_width_to_frame()
        self.position_all_macro_titles()
        self.sync_macro_half_boxes()
    


    def show_message(self, title, msg):
        """Show Notification (Tray Bubble or Popup)"""
        if hasattr(self, 'tray_manager'):
            self.tray_manager.tray_icon.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 2000)
        else:
            # Fallback (Modal)
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setText(msg)
            box.setIcon(QMessageBox.Icon.Information)
            box.show()
            QTimer.singleShot(2000, box.close) # Auto-close

    def toggle_window_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.restore_window()
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)

    def toggle_crosshair_visibility(self):
        checked = not self.btn_cross_toggle.isChecked()
        self.btn_cross_toggle.setChecked(checked)
        self.toggle_crosshair(checked)

    def restore_window(self):
        self.setWindowState(
            self.windowState()
            & ~Qt.WindowState.WindowMinimized
        )
        if hasattr(self, "tray_manager") and self.tray_manager:
            self.tray_manager.hide()
        self.showNormal()
        self.setFixedWidth(self.WINDOW_WIDTH)
        self.raise_()
        self.activateWindow()
        logger.info("window restored from tray")
        self.position_aim_model_notice()
        self._layout_sync_timer.start(120)
        if hasattr(self, "last_data"):
            self.update_aim_visual_overlay(self.last_data)

    def center_on_screen(self):
        screen = self.screen()
        if screen is None:
            app = QApplication.instance()
            screen = app.primaryScreen() if app else None
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        x = available.x() + max(0, (available.width() - frame.width()) // 2)
        y = available.y() + max(0, (available.height() - frame.height()) // 2)
        self.move(x, y)

    def update_aim_visual_overlay(self, data):
        aim_state = data.get("aim", {}) if isinstance(data, dict) else {}
        show_fov = bool(hasattr(self, "aim_chk_show_fov") and self.aim_chk_show_fov.isChecked())
        show_detect = bool(hasattr(self, "aim_chk_show_detect") and self.aim_chk_show_detect.isChecked())
        fov_size = self.aim_slider_fov.value() if hasattr(self, "aim_slider_fov") and self.aim_slider_fov else 300
        toggles = aim_state.get("toggles", {}) if isinstance(aim_state, dict) and isinstance(aim_state.get("toggles", {}), dict) else {}
        sliders = aim_state.get("sliders", {}) if isinstance(aim_state, dict) and isinstance(aim_state.get("sliders", {}), dict) else {}
        colors = aim_state.get("colors", {}) if isinstance(aim_state, dict) and isinstance(aim_state.get("colors", {}), dict) else {}
        fov_color = colors.get("FOV Color")
        detect_color = colors.get("Detected Player Color")
        if not fov_color and hasattr(self, "aim_color_controls"):
            button = self.aim_color_controls.get("FOV Color")
            fov_color = button.property("color_value") if button is not None else None
        if not detect_color and hasattr(self, "aim_color_controls"):
            button = self.aim_color_controls.get("Detected Player Color")
            detect_color = button.property("color_value") if button is not None else None

        def _toggle_value(key: str, default: bool = False) -> bool:
            checkbox = getattr(self, "aim_toggle_controls", {}).get(key)
            if checkbox is not None:
                return bool(checkbox.isChecked())
            return bool(toggles.get(key, default))

        def _slider_value(key: str, default):
            control = getattr(self, "aim_listing_controls", {}).get(key)
            if control and control.get("slider") is not None:
                return self.aim_test_slider_to_value(control["spec"], control["slider"].value())
            return sliders.get(key, default)

        backend = getattr(self, "backend", None)
        if backend is not None and hasattr(backend, "update_aim_visual_settings"):
            backend.update_aim_visual_settings(
                {
                    "show_fov": show_fov,
                    "show_detect": show_detect,
                    "show_confidence": _toggle_value("Show AI Confidence", False),
                    "show_tracers": _toggle_value("Show Tracers", False),
                    "fov_size": fov_size,
                    "fov_color": fov_color,
                    "detect_color": detect_color,
                    "border_thickness": float(_slider_value("Border Thickness", 2.0)),
                    "opacity": float(_slider_value("Opacity", 1.0)),
                }
            )

    def closeEvent(self, event):
        """Cleanup resources on close, including detached overlays."""
        if self._is_shutting_down:
            logger.info("closeEvent accepted during shutdown")
            event.accept()
            return

        logger.info("closeEvent redirected to handle_close_action")
        event.ignore()
        self.handle_close_action()
