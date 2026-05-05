import cv2
import mss
import numpy as np
import os
import time


def select_roi_interactive():
    print(" === TOOL CHỌN VÙNG ROI CỰC NHANH (VIP) ===")
    print(" > [BƯỚC 1] Sếp có 5 giây để Alt-Tab vào game và bật bảng Inventory lên...")
    for i in range(5, 0, -1):
        print(f" > BẮT ĐẦU SAU: {i}...")
        time.sleep(1)

    print(" > [BƯỚC 2] Đang chụp ảnh màn hình...")
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        img = np.ascontiguousarray(np.array(sct_img)[:, :, :3], dtype=np.uint8)

    # HIỂN THỊ CỬA SỔ CHỌN ROI
    window_name = "KEO CHUOT DE CHON VUNG (ENTER DE XAC NHAN - ESC DE HUY)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Cho phép người dùng kéo thả chọn vùng
    roi = cv2.selectROI(window_name, img, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow(window_name)

    x, y, w, h = roi
    if w == 0 or h == 0:
        print(" > [!] Sếp chưa chọn vùng nào cả. Thoát tool.")
        return

    print(f"\n > [!] TOA DO DA CHON: [X={x}, Y={y}, W={w}, H={h}]")

    # BƯỚC 3: GHI VÀO ROI_STORAGE.PY
    print(" > [SYSTEM] Đang cập nhật vào roi_storage.py...")
    try:
        # Đường dẫn file tọa độ
        base_dir = os.path.dirname(os.path.dirname(__file__))
        toa_do_path = os.path.join(base_dir, "src", "detection", "roi_storage.py")

        with open(toa_do_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        # Chốt chặn độ phân giải (Lấy từ ảnh vừa chụp)
        screen_res = f"'{img.shape[1]}x{img.shape[0]}'"
        found_target_res = False
        updated_dieukien = False

        for line in lines:
            if screen_res in line:
                found_target_res = True

            if found_target_res and "'dieukien':" in line and not updated_dieukien:
                # Tìm dấu đóng ngoặc hoặc phẩy để thay thế chính xác
                new_lines.append(
                    f"                     'dieukien': [{x}, {y}, {w}, {h}]}},\n"
                )
                updated_dieukien = True
            else:
                new_lines.append(line)

        with open(toa_do_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f" > [SUCCESS] Đã cập nhật tọa độ 'dieukien' vào {screen_res}!")
        print(" > Sấy thôi sếp ơi!")

    except Exception as e:
        print(f" > [ERROR] Lỗi cập nhật file: {e}")


if __name__ == "__main__":
    select_roi_interactive()
