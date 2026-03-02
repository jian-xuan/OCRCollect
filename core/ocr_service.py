import json
import logging
import threading
import time
import uvicorn
from datetime import datetime
from typing import Dict, Any, Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from PyQt5.QtCore import QObject, pyqtSignal

# 导入原有OCR功能
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common_ocr import (
    capture_screenshot, capture_all_screenshot, ocr_screenshot,
    detect_button_state, get_config, sync_data, app as fastapi_app,
    screenshot_data as common_screenshot_data
)


class OCRService(QObject):
    """OCR服务类"""
    
    # 信号定义
    log_signal = pyqtSignal(str, int)  # message, level
    ocr_result_signal = pyqtSignal(str, str)  # var_name, result
    service_started_signal = pyqtSignal()
    service_stopped_signal = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        # 使用 common_ocr 的 screenshot_data，确保 API 能返回数据
        self.screenshot_data = common_screenshot_data
        self.api_server_thread = None
        self.api_server = None
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger("OCRService")
        self.logger.setLevel(logging.INFO)
        
        # 自定义日志处理器，将日志发送到UI
        class QtLogHandler(logging.Handler):
            def __init__(self, service):
                super().__init__()
                self.service = service
            
            def emit(self, record):
                msg = self.format(record)
                level = record.levelno
                self.service.log_signal.emit(msg, level)
        
        handler = QtLogHandler(self)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        self.logger.addHandler(handler)
    
    def _start_api_server(self):
        """启动FastAPI服务器"""
        try:
            self.log_signal.emit("🚀 正在启动FastAPI服务...", 20)
            
            # 完全禁用uvicorn的日志系统，避免与PyInstaller冲突
            import logging
            # 禁用所有uvicorn相关的logger
            for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "uvicorn.asgi", "fastapi"]:
                logger = logging.getLogger(logger_name)
                logger.handlers = []  # 清除所有处理器
                logger.filters = []   # 清除所有过滤器
                logger.propagate = False  # 阻止传播到父logger
                logger.setLevel(logging.ERROR)  # 只显示错误级别
                # 添加一个空的NullHandler，防止"No handler found"警告
                logger.addHandler(logging.NullHandler())
            
            # 使用最简单的配置运行uvicorn
            uvicorn.run(
                fastapi_app, 
                host="0.0.0.0", 
                port=8000, 
                log_level="critical",  # 只显示关键错误
                access_log=False,
                use_colors=False,  # 禁用颜色，避免某些终端问题
                loop="asyncio"  # 使用标准asyncio循环
            )
        except Exception as e:
            self.log_signal.emit(f"❌ FastAPI服务启动失败: {e}", 40)
    
    def start(self):
        """启动OCR服务"""
        # 使用锁防止重复启动
        if hasattr(self, '_starting') and self._starting:
            self.logger.warning("服务正在启动中，请稍候...")
            return False
        
        if self.is_running:
            self.logger.warning("服务已经在运行中")
            return False
        
        self._starting = True
        
        try:
            self.log_signal.emit("🚀 正在启动OCR服务...", 20)
            
            # 1. 先标记为运行中（防止重复启动）
            self.is_running = True
            
            # 2. 启动FastAPI服务器（在后台线程）
            self.log_signal.emit("📡 正在启动FastAPI服务 (http://0.0.0.0:8000)...", 20)
            self.api_server_thread = threading.Thread(target=self._start_api_server, daemon=True)
            self.api_server_thread.start()
            
            # 3. 添加定时任务
            self.log_signal.emit("⏰ 正在配置定时任务...", 20)
            self.scheduler.add_job(
                self._sync_data_job, 
                CronTrigger(minute='00,10,20,30,40,50', second='20')
            )
            self.scheduler.add_job(
                self._update_screenshot_data_job, 
                IntervalTrigger(seconds=30)
            )
            
            # 4. 启动调度器
            self.scheduler.start()
            
            self.log_signal.emit("✅ OCR服务启动完成！", 20)
            self.log_signal.emit("📝 API地址: http://localhost:8000", 20)
            self.log_signal.emit("📊 数据接口: http://localhost:8000/screenshot_data", 20)
            
            # 5. 发射信号（只发射一次）
            self.service_started_signal.emit()
            
            # 6. 延迟后执行初始数据更新
            threading.Thread(target=self._initial_task, daemon=True).start()
            
            self._starting = False
            return True
        except Exception as e:
            self.is_running = False
            self._starting = False
            self.logger.error(f"启动服务失败: {e}")
            self.log_signal.emit(f"❌ 启动服务失败: {e}", 40)
            return False
    
    def stop(self):
        """停止OCR服务"""
        if not self.is_running:
            return True
        
        try:
            # 停止调度器
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("OCR服务已停止")
            self.service_stopped_signal.emit()
            return True
        except Exception as e:
            self.logger.error(f"停止服务失败: {e}")
            return False
    
    def _initial_task(self):
        """初始任务"""
        time.sleep(3)  # 等待API服务器完全启动
        self.logger.info("执行初始数据更新...")
        self._update_screenshot_data_job()
    
    def _sync_data_job(self):
        """同步数据任务"""
        try:
            self.logger.info(f"同步数据: {self.screenshot_data}")
        except Exception as e:
            self.logger.error(f"同步数据失败: {e}")
    
    def _update_screenshot_data_job(self):
        """更新截图数据任务"""
        try:
            config = self.config_manager.config
            regions = config.get('regions', [])
            buttons = config.get('buttons', [])
            ocr_url = config.get('ocr_url', 'http://127.0.0.1:1224/api/ocr')
            show_log = config.get('show_log', False)
            
            # 处理OCR区域
            for region in regions:
                try:
                    region_name, base64_image = capture_screenshot(region)
                    result = ocr_screenshot(base64_image, ocr_url)
                    
                    if show_log:
                        self.logger.info(f"OCR结果 {region_name}: {result}")
                    
                    self.screenshot_data[region_name] = result
                    self.ocr_result_signal.emit(region_name, str(result))
                    
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"获取截图失败 {region['name']}: {e}")
                    self.screenshot_data[region['name']] = -1
            
            # 处理按钮
            for button in buttons:
                try:
                    result = detect_button_state(button)
                    self.logger.info(f"按钮状态 {button['name']}: {result}")
                    self.screenshot_data[button['name']] = result
                    self.ocr_result_signal.emit(button['name'], str(result))
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"检测按钮失败 {button['name']}: {e}")
                    self.screenshot_data[button['name']] = -1
            
            # 全屏截图
            try:
                name, base64_image = capture_all_screenshot()
                self.screenshot_data['image'] = base64_image
            except Exception as e:
                self.logger.error(f"全屏截图失败: {e}")
        
        except Exception as e:
            self.logger.error(f"更新截图数据失败: {e}")
    
    def get_screenshot_data(self) -> Dict[str, Any]:
        """获取截图数据"""
        return self.screenshot_data.copy()
