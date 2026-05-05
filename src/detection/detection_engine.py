import cv2
import os
import numpy as np
from src.core.path_utils import get_resource_path


# Nhận diện súng, phụ kiện và trạng thái từ ảnh chụp
class DetectionEngine:
    def __init__(self, template_folder="FullHD"):
        """
        Khởi tạo hệ thống và nạp sẵn toàn bộ mẫu ảnh vào RAM (Súng, UI, Phụ kiện, Tay cầm, Scope, Tư thế).
        """
        self.base_dir = get_resource_path("")
        self.template_dir = self._resolve_template_dir(template_folder)

        # Kho lưu trữ tập trung để quản lý dễ dàng
        self.templates = {
            "weapons": {},
            "ui": {},
            "accessories": {},
            "grip": {},
            "scopes": {},
            "stances": {},
            "dieukien": {},  # Bảng điều kiện mở khóa detect
        }

        # Nạp toàn bộ các danh mục
        total_count = 0
        for category in self.templates.keys():
            total_count += self._load_category(category)

        # BÁO CÁO TÓM TẮT (GỌN GÀNG)
        print(
            f" > [SYSTEM] Detection Engine: Loaded {total_count} templates (BGR Mode)"
        )

    def _resolve_template_dir(self, template_folder):
        candidates = [
            os.path.join(self.base_dir, template_folder),
            os.path.join(self.base_dir, "src", "Template", template_folder),
        ]

        aliases = {
            "FullHD": "1920x1080",
            "2K": "3440x1440",
        }
        alias_folder = aliases.get(template_folder)
        if alias_folder:
            candidates.append(
                os.path.join(self.base_dir, "src", "Template", alias_folder)
            )

        for path in candidates:
            if os.path.exists(path):
                return path

        return candidates[0]

    def _load_category(self, category):
        """Hàm dùng chung để nạp toàn bộ ảnh từ một thư mục vào dictionary."""
        path = os.path.join(self.template_dir, category)
        if not os.path.exists(path):
            return 0

        count = 0
        for file in os.listdir(path):
            if file.lower().endswith((".png", ".jpg", ".jpeg")):
                full_path = os.path.join(path, file)
                # ĐỌC ẢNH MÀU (BGR) để phân biệt chính xác theo yêu cầu
                img = cv2.imread(full_path)
                if img is not None:
                    # Lưu tên nguyên bản (viết hoa) - Không xóa hậu tố để tránh lỗi VSS -> V
                    name = os.path.splitext(file)[0].upper()
                    self.templates[category][name] = img
                    count += 1
        return count

    def _match(self, roi, category, threshold=0.8):
        if category not in self.templates or not self.templates[category]:
            return "NONE"

        max_val = -1
        best_name = "NONE"

        for name, tpl in self.templates[category].items():
            if tpl.shape[0] > roi.shape[0] or tpl.shape[1] > roi.shape[1]:
                continue

            # So sánh ảnh MÀU (BGR)
            res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)

            if val > max_val:
                max_val = val
                best_name = name

            if val > 0.98:  # Early exit optimization
                break

        return best_name if max_val >= threshold else "NONE"

    # --- CÁC HÀM PUBLIC ĐỂ CLASS THREAD GỌI ---

    def detect_weapon_name(self, roi, threshold=0.8):
        # TRẢ VỀ TÊN NGUYÊN BẢN 100% (Ví dụ: VSS, M16A4, ACE32 giữ nguyên)
        return self._match(roi, "weapons", threshold)

    def detect_ui_anchor(self, roi, threshold=0.65):
        """Kiểm tra xem cái 'dieukien' có xuất hiện tại ROI này không"""
        return self._match(roi, "dieukien", threshold)

    def detect_accessory(self, roi, threshold=0.8):
        res = self._match(roi, "accessories", threshold)
        if res == "NONE":
            return "NONE"

        # Gộp các biến thể (GiamGiat, GiamGiat1 -> GiamGiat)
        name = res.upper()
        if "GIAMGIAT" in name:
            return "GiamGiat"
        if "ANTIALUA" in name:
            return "AnTiaLua"
        if "GIAMRUNG" in name:
            return "GiamRung"
        if "ATLSMG" in name:
            return "ATLsmg"
        if "GGIATSMG" in name:
            return "GGiatSMG"
        if "GTHANHSMG" in name:
            return "GThanhSMG"
        return res

    def detect_grip(self, roi, threshold=0.8):
        res = self._match(roi, "grip", threshold)
        if res == "NONE":
            return "NONE"

        # Gộp các biến thể (tcDung, tcDung1 -> tcDung)
        name = res.upper()
        if "TCDUNG" in name:
            return "tcDung"
        if "TCHONG" in name:
            return "tcHong"
        if "TCLASER" in name:
            return "tcLaser"
        if "TCNAMCHAT" in name:
            return "tcNamChat"
        if "TCNGHIENG" in name:
            return "tcNghieng"
        if "TCNHE" in name:
            return "tcNhe"
        return res

    def detect_scope(self, roi, threshold=0.8):
        res = self._match(roi, "scopes", threshold)
        if res == "NONE":
            return "NONE"

        name = res.upper()
        # Xử lý đặc biệt cho Scope Kết Hợp
        if "SCOPEKH" in name:
            return "ScopeKH"

        # Gộp các biến thể (Scope1x, Scope1s -> Scope1)
        import re

        match = re.search(r"SCOPE(\d+)", name)
        if match:
            return "Scope" + match.group(1)

        return res

    def detect_stance(self, roi, threshold=0.6):
        res = self._match(roi, "stances", threshold)
        if res == "NONE":
            return "Stand"

        name = res.upper()
        if "STANDING" in name:
            return "Stand"
        if "CROUCHING" in name:
            return "Crouch"
        if "PRONE" in name:
            return "Prone"
        return "Stand"
