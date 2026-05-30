# -*- coding: utf-8 -*-
"""
数据库配置区域组件
负责数据库类型选择、连接参数配置、连接测试等功能
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QLineEdit, QPushButton, QRadioButton,
                             QButtonGroup, QMessageBox, QFileDialog, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.styles import UIStyles


class DatabaseConfigSection(QWidget):
    """数据库配置区域组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent  # 引用父页面，用于访问log_text等
        
        # UI组件
        self.db_type_group = None
        self.sqlite_radio = None
        self.mysql_radio = None
        self.sybase_radio = None
        self.db_path_input = None
        self.host_input = None
        self.port_input = None
        self.user_input = None
        self.pwd_input = None
        self.dbname_input = None
        self.advanced_widget = None
        self.test_conn_btn = None
        
        self.initUI()
    
    def initUI(self):
        """初始化数据库配置区域UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 数据库配置分组
        db_group = QGroupBox("🗄️ 数据库配置")
        db_group.setStyleSheet(UIStyles.group_box_style())
        db_layout = QVBoxLayout()
        
        # 数据库类型 - 使用单选按钮
        type_label = QLabel("数据库类型:")
        db_layout.addWidget(type_label)
        
        # 创建单选按钮组
        self.db_type_group = QButtonGroup(self)
        self.db_type_group.setExclusive(True)
        
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(20)
        
        # SQLite 单选按钮
        self.sqlite_radio = QRadioButton("SQLite")
        self.sqlite_radio.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.sqlite_radio.setChecked(True)
        self.sqlite_radio.toggled.connect(lambda: self.on_db_type_changed("SQLite"))
        radio_layout.addWidget(self.sqlite_radio)
        self.db_type_group.addButton(self.sqlite_radio, 0)
        
        # MySQL 单选按钮
        self.mysql_radio = QRadioButton("MySQL")
        self.mysql_radio.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.mysql_radio.toggled.connect(lambda: self.on_db_type_changed("MySQL"))
        radio_layout.addWidget(self.mysql_radio)
        self.db_type_group.addButton(self.mysql_radio, 1)
        
        # Sybase 单选按钮
        self.sybase_radio = QRadioButton("Sybase Anywhere 9")
        self.sybase_radio.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.sybase_radio.toggled.connect(lambda: self.on_db_type_changed("Sybase Anywhere 9"))
        radio_layout.addWidget(self.sybase_radio)
        self.db_type_group.addButton(self.sybase_radio, 2)
        
        radio_layout.addStretch()
        db_layout.addLayout(radio_layout)
        
        # SQLite 路径
        self.sqlite_path_layout = QHBoxLayout()
        self.sqlite_path_layout.addWidget(QLabel("数据库路径:"))
        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText("inex.db")
        self.sqlite_path_layout.addWidget(self.db_path_input)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_database)
        self.sqlite_path_layout.addWidget(self.browse_btn)
        db_layout.addLayout(self.sqlite_path_layout)
        
        # MySQL/Sybase 连接参数（隐藏）
        self.advanced_layout = QVBoxLayout()
        
        advanced_frame = QFrame()
        advanced_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        advanced_inner = QVBoxLayout()
        
        # 主机
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("主机:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        host_layout.addWidget(self.host_input)
        advanced_inner.addLayout(host_layout)
        
        # 端口
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("端口:"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("3306")
        port_layout.addWidget(self.port_input)
        advanced_inner.addLayout(port_layout)
        
        # 用户名
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("用户名:"))
        self.user_input = QLineEdit()
        user_layout.addWidget(self.user_input)
        advanced_inner.addLayout(user_layout)
        
        # 密码
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(QLabel("密码:"))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        pwd_layout.addWidget(self.pwd_input)
        advanced_inner.addLayout(pwd_layout)
        
        # 数据库名
        dbname_layout = QHBoxLayout()
        dbname_layout.addWidget(QLabel("数据库名:"))
        self.dbname_input = QLineEdit()
        dbname_layout.addWidget(self.dbname_input)
        advanced_inner.addLayout(dbname_layout)
        
        advanced_frame.setLayout(advanced_inner)
        self.advanced_layout.addWidget(advanced_frame)
        self.advanced_widget = QWidget()
        self.advanced_widget.setLayout(self.advanced_layout)
        self.advanced_widget.setVisible(False)
        db_layout.addWidget(self.advanced_widget)
        
        # 测试连接按钮区域
        test_layout = QHBoxLayout()
        
        self.test_conn_btn = QPushButton("🔌 测试连接")
        self.test_conn_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_conn_btn)
        
        self.open_test_dialog_btn = QPushButton("🗄️ 数据库管理")
        self.open_test_dialog_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        self.open_test_dialog_btn.clicked.connect(self.open_db_manager)
        test_layout.addWidget(self.open_test_dialog_btn)
        
        self.sybase_help_btn = QPushButton("❓ Sybase帮助")
        self.sybase_help_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.sybase_help_btn.clicked.connect(self.show_sybase_help)
        test_layout.addWidget(self.sybase_help_btn)
        
        self.check_driver_btn = QPushButton("🔍 检测驱动")
        self.check_driver_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        self.check_driver_btn.clicked.connect(self.check_sybase_drivers)
        test_layout.addWidget(self.check_driver_btn)
        
        test_layout.addStretch()
        db_layout.addLayout(test_layout)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        self.setLayout(layout)
    
    def on_db_type_changed(self, db_type):
        """数据库类型切换"""
        if hasattr(self.parent_page, 'log_text'):
            self.parent_page.log_text.append(f"[INFO] 切换数据库类型：{db_type}")
        
        if db_type == "SQLite":
            self.sqlite_path_layout.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.advanced_widget.setVisible(False)
        else:
            self.sqlite_path_layout.setEnabled(False)
            self.browse_btn.setEnabled(False)
            self.advanced_widget.setVisible(True)
            
            # 如果是 Sybase，检测可用驱动
            if db_type == "Sybase Anywhere 9":
                self.check_sybase_drivers()
    
    def browse_database(self):
        """浏览数据库文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据库文件",
            "",
            "SQLite Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.db_path_input.setText(file_path)
            if hasattr(self.parent_page, 'log_text'):
                self.parent_page.log_text.append(f"[INFO] 选择数据库：{file_path}")
    
    def test_connection(self):
        """测试数据库连接 - 委托给父页面处理"""
        if hasattr(self.parent_page, 'test_connection'):
            self.parent_page.test_connection()
    
    def open_db_manager(self):
        """打开数据库集成管理对话框"""
        if hasattr(self.parent_page, 'open_db_test_dialog'):
            self.parent_page.open_db_test_dialog()
    
    def show_sybase_help(self):
        """显示 Sybase 连接帮助"""
        if hasattr(self.parent_page, 'show_sybase_help'):
            self.parent_page.show_sybase_help()
    
    def check_sybase_drivers(self):
        """检测 Sybase SQL Anywhere 9 可用驱动"""
        if hasattr(self.parent_page, 'check_sybase_drivers'):
            self.parent_page.check_sybase_drivers()
    
    def get_db_type(self):
        """获取当前选择的数据库类型"""
        if self.sqlite_radio.isChecked():
            return 'sqlite'
        elif self.mysql_radio.isChecked():
            return 'mysql'
        elif self.sybase_radio.isChecked():
            return 'sybase'
        return 'sqlite'
    
    def set_db_type(self, db_type):
        """设置数据库类型"""
        if db_type == 'sqlite':
            self.sqlite_radio.setChecked(True)
        elif db_type == 'mysql':
            self.mysql_radio.setChecked(True)
        elif db_type == 'sybase':
            self.sybase_radio.setChecked(True)
    
    def get_config(self):
        """获取当前配置"""
        config = {
            'type': self.get_db_type(),
            'path': self.db_path_input.text(),
            'host': self.host_input.text(),
            'port': self.port_input.text(),
            'user': self.user_input.text(),
            'password': self.pwd_input.text(),
            'database': self.dbname_input.text()
        }
        return config
    
    def load_config(self, config_data):
        """加载配置"""
        # 数据库类型
        db_type = config_data.get('type', 'sqlite')
        self.set_db_type(db_type)
        
        # 路径和参数
        self.db_path_input.setText(config_data.get('path', 'inex.db'))
        self.host_input.setText(config_data.get('host', 'localhost'))
        self.port_input.setText(str(config_data.get('port', '3306')))
        self.user_input.setText(config_data.get('user', ''))
        self.dbname_input.setText(config_data.get('database', ''))
