import sys
import os

# 确保工作目录正确（对于exe和脚本都适用）
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe，切换到exe所在目录
    exe_dir = os.path.dirname(sys.executable)
    os.chdir(exe_dir)
    print(f"Running as exe, working directory: {exe_dir}")
else:
    # 如果是脚本运行，切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Running as script, working directory: {script_dir}")

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from core.config_manager import ConfigManager
from core.ocr_service import OCRService
from ui.main_window import MainWindow
from ui.system_tray import SystemTray


class OCRApplication:
    """OCR应用程序主类"""
    
    def __init__(self):
        # 创建QApplication
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # 设置应用程序图标
        self._setup_app_icon()
        
        # 设置全局字体
        font = QFont("Microsoft YaHei", 9)
        self.app.setFont(font)
        
        # 检查系统托盘是否真正可用
        self.tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        print(f"System Tray Available: {self.tray_available}")
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化OCR服务
        self.ocr_service = OCRService(self.config_manager)
        
        # 初始化主窗口
        self.main_window = MainWindow(self.config_manager)
        
        # 初始化系统托盘（如果可用）
        self.system_tray = None
        if self.tray_available:
            self.system_tray = SystemTray()
        
        # 连接信号
        self._connect_signals()
        
        # 检查是否自动启动服务
        self._check_auto_start_service()
    
    def _setup_app_icon(self):
        """设置应用程序图标"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        icon_path = os.path.join(base_path, 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
            print(f"App icon set: {icon_path}")
        else:
            print(f"Icon file not found: {icon_path}")
    
    def _connect_signals(self):
        """连接信号"""
        # 系统托盘信号
        if self.system_tray:
            self.system_tray.show_window_signal.connect(self._show_main_window)
            self.system_tray.toggle_service_signal.connect(self._toggle_service)
            self.system_tray.exit_signal.connect(self._exit_application)
        
        # 主窗口信号
        self.main_window.service_toggle_signal.connect(self._toggle_service)
        
        # OCR服务信号
        self.ocr_service.log_signal.connect(self._on_log_message)
        self.ocr_service.ocr_result_signal.connect(self._on_ocr_result)
        self.ocr_service.service_started_signal.connect(self._on_service_started)
        self.ocr_service.service_stopped_signal.connect(self._on_service_stopped)
    
    def _check_auto_start_service(self):
        """检查是否自动启动服务 - 默认自动启动"""
        # 默认自动启动服务
        auto_start = self.config_manager.get_setting('auto_start_service', True)
        if auto_start:
            # 延迟启动，确保UI已经准备好
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2000, self._auto_start_service)
    
    def _auto_start_service(self):
        """自动启动服务"""
        print("Auto-starting service...")
        if self.system_tray:
            # 显示托盘消息提示服务正在启动
            self.system_tray.show_message(
                "OCR变量管理器",
                "🚀 正在启动OCR服务..."
            )
        self._toggle_service(True)
    
    def _show_main_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    def _toggle_service(self, start: bool):
        """切换服务状态"""
        try:
            if start:
                # 启动服务
                if self.ocr_service.is_running:
                    print("Service already running, skipping start")
                    return
                print("Starting OCR service...")
                success = self.ocr_service.start()
                if success:
                    print("OCR service started successfully")
                else:
                    print("Failed to start OCR service")
            else:
                # 停止服务
                if not self.ocr_service.is_running:
                    print("Service not running, skipping stop")
                    return
                print("Stopping OCR service...")
                success = self.ocr_service.stop()
                if success:
                    print("OCR service stopped successfully")
                else:
                    print("Failed to stop OCR service")
        except Exception as e:
            print(f"Error in _toggle_service: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_service_started(self):
        """服务启动回调 - 只更新UI状态，不重复启动服务"""
        print("Service started callback received")
        if self.system_tray:
            self.system_tray.set_service_status(True)
        try:
            self.main_window.set_service_status(True)
        except Exception as e:
            print(f"Warning: Could not update main window status: {e}")
        if self.system_tray:
            self.system_tray.show_message("OCR服务", "✅ 服务已启动")
    
    def _on_service_stopped(self):
        """服务停止回调 - 只更新UI状态"""
        print("Service stopped callback received")
        if self.system_tray:
            self.system_tray.set_service_status(False)
        try:
            self.main_window.set_service_status(False)
        except Exception as e:
            print(f"Warning: Could not update main window status: {e}")
    
    def _on_log_message(self, message: str, level: int):
        """日志消息回调"""
        self.main_window.add_console_log(message, level)
    
    def log_message(self, message: str, level: int = 20):
        """记录日志消息"""
        self._on_log_message(message, level)
    
    def _on_ocr_result(self, var_name: str, result: str):
        """OCR结果回调"""
        self.main_window.add_console_log(f"📊 {var_name}: {result}", 20)
    
    def _exit_application(self):
        """退出应用程序"""
        # 停止服务
        if self.ocr_service.is_running:
            self.ocr_service.stop()
        
        # 隐藏托盘图标
        if self.system_tray:
            self.system_tray.hide()
        
        # 退出应用
        self.app.quit()
    
    def run(self):
        """运行应用程序"""
        if self.system_tray:
            # 显示系统托盘
            self.system_tray.show()
            
            # 启动时不显示主窗口，只显示托盘
            # 主窗口可以通过双击托盘图标或右键菜单打开
            
            # 显示启动提示
            self.system_tray.show_message(
                "OCR变量管理器", 
                "✅ 程序已启动\n双击托盘图标打开主窗口\n服务将在后台自动启动",
                msecs=5000
            )
            
            print("Running with system tray")
        else:
            # 系统托盘不可用，显示主窗口
            print("System tray not available, showing main window")
            self.main_window.show()
        
        # 运行应用
        return self.app.exec_()


def main():
    """主函数"""
    print("程序启动中...")
    try:
        app = OCRApplication()
        print("OCRApplication 创建成功")
        sys.exit(app.run())
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
