# -*- coding: utf-8 -*-
"""
预算管理模块
提供预算设置、查询和预警功能
"""

from typing import List, Dict, Optional
import sqlite3
from datetime import datetime
import logging
from utils.logger import log_manager  # 新增:导入统一日志管理器用于error调用

logger = logging.getLogger('BudgetManager')


class BudgetAlert:
    """预算预警管理器
    
    功能:
    - 检查预算超支情况
    - 发送预警通知
    - 支持多种预警级别（警告/危险）
    """
    
    def __init__(self, budget_manager):
        """初始化预算预警
        
        Args:
            budget_manager: BudgetManager 实例
        """
        self.budget_manager = budget_manager
        self.alert_callbacks = []  # 预警回调函数列表
    
    def add_alert_callback(self, callback):
        """添加预警回调函数
        
        Args:
            callback: 回调函数，接收预警信息字典作为参数
        """
        self.alert_callbacks.append(callback)
        logger.info("[预算预警] 添加预警回调函数")
    
    def check_budget_exceeded(self, category: str, amount: float, month: str = None, zth: str = None) -> List[Dict]:
        """检查预算是否即将超支或已超支
        
        Args:
            category: 支出类别
            amount: 当前支出金额
            month: 月份，格式 YYYY-MM，默认为当前月
            zth: 账套号，默认使用当前账套
            
        Returns:
            List[Dict]: 预警列表
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        warnings = []
        
        try:
            # 获取月度预算
            budget = self.budget_manager.get_monthly_budget(month, zth)
            
            # 如果未设置预算，不产生预警
            if budget <= 0:
                return warnings
            
            # 获取已支出金额
            spent = self.budget_manager.get_monthly_expense(month, zth)
            
            # 计算加上当前金额后的总支出
            total_spent = spent + amount
            usage_rate = (total_spent / budget * 100) if budget > 0 else 0
            
            # 80%阈值预警
            if total_spent > budget * 0.8 and total_spent <= budget:
                warning = {
                    'type': 'warning',
                    'level': 1,
                    'category': category,
                    'message': f"⚠️ {category} 预算即将超支！\n"
                              f"已使用: ¥{total_spent:.2f} / ¥{budget:.2f} ({usage_rate:.1f}%)\n"
                              f"剩余额度: ¥{budget - total_spent:.2f}",
                    'budget': budget,
                    'spent': total_spent,
                    'remaining': budget - total_spent,
                    'usage_rate': usage_rate,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                warnings.append(warning)
                self._trigger_alerts(warning)
            
            # 超预算警告
            elif total_spent > budget:
                overrun = total_spent - budget
                warning = {
                    'type': 'danger',
                    'level': 2,
                    'category': category,
                    'message': f"🚨 {category} 预算已超支！\n"
                              f"已使用: ¥{total_spent:.2f} / ¥{budget:.2f} ({usage_rate:.1f}%)\n"
                              f"超出金额: ¥{overrun:.2f}",
                    'budget': budget,
                    'spent': total_spent,
                    'overrun': overrun,
                    'usage_rate': usage_rate,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                warnings.append(warning)
                self._trigger_alerts(warning)
            
            return warnings
            
        except Exception as e:
            logger.error(f"[预算预警] 检查预算超支失败: {e}", exc_info=True)
            return []
    
    def check_category_budget(self, category: str, amount: float, month: str = None, zth: str = None) -> List[Dict]:
        """检查特定类别的预算使用情况
        
        Args:
            category: 支出类别
            amount: 支出金额
            month: 月份，格式 YYYY-MM
            zth: 账套号
            
        Returns:
            List[Dict]: 预警列表
        """
        return self.check_budget_exceeded(category, amount, month, zth)
    
    def send_alert(self, message: str, level: int = 1):
        """发送预警通知
        
        Args:
            message: 预警消息
            level: 预警级别 (1=警告, 2=危险)
        """
        alert_info = {
            'type': 'warning' if level == 1 else 'danger',
            'level': level,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.warning(f"[预算预警] {message}")
        self._trigger_alerts(alert_info)
    
    def _trigger_alerts(self, alert_info: Dict):
        """触发所有预警回调
        
        Args:
            alert_info: 预警信息字典
        """
        for callback in self.alert_callbacks:
            try:
                callback(alert_info)
            except Exception as e:
                logger.error(f"[预算预警] 执行回调失败: {e}", exc_info=True)
    
    def get_budget_status_summary(self, month: str = None, zth: str = None) -> Dict:
        """获取预算状态摘要
        
        Args:
            month: 月份，格式 YYYY-MM
            zth: 账套号
            
        Returns:
            Dict: 预算状态摘要
        """
        if month is None:
            month = datetime.now().strftime('%Y-%m')
        
        try:
            budget = self.budget_manager.get_monthly_budget(month, zth)
            actual = self.budget_manager.get_monthly_expense(month, zth)
            remaining = budget - actual
            usage_rate = (actual / budget * 100) if budget > 0 else 0
            
            # 确定状态
            if budget <= 0:
                status = 'not_set'
                status_text = '未设置预算'
            elif actual > budget:
                status = 'overrun'
                status_text = '已超支'
            elif actual > budget * 0.8:
                status = 'warning'
                status_text = '即将超支'
            elif actual > budget * 0.5:
                status = 'normal'
                status_text = '正常'
            else:
                status = 'healthy'
                status_text = '良好'
            
            return {
                'month': month,
                'budget': budget,
                'actual': actual,
                'remaining': remaining,
                'usage_rate': usage_rate,
                'status': status,
                'status_text': status_text
            }
        except Exception as e:
            logger.error(f"[预算预警] 获取预算状态摘要失败: {e}", exc_info=True)
            return {}


class BudgetManager:
    """预算管理器
    
    功能:
    - 设置月度预算
    - 查询预算信息
    - 检查预算预警（80%预警，100%超支）
    - 生成预算报告
    """
    
    def __init__(self, db_manager):
        """初始化预算管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self._ensure_budget_table()
    
    def _ensure_budget_table(self):
        """确保预算表存在"""
        if not self.db_manager.is_connected():
            logger.warning("[预算管理] 数据库未连接")
            return
        
        try:
            backend = self.db_manager.get_backend()
            backend.execute('''
                CREATE TABLE IF NOT EXISTS sz_budget (
                    id INTEGER PRIMARY KEY,
                    zth CHAR(20) NOT NULL,
                    month CHAR(7) NOT NULL,
                    budget_amount REAL NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(zth, month)
                )
            ''')
            
            # 创建预算变更历史表
            backend.execute('''
                CREATE TABLE IF NOT EXISTS sz_budget_history (
                    id INTEGER PRIMARY KEY,
                    zth CHAR(20) NOT NULL,
                    month CHAR(7) NOT NULL,
                    old_amount REAL,
                    new_amount REAL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    changed_by CHAR(20)
                )
            ''')
            
            logger.info("[预算管理] 预算表和历史表初始化成功")
        except Exception as e:
            logger.error(f"[预算管理] 创建预算表失败: {e}", exc_info=True)
    
    def set_monthly_budget(self, month: str, amount: float, zth: str = None) -> bool:
        """设置月度预算
        
        Args:
            month: 月份，格式 YYYY-MM (如: 2026-04)
            amount: 预算金额
            zth: 账套号，默认使用当前账套
            
        Returns:
            bool: 是否设置成功
        """
        if not self.db_manager.is_connected():
            logger.warning("[预算管理] 数据库未连接")
            return False
        
        if zth is None:
            zth = self.db_manager.current_account
        
        # 验证月份格式
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            logger.error(f"[预算管理] 月份格式错误: {month}，应为 YYYY-MM", exc_info=True)
            return False
        
        if amount < 0:
            logger.error(f"[预算管理] 预算金额不能为负数: {amount}", exc_info=True)
            return False
        
        try:
            backend = self.db_manager.get_backend()
            
            # 获取旧预算值（用于历史记录）
            backend.execute(
                "SELECT budget_amount FROM sz_budget WHERE zth=? AND month=?",
                (zth, month)
            )
            result = backend.fetchone()
            old_amount = result[0] if result else None
            
            # 先尝试更新，如果不存在则插入
            backend.execute(
                "UPDATE sz_budget SET budget_amount=?, updated_at=CURRENT_TIMESTAMP WHERE zth=? AND month=?",
                (amount, zth, month)
            )
            
            # 检查是否更新了记录
            backend.execute("SELECT changes()")
            changes = backend.fetchone()[0]
            
            # 如果没有更新（记录不存在），则插入
            if changes == 0:
                backend.execute(
                    "INSERT INTO sz_budget (zth, month, budget_amount, created_at, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (zth, month, amount)
                )
            
            # 记录预算变更历史
            backend.execute(
                "INSERT INTO sz_budget_history (zth, month, old_amount, new_amount, changed_by) VALUES (?, ?, ?, ?, ?)",
                (zth, month, old_amount, amount, 'system')
            )
            
            logger.info(f"[预算管理] 设置预算成功: {month} = {amount:.2f}")
            return True
        except Exception as e:
            logger.error(f"[预算管理] 设置预算失败: {e}", exc_info=True)
            return False
    
    def get_monthly_budget(self, month: str, zth: str = None) -> float:
        """获取月度预算
        
        Args:
            month: 月份，格式 YYYY-MM
            zth: 账套号，默认使用当前账套
            
        Returns:
            float: 预算金额，未设置返回0
        """
        if not self.db_manager.is_connected():
            return 0.0
        
        if zth is None:
            zth = self.db_manager.current_account
        
        try:
            backend = self.db_manager.get_backend()
            backend.execute(
                "SELECT budget_amount FROM sz_budget WHERE zth=? AND month=?",
                (zth, month)
            )
            result = backend.fetchone()
            return result[0] if result else 0.0
        except Exception as e:
            logger.error(f"[预算管理] 查询预算失败: {e}", exc_info=True)
            return 0.0
    
    def get_monthly_expense(self, month: str, zth: str = None) -> float:
        """获取月度实际支出
        
        Args:
            month: 月份，格式 YYYY-MM
            zth: 账套号，默认使用当前账套
            
        Returns:
            float: 实际支出金额
        """
        if not self.db_manager.is_connected():
            return 0.0
        
        if zth is None:
            zth = self.db_manager.current_account
        
        try:
            backend = self.db_manager.get_backend()
            # 计算指定月份的总支出
            backend.execute('''
                SELECT COALESCE(SUM(je), 0) 
                FROM sz_sheet_zc 
                WHERE zth=? AND strftime('%Y-%m', rq)=?
            ''', (zth, month))
            
            result = backend.fetchone()
            expense = result[0] if result else 0.0
            logger.debug(f"[预算管理] {month} 实际支出: {expense:.2f}")
            return expense
        except Exception as e:
            logger.error(f"[预算管理] 查询支出失败: {e}", exc_info=True)
            return 0.0
    
    def check_budget_warning(self, month: str, zth: str = None) -> List[Dict]:
        """检查预算超支预警
        
        Args:
            month: 月份，格式 YYYY-MM
            zth: 账套号，默认使用当前账套
            
        Returns:
            List[Dict]: 预警列表，包含预警类型和消息
        """
        if not self.db_manager.is_connected():
            return []
        
        if zth is None:
            zth = self.db_manager.current_account
        
        warnings = []
        
        try:
            budget = self.get_monthly_budget(month, zth)
            
            # 如果未设置预算，不产生预警
            if budget <= 0:
                logger.debug(f"[预算管理] {month} 未设置预算")
                return warnings
            
            actual = self.get_monthly_expense(month, zth)
            usage_rate = (actual / budget * 100) if budget > 0 else 0
            
            logger.info(f"[预算管理] {month} 预算使用情况: {actual:.2f}/{budget:.2f} ({usage_rate:.1f}%)")
            
            # 达到80%预警
            if actual > budget * 0.8:
                warnings.append({
                    'type': 'warning',
                    'level': 1,
                    'message': f'{month} 支出已达预算的 {usage_rate:.1f}% ({actual:.2f}/{budget:.2f})',
                    'budget': budget,
                    'actual': actual,
                    'usage_rate': usage_rate
                })
            
            # 超预算警告
            if actual > budget:
                warnings.append({
                    'type': 'danger',
                    'level': 2,
                    'message': f'{month} 支出已超预算! 超出 {(actual - budget):.2f}',
                    'budget': budget,
                    'actual': actual,
                    'usage_rate': usage_rate,
                    'overrun': actual - budget
                })
            
            return warnings
            
        except Exception as e:
            logger.error(f"[预算管理] 检查预警失败: {e}", exc_info=True)
            return []
    
    def get_budget_report(self, month: str, zth: str = None) -> Dict:
        """获取预算报告
        
        Args:
            month: 月份，格式 YYYY-MM
            zth: 账套号，默认使用当前账套
            
        Returns:
            Dict: 包含预算、支出、结余等信息的报告
        """
        if not self.db_manager.is_connected():
            return {}
        
        if zth is None:
            zth = self.db_manager.current_account
        
        try:
            budget = self.get_monthly_budget(month, zth)
            actual = self.get_monthly_expense(month, zth)
            remaining = budget - actual
            usage_rate = (actual / budget * 100) if budget > 0 else 0
            
            warnings = self.check_budget_warning(month, zth)
            
            report = {
                'month': month,
                'budget': budget,
                'actual_expense': actual,
                'remaining': remaining,
                'usage_rate': usage_rate,
                'warnings': warnings,
                'status': 'normal' if not warnings else warnings[-1]['type']
            }
            
            logger.info(f"[预算管理] 生成报告: {report}")
            return report
            
        except Exception as e:
            logger.error(f"[预算管理] 生成报告失败: {e}", exc_info=True)
            return {}
    
    def get_all_budgets(self, zth: str = None) -> List[Dict]:
        """获取所有预算记录
        
        Args:
            zth: 账套号，默认使用当前账套
            
        Returns:
            List[Dict]: 预算记录列表
        """
        if not self.db_manager.is_connected():
            return []
        
        if zth is None:
            zth = self.db_manager.current_account
        
        try:
            backend = self.db_manager.get_backend()
            backend.execute(
                "SELECT month, budget_amount, created_at, updated_at FROM sz_budget WHERE zth=? ORDER BY month DESC",
                (zth,)
            )
            results = backend.fetchall()
            
            budgets = []
            for row in results:
                budgets.append({
                    'month': row[0],
                    'budget_amount': row[1],
                    'created_at': row[2],
                    'updated_at': row[3]
                })
            
            return budgets
        except Exception as e:
            logger.error(f"[预算管理] 查询所有预算失败: {e}", exc_info=True)
            return []
    
    def delete_budget(self, month: str, zth: str = None) -> bool:
        """删除预算记录
        
        Args:
            month: 月份，格式 YYYY-MM
            zth: 账套号，默认使用当前账套
            
        Returns:
            bool: 是否删除成功
        """
        if not self.db_manager.is_connected():
            return False
        
        if zth is None:
            zth = self.db_manager.current_account
        
        try:
            backend = self.db_manager.get_backend()
            backend.execute(
                "DELETE FROM sz_budget WHERE zth=? AND month=?",
                (zth, month)
            )
            logger.info(f"[预算管理] 删除预算成功: {month}")
            return True
        except Exception as e:
            logger.error(f"[预算管理] 删除预算失败: {e}", exc_info=True)
            return False
