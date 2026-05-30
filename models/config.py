# -*- coding: utf-8 -*-
"""
系统配置模块
管理数据库连接、系统设置等
"""

import os
import json
import threading
from datetime import datetime
from utils.logger import log_manager  # 新增:导入日志管理器


class ConfigManager:
    """配置管理器（线程安全单例）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.__initialized = False
        return cls._instance
    
    def __init__(self):
        if self.__initialized:
            return
        
        self.config_file = 'config.json'
        self.config = {
            'database': {
                'type': 'sqlite',
                'path': 'data/inex.db',
                'auto_backup': True,
                'backup_interval': 7  # 天
            },
            'system': {
                'company_name': '收支管理系统',
                'version': '2.0',
                'author': '滕宇豪',
                'student_id': '270457',
                'class': '大数据与财务管理 03 班'
            },
            'ui': {
                'theme': 'default',
                'font_size': 10,
                'window_width': 1600,
                'window_height': 900
            },
            'log': {
                'level': 'INFO',
                'path': './logs/'
            },
            'api': {},  # API配置（AI相关）
            'ai': {}  # AI配置（兼容旧版本）
        }
        self.load_config()
        self.__initialized = True
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 合并配置
                    for key in saved_config:
                        if isinstance(saved_config[key], dict):
                            # 如果key存在且是字典类型，则合并；否则直接赋值
                            if key in self.config and isinstance(self.config[key], dict):
                                self.config[key].update(saved_config[key])
                            else:
                                self.config[key] = saved_config[key]
                        else:
                            self.config[key] = saved_config[key]
                print(f"[配置] 已加载配置文件：{self.config_file}")
            except Exception as e:
                log_manager.error(f"配置加载失败：{str(e)}，使用默认配置", exc_info=True)
        else:
            self.save_config()
            log_manager.info(f"创建默认配置文件：{self.config_file}")
    
    def save_config(self):
        """保存配置文件（带备份和回滚机制）"""
        backup_file = None
        
        try:
            # 如果配置文件存在，先创建备份
            if os.path.exists(self.config_file):
                backup_file = self.config_file + '.bak'
                import shutil
                shutil.copy2(self.config_file, backup_file)
            
            # 写入新配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())  # 确保数据写入磁盘
            
            log_manager.info(f"配置已保存：{self.config_file}")
            
            # 删除备份文件（成功保存后）
            if backup_file and os.path.exists(backup_file):
                os.remove(backup_file)
                
        except Exception as e:
            log_manager.error(f"配置保存失败：{str(e)}")
            
            # 回滚：从备份恢复
            if backup_file and os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.copy2(backup_file, self.config_file)
                    log_manager.warning("已从备份恢复配置文件")
                except Exception as rollback_error:
                    log_manager.error(f"配置回滚失败：{str(rollback_error)}")
            
            raise
    
    def get_database_config(self):
        """获取数据库配置"""
        return self.config['database']
    
    def set_database_config(self, db_type, **kwargs):
        """设置数据库配置"""
        self.config['database']['type'] = db_type
        for key, value in kwargs.items():
            self.config['database'][key] = value
        self.save_config()
    
    def get_system_setting(self, key, default=None):
        """获取系统设置"""
        return self.config['system'].get(key, default)
    
    def set_system_setting(self, key, value):
        """设置系统参数"""
        self.config['system'][key] = value
        self.save_config()
    
    def get_ui_setting(self, key, default=None):
        """获取 UI 设置"""
        return self.config['ui'].get(key, default)
    
    def set_ui_setting(self, key, value):
        """设置 UI 参数"""
        self.config['ui'][key] = value
        self.save_config()
    
    def get_log_setting(self, key, default=None):
        """获取日志设置"""
        return self.config['log'].get(key, default)
    
    def set_log_setting(self, key, value):
        """设置日志参数"""
        self.config['log'][key] = value
        self.save_config()
    
    def get(self, key, default=None):
        """
        通用配置读取方法
        
        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'ui.theme'）
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            # 支持嵌套键，如 'database.type'
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                else:
                    return default
            
            return value if value is not None else default
        except Exception:
            return default
    
    def set(self, key, value):
        """
        通用配置保存方法
        
        Args:
            key: 配置键（支持点号分隔的嵌套键，如 'ui.theme'）
            value: 配置值
        """
        try:
            # 支持嵌套键，如 'database.type'
            keys = key.split('.')
            
            # 导航到父级
            config_section = self.config
            for k in keys[:-1]:
                if k not in config_section:
                    config_section[k] = {}
                config_section = config_section[k]
            
            # 设置最终值
            config_section[keys[-1]] = value
            self.save_config()
        except Exception as e:
            log_manager.error(f"配置保存失败 [{key}={value}]: {str(e)}")
    
    def get_api_setting(self, key, default=None):
        """获取 API 设置（加密存储）"""
        if 'api' not in self.config:
            self.config['api'] = {}
        return self.config['api'].get(key, default)
    
    def set_api_setting(self, key, value):
        """设置 API 参数（加密存储）"""
        if 'api' not in self.config:
            self.config['api'] = {}
        self.config['api'][key] = value
        self.save_config()
    
    def get_deepseek_config(self):
        """获取 DeepSeek 完整配置"""
        return {
            'api_key': self.get_api_setting('key', ''),
            'model': self.get_api_setting('model', 'deepseek-chat'),
            'temperature': self.get_api_setting('temperature', 0.7),
            'max_tokens': self.get_api_setting('max_tokens', 2000),
            'base_url': self.get_api_setting('base_url', 'https://api.deepseek.com/v1')
        }
    
    def save_deepseek_config(self, api_key, model='deepseek-chat', temperature=0.7, max_tokens=1000, base_url='https://api.deepseek.com/v1'):
        """保存 DeepSeek 配置（加密存储）"""
        # 使用 AIConfigManager 进行加密存储
        from utils.ai_assistant import AIConfigManager
        ai_config = AIConfigManager()
        ai_config.save_config(api_key, model, temperature, max_tokens)
        
        # 同时在 config.json 中保存非敏感配置
        self.set_api_setting('model', model)
        self.set_api_setting('temperature', temperature)
        self.set_api_setting('max_tokens', max_tokens)
        self.set_api_setting('base_url', base_url)


# 全局配置实例
config = ConfigManager()
