import ctypes

import cv2
import dxcam  # New
import mss
import numpy as np

from src.detection import roi_storage


# Chụp màn hình và cắt các vùng ROI cần nhận diện
class ScreenCapture:
    def __init__(self, capture_mode="MSS"):
        self.capture_mode = str(capture_mode).upper()

        # 0. Init DXCam if needed
        self.camera = None
        if self.capture_mode == "DXCAM":
            try:
                self.camera = dxcam.create(output_color="BGR")
            except Exception:
                self.capture_mode = "MSS"

        self._sct = None  # Sẽ khởi tạo lười (Lazy) trong từng luồng để an toàn
        self.bbox = {}  # Khởi tạo tường minh để linter không báo lỗi

        # Lấy độ phân giải màn hình

        user32 = ctypes.windll.user32
        self.width = user32.GetSystemMetrics(0)
        self.height = user32.GetSystemMetrics(1)
        self.resolution = (self.width, self.height)
        self.res_key = f"{self.width}x{self.height}"

        # 1. Ưu tiên lấy từ Config (Module) - TUYỆT ĐỐI KHÔNG TỰ CO GIÃN
        saved_rois = roi_storage.get_roi(self.res_key)

        if not saved_rois:
            # Fallback về 1920x1080 nếu không có tọa độ cho độ phân giải hiện tại
            saved_rois = roi_storage.get_roi("1920x1080")

        if saved_rois:
            self.rois = self.convert_list_to_dict(saved_rois)
        else:
            self.rois = {}  # Không có tọa độ thì không soi, tránh bị loạn

        # Calculate bounding box immediately
        self.calculate_bounding_box()

    def get_sct(self):
        """Khởi tạo mss.mss() riêng cho từng luồng (Thread-safe)"""
        if self._sct is None:
            self._sct = mss.mss()
        return self._sct

    def convert_list_to_dict(self, saved_rois):
        # Convert List [x,y,w,h] -> Dict {"left": x, ...}
        rois = {}
        for key, val in saved_rois.items():
            rois[key] = {
                "left": val[0],
                "top": val[1],
                "width": val[2],
                "height": val[3],
            }
        return rois

    def calculate_bounding_box(self):
        """Calculates the minimal bounding box containing all ROIs for efficient capture"""
        if not self.rois:
            return None

        l = min(r["left"] for r in self.rois.values())
        t = min(r["top"] for r in self.rois.values())
        r_max = max(r["left"] + r["width"] for r in self.rois.values())
        b_max = max(r["top"] + r["height"] for r in self.rois.values())

        self.bbox = {
            "left": l - 10,  # Small padding
            "top": t - 10,
            "width": (r_max - l) + 20,
            "height": (b_max - t) + 20,
        }

    def grab_regional_image(self):
        """Siêu nén: Chỉ chụp 1 vùng chứa mọi ROI (Cực nhạy)"""
        if not hasattr(self, "bbox") or not self.bbox:
            self.calculate_bounding_box()

        if self.capture_mode == "DXCAM" and self.camera:
            l, t, w, h = (
                self.bbox["left"],
                self.bbox["top"],
                self.bbox["width"],
                self.bbox["height"],
            )
            region = (l, t, l + w, t + h)
            frame = self.camera.grab(region=region)
            if frame is not None:
                return frame

        # MSS Regional Grab (Thread-safe)
        sct_img = self.get_sct().grab(self.bbox)
        return np.array(sct_img)[:, :, :3]  # BGR conversion

    def get_roi_from_image(self, regional_img, roi_name):
        """Cắt lát từ vùng Regional Image (Cực nhanh vì không phải chụp lại)"""
        roi = self.rois.get(roi_name)
        if not roi or regional_img is None:
            return None

        # Tọa độ tương đối so với bbox
        lx = roi["left"] - self.bbox["left"]
        ly = roi["top"] - self.bbox["top"]
        w, h = roi["width"], roi["height"]

        # Slice mảng Numpy
        return regional_img[ly : ly + h, lx : lx + w]

    def grab_screen(self):
        """Full screen capture cho debug"""
        if self.capture_mode == "DXCAM" and self.camera:
            frame = self.camera.grab()
            if frame is not None:
                return frame

        monitor = {"top": 0, "left": 0, "width": self.width, "height": self.height}
        sct_img = self.get_sct().grab(monitor)
        return np.array(sct_img)[:, :, :3]

    def debug_rois(self):
        """Vẽ ROI và BBox lên ảnh để kiểm tra tọa độ súng/phụ kiện/tư thế"""
        img = self.grab_screen()
        if not hasattr(self, "bbox"):
            self.calculate_bounding_box()

        bx, by, bw, bh = (
            self.bbox["left"],
            self.bbox["top"],
            self.bbox["width"],
            self.bbox["height"],
        )
        cv2.rectangle(img, (bx, by), (bx + bw, by + bh), (0, 0, 255), 3)
        cv2.putText(
            img, "REGION", (bx, by - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
        )

        for name, roi in self.rois.items():
            x, y, w, h = roi["left"], roi["top"], roi["width"], roi["height"]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                img, name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1
            )

        filename = "debug_roi_preview.jpg"
        cv2.imwrite(filename, img)
        return filename
