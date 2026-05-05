import sys
import os
import json
import subprocess
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QGroupBox,
    QFormLayout,
    QScrollArea,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import Qt

# Tự động tìm thư mục gốc của dự án (Project Root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Giao diện chỉnh sửa nhanh thông số recoil
class RecoilSettingsTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ADVANCED RECOIL TUNER - ELITE LEAN")
        self.resize(1100, 800)

        self.apply_styles()
        self.load_data()
        self.init_ui()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                border: 2px solid #2d2d2d;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
                font-weight: bold;
                color: #2ecc71;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #2ecc71;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #2ecc71;
                color: black;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2ecc71;
                color: black;
                border-radius: 6px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QLabel {
                font-weight: bold;
                color: #888888;
            }
            QScrollArea {
                border: none;
            }
        """)

    def load_data(self):
        try:
            # Import trực tiếp từ file Python để lấy giá trị hiện tại
            from src.recoil.base_recoil_data import BaseRecoilData

            self.recoil_data = BaseRecoilData
            # Copy dữ liệu để chỉnh sửa (tránh mutate class trực tiếp)
            self.working_weapons = dict(BaseRecoilData.Weapons)
            self.working_scopes = dict(BaseRecoilData.scope_multipliers)
            self.working_grips = dict(BaseRecoilData.grips)
            self.working_accs = dict(BaseRecoilData.accessories)
            self.working_shift = BaseRecoilData.Shift_Boost
            self.working_rate = BaseRecoilData.sampling_rate_ms
        except Exception as e:
            QMessageBox.critical(
                self, "Lỗi nạp dữ liệu", f"Không thể đọc base_recoil_data.py: {e}"
            )
            sys.exit(1)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- PANEL TRÁI: DANH SÁCH SÚNG ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        search_label = QLabel("TÌM SÚNG:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập tên súng...")
        self.search_input.textChanged.connect(self.filter_weapons)

        self.weapon_list = QListWidget()
        self.weapon_list.addItems(sorted(self.working_weapons.keys()))
        self.weapon_list.currentRowChanged.connect(self.load_weapon_settings)

        save_btn = QPushButton("LƯU & RESET MACRO")
        save_btn.setFixedHeight(50)
        save_btn.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; font-size: 14px;"
        )
        save_btn.clicked.connect(self.save_and_apply)

        left_layout.addWidget(search_label)
        left_layout.addWidget(self.search_input)
        left_layout.addWidget(self.weapon_list)
        left_layout.addWidget(save_btn)

        # --- PANEL PHẢI: CHI TIẾT ---
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_content = QWidget()
        self.right_layout = QVBoxLayout(right_content)

        # 1. GLOBAL MULTIPLIERS (SCOPE/GRIP/ACC)
        self.init_global_section()

        # 2. WEAPON SPECIFIC (STANCE)
        self.init_weapon_section()

        right_panel.setWidget(right_content)

        # Splitter để resize
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 4)

        main_layout.addWidget(splitter)

    def init_global_section(self):
        global_group = QGroupBox("CÀI ĐẶT HỆ SỐ CHUNG (GLOBAL MULTIPLIERS)")
        g_main_layout = QHBoxLayout(global_group)

        # Sắp xếp thứ tự ưu tiên
        scope_order = ["Reddot", "2x", "3x", "4x", "6x", "8x"]

        # Scopes Column
        scope_box = QWidget()
        scope_layout = QFormLayout(scope_box)
        scope_layout.addRow(QLabel("--- SCOPES ---"), QLabel(""))
        self.scope_inputs = {}
        for scope in scope_order:
            if scope in self.working_scopes:
                val = self.working_scopes[scope]
                input_field = QLineEdit(str(val))
                input_field.setFixedWidth(60)
                self.scope_inputs[scope] = input_field
                scope_layout.addRow(f"{scope}:", input_field)

        # Grips Column
        grip_box = QWidget()
        grip_layout = QFormLayout(grip_box)
        grip_layout.addRow(QLabel("--- TAY CẦM ---"), QLabel(""))
        self.grip_inputs = {}
        # Sắp xếp grips: NONE trước, còn lại theo Alphabet
        grip_list = sorted([k for k in self.working_grips.keys() if k != "NONE"])
        grip_list = ["NONE"] + grip_list
        for grip in grip_list:
            if grip in self.working_grips:
                val = self.working_grips[grip]
                input_field = QLineEdit(str(val))
                input_field.setFixedWidth(60)
                self.grip_inputs[grip] = input_field
                grip_layout.addRow(f"{grip}:", input_field)

        # Accessories Column
        acc_box = QWidget()
        acc_layout = QFormLayout(acc_box)
        acc_layout.addRow(QLabel("--- ĐẦU NÒNG ---"), QLabel(""))
        self.acc_inputs = {}
        # Sắp xếp accs: NONE trước, còn lại theo Alphabet
        acc_list = sorted([k for k in self.working_accs.keys() if k != "NONE"])
        acc_list = ["NONE"] + acc_list
        for acc in acc_list:
            if acc in self.working_accs:
                val = self.working_accs[acc]
                input_field = QLineEdit(str(val))
                input_field.setFixedWidth(60)
                self.acc_inputs[acc] = input_field
                acc_layout.addRow(f"{acc}:", input_field)

        g_main_layout.addWidget(scope_box)
        g_main_layout.addWidget(grip_box)
        g_main_layout.addWidget(acc_box)

        self.right_layout.addWidget(global_group)

    def init_weapon_section(self):
        self.weapon_group = QGroupBox("THÔNG SỐ RIÊNG TỪNG SÚNG (TƯ THẾ)")
        self.w_layout = QFormLayout(self.weapon_group)
        self.stance_inputs = {}

        self.right_layout.addWidget(self.weapon_group)
        self.weapon_group.setEnabled(False)

    def filter_weapons(self, text):
        self.weapon_list.clear()
        filtered = [
            w for w in sorted(self.working_weapons.keys()) if text.upper() in w.upper()
        ]
        self.weapon_list.addItems(filtered)

    def load_weapon_settings(self, index):
        if index < 0:
            return
        weapon_name = self.weapon_list.currentItem().text()
        self.weapon_group.setTitle(f"TƯ THẾ: {weapon_name}")
        self.weapon_group.setEnabled(True)

        # Clear old rows
        while self.w_layout.count():
            item = self.w_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stance_data = self.working_weapons[weapon_name].get("stance_multipliers", {})
        self.stance_inputs = {}
        for stance in ["Stand", "Crouch", "Prone"]:
            val = stance_data.get(stance, 1.0)
            input_field = QLineEdit(str(val))
            self.stance_inputs[stance] = input_field
            self.w_layout.addRow(f"{stance}:", input_field)
            input_field.textChanged.connect(
                lambda text, w=weapon_name, s=stance: self.update_stance_map(w, s, text)
            )

    def update_stance_map(self, weapon, stance, text):
        try:
            val = float(text)
            if "stance_multipliers" not in self.working_weapons[weapon]:
                self.working_weapons[weapon]["stance_multipliers"] = {}
            self.working_weapons[weapon]["stance_multipliers"][stance] = val
        except:
            pass

    def save_and_apply(self):
        try:
            # Update Global Multipliers from UI
            for scope, input_f in self.scope_inputs.items():
                self.working_scopes[scope] = float(input_f.text())
            for grip, input_f in self.grip_inputs.items():
                self.working_grips[grip] = float(input_f.text())
            for acc, input_f in self.acc_inputs.items():
                self.working_accs[acc] = float(input_f.text())

            # Generate Python Content
            output = "class BaseRecoilData:\n"
            output += f"    sampling_rate_ms = {self.working_rate}\n"
            output += f"    Shift_Boost = {self.working_shift}\n\n"

            def fmt_dict(d, indent=4):
                items = []
                for k, v in d.items():
                    items.append(f'{" " * (indent + 4)}"{k}": {v}')
                return (
                    " " * indent + "{\n" + ",\n".join(items) + "\n" + " " * indent + "}"
                )

            output += (
                "    scope_multipliers = " + fmt_dict(self.working_scopes) + "\n\n"
            )
            output += "    grips = " + fmt_dict(self.working_grips) + "\n\n"
            output += "    accessories = " + fmt_dict(self.working_accs) + "\n\n"

            output += "    Weapons = {\n"
            for gun, gdata in self.working_weapons.items():
                bt_str = json.dumps(gdata.get("BaseTable", []))
                sm_str = json.dumps(gdata.get("stance_multipliers", {}))
                output += f'        "{gun}": {{\n'
                output += f'            "BaseTable": {bt_str},\n'
                output += f'            "stance_multipliers": {sm_str},\n'
                output += "        },\n"
            output = output.strip().rstrip(",") + "\n    }\n"

            # Ghi vào file (Sử dụng đường dẫn tuyệt đối)
            save_path = os.path.join(
                PROJECT_ROOT, "src", "recoil", "base_recoil_data.py"
            )
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(output)

            # QMessageBox.information(self, "Thành công", "Đã lưu thông số! Đang khởi động lại Macro...")
            self.restart_macro()

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {e}")

    def restart_macro(self):
        try:
            # Diệt đúng tiến trình đang chạy entrypoint chính
            # WMIC là cách an nhất trên Windows để tìm theo tên file chạy
            cmd = "wmic process where \"commandline like '%src\\\\app\\\\main.py%'\" call terminate"
            subprocess.run(cmd, shell=True, capture_output=True)

            # Thêm 1 giây chờ để hệ thống giải phóng tài nguyên
            import time

            time.sleep(1)

            # Khởi động lại (Sử dụng đường dẫn tuyệt đối và đúng thư mục làm việc)
            macro_path = os.path.join(PROJECT_ROOT, "src", "app", "main.py")
            python_path = sys.executable
            # 0x00000010 là flag CREATE_NEW_CONSOLE trên Windows
            subprocess.Popen(
                [python_path, macro_path], cwd=PROJECT_ROOT, creationflags=0x00000010
            )

        except Exception as e:
            print(f"Restart failed: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RecoilSettingsTool()
    window.show()
    sys.exit(app.exec())
