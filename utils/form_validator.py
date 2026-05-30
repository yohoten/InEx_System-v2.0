# -*- coding: utf-8 -*-
"""
表单验证工具模块
提供统一的表单验证功能,包括金额、日期、必填字段等验证
"""

from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from utils.logger import log_manager


class FormValidator:
    """表单验证器 - 提供常用验证方法"""
    
    # 常量定义
    MAX_AMOUNT = Decimal('999999.99')  # 最大金额
    MIN_AMOUNT = Decimal('0')  # 最小金额
    MAX_DATE_RANGE_YEARS = 5  # 最大日期范围(年)
    
    @staticmethod
    def validate_amount(amount_str, field_name="金额"):
        """验证金额格式
        
        Args:
            amount_str: 金额字符串
            field_name: 字段名称(用于错误提示)
        
        Returns:
            tuple: (是否有效, 错误消息或Decimal对象)
        """
        if not amount_str or not amount_str.strip():
            return False, f"{field_name}不能为空"
        
        try:
            amount = Decimal(amount_str.strip())
        except (InvalidOperation, ValueError):
            return False, f"{field_name}格式不正确,请输入数字"
        
        if amount < FormValidator.MIN_AMOUNT:
            return False, f"{field_name}不能为负数"
        
        if amount > FormValidator.MAX_AMOUNT:
            return False, f"{field_name}不能超过{FormValidator.MAX_AMOUNT}"
        
        # 检查小数位数(最多2位)
        if amount.as_tuple().exponent < -2:
            return False, f"{field_name}最多保留2位小数"
        
        return True, amount
    
    @staticmethod
    def validate_date_range(start_date, end_date, field_prefix="日期"):
        """验证日期范围
        
        Args:
            start_date: 起始日期(QDate或date对象)
            end_date: 结束日期(QDate或date对象)
            field_prefix: 字段前缀(用于错误提示)
        
        Returns:
            tuple: (是否有效, 错误消息)
        """
        if not start_date or not end_date:
            return False, f"{field_prefix}不能为空"
        
        # 转换为date对象(兼容QDate)
        if hasattr(start_date, 'toPyDate'):
            start_date = start_date.toPyDate()
        if hasattr(end_date, 'toPyDate'):
            end_date = end_date.toPyDate()
        
        if start_date > end_date:
            return False, f"起始{field_prefix}不能晚于结束{field_prefix}"
        
        # 检查日期范围
        delta = end_date - start_date
        max_days = FormValidator.MAX_DATE_RANGE_YEARS * 365
        if delta.days > max_days:
            return False, f"{field_prefix}范围不能超过{FormValidator.MAX_DATE_RANGE_YEARS}年"
        
        return True, ""
    
    @staticmethod
    def validate_required(value, field_name="字段"):
        """验证必填字段
        
        Args:
            value: 字段值
            field_name: 字段名称(用于错误提示)
        
        Returns:
            tuple: (是否有效, 错误消息)
        """
        if value is None:
            return False, f"{field_name}不能为空"
        
        if isinstance(value, str) and not value.strip():
            return False, f"{field_name}不能为空"
        
        return True, ""
    
    @staticmethod
    def validate_integer(value, field_name="数值", min_val=None, max_val=None):
        """验证整数
        
        Args:
            value: 整数字符串或整数
            field_name: 字段名称
            min_val: 最小值(可选)
            max_val: 最大值(可选)
        
        Returns:
            tuple: (是否有效, 错误消息或int对象)
        """
        if not value or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name}不能为空"
        
        try:
            int_val = int(str(value).strip())
        except ValueError:
            return False, f"{field_name}必须是整数"
        
        if min_val is not None and int_val < min_val:
            return False, f"{field_name}不能小于{min_val}"
        
        if max_val is not None and int_val > max_val:
            return False, f"{field_name}不能大于{max_val}"
        
        return True, int_val
    
    @staticmethod
    def validate_email(email, field_name="邮箱"):
        """验证邮箱格式
        
        Args:
            email: 邮箱地址
            field_name: 字段名称
        
        Returns:
            tuple: (是否有效, 错误消息)
        """
        if not email or not email.strip():
            return False, f"{field_name}不能为空"
        
        # 简单邮箱格式验证
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.strip()):
            return False, f"{field_name}格式不正确"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone, field_name="手机号"):
        """验证手机号格式(中国大陆)
        
        Args:
            phone: 手机号
            field_name: 字段名称
        
        Returns:
            tuple: (是否有效, 错误消息)
        """
        if not phone or not phone.strip():
            return False, f"{field_name}不能为空"
        
        # 中国大陆手机号验证
        import re
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, phone.strip()):
            return False, f"{field_name}格式不正确"
        
        return True, ""
    
    @staticmethod
    def get_validation_style(is_valid):
        """获取验证样式(用于输入框边框颜色)
        
        Args:
            is_valid: 是否有效
        
        Returns:
            str: QSS样式字符串
        """
        if is_valid:
            return "border: 1px solid #10b981;"  # 绿色
        else:
            return "border: 1px solid #ef4444;"  # 红色
