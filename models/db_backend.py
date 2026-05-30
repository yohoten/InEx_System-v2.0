# -*- coding: utf-8 -*-
"""
数据库管理器 v2.0
支持 SQLite / MySQL 8.0（连接池） / Sybase Anywhere 9（多连接方式）
提供自动重连、SQL兼容性适配、性能监控等功能
"""

import sqlite3
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from utils.logger import log_manager  # 新增:导入日志管理器

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DatabaseEnhanced')


class DatabaseBackend:
    """数据库后端抽象基类"""
    
    def connect(self, **params):
        raise NotImplementedError
    
    def disconnect(self):
        raise NotImplementedError
    
    def is_connected(self) -> bool:
        raise NotImplementedError
    
    def execute(self, sql: str, params=None):
        raise NotImplementedError

    def begin_transaction(self):
        """开始事务"""
        pass

    def commit_transaction(self):
        """提交事务"""
        pass

    def rollback_transaction(self):
        """回滚事务"""
        pass
    
    def fetchall(self):
        raise NotImplementedError
    
    def fetchone(self):
        raise NotImplementedError
    
    def get_backend_type(self) -> str:
        """获取数据库类型"""
        raise NotImplementedError


class SQLiteBackend(DatabaseBackend):
    """SQLite 数据库后端实现"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.db_path = 'inex.db'
    
    def connect(self, **params):
        """连接到 SQLite 数据库"""
        self.db_path = params.get('database', 'inex.db')
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            # 启用外键支持
            self.cursor.execute("PRAGMA foreign_keys = ON")
            return True
        except Exception as e:
            log_manager.error(f"SQLite连接失败：{str(e)}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.conn is not None
    
    def execute(self, sql: str, params=None):
        """执行 SQL 语句"""
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        self.conn.commit()

    def begin_transaction(self):
        """开始事务（暂停自动提交）"""
        self.cursor.execute("BEGIN IMMEDIATE")

    def commit_transaction(self):
        """提交事务（恢复自动提交）"""
        self.conn.commit()

    def rollback_transaction(self):
        """回滚事务"""
        self.conn.rollback()
    
    def fetchall(self):
        """获取所有结果"""
        return self.cursor.fetchall()
    
    def fetchone(self):
        """获取单条结果"""
        return self.cursor.fetchone()
    
    def get_backend_type(self) -> str:
        return "SQLite"


class EnhancedMySQLBackend(DatabaseBackend):
    """MySQL后端 - 支持连接池和自动重连"""
    
    def __init__(self, pool_size=5, max_overflow=10):
        self.pool = None
        self.conn = None
        self.cursor = None
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.config = {}
        self._last_used = time.time()
        self._query_count = 0
        self._total_query_time = 0
    
    def connect(self, **params):
        """初始化连接池并获取连接"""
        try:
            import pymysql
            try:
                from dbutils.pooled_db import PooledDB
            except ImportError:
                # DBUtils 3.x 版本的导入路径
                from DBUtils.PooledDB import PooledDB
            
            # 构建连接池配置
            pool_config = {
                'creator': pymysql,
                'maxconnections': self.pool_size + self.max_overflow,
                'mincached': 2,  # 启动时创建的最小连接数
                'maxcached': self.pool_size,  # 闲置连接池最大数量
                # 'maxshared': 3,  # 已移除：pymysql 不支持此参数
                'blocking': True,  # 连接池满时阻塞等待
                'maxusage': 1000,  # 单个连接最多复用次数
                'recycle': 3600,  # 连接回收时间（秒）
                
                # 数据库连接参数
                'host': params.get('host', 'localhost'),
                'port': params.get('port', 3306),
                'user': params.get('user', 'root'),
                'password': params.get('password', ''),
                'database': params.get('database', 'inex_db'),
                'charset': params.get('charset', 'utf8mb4'),
                'autocommit': True,
                
                # 连接超时设置
                'connect_timeout': 10,
                'read_timeout': 30,
                'write_timeout': 30,
            }
            
            # 创建连接池
            self.pool = PooledDB(**pool_config)
            self.config = pool_config
            
            # 从池中获取初始连接
            self._acquire_connection()
            
            logger.info(f"[MySQL] 连接池初始化成功 (池大小:{self.pool_size}, 最大溢出:{self.max_overflow})")
            return True
            
        except ImportError as e:
            logger.error(f"[MySQL] 缺少依赖: {e}")
            logger.error("[MySQL] 请运行: pip install DBUtils pymysql")
            return False
        except Exception as e:
            logger.error(f"[MySQL] 连接池初始化失败: {e}")
            return False
    
    def _acquire_connection(self):
        """从连接池获取连接"""
        if self.pool:
            self.conn = self.pool.connection()
            self.cursor = self.conn.cursor()
            self._last_used = time.time()
    
    def _release_connection(self):
        """释放连接回池"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()  # 实际是返回到池中
            self.conn = None
            self.cursor = None
    
    def execute(self, sql: str, params=None, retry=3):
        """执行SQL - 带自动重连和性能监控"""
        for attempt in range(retry):
            try:
                # 检查连接是否有效
                if not self._is_connection_valid():
                    logger.warning(f"[MySQL] 连接失效，尝试重连 ({attempt+1}/{retry})")
                    self._reconnect()
                
                # 执行查询并计时
                start_time = time.time()
                if params:
                    self.cursor.execute(sql, params)
                else:
                    self.cursor.execute(sql)
                
                duration = (time.time() - start_time) * 1000
                self._query_count += 1
                self._total_query_time += duration
                
                # 记录慢查询
                if duration > 1000:
                    logger.warning(f"[MySQL] 慢查询: {duration:.0f}ms\n{sql[:100]}")
                
                self.conn.commit()
                self._last_used = time.time()
                return
                
            except Exception as e:
                error_code = getattr(e, 'args', [None])[0] if hasattr(e, 'args') else None
                
                # 可重试的错误码
                if error_code in (2006, 2013, 2055):  # Server gone away / Lost connection
                    logger.warning(f"[MySQL] 连接错误 {error_code}，尝试重连...")
                    self._reconnect()
                    continue
                else:
                    logger.error(f"[MySQL] 执行失败: {e}\nSQL: {sql[:200]}")
                    if self.conn:
                        self.conn.rollback()
                    raise
        
        raise Exception(f"[MySQL] 重试{retry}次后仍失败")
    
    def _is_connection_valid(self) -> bool:
        """检查连接是否有效"""
        if not self.conn or not self.cursor:
            return False
        
        # 检查连接空闲时间（超过30分钟主动重连）
        if time.time() - self._last_used > 1800:
            return False
        
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"[MySQL] 连接检查失败: {e}")
            return False
    
    def _reconnect(self):
        """重新建立连接"""
        self._release_connection()
        self._acquire_connection()
        logger.info("[MySQL] 重连成功")
    
    def disconnect(self):
        """关闭连接池"""
        self._release_connection()
        if self.pool:
            self.pool.close()
            self.pool = None
        logger.info("[MySQL] 连接池已关闭")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.pool is not None and self._is_connection_valid()
    
    def fetchall(self):
        """获取所有结果"""
        result = self.cursor.fetchall()
        self._last_used = time.time()
        return result
    
    def fetchone(self):
        """获取单条结果"""
        result = self.cursor.fetchone()
        self._last_used = time.time()
        return result
    
    def get_backend_type(self) -> str:
        return "MySQL 8.0 (Enhanced with Connection Pool)"
    
    def get_pool_status(self) -> dict:
        """获取连接池状态（用于监控）"""
        if not self.pool:
            return {}
        
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'connections_in_use': self.pool._conns.qsize() if hasattr(self.pool, '_conns') else 0,
            'idle_connections': self.pool._idle_cache.qsize() if hasattr(self.pool, '_idle_cache') else 0,
            'total_queries': self._query_count,
            'avg_query_time_ms': round(self._total_query_time / max(1, self._query_count), 2),
        }


