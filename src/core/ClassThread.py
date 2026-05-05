import sys
import time
import cv2
import hashlib
import copy
import concurrent.futures
import win32api
import win32gui
import ctypes
from PyQt6.QtCore import QThread, pyqtSignal
from src.core import Utils
from src.detect.ClassCapture import ScreenCapture
from src.detect.ClassDetection import DetectionEngine
from src.core.ClassGhimTam import RecoilExecutor
from src.core.ClassPubgConfig import PubgConfig

# ─── C-Style Structures for SendInput (FastLoot Logic) ───
# Khai báo cấu trúc dữ liệu chuột cho Windows API
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), 
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulonglong) if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.POINTER(ctypes.c_ulong))
    ]
# Khai báo cấu trúc dữ liệu bàn phím cho Windows API
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong), 
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulonglong) if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.POINTER(ctypes.c_ulong))
    ]
# Gom dữ liệu input chuột hoặc bàn phím vào một union
class INPUT_u(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]
# Đóng gói một lệnh input gửi xuống Windows
class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", INPUT_u)]

def batch_send(inputs_list):
    """Engine xử lý chuột/phím siêu tốc cho FastLoot"""
    SW, SH = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    n = len(inputs_list)
    input_array = (INPUT * n)()
    for i, item in enumerate(inputs_list):
        if len(item) == 3: # Mouse
            flags, x, y = item
            nx, ny = int(x * 65535 / SW), int(y * 65535 / SH)
            input_array[i].type = 0
            input_array[i].u.mi = MOUSEINPUT(nx, ny, 0, flags, 0, None)
        elif len(item) == 2: # Keyboard
            scan, flags = item
            input_array[i].type = 1
            input_array[i].u.ki = KEYBDINPUT(0, scan, flags | 0x0008, 0, None)
    ctypes.windll.user32.SendInput(n, ctypes.pointer(input_array), ctypes.sizeof(INPUT))


