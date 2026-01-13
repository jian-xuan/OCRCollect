import win32gui
import win32con
import time

def get_window_handle(title):
    """根据窗口标题获取窗口句柄"""
    return win32gui.FindWindow(None, title)

def set_window_position(hwnd, x, y, width, height):
    """设置窗口的位置和大小"""
    win32gui.MoveWindow(hwnd, x, y, width, height, True)

def main():
    # 等待用户打开两个窗口
    print("请打开两个需要并排显示的窗口，并确保它们的标题栏可见。")
    input("按回车键继续...")

    # 获取两个窗口的标题
    title1 = input("请输入第一个窗口的标题：")
    title2 = input("请输入第二个窗口的标题：")

    # 获取窗口句柄
    hwnd1 = get_window_handle(title1)
    hwnd2 = get_window_handle(title2)

    if not hwnd1 or not hwnd2:
        print("无法找到指定的窗口，请检查窗口标题是否正确。")
        return

    # 获取屏幕分辨率
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    # 计算窗口大小
    half_width = screen_width // 2

    # 设置窗口位置和大小
    set_window_position(hwnd1, 0, 0, half_width, screen_height)
    set_window_position(hwnd2, half_width, 0, half_width, screen_height)

    print("窗口已并排显示。")

if __name__ == "__main__":
    main()