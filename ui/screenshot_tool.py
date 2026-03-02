from PyQt5.QtWidgets import QWidget, QApplication, QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint, QObject
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QPixmap, QScreen


class ScreenshotOverlay(QWidget):
    """截图覆盖层窗口"""
    
    region_selected = pyqtSignal(int, int, int, int, QPixmap)  # x, y, width, height, screenshot
    cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        self.start_pos = None
        self.end_pos = None
        self.is_drawing = False
        self.screenshot = None
        self.selected_region = None
        
        # 获取屏幕几何信息
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geometry)
        
        # 捕获屏幕截图
        self._capture_screen()
    
    def _capture_screen(self):
        """捕获屏幕截图"""
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
    
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        
        # 绘制半透明黑色背景
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        if self.is_drawing and self.start_pos and self.end_pos:
            # 计算选区
            rect = self._get_selection_rect()
            
            # 绘制选区内的原图
            painter.drawPixmap(rect, self.screenshot, rect)
            
            # 绘制选区边框
            pen = QPen(QColor(0, 150, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # 绘制坐标信息
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Microsoft YaHei", 10)
            painter.setFont(font)
            
            text = f"X: {rect.x()}, Y: {rect.y()}, W: {rect.width()}, H: {rect.height()}"
            text_rect = painter.boundingRect(rect, Qt.AlignLeft, text)
            text_rect.moveTo(rect.x(), rect.y() - 25)
            painter.fillRect(text_rect, QColor(0, 0, 0, 180))
            painter.drawText(text_rect, Qt.AlignCenter, text)
    
    def _get_selection_rect(self):
        """获取选区矩形"""
        if not self.start_pos or not self.end_pos:
            return QRect()
        
        x1, y1 = self.start_pos.x(), self.start_pos.y()
        x2, y2 = self.end_pos.x(), self.end_pos.y()
        
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        return QRect(x, y, width, height)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_drawing = True
            self.update()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_drawing:
            self.end_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.end_pos = event.pos()
            self.is_drawing = False
            
            rect = self._get_selection_rect()
            if rect.width() > 10 and rect.height() > 10:
                # 保存选定区域信息
                self.selected_region = {
                    'x': rect.x(),
                    'y': rect.y(),
                    'width': rect.width(),
                    'height': rect.height(),
                    'pixmap': self.screenshot.copy(rect)
                }
                # 显示预览对话框，不关闭覆盖层
                self._show_preview()
            else:
                # 区域太小，取消选择
                self.cancelled.emit()
                self.close()
    
    def _show_preview(self):
        """显示预览对话框"""
        if not self.selected_region:
            return
        
        # 创建预览对话框
        preview = ScreenshotPreviewDialog(
            self.selected_region['x'],
            self.selected_region['y'],
            self.selected_region['width'],
            self.selected_region['height'],
            self.selected_region['pixmap'],
            self
        )
        
        # 连接信号
        preview.confirmed.connect(self._on_preview_confirmed)
        preview.cancelled.connect(self._on_preview_cancelled)
        
        # 显示对话框（非模态，但保持在最前）
        preview.show()
        preview.raise_()
        preview.activateWindow()
    
    def _on_preview_confirmed(self):
        """预览确认"""
        if self.selected_region:
            self.region_selected.emit(
                self.selected_region['x'],
                self.selected_region['y'],
                self.selected_region['width'],
                self.selected_region['height'],
                self.selected_region['pixmap']
            )
        self.close()
    
    def _on_preview_cancelled(self):
        """预览取消"""
        # 清除选择，允许重新选择
        self.selected_region = None
        self.start_pos = None
        self.end_pos = None
        self.update()
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key_Escape:
            self.cancelled.emit()
            self.close()


class ScreenshotPreviewDialog(QDialog):
    """截图预览对话框"""
    
    confirmed = pyqtSignal()
    cancelled = pyqtSignal()
    
    def __init__(self, x, y, width, height, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("确认截图区域")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(450, 400)
        
        self.x, self.y, self.width, self.height = x, y, width, height
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #4834d4;
                border-radius: 12px;
            }
            QLabel {
                font-size: 14px;
                color: #2c3e50;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #4834d4;
            }
            QLabel#coord {
                font-family: 'Consolas', monospace;
                background-color: #f8f9fa;
                padding: 8px 12px;
                border-radius: 6px;
                color: #4834d4;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel("📷 确认截图区域")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 坐标信息
        coord_text = f"X: {x},  Y: {y},  宽度: {width},  高度: {height}"
        coord_label = QLabel(coord_text)
        coord_label.setObjectName("coord")
        coord_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(coord_label)
        
        # 预览图
        preview_frame = QLabel()
        preview_frame.setAlignment(Qt.AlignCenter)
        preview_frame.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        # 缩放预览图
        scaled_pixmap = pixmap.scaled(380, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        preview_frame.setPixmap(scaled_pixmap)
        preview_frame.setMinimumSize(400, 240)
        layout.addWidget(preview_frame)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        
        self.cancel_btn = QPushButton("❌ 重新选择")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        
        self.confirm_btn = QPushButton("✅ 确认使用")
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.confirm_btn.clicked.connect(self._on_confirm)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.confirm_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
    
    def _on_confirm(self):
        self.confirmed.emit()
        self.accept()
    
    def _on_cancel(self):
        self.cancelled.emit()
        self.reject()


class ScreenshotTool(QObject):
    """截图工具类"""
    
    region_captured = pyqtSignal(int, int, int, int)  # x, y, width, height
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay = None
    
    def start_screenshot(self):
        """开始截图"""
        self.overlay = ScreenshotOverlay()
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.cancelled.connect(self._on_cancelled)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay.activateWindow()
    
    def _on_region_selected(self, x, y, width, height, pixmap):
        """区域被选中并确认"""
        self.region_captured.emit(x, y, width, height)
    
    def _on_cancelled(self):
        """用户取消"""
        self.cancelled.emit()
