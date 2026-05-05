from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget


# Trang Macro/Recoil giữ lại toàn bộ widget và bind hiện tại.
class RecoilPanel(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("RecoilPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        window.build_recoil_page(layout)
