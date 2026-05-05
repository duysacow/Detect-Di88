from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame,
    QGridLayout,
    QGroupBox,
    QComboBox,
    QGraphicsDropShadowEffect,
    QMessageBox,
    QSystemTrayIcon,
    QMenu,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QSize, QEvent
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QBrush,
    QKeySequence,
    QPixmap,
)
import win32api
import sys
import os

# IMPORT LOCAL COMPONENTS
from src.gui.game_overlay import GameOverlay

from src.gui.crosshair_overlay import CrosshairOverlay

from src.core.path_utils import get_resource_path
from src.core.settings import SettingsManager

# IMPORT HELPERS & MANAGERS (STEP 6)
from src.gui.tray_manager import TrayManager
from src.gui.ui_utils import create_panel, add_setting_row, create_data_row


# Quản lý cửa sổ giao diện chính của macro
class MacroWindow(QMainWindow):
    signal_settings_changed = (
        pyqtSignal()
    )  # Signal to notify Backend/InputBridge of config changes

    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(650, 500)
        icon_path = get_resource_path("di88vp.ico")
        self.setWindowIcon(QIcon(icon_path))

        # 3. --- AUTO DETECT RESOLUTION & MESSAGE BOX ---
        w = win32api.GetSystemMetrics(0)
        h = win32api.GetSystemMetrics(1)
        res_key = f"{w}x{h}"

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("THÔNG BÁO ĐỘ PHÂN GIẢI")
        msg.setText(f"ĐANG SỬ DỤNG ĐỘ PHÂN GIẢI: {res_key}")
        msg.exec()

        # 2. Logic Components (Connected via set_backend)
        self.backend = None

        # 3. Threads (PLACEHOLDER)

        # 4. Crosshair Overlay & Game HUD
        self.crosshair = CrosshairOverlay(self)

        self.game_overlay = GameOverlay(None)  # DETACH TO AVOID TASKBAR ISSUES

        # 5. UI Setup
        self.load_style()
        self.setup_ui()

        # 6. Tray Manager (Step 6)
        self.tray_manager = TrayManager(self)
        self.tray_manager.show()

        self.dragPos = None

        # Enable keyboard events for arrow keys AND Keybinds
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        # Keybind Listener State
        self.listening_key = False
        self.target_key_btn = None
        self.temp_original_text = None

        # Temporary unsaved keybind values (for manual save)
        self.temp_guitoggle_value = None
        self.temp_overlay_key_value = None
        self.temp_fast_loot_key_value = None

        # Install Global Event Filter to catch clicks anywhere
        self.installEventFilter(self)

    def repolish(self, widget):
        """Forces Qt to re-read properties and apply QSS"""
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def load_style(self):
        """Loads the external QSS stylesheet"""
        try:
            style_path = get_resource_path("src/gui/style.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[WARN] Could not load style.qss: {e}")

    def setup_ui(self):
        # Container chính (Bo tròn, Gradient nền)
        self.container = QFrame(self)
        self.container.setObjectName("MainContainer")
        self.container.setGeometry(5, 5, 640, 490)  # Adjusted for DropShadow

        # Drop Shadow nhẹ hơn để tránh lỗi rendering (UpdateLayeredWindowIndirect)
        # BỎ HOÀN TOÀN DROPSHADOW ĐỂ CỨU FPS GAME
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(4)
        # shadow.setOffset(0, 4)
        # self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TITLE BAR ---
        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(30)
        header_layout = QHBoxLayout(self.title_bar)
        header_layout.setContentsMargins(10, 0, 10, 0)

        btn_min = QPushButton("─")
        btn_min.setObjectName("MinBtn")
        btn_min.setFixedSize(20, 20)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.clicked.connect(self.hide)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("CloseBtn")
        btn_close.setFixedSize(20, 20)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.close)

        self.app_title_label = QLabel("Di88-VP")
        self.app_title_label.setObjectName("AppTitle")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(4)
        glow.setColor(QColor(0, 0, 0, 200))  # Bóng đen nhẹ
        glow.setOffset(1, 1)
        self.app_title_label.setGraphicsEffect(glow)

        # 1. Thêm logo app (di88vp.ico) vào Layout để nằm cạnh chữ
        self.app_logo = QLabel()
        icon_path = get_resource_path("di88vp.ico")
        logo_icon = QIcon(icon_path)
        self.app_logo.setPixmap(logo_icon.pixmap(22, 22))
        self.app_logo.setContentsMargins(0, 0, 5, 0)

        header_layout.addStretch()
        header_layout.addWidget(self.app_logo)
        header_layout.addWidget(self.app_title_label)
        header_layout.addStretch()
        header_layout.addWidget(btn_min)
        header_layout.addSpacing(5)
        header_layout.addWidget(btn_close)

        # Sự kiện kéo thả
        self.title_bar.mousePressEvent = self.mousePressEvent
        self.title_bar.mouseMoveEvent = self.mouseMoveEvent

        main_layout.addWidget(self.title_bar)

        # --- BODY V-LAYOUT (TOP/BOTTOM) ---
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(5, 5, 5, 5)
        body_layout.setSpacing(10)

        # --- 1. TOP UNIFIED BOX (GUNS + SETTINGS) ---
        top_box = QFrame()
        top_box.setObjectName("TopUnifiedBox")
        top_box.setStyleSheet("""
            QFrame#TopUnifiedBox {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        """)
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(10)

        # >>> LEFT PART (GUNS)
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        # Giữ tỉ lệ 1:1 với Settings
        left_column.setMinimumWidth(280)

        # GUN 1
        self.panel_g1, l_g1 = create_panel("GUN 1", "#FF4444", "P1")
        self.grid_g1 = QGridLayout()
        self.grid_g1.setSpacing(6)
        self.lbl_g1_name = create_data_row(self.grid_g1, 0, "Name")
        self.lbl_g1_scope = create_data_row(self.grid_g1, 1, "Scope")
        self.lbl_g1_grip = create_data_row(self.grid_g1, 2, "Grip")
        self.lbl_g1_muzzle = create_data_row(self.grid_g1, 3, "Muzz")
        l_g1.addLayout(self.grid_g1)
        left_layout.addWidget(self.panel_g1, stretch=1)

        # GUN 2
        self.panel_g2, l_g2 = create_panel("GUN 2", "#44FF44", "P2")
        self.grid_g2 = QGridLayout()
        self.grid_g2.setSpacing(6)
        self.lbl_g2_name = create_data_row(self.grid_g2, 0, "Name")
        self.lbl_g2_scope = create_data_row(self.grid_g2, 1, "Scope")
        self.lbl_g2_grip = create_data_row(self.grid_g2, 2, "Grip")
        self.lbl_g2_muzzle = create_data_row(self.grid_g2, 3, "Muzz")
        l_g2.addLayout(self.grid_g2)
        left_layout.addWidget(self.panel_g2, stretch=1)

        top_layout.addWidget(left_column, stretch=1)

        # >>> VERTICAL SEPARATOR
        v_sep = QFrame()
        v_sep.setFrameShape(QFrame.Shape.VLine)
        v_sep.setStyleSheet("background: #3a3a3a; border: none;")
        top_layout.addWidget(v_sep)

        # >>> RIGHT COLUMN (SETTINGS)
        self.group_settings = QWidget()
        self.group_settings.setObjectName("SettingsBox")

        settings_layout = QVBoxLayout(self.group_settings)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(10)

        lbl_settings_title = QLabel("CÀI ĐẶT CHUNG")
        lbl_settings_title.setStyleSheet(
            "color: #ffffff; font-weight: bold; letter-spacing: 1px;"
        )
        lbl_settings_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_layout.addWidget(lbl_settings_title)
        settings_layout.addSpacing(5)

        # Overlay
        row_overlay = QHBoxLayout()
        lbl_overlay = QLabel("Overlay")
        lbl_overlay.setFixedWidth(100)
        lbl_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_overlay.setProperty("class", "SettingLabel")
        self.btn_overlay_key = QPushButton("delete")
        self.btn_overlay_key.setProperty("class", "SettingBtn")
        self.btn_overlay_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_key.setFixedHeight(25)
        self.btn_overlay_key.clicked.connect(
            lambda: self.start_keybind_listening(self.btn_overlay_key, "overlay_key")
        )

        self.btn_overlay_toggle = QPushButton("ON")
        self.btn_overlay_toggle.setObjectName("OverlayToggleBtn")
        self.btn_overlay_toggle.setProperty("state", "ON")
        self.btn_overlay_toggle.setCheckable(False)
        self.btn_overlay_toggle.clicked.connect(self.toggle_overlay_visibility)
        self.btn_overlay_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay_toggle.setFixedSize(50, 28)
        row_overlay.addWidget(lbl_overlay)
        row_overlay.addWidget(self.btn_overlay_key)
        row_overlay.addSpacing(5)
        row_overlay.addWidget(self.btn_overlay_toggle)
        settings_layout.addLayout(row_overlay)

        # FastLoot
        row_fastloot = QHBoxLayout()
        lbl_fastloot = QLabel("Fast Loot")
        lbl_fastloot.setFixedWidth(100)
        lbl_fastloot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_fastloot.setProperty("class", "SettingLabel")
        self.btn_fastloot_key = QPushButton("caps_lock")
        self.btn_fastloot_key.setProperty("class", "SettingBtn")
        self.btn_fastloot_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_key.setFixedHeight(25)
        self.btn_fastloot_key.clicked.connect(
            lambda: self.start_keybind_listening(self.btn_fastloot_key, "fast_loot_key")
        )

        self.btn_fastloot_toggle = QPushButton("OFF")
        self.btn_fastloot_toggle.setObjectName("FastLootToggleBtn")
        self.btn_fastloot_toggle.setProperty("state", "OFF")
        self.btn_fastloot_toggle.clicked.connect(self.toggle_fast_loot)
        self.btn_fastloot_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fastloot_toggle.setFixedSize(50, 28)
        row_fastloot.addWidget(lbl_fastloot)
        row_fastloot.addWidget(self.btn_fastloot_key)
        row_fastloot.addSpacing(5)
        row_fastloot.addWidget(self.btn_fastloot_toggle)
        settings_layout.addLayout(row_fastloot)

        # StopKeys
        self.btn_stopkeys = add_setting_row(settings_layout, "STOPKEYS", "X, G, 5")
        self.btn_stopkeys.setEnabled(False)
        self.btn_stopkeys.setCursor(Qt.CursorShape.ArrowCursor)

        # ADS Mode
        self.btn_adsmode = add_setting_row(settings_layout, "ADS MODE", "HOLD")
        self.btn_adsmode.setEnabled(False)
        self.btn_adsmode.setCursor(Qt.CursorShape.ArrowCursor)

        # GUI Toggle
        self.btn_guitoggle = add_setting_row(settings_layout, "BẬT/TẮt GUI", "F1")
        self.btn_guitoggle.setEnabled(False)
        self.btn_guitoggle.setCursor(Qt.CursorShape.ArrowCursor)

        # Capture Mode
        row_capture = QHBoxLayout()
        lbl_cap = QLabel("CAPTURE")
        lbl_cap.setFixedWidth(100)
        lbl_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cap.setProperty("class", "SettingLabel")

        self.btn_mode_mss = QPushButton("MSS")
        self.btn_mode_mss.setObjectName("ModeMssBtn")
        self.btn_mode_mss.setProperty("class", "CaptureBtn")
        self.btn_mode_mss.setFixedSize(65, 25)
        self.btn_mode_mss.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_mss.clicked.connect(lambda: self.set_capture_mode("MSS"))

        self.btn_mode_dxcam = QPushButton("DXCAM")
        self.btn_mode_dxcam.setObjectName("ModeDxcamBtn")
        self.btn_mode_dxcam.setProperty("class", "CaptureBtn")
        self.btn_mode_dxcam.setFixedSize(65, 25)
        self.btn_mode_dxcam.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mode_dxcam.clicked.connect(lambda: self.set_capture_mode("DXCAM"))

        row_capture.addWidget(lbl_cap)

        btns_container = QWidget()
        btns_layout = QHBoxLayout(btns_container)
        btns_layout.setContentsMargins(0, 0, 0, 0)
        btns_layout.setSpacing(5)
        btns_layout.addStretch()
        btns_layout.addWidget(self.btn_mode_mss)
        btns_layout.addWidget(self.btn_mode_dxcam)
        btns_layout.addStretch()

        row_capture.addWidget(btns_container)
        settings_layout.addLayout(row_capture)

        settings_layout.addSpacing(5)

        settings_layout.addStretch()
        top_layout.addWidget(self.group_settings, stretch=1)
        body_layout.addWidget(top_box)

        # --- 2. BOTTOM CARDS ROW ---
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(15)

        # Left Bottom Card: Tư thế / Macro
        self.footer = QFrame()
        # Bỏ fixed width để chia đều 50-50 với cross_card
        self.footer.setFixedHeight(115)
        self.footer.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        """)
        f_layout = QVBoxLayout(self.footer)
        f_layout.setSpacing(2)
        f_layout.setContentsMargins(8, 8, 8, 8)

        self.lbl_stance = QLabel("TƯ THẾ: ĐỨNG")
        self.lbl_stance.setObjectName("StanceLabel")
        self.lbl_stance.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_stance.setFixedHeight(30)
        self.lbl_stance.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
                background: #262626;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
        """)
        f_layout.addWidget(self.lbl_stance)

        self.btn_macro = QPushButton("MACRO : OFF")
        self.btn_macro.setCursor(Qt.CursorShape.ForbiddenCursor)
        self.btn_macro.setFixedHeight(30)
        self.btn_macro.setStyleSheet("""
            QPushButton {
                color: #ff4444;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
                background: #1a1010;
                border: 1px solid #441111;
                border-radius: 5px;
            }
        """)
        self.update_macro_style(False)
        f_layout.addWidget(self.btn_macro)

        bottom_row.addWidget(self.footer)

        # Right Bottom Card: Tâm Ảo & Màu + Buttons
        cross_card = QFrame()
        cross_card.setFixedHeight(115)
        cross_card.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        """)
        cross_card_layout = QVBoxLayout(cross_card)
        cross_card_layout.setSpacing(6)
        cross_card_layout.setContentsMargins(10, 8, 10, 8)

        lbl_cross = QLabel("Tâm Ảo & Màu:")
        lbl_cross.setObjectName("CrosshairSectionTitle")
        cross_card_layout.addWidget(lbl_cross)

        row_cross = QHBoxLayout()
        self.btn_cross_toggle = QPushButton("ON")
        self.btn_cross_toggle.setObjectName("CrosshairToggleBtn")
        self.btn_cross_toggle.setProperty("checked", "true")
        self.btn_cross_toggle.setCheckable(True)
        self.btn_cross_toggle.setChecked(True)
        self.btn_cross_toggle.setFixedSize(40, 20)
        self.btn_cross_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cross_toggle.clicked.connect(self.toggle_crosshair)

        self.combo_style = QComboBox()
        self.combo_style.addItems(
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
        self.combo_style.setCurrentText("Style 1")
        self.combo_style.setFixedHeight(20)
        self.combo_style.currentIndexChanged.connect(self.change_crosshair_style)

        self.combo_color = QComboBox()
        self.combo_color.addItems(
            [
                "Đỏ",
                "Đỏ Cam",
                "Cam",
                "Vàng",
                "Xanh Lá",
                "Xanh Ngọc",
                "Xanh Dương",
                "Tím",
                "Tím Hồng",
                "Hồng",
                "Trắng",
                "Bạc",
            ]
        )
        self.combo_color.setCurrentText("Đỏ")
        self.combo_color.setFixedHeight(20)
        self.combo_color.currentIndexChanged.connect(self.change_crosshair_color)

        row_cross.addWidget(self.btn_cross_toggle)
        row_cross.addWidget(self.combo_style)
        row_cross.addWidget(self.combo_color)
        cross_card_layout.addLayout(row_cross)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #3a3a3a; border: none;")
        sep.setFixedHeight(1)
        cross_card_layout.addWidget(sep)

        row_btns = QHBoxLayout()
        btn_default = QPushButton("CÀI ĐẶT GỐC")
        btn_default.setObjectName("DefaultBtn")
        btn_default.setFixedHeight(30)
        btn_default.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_default.clicked.connect(self.reset_to_defaults)

        btn_save = QPushButton("LƯU CÀI ĐẶT")
        btn_save.setObjectName("SaveBtn")
        btn_save.setFixedHeight(30)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self.save_config)

        row_btns.addWidget(btn_default)
        row_btns.addWidget(btn_save)
        cross_card_layout.addLayout(row_btns)

        bottom_row.addWidget(cross_card)
        body_layout.addLayout(bottom_row)

        main_layout.addWidget(body_widget)

        # Load Settings (General)
        self.load_config()

        # Load Crosshair Settings
        self.load_crosshair_settings()

    # BƯỚC 3: XỬ LÝ NÚT BẬT/TẮT (Trong MainWindow)
    def toggle_overlay_visibility(self):
        if self.btn_overlay_toggle.text() == "ON":
            self.game_overlay.hide()
            self.btn_overlay_toggle.setText("OFF")
            self.btn_overlay_toggle.setProperty("state", "OFF")
        else:
            self.game_overlay.show()
            self.btn_overlay_toggle.setText("ON")
            self.btn_overlay_toggle.setProperty("state", "ON")
        self.repolish(self.btn_overlay_toggle)

    def toggle_fast_loot(self):
        if self.btn_fastloot_toggle.text() == "ON":
            self.btn_fastloot_toggle.setText("OFF")
            self.btn_fastloot_toggle.setProperty("state", "OFF")
        else:
            self.btn_fastloot_toggle.setText("ON")
            self.btn_fastloot_toggle.setProperty("state", "ON")
        self.repolish(self.btn_fastloot_toggle)

    def toggle_crosshair(self, checked):
        self.crosshair.set_active(checked)
        if checked:
            self.crosshair.show()
            self.crosshair.raise_()
            self.btn_cross_toggle.setText("ON")
            self.btn_cross_toggle.setProperty("checked", "true")
        else:
            self.crosshair.hide()
            self.btn_cross_toggle.setText("OFF")
            self.btn_cross_toggle.setProperty("checked", "false")
        self.repolish(self.btn_cross_toggle)
        self.save_crosshair_settings()  # Auto-save

    def change_crosshair_style(self, index):
        style = self.combo_style.currentText()
        self.crosshair.set_style(style)
        self.save_crosshair_settings()  # Auto-save

    def change_crosshair_color(self, index):
        color = self.combo_color.currentText()
        self.crosshair.set_color(color)
        self.save_crosshair_settings()  # Auto-save

    # --- KEYBIND LISTENER LOGIC ---
    def start_keybind_listening(self, btn, setting_key):
        self.listening_key = True
        self.target_key_btn = btn
        self.target_key_btn = btn
        self.target_setting_key = setting_key  # "fastloot"
        # Store previous text to revert on cancel
        self.temp_original_text = btn.text()

        btn.setText("PRESS KEY...")
        btn.setStyleSheet(
            "background-color: #FF00FF; color: white; border: 1px solid #fff;"
        )
        self.setFocus()  # Ensure Window gets key events

    def keyPressEvent(self, event):
        # 1. Handle Keybind Listening
        if self.listening_key and self.target_key_btn:
            key = event.key()

            # Convert Qt Key to Pynput/Win32 friendly string
            key_name = QKeySequence(key).toString().lower()

            # Special mapping for Common Keys
            if key == Qt.Key.Key_CapsLock:
                key_name = "caps_lock"
            elif key == Qt.Key.Key_Shift:
                key_name = "shift"
            elif key == Qt.Key.Key_Control:
                key_name = "ctrl"
            elif key == Qt.Key.Key_Alt:
                key_name = "alt"

            # CLEAR KEY (Escape / Backspace / Delete) -> NONE
            elif (
                key == Qt.Key.Key_Escape
                or key == Qt.Key.Key_Backspace
                or key == Qt.Key.Key_Delete
            ):
                key_name = "NONE"

            # Update Button

            # Update Button (UPPERCASE for professional look)
            self.target_key_btn.setText(key_name.upper())
            self.target_key_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a; color: #ccc; 
                    border: 1px solid #444; border-radius: 4px; font-size: 11px;
                }
                QPushButton:hover { border: 1px solid #666; background-color: #333; }
            """)

            # DON'T SAVE YET - only store temporarily
            # User must click "Save Config" button to commit changes

            # Removed fastloot
            if self.target_setting_key == "gui_toggle":
                self.temp_guitoggle_value = key_name
            elif self.target_setting_key == "overlay_key":
                self.temp_overlay_key_value = key_name
            elif self.target_setting_key == "fast_loot_key":
                self.temp_fast_loot_key_value = key_name

            # Reset State (CRITICAL - prevents infinite loop!)
            self.listening_key = False
            self.target_key_btn = None
            self.temp_original_text = None

            return

        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Global Event Filter to handle clicking away"""
        if self.listening_key and event.type() == QEvent.Type.MouseButtonPress:
            # Logic: If clicking ANYWHERE while listening, check if it's the target button.
            # If not, Cancel.

            # Note: The event object might be the window or a child widget.
            # We just want to know if the user clicked.

            # Check if the click target is the button itself?
            # It's hard to distinguish perfectly if obj is proper.
            # Simpler: If listening, ANY click sends 'Cancel' unless it's handled by KeyPress?
            # Actually, we want to allow clicking the button again? No need.

            # If we are here, a mouse press happened.
            # Check if cursor is over the button?
            if self.target_key_btn and self.target_key_btn.underMouse():
                return super().eventFilter(obj, event)

            # Clicked OUTSIDE
            self.cancel_listening()
            # Don't consume event, let it propagate (e.g. clicking Save should still work)

        return super().eventFilter(obj, event)

    def cancel_listening(self):
        """Helper to cancel listening state"""
        if not self.listening_key:
            return

        if self.target_key_btn:
            # Revert Text (UPPERCASE!)
            if hasattr(self, "temp_original_text") and self.temp_original_text:
                self.target_key_btn.setText(self.temp_original_text.upper())
            else:
                self.target_key_btn.setText("CAPS_LOCK")

            # Revert Style
            self.target_key_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a; color: #ccc; 
                    border: 1px solid #444; border-radius: 4px; font-size: 11px;
                }
                QPushButton:hover { border: 1px solid #666; background-color: #333; }
            """)

        self.listening_key = False
        self.target_key_btn = None
        self.temp_original_text = None

    def load_config(self):
        """Load settings from settings.json"""
        try:
            settings = self.settings_manager.load()

            # Load Mouse Mode (Legacy Support / Hidden)
            # mouse_mode = settings.get("mouse_mode", "Win32")
            # Default Win32 (No UI)

            # Load GUI Toggle Key
            gui_toggle_key = "F1"  # Default
            if "keybinds" in settings and isinstance(settings["keybinds"], dict):
                gui_toggle_key = settings["keybinds"].get("gui_toggle", "f1")

            self.btn_guitoggle.setText(gui_toggle_key.upper())

            # Load ADS Mode
            ads_mode = settings.get("ads_mode", "HOLD")
            self.btn_adsmode.setText(ads_mode.upper())

            # Load Capture Mode
            cap_mode = settings.get("capture_mode", "MSS")
            self.set_capture_mode_ui(cap_mode.upper())

            # Load FastLoot
            fast_loot = settings.get("fast_loot", False)
            self.btn_fastloot_toggle.setText("ON" if fast_loot else "OFF")
            self.btn_fastloot_toggle.setProperty("state", "ON" if fast_loot else "OFF")
            self.repolish(self.btn_fastloot_toggle)

            fl_key = settings.get("fast_loot_key", "caps_lock")
            self.btn_fastloot_key.setText(fl_key.upper())

            ov_key = settings.get("overlay_key", "delete")
            self.btn_overlay_key.setText(ov_key.upper())
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")

    def toggle_ads_mode(self):
        modes = ["ADS: HOLD", "ADS: TOGGLE", "ADS: CLICK"]
        current = self.btn_adsmode.text()

        idx = modes.index(current)
        next_idx = (idx + 1) % len(modes)

        self.btn_adsmode.setText(modes[next_idx])

    def set_capture_mode(self, mode):
        self.set_capture_mode_ui(mode)

    def set_capture_mode_ui(self, mode):
        """Update buttons styles based on current selected mode"""
        mode = mode.upper()

        # 1. Update Properties
        self.btn_mode_dxcam.setProperty(
            "active", "true" if mode == "DXCAM" else "false"
        )
        self.btn_mode_mss.setProperty("active", "true" if mode == "MSS" else "false")

        # 2. Force Repolish
        self.repolish(self.btn_mode_dxcam)
        self.repolish(self.btn_mode_mss)

        # We need a property to read the "current" text during Save
        self.current_capture_mode = mode

    def cycle_ads_mode(self):
        current = self.btn_ads_hide.text()

        # Simple toggle between 2 states
        if "HOLD" in current:
            new_mode = "ADS CLICK"
            mode_val = "TOGGLE"
        else:
            new_mode = "ADS HOLD"
            mode_val = "HOLD"

        self.btn_ads_hide.setText(new_mode)
        self.crosshair.set_ads_mode(mode_val)
        self.save_crosshair_settings()  # Auto-save

    def load_crosshair_settings(self):
        """Load crosshair settings from settings.json"""
        try:
            data = self.settings_manager.get("crosshair", {})

            # Active
            is_on = data.get("active", False)
            self.btn_cross_toggle.setChecked(is_on)
            self.toggle_crosshair(is_on)

            if is_on:
                self.crosshair.show()
                self.crosshair.raise_()

            # Style
            style = data.get("style", "1: Gap Cross")

            # Robust mapping for old names
            old_name_mapping = {
                "Style 1": "1: Gap Cross",
                "Style 2": "3: Circle Dot",
                "Style 6": "6: Micro Dot",
            }
            if style in old_name_mapping:
                style = old_name_mapping[style]

            # Try to match the combo box exact text
            idx = self.combo_style.findText(style)
            if idx == -1:
                idx = 0  # Default fallback

            self.combo_style.setCurrentIndex(idx)
            self.crosshair.set_style(style)

            # Color (Map back to index)
            color_map = {"White": 0, "Red": 1, "Green": 2, "Blue": 3, "Yellow": 4}
            # Need to map Qt Color to string if saved differently?
            # Assuming we save the Combo text for simplicity or map index
            saved_color_idx = data.get("color_index", 0)
            self.combo_color.setCurrentIndex(saved_color_idx)
            # Trigger color update
            self.change_crosshair_color(saved_color_idx)

            # ADS Mode
            ads_mode = data.get("ads_mode", "HOLD")
            self.btn_ads_hide.setText(f"ADS: {ads_mode}")
            self.crosshair.set_ads_mode(ads_mode)

        except Exception as e:
            print(f"[ERROR] Load Crosshair settings failed: {e}")

    def save_crosshair_settings(self):
        """Save crosshair settings to settings.json"""
        try:
            is_active = self.btn_cross_toggle.isChecked()

            style_val = self.combo_style.currentText()

            color_idx = self.combo_color.currentIndex()

            data = {
                "active": is_active,
                "style": style_val,
                "color_index": color_idx,
            }
            self.settings_manager.set("crosshair", data)
        except Exception as e:
            print(f"[ERROR] Save Crosshair settings failed: {e}")

    # --- MAIN SAVE CONFIG ---
    def reset_to_defaults(self):
        """Reset all settings to project defaults and update UI"""
        from PyQt6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Reset tất cả cài đặt về mặc định?\nKeybind, Tâm ảo đều về default.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 1. Reset settings.json về mặc định
            defaults = self.settings_manager.reset_to_defaults()
            self.settings_manager._cache = None  # Force reload

            # 2. Reset Keybinds UI
            kb = defaults.get("keybinds", {})
            if hasattr(self, "btn_guitoggle") and self.btn_guitoggle:
                self.btn_guitoggle.setText(kb.get("gui_toggle", "f1").upper())

            # 3. Reset ADS Mode button
            ads_mode = defaults.get("ads_mode", "HOLD")
            if hasattr(self, "btn_adsmode") and self.btn_adsmode:
                self.btn_adsmode.setText(ads_mode)

            # 3.5 Reset Capture Mode button
            cap_mode = defaults.get("capture_mode", "MSS")
            self.set_capture_mode_ui(cap_mode)

            # 4. Reset Crosshair UI
            cr = defaults.get("crosshair", {})
            if hasattr(self, "combo_style") and self.combo_style:
                style = cr.get("style", "1: Gap Cross")
                idx = self.combo_style.findText(style)
                self.combo_style.setCurrentIndex(max(0, idx))
            if hasattr(self, "combo_color") and self.combo_color:
                color = cr.get("color", "Red")
                color_idx = {
                    "Red": 0,
                    "Green": 1,
                    "Blue": 2,
                    "Cyan": 3,
                    "Yellow": 4,
                    "Magenta": 5,
                    "White": 6,
                }
                self.combo_color.setCurrentIndex(color_idx.get(color, 0))
            if hasattr(self, "btn_ads_hide") and self.btn_ads_hide:
                ads_cross = cr.get("ads_mode", "HOLD")
                self.btn_ads_hide.setText(f"ADS: {ads_cross}")
            if hasattr(self, "btn_cross_toggle") and self.btn_cross_toggle:
                self.btn_cross_toggle.setChecked(cr.get("active", True))
            if hasattr(self, "crosshair") and self.crosshair:
                self.crosshair.set_style(cr.get("style", "1: Gap Cross"))
                self.crosshair.set_color(cr.get("color", "Red"))
                self.crosshair.set_ads_mode(cr.get("ads_mode", "HOLD"))

            pass
            QMessageBox.information(
                self, "Xong!", "Reset thành công! Tất cả đã về mặc định."
            )
        except Exception as e:
            print(f"[ERROR] reset_to_defaults failed: {e}")
            QMessageBox.warning(self, "Lỗi", f"Reset thất bại: {e}")

    def save_config(self):
        """Manually Save All Settings (Triggered by Button)"""
        try:

            # 2. GUI Toggle Key (use temp value if changed, otherwise button text)
            if self.temp_guitoggle_value:
                guitoggle_key = self.temp_guitoggle_value
                self.temp_guitoggle_value = None  # Clear temp after saving
            else:
                guitoggle_key = self.btn_guitoggle.text().lower()

            capture_mode = getattr(self, "current_capture_mode", "MSS")

            # Construct Data
            current_settings = self.settings_manager.load()

            # Update Keybinds (Standard Path)
            if "keybinds" not in current_settings or not isinstance(
                current_settings["keybinds"], dict
            ):
                current_settings["keybinds"] = {}

            current_settings["keybinds"]["gui_toggle"] = guitoggle_key.lower()
            current_settings["capture_mode"] = capture_mode

            # Fast Loot
            current_settings["fast_loot"] = self.btn_fastloot_toggle.text() == "ON"
            if self.temp_fast_loot_key_value:
                current_settings["fast_loot_key"] = self.temp_fast_loot_key_value
                self.temp_fast_loot_key_value = None
            else:
                current_settings["fast_loot_key"] = self.btn_fastloot_key.text().lower()

            # Overlay Key
            if self.temp_overlay_key_value:
                current_settings["overlay_key"] = self.temp_overlay_key_value
                self.temp_overlay_key_value = None
            else:
                current_settings["overlay_key"] = self.btn_overlay_key.text().lower()

            # Save to File
            self.settings_manager.save(current_settings)

            # Notify Backend to reload config
            self.signal_settings_changed.emit()

            # Hiện thông báo giống như khi mở app (Always on Top)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("LƯU CÀI ĐẶT")
            msg.setText("ĐÃ LƯU CÀI ĐẶT THÀNH CÔNG!")
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg.exec()

        except Exception as e:
            print(f"[ERROR] Save Config Failed: {e}")
            QMessageBox.critical(self, "Error", f"Lỗi lưu cài đặt: {e}")

    def update_macro_style(self, is_on):
        base = "font-size: 12px; font-weight: bold; letter-spacing: 2px; border-radius: 5px;"
        if is_on:
            self.btn_macro.setText("MACRO : ON")
            self.btn_macro.setStyleSheet(
                f"QPushButton {{ color: #00FFFF; background: #0d1f1f; border: 1px solid #006666; {base} }}"
            )
        else:
            self.btn_macro.setText("MACRO : OFF")
            self.btn_macro.setStyleSheet(
                f"QPushButton {{ color: #ff4444; background: #1a1010; border: 1px solid #441111; {base} }}"
            )

    def set_backend(self, backend):
        self.backend = backend

    def update_ads_display(self, mode: str):
        """Cập nhật hiển thị ADS MODE từ PUBG config — không thể click"""
        if hasattr(self, "btn_adsmode") and self.btn_adsmode:
            self.btn_adsmode.setText(mode.upper())
        # Đồng bộ nút ADS trong crosshair section
        if hasattr(self, "btn_ads_hide") and self.btn_ads_hide:
            self.btn_ads_hide.setText(f"ADS: {mode.upper()}")
        # Đồng bộ crosshair overlay
        if hasattr(self, "crosshair") and self.crosshair:
            self.crosshair.set_ads_mode(mode.upper())

    def toggle_ads_mode(self):
        """Toggle ADS Mode between HOLD and CLICK"""
        current = self.btn_adsmode.text()
        if current == "HOLD":
            new_mode = "CLICK"
        else:
            new_mode = "HOLD"

        self.btn_adsmode.setText(new_mode)

        # Save to settings
        try:
            from src.core.settings import SettingsManager

            settings = SettingsManager()
            settings.set("ads_mode", new_mode)
        except Exception as e:
            print(f"[ERROR] Failed to save ADS mode: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")

    def showEvent(self, event):
        """Force UI update when window is shown"""
        super().showEvent(event)
        if hasattr(self, "last_data") and self.last_data:
            self.update_ui_state(self.last_data)

    def update_ui_state(self, data):
        # Cache data for showEvent
        self.last_data = data

        # ALWAYS UPDATE INTERNAL STATE
        # Helper: Clean Text (No brackets, UPPER None)
        def fmt(val):
            return "NONE" if val == "None" else val

        g1 = data["gun1"]
        g2 = data["gun2"]
        active_slot = data.get("active_slot", 1)
        active_gun = g1 if active_slot == 1 else g2

        weapon_name = fmt(active_gun["name"])
        scope_name = fmt(active_gun["scope"])

        # Map scope name to X1...X8 for Key lookup
        # Map scope name to Scope1...Scope8 for Key lookup (Đồng bộ với Backend)
        def get_scope_display(s):
            s = str(s).lower()
            is_kh = "kh" in s
            digit = "1"
            if "8" in s:
                digit = "8"
            elif "6" in s:
                digit = "6"
            elif "4" in s:
                digit = "4"
            elif "3" in s:
                digit = "3"
            elif "2" in s:
                digit = "2"

            prefix = "ScopeKH" if is_kh else "Scope"
            return prefix + digit

        self.current_scope_key = get_scope_display(scope_name)
        self.current_weapon = weapon_name

        # OPTIMIZATION: If window is hidden, only update the overlay, skip main UI labels
        if not self.isVisible():
            # Still update overlay because it's always "visible" or needed
            self.game_overlay.update_status(
                weapon_name,
                scope_name,
                data["stance"],
                grip=active_gun.get("grip", "NONE"),
                muzzle=active_gun.get("accessories", "NONE"),
                is_paused=data.get("paused", False),
                is_firing=data.get("firing", False),
                ai_status=data.get("ai_status", "HIBERNATE"),
            )
            return

        # Update Gun 1 UI
        self.lbl_g1_name.setText(fmt(g1["name"]))
        self.lbl_g1_scope.setText(fmt(g1["scope"]))
        self.lbl_g1_grip.setText(fmt(g1["grip"]))
        self.lbl_g1_muzzle.setText(fmt(g1["accessories"]))

        # Update Gun 2 UI
        self.lbl_g2_name.setText(fmt(g2["name"]))
        self.lbl_g2_scope.setText(fmt(g2["scope"]))
        self.lbl_g2_grip.setText(fmt(g2["grip"]))
        self.lbl_g2_muzzle.setText(fmt(g2["accessories"]))

        # Remove active slot glow - Use static neutral colors
        static_border = "border: 1px solid #333;"
        self.panel_g1.setStyleSheet(
            f"QFrame#P1 {{ background-color: #262626; border-radius: 8px; {static_border} }}"
        )
        self.panel_g2.setStyleSheet(
            f"QFrame#P2 {{ background-color: #262626; border-radius: 8px; {static_border} }}"
        )

        def item_style(lbl, val):
            if val == "NONE":
                lbl.setStyleSheet(
                    "background-color: #2e2e2e; color: #666; border-radius: 4px; padding: 2px; font-size: 11px;"
                )
            else:
                lbl.setStyleSheet(
                    "background-color: #2e2e2e; color: #FFD700; border-radius: 4px; padding: 2px; font-size: 11px; font-weight: bold;"
                )

        item_style(self.lbl_g1_name, fmt(g1["name"]))
        item_style(self.lbl_g1_scope, fmt(g1["scope"]))
        item_style(self.lbl_g1_grip, fmt(g1["grip"]))
        item_style(self.lbl_g1_muzzle, fmt(g1["accessories"]))

        item_style(self.lbl_g2_name, fmt(g2["name"]))
        item_style(self.lbl_g2_scope, fmt(g2["scope"]))
        item_style(self.lbl_g2_grip, fmt(g2["grip"]))
        item_style(self.lbl_g2_muzzle, fmt(g2["accessories"]))

        # Update Overlay
        self.game_overlay.update_status(
            weapon_name,
            scope_name,
            data["stance"],
            grip=active_gun.get("grip", "NONE"),
            muzzle=active_gun.get("accessories", "NONE"),
            is_paused=data.get("paused", False),
            is_firing=data.get("firing", False),
            ai_status=data.get("ai_status", "HIBERNATE"),
        )

        stance = data["stance"]
        s_lower = str(stance).lower()

        # Mapping về tiếng Việt chuẩn
        vn_stance = "Đứng"
        if "crouch" in s_lower:
            vn_stance = "Ngồi"
        elif "prone" in s_lower:
            vn_stance = "Nằm"
        elif "stand" in s_lower:
            vn_stance = "Đứng"
        else:
            vn_stance = stance

        # The user requested No color change on stance depending on slot or stance type, just a fixed color
        color = "#aaaaaa"

        self.lbl_stance.setText(f"TƯ THẾ : {(vn_stance or 'ĐỨNG').upper()}")
        self.lbl_stance.setStyleSheet(f"""
            background-color: #262626; 
            color: {color}; 
            font-size: 11px; 
            font-weight: bold; 
            border: 1px solid #3a3a3a; 
            border-radius: 5px;
        """)

    # --- DRAG LOGIC (SMOOTH PYQT DRAG) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()
            # Tạm thời tắt DropShadow để kéo mượt hơn, không bị khựng CPU
            if hasattr(self, "container"):
                self.container.setGraphicsEffect(None)
            event.accept()

    def mouseMoveEvent(self, event):
        if (
            event.buttons() == Qt.MouseButton.LeftButton
            and hasattr(self, "dragPos")
            and self.dragPos is not None
        ):
            # Tính toán và di chuyển
            new_pos = self.pos() + event.globalPosition().toPoint() - self.dragPos
            self.move(new_pos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        # Bật lại DropShadow khi dừng kéo để giữ vẻ "Premium"
        if hasattr(self, "container"):
            from PyQt6.QtWidgets import QGraphicsDropShadowEffect

            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 150))
            shadow.setOffset(0, 5)
            self.container.setGraphicsEffect(shadow)
        super().mouseReleaseEvent(event)

    def show_message(self, title, msg):
        """Show Notification (Tray Bubble or Popup)"""
        if hasattr(self, "tray_manager"):
            self.tray_manager.tray_icon.showMessage(
                title, msg, QSystemTrayIcon.MessageIcon.Information, 2000
            )
        else:
            # Fallback (Modal)
            box = QMessageBox(self)
            box.setWindowTitle(title)
            box.setText(msg)
            box.setIcon(QMessageBox.Icon.Information)
            box.show()
            QTimer.singleShot(2000, box.close)  # Auto-close

    def restore_window(self):
        self.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Cleanup resources on close, including detached overlays."""
        if hasattr(self, "game_overlay") and self.game_overlay:
            self.game_overlay.close()

        event.accept()
