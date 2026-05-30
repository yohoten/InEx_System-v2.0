# -*- coding: utf-8 -*-
"""
数据库连接测试对话框
提供图形化的数据库连接测试功能，支持 SQLite / MySQL / Sybase
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QTextEdit,
                             QGroupBox, QFormLayout, QMessageBox, QFileDialog,
                             QSplitter, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor

import sys
import os

from ui.styles import UIStyles


class DatabaseConnectionDialog(QDialog):
    """数据库连接测试对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据库连接测试")
        self.setFixedSize(900, 650)
        self.setModal(True)
        
        # 初始化 UI
        self.initUI()
        
        # 加载默认配置
        self.load_default_config()
    
    def initUI(self):
        """初始化 UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== 左侧：连接配置区域 ==========
        config_group = QGroupBox("数据库连接配置")
        config_group.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        config_layout = QFormLayout()
        config_layout.setSpacing(10)
        config_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 数据库类型选择
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["SQLite", "MySQL 8.0", "Sybase SQL Anywhere 9"])
        self.db_type_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.db_type_combo.currentIndexChanged.connect(self.on_db_type_changed)
        config_layout.addRow("数据库类型:", self.db_type_combo)
        
        # ===== SQLite 专属配置 =====
        self.sqlite_group = QWidget()
        sqlite_layout = QFormLayout()
        sqlite_layout.setContentsMargins(0, 0, 0, 0)
        
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setPlaceholderText("选择 SQLite 数据库文件路径")
        self.db_path_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_sqlite_file)
        
        sqlite_path_layout = QHBoxLayout()
        sqlite_path_layout.addWidget(self.db_path_edit)
        sqlite_path_layout.addWidget(browse_btn)
        sqlite_layout.addRow("数据库文件:", sqlite_path_layout)
        
        self.sqlite_group.setLayout(sqlite_layout)
        config_layout.addRow("", self.sqlite_group)
        
        # ===== MySQL 专属配置 =====
        self.mysql_group = QWidget()
        mysql_layout = QFormLayout()
        mysql_layout.setContentsMargins(0, 0, 0, 0)
        
        self.host_edit = QLineEdit("localhost")
        self.host_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        mysql_layout.addRow("主机地址:", self.host_edit)
        
        self.port_edit = QLineEdit("3306")
        self.port_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        mysql_layout.addRow("端口号:", self.port_edit)
        
        self.user_edit = QLineEdit("root")
        self.user_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        mysql_layout.addRow("用户名:", self.user_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        mysql_layout.addRow("密码:", self.password_edit)
        
        self.database_edit = QLineEdit("inex_db")
        self.database_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        mysql_layout.addRow("数据库名:", self.database_edit)
        
        self.mysql_group.setLayout(mysql_layout)
        self.mysql_group.setVisible(False)
        config_layout.addRow("", self.mysql_group)
        
        # ===== Sybase 专属配置 =====
        self.sybase_group = QWidget()
        sybase_layout = QFormLayout()
        sybase_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sybase_dsn_input = QLineEdit()
        self.sybase_dsn_input.setPlaceholderText("ODBC DSN 名称")
        self.sybase_dsn_input.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        sybase_layout.addRow("DSN 名称:", self.sybase_dsn_input)
        
        self.sybase_uid_input = QLineEdit("dba")
        self.sybase_uid_input.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        sybase_layout.addRow("用户 ID:", self.sybase_uid_input)
        
        self.sybase_pwd_input = QLineEdit("sql")
        self.sybase_pwd_input.setEchoMode(QLineEdit.Password)
        self.sybase_pwd_input.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        sybase_layout.addRow("密码:", self.sybase_pwd_input)
        
        self.sybase_dbn_input = QLineEdit("demo")
        self.sybase_dbn_input.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        sybase_layout.addRow("数据库名:", self.sybase_dbn_input)
        
        self.sybase_group.setLayout(sybase_layout)
        self.sybase_group.setVisible(False)
        config_layout.addRow("", self.sybase_group)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # ========== 右侧：测试按钮和日志区域 ==========
        splitter = QSplitter(Qt.Vertical)
        
        # 操作按钮区域
        btn_widget = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.test_btn = QPushButton("🔍 测试连接")
        self.test_btn.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        self.test_btn.setStyleSheet(UIStyles.primary_button(font_size=11, font_weight="bold"))
        self.test_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.test_btn)

        self.connect_btn = QPushButton("✅ 连接数据库")
        self.connect_btn.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        self.connect_btn.setStyleSheet(UIStyles.success_button(font_size=11, font_weight="bold"))
        self.connect_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.connect_btn)
        
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.save_btn.setStyleSheet(UIStyles.primary_button())
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)
        
        btn_layout.addStretch()
        
        self.clear_log_btn = QPushButton("🗑️ 清空日志")
        self.clear_log_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.clear_log_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.clear_log_btn)
        
        btn_widget.setLayout(btn_layout)
        splitter.addWidget(btn_widget)
        
        # 日志输出区域
        log_group = QGroupBox("连接测试日志")
        log_group.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        splitter.addWidget(log_group)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        
        main_layout.addWidget(splitter)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(close_btn)
        
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
    
    def on_db_type_changed(self, index):
        """数据库类型切换"""
        db_type = self.db_type_combo.currentText()
        
        # 隐藏所有配置组
        self.sqlite_group.setVisible(False)
        self.mysql_group.setVisible(False)
        self.sybase_group.setVisible(False)
        
        # 显示对应的配置组
        if db_type == "SQLite":
            self.sqlite_group.setVisible(True)
        elif db_type == "MySQL 8.0":
            self.mysql_group.setVisible(True)
        elif db_type == "Sybase SQL Anywhere 9":
            self.sybase_group.setVisible(True)
    
    def browse_sqlite_file(self):
        """浏览 SQLite 数据库文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 SQLite 数据库文件",
            "",
            "SQLite 数据库 (*.db *.sqlite);;所有文件 (*)"
        )
        if file_path:
            self.db_path_edit.setText(file_path)
    
    def test_connection(self):
        """测试数据库连接"""
        db_type = self.db_type_combo.currentText()
        self.append_log(f"\n{'='*60}")
        self.append_log(f"开始测试 {db_type} 连接...")
        self.append_log(f"{'='*60}\n")
        
        try:
            if db_type == "SQLite":
                self._test_sqlite()
            elif db_type == "MySQL 8.0":
                self._test_mysql()
            elif db_type == "Sybase SQL Anywhere 9":
                self._test_sybase()
        
        except Exception as e:
            self.append_log(f"❌ 连接失败: {str(e)}", "red")
            QMessageBox.critical(self, "连接失败", f"数据库连接失败:\n{str(e)}")
    
    def _test_sqlite(self):
        """测试 SQLite 连接"""
        db_path = self.db_path_edit.text().strip()
        
        if not db_path:
            self.append_log("⚠️ 错误: 未指定数据库文件路径", "yellow")
            return
        
        if not os.path.exists(db_path):
            self.append_log(f"⚠️ 错误: 文件不存在 - {db_path}", "yellow")
            return
        
        self.append_log(f"📁 数据库路径: {db_path}")
        
        # 尝试连接
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 执行测试查询
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
            tables = cursor.fetchall()
            
            self.append_log(f"✅ 连接成功!", "green")
            self.append_log(f"📊 发现 {len(tables)} 个表:")
            for table in tables:
                self.append_log(f"   - {table[0]}")
            
            # 获取数据库大小
            file_size = os.path.getsize(db_path)
            self.append_log(f"💾 数据库大小: {file_size / 1024:.2f} KB")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.append_log(f"❌ 连接失败: {str(e)}", "red")
            raise
    
    def _test_mysql(self):
        """测试 MySQL 连接"""
        host = self.host_edit.text().strip()
        port = self.port_edit.text().strip()
        user = self.user_edit.text().strip()
        password = self.password_edit.text()
        database = self.database_edit.text().strip()
        
        self.append_log(f"🌐 主机: {host}:{port}")
        self.append_log(f"👤 用户: {user}")
        self.append_log(f"📂 数据库: {database}")
        
        try:
            import pymysql
            
            conn = pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            self.append_log(f"✅ 连接成功!", "green")
            self.append_log(f"📊 MySQL 版本: {version}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            self.append_log(f"📋 发现 {len(tables)} 个表")
            
            cursor.close()
            conn.close()
            
        except ImportError:
            self.append_log("❌ 错误: 未安装 pymysql 库", "red")
            self.append_log("💡 请运行: pip install pymysql", "yellow")
            raise
        except Exception as e:
            self.append_log(f"❌ 连接失败: {str(e)}", "red")
            raise
    
    def _test_sybase(self):
        """测试 Sybase SQL Anywhere 连接"""
        dsn = self.sybase_dsn_input.text().strip()
        uid = self.sybase_uid_input.text().strip()
        pwd = self.sybase_pwd_input.text()
        dbn = self.sybase_dbn_input.text().strip()
        
        self.append_log(f"🔗 DSN: {dsn}")
        self.append_log(f"👤 用户: {uid}")
        self.append_log(f"📂 数据库: {dbn}")
        
        # 方法 1: 使用 sqlanydb（推荐）
        try:
            import sqlanydb
            
            self.append_log("📦 使用 sqlanydb 驱动...")
            
            conn = sqlanydb.connect(
                uid=uid,
                pwd=pwd,
                eng=dbn,
                dbn=dbn
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            
            self.append_log(f"✅ 连接成功!", "green")
            self.append_log(f"📊 SQL Anywhere 版本: {version}")
            
            cursor.close()
            conn.close()
            return
            
        except ImportError:
            self.append_log("⚠️ sqlanydb 未安装，尝试 ODBC...", "yellow")
        except Exception as e:
            self.append_log(f"⚠️ sqlanydb 连接失败: {str(e)}", "yellow")
        
        # 方法 2: 使用 pyodbc
        try:
            import pyodbc
            
            self.append_log("📦 使用 pyodbc 驱动...")
            
            conn_str = f"Driver={{Adaptive Server Anywhere 9.0}};DSN={dsn};UID={uid};PWD={pwd};DBN={dbn};"
            conn = pyodbc.connect(conn_str)
            
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            
            self.append_log(f"✅ 连接成功!", "green")
            self.append_log(f"📊 SQL Anywhere 版本: {version}")
            
            cursor.close()
            conn.close()
            
        except ImportError:
            self.append_log("❌ 错误: 未安装 pyodbc 库", "red")
            self.append_log("💡 请运行: pip install pyodbc", "yellow")
            raise
        except Exception as e:
            self.append_log(f"❌ ODBC 连接失败: {str(e)}", "red")
            self.append_log("💡 请确保已安装 SQL Anywhere ODBC 驱动", "yellow")
            raise
    
    def save_config(self):
        """保存配置到 config.json"""
        from models.config import config
        
        db_type = self.db_type_combo.currentText()
        
        db_config = {
            'type': db_type,
            'sqlite': {
                'path': self.db_path_edit.text()
            },
            'mysql': {
                'host': self.host_edit.text(),
                'port': int(self.port_edit.text()),
                'user': self.user_edit.text(),
                'password': self.password_edit.text(),
                'database': self.database_edit.text()
            },
            'sybase': {
                'dsn': self.sybase_dsn_input.text(),
                'uid': self.sybase_uid_input.text(),
                'pwd': self.sybase_pwd_input.text(),
                'dbn': self.sybase_dbn_input.text()
            }
        }
        
        config.set('database', db_config)
        config.save()
        
        self.append_log("\n✅ 配置已保存到 config.json", "green")
        QMessageBox.information(self, "成功", "数据库配置已保存！")
    
    def load_default_config(self):
        """加载默认配置"""
        from models.config import config
        
        db_config = config.get_database_config()
        
        if db_config:
            db_type = db_config.get('type', 'SQLite')
            
            # 设置数据库类型
            index = self.db_type_combo.findText(db_type)
            if index >= 0:
                self.db_type_combo.setCurrentIndex(index)
            
            # 加载 SQLite 配置
            sqlite_config = db_config.get('sqlite', {})
            if sqlite_config.get('path'):
                self.db_path_edit.setText(sqlite_config['path'])
            
            # 加载 MySQL 配置
            mysql_config = db_config.get('mysql', {})
            if mysql_config:
                self.host_edit.setText(mysql_config.get('host', 'localhost'))
                self.port_edit.setText(str(mysql_config.get('port', 3306)))
                self.user_edit.setText(mysql_config.get('user', 'root'))
                self.password_edit.setText(mysql_config.get('password', ''))
                self.database_edit.setText(mysql_config.get('database', 'inex_db'))
            
            # 加载 Sybase 配置
            sybase_config = db_config.get('sybase', {})
            if sybase_config:
                self.sybase_dsn_input.setText(sybase_config.get('dsn', ''))
                self.sybase_uid_input.setText(sybase_config.get('uid', 'dba'))
                self.sybase_pwd_input.setText(sybase_config.get('pwd', 'sql'))
                self.sybase_dbn_input.setText(sybase_config.get('dbn', 'demo'))
    
    def append_log(self, message, color=None):
        """添加日志"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if color:
            color_map = {
                'green': '#2ECC71',
                'red': '#E74C3C',
                'yellow': '#F39C12'
            }
            html = f'<span style="color: {color_map.get(color, "#D4D4D4")}">{message}</span><br>'
            cursor.insertHtml(html)
        else:
            cursor.insertText(message + '\n')
        
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()