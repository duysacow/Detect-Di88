import os
import sys
import ctypes


def optimize_system():
    """Sets CPU affinity to the last core and lowers process priority for gaming performance."""
    try:
        kernel32 = ctypes.windll.kernel32

        # Define Argument/Return types for Windows API
        # SetProcessAffinityMask(HANDLE hProcess, DWORD_PTR dwProcessAffinityMask)
        kernel32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        kernel32.SetProcessAffinityMask.restype = ctypes.c_int

        # SetPriorityClass(HANDLE hProcess, DWORD dwPriorityClass)
        kernel32.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel32.SetPriorityClass.restype = ctypes.c_int

        # 1. Get CPU Count (Logical Processors)
        cpu_count = os.cpu_count()
        if not cpu_count:
            return

        # 2. Get Current Process Handle (Pseudo-handle -1 stands for current process)
        handle = kernel32.GetCurrentProcess()

        # 3. Set CPU Affinity (Last Core only)
        # Giúp tránh giật lag khi chơi game bằng cách chạy Macro trên nhân CPU cuối cùng
        last_core_index = cpu_count - 1
        mask = 1 << last_core_index
        kernel32.SetProcessAffinityMask(handle, mask)

        # 4. Set Priority Class (High Priority: 0x80)
        # Ưu tiên CPU cao cho Macro để soi ảnh mượt mà nhất
        kernel32.SetPriorityClass(handle, 0x80)

        print(f"[SYSTEM] Optimized: Affinity Core {last_core_index}, Priority HIGH")
    except Exception as e:
        print(f"[SYSTEM] Optimization failed: {e}")


if __name__ == "__main__":
    optimize_system()
    input("\nPress Enter to Exit...")
