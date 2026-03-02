import os
import sys


def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    适用于开发环境和PyInstaller打包后的环境
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境，使用当前工作目录
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(base_path, relative_path)


def get_executable_dir():
    """
    获取可执行文件所在的目录
    """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def get_config_path():
    """
    获取配置文件的路径
    配置文件应该与可执行文件在同一目录
    """
    exe_dir = get_executable_dir()
    return os.path.join(exe_dir, 'config.yaml')