# Luồng xử lý nhận diện hình ảnh và trạng thái game
class VisionWorker(QThread):
    signal_vision_update = pyqtSignal(object)

    def __init__(self, backend, capture, detector):
        super().__init__()
        self.backend = backend
        self.capture = capture
        self.detector = detector
        self.running = True
        # Worker không nên giữ state lâu dài để tránh ghi đè sai lệch dữ liệu từ phím bấm

    def run(self):
        """HÀM KHỞI CHẠY LUỒNG (Bắt buộc của QThread)"""
        self.run_vision_loop()

    def run_vision_loop(self):
        last_hashes = {} # { "gun1_name": hash, ... }
        last_cfg_check = 0.0  # throttle đọc file config
        
        while self.running:
            # 1. CẬP NHẬT SEN mỗi 0.5 giây (đọc trực tiếp file, so sánh giá trị)
            now = time.time()
            if now - last_cfg_check >= 0.1:
                last_cfg_check = now
                if self.backend.pubg_config.parse_config():
                    self.backend.pubg_config.debug_print()
                    ads = getattr(self.backend.pubg_config, 'ads_mode', None)
                    if ads:
                        self.backend.signal_ads_update.emit(ads.upper())

            try:
                if not Utils.is_game_active():
                    time.sleep(0.5)
                    continue
                
                # 2. KIỂM TRA TRẠNG THÁI MENU CHẶN
                menu_blocked = getattr(self.backend, 'menu_blocked', False)
                
                # 3. TRẠNG THÁI TRỎ CHUỘT (TRIGGER CHÍNH)
                flags, h_cursor, (cx, cy) = win32gui.GetCursorInfo()
                self.is_cursor_visible = (flags != 0)
                
                # CHỐNG QUÉT BẬY: Chỉ quét khi trỏ chuột đang nằm TRÊN cửa sổ game
                # Đã gỡ bỏ check HWND tại con trỏ vì dễ xung đột với Discord/OBS/Nvidia Overlay

                
                # TRẠNG THÁI PHÍM TAB
                self.is_tab_held = (win32api.GetAsyncKeyState(0x09) & 0x8000) != 0

                # TỰ ĐỘNG RESET CỔNG KHI ĐÓNG MENU
                if not self.is_cursor_visible:
                    # Nếu không còn trỏ chuột -> Chắc chắn đã đóng Menu -> Reset Gate
                    if self.backend: self.backend.inventory_gate = False
            except:
                self.is_tab_held = False
                self.is_cursor_visible = False

            img = self.capture.grab_regional_image()
            if img is None:
                time.sleep(0.01)
                continue

            # 4. QUÉT TƯ THẾ (Luôn quét, không cần dieukien)
            new_vision_state = {}
            if not menu_blocked:
                roi_img = self.capture.get_roi_from_image(img, "stance")
                if roi_img is not None:
                    curr_hash = hashlib.md5(roi_img.tobytes()).hexdigest()
                    if last_hashes.get("stance") != curr_hash:
                        last_hashes["stance"] = curr_hash
                        new_vision_state["stance"] = self.detector.detect_stance(roi_img)

            # ====== TÚI ĐỒ GATEKEEPER: CHỈ QUÉT KHI CẦN THIẾT ======
            # 1. Check Trỏ chuột
            if not self.is_cursor_visible or menu_blocked:
                new_vision_state["ai_status"] = "HIBERNATE"
                self.signal_vision_update.emit(new_vision_state)
                time.sleep(0.03) # Mức 30fps: Nhạy mà cực nhẹ máy
                continue

            # 2. Check Template "DieuKienDetect" (Dùng Threshold cực thấp 0.4 để chống lóa)
            roi_dieukien = self.capture.get_roi_from_image(img, "dieukien")
            if roi_dieukien is None or self.detector.detect_ui_anchor(roi_dieukien, threshold=0.4) == "NONE":
                new_vision_state["ai_status"] = "HIBERNATE"
                self.signal_vision_update.emit(new_vision_state)
                time.sleep(0.03)
                continue


            
            # Nếu lọt qua cửa: Chính thức ACTIVE và quét súng
            new_vision_state["ai_status"] = "ACTIVE"

            # ====== QUÉT SONG SONG CẢ 2 SLOT CÙNG LÚC (Điều kiện 2) ======
            def scan_slot(i):
                """Quét 1 slot súng. Chạy song song với slot kia."""
                s_key = f"gun{i}"
                roi_types = {
                    "name":  "name",
                    "scope": "scope",
                    "grip":  "grip",
                    "muzzle":"accessories"
                }
                detected = {}
                for r_type, field in roi_types.items():
                    roi_name = f"{s_key}_{r_type}"
                    roi_img = self.capture.get_roi_from_image(img, roi_name)
                    if roi_img is None:
                        continue
                    # Điều kiện 4: Chỉ nhận diện khi ảnh thay đổi (hash)
                    curr_hash = hashlib.md5(roi_img.tobytes()).hexdigest()
                    if last_hashes.get(roi_name) == curr_hash:
                        continue
                    last_hashes[roi_name] = curr_hash

                    if r_type == "name":   detected[field] = self.detector.detect_weapon_name(roi_img)
                    elif r_type == "scope":  detected[field] = self.detector.detect_scope(roi_img)
                    elif r_type == "grip":   detected[field] = self.detector.detect_grip(roi_img)
                    elif r_type == "muzzle": detected[field] = self.detector.detect_accessory(roi_img)

                return s_key, detected

            # Nếu đã vượt qua các bước check ở trên -> Chắc chắn đang mở túi đồ
            new_vision_state["ai_status"] = "ACTIVE"

            # Chạy scan_slot(1) và scan_slot(2) ĐỒNG THỜI
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                futures = {ex.submit(scan_slot, i): i for i in [1, 2]}
                for fut in concurrent.futures.as_completed(futures):
                    s_key, detected = fut.result()
                    if detected:
                        new_vision_state[s_key] = detected
                        # Hễ soi ra được "Cái gì đó" (Súng/Scope...) -> Ép ACTIVE ngay!
                        new_vision_state["ai_status"] = "ACTIVE"


            # Luôn gửi dữ liệu (kể cả rỗng) khi đang mở túi đồ để update UI
            self.signal_vision_update.emit(new_vision_state)

            
            time.sleep(0.02)

