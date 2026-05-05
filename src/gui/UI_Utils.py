from PyQt6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame)
from PyQt6.QtCore import Qt

def create_panel(title, color_hex, obj_name):
    """Tạo một khung Panel với tiêu đề và màu sắc định sẵn"""
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
    """Thành phần của cột Settings: Label bên trái, Button bên phải"""
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
    """Thành phần của cột Gun Info: Label tĩnh bên trái, Label dữ liệu bên phải"""
    l = QLabel(f"{label}")
    l.setProperty("class", "RowLabel")
    
    val = QLabel("NONE")
    val.setProperty("class", "ValueLabel")
    val.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    grid.addWidget(l, row, 0)
    grid.addWidget(val, row, 1)
    
    return val
