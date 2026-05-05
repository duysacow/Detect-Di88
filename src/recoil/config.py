import importlib
import re
from .base_recoil_data import BaseRecoilData
from pathlib import Path

# Pre-load data once
from . import base_recoil_data as BaseRecoilDataModule


# Quản lý đọc và tra cứu cấu hình recoil
class RecoilConfig:
    def __init__(self):
        # 1. NGUỒN DỮ LIỆU TUYỆT ĐỐI
        self.data = BaseRecoilDataModule.BaseRecoilData
        self.cache = {}

    def reload_data(self):
        """Reloads base_recoil_data"""
        try:
            from . import base_recoil_data as BaseRecoilDataModule

            importlib.reload(BaseRecoilDataModule)
            self.data = BaseRecoilDataModule.BaseRecoilData

            self.cache.clear()
            return True
        except Exception:
            return False

    def get_attr(self, obj, attr, default=None):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def get_master_multiplier(self, gun_data):
        """
        Calculates Final Fixed Multiplier (Base * Scope * Grip * Muzzle)
        """
        try:
            # 1. Tìm súng (Case-insensitive)
            w_name_raw = str(gun_data.get("name", "NONE")).strip()
            weapons_dict = getattr(self.data, "Weapons", {})
            w_name = w_name_raw if w_name_raw in weapons_dict else w_name_raw.upper()

            if w_name not in weapons_dict:
                return 1.0
            w_data = weapons_dict[w_name]

            # B. Scope (Map tên Reddot, 2x, 3x... về Scope1/2/3... để tra cứu hệ số)
            sc_val_raw = str(gun_data.get("scope", "NONE"))
            sc_val_upper = sc_val_raw.upper()

            # Bảng ánh xạ tên nhận diện sang Key trong ClassBaseRecoil.py
            scope_map = {
                "REDDOT": "Scope1",
                "HOLOSIGHT": "Scope1",
                "NONE": "Scope1",
                "2X": "Scope2",
                "3X": "Scope3",
                "4X": "Scope4",
                "6X": "Scope6",
                "8X": "Scope8",
            }

            if "KH" in sc_val_upper:
                match = re.search(r"\d+", sc_val_upper)
                digit = match.group() if match else "1"
                sc_key = f"ScopeKH{digit}"  # Tách riêng thành ScopeKH1, ScopeKH4
            else:
                # Tìm trong bảng map, nếu không thấy thì thử phỏng đoán hoặc CamelCase
                sc_key = scope_map.get(sc_val_upper)
                if not sc_key:
                    val = sc_val_raw.split("_")[0]
                    sc_key = (
                        val.capitalize() if val.lower().startswith("scope") else val
                    )

            scope_mult = getattr(self.data, "scope_multipliers", {}).get(sc_key, 1.0)

            # C. Tay cầm (Case-insensitive lookup)
            g_key_raw = gun_data.get("grip", "NONE")
            grips_map = getattr(self.data, "grips", {})
            grip_match = next(
                (v for k, v in grips_map.items() if k.lower() == g_key_raw.lower()),
                None,
            )
            grip_mult = float(
                grip_match if grip_match is not None else grips_map.get("NONE", 1.25)
            )

            # D. Nòng (Case-insensitive lookup)
            m_key_raw = gun_data.get("accessories", "NONE")
            acc_map = getattr(self.data, "accessories", {})
            acc_match = next(
                (v for k, v in acc_map.items() if k.lower() == m_key_raw.lower()), None
            )
            muzzle_mult = float(
                acc_match if acc_match is not None else acc_map.get("NONE", 1.25)
            )

            total = scope_mult * grip_mult * muzzle_mult

            # 4. Áp dụng Strength % (Hệ số độ mạnh cho từng Scope)
            strength_map = {
                "Scope1": "Strength_Normal",
                "ScopeKH1": "Strength_Normal",
                "Scope2": "Strength_2x",
                "Scope3": "Strength_3x",
                "Scope4": "Strength_4x",
                "ScopeKH4": "Strength_4x",
                "Scope6": "Strength_6x",
                "Scope8": "Strength_8x",
            }
            str_attr = strength_map.get(sc_key)
            if str_attr:
                strength_percent = getattr(self.data, str_attr, 100)
                total = total * (float(strength_percent) / 100.0)

            return total

        except Exception:
            return 1.0

    def get_all_stance_multipliers(self, w_name):
        """Lấy bộ hệ số tư thế của súng từ ClassBaseRecoil"""
        try:
            weapons_dict = getattr(self.data, "Weapons", {})
            w_key = w_name if w_name in weapons_dict else w_name.upper()
            if w_key not in weapons_dict:
                return {"Stand": 1.25, "Crouch": 1.0, "Prone": 0.7}

            w_data = weapons_dict[w_key]
            st_data = self.get_attr(w_data, "stance_multipliers", {})

            return {
                "Stand": self.get_attr(st_data, "Stand", 1.0),
                "Crouch": self.get_attr(st_data, "Crouch", 1.0),
                "Prone": self.get_attr(st_data, "Prone", 1.0),
            }

        except:
            return {"Stand": 1.25, "Crouch": 1.0, "Prone": 0.7}

    def get_base_table(self, w_name):
        """Lấy bảng pattern gốc cho súng (BaseTable)"""
        try:
            weapons_dict = getattr(self.data, "Weapons", {})
            w_key = w_name if w_name in weapons_dict else w_name.upper()
            if w_key not in weapons_dict:
                return []
            return self.get_attr(weapons_dict[w_key], "BaseTable", [])
        except:
            return []

    def get_raw_pattern(self, base_table):

        raw_pattern = []
        for entry in base_table:
            if len(entry) == 2:
                val, count = entry
                for _ in range(int(count)):
                    raw_pattern.append(val)
            elif len(entry) == 1:
                raw_pattern.append(entry[0])
        return raw_pattern
