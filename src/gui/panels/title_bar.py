from __future__ import annotations

from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from src.core.path_utils import get_resource_path


# Thanh tiêu đề chính của cửa sổ.
class TitleBarPanel(QFrame):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("TitleBar")
        self.setFixedHeight(30)
        self.setStyleSheet(
            """
            QFrame#TitleBar {
                background: transparent;
                border: none;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }
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
            QLabel#AppTitle {
                color: #e9edf2;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0px;
                background: transparent;
                border: none;
            }
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        btn_min = QPushButton("-")
        btn_min.setObjectName("MinBtn")
        btn_min.setFixedSize(20, 20)
        btn_min.clicked.connect(window.hide)

        btn_close = QPushButton("X")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(20, 20)
        btn_close.clicked.connect(window.close)

        title = QLabel("Macro & Aim By Di88")
        title.setObjectName("AppTitle")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(4)
        glow.setColor(QColor(0, 0, 0, 200))
        glow.setOffset(1, 1)
        title.setGraphicsEffect(glow)

        logo = QLabel()
        icon_path = get_resource_path("di88vp.ico")
        logo.setPixmap(QIcon(icon_path).pixmap(22, 22))
        logo.setContentsMargins(0, 0, 5, 0)

        left_placeholder = QWidget()
        left_placeholder.setFixedWidth(45)

        center_wrap = QWidget()
        center_layout = QHBoxLayout(center_wrap)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(logo)
        center_layout.addWidget(title)

        right_wrap = QWidget()
        right_wrap.setFixedWidth(45)
        right_layout = QHBoxLayout(right_wrap)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(btn_min)
        right_layout.addWidget(btn_close)

        layout.addWidget(left_placeholder, 0)
        layout.addStretch(1)
        layout.addWidget(center_wrap, 0)
        layout.addStretch(1)
        layout.addWidget(right_wrap, 0)

        self.mousePressEvent = window.mousePressEvent
        self.mouseMoveEvent = window.mouseMoveEvent
