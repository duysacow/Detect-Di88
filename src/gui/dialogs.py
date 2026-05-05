from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QWidget


# Hộp thoại chuẩn cho GUI cũ để giữ tiêu đề/nút nhất quán.
def show_info(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(message)
    box.setWindowFlags(box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    box.exec()


# Hộp thoại cảnh báo chuẩn cho GUI cũ.
def show_warning(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(message)
    box.setWindowFlags(box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    box.exec()


# Hộp thoại lỗi chuẩn cho GUI cũ.
def show_critical(parent: QWidget | None, title: str, message: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Critical)
    box.setWindowTitle(title)
    box.setText(message)
    box.setWindowFlags(box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    box.exec()


# Hộp thoại xác nhận chuẩn để không lặp code QMessageBox trong window.
def ask_confirmation(parent: QWidget | None, title: str, message: str) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Question)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    box.setDefaultButton(QMessageBox.StandardButton.No)
    box.setWindowFlags(box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    return box.exec() == int(QMessageBox.StandardButton.Yes)
