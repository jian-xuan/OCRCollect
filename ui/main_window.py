from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QPushButton, QSpinBox, QDoubleSpinBox, QTabWidget,
    QTextEdit, QGroupBox, QFormLayout, QSplitter,
    QMessageBox, QInputDialog, QFileDialog, QComboBox,
    QCheckBox, QDialog, QDialogButtonBox, QApplication,
    QFrame, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFont
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.startup_manager import StartupManager
from ui.screenshot_tool import ScreenshotTool
from resources.styles import get_application_style


class AddVariableDialog(QDialog):
    """添加变量对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加变量")
        self.setMinimumWidth(350)
        self.setStyleSheet(get_application_style())

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("添加新变量")
        title.setObjectName("title_label")
        layout.addWidget(title)

        subtitle = QLabel("选择变量类型并输入名称")
        subtitle.setObjectName("subtitle_label")
        layout.addWidget(subtitle)

        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.type_combo = QComboBox()
        self.type_combo.addItem("📝 OCR文字识别", "ocr")
        self.type_combo.addItem("🔘 Button按钮识别", "button")
        form_layout.addRow("变量类型:", self.type_combo)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入变量名称")
        form_layout.addRow("变量名称:", self.name_edit)

        layout.addLayout(form_layout)
        layout.addStretch()

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        return {
            'type': self.type_combo.currentData(),
            'name': self.name_edit.text().strip()
        }


class MainWindow(QMainWindow):
    """主窗口"""

    service_toggle_signal = pyqtSignal(bool)
    exit_signal = pyqtSignal()

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.startup_manager = StartupManager()
        self.screenshot_tool = ScreenshotTool(self)
        self.current_variable = None
        self.is_service_running = False

        self._init_ui()
        self._load_variables()
        self._connect_signals()
        self._apply_styles()

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("OCR变量管理器")
        self.setMinimumSize(1000, 700)
        
        # 设置窗口图标
        self._setup_window_icon()

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 顶部标题栏
        header = self._create_header()
        main_layout.addLayout(header)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        main_layout.addWidget(splitter, 1)

        # 左侧：变量列表
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧：变量详情和日志
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割比例
        splitter.setSizes([320, 680])

        # 底部状态栏
        footer = self._create_footer()
        main_layout.addLayout(footer)
    
    def _setup_window_icon(self):
        """设置窗口图标"""
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        icon_path = os.path.join(base_path, 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _create_header(self):
        """创建顶部标题栏"""
        layout = QHBoxLayout()

        # 标题
        title = QLabel("🔍 OCR变量管理器")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 8px 0;
        """)
        layout.addWidget(title)

        layout.addStretch()

        # 服务控制按钮
        self.service_btn = QPushButton("▶ 启动服务")
        self.service_btn.setObjectName("success_btn")
        self.service_btn.setMinimumWidth(120)
        self.service_btn.clicked.connect(self._on_service_toggle)
        layout.addWidget(self.service_btn)

        # 隐藏按钮
        hide_btn = QPushButton("🗕 隐藏")
        hide_btn.setObjectName("secondary_btn")
        hide_btn.clicked.connect(self.hide)
        layout.addWidget(hide_btn)

        return layout

    def _create_left_panel(self):
        """创建左侧面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 变量列表标题
        header_layout = QHBoxLayout()
        list_title = QLabel("📋 变量列表")
        list_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        header_layout.addWidget(list_title)

        # 变量计数
        self.var_count_label = QLabel("(0)")
        self.var_count_label.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(self.var_count_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 变量列表
        self.variable_list = QListWidget()
        self.variable_list.setMinimumWidth(300)
        layout.addWidget(self.variable_list)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("➕ 添加")
        self.add_btn.setObjectName("success_btn")
        self.add_btn.clicked.connect(self._on_add_variable)
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton("🗑 删除")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.clicked.connect(self._on_delete_variable)
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

        return widget

    def _create_right_panel(self):
        """创建右侧面板"""
        self.tab_widget = QTabWidget()

        # 变量详情选项卡
        self.detail_tab = self._create_detail_tab()
        self.tab_widget.addTab(self.detail_tab, "⚙️ 变量详情")

        # 控制台日志选项卡（合并OCR和调试日志）
        self.console_tab = self._create_console_tab()
        self.tab_widget.addTab(self.console_tab, "📟 控制台")

        # 设置选项卡
        self.settings_tab = self._create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "🔧 设置")

        return self.tab_widget

    def _create_detail_tab(self):
        """创建变量详情选项卡"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 变量信息卡片
        info_card = QGroupBox("变量信息")
        info_layout = QFormLayout()
        info_layout.setSpacing(12)

        self.name_label = QLabel("未选择变量")
        self.name_label.setStyleSheet("font-weight: bold; color: #4834d4;")
        info_layout.addRow("变量名称:", self.name_label)

        self.type_label = QLabel("-")
        info_layout.addRow("变量类型:", self.type_label)

        info_card.setLayout(info_layout)
        layout.addWidget(info_card)

        # 区域设置卡片
        region_card = QGroupBox("区域设置")
        region_layout = QGridLayout()
        region_layout.setSpacing(12)

        # X, Y, 宽度, 高度
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.x_spin.valueChanged.connect(self._on_value_changed)
        region_layout.addWidget(QLabel("X 坐标:"), 0, 0)
        region_layout.addWidget(self.x_spin, 0, 1)

        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        self.y_spin.valueChanged.connect(self._on_value_changed)
        region_layout.addWidget(QLabel("Y 坐标:"), 0, 2)
        region_layout.addWidget(self.y_spin, 0, 3)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 9999)
        self.width_spin.valueChanged.connect(self._on_value_changed)
        region_layout.addWidget(QLabel("宽度:"), 1, 0)
        region_layout.addWidget(self.width_spin, 1, 1)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 9999)
        self.height_spin.valueChanged.connect(self._on_value_changed)
        region_layout.addWidget(QLabel("高度:"), 1, 2)
        region_layout.addWidget(self.height_spin, 1, 3)

        region_card.setLayout(region_layout)
        layout.addWidget(region_card)

        # 截图按钮
        self.screenshot_btn = QPushButton("📷 截图获取位置")
        self.screenshot_btn.setMinimumHeight(45)
        self.screenshot_btn.setStyleSheet("""
            QPushButton {
                background-color: #0984e3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74b9ff;
            }
        """)
        self.screenshot_btn.clicked.connect(self._on_screenshot)
        layout.addWidget(self.screenshot_btn)

        # Button特有设置
        self.button_settings_card = QGroupBox("按钮设置")
        button_layout = QFormLayout()
        button_layout.setSpacing(12)

        # On图片
        on_layout = QHBoxLayout()
        self.on_image_edit = QLineEdit()
        self.on_image_edit.setPlaceholderText("选择按钮开启状态的图片")
        on_layout.addWidget(self.on_image_edit)
        self.on_image_btn = QPushButton("浏览...")
        self.on_image_btn.clicked.connect(lambda: self._select_image('on_image'))
        on_layout.addWidget(self.on_image_btn)
        button_layout.addRow("On 图片:", on_layout)

        # Off图片
        off_layout = QHBoxLayout()
        self.off_image_edit = QLineEdit()
        self.off_image_edit.setPlaceholderText("选择按钮关闭状态的图片")
        off_layout.addWidget(self.off_image_edit)
        self.off_image_btn = QPushButton("浏览...")
        self.off_image_btn.clicked.connect(lambda: self._select_image('off_image'))
        off_layout.addWidget(self.off_image_btn)
        button_layout.addRow("Off 图片:", off_layout)

        # 阈值
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setSingleStep(0.05)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setValue(0.8)
        self.threshold_spin.valueChanged.connect(self._on_value_changed)
        button_layout.addRow("匹配阈值:", self.threshold_spin)

        self.button_settings_card.setLayout(button_layout)
        layout.addWidget(self.button_settings_card)

        layout.addStretch()

        scroll.setWidget(widget)
        return scroll

    def _create_console_tab(self):
        """创建控制台日志选项卡（合并OCR和调试日志）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 工具栏
        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("📟 控制台输出"))
        toolbar.addStretch()

        # 日志级别过滤
        toolbar.addWidget(QLabel("日志级别:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem("DEBUG", 10)
        self.log_level_combo.addItem("INFO", 20)
        self.log_level_combo.addItem("WARNING", 30)
        self.log_level_combo.addItem("ERROR", 40)
        self.log_level_combo.setCurrentIndex(1)
        toolbar.addWidget(self.log_level_combo)

        # 清空按钮
        clear_btn = QPushButton("🗑 清空")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.clicked.connect(self._clear_console)
        toolbar.addWidget(clear_btn)

        # 复制按钮
        copy_btn = QPushButton("📋 复制")
        copy_btn.clicked.connect(self._copy_console)
        toolbar.addWidget(copy_btn)

        layout.addLayout(toolbar)

        # 日志显示区域
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        layout.addWidget(self.console_text)

        return widget

    def _create_settings_tab(self):
        """创建设置选项卡"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # OCR设置
        ocr_group = QGroupBox("OCR设置")
        ocr_layout = QFormLayout()
        ocr_layout.setSpacing(12)

        self.ocr_url_edit = QLineEdit()
        self.ocr_url_edit.setText(self.config_manager.get_ocr_url())
        self.ocr_url_edit.editingFinished.connect(self._on_ocr_url_changed)
        ocr_layout.addRow("OCR服务地址:", self.ocr_url_edit)

        self.show_log_check = QCheckBox("启用详细日志输出")
        self.show_log_check.setChecked(self.config_manager.get_show_log())
        self.show_log_check.stateChanged.connect(self._on_show_log_changed)
        ocr_layout.addRow(self.show_log_check)

        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)

        # 启动设置
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout()
        startup_layout.setSpacing(12)

        self.auto_startup_check = QCheckBox("开机时自动启动程序")
        self.auto_startup_check.setChecked(self.startup_manager.is_startup_enabled())
        self.auto_startup_check.stateChanged.connect(self._on_auto_startup_changed)
        startup_layout.addRow(self.auto_startup_check)

        self.auto_service_check = QCheckBox("启动程序时自动运行OCR服务")
        self.auto_service_check.setChecked(
            self.config_manager.get_setting('auto_start_service', True)
        )
        self.auto_service_check.stateChanged.connect(self._on_auto_service_changed)
        startup_layout.addRow(self.auto_service_check)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        layout.addStretch()

        scroll.setWidget(widget)
        return scroll

    def _create_footer(self):
        """创建底部状态栏"""
        layout = QHBoxLayout()
        layout.setSpacing(16)

        # 服务状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("服务状态:"))

        self.status_indicator = QLabel("⏹ 已停止")
        self.status_indicator.setStyleSheet("""
            color: #e74c3c;
            font-weight: bold;
        """)
        status_layout.addWidget(self.status_indicator)

        layout.addLayout(status_layout)
        layout.addStretch()

        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(version_label)

        return layout

    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet(get_application_style())

    def _connect_signals(self):
        """连接信号"""
        self.variable_list.currentItemChanged.connect(self._on_variable_selected)
        self.screenshot_tool.region_captured.connect(self._on_screenshot_captured)
        self.screenshot_tool.cancelled.connect(self._on_screenshot_cancelled)

    def _load_variables(self):
        """加载变量列表"""
        self.variable_list.clear()

        variables = self.config_manager.get_all_variables()
        for var in variables:
            item = QListWidgetItem()

            # 根据类型设置图标和颜色
            if var['type'] == 'ocr':
                icon = "📝"
                tooltip = f"OCR文字识别: {var['name']}"
            else:
                icon = "🔘"
                tooltip = f"Button按钮识别: {var['name']}"

            item.setText(f"{icon} {var['name']}")
            item.setData(Qt.UserRole, var['name'])
            item.setToolTip(tooltip)

            self.variable_list.addItem(item)

        # 更新计数
        self.var_count_label.setText(f"({len(variables)})")

    def _on_variable_selected(self, current, previous):
        """变量被选中"""
        if not current:
            self.current_variable = None
            self._clear_detail_form()
            return

        var_name = current.data(Qt.UserRole)
        var = self.config_manager.get_variable(var_name)

        if var:
            self.current_variable = var
            self._update_detail_form(var)

    def _update_detail_form(self, var):
        """更新详情表单"""
        # 基本信息
        self.name_label.setText(var['name'])

        if var['type'] == 'ocr':
            self.type_label.setText("📝 OCR文字识别")
            self.type_label.setStyleSheet("color: #3498db;")
            self.button_settings_card.setVisible(False)
        else:
            self.type_label.setText("🔘 Button按钮识别")
            self.type_label.setStyleSheet("color: #e67e22;")
            self.button_settings_card.setVisible(True)

        # 坐标
        self.x_spin.setValue(var.get('left', 0))
        self.y_spin.setValue(var.get('top', 0))
        self.width_spin.setValue(var.get('width', 100))
        self.height_spin.setValue(var.get('height', 30))

        # Button特有字段
        self.on_image_edit.setText(var.get('on_image', ''))
        self.off_image_edit.setText(var.get('off_image', ''))
        self.threshold_spin.setValue(var.get('threshold', 0.8))

    def _clear_detail_form(self):
        """清空详情表单"""
        self.name_label.setText("未选择变量")
        self.type_label.setText("-")
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self.width_spin.setValue(100)
        self.height_spin.setValue(30)
        self.on_image_edit.clear()
        self.off_image_edit.clear()
        self.threshold_spin.setValue(0.8)
        self.button_settings_card.setVisible(False)

    def _on_value_changed(self):
        """值改变时自动保存"""
        if not self.current_variable:
            return

        name = self.current_variable['name']
        data = {
            'left': self.x_spin.value(),
            'top': self.y_spin.value(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value()
        }

        if self.current_variable['type'] == 'ocr':
            self.config_manager.update_region(name, **data)
        else:
            data['on_image'] = self.on_image_edit.text()
            data['off_image'] = self.off_image_edit.text()
            data['threshold'] = self.threshold_spin.value()
            self.config_manager.update_button(name, **data)

    def _on_add_variable(self):
        """添加变量"""
        dialog = AddVariableDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            name = data['name']
            var_type = data['type']

            if not name:
                QMessageBox.warning(self, "警告", "变量名称不能为空")
                return

            if var_type == 'ocr':
                success = self.config_manager.add_region(name)
            else:
                success = self.config_manager.add_button(name)

            if success:
                self._load_variables()
                # 选中新添加的变量
                for i in range(self.variable_list.count()):
                    item = self.variable_list.item(i)
                    if item.data(Qt.UserRole) == name:
                        self.variable_list.setCurrentItem(item)
                        break
                self.add_console_log(f"✅ 添加变量成功: {name}", 20)
            else:
                QMessageBox.warning(self, "警告", f"变量 {name} 已存在")

    def _on_delete_variable(self):
        """删除变量"""
        current = self.variable_list.currentItem()
        if not current:
            QMessageBox.information(self, "提示", "请先选择一个变量")
            return

        var_name = current.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除变量 '{var_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.config_manager.delete_variable(var_name)
            self._load_variables()
            self._clear_detail_form()
            self.add_console_log(f"🗑️ 删除变量: {var_name}", 20)

    def _on_screenshot(self):
        """截图获取位置"""
        if not self.current_variable:
            QMessageBox.information(self, "提示", "请先选择一个变量")
            return

        self.hide()
        QApplication.processEvents()
        self.screenshot_tool.start_screenshot()

    def _on_screenshot_captured(self, x, y, width, height):
        """截图完成"""
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self._on_value_changed()
        self.show()
        self.raise_()
        self.add_console_log(f"📷 截图区域: X={x}, Y={y}, W={width}, H={height}", 20)

    def _on_screenshot_cancelled(self):
        """截图取消"""
        self.show()
        self.raise_()

    def _select_image(self, image_type):
        """选择图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            if image_type == 'on_image':
                self.on_image_edit.setText(file_path)
            else:
                self.off_image_edit.setText(file_path)
            self._on_value_changed()

    def _on_service_toggle(self):
        """切换服务状态"""
        self.service_toggle_signal.emit(not self.is_service_running)

    def set_service_status(self, running: bool):
        """设置服务状态"""
        self.is_service_running = running
        if running:
            self.service_btn.setText("⏹ 停止服务")
            self.service_btn.setObjectName("danger_btn")
            self.status_indicator.setText("▶ 运行中")
            self.status_indicator.setStyleSheet("""
                color: #27ae60;
                font-weight: bold;
            """)
            self.add_console_log("✅ OCR服务已启动", 20)
        else:
            self.service_btn.setText("▶ 启动服务")
            self.service_btn.setObjectName("success_btn")
            self.status_indicator.setText("⏹ 已停止")
            self.status_indicator.setStyleSheet("""
                color: #e74c3c;
                font-weight: bold;
            """)
            self.add_console_log("⏹ OCR服务已停止", 20)

        # 重新应用按钮样式
        self.service_btn.style().unpolish(self.service_btn)
        self.service_btn.style().polish(self.service_btn)

    def add_console_log(self, message: str, level: int = 20):
        """添加控制台日志"""
        # 检查日志级别
        current_level = self.log_level_combo.currentData()
        if level < current_level:
            return

        # 根据级别设置颜色
        colors = {
            10: "#95a5a6",  # DEBUG - 灰色
            20: "#ecf0f1",  # INFO - 白色
            30: "#f39c12",  # WARNING - 橙色
            40: "#e74c3c"   # ERROR - 红色
        }
        color = colors.get(level, "#ecf0f1")

        # 获取当前时间
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 添加带颜色的日志
        html = f'<span style="color: {color}">[{timestamp}] {message}</span>'
        self.console_text.append(html)

        # 自动滚动
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear_console(self):
        """清空控制台"""
        self.console_text.clear()

    def _copy_console(self):
        """复制控制台内容"""
        text = self.console_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.add_console_log("📋 已复制到剪贴板", 20)

    def _on_ocr_url_changed(self):
        """OCR地址改变"""
        self.config_manager.set_ocr_url(self.ocr_url_edit.text())
        self.add_console_log(f"📝 OCR地址已更新: {self.ocr_url_edit.text()}", 20)

    def _on_show_log_changed(self, state):
        """显示日志选项改变"""
        self.config_manager.set_show_log(state == Qt.Checked)

    def _on_auto_startup_changed(self, state):
        """开机自启选项改变"""
        enabled = state == Qt.Checked
        success = self.startup_manager.toggle_startup(enabled)
        if success:
            self.config_manager.set_setting('auto_start_with_windows', enabled)
            if enabled:
                self.add_console_log("✅ 已设置开机自启", 20)
                # 使用控制台日志代替对话框
                self.add_console_log("💡 提示：程序将在Windows启动时自动运行", 20)
            else:
                self.add_console_log("⏹ 已取消开机自启", 20)
        else:
            self.add_console_log("❌ 设置开机自启失败", 40)
            # 恢复复选框状态
            self.auto_startup_check.setChecked(not enabled)

    def _on_auto_service_changed(self, state):
        """自动启动服务选项改变"""
        self.config_manager.set_setting('auto_start_service', state == Qt.Checked)

    def closeEvent(self, event):
        """关闭事件"""
        event.ignore()
        self.hide()
