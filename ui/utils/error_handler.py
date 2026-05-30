# -*- coding: utf-8 -*-
"""错误处理工具 - 统一的错误提示管理"""

from PyQt5.QtWidgets import QMessageBox
from datetime import datetime
import functools


class ErrorLevel:
    """错误级别枚举"""
    INFO = "info"           # 提示信息
    WARNING = "warn"        # 警告
    ERROR = "error"         # 错误
    CRITICAL = "critical"   # 严重错误


def show_error(widget, message, level=ErrorLevel.ERROR, action_suggestions=None, toast=None):
    """
    统一错误提示函数
    
    Args:
        widget: 父窗口部件
        message: 错误消息文本
        level: 错误级别 (ErrorLevel)
        action_suggestions: 建议操作列表
        toast: Toast组件实例（可选）
    """
    icons = {
        ErrorLevel.INFO: "ℹ️",
        ErrorLevel.WARNING: "⚠️",
        ErrorLevel.ERROR: "❌",
        ErrorLevel.CRITICAL: "🚨"
    }
    
    colors = {
        ErrorLevel.INFO: "#3b82f6",
        ErrorLevel.WARNING: "#f59e0b",
        ErrorLevel.ERROR: "#ef4444",
        ErrorLevel.CRITICAL: "#dc2626"
    }
    
    # 构建消息
    full_message = f"{icons[level]} {message}"
    
    if action_suggestions:
        full_message += "\n\n💡 建议操作:\n"
        for i, suggestion in enumerate(action_suggestions, 1):
            full_message += f"{i}. {suggestion}\n"
    
    # 根据级别选择对话框类型
    if level in [ErrorLevel.INFO, ErrorLevel.WARNING]:
        if toast:
            toast.show_message(full_message, icons[level], 5000)
        else:
            QMessageBox.information(widget, "提示", full_message)
    elif level == ErrorLevel.ERROR:
        QMessageBox.critical(widget, "错误", full_message)
    else:  # CRITICAL
        QMessageBox.critical(widget, "严重错误", full_message)


def show_technical_error(widget, error, toast=None):
    """
    显示技术性错误（供高级用户）
    
    Args:
        widget: 父窗口部件
        error: 异常对象
        toast: Toast组件实例（可选）
    """
    reply = QMessageBox.question(
        widget,
        "发生错误",
        f"❌ 操作失败\n\n"
        f"错误信息: {str(error)}\n\n"
        f"是否查看详细技术信息？",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        QMessageBox.critical(
            widget,
            "技术详情",
            f"错误类型: {type(error).__name__}\n"
            f"错误信息: {str(error)}\n"
            f"时间: {datetime.now()}\n\n"
            f"建议:\n"
            f"1. 检查数据库连接\n"
            f"2. 查看日志文件: data/app.log\n"
            f"3. 联系技术支持"
        )
    else:
        # 即使用户选择不查看详情，也显示简要提示
        if toast:
            toast.error("操作失败，请查看日志或联系技术支持")


def safe_execute(func):
    """
    安全执行装饰器 - 自动捕获异常并显示友好错误提示
    
    使用方法:
    @safe_execute(error_level=ErrorLevel.ERROR, action_suggestions=["重试", "检查网络"])
    def my_function(self):
        # 可能抛出异常的代码
        pass
    
    Args:
        func: 被装饰的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 从kwargs或默认值获取配置
        error_level = kwargs.pop('error_level', ErrorLevel.ERROR)
        action_suggestions = kwargs.pop('action_suggestions', None)
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 获取self参数(通常是QWidget)
            widget = args[0] if args else None
            
            # 如果有toast属性,使用toast显示
            toast = getattr(widget, 'toast', None)
            
            # 显示错误
            show_error(
                widget,
                f"{func.__name__} 执行失败: {str(e)}",
                level=error_level,
                action_suggestions=action_suggestions,
                toast=toast
            )
            
            # 记录到日志
            print(f"[ERROR] {func.__name__}: {type(e).__name__}: {str(e)}")
            
            return None
    
    return wrapper


def handle_database_error(func):
    """
    数据库操作错误处理装饰器
    
    专门用于数据库相关操作,提供针对性的错误建议
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            widget = args[0] if args else None
            toast = getattr(widget, 'toast', None)
            
            # 根据错误类型提供不同建议
            error_msg = str(e).lower()
            suggestions = []
            
            if "connection" in error_msg or "connect" in error_msg:
                suggestions = [
                    "检查数据库服务是否启动",
                    "验证网络连接",
                    "确认数据库配置正确"
                ]
            elif "permission" in error_msg or "access denied" in error_msg:
                suggestions = [
                    "检查数据库用户名和密码",
                    "确认用户权限设置",
                    "联系数据库管理员"
                ]
            elif "table" in error_msg or "column" in error_msg:
                suggestions = [
                    "检查数据库表结构",
                    "运行数据库初始化脚本",
                    "查看data/temp_init_data.sql"
                ]
            else:
                suggestions = [
                    "重试操作",
                    "查看日志文件: data/app.log",
                    "联系技术支持"
                ]
            
            show_error(
                widget,
                f"数据库操作失败: {str(e)}",
                level=ErrorLevel.ERROR,
                action_suggestions=suggestions,
                toast=toast
            )
            
            print(f"[DB_ERROR] {func.__name__}: {type(e).__name__}: {str(e)}")
            return None
    
    return wrapper
