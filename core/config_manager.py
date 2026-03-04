import yaml
import os
from typing import List, Dict, Any, Optional

from core.utils import get_config_path


class ConfigManager:
    """配置管理器，负责读写config.yaml"""
    
    def __init__(self, config_path: str = None):
        # 使用工具函数获取正确的配置文件路径
        self.config_path = config_path or get_config_path()
        print(f"Config path: {self.config_path}")  # 调试信息
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self._get_default_config()
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'regions': [],
            'buttons': [],
            'ocr_url': 'http://127.0.0.1:1224/api/ocr',
            'show_log': False,
            'settings': {
                'auto_start_service': True,
                'auto_start_with_windows': False
            }
        }
    
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_regions(self) -> List[Dict[str, Any]]:
        """获取OCR区域列表"""
        return self.config.get('regions', [])
    
    def get_buttons(self) -> List[Dict[str, Any]]:
        """获取按钮列表"""
        return self.config.get('buttons', [])
    
    def get_all_variables(self) -> List[Dict[str, Any]]:
        """获取所有变量（包含类型信息）"""
        variables = []
        
        for region in self.get_regions():
            var = region.copy()
            var['type'] = 'ocr'
            variables.append(var)
        
        for button in self.get_buttons():
            var = button.copy()
            var['type'] = 'button'
            variables.append(var)
        
        return variables
    
    def add_region(self, name: str, alias: str = '', left: int = 0, top: int = 0, 
                   width: int = 100, height: int = 30) -> bool:
        """添加 OCR 区域变量"""
        if self._variable_exists(name):
            print(f"变量 {name} 已存在")
            return False
        
        region = {
            'name': name,
            'alias': alias,
            'left': left,
            'top': top,
            'width': width,
            'height': height
        }
        
        if 'regions' not in self.config:
            self.config['regions'] = []
        
        self.config['regions'].append(region)
        return self.save_config()
    
    def add_button(self, name: str, alias: str = '', left: int = 0, top: int = 0,
                   width: int = 50, height: int = 50,
                   on_image: str = '', off_image: str = '',
                   threshold: float = 0.8) -> bool:
        """添加按钮变量"""
        if self._variable_exists(name):
            print(f"变量 {name} 已存在")
            return False
        
        button = {
            'name': name,
            'alias': alias,
            'left': left,
            'top': top,
            'width': width,
            'height': height,
            'on_image': on_image,
            'off_image': off_image,
            'threshold': threshold,
            'timeout': 3,
            'interval': 0.1,
            'use_opencv': True
        }
        
        if 'buttons' not in self.config:
            self.config['buttons'] = []
        
        self.config['buttons'].append(button)
        return self.save_config()
    
    def delete_variable(self, name: str) -> bool:
        """删除变量"""
        # 从regions中删除
        if 'regions' in self.config:
            self.config['regions'] = [
                r for r in self.config['regions'] if r['name'] != name
            ]
        
        # 从buttons中删除
        if 'buttons' in self.config:
            self.config['buttons'] = [
                b for b in self.config['buttons'] if b['name'] != name
            ]
        
        return self.save_config()
    
    def update_region(self, name: str, **kwargs) -> bool:
        """更新OCR区域变量"""
        for region in self.config.get('regions', []):
            if region['name'] == name:
                for key, value in kwargs.items():
                    if key in ['left', 'top', 'width', 'height']:
                        region[key] = int(value)
                    elif key == 'alias':
                        region[key] = str(value)
                return self.save_config()
        return False

    def update_button(self, name: str, **kwargs) -> bool:
        """更新按钮变量"""
        for button in self.config.get('buttons', []):
            if button['name'] == name:
                for key, value in kwargs.items():
                    if key in ['left', 'top', 'width', 'height']:
                        button[key] = int(value)
                    elif key in ['on_image', 'off_image']:
                        button[key] = str(value)
                    elif key == 'threshold':
                        button[key] = float(value)
                    elif key == 'alias':
                        button[key] = str(value)
                return self.save_config()
        return False
    
    def get_variable(self, name: str) -> Optional[Dict[str, Any]]:
        """获取变量信息"""
        # 查找regions
        for region in self.config.get('regions', []):
            if region['name'] == name:
                result = region.copy()
                result['type'] = 'ocr'
                return result
        
        # 查找buttons
        for button in self.config.get('buttons', []):
            if button['name'] == name:
                result = button.copy()
                result['type'] = 'button'
                return result
        
        return None
    
    def _variable_exists(self, name: str) -> bool:
        """检查变量是否已存在"""
        return self.get_variable(name) is not None
    
    def get_ocr_url(self) -> str:
        """获取OCR服务URL"""
        return self.config.get('ocr_url', 'http://127.0.0.1:1224/api/ocr')
    
    def set_ocr_url(self, url: str):
        """设置OCR服务URL"""
        self.config['ocr_url'] = url
        self.save_config()
    
    def get_show_log(self) -> bool:
        """获取是否显示日志"""
        return self.config.get('show_log', False)
    
    def set_show_log(self, show: bool):
        """设置是否显示日志"""
        self.config['show_log'] = show
        self.save_config()
    
    def get_setting(self, key: str, default=None):
        """获取设置项"""
        settings = self.config.get('settings', {})
        return settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """设置设置项"""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
        self.save_config()