# Luồng polling phím nóng và thao tác hỗ trợ trong game
class KeyPollingThread(QThread):
    def __init__(self, parent=None):
        super().__init__()
        self.backend = parent
        self.running = True
        self._last_keys = [False] * 8 # C, Z, X, Space, 1, 2, Ctrl, Alt
        self.refresh_settings()

    def refresh_settings(self):
        """Pre-load settings to avoid disk I/O in the tight loop"""
        from src.core.ClassSettings import SettingsManager
        sm = SettingsManager()
        self.fast_loot_enabled = sm.get("fast_loot", False)
        fl_key_str = sm.get("fast_loot_key", "caps_lock").lower()
        self.fast_loot_vk = {
            "caps_lock": 0x14, "caps lock": 0x14, 
            "shift": 0x10, "ctrl": 0x11, "alt": 0x12
        }.get(fl_key_str, 0x14)

    def run(self):
        while self.running and self.backend.running:
            # 1. KIỂM TRA ĐANG Ở TRONG GAME + KHÔNG TẠM DỪNG
            if not Utils.is_game_active():
                self.backend.executor.stop_recoil()
                time.sleep(0.1)
                continue

            # Poll Keys: Ctrl(0x11), Alt(0x12), 1(0x31), 2(0x32), C(0x43), Z(0x5A), Space(0x20), RClick(0x02)
            vks = [0x11, 0x12, 0x31, 0x32, 0x43, 0x5A, 0x20, 0x02]
            current_keys = [ (win32api.GetAsyncKeyState(vk) & 0x8000) != 0 for vk in vks ]
            
            # 2. Stance Toggle (C - Crouch, Z - Prone, Space - Stand)
            if current_keys[4] and not self._last_keys[4]: self.backend.set_stance_by_key("Crouch")
            if current_keys[5] and not self._last_keys[5]: self.backend.set_stance_by_key("Prone")
            if current_keys[6] and not self._last_keys[6]: self.backend.set_stance_by_key("Stand")

            # 3. TRẠNG THÁI CHẶN QUÉT (Dành cho M và ESC)
            is_tab = (win32api.GetAsyncKeyState(0x09) & 0x8000) != 0
            is_esc = (win32api.GetAsyncKeyState(0x1B) & 0x8000) != 0
            is_map = (win32api.GetAsyncKeyState(0x4D) & 0x8000) != 0
            is_comma = (win32api.GetAsyncKeyState(0xBC) & 0x8000) != 0  # Phím ','

            if is_tab: 
                self.backend.menu_blocked = False # TAB mở thì cho quét
            elif is_esc or is_map or is_comma:
                self.backend.menu_blocked = True  # Map/ESC/Comma thì chặn quét

            # 4. Hybrid Scope Toggle
            if current_keys[1] and (current_keys[7] and not self._last_keys[7]):
                self.backend.toggle_hybrid_mode()

            # 5. FastLoot (Optimized: No disk I/O here)
            if self.fast_loot_enabled:
                if (win32api.GetAsyncKeyState(self.fast_loot_vk) & 0x8000):
                    self.perform_fast_loot(self.fast_loot_vk)

            self._last_keys = current_keys
            time.sleep(0.01)

    def perform_fast_loot(self, trigger_vk):
        """Logic gắp đồ thần tốc"""
        MOUSE_MOVE_ABS, MOUSE_DOWN, MOUSE_UP = 0x0001 | 0x8000, 0x0002, 0x0004
        loot_coords = [(68, 579), (68, 512), (66, 450), (67, 390), (68, 329), (67, 266), (69, 207), (68, 146)]
        dest_x, dest_y = 938, 504 
        # Open Tab
        batch_send([(0x17, 0)]); time.sleep(0.02); batch_send([(0x17, 2)]); time.sleep(0.18) 
        while (win32api.GetAsyncKeyState(trigger_vk) & 0x8000):
            for lx, ly in loot_coords:
                if not (win32api.GetAsyncKeyState(trigger_vk) & 0x8000): break
                batch_send([(MOUSE_MOVE_ABS, lx, ly), (MOUSE_DOWN, 0, 0), (MOUSE_MOVE_ABS, dest_x, dest_y), (MOUSE_UP, 0, 0)])
                time.sleep(0.015)
            time.sleep(0.05)
        # Close Tab
        batch_send([(0x17, 0)]); time.sleep(0.02); batch_send([(0x17, 2)])

