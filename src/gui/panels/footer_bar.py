from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QWidget


# Thanh hành động cuối cửa sổ cho save/reset.
class FooterBarPanel(QFrame):
    def __init__(self, window) -> None:
        super().__init__()
        self.setObjectName("BottomActionBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        left_wrap = QWidget()
        left_layout = QHBoxLayout(left_wrap)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addStretch(1)

        btn_default = QPushButton("CÀI ĐẶT GỐC")
        btn_default.setObjectName("DefaultBtn")
        btn_default.setFixedHeight(34)
        btn_default.setMinimumWidth(180)
        btn_default.clicked.connect(window.reset_to_defaults)
        left_layout.addWidget(btn_default)

        right_wrap = QWidget()
        right_layout = QHBoxLayout(right_wrap)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        btn_save = QPushButton("LƯU CÀI ĐẶT")
        btn_save.setObjectName("SaveBtn")
        btn_save.setFixedHeight(34)
        btn_save.setMinimumWidth(180)
        btn_save.clicked.connect(window.save_config)
        right_layout.addStretch(1)
        right_layout.addWidget(btn_save)

        layout.addWidget(left_wrap, 1)
        layout.addStretch(1)
        layout.addWidget(right_wrap, 1)
