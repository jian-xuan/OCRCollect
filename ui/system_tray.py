from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QIcon
import os


class SystemTray(QObject):
    """系统托盘类"""
    
    # 信号定义
    show_window_signal = pyqtSignal()
    toggle_service_signal = pyqtSignal()
    exit_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(parent)
        self.is_service_running = False
        self._setup_icon()
        self._setup_menu()
    
    def _setup_icon(self):
        """设置托盘图标"""
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_path, 'resources', 'logo.png')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(QApplication.style().standardIcon(0))
    
    def _setup_menu(self):
        """设置托盘菜单"""
        self.menu = QMenu()
        
        # 显示主窗口
        self.show_action = QAction("🏠 显示主窗口", self)
        self.show_action.triggered.connect(self._on_show_window)
        self.menu.addAction(self.show_action)
        
        self.menu.addSeparator()
        
        # 启动/停止服务
        self.service_action = QAction("▶ 启动服务", self)
        self.service_action.triggered.connect(self._on_toggle_service)
        self.menu.addAction(self.service_action)
        
        self.menu.addSeparator()
        
        # 退出
        self.exit_action = QAction("❌ 退出程序", self)
        self.exit_action.triggered.connect(self._on_exit)
        self.menu.addAction(self.exit_action)
        
        self.tray_icon.setContextMenu(self.menu)
        
        # 双击显示窗口
        self.tray_icon.activated.connect(self._on_activated)
    
    def _on_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window_signal.emit()
    
    def _on_show_window(self):
        """显示窗口"""
        self.show_window_signal.emit()
    
    def _on_toggle_service(self):
        """切换服务状态"""
        self.toggle_service_signal.emit()
    
    def _on_exit(self):
        """退出程序"""
        self.exit_signal.emit()
    
    def show(self):
        """显示托盘图标"""
        self.tray_icon.show()
    
    def hide(self):
        """隐藏托盘图标"""
        self.tray_icon.hide()
    
    def set_service_status(self, running: bool):
        """设置服务状态"""
        self.is_service_running = running
        if running:
            self.service_action.setText("⏹ 停止服务")
        else:
            self.service_action.setText("▶ 启动服务")
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, msecs=3000):
        """显示气泡消息"""
        self.tray_icon.showMessage(title, message, icon, msecs)
