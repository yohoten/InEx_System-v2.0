# -*- coding: utf-8 -*-
"""
数据库连接池模块：提供 SQLite 连接池管理，支持多线程安全访问
"""

import sqlite3
import time
import traceback
from queue import Queue, Empty
from threading import Lock
from typing import Optional, Dict
from collections import defaultdict
import logging

logger = logging.getLogger('ConnectionPool')


class SQLiteConnectionPool:
    """SQLite 数据库连接池
    
    特性:
    - 预创建固定数量连接
    - 线程安全的连接获取和释放
    - 支持超时控制
    - 自动健康检查
    - 连接泄漏检测
    """
    
    def __init__(self, db_path: str, max_connections: int = 5):
        """初始化连接池
        
        Args:
            db_path: 数据库文件路径
            max_connections: 最大连接数，默认5
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = Queue(maxsize=max_connections)
        self.lock = Lock()
        self._closed = False
        
        # 连接泄漏检测
        self._connection_users = defaultdict(list)  # 跟踪连接使用者
        self._leak_threshold = 300  # 5分钟视为泄漏
        
        # 预创建连接
        logger.info(f"[连接池] 初始化，数据库: {db_path}, 最大连接数: {max_connections}")
        for i in range(max_connections):
            try:
                conn = self._create_connection()
                self.pool.put(conn)
                logger.debug(f"[连接池] 创建连接 {i+1}/{max_connections}")
            except Exception as e:
                logger.error(f"[连接池] 创建连接失败: {e}")
                raise
        
        logger.info("[连接池] 初始化完成")
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建新的数据库连接
        
        Returns:
            sqlite3.Connection: 新的数据库连接
        """
        conn = sqlite3.connect(self.db_path)
        # 启用外键支持
        conn.execute("PRAGMA foreign_keys = ON")
        # 设置 WAL 模式以提高并发性能
        conn.execute("PRAGMA journal_mode = WAL")
        # 设置同步模式
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn
    
    def get_connection(self, timeout: int = 5) -> sqlite3.Connection:
        """从连接池获取连接
        
        Args:
            timeout: 超时时间（秒），默认5秒
            
        Returns:
            sqlite3.Connection: 数据库连接
            
        Raises:
            Exception: 连接池已满或超时
        """
        if self._closed:
            raise Exception("连接池已关闭")
        
        try:
            conn = self.pool.get(timeout=timeout)
            # 健康检查：验证连接是否有效
            if not self._is_connection_valid(conn):
                logger.warning("[连接池] 检测到无效连接，重新创建")
                conn = self._create_connection()
            
            # 记录调用栈用于泄漏检测
            stack = traceback.extract_stack()
            self._connection_users[id(conn)].append({
                'time': time.time(),
                'stack': stack
            })
            
            logger.debug("[连接池] 获取连接成功")
            return conn
        except Empty:
            raise Exception("数据库连接池已满，请稍后重试")
        except Exception as e:
            logger.error(f"[连接池] 获取连接失败: {e}")
            raise
    
    def release_connection(self, conn: sqlite3.Connection):
        """释放连接回连接池
        
        Args:
            conn: 要释放的数据库连接
        """
        if self._closed:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"[连接池] 关闭已失效连接失败: {e}")
            return
        
        try:
            # 清除泄漏检测记录
            conn_id = id(conn)
            if conn_id in self._connection_users:
                self._connection_users[conn_id].clear()
            
            # 检查连接是否仍然有效
            if self._is_connection_valid(conn):
                self.pool.put_nowait(conn)
                logger.debug("[连接池] 释放连接成功")
            else:
                logger.warning("[连接池] 连接已失效，丢弃并创建新连接")
                conn.close()
                new_conn = self._create_connection()
                self.pool.put_nowait(new_conn)
        except Exception as e:
            logger.error(f"[连接池] 释放连接失败: {e}")
            try:
                conn.close()
            except Exception as e2:
                logger.warning(f"[连接池] 清理失败连接出错: {e2}")
    
    def _is_connection_valid(self, conn: sqlite3.Connection) -> bool:
        """检查连接是否有效
        
        Args:
            conn: 数据库连接
            
        Returns:
            bool: 连接是否有效
        """
        try:
            conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.debug(f"[连接池] 连接有效性检查失败: {e}")
            return False
    
    def close_all(self):
        """关闭所有连接"""
        if self._closed:
            return
        
        self._closed = True
        logger.info("[连接池] 开始关闭所有连接")
        
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Exception as e:
                logger.warning(f"[连接池] 关闭连接时出错: {e}")
        
        logger.info("[连接池] 所有连接已关闭")
    
    def check_leaks(self) -> list:
        """检查连接泄漏
        
        Returns:
            list: 泄漏的连接列表，包含持有时间和分配位置
        """
        current_time = time.time()
        leaks = []
        
        for conn_id, users in self._connection_users.items():
            for user in users:
                held_time = current_time - user['time']
                if held_time > self._leak_threshold:
                    leaks.append({
                        'conn_id': conn_id,
                        'held_for_seconds': held_time,
                        'stack': user['stack']
                    })
        
        if leaks:
            logger.warning(f"[连接池] ⚠️ 检测到 {len(leaks)} 个可能的连接泄漏")
            for i, leak in enumerate(leaks, 1):
                logger.warning(f"  泄漏 #{i}:")
                logger.warning(f"    持有时间: {leak['held_for_seconds']:.0f}秒 ({leak['held_for_seconds']/60:.1f}分钟)")
                logger.warning(f"    分配位置:")
                for line in traceback.format_list(leak['stack'])[-5:]:  # 只显示最后5行
                    logger.warning(f"      {line.strip()}")
        
        return leaks
    
    def get_pool_status(self) -> Dict:
        """获取连接池状态
        
        Returns:
            Dict: 包含连接池状态信息
        """
        return {
            'total': self.max_connections,
            'available': self.pool.qsize(),
            'in_use': self.max_connections - self.pool.qsize()
        }


class ConnectionContextManager:
    """连接上下文管理器
    
    使用示例:
        with ConnectionContextManager(pool) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
    """
    
    def __init__(self, pool: SQLiteConnectionPool):
        self.pool = pool
        self.conn = None
    
    def __enter__(self):
        self.conn = self.pool.get_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.pool.release_connection(self.conn)
            self.conn = None
        return False


