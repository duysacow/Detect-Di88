from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.gui.widgets import MainNavButton


# Sidebar trái chứa brand card và navigation page chính.
class SidebarPanel(QFrame):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("MainSidebar")
        self.setFixedWidth(160)
        self.setStyleSheet(
            """
            QFrame#MainSidebar {
                background: #121212;
                border: 1px solid #313131;
                border-radius: 14px;
            }
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
            QLabel#NavBrandTitle {
                color: #f4f7fb;
                font-size: 16px;
                font-weight: 900;
                letter-spacing: 0px;
                background: transparent;
                border: none;
            }
            QLabel#NavBrandSubtitle {
                color: #78dfff;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
            QFrame#NavBrandLine {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d8ff, stop:1 #2f4dff);
                border: none;
                border-radius: 1px;
            }
            QLabel#NavVersionLabel {
                color: #6e6e6e;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }
            QPushButton#MainNavButton {
                background: #171717;
                color: #aeb7c2;
                border: 1px solid #2f3942;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 11px;
                font-weight: 900;
                text-align: left;
            }
            QPushButton#MainNavButton:hover {
                background: #1d232b;
                border: 1px solid #445567;
                color: #ffffff;
            }
            QPushButton#MainNavButton[active="true"] {
                background: #233447;
                border: 1px solid #4d6a88;
                color: #ffffff;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 14, 12, 14)
        layout.setSpacing(10)

        brand = QFrame()
        brand.setObjectName("NavBrandCard")
        brand.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(12, 12, 12, 10)
        brand_layout.setSpacing(4)

        title = QLabel("Di88 Control")
        title.setObjectName("NavBrandTitle")
        subtitle = QLabel("Macro & Aim")
        subtitle.setObjectName("NavBrandSubtitle")
        line = QFrame()
        line.setObjectName("NavBrandLine")
        line.setFixedHeight(2)

        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        brand_layout.addSpacing(2)
        brand_layout.addWidget(line)
        layout.addWidget(brand)
        layout.addSpacing(8)

        self.btn_home = MainNavButton("HOME", "home")
        self.btn_macro = MainNavButton("MACRO", "macro")
        self.btn_aim = MainNavButton("AIM BOT", "aim")

        self.btn_home.clicked.connect(lambda: window.set_active_page("home"))
        self.btn_macro.clicked.connect(lambda: window.set_active_page("macro"))
        self.btn_aim.clicked.connect(lambda: window.set_active_page("aim"))

        layout.addWidget(self.btn_home)
        layout.addWidget(self.btn_macro)
        layout.addWidget(self.btn_aim)
        layout.addStretch(1)

        version = QLabel("v2.0 DI88")
        version.setObjectName("NavVersionLabel")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

    def set_active(self, page_name: str) -> None:
        self.btn_home.set_active(page_name == "home")
        self.btn_macro.set_active(page_name == "macro")
        self.btn_aim.set_active(page_name == "aim")
