import math

class SensitivityCalculator:
    def __init__(self):
        self.base_vert_sens = 1.0
        # Mốc chuẩn - bộ JSON được train ở Sens = 30.0
        self.base_sens = 30.0

    def calculate_sens_multiplier(self, pubg_config, gun_info, hybrid_mode="Scope1"):
        """
        Công thức ĐƯỜNG CONG MŨ của PUBG (uniform cho mọi scope):
            multiplier = 10 ^ ((base_sens - current_sens) / 50)
        
        - Sens tăng (> 30) → multiplier < 1 → ghìm nhẹ lại (cursor đã nhanh hơn)
        - Sens giảm (< 30) → multiplier > 1 → ghìm mạnh thêm (cursor đã chậm hơn)
        - Sens = 30       → multiplier = 1 → giữ nguyên (baseline gốc)
        """
        # 1. Hệ số Vertical (Tuyến tính nghịch đảo - giữ nguyên vì đây là multiplier tuyến tính)
        curr_vert = pubg_config.vertical_multiplier
        if curr_vert <= 0:
            curr_vert = self.base_vert_sens
        vert_factor = self.base_vert_sens / curr_vert

        # 2. Phân rã Sens key theo loại Scope AI nhận diện (Sửa để khớp "Scope2", "Scope3"...)
        scope_name = gun_info.get("scope", "NONE").upper()
        sens_key = "Scoping"  # Mặc định: Red Dot / Holo
        
        if "NONE" in scope_name:
            sens_key = "Targeting"
        elif "2" in scope_name: sens_key = "Scope2X" 
        elif "3" in scope_name: sens_key = "Scope3X"
        elif "4" in scope_name: sens_key = "Scope4X"
        elif "6" in scope_name: sens_key = "Scope3X" # Map X6 về X3 theo ý sếp
        elif "8" in scope_name: sens_key = "Scope3X" # Map X8 về X3 luôn
        elif "15" in scope_name: sens_key = "Scope3X"


        if "SCOPEKH" in scope_name:
            sens_key = "Scope4X" if hybrid_mode == "Scope4" else "Scoping"

        # 3. Lấy giá trị UI hiện tại (0-100)
        in_game_sens = pubg_config.sensitivities.get(sens_key, self.base_sens)
        if in_game_sens <= 0:
            in_game_sens = self.base_sens

        # 4. Tính hệ số bù theo đường cong mũ 10 (Giống hệt công thức Scoping)
        scope_factor = math.pow(10, (self.base_sens - in_game_sens) / 50.0)



        return scope_factor * vert_factor


