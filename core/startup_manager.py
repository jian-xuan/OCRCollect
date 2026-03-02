import os
import sys
import winshell
from win32com.client import Dispatch


class StartupManager:
    """开机自启管理器"""
    
    def __init__(self):
        # 获取启动文件夹路径
        self.startup_folder = winshell.startup()
        # 快捷方式名称
        self.shortcut_name = "OCR变量管理器.lnk"
        self.shortcut_path = os.path.join(self.startup_folder, self.shortcut_name)
    
    def is_startup_enabled(self) -> bool:
        """检查是否已设置开机自启"""
        return os.path.exists(self.shortcut_path)
    
    def enable_startup(self) -> bool:
        """启用开机自启"""
        try:
            # 获取当前程序路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe
                program_path = sys.executable
            else:
                # 如果是脚本运行
                program_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))
            
            # 获取程序所在目录
            work_dir = os.path.dirname(program_path)
            
            # 创建快捷方式
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(self.shortcut_path)
            
            if program_path.endswith('.py'):
                # 如果是Python脚本，使用pythonw.exe启动（无窗口）
                pythonw_path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                shortcut.Targetpath = pythonw_path
                shortcut.Arguments = f'"{program_path}"'
            else:
                # 如果是exe
                shortcut.Targetpath = program_path
            
            # 设置工作目录（关键：确保能正确读取config.yaml）
            shortcut.WorkingDirectory = work_dir
            
            # 设置图标（如果有的话）
            icon_path = os.path.join(work_dir, 'resources', 'icon.ico')
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            
            shortcut.save()
            
            return True
        except Exception as e:
            print(f"启用开机自启失败: {e}")
            return False
    
    def disable_startup(self) -> bool:
        """禁用开机自启"""
        try:
            if os.path.exists(self.shortcut_path):
                os.remove(self.shortcut_path)
            return True
        except Exception as e:
            print(f"禁用开机自启失败: {e}")
            return False
    
    def toggle_startup(self, enable: bool) -> bool:
        """切换开机自启状态"""
        if enable:
            return self.enable_startup()
        else:
            return self.disable_startup()
