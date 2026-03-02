"""
现代化UI样式定义
"""

# 主窗口样式
MAIN_WINDOW_STYLE = """
QMainWindow {
    background-color: #f5f6fa;
}
"""

# 按钮样式
BUTTON_STYLE = """
QPushButton {
    background-color: #4834d4;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #686de0;
}

QPushButton:pressed {
    background-color: #30336b;
}

QPushButton:disabled {
    background-color: #bdc3c7;
    color: #7f8c8d;
}

QPushButton#danger_btn {
    background-color: #e74c3c;
}

QPushButton#danger_btn:hover {
    background-color: #c0392b;
}

QPushButton#success_btn {
    background-color: #27ae60;
}

QPushButton#success_btn:hover {
    background-color: #229954;
}

QPushButton#secondary_btn {
    background-color: #95a5a6;
}

QPushButton#secondary_btn:hover {
    background-color: #7f8c8d;
}
"""

# 输入框样式
INPUT_STYLE = """
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #4834d4;
}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #ecf0f1;
    color: #7f8c8d;
}
"""

# 列表样式
LIST_STYLE = """
QListWidget {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 8px;
    outline: none;
}

QListWidget::item {
    padding: 12px 16px;
    margin: 4px 0px;
    border-radius: 6px;
    font-size: 13px;
    color: #2c3e50;
}

QListWidget::item:selected {
    background-color: #4834d4;
    color: white;
}

QListWidget::item:hover {
    background-color: #f0f0f0;
}

QListWidget::item:selected:hover {
    background-color: #686de0;
}
"""

# 分组框样式
GROUP_BOX_STYLE = """
QGroupBox {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    margin-top: 16px;
    padding-top: 16px;
    font-size: 14px;
    font-weight: bold;
    color: #2c3e50;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #4834d4;
}
"""

# 标签样式
LABEL_STYLE = """
QLabel {
    font-size: 13px;
    color: #2c3e50;
}

QLabel#title_label {
    font-size: 18px;
    font-weight: bold;
    color: #2c3e50;
    padding: 8px 0;
}

QLabel#subtitle_label {
    font-size: 14px;
    color: #7f8c8d;
    padding: 4px 0;
}

QLabel#status_running {
    color: #27ae60;
    font-weight: bold;
}

QLabel#status_stopped {
    color: #e74c3c;
    font-weight: bold;
}
"""

# 选项卡样式
TAB_STYLE = """
QTabWidget::pane {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    background-color: white;
    top: -2px;
}

QTabBar::tab {
    background-color: #ecf0f1;
    border: 2px solid #e0e0e0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 12px 24px;
    margin-right: 4px;
    font-size: 13px;
    font-weight: 500;
    color: #7f8c8d;
}

QTabBar::tab:selected {
    background-color: white;
    color: #4834d4;
    border-bottom: 2px solid white;
}

QTabBar::tab:hover:!selected {
    background-color: #d5dbdb;
    color: #2c3e50;
}
"""

# 日志文本框样式
LOG_TEXT_STYLE = """
QTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 2px solid #3c3c3c;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.5;
}

QTextEdit:focus {
    border-color: #4834d4;
}
"""

# 下拉框样式
COMBO_STYLE = """
QComboBox {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #bdc3c7;
}

QComboBox:focus {
    border-color: #4834d4;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #7f8c8d;
    width: 0;
    height: 0;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    selection-background-color: #4834d4;
    selection-color: white;
    padding: 4px;
}
"""

# 复选框样式
CHECKBOX_STYLE = """
QCheckBox {
    font-size: 13px;
    color: #2c3e50;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #bdc3c7;
    border-radius: 4px;
    background-color: white;
}

QCheckBox::indicator:checked {
    background-color: #4834d4;
    border-color: #4834d4;
}

QCheckBox::indicator:hover {
    border-color: #4834d4;
}
"""

# 滚动条样式
SCROLLBAR_STYLE = """
QScrollBar:vertical {
    background-color: #f5f6fa;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #f5f6fa;
    height: 12px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal {
    background-color: #bdc3c7;
    border-radius: 6px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #95a5a6;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

# 分割器样式
SPLITTER_STYLE = """
QSplitter::handle {
    background-color: #e0e0e0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #4834d4;
}
"""

# 对话框样式
DIALOG_STYLE = """
QDialog {
    background-color: #f5f6fa;
}
"""

# 应用所有样式
def get_application_style():
    """获取完整的应用程序样式"""
    return (
        MAIN_WINDOW_STYLE +
        BUTTON_STYLE +
        INPUT_STYLE +
        LIST_STYLE +
        GROUP_BOX_STYLE +
        LABEL_STYLE +
        TAB_STYLE +
        LOG_TEXT_STYLE +
        COMBO_STYLE +
        CHECKBOX_STYLE +
        SCROLLBAR_STYLE +
        SPLITTER_STYLE +
        DIALOG_STYLE
    )