# Điều phối backend, state game và đồng bộ recoil
class BackendThread(QThread):
    signal_update = pyqtSignal(object)
    signal_message = pyqtSignal(str, str)
    signal_ads_update = pyqtSignal(str)  # Emit ADS mode string khi PUBG config thay đổi

    def __init__(self):
        super().__init__()
        self.running = True
        from src.core.ClassSettings import SettingsManager
        settings = SettingsManager()
        # Ưu tiên dùng DXCAM để không làm tụt FPS game, nếu lỗi tự fallback về MSS
        self.capture = ScreenCapture(capture_mode="DXCAM")
        self.detector = DetectionEngine(template_folder="FullHD")
        self.executor = RecoilExecutor()
        
        self.state = {
            "gun1": {"name": "NONE", "scope": "NONE", "grip": "NONE", "accessories": "NONE"},
            "gun2": {"name": "NONE", "scope": "NONE", "grip": "NONE", "accessories": "NONE"},
            "stance": "Stand", "active_slot": 1, "paused": False,
            "firing": False, # Trạng thái đang sấy để làm Overlay chớp chớp
            "hybrid_mode": "Scope1", # Mặc định là X1 cho Scope Kết Hợp
            "ai_status": "HIBERNATE"
        }

        self.stance_lock_until = 0.0
        self.ai_active_until = 0.0

        self.stance_buffer = [] # Lưu 3 kỳ gần nhất của AI để lọc nhiễu
        self.weapon_buffers = {"gun1": [], "gun2": []} # Xác nhận 2 frame trước khi về NONE
        self.menu_blocked = False # Cửa chặn: True nếu đang mở Map/ESC

        
        self.pubg_config = PubgConfig()
        
        # Hệ thống Bù lực Sens (Persistence)
        from src.core.ClassSensCalculator import SensitivityCalculator
        self.sens_calculator = SensitivityCalculator()

        if self.pubg_config.parse_config():
            self.pubg_config.debug_print()

        self.vision_worker = VisionWorker(self, self.capture, self.detector)
        self.vision_worker.signal_vision_update.connect(self._on_vision_update)
        self.vision_worker.start()
        self.poller = KeyPollingThread(self)
        self.poller.start()


    def _sync_executor(self):
        slot = self.state["active_slot"]
        # Làm bản copy để không làm hỏng state gốc khi ghi đè
        gun_info = copy.deepcopy(self.state[f"gun{slot}"])
        
        # Xóa bỏ logic ép ScopeKH về Scope1/4 để dùng hệ số riêng
        self.executor.live_stance = self.state["stance"]
        self.executor.current_gun_name = gun_info["name"]
        
        # Tính toán hệ số bù Sensitivity (X1/X4/X8...)
        sens_multiplier = self.sens_calculator.calculate_sens_multiplier(
            self.pubg_config, 
            gun_info, 
            hybrid_mode=self.state.get("hybrid_mode", "Scope1")
        )

        # Lấy Master multiplier từ JSON
        base_mult = self.executor.config.get_master_multiplier(gun_info)
        
        # NHÂN HỆ SỐ BÙ VÀO LỰC GỐC
        self.executor.gun_base_mult = base_mult * sens_multiplier
        st = self.executor.config.get_all_stance_multipliers(gun_info["name"])
        
        # LẤY TRỰC TIẾP TỪ DICTIONARY CỦA CONFIG (KHÔNG HARDCODE SỐ TRONG FILE NÀY)
        self.executor.st_stand = float(st["Stand"])
        self.executor.st_crouch = float(st["Crouch"])
        self.executor.st_prone = float(st["Prone"])

    def toggle_hybrid_mode(self):
        """Chuyển đổi giữa X1 và X4 cho Scope Kết Hợp"""
        if self.state.get("hybrid_mode") == "Scope1":
            self.state["hybrid_mode"] = "Scope4"
        else:
            self.state["hybrid_mode"] = "Scope1"
        
        # Cập nhật tên hiển thị trong State để Overlay (Bottom Bar) nhận ra X1/X4 mới
        slot = self.state.get("active_slot", 1)
        gun_key = f"gun{slot}"
        current_scope = self.state[gun_key].get("scope", "")
        if "KH" in str(current_scope).upper():
            zoom = "1" if self.state["hybrid_mode"] == "Scope1" else "4"
            self.state[gun_key]["scope"] = f"ScopeKH_{zoom}"

        # Hiển thị thông báo lớn trung tâm màn hình
        msg = "KH X4" if self.state["hybrid_mode"] == "Scope4" else "KH X1"
        self.signal_message.emit("SCOPE", msg)

        self._sync_executor()
        self.signal_update.emit(self.state)

    def reload_config(self):
        self.executor.reload_config()
        self.poller.refresh_settings()
        self.signal_message.emit("SUCCESS", "CONFIG REFRESHED!")

    def _on_vision_update(self, data):
        """
        XỬ LÝ CÁC THAY ĐỔI TỪ VISION (ZIN Logic)
        """
        def normalize_scope(name):
            if not name: return "NONE"
            n = str(name).upper()
            if "KH" in n: return "SCOPEKH" 
            return n

        new_state = copy.deepcopy(self.state)
        changed = False

        if "ai_status" in data:
            if data["ai_status"] == "ACTIVE":
                self.ai_active_until = time.time() + 0.5
            elif data["ai_status"] == "HIBERNATE" and time.time() < self.ai_active_until:
                data["ai_status"] = "ACTIVE"

            if new_state.get("ai_status") != data["ai_status"]:
                new_state["ai_status"] = data["ai_status"]
                changed = True

        # 1. Xử lý Tư thế (Stance) với Bộ lọc 3 khung hình
        if "stance" in data:
            if time.time() > self.stance_lock_until:
                # Thêm vào hàng đợi lọc nhiễu
                self.stance_buffer.append(data["stance"])
                if len(self.stance_buffer) > 3: self.stance_buffer.pop(0)

                # Nếu 3 lần cuối cùng trùng khớp và khác với thực tế hiện tại -> Cập nhật
                if len(self.stance_buffer) == 3 and all(s == self.stance_buffer[0] for s in self.stance_buffer):
                    target_stance = self.stance_buffer[0]
                    if new_state.get("stance") != target_stance:
                        new_state["stance"] = target_stance
                        changed = True

        # 2. Xử lý Súng (1 & 2)
        active_slot = new_state.get("active_slot", 1)
        
        for slot_num in [1, 2]:
            key = f"gun{slot_num}"
            if key in data and data[key]:
                partial_weapon = data[key]
                old_weapon = self.state.get(key, {})
                
                # CHUẨN HÓA PHẦN CỨNG
                old_scope_raw = old_weapon.get("scope", "NONE") if isinstance(old_weapon, dict) else "NONE"
                old_scope_norm = normalize_scope(old_scope_raw)
                
                new_scope_raw = partial_weapon.get("scope", old_scope_raw)
                new_scope_norm = normalize_scope(new_scope_raw)

                # Merge dữ liệu (Chỉ cập nhật NAME nếu chắc chắn 2 frame)
                new_name = partial_weapon.get("name", "NONE")
                if new_name == "NONE":
                    self.weapon_buffers[key].append("NONE")
                    if len(self.weapon_buffers[key]) < 2: # Cần 2 frame xác nhận để về NONE
                        partial_weapon["name"] = old_weapon.get("name", "NONE")
                    if len(self.weapon_buffers[key]) > 5: self.weapon_buffers[key].pop(0)
                else:
                    self.weapon_buffers[key] = [] # Reset buffer khi thấy súng thật

                merged_weapon = {**old_weapon, **partial_weapon} if isinstance(old_weapon, dict) else partial_weapon
                
                # RESET KHI ĐỔI PHẦN CỨNG (VD: Từ Reddot -> ScopeKH)
                if slot_num == active_slot:
                    old_name = old_weapon.get("name", "NONE") if isinstance(old_weapon, dict) else "NONE"
                    new_name = partial_weapon.get("name", old_name)
                    
                    if new_name != old_name or new_scope_norm != old_scope_norm:
                        if new_scope_norm == "SCOPEKH":
                            new_state["hybrid_mode"] = "Scope1"
                        changed = True

                # ĐỒNG BỘ TÊN HIỂN THỊ (Để Overlay hiện đúng KH X1/X4)
                if new_scope_norm == "SCOPEKH":
                    # Ép tên có hậu tố X1/X4 để GameOverlay.py nhận diện được
                    zoom = "1" if new_state["hybrid_mode"] == "Scope1" else "4"
                    merged_weapon["scope"] = f"ScopeKH_{zoom}"

                new_state[key] = merged_weapon
                changed = True

        # (Bỏ logic tự động đổi active_slot từ Vision để tránh nhảy súng loạn xạ)

        # 3. CHỈ EMIT KHI CÓ THAY ĐỔI THỰC SỰ
        if changed:
            # BẢO VỆ TRẠNG THÁI: Lấy lại trạng thái mới nhất từ MainThread trước khi ghi đè
            new_state["firing"] = self.state.get("firing", False)
            new_state["paused"] = self.state.get("paused", False)
            new_state["active_slot"] = self.state.get("active_slot", 1)
            
            self.state = new_state
            self._sync_executor()

            self.signal_update.emit(copy.deepcopy(self.state))
            
            # Gửi thông báo Overlay đặc biệt nếu đang dùng ScopeKH
            slot = self.state.get("active_slot", 1)
            gun_info = self.state.get(f"gun{slot}", {})
            if normalize_scope(gun_info.get("scope")) == "SCOPEKH":
                msg = "KH X4" if self.state.get("hybrid_mode") == "Scope4" else "KH X1"
                self.signal_message.emit("SCOPE", msg)

    def set_slot(self, slot):
        # TỰ ĐỘNG BỎ TẠM DỪNG: Khi chuyển súng thì coi như muốn dùng sấy luôn
        self.state["paused"] = False
        
        if self.state.get("active_slot") != slot:
            self.state["active_slot"] = slot
            
        self._sync_executor()

        # Luôn Emit để GUI cập nhật màu mè chính xác
        self.signal_update.emit(copy.deepcopy(self.state))

    def set_paused(self, paused):
        self.state["paused"] = paused
        self.signal_update.emit(copy.deepcopy(self.state))

    def set_firing(self, is_firing):
        """Cập nhật trạng thái đang bắn để Overlay đổi màu"""
        if self.state.get("firing") != is_firing:
            self.state["firing"] = is_firing
            self.signal_update.emit(copy.deepcopy(self.state))

    def set_stance_by_key(self, stance):
        """Cập nhật tư thế từ phím bấm (Ưu tiên tuyệt đối)"""
        if stance == "Crouch" and self.state.get("stance") == "Crouch":
            stance = "Stand" # Toggle off
        elif stance == "Prone" and self.state.get("stance") == "Prone":
            stance = "Stand" # Toggle off
        # Nếu Space (Stand) thì không cần Toggle, ép về Stand luôn
        
        self.state["stance"] = stance
        # Reset buffer AI để không bị ghi đè nhầm ngay lập tức
        self.stance_buffer = [stance] * 3
        # Lock AI trong 0.8 giây để chờ game đổi icon xong
        self.stance_lock_until = time.time() + 0.8 
        
        if self.executor:
            self.executor.live_stance = stance
            
        self.signal_update.emit(copy.deepcopy(self.state))

    def stop(self):
        self.running = False
        self.vision_worker.running = False
        self.poller.running = False
        self.quit()
