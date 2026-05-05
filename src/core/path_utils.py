import os
import sys


def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and for Nuitka/PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # Chế độ đóng gói: __file__ sẽ trỏ vào thư mục tạm mà Nuitka xả nén ra
        base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    # Chế độ phát triển (Local)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    return os.path.join(project_root, relative_path)
