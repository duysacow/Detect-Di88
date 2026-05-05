from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.ui_utils import add_setting_row, create_data_row, create_panel


# Trang macro dùng lại bind macro/recoil hiện tại của app.
class MacroPage(QWidget):
    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self.setObjectName("MacroPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_header())
        self._build_status_bar(layout)
        self._build_detection_info(layout)
        self._build_sections(layout)
        layout.addStretch(1)

    def _build_header(self):
        card = QFrame()
        card.setObjectName("PageBanner")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(3)
        eyebrow = QLabel("DI88 MACRO")
        eyebrow.setObjectName("PageBannerEyebrow")
        title = QLabel("TRUNG TÂM MACRO")
        title.setObjectName("PageBannerTitle")
        subtitle = QLabel("Macro / Recoil Control")
        subtitle.setObjectName("PageBannerSubtitle")
        layout.addWidget(eyebrow)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return card

    def _build_status_bar(self, root_layout: QVBoxLayout) -> None:
        self.window.footer = QFrame()
        self.window.footer.setObjectName("MacroStatusPanel")
        self.window.footer.setFixedHeight(58)
        layout = QHBoxLayout(self.window.footer)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.window.btn_macro = QPushButton("MACRO : OFF")
        self.window.btn_macro.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.window.btn_macro.setFixedHeight(32)
        self.window.update_macro_style(False)

        self.window.lbl_stance = QLabel("TƯ THẾ : ĐỨNG")
        self.window.lbl_stance.setObjectName("StatusValueLabel")
        self.window.lbl_stance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window.lbl_stance.setFixedHeight(32)

        self.window.lbl_ads_status = QLabel("ADS : HOLD")
        self.window.lbl_ads_status.setObjectName("StatusValueLabel")
        self.window.lbl_ads_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.window.lbl_ads_status.setFixedHeight(32)

        layout.addWidget(self.window.btn_macro, 1)
        layout.addWidget(self.window.lbl_stance, 1)
        layout.addWidget(self.window.lbl_ads_status, 1)
        root_layout.addWidget(self.window.footer)

    def _build_detection_info(self, root_layout: QVBoxLayout) -> None:
        card = QFrame()
        card.setObjectName("DetectionInfoCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)
        title = QLabel("Thông Tin Súng")
        title.setObjectName("MacroSectionTitle")
        layout.addWidget(title)
        layout.addStretch(1)
        root_layout.addWidget(card)

    def _build_sections(self, root_layout: QVBoxLayout) -> None:
        columns = QHBoxLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setSpacing(10)

        left_col = QVBoxLayout()
        left_col.setContentsMargins(0, 0, 0, 0)
        left_col.setSpacing(10)
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(10)

        left_col.addWidget(self._build_guns_panel())
        left_col.addWidget(self._build_capture_panel())
        left_col.addWidget(self._build_usage_panel())

        right_col.addWidget(self._build_crosshair_panel())
        right_col.addWidget(self._build_bind_panel())
        right_col.addWidget(self._build_toggle_panel())
        right_col.addWidget(self._build_scope_panel())

        columns.addLayout(left_col, 1)
        columns.addLayout(right_col, 1)
        root_layout.addLayout(columns)

    def _card(self, object_name: str, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName(object_name)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        label = QLabel(title)
        label.setObjectName("MacroSectionTitle")
        layout.addWidget(label)
        return card, layout

    def _build_guns_panel(self):
        card, layout = self._card("MacroGunPanel", "Súng 1 / Súng 2")

        self.window.panel_g1, l_g1 = create_panel("GUN 1", "#FF4444", "P1")
        self.window.grid_g1 = QGridLayout()
        self.window.grid_g1.setSpacing(6)
        self.window.lbl_g1_name = create_data_row(self.window.grid_g1, 0, "Name")
        self.window.lbl_g1_scope = create_data_row(self.window.grid_g1, 1, "Scope")
        self.window.lbl_g1_grip = create_data_row(self.window.grid_g1, 2, "Grip")
        self.window.lbl_g1_muzzle = create_data_row(self.window.grid_g1, 3, "Muzz")
        l_g1.addLayout(self.window.grid_g1)
        layout.addWidget(self.window.panel_g1)

        self.window.panel_g2, l_g2 = create_panel("GUN 2", "#44FF44", "P2")
        self.window.grid_g2 = QGridLayout()
        self.window.grid_g2.setSpacing(6)
        self.window.lbl_g2_name = create_data_row(self.window.grid_g2, 0, "Name")
        self.window.lbl_g2_scope = create_data_row(self.window.grid_g2, 1, "Scope")
        self.window.lbl_g2_grip = create_data_row(self.window.grid_g2, 2, "Grip")
        self.window.lbl_g2_muzzle = create_data_row(self.window.grid_g2, 3, "Muzz")
        l_g2.addLayout(self.window.grid_g2)
        layout.addWidget(self.window.panel_g2)
        return card

    def _build_capture_panel(self):
        card, layout = self._card("MacroCapturePanel", "Chế Độ Chụp")
        row_capture = QHBoxLayout()
        lbl_cap = QLabel("CAPTURE")
        lbl_cap.setFixedWidth(100)
        lbl_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cap.setProperty("role", "setting-label")

        self.window.btn_mode_mss = QPushButton("MSS")
        self.window.btn_mode_mss.setObjectName("ModeMssBtn")
        self.window.btn_mode_mss.setProperty("role", "capture-btn")
        self.window.btn_mode_mss.setFixedSize(65, 25)
        self.window.btn_mode_mss.clicked.connect(lambda: self.window.set_capture_mode("MSS"))

        self.window.btn_mode_dxcam = QPushButton("DXCAM")
        self.window.btn_mode_dxcam.setObjectName("ModeDxcamBtn")
        self.window.btn_mode_dxcam.setProperty("role", "capture-btn")
        self.window.btn_mode_dxcam.setFixedSize(65, 25)
        self.window.btn_mode_dxcam.clicked.connect(lambda: self.window.set_capture_mode("DXCAM"))

        btns = QWidget()
        btns_layout = QHBoxLayout(btns)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(5)
        btns_layout.addStretch()
        btns_layout.addWidget(self.window.btn_mode_mss)
        btns_layout.addWidget(self.window.btn_mode_dxcam)
        btns_layout.addStretch()
        row_capture.addWidget(lbl_cap)
        row_capture.addWidget(btns, 1)
        layout.addLayout(row_capture)
        return card

    def _build_usage_panel(self):
        card, layout = self._card("MacroGuidePanel", "Hướng Dẫn Sử Dụng")
        self.window.group_settings = QWidget()
        settings_layout = QVBoxLayout(self.window.group_settings)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(8)

        row_overlay = QHBoxLayout()
        lbl_overlay = QLabel("Overlay")
        lbl_overlay.setFixedWidth(100)
        lbl_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_overlay.setProperty("role", "setting-label")
        self.window.btn_overlay_key = QPushButton("delete")
        self.window.btn_overlay_key.setProperty("role", "setting-btn")
        self.window.btn_overlay_key.setFixedHeight(25)
        self.window.btn_overlay_key.clicked.connect(
            lambda: self.window.start_keybind_listening(self.window.btn_overlay_key, "overlay_key")
        )
        self.window.btn_overlay_toggle = QPushButton("ON")
        self.window.btn_overlay_toggle.setObjectName("OverlayToggleBtn")
        self.window.btn_overlay_toggle.setProperty("state", "ON")
        self.window.btn_overlay_toggle.setCheckable(False)
        self.window.btn_overlay_toggle.clicked.connect(self.window.toggle_overlay_visibility)
        self.window.btn_overlay_toggle.setFixedSize(50, 28)
        row_overlay.addWidget(lbl_overlay)
        row_overlay.addWidget(self.window.btn_overlay_key)
        row_overlay.addSpacing(5)
        row_overlay.addWidget(self.window.btn_overlay_toggle)
        settings_layout.addLayout(row_overlay)

        row_fastloot = QHBoxLayout()
        lbl_fastloot = QLabel("Fast Loot")
        lbl_fastloot.setFixedWidth(100)
        lbl_fastloot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_fastloot.setProperty("role", "setting-label")
        self.window.btn_fastloot_key = QPushButton("caps_lock")
        self.window.btn_fastloot_key.setProperty("role", "setting-btn")
        self.window.btn_fastloot_key.setFixedHeight(25)
        self.window.btn_fastloot_key.clicked.connect(
            lambda: self.window.start_keybind_listening(self.window.btn_fastloot_key, "fast_loot_key")
        )
        self.window.btn_fastloot_toggle = QPushButton("OFF")
        self.window.btn_fastloot_toggle.setObjectName("FastLootToggleBtn")
        self.window.btn_fastloot_toggle.setProperty("state", "OFF")
        self.window.btn_fastloot_toggle.clicked.connect(self.window.toggle_fast_loot)
        self.window.btn_fastloot_toggle.setFixedSize(50, 28)
        row_fastloot.addWidget(lbl_fastloot)
        row_fastloot.addWidget(self.window.btn_fastloot_key)
        row_fastloot.addSpacing(5)
        row_fastloot.addWidget(self.window.btn_fastloot_toggle)
        settings_layout.addLayout(row_fastloot)

        self.window.btn_stopkeys = add_setting_row(settings_layout, "STOPKEYS", "X, G, 5")
        self.window.btn_stopkeys.setEnabled(False)
        self.window.btn_adsmode = add_setting_row(settings_layout, "ADS MODE", "HOLD")
        self.window.btn_adsmode.setEnabled(False)
        self.window.btn_guitoggle = add_setting_row(settings_layout, "BẬT/TẮT GUI", "F1")
        self.window.btn_guitoggle.setEnabled(False)

        layout.addWidget(self.window.group_settings)
        return card

    def _build_bind_panel(self):
        card, layout = self._card("MacroBindPanel", "Bind Nút")
        helper = QLabel("Giữ nguyên bind logic macro hiện tại")
        helper.setStyleSheet("color: #9f9f9f; font-size: 11px; background: transparent;")
        layout.addWidget(helper)
        return card

    def _build_toggle_panel(self):
        card, layout = self._card("MacroTogglePanel", "Bật/Tắt")
        helper = QLabel("Overlay / Fast Loot / GUI Toggle")
        helper.setStyleSheet("color: #9f9f9f; font-size: 11px; background: transparent;")
        layout.addWidget(helper)
        return card

    def _build_crosshair_panel(self):
        card, layout = self._card("MacroScopePanel", "Cường Độ Scope")
        cross = QFrame()
        cross_layout = QVBoxLayout(cross)
        cross_layout.setContentsMargins(0, 0, 0, 0)
        cross_layout.setSpacing(6)
        lbl_cross = QLabel("Tâm Ngắm")
        lbl_cross.setObjectName("CrosshairSectionTitle")
        cross_layout.addWidget(lbl_cross)

        row_cross = QHBoxLayout()
        self.window.btn_cross_toggle = QPushButton("ON")
        self.window.btn_cross_toggle.setObjectName("CrosshairToggleBtn")
        self.window.btn_cross_toggle.setProperty("checked", "true")
        self.window.btn_cross_toggle.setCheckable(True)
        self.window.btn_cross_toggle.setChecked(True)
        self.window.btn_cross_toggle.setFixedSize(40, 20)
        self.window.btn_cross_toggle.clicked.connect(self.window.toggle_crosshair)

        self.window.combo_style = QComboBox()
        self.window.combo_style.addItems(
            [
                "1: Gap Cross",
                "2: T-Shape",
                "3: Circle Dot",
                "5: Classic",
                "6: Micro Dot",
                "7: Hollow Box",
                "8: Cross + Dot",
                "9: Chevron",
                "10: X-Shape",
                "11: Diamond",
                "13: Triangle",
                "14: Square Dot",
                "17: Bracket Dot",
                "18: Shuriken",
                "19: Center Gap",
                "22: Plus Dot",
                "23: V-Shape",
                "24: Star",
            ]
        )
        self.window.combo_style.setCurrentText("Style 1")
        self.window.combo_style.setFixedHeight(20)
        self.window.combo_style.currentIndexChanged.connect(self.window.change_crosshair_style)

        self.window.combo_color = QComboBox()
        self.window.combo_color.addItems(
            ["Đỏ", "Đỏ Cam", "Cam", "Vàng", "Xanh Lá", "Xanh Ngọc", "Xanh Dương", "Tím", "Tím Hồng", "Hồng", "Trắng", "Bạc"]
        )
        self.window.combo_color.setCurrentText("Đỏ")
        self.window.combo_color.setFixedHeight(20)
        self.window.combo_color.currentIndexChanged.connect(self.window.change_crosshair_color)

        row_cross.addWidget(self.window.btn_cross_toggle)
        row_cross.addWidget(self.window.combo_style)
        row_cross.addWidget(self.window.combo_color)
        cross_layout.addLayout(row_cross)
        layout.addWidget(cross)
        return card

    def _build_scope_panel(self):
        card, layout = self._card("MacroScopePanel", "Cường Độ Scope")
        helper = QLabel("Scope đang dùng theo logic macro hiện tại")
        helper.setStyleSheet(
            "color: #9f9f9f; font-size: 11px; background: transparent;"
        )
        layout.addWidget(helper)
        return card
