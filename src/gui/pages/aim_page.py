from __future__ import annotations

from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.gui.widgets import (
    create_combo,
    create_labeled_row,
    create_panel_card,
    create_slider_block,
)


# Trang AIM BOT chỉ dựng UI, chưa bind logic.
class AimPage(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("AimPage")
        self.setStyleSheet("background: #1b1b1b; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_main_grid(), 1)

    def _build_header(self):
        card, card_layout = create_panel_card("PageBanner")
        eyebrow = QLabel("DI88 AIM")
        eyebrow.setObjectName("PageBannerEyebrow")
        title = QLabel("TRUNG TÂM AIM")
        title.setObjectName("PageBannerTitle")
        subtitle = QLabel("Aim UI placeholder")
        subtitle.setObjectName("PageBannerSubtitle")
        card_layout.addWidget(eyebrow)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        return card

    def _build_main_grid(self):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        top_row = QWidget()
        top_layout = QVBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        model_card, model_layout = create_panel_card("AimSectionCard")
        model_layout.addWidget(self._section_title("Model"))
        model_layout.addWidget(create_labeled_row("MODEL", create_combo(["Default", "Precision", "Tracking"])))
        top_layout.addWidget(model_card)

        capture_card, capture_layout = create_panel_card("AimSectionCard")
        capture_layout.addWidget(self._section_title("Phương Thức Chụp"))
        capture_layout.addWidget(create_labeled_row("CAPTURE", create_combo(["DirectX", "GDI+"])))
        top_layout.addWidget(capture_card)

        settings_card, settings_layout = create_panel_card("AimSectionCard")
        settings_layout.addWidget(self._section_title("Cài Đặt"))
        for label_text, value in [("Vùng FOV", 35), ("Ngưỡng Tin Cậy AI", 45), ("Tốc Độ Chụp (FPS)", 60)]:
            block, _ = create_slider_block(label_text, value)
            settings_layout.addWidget(block)
        top_layout.addWidget(settings_card)

        shortcuts_card, shortcuts_layout = create_panel_card("AimSectionCard")
        shortcuts_layout.addWidget(self._section_title("Phím Tắt"))
        for label_text, key_text in [("Bật/Tắt Aim", "F8"), ("Phím Aim", "RIGHT MOUSE"), ("Bật/Tắt Trigger", "F7")]:
            btn = QPushButton(key_text)
            btn.setProperty("role", "setting-btn")
            btn.setFixedHeight(26)
            shortcuts_layout.addWidget(create_labeled_row(label_text, btn))
        top_layout.addWidget(shortcuts_card)

        smooth_card, smooth_layout = create_panel_card("AimSectionCard")
        smooth_layout.addWidget(self._section_title("Độ Nhạy / Độ Mượt"))
        for label_text, value in [("Độ Nhạy Chuột", 80), ("Độ Mượt", 50)]:
            block, _ = create_slider_block(label_text, value)
            smooth_layout.addWidget(block)
        top_layout.addWidget(smooth_card)

        listing_card, listing_layout = create_panel_card("AimSectionCard")
        listing_layout.addWidget(self._section_title("Danh Sách Liệt Kê"))
        for label_text, value in [("Head", 60), ("Chest", 75), ("Body", 85)]:
            block, _ = create_slider_block(label_text, value)
            listing_layout.addWidget(block)
        top_layout.addWidget(listing_card)

        display_card, display_layout = create_panel_card("AimSectionCard")
        display_layout.addWidget(self._section_title("Hiển Thị"))
        display_layout.addWidget(create_labeled_row("OVERLAY", create_combo(["FOV", "Detect", "All"])))
        top_layout.addWidget(display_card)

        advanced_card, advanced_layout = create_panel_card("AimSectionCard")
        advanced_layout.addWidget(self._section_title("Tùy Chọn Nâng Cao"))
        advanced_layout.addWidget(create_labeled_row("MODE", create_combo(["Disabled", "Safe Placeholder"])))
        disabled = QLabel("Disabled")
        disabled.setObjectName("AimDisabledLabel")
        advanced_layout.addWidget(disabled)
        top_layout.addWidget(advanced_card)

        layout.addWidget(top_row)
        wrapper.setDisabled(True)
        return wrapper

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("AimSectionTitle")
        return label
