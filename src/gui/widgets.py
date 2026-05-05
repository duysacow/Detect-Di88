from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# Nút điều hướng chính để đổi page trong stacked widget.
class MainNavButton(QPushButton):
    def __init__(self, text: str, page_name: str) -> None:
        super().__init__(text)
        self.page_name = page_name
        self.setObjectName("MainNavButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setMinimumHeight(38)
        self.setProperty("active", "false")

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


# Card dùng chung cho panel UI.
def create_panel_card(object_name: str) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame()
    card.setObjectName(object_name)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(10)
    return card, layout


# Tạo một hàng setting đơn giản cho UI placeholder.
def create_labeled_row(label_text: str, control: QWidget) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    label = QLabel(label_text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setProperty("role", "setting-label")
    label.setFixedWidth(110)

    layout.addWidget(label)
    layout.addWidget(control, 1)
    return row


# Tạo một slider row cho Aim tab placeholder.
def create_slider_block(label_text: str, value: int) -> tuple[QWidget, QSlider]:
    block = QWidget()
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    label = QLabel(label_text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setProperty("role", "setting-label")
    layout.addWidget(label)

    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, 100)
    slider.setValue(value)

    value_label = QLabel(str(value))
    value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    value_label.setFixedWidth(36)
    value_label.setObjectName("AimSliderValue")

    row_layout.addWidget(slider, 1)
    row_layout.addWidget(value_label)
    layout.addWidget(row)
    return block, slider


# Combo placeholder cho Aim tab.
def create_combo(items: list[str]) -> QComboBox:
    combo = QComboBox()
    combo.addItems(items)
    return combo