class EnhancedSybaseBackend(DatabaseBackend):
    """Sybase后端 - 支持多种连接方式和友好错误提示"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.config = {}
        self._query_count = 0
        self._total_query_time = 0
    
    def connect(self, **params):
        """智能连接Sybase - 自动选择最佳连接方式
        
        连接优先级:
        1. sqlanydb 驱动（文件直连，最快最方便）
        2. pyodbc DSN连接（传统方式）
        3. pyodbc DSN-less连接（推荐生产环境）
        4. pyodbc 文件直连（单机模式）
        """
        
        # 步骤1: 先尝试 sqlanydb（最快方式，无需ODBC配置）
        try:
            logger.info("[Sybase] 尝试 sqlanydb 驱动...")
            if self._connect_via_sqlanydb(params):
                logger.info("[Sybase] sqlanydb 连接成功")
                return True
        except ImportError:
            logger.info("[Sybase] sqlanydb 未安装，尝试 pyodbc...")
        except Exception as e:
            logger.warning(f"[Sybase] sqlanydb 连接失败: {e}")
        
        # 步骤2: 检查 pyodbc 驱动
        if not self._check_driver_installed():
            self._show_driver_install_guide()
            return False
        
        # 步骤3: 尝试多种 pyodbc 连接方式
        connection_methods = [
            ('DSN连接', self._connect_via_dsn, params),
            ('DSN-less连接', self._connect_via_dsnless, params),
            ('文件直连', self._connect_via_file, params),
        ]
        
        last_error = None
        for method_name, connect_func, method_params in connection_methods:
            try:
                logger.info(f"[Sybase] 尝试{method_name}...")
                if connect_func(method_params):
                    logger.info(f"[Sybase] {method_name}成功")
                    return True
            except Exception as e:
                last_error = e
                logger.warning(f"[Sybase] {method_name}失败: {e}")
                continue
        
        # 所有方法都失败
        error_msg = self._parse_sybase_error(last_error)
        logger.error(f"[Sybase] 所有连接方式均失败: {error_msg}")
        return False
    
    def _connect_via_sqlanydb(self, params) -> bool:
        """通过 sqlanydb 驱动连接（文件直连，无需ODBC配置）
        
        sqlanydb 是 Sybase SQL Anywhere 的原生 Python 驱动，
        比 pyodbc 更方便，无需配置 ODBC 数据源。
        """
        import sqlanydb
        
        db_file = params.get('db_file', '')
        if not db_file or not os.path.exists(db_file):
            # 如果 db_file 不存在但有 dbf 参数，尝试使用 dbf
            db_file = params.get('dbf', db_file)
            if not db_file or not os.path.exists(db_file):
                raise FileNotFoundError(f"数据库文件不存在: {db_file}")
        
        uid = params.get('uid', params.get('UID', 'DBA'))
        pwd = params.get('pwd', params.get('PWD', 'sql'))
        
        self.conn = sqlanydb.connect(
            dbf=db_file,
            uid=uid,
            pwd=pwd
        )
        self.cursor = self.conn.cursor()
        
        # 验证连接
        try:
            self.cursor.execute("SELECT @@VERSION")
            version = self.cursor.fetchone()[0]
            logger.info(f"[Sybase sqlanydb] 连接成功，版本: {version}")
        except Exception:
            logger.info(f"[Sybase sqlanydb] 连接成功")
        
        return True
    
    def _check_driver_installed(self) -> bool:
        """检查Sybase ODBC驱动是否安装"""
        try:
            import pyodbc
            drivers = pyodbc.drivers()
            sybase_drivers = [d for d in drivers if 'Adaptive Server Anywhere' in d or 'SQL Anywhere' in d]
            
            if not sybase_drivers:
                logger.error("[Sybase] 未检测到Sybase ODBC驱动")
                return False
            
            logger.info(f"[Sybase] 检测到驱动: {sybase_drivers}")
            return True
            
        except ImportError:
            logger.error("[Sybase] pyodbc库未安装")
            return False
        except Exception as e:
            logger.error(f"[Sybase] 驱动检测失败: {e}")
            return False
    
    def _connect_via_dsn(self, params) -> bool:
        """通过DSN连接（传统方式）"""
        import pyodbc
        
        dsn = params.get('dsn', '')
        if not dsn:
            raise ValueError("DSN名称不能为空")
        
        uid = params.get('uid', 'dba')
        pwd = params.get('pwd', 'sql')
        dbn = params.get('dbn', 'inex_db')
        
        connection_string = (
            f"DRIVER={{Adaptive Server Anywhere 9.0}};"
            f"DSN={dsn};"
            f"UID={uid};"
            f"PWD={pwd};"
            f"DBN={dbn};"
            f"CommLinks=tcpip{{Host=localhost}};"
            f"Timeout=30;"
        )
        
        self.conn = pyodbc.connect(connection_string, timeout=30, autocommit=True)
        self.cursor = self.conn.cursor()
        
        # 验证连接
        self.cursor.execute("SELECT @@version")
        version = self.cursor.fetchone()[0]
        logger.info(f"[Sybase DSN] 连接成功，版本: {version}")
        
        return True
    
    def _connect_via_dsnless(self, params) -> bool:
        """DSN-less连接（无需配置ODBC，推荐）"""
        import pyodbc
        
        host = params.get('host', 'localhost')
        port = params.get('port', 2638)  # Sybase默认端口
        uid = params.get('uid', 'dba')
        pwd = params.get('pwd', 'sql')
        dbn = params.get('dbn', 'inex_db')
        eng = params.get('eng', 'inex_server')  # 服务器引擎名
        
        connection_string = (
            f"DRIVER={{Adaptive Server Anywhere 9.0}};"
            f"ENG={eng};"
            f"LINKS=tcpip{{HOST={host};PORT={port}}};"
            f"UID={uid};"
            f"PWD={pwd};"
            f"DBN={dbn};"
            f"Timeout=30;"
        )
        
        self.conn = pyodbc.connect(connection_string, timeout=30, autocommit=True)
        self.cursor = self.conn.cursor()
        
        logger.info(f"[Sybase DSN-less] 连接成功: {host}:{port}/{dbn}")
        return True
    
    def _connect_via_file(self, params) -> bool:
        """直接连接数据库文件（单机模式）"""
        import pyodbc
        
        db_file = params.get('db_file', '')
        if not db_file or not os.path.exists(db_file):
            raise FileNotFoundError(f"数据库文件不存在: {db_file}")
        
        uid = params.get('uid', 'dba')
        pwd = params.get('pwd', 'sql')
        
        connection_string = (
            f"DRIVER={{Adaptive Server Anywhere 9.0}};"
            f"DBF={db_file};"
            f"UID={uid};"
            f"PWD={pwd};"
            f"ENG=inex_server;"
            f"AutoStop=NO;"  # 最后一个连接断开时不停止服务器
            f"Timeout=30;"
        )
        
        self.conn = pyodbc.connect(connection_string, timeout=30, autocommit=True)
        self.cursor = self.conn.cursor()
        
        logger.info(f"[Sybase File] 连接成功: {db_file}")
        return True
    
    def _show_driver_install_guide(self):
        """显示驱动安装指南（控制台输出）"""
        guide = """
╔══════════════════════════════════════════════════════════╗
║          Sybase SQL Anywhere 9 驱动安装指南              ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  您已确认安装了 \"Adaptive Server Anywhere 9.0\" 驱动     ║
║                                                          ║
║  下一步：配置DSN或直接在应用中连接                       ║
║                                                          ║
║  方法1: 配置系统DSN（推荐初次使用）                      ║
║    1. 打开 \"ODBC数据源管理器(32位)\"                    ║
║    2. 切换到 \"系统DSN\" 标签页                          ║
║    3. 点击 \"添加\"                                      ║
║    4. 选择 \"Adaptive Server Anywhere 9.0\"             ║
║    5. 填写配置：                                         ║
║       - Data Source Name: InExSystem                     ║
║       - User ID: dba                                     ║
║       - Password: sql                                    ║
║       - Database File: 您的数据库路径                     ║
║       - Server Name: inex_server                         ║
║    6. 点击 \"Test Connection\" 测试                      ║
║    7. 点击 \"OK\" 保存                                   ║
║                                                          ║
║  方法2: DSN-less连接（应用内自动处理）                   ║
║    在应用中选择Sybase，输入：                             ║
║    - 主机: localhost                                     ║
║    - 端口: 2638                                          ║
║    - 用户名: dba                                         ║
║    - 密码: sql                                           ║
║    - 数据库文件: 完整路径                                 ║
║                                                          ║
║  注意: 使用前需启动Sybase服务器                          ║
║    dbsrv9.exe -n inex_server your_db.db                  ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """
        log_manager.info(guide)
    
    def _parse_sybase_error(self, error):
        """解析Sybase错误代码，提供精准提示"""
        if not error:
            return "未知错误"
        
        error_str = str(error).upper()
        
        error_map = {
            'DATA SOURCE NAME NOT FOUND': 
                "ODBC DSN未配置\n请在ODBC数据源管理器中添加DSN",
            
            'INVALID USER ID OR PASSWORD':
                "用户名或密码错误\n默认账户: dba/sql",
            
            'DATABASE SERVER NOT FOUND':
                "数据库服务器未启动\n请运行: dbsrv9.exe -n inex_server inex.db",
            
            'DATABASE FILE NOT FOUND':
                "数据库文件不存在\n请检查文件路径是否正确",
            
            'LICENSE EXPIRED':
                "Sybase许可证已过期\n请联系管理员更新许可证",
            
            'TOO MANY CONNECTIONS':
                "连接数已达上限\n请关闭其他连接或增加最大连接数",
        }
        
        for key, message in error_map.items():
            if key in error_str:
                return message
        
        return f"未知错误: {str(error)}"
    
    def disconnect(self):
        """断开连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("[Sybase] 连接已关闭")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.conn:
            return False
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"[Sybase] 连接检查失败: {e}")
            return False
    
    def execute(self, sql: str, params=None):
        """执行SQL"""
        try:
            start_time = time.time()
            
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            duration = (time.time() - start_time) * 1000
            self._query_count += 1
            self._total_query_time += duration
            
            # 记录慢查询
            if duration > 1000:
                logger.warning(f"[Sybase] 慢查询: {duration:.0f}ms\n{sql[:100]}")
            
            self.conn.commit()
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            error_msg = self._parse_sybase_error(e)
            logger.error(f"[Sybase] 执行失败: {error_msg}\nSQL: {sql[:200]}")
            raise
    
    def fetchall(self):
        """获取所有结果"""
        return self.cursor.fetchall()
    
    def fetchone(self):
        """获取单条结果"""
        return self.cursor.fetchone()
    
    def get_backend_type(self) -> str:
        return "Sybase Anywhere 9 (Enhanced)"
    
    def get_performance_stats(self) -> dict:
        """获取性能统计"""
        return {
            'total_queries': self._query_count,
            'avg_query_time_ms': round(self._total_query_time / max(1, self._query_count), 2),
        }


class SQLFileImporter:
    """SQL 文件导入器（通用）"""
    
    def __init__(self, backend: DatabaseBackend):
        self.backend = backend
    
    def execute_sql_file(self, sql_file_path: str, encoding: str = 'auto') -> Dict[str, int]:
        """执行 SQL 文件中的所有语句（事务优化 + 自动重建流水账和月报表）

        Args:
            sql_file_path: SQL 文件路径
            encoding: 文件编码（'auto' 自动检测，或指定 'utf-8', 'gbk' 等）

        Returns:
            执行统计 {表名: 影响行数}
        """
        stats = {}

        try:
            # 自动检测编码
            if encoding == 'auto':
                encoding = self._detect_encoding(sql_file_path)
                log_manager.info(f"SQL导入检测到文件编码：{encoding}")

            with open(sql_file_path, 'r', encoding=encoding) as f:
                content = f.read()

            # 分割 SQL 语句（按分号分隔）
            statements = self._split_sql_statements(content)

            log_manager.info(f"SQL导入找到 {len(statements)} 条 SQL 语句")

            # 开始事务——大幅提升导入速度
            self.backend.begin_transaction()

            executed = 0
            has_data_changes = False
            for i, stmt in enumerate(statements, 1):
                stmt = stmt.strip()
                if not stmt or stmt.startswith('--'):
                    continue

                try:
                    # 提取表名（用于统计）
                    table_name = self._extract_table_name(stmt)

                    # 执行 SQL（事务期间不自动提交）
                    self.backend.cursor.execute(stmt)

                    # 统计
                    if table_name:
                        stats[table_name] = stats.get(table_name, 0) + 1
                        if table_name in ('sz_sheet_sr', 'sz_sheet_zc', 'sz_d_zt'):
                            has_data_changes = True

                    executed += 1

                    if i % 500 == 0:
                        log_manager.debug(f"SQL导入进度：已执行 {i}/{len(statements)} 条语句...")

                except Exception as e:
                    log_manager.warning(f"SQL导入第 {i} 条语句执行失败：{str(e)[:100]}")

            # 提交事务
            self.backend.commit_transaction()
            log_manager.info(f"SQL导入完成：成功执行 {executed}/{len(statements)} 条语句")

            # 如果导入了收支数据，自动重建流水账和月报表
            if has_data_changes:
                log_manager.info("检测到数据变更，自动重建流水账和月报表...")
                self._rebuild_derived_tables()
                log_manager.info("流水账和月报表重建完成")

            return stats

        except Exception as e:
            try:
                self.backend.rollback_transaction()
            except Exception:
                pass
            log_manager.error(f"SQL导入失败：{str(e)}", exc_info=True)
            return {}

    def _rebuild_derived_tables(self):
        """重建所有账套的流水账和月报表"""
        try:
            cur = self.backend.cursor
            # 获取所有账套号
            cur.execute("SELECT zth FROM sz_d_zt")
            zth_list = [row[0] for row in cur.fetchall()]

            # === 重建流水账 ===
            cur.execute("DELETE FROM sz_table_lsz")
            for zth in zth_list:
                cur.execute("""
                    SELECT rq, 'SR' as srzc, djh, sr_code, je, 0, zf_code, bz
                    FROM sz_sheet_sr WHERE zth = ?
                    UNION ALL
                    SELECT rq, 'ZC' as srzc, djh, zc_code, 0, je, zf_code, bz
                    FROM sz_sheet_zc WHERE zth = ?
                    ORDER BY rq, srzc DESC, djh
                """, (zth, zth))
                records = cur.fetchall()
                balance = 0.0
                for xh, rec in enumerate(records, 1):
                    rq, srzc, djh, code, srje, zcje, zf_code, bz = rec
                    if srzc == 'SR':
                        balance += float(srje or 0)
                    else:
                        balance -= float(zcje or 0)
                    cur.execute("""
                        INSERT INTO sz_table_lsz (zth, rq, xh, srzc, djh, sr_code, srje, zc_code, zcje, ye, zf_code, bz)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (zth, rq, xh, srzc, djh,
                          code if srzc == 'SR' else None, srje,
                          code if srzc == 'ZC' else None, zcje,
                          round(balance, 2), zf_code, bz))

            # === 重建月报表（含期初余额结转）===
            cur.execute("DELETE FROM sz_report_srzc")
            cur.execute("""
                SELECT DISTINCT strftime('%Y-%m', rq) FROM sz_sheet_sr
                UNION SELECT DISTINCT strftime('%Y-%m', rq) FROM sz_sheet_zc ORDER BY 1
            """)
            months = [row[0] for row in cur.fetchall()]

            for zth in zth_list:
                prev_qmye = {}
                for ym in months:
                    qsrq = f"{ym}-01"
                    y, m = int(ym.split('-')[0]), int(ym.split('-')[1])
                    jsrq = f"{y+1}-01-01" if m == 12 else f"{y}-{m+1:02d}-01"
                    cur.execute("""
                        SELECT zf_code,
                               SUM(CASE WHEN srzc='SR' THEN srje ELSE 0 END),
                               SUM(CASE WHEN srzc='ZC' THEN zcje ELSE 0 END)
                        FROM sz_table_lsz
                        WHERE zth=? AND strftime('%Y-%m', rq)=?
                        GROUP BY zf_code
                    """, (zth, ym))
                    for row in cur.fetchall():
                        zf_code, srje, zcje = row
                        srje, zcje = float(srje or 0), float(zcje or 0)
                        qcye = prev_qmye.get(zf_code, 0.0)
                        qmye = round(qcye + srje - zcje, 2)
                        cur.execute("""
                            INSERT INTO sz_report_srzc (zth, qsrq, jsrq, zf_code, qcye, srje, zcje, qmye)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (zth, qsrq, jsrq, zf_code, round(qcye, 2), round(srje, 2), round(zcje, 2), qmye))
                        prev_qmye[zf_code] = qmye

            self.backend.conn.commit()
        except Exception as e:
            log_manager.warning(f"重建派生表时出错（可稍后手动重建）: {e}")
    
    def _detect_encoding(self, file_path: str) -> str:
        """检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            编码名称
        """
        # 常见编码列表（按优先级排序）
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 尝试读取前 1KB
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # 默认返回 utf-8
        return 'utf-8'
    
    def _split_sql_statements(self, content: str) -> List[str]:
        """智能分割 SQL 语句（处理引号内的分号）"""
        statements = []
        current_stmt = ""
        in_single_quote = False
        in_double_quote = False
        
        for char in content:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current_stmt += char
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current_stmt += char
            elif char == ';' and not in_single_quote and not in_double_quote:
                # 语句结束
                if current_stmt.strip():
                    statements.append(current_stmt.strip())
                current_stmt = ""
            else:
                current_stmt += char
        
        # 添加最后一条语句（如果没有分号结尾）
        if current_stmt.strip():
            statements.append(current_stmt.strip())
        
        return statements
    
    def _extract_table_name(self, sql: str) -> Optional[str]:
        """从 SQL 语句中提取表名"""
        import re
        
        sql_upper = sql.upper().strip()
        
        # INSERT INTO table_name
        match = re.search(r'INSERT\s+INTO\s+(\w+)', sql_upper)
        if match:
            return match.group(1).lower()
        
        # CREATE TABLE table_name
        match = re.search(r'CREATE\s+TABLE\s+(\w+)', sql_upper)
        if match:
            return match.group(1).lower()
        
        # UPDATE table_name
        match = re.search(r'UPDATE\s+(\w+)', sql_upper)
        if match:
            return match.group(1).lower()
        
        # DELETE FROM table_name
        match = re.search(r'DELETE\s+FROM\s+(\w+)', sql_upper)
        if match:
            return match.group(1).lower()
        
        return None


