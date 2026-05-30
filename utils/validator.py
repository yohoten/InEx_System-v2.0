# -*- coding: utf-8 -*-
"""
数据验证器模块
提供统一的数据验证功能，防止脏数据进入数据库
"""

from datetime import datetime
from typing import Tuple


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_income_record(record: dict) -> Tuple[bool, str]:
        """验证收入记录
        
        Args:
            record: 收入记录字典，包含 rq, sr_code, je, zf_code 等字段
            
        Returns:
            (是否有效, 错误信息)
        """
        # 验证日期
        if not record.get('rq'):
            return False, "日期不能为空"
        
        if not DataValidator.validate_date_format(record['rq']):
            return False, f"日期格式错误：{record['rq']}（应为 YYYY-MM-DD）"
        
        # 验证金额
        je = record.get('je')
        if je is None or je == '':
            return False, "金额不能为空"
        
        try:
            je = float(je)
        except (ValueError, TypeError):
            return False, f"金额格式错误：{je}"
        
        if je <= 0:
            return False, "金额必须大于 0"
        
        if je > 999999.99:
            return False, "金额超出范围（最大 999999.99）"
        
        # 验证收入类型
        if not record.get('sr_code'):
            return False, "请选择收入类型"
        
        # 验证支付方式
        if not record.get('zf_code'):
            return False, "请选择支付方式"
        
        return True, ""
    
    @staticmethod
    def validate_expense_record(record: dict) -> Tuple[bool, str]:
        """验证支出记录
        
        Args:
            record: 支出记录字典，包含 rq, zc_code, je, zf_code 等字段
            
        Returns:
            (是否有效, 错误信息)
        """
        # 验证日期
        if not record.get('rq'):
            return False, "日期不能为空"
        
        if not DataValidator.validate_date_format(record['rq']):
            return False, f"日期格式错误：{record['rq']}（应为 YYYY-MM-DD）"
        
        # 验证金额
        je = record.get('je')
        if je is None or je == '':
            return False, "金额不能为空"
        
        try:
            je = float(je)
        except (ValueError, TypeError):
            return False, f"金额格式错误：{je}"
        
        if je <= 0:
            return False, "金额必须大于 0"
        
        if je > 999999.99:
            return False, "金额超出范围（最大 999999.99）"
        
        # 验证支出类型
        if not record.get('zc_code'):
            return False, "请选择支出类型"
        
        # 验证支付方式
        if not record.get('zf_code'):
            return False, "请选择支付方式"
        
        return True, ""
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """验证日期格式 YYYY-MM-DD
        
        Args:
            date_str: 日期字符串
            
        Returns:
            是否为有效日期格式
        """
        if not date_str:
            return False
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_amount(amount) -> Tuple[bool, str]:
        """验证金额
        
        Args:
            amount: 金额值
            
        Returns:
            (是否有效, 错误信息)
        """
        if amount is None or amount == '':
            return False, "金额不能为空"
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return False, f"金额格式错误：{amount}"
        
        if amount <= 0:
            return False, "金额必须大于 0"
        
        if amount > 999999.99:
            return False, "金额超出范围（最大 999999.99）"
        
        return True, ""
    
    @staticmethod
    def validate_code(code: str, code_type: str = "类型代码") -> Tuple[bool, str]:
        """验证代码字段
        
        Args:
            code: 代码值
            code_type: 代码类型描述（用于错误提示）
            
        Returns:
            (是否有效, 错误信息)
        """
        if not code or not code.strip():
            return False, f"{code_type}不能为空"
        
        if len(code) > 10:
            return False, f"{code_type}长度不能超过 10 个字符"
        
        return True, ""
    
    @staticmethod
    def validate_string(text: str, field_name: str = "字段", 
                       max_length: int = 200, required: bool = False) -> Tuple[bool, str]:
        """验证字符串字段
        
        Args:
            text: 文本内容
            field_name: 字段名称（用于错误提示）
            max_length: 最大长度
            required: 是否必填
            
        Returns:
            (是否有效, 错误信息)
        """
        if required and (not text or not text.strip()):
            return False, f"{field_name}不能为空"
        
        if text and len(text) > max_length:
            return False, f"{field_name}长度不能超过 {max_length} 个字符"
        
        return True, ""
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """清理字符串（去除首尾空格、特殊字符）
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 去除首尾空格
        text = text.strip()
        
        # 替换危险字符（简单的 SQL 注入防护）
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
        for char in dangerous_chars:
            text = text.replace(char, "")
        
        return text
    
    @staticmethod
    def validate_account_number(account: str) -> Tuple[bool, str]:
        """验证账套号
        
        Args:
            account: 账套号
            
        Returns:
            (是否有效, 错误信息)
        """
        if not account or not account.strip():
            return False, "账套号不能为空"
        
        if len(account) != 10:
            return False, "账套号必须为 10 位数字"
        
        if not account.isdigit():
            return False, "账套号只能包含数字"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            (是否有效, 错误信息)
        """
        if not password:
            return False, "密码不能为空"
        
        if len(password) < 6:
            return False, "密码长度至少 6 位"
        
        if len(password) > 50:
            return False, "密码长度不能超过 50 位"
        
        return True, ""


# 全局验证器实例
validator = DataValidator()
