# -*- coding: utf-8 -*-
"""
日志管理工具模块
支持日志记录、文件管理、级别过滤
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LogManager:
    """日志管理器"""
    
    def __init__(self, name: str = "InEx_system", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        self.logger = None
        self.log_file = None
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def setup_logger(self, level: str = 'INFO', log_to_file: bool = True):
        """设置日志记录器"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # 清除已有的 handlers
        self.logger.handlers.clear()
        
        # 创建 formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件 handler
        if log_to_file:
            timestamp = datetime.now().strftime("%Y%m%d")
            self.log_file = os.path.join(self.log_dir, f"{self.name}_{timestamp}.log")
            
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        print(f"[日志] 日志系统初始化完成，级别：{level}")
        return self.logger
    
    def debug(self, message: str):
        """记录 DEBUG 级别日志"""
        if self.logger:
            self.logger.debug(message)
    
    def info(self, message: str):
        """记录 INFO 级别日志"""
        if self.logger:
            self.logger.info(message)
    
    def warning(self, message: str):
        """记录 WARNING 级别日志"""
        if self.logger:
            self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """记录 ERROR 级别日志
        
        Args:
            message: 错误消息
            exc_info: 是否包含异常堆栈信息(默认False)
        """
        if self.logger:
            self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str):
        """记录 CRITICAL 级别日志"""
        if self.logger:
            self.logger.critical(message)
    
    def get_log_file_path(self) -> Optional[str]:
        """获取当前日志文件路径"""
        return self.log_file
    
    def clear_old_logs(self, days: int = 7):
        """清理旧日志文件"""
        import time
        
        if not os.path.exists(self.log_dir):
            return
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                filepath = os.path.join(self.log_dir, filename)
                file_mtime = os.path.getmtime(filepath)
                
                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    print(f"[日志] 清理旧日志：{filename}")


# 全局日志管理器实例
log_manager = LogManager()