class EnhancedDataManager:
    """数据管理器 - 支持多种数据库后端"""
    
    def __init__(self):
        self._backend: Optional[DatabaseBackend] = None
        self._demo_mode = True
        self.current_account = '2501033401'  # 默认账套号
    
    def set_backend(self, backend: DatabaseBackend):
        """设置数据库后端"""
        if self._backend:
            self._backend.disconnect()
        self._backend = backend
        self._demo_mode = False
    
    def get_backend(self) -> Optional[DatabaseBackend]:
        """获取当前数据库后端"""
        return self._backend
    
    def is_connected(self) -> bool:
        """检查是否已连接数据库"""
        return self._backend is not None and self._backend.is_connected()
    
    def connect_sqlite(self, db_path='inex.db'):
        """连接 SQLite 数据库"""
        backend = SQLiteBackend()
        if backend.connect(database=db_path):
            self.set_backend(backend)
            logger.info(f"[数据库] 已连接到 SQLite: {db_path}")
            return True
        return False
    
    def connect_mysql(self, host='localhost', port=3306, user='root', 
                     password='', database='inex_db', pool_size=5):
        """连接 MySQL 8.0 数据库（带连接池）"""
        backend = EnhancedMySQLBackend(pool_size=pool_size)
        if backend.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        ):
            self.set_backend(backend)
            logger.info(f"[数据库] 已连接到 MySQL: {host}:{port}/{database}")
            return True
        return False
    
    def connect_sybase(self, dsn='', uid='dba', pwd='sql', dbn='inex_db',
                      host='localhost', port=2638, db_file=''):
        """连接 Sybase Anywhere 9 数据库（智能选择连接方式）"""
        backend = EnhancedSybaseBackend()
        
        # 根据参数自动选择连接方式
        params = {
            'dsn': dsn,
            'uid': uid,
            'pwd': pwd,
            'dbn': dbn,
            'host': host,
            'port': port,
            'db_file': db_file,
        }
        
        if backend.connect(**params):
            self.set_backend(backend)
            logger.info(f"[数据库] 已连接到 Sybase")
            return True
        return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self._backend:
            self._backend.disconnect()
            self._backend = None
            self._demo_mode = True
            logger.info("[数据库] 已断开连接")
    
    # ========== 事务管理方法 ==========
    
    def begin_transaction(self):
        """开始事务"""
        if self.is_connected():
            backend_type = self._backend.get_backend_type()
            try:
                if 'SQLite' in backend_type:
                    self._backend.execute("BEGIN TRANSACTION")
                elif 'MySQL' in backend_type:
                    self._backend.execute("START TRANSACTION")
                elif 'Sybase' in backend_type:
                    # Sybase 默认自动提交，需要显式关闭
                    self._backend.execute("SET CHAINED ON")
                logger.debug("[事务] 事务已开始")
            except Exception as e:
                logger.error(f"[事务] 开始事务失败: {e}")
                raise
    
    def commit_transaction(self):
        """提交事务"""
        if self.is_connected():
            try:
                backend_type = self._backend.get_backend_type()
                if 'SQLite' in backend_type or 'MySQL' in backend_type:
                    self._backend.conn.commit()
                elif 'Sybase' in backend_type:
                    self._backend.conn.commit()
                    self._backend.execute("SET CHAINED OFF")
                logger.debug("[事务] 事务已提交")
            except Exception as e:
                logger.error(f"[事务] 提交事务失败: {e}")
                raise
    
    def rollback_transaction(self):
        """回滚事务"""
        if self.is_connected():
            try:
                backend_type = self._backend.get_backend_type()
                if 'SQLite' in backend_type or 'MySQL' in backend_type:
                    self._backend.conn.rollback()
                elif 'Sybase' in backend_type:
                    self._backend.conn.rollback()
                    self._backend.execute("SET CHAINED OFF")
                logger.warning("[事务] 事务已回滚")
            except Exception as e:
                logger.error(f"[事务] 回滚事务失败: {e}")
                raise
    
    # ========== 业务数据操作方法 ==========
    
    def get_income_types(self) -> List[Tuple[str, str]]:
        """获取收入类型列表"""
        if not self.is_connected():
            return []
        self._backend.execute("SELECT sr_code, sr_name FROM sz_c_sr")
        return self._backend.fetchall()
    
    def get_expense_types(self) -> List[Tuple[str, str]]:
        """获取支出类型列表"""
        if not self.is_connected():
            return []
        self._backend.execute("SELECT zc_code, zc_name FROM sz_c_zc")
        return self._backend.fetchall()
    
    def get_payment_methods(self) -> List[Tuple[str, str]]:
        """获取支付方式列表"""
        if not self.is_connected():
            return []
        self._backend.execute("SELECT zf_code, zf_name FROM sz_c_zf")
        return self._backend.fetchall()
    
    def get_account_info(self, zth: str) -> Optional[Tuple]:
        """获取账套信息"""
        if not self.is_connected():
            return None
        self._backend.execute(
            "SELECT * FROM sz_d_zt WHERE zth=?",
            (zth,)
        )
        return self._backend.fetchone()
    
    def get_accounts(self) -> List[Tuple]:
        """获取所有账套列表"""
        if not self.is_connected():
            return []
        self._backend.execute("SELECT * FROM sz_d_zt ORDER BY zth")
        return self._backend.fetchall()
    
    def get_income_records(self, filters=None, limit=None, offset=None) -> List[Tuple]:
        """获取收入记录（支持条件筛选和分页）

        Args:
            filters: 筛选条件字典
            limit: 返回行数限制（None=全部）
            offset: 偏移量（配合limit使用）
        """
        if not self.is_connected():
            return []

        sql = """
            SELECT s.djh, s.rq, c.sr_name, s.je, z.zf_name, s.bz, s.sr_code, s.zf_code
            FROM sz_sheet_sr s
            LEFT JOIN sz_c_sr c ON s.sr_code = c.sr_code
            LEFT JOIN sz_c_zf z ON s.zf_code = z.zf_code
            WHERE s.zth = ?
        """
        params = [self.current_account]

        # 应用筛选条件
        if filters:
            if filters.get('start_date'):
                sql += " AND s.rq >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                sql += " AND s.rq <= ?"
                params.append(filters['end_date'])
            if filters.get('min_amount') is not None:
                sql += " AND s.je >= ?"
                params.append(filters['min_amount'])
            if filters.get('max_amount') is not None:
                sql += " AND s.je <= ?"
                params.append(filters['max_amount'])
            if filters.get('payment_code'):
                sql += " AND s.zf_code = ?"
                params.append(filters['payment_code'])
            if filters.get('income_type_code'):
                sql += " AND s.sr_code = ?"
                params.append(filters['income_type_code'])

        sql += " ORDER BY s.rq DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)

        self._backend.execute(sql, tuple(params))
        return self._backend.fetchall()
    
    def get_expense_records(self, filters=None, limit=None, offset=None) -> List[Tuple]:
        """获取支出记录（支持条件筛选和分页）

        Args:
            filters: 筛选条件字典
            limit: 返回行数限制（None=全部）
            offset: 偏移量（配合limit使用）
        """
        if not self.is_connected():
            return []

        sql = """
            SELECT s.djh, s.rq, c.zc_name, s.je, z.zf_name, s.bz, s.zc_code, s.zf_code
            FROM sz_sheet_zc s
            LEFT JOIN sz_c_zc c ON s.zc_code = c.zc_code
            LEFT JOIN sz_c_zf z ON s.zf_code = z.zf_code
            WHERE s.zth = ?
        """
        params = [self.current_account]

        # 应用筛选条件
        if filters:
            if filters.get('start_date'):
                sql += " AND s.rq >= ?"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                sql += " AND s.rq <= ?"
                params.append(filters['end_date'])
            if filters.get('min_amount') is not None:
                sql += " AND s.je >= ?"
                params.append(filters['min_amount'])
            if filters.get('max_amount') is not None:
                sql += " AND s.je <= ?"
                params.append(filters['max_amount'])
            if filters.get('payment_code'):
                sql += " AND s.zf_code = ?"
                params.append(filters['payment_code'])
            if filters.get('expense_type_code'):
                sql += " AND s.zc_code = ?"
                params.append(filters['expense_type_code'])

        sql += " ORDER BY s.rq DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)

        self._backend.execute(sql, tuple(params))
        return self._backend.fetchall()
    
    def _generate_document_number(self, table: str) -> str:
        """生成唯一单据号（线程安全）
        
        Args:
            table: 表名 ('sz_sheet_sr' 或 'sz_sheet_zc')
            
        Returns:
            str: 唯一的单据号
        """
        import time
        
        # 使用时间戳 + 随机数确保唯一性
        timestamp = int(time.time() * 1000) % 1000000
        random_part = int.from_bytes(os.urandom(2), 'big') % 10000
        
        return f"{timestamp:06d}{random_part:04d}"
    
    def add_income_record(self, data: Dict = None, rq: str = None, sr_code: str = None, 
                         je: float = None, zf_code: str = None, bz: str = '') -> bool:
        """添加收入记录
        
        Args:
            data: 字典格式的数据（兼容旧接口）
            rq: 日期
            sr_code: 收入类型编码
            je: 金额
            zf_code: 支付方式编码
            bz: 备注
        """
        if not self.is_connected():
            return False
        
        # 兼容两种调用方式
        if data is not None:
            rq = data.get('rq')
            sr_code = data.get('sr_code')
            je = data.get('je')
            zf_code = data.get('zf_code')
            bz = data.get('bz', '')
        
        try:
            new_djh = self._generate_document_number('sz_sheet_sr')
            
            self._backend.execute("""
                INSERT INTO sz_sheet_sr (zth, djh, rq, sr_code, je, zf_code, bz)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.current_account,
                new_djh,
                rq,
                sr_code,
                je,
                zf_code,
                bz
            ))
            logger.info(f"[收入管理] 添加记录成功：单据号={new_djh}")
            return True
        except Exception as e:
            logger.error(f"[收入管理] 添加失败：{str(e)}")
            return False
    
    def add_income(self, rq: str, sr_code: str, je: float, zf_code: str, bz: str = '') -> str:
        """添加收入记录（便捷方法）"""
        if not self.is_connected():
            return ''
        
        try:
            new_djh = self._generate_document_number('sz_sheet_sr')
            
            self._backend.execute("""
                INSERT INTO sz_sheet_sr (zth, djh, rq, sr_code, je, zf_code, bz)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.current_account,
                new_djh,
                rq,
                sr_code,
                je,
                zf_code,
                bz
            ))
            logger.info(f"[收入管理] 添加记录成功：单据号={new_djh}")
            return new_djh
        except Exception as e:
            logger.error(f"[收入管理] 添加失败：{str(e)}")
            return ''
    
    def add_expense_record(self, data: Dict = None, rq: str = None, zc_code: str = None, 
                          je: float = None, zf_code: str = None, bz: str = '') -> bool:
        """添加支出记录
        
        Args:
            data: 字典格式的数据（兼容旧接口）
            rq: 日期
            zc_code: 支出类型编码
            je: 金额
            zf_code: 支付方式编码
            bz: 备注
        """
        if not self.is_connected():
            return False
        
        # 兼容两种调用方式
        if data is not None:
            rq = data.get('rq')
            zc_code = data.get('zc_code')
            je = data.get('je')
            zf_code = data.get('zf_code')
            bz = data.get('bz', '')
        
        try:
            new_djh = self._generate_document_number('sz_sheet_zc')
            
            self._backend.execute("""
                INSERT INTO sz_sheet_zc (zth, djh, rq, zc_code, je, zf_code, bz)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.current_account,
                new_djh,
                rq,
                zc_code,
                je,
                zf_code,
                bz
            ))
            logger.info(f"[支出管理] 添加记录成功：单据号={new_djh}")
            return True
        except Exception as e:
            logger.error(f"[支出管理] 添加失败：{str(e)}")
            return False
    
    def add_expense(self, rq: str, zc_code: str, je: float, zf_code: str, bz: str = '') -> str:
        """添加支出记录（便捷方法）"""
        if not self.is_connected():
            return ''
        
        try:
            new_djh = self._generate_document_number('sz_sheet_zc')
            
            self._backend.execute("""
                INSERT INTO sz_sheet_zc (zth, djh, rq, zc_code, je, zf_code, bz)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.current_account,
                new_djh,
                rq,
                zc_code,
                je,
                zf_code,
                bz
            ))
            logger.info(f"[支出管理] 添加记录成功：单据号={new_djh}")
            return new_djh
        except Exception as e:
            logger.error(f"[支出管理] 添加失败：{str(e)}")
            return ''
    
    def delete_income_record(self, djh: str) -> bool:
        """删除收入记录"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute("DELETE FROM sz_sheet_sr WHERE djh=?", (djh,))
            logger.info(f"[收入管理] 删除记录成功：单据号={djh}")
            return True
        except Exception as e:
            logger.error(f"[收入管理] 删除失败：{str(e)}")
            return False
    
    def delete_expense_record(self, djh: str) -> bool:
        """删除支出记录"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute("DELETE FROM sz_sheet_zc WHERE djh=?", (djh,))
            logger.info(f"[支出管理] 删除记录成功：单据号={djh}")
            return True
        except Exception as e:
            logger.error(f"[支出管理] 删除失败：{str(e)}")
            return False
    
    def update_income_payment(self, djh: str, zf_code: str) -> bool:
        """更新收入记录的支付方式"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_sheet_sr SET zf_code=? WHERE djh=? AND zth=?",
                (zf_code, djh, self.current_account)
            )
            logger.info(f"[收入管理] 更新支付方式成功：单据号={djh}, 新支付方式={zf_code}")
            return True
        except Exception as e:
            logger.error(f"[收入管理] 更新支付方式失败：{str(e)}")
            return False
    
    def update_income_type(self, djh: str, sr_code: str) -> bool:
        """更新收入记录的类型（注意：这是更新记录，不是更新码表）"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_sheet_sr SET sr_code=? WHERE djh=? AND zth=?",
                (sr_code, djh, self.current_account)
            )
            logger.info(f"[收入管理] 更新收入类型成功：单据号={djh}, 新类型={sr_code}")
            return True
        except Exception as e:
            logger.error(f"[收入管理] 更新收入类型失败：{str(e)}")
            return False
    
    def update_expense_payment(self, djh: str, zf_code: str) -> bool:
        """更新支出记录的支付方式"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_sheet_zc SET zf_code=? WHERE djh=? AND zth=?",
                (zf_code, djh, self.current_account)
            )
            logger.info(f"[支出管理] 更新支付方式成功：单据号={djh}, 新支付方式={zf_code}")
            return True
        except Exception as e:
            logger.error(f"[支出管理] 更新支付方式失败：{str(e)}")
            return False
    
    def update_expense_type(self, djh: str, zc_code: str) -> bool:
        """更新支出记录的类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_sheet_zc SET zc_code=? WHERE djh=? AND zth=?",
                (zc_code, djh, self.current_account)
            )
            logger.info(f"[支出管理] 更新支出类型成功：单据号={djh}, 新类型={zc_code}")
            return True
        except Exception as e:
            logger.error(f"[支出管理] 更新支出类型失败：{str(e)}")
            return False
    
    # ========== 分类管理 CRUD 方法 ==========
    
    def add_income_type(self, code: str, name: str) -> bool:
        """添加收入类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "INSERT INTO sz_c_sr (sr_code, sr_name) VALUES (?, ?)",
                (code, name)
            )
            logger.info(f"[分类管理] 添加收入类型成功：{code}-{name}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 添加收入类型失败：{str(e)}")
            return False
    
    def update_income_type(self, code: str, name: str) -> bool:
        """更新收入类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_c_sr SET sr_name=? WHERE sr_code=?",
                (name, code)
            )
            logger.info(f"[分类管理] 更新收入类型成功：{code}-{name}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 更新收入类型失败：{str(e)}")
            return False
    
    def delete_income_type(self, code: str) -> bool:
        """删除收入类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "DELETE FROM sz_c_sr WHERE sr_code=?",
                (code,)
            )
            logger.info(f"[分类管理] 删除收入类型成功：{code}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 删除收入类型失败：{str(e)}")
            return False
    
    def add_expense_type(self, code: str, name: str) -> bool:
        """添加支出类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "INSERT INTO sz_c_zc (zc_code, zc_name) VALUES (?, ?)",
                (code, name)
            )
            logger.info(f"[分类管理] 添加支出类型成功：{code}-{name}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 添加支出类型失败：{str(e)}")
            return False
    
    def update_expense_type(self, code: str, name: str) -> bool:
        """更新支出类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_c_zc SET zc_name=? WHERE zc_code=?",
                (name, code)
            )
            logger.info(f"[分类管理] 更新支出类型成功：{code}-{name}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 更新支出类型失败：{str(e)}")
            return False
    
    def delete_expense_type(self, code: str) -> bool:
        """删除支出类型"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "DELETE FROM sz_c_zc WHERE zc_code=?",
                (code,)
            )
            logger.info(f"[分类管理] 删除支出类型成功：{code}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 删除支出类型失败：{str(e)}")
            return False
    
    def add_payment_method(self, code: str, name: str) -> bool:
        """添加支付方式"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "INSERT INTO sz_c_zf (zf_code, zf_name) VALUES (?, ?)",
                (code, name)
            )
            logger.info(f"[分类管理] 添加支付方式成功：{code}-{name}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 添加支付方式失败：{str(e)}")
            return False
    
    def update_payment_method(self, code: str, name: str) -> bool:
        """更新支付方式"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_c_zf SET zf_name=? WHERE zf_code=?",
                (name, code)
            )
            logger.info(f"[分类管理] 更新支付方式成功：{code}-{name}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 更新支付方式失败：{str(e)}")
            return False
    
    def delete_payment_method(self, code: str) -> bool:
        """删除支付方式"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "DELETE FROM sz_c_zf WHERE zf_code=?",
                (code,)
            )
            logger.info(f"[分类管理] 删除支付方式成功：{code}")
            return True
        except Exception as e:
            logger.error(f"[分类管理] 删除支付方式失败：{str(e)}")
            return False
    
    # ========== 记录更新方法 ==========
    
    def update_income_record(self, djh: str, data: Dict) -> bool:
        """更新收入记录"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute("""
                UPDATE sz_sheet_sr 
                SET rq=?, sr_code=?, je=?, zf_code=?, bz=?
                WHERE djh=? AND zth=?
            """, (
                data['rq'],
                data['sr_code'],
                data['je'],
                data['zf_code'],
                data.get('bz', ''),
                djh,
                self.current_account
            ))
            logger.info(f"[收入管理] 更新记录成功：单据号={djh}")
            return True
        except Exception as e:
            logger.error(f"[收入管理] 更新失败：{str(e)}")
            return False
    
    def update_expense_record(self, djh: str, data: Dict) -> bool:
        """更新支出记录"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute("""
                UPDATE sz_sheet_zc 
                SET rq=?, zc_code=?, je=?, zf_code=?, bz=?
                WHERE djh=? AND zth=?
            """, (
                data['rq'],
                data['zc_code'],
                data['je'],
                data['zf_code'],
                data.get('bz', ''),
                djh,
                self.current_account
            ))
            logger.info(f"[支出管理] 更新记录成功：单据号={djh}")
            return True
        except Exception as e:
            logger.error(f"[支出管理] 更新失败：{str(e)}")
            return False
    
    def update_cash_flow_remark(self, xh: int, bz: str) -> bool:
        """更新流水账备注"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "UPDATE sz_table_lsz SET bz=? WHERE xh=? AND zth=?",
                (bz, xh, self.current_account)
            )
            logger.info(f"[流水账] 更新备注成功：序号={xh}")
            return True
        except Exception as e:
            logger.error(f"[流水账] 更新备注失败：{str(e)}")
            return False
    
    def delete_cash_flow_by_xh(self, xh: int) -> bool:
        """根据序号删除流水账记录"""
        if not self.is_connected():
            return False
        
        try:
            self._backend.execute(
                "DELETE FROM sz_table_lsz WHERE xh=? AND zth=?",
                (xh, self.current_account)
            )
            logger.info(f"[流水账] 删除记录成功：序号={xh}")
            return True
        except Exception as e:
            logger.error(f"[流水账] 删除记录失败：{str(e)}")
            return False
    
    def get_cash_flow_filtered(self, start_date: str = None, end_date: str = None, 
                                srzc: str = None, min_amount: float = None, 
                                max_amount: float = None) -> List[Tuple]:
        """条件查询流水账
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            srzc: 收支类型 ('SR'=收入, 'ZC'=支出, None=全部)
            min_amount: 最小金额
            max_amount: 最大金额
            
        Returns:
            符合条件的流水账记录列表
        """
        if not self.is_connected():
            return []
        
        sql = """
            SELECT rq, xh, srzc, djh, 
                   COALESCE(sr_code, '') as sr_code,
                   COALESCE(srje, 0) as srje,
                   COALESCE(zc_code, '') as zc_code,
                   COALESCE(zcje, 0) as zcje,
                   ye, zf_code, bz
            FROM sz_table_lsz
            WHERE zth = ?
        """
        params = [self.current_account]
        
        # 添加日期筛选
        if start_date:
            sql += " AND rq >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND rq <= ?"
            params.append(end_date)
        
        # 添加收支类型筛选
        if srzc:
            sql += " AND srzc = ?"
            params.append(srzc)
        
        # 添加金额筛选（需要同时检查收入和支出金额）
        if min_amount is not None:
            sql += " AND (srje >= ? OR zcje >= ?)"
            params.extend([min_amount, min_amount])
        if max_amount is not None:
            sql += " AND (srje <= ? OR zcje <= ?)"
            params.extend([max_amount, max_amount])
        
        sql += " ORDER BY rq, xh"
        
        self._backend.execute(sql, tuple(params))
        return self._backend.fetchall()
    
    def get_cash_flow(self, limit=None, offset=None) -> List[Tuple]:
        """获取流水账"""
        if not self.is_connected():
            return []

        sql = """
            SELECT rq, xh, srzc, djh,
                   COALESCE(sr_code, '') as sr_code,
                   COALESCE(srje, 0) as srje,
                   COALESCE(zc_code, '') as zc_code,
                   COALESCE(zcje, 0) as zcje,
                   ye, zf_code, bz
            FROM sz_table_lsz
            WHERE zth = ?
            ORDER BY rq, xh
        """
        params = [self.current_account]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)

        self._backend.execute(sql, tuple(params))
        return self._backend.fetchall()

    def get_income_avg_amount(self) -> float:
        """获取收入平均金额（快速AVG查询）"""
        if not self.is_connected():
            return 0.0
        self._backend.execute("SELECT AVG(je) FROM sz_sheet_sr WHERE zth=?", (self.current_account,))
        row = self._backend.fetchone()
        return float(row[0]) if row and row[0] else 0.0

    def get_expense_avg_amount(self) -> float:
        """获取支出平均金额（快速AVG查询）"""
        if not self.is_connected():
            return 0.0
        self._backend.execute("SELECT AVG(je) FROM sz_sheet_zc WHERE zth=?", (self.current_account,))
        row = self._backend.fetchone()
        return float(row[0]) if row and row[0] else 0.0

    def get_recent_flow(self, limit=10) -> List[Tuple]:
        """获取最近N条流水记录（快速查询）"""
        return self.get_cash_flow(limit=limit)
    
    def generate_cash_flow(self):
        """生成收支流水账"""
        if not self.is_connected():
            return
        
        try:
            # 清空旧流水账
            self._backend.execute("DELETE FROM sz_table_lsz WHERE zth=?", (self.current_account,))
            
            # 获取所有收入和支出数据
            self._backend.execute("""
                SELECT rq, 'SR' as srzc, djh, sr_code as code, je as srje, 0 as zcje, zf_code, bz
                FROM sz_sheet_sr WHERE zth = ?
                UNION ALL
                SELECT rq, 'ZC' as srzc, djh, zc_code as code, 0 as srje, je as zcje, zf_code, bz
                FROM sz_sheet_zc WHERE zth = ?
                ORDER BY rq, srzc DESC, djh
            """, (self.current_account, self.current_account))
            
            records = self._backend.fetchall()
            
            # 计算余额并插入流水账表
            current_balance = 0.0
            xh = 0
            
            for record in records:
                xh += 1
                rq, srzc, djh, code, srje, zcje, zf_code, bz = record
                
                if srzc == 'SR':
                    current_balance += srje
                else:
                    current_balance -= zcje
                
                self._backend.execute("""
                    INSERT INTO sz_table_lsz (zth, rq, xh, srzc, djh, sr_code, srje, zc_code, zcje, ye, zf_code, bz)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.current_account, rq, xh, srzc, djh, 
                      code if srzc == 'SR' else None, srje,
                      code if srzc == 'ZC' else None, zcje,
                      current_balance, zf_code, bz))
            
            logger.info("[流水账] 生成成功")
        except Exception as e:
            logger.error(f"[流水账] 生成失败：{str(e)}")
    
    def get_monthly_report(self, year_month: str) -> List[Tuple]:
        """获取月度报表"""
        if not self.is_connected():
            return []
        
        backend_type = self._backend.get_backend_type()
        
        if 'SQLite' in backend_type:
            sql = """
                SELECT 
                    qsrq, jsrq, zf_code, qcye, srje, zcje, qmye
                FROM sz_report_srzc
                WHERE zth = ? AND strftime('%Y-%m', qsrq) = ?
                ORDER BY qsrq, zf_code
            """
        else:
            # MySQL/Sybase 使用 DATE_FORMAT
            sql = """
                SELECT 
                    qsrq, jsrq, zf_code, qcye, srje, zcje, qmye
                FROM sz_report_srzc
                WHERE zth = ? AND DATE_FORMAT(qsrq, '%%Y-%%m') = ?
                ORDER BY qsrq, zf_code
            """
        
        self._backend.execute(sql, (self.current_account, year_month))
        return self._backend.fetchall()
    
    def generate_monthly_report(self, year_month: str):
        """生成月度报表"""
        if not self.is_connected():
            return
        
        try:
            # 计算起始和结束日期
            qsrq = f"{year_month}-01"
            if int(year_month.split('-')[1]) == 12:
                jsrq = f"{int(year_month.split('-')[0]) + 1}-01-01"
            else:
                jsrq = f"{year_month}-{int(year_month.split('-')[1]) + 1:02d}-01"
            
            # 清空旧报表
            backend_type = self._backend.get_backend_type()
            if 'SQLite' in backend_type:
                self._backend.execute(
                    "DELETE FROM sz_report_srzc WHERE zth=? AND strftime('%Y-%m', qsrq)=?",
                    (self.current_account, year_month)
                )
                
                # 生成新报表 - 计算期初余额
                sql = """
                    INSERT INTO sz_report_srzc (zth, qsrq, jsrq, zf_code, qcye, srje, zcje, qmye)
                    SELECT
                        ?, ?, ?, zf_code,
                        COALESCE(
                            (SELECT qmye FROM sz_report_srzc AS prev
                             WHERE prev.zth = sz_current.zth
                               AND prev.zf_code = sz_current.zf_code
                               AND prev.jsrq = ?),
                            0
                        ) as qcye,
                        SUM(CASE WHEN srzc='SR' THEN srje ELSE 0 END) as srje,
                        SUM(CASE WHEN srzc='ZC' THEN zcje ELSE 0 END) as zcje,
                        COALESCE(
                            (SELECT qmye FROM sz_report_srzc AS prev
                             WHERE prev.zth = sz_current.zth
                               AND prev.zf_code = sz_current.zf_code
                               AND prev.jsrq = ?),
                            0
                        ) + SUM(srje - zcje) as qmye
                    FROM sz_table_lsz AS sz_current
                    WHERE zth=? AND strftime('%Y-%m', rq)=?
                    GROUP BY zf_code
                """
                self._backend.execute(sql, (
                    self.current_account, qsrq, jsrq,
                    qsrq,  # prev.jsrq = current.qsrq (上月期末 = 本月期初)
                    qsrq,  # same for qmye calculation
                    self.current_account, year_month
                ))
            else:
                # MySQL/Sybase
                self._backend.execute(
                    "DELETE FROM sz_report_srzc WHERE zth=? AND DATE_FORMAT(qsrq, '%Y-%m')=?",
                    (self.current_account, year_month)
                )
                sql = """
                    INSERT INTO sz_report_srzc (zth, qsrq, jsrq, zf_code, qcye, srje, zcje, qmye)
                    SELECT
                        ?, ?, ?, zf_code,
                        COALESCE(
                            (SELECT qmye FROM sz_report_srzc AS prev
                             WHERE prev.zth = sz_current.zth
                               AND prev.zf_code = sz_current.zf_code
                               AND prev.jsrq = ?),
                            0
                        ) as qcye,
                        SUM(CASE WHEN srzc='SR' THEN srje ELSE 0 END) as srje,
                        SUM(CASE WHEN srzc='ZC' THEN zcje ELSE 0 END) as zcje,
                        COALESCE(
                            (SELECT qmye FROM sz_report_srzc AS prev
                             WHERE prev.zth = sz_current.zth
                               AND prev.zf_code = sz_current.zf_code
                               AND prev.jsrq = ?),
                            0
                        ) + SUM(srje - zcje) as qmye
                    FROM sz_table_lsz AS sz_current
                    WHERE zth=? AND DATE_FORMAT(rq, '%Y-%m')=?
                    GROUP BY zf_code
                """
                self._backend.execute(sql, (
                    self.current_account, qsrq, jsrq,
                    qsrq, qsrq,
                    self.current_account, year_month
                ))
            logger.info(f"[月报表] {year_month} 生成成功")
        except Exception as e:
            logger.error(f"[月报表] 生成失败：{str(e)}")
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        if not self.is_connected():
            return {}
        
        # 总收入
        self._backend.execute(
            "SELECT SUM(je) FROM sz_sheet_sr WHERE zth=?",
            (self.current_account,)
        )
        total_income = self._backend.fetchone()[0] or 0
        
        # 总支出
        self._backend.execute(
            "SELECT SUM(je) FROM sz_sheet_zc WHERE zth=?",
            (self.current_account,)
        )
        total_expense = self._backend.fetchone()[0] or 0
        
        # 净结余
        balance = total_income - total_expense
        
        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance
        }
    
    def get_tables(self) -> List[str]:
        """获取数据库中所有表名列表"""
        if not self.is_connected():
            return []
        
        try:
            backend_type = self._backend.get_backend_type()
            
            if 'SQLite' in backend_type:
                self._backend.execute("SELECT name FROM sqlite_master WHERE type='table'")
            elif 'MySQL' in backend_type:
                self._backend.execute("SHOW TABLES")
            elif 'Sybase' in backend_type:
                self._backend.execute("""
                    SELECT table_name 
                    FROM systable 
                    WHERE table_type = 'BASE'
                    ORDER BY table_name
                """)
            else:
                return []
            
            tables = self._backend.fetchall()
            return [t[0] for t in tables]
        except Exception as e:
            logger.error(f"[数据库] 获取表列表失败: {str(e)}")
            return []
    
    def get_record_count(self, table_name: str) -> int:
        """获取指定表的记录数"""
        if not self.is_connected():
            return 0
        
        try:
            sql = f"SELECT COUNT(*) FROM {table_name}"
            self._backend.execute(sql)
            result = self._backend.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"[数据库] 获取表 {table_name} 记录数失败: {str(e)}")
            return 0
    
    def global_search(self, keyword: str, search_types: List[str] = None, all_accounts: bool = False) -> Dict[str, List[Dict]]:
        """全局搜索功能

        Args:
            keyword: 搜索关键字
            search_types: 搜索类型 ['income','expense','category','payment']
            all_accounts: True=搜索全部账套，False=仅当前账套
        """
        if not self.is_connected() or not keyword:
            return {}

        if search_types is None:
            search_types = ['income', 'expense', 'category', 'payment']

        results = {}
        like_pattern = f"%{keyword}%"
        zth_filter = "" if all_accounts else " AND s.zth = ?"
        extra_col = ", s.zth" if all_accounts else ""

        try:
            # 1. 搜索收入记录
            if 'income' in search_types:
                sql = f"""
                    SELECT s.djh, s.rq, c.sr_name as type_name, s.je, z.zf_name as payment_name, s.bz{extra_col}
                    FROM sz_sheet_sr s
                    LEFT JOIN sz_c_sr c ON s.sr_code = c.sr_code
                    LEFT JOIN sz_c_zf z ON s.zf_code = z.zf_code
                    WHERE 1=1{zth_filter} AND (
                        s.djh LIKE ? OR s.rq LIKE ? OR c.sr_name LIKE ?
                        OR CAST(s.je AS TEXT) LIKE ? OR z.zf_name LIKE ? OR s.bz LIKE ?
                    )
                    ORDER BY s.rq DESC LIMIT 50
                """
                params = [self.current_account] if not all_accounts else []
                params += [like_pattern] * 6
                self._backend.execute(sql, tuple(params))
                rows = self._backend.fetchall()
                results['income'] = [
                    {'djh': r[0], 'rq': r[1], 'type_name': r[2], 'je': r[3],
                     'payment_name': r[4], 'bz': r[5],
                     'zth': r[6] if all_accounts and len(r) > 6 else self.current_account}
                    for r in rows
                ]

            # 2. 搜索支出记录
            if 'expense' in search_types:
                sql = f"""
                    SELECT s.djh, s.rq, c.zc_name as type_name, s.je, z.zf_name as payment_name, s.bz{extra_col}
                    FROM sz_sheet_zc s
                    LEFT JOIN sz_c_zc c ON s.zc_code = c.zc_code
                    LEFT JOIN sz_c_zf z ON s.zf_code = z.zf_code
                    WHERE 1=1{zth_filter} AND (
                        s.djh LIKE ? OR s.rq LIKE ? OR c.zc_name LIKE ?
                        OR CAST(s.je AS TEXT) LIKE ? OR z.zf_name LIKE ? OR s.bz LIKE ?
                    )
                    ORDER BY s.rq DESC LIMIT 50
                """
                params = [self.current_account] if not all_accounts else []
                params += [like_pattern] * 6
                self._backend.execute(sql, tuple(params))
                rows = self._backend.fetchall()
                results['expense'] = [
                    {'djh': r[0], 'rq': r[1], 'type_name': r[2], 'je': r[3],
                     'payment_name': r[4], 'bz': r[5],
                     'zth': r[6] if all_accounts and len(r) > 6 else self.current_account}
                    for r in rows
                ]
            
            # 3. 搜索分类名称
            if 'category' in search_types:
                categories = []
                
                # 搜索收入分类
                self._backend.execute(
                    "SELECT sr_code, sr_name FROM sz_c_sr WHERE sr_name LIKE ?",
                    (like_pattern,)
                )
                for row in self._backend.fetchall():
                    categories.append({
                        'code': row[0],
                        'name': row[1],
                        'type': '收入'
                    })
                
                # 搜索支出分类
                self._backend.execute(
                    "SELECT zc_code, zc_name FROM sz_c_zc WHERE zc_name LIKE ?",
                    (like_pattern,)
                )
                for row in self._backend.fetchall():
                    categories.append({
                        'code': row[0],
                        'name': row[1],
                        'type': '支出'
                    })
                
                results['category'] = categories
            
            # 4. 搜索支付方式
            if 'payment' in search_types:
                self._backend.execute(
                    "SELECT zf_code, zf_name FROM sz_c_zf WHERE zf_name LIKE ?",
                    (like_pattern,)
                )
                rows = self._backend.fetchall()
                results['payment'] = [
                    {'code': row[0], 'name': row[1]}
                    for row in rows
                ]
            
            log_manager.info(f"全局搜索完成: 关键字='{keyword}', 结果数={sum(len(v) for v in results.values())}")
            return results
            
        except Exception as e:
            log_manager.error(f"全局搜索失败: {str(e)}", exc_info=True)
            return {}


# 全局数据管理器实例
db_manager = EnhancedDataManager()
