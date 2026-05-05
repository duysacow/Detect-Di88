from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.gui.widgets import (
    create_combo,
    create_labeled_row,
    create_panel_card,
    create_slider_block,
)


# Trang Aim chỉ dựng UI placeholder, chưa bind logic.
class AimPanel(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("AimPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        hero_card, hero_layout = create_panel_card("AimHeroCard")
        title = QLabel("AIM ASSIST")
        title.setObjectName("AimHeroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("Coming Soon")
        subtitle.setObjectName("AimHeroSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addStretch()
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addStretch()
        layout.addWidget(hero_card)

        control_card, control_layout = create_panel_card("AimControlCard")
        control_layout.addWidget(
            create_labeled_row(
                "MODEL", create_combo(["Default", "Precision", "Tracking"])
            )
        )

        bind_button = QPushButton("ALT")
        bind_button.setProperty("class", "SettingBtn")
        bind_button.setFixedHeight(26)
        control_layout.addWidget(create_labeled_row("KEY BIND", bind_button))

        for label_text, value in [
            ("SMOOTH", 35),
            ("FOV", 50),
            ("SPEED", 40),
        ]:
            block, _ = create_slider_block(label_text, value)
            control_layout.addWidget(block)

        status = QLabel("Disabled")
        status.setObjectName("AimDisabledLabel")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(status)
        layout.addWidget(control_card, 1)

        self.setDisabled(True)
