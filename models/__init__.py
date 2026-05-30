# -*- coding: utf-8 -*-
"""
收支管理系统 - 数据模型层
包含数据库后端、连接池、预算管理和配置管理模块
"""

from models.db_backend import db_manager, EnhancedDataManager as DataManager
from models.db_pool import SQLiteConnectionPool, ConnectionContextManager
from models.budget_manager import BudgetManager, BudgetAlert
from models.config import ConfigManager

__version__ = '2.0'
__author__ = '滕宇豪'

__all__ = [
    'db_manager',
    'DataManager',
    'SQLiteConnectionPool',
    'ConnectionContextManager',
    'BudgetManager',
    'BudgetAlert',
    'ConfigManager'
]