# KHO LƯU TRỮ TỌA ĐỘ (Cập nhật tự động bởi ToolOverlayROI)

DATA = {   '1728x1080': {   'dieukien': [569, 871, 48, 61],
                     'gun1_grip': [1337, 220, 54, 66],
                     'gun1_muzzle': [1236, 220, 53, 66],
                     'gun1_name': [1269, 76, 167, 53],
                     'gun1_scope': [1506, 101, 54, 62],
                     'gun2_grip': [1338, 447, 52, 63],
                     'gun2_muzzle': [1235, 447, 53, 66],
                     'gun2_name': [1268, 302, 169, 54],
                     'gun2_scope': [1507, 325, 55, 63],
                     'stance': [602, 954, 54, 79]},
    '1920x1080': {   'dieukien': [664, 871, 49, 60],
                     'gun1_grip': [1434, 220, 53, 65],
                     'gun1_muzzle': [1330, 220, 55, 67],
                     'gun1_name': [1365, 77, 167, 52],
                     'gun1_scope': [1602, 98, 54, 66],
                     'gun2_grip': [1432, 448, 54, 64],
                     'gun2_muzzle': [1331, 448, 54, 65],
                     'gun2_name': [1364, 302, 170, 53],
                     'gun2_scope': [1602, 323, 56, 66],
                     'stance': [699, 958, 52, 74]}}

# Helper Functions
def get_roi(resolution_key):
    return DATA.get(resolution_key, None)
