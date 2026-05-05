import os
import re
import hashlib

class PubgConfig:
    def __init__(self):
        self.config_path = os.path.join(os.environ['LOCALAPPDATA'], 
                                        r"TslGame\Saved\Config\WindowsNoEditor\GameUserSettings.ini")
        self.last_mtime = 0.0
        self.last_size = 0
        self.sensitivities = {}
        self.true_sensitivities = {}  # LastConvertedSensitivity per scope
        self.vertical_multiplier = 1.0
        self.per_scope_enabled = False
        self.ads_mode = "Hold"


    def parse_config(self):
        """Kiểm tra thay đổi (mtime & size) trước khi đọc file để tiết kiệm tài nguyên"""
        if not os.path.exists(self.config_path):
            return False

        try:
            # 0. KIỂM TRA NHANH: Chỉ đọc nếu file thay đổi thực sự
            st = os.stat(self.config_path)
            curr_mtime = st.st_mtime
            curr_size = st.st_size
            
            if curr_mtime == self.last_mtime and curr_size == self.last_size:
                return False

            try:
                with open(self.config_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except PermissionError:
                return False  # PUBG đang ghi file, bỏ qua nhịp này
            
            # Cập nhật dấu vân tay file
            self.last_mtime = curr_mtime
            self.last_size = curr_size

            # Lưu lại giá trị cũ để so sánh
            old_v = self.vertical_multiplier
            old_sens = self.sensitivities.copy()
            old_mode = getattr(self, 'ads_mode', 'HOLD')

            # 1. Vertical Multiplier (TRÍCH XUẤT PHẦN TỬ CUỐI CÙNG DO PUBG BỊ TRÙNG LẶP MÃ)
            v_matches = list(re.finditer(r'MouseVerticalSensitivityMultiplierAdjusted=([\d\.]+)', content))
            if v_matches:
                self.vertical_multiplier = float(v_matches[-1].group(1))

            # 2. SensitiveMap - LẤY KHỐI CUỐI CÙNG (Cái game đang dùng)
            mouse_matches = list(re.finditer(r'\(Mouse, \(Array=\((.*?)\)\)\)', content))
            new_sens = {}
            true_sens_map = {}
            
            if mouse_matches:
                # Lấy match cuối cùng
                mouse_block = mouse_matches[-1].group(1)
                for match in re.finditer(r'SensitiveName="([^"]+)",Sensitivity=([\d\.]+),LastConvertedSensitivity=([\d\.]+)', mouse_block):
                    name = match.group(1)
                    new_sens[name] = float(match.group(2))
                    true_sens_map[name] = float(match.group(3))

            self.sensitivities = new_sens
            self.true_sensitivities = true_sens_map
            
            # 3. XỬ LÝ ĐỘ NHẠY TẤT CẢ NÒNG NGẮM CHUNG
            # bIsUsingPerScopeMouseSensitivity=True  => Sens riêng từng scope (KHÔNG alias)
            # bIsUsingPerScopeMouseSensitivity=False => Sens chung (alias 2x->15x về ScopingMagnified)
            per_scope_matches = re.findall(r'bIsUsingPerScopeMouseSensitivity=(True|False)', content)
            self.per_scope_enabled = False
            if per_scope_matches and per_scope_matches[-1] == "False":
                self.per_scope_enabled = True
                
                # Ghi đè toàn bộ Scope (2x -> 15x) bằng ScopingMagnified
                master_sens = new_sens.get("ScopingMagnified", 50.0)
                master_true = true_sens_map.get("ScopingMagnified", 0.02)
                for s_key in ["Scope2X", "Scope3X", "Scope4X", "Scope6X", "Scope8X", "Scope15X"]:
                    self.sensitivities[s_key] = master_sens
                    self.true_sensitivities[s_key] = master_true
            
            # 3. ADS Mode
            ads_match = re.search(r'InputModeADS=(\w+)', content)
            self.ads_mode = ads_match.group(1) if ads_match else "Hold"

            # Chỉ trả True nếu có gì đó thực sự thay đổi
            if (old_v == self.vertical_multiplier
                    and old_sens == self.sensitivities
                    and old_mode == self.ads_mode):
                return False

            return True
        except Exception as e:
            print(f"[ERROR] PubgConfig: {e}")
            return False

    def debug_print(self):
        print("\n[HOT-RELOAD] Đã tải settings game thành công!")
        print(f" => Vertical: {self.vertical_multiplier}")
        print(f" => ADS Mode: {getattr(self, 'ads_mode', 'Hold')}")
        order = ["Normal", "Targeting", "Scoping", "ScopingMagnified", "Scope2X", "Scope3X", "Scope4X", "Scope6X", "Scope8X", "Scope15X"]
        for name in order:
            if name in self.sensitivities:
                print(f" => {name}: {round(self.sensitivities[name], 1)}")
        print("-" * 40)

if __name__ == "__main__":
    # Test script
    cfg = PubgConfig()
    if cfg.parse_config():
        cfg.debug_print()
    else:
        print("Không tìm thấy file cấu hình PUBG!")
