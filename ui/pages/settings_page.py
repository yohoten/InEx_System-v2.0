# -*- coding: utf-8 -*-
"""
系统设置页面：管理数据库配置、自动备份、日志级别等系统参数
采用模块化架构，使用Section组件提高可维护性
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QApplication,
                             QGroupBox, QLineEdit, QRadioButton, QButtonGroup,
                             QCheckBox, QSpinBox, QComboBox, QTextEdit,
                             QDoubleSpinBox, QFrame, QFileDialog, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime


from models.config import config
from ui.styles import UIStyles
from ui.pages.settings_features import SettingsFeaturesMixin
from ui.pages.settings_sections import (
    DatabaseConfigSection,
    BackupManagementSection,
    LogConfigurationSection,
    AIAssistantSection
)
from utils.ai_assistant import AISuggestionsWorker
from utils.logger import log_manager


class SettingsPage(SettingsFeaturesMixin, QWidget):
    """系统设置页面 - 模块化版本"""
    
    def __init__(self):
        super().__init__()
        
        # 创建Section组件
        self.db_section = DatabaseConfigSection(parent=self)
        self.backup_section = BackupManagementSection(parent=self)
        self.log_section = LogConfigurationSection(parent=self)
        self.ai_section = AIAssistantSection(parent=self)
        
        self.initUI()
        self.load_settings()
        
        # 检查必要的依赖模块
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查必要的依赖模块是否已安装"""
        missing_modules = []
        
        # 检查数据库驱动
        try:
            import pymysql
        except ImportError:
            missing_modules.append("pymysql (MySQL支持)")
        
        try:
            import pyodbc
        except ImportError:
            missing_modules.append("pyodbc (Sybase/ODBC支持)")
        
        try:
            import sqlanydb
        except ImportError:
            missing_modules.append("sqlanydb (Sybase原生支持)")
        
        # 如果有缺失的模块,记录警告
        if missing_modules:
            print(f"[系统设置] ⚠️ 以下可选模块未安装: {', '.join(missing_modules)}")
            print("[系统设置] 如需使用相应数据库,请运行: pip install " + " ".join([m.split()[0] for m in missing_modules]))
    
    def load_settings(self):
        """从配置文件加载设置并更新UI"""
        try:
            # 加载数据库配置
            db_config = config.get_database_config()
            
            # 设置数据库类型（单选按钮）
            db_type = db_config.get('type', 'sqlite')
            if hasattr(self, 'db_section'):
                if db_type == 'sqlite':
                    self.db_section.sqlite_radio.setChecked(True)
                elif db_type == 'mysql':
                    self.db_section.mysql_radio.setChecked(True)
                elif db_type == 'sybase':
                    self.db_section.sybase_radio.setChecked(True)
                
                # 设置SQLite路径
                db_path = db_config.get('path', 'data/inex.db')
                self.db_section.db_path_input.setText(db_path)
                
                # 设置MySQL/Sybase连接参数
                self.db_section.host_input.setText(db_config.get('host', 'localhost'))
                self.db_section.port_input.setText(str(db_config.get('port', 3306)))
                self.db_section.user_input.setText(db_config.get('user', ''))
                self.db_section.pwd_input.setText(db_config.get('password', ''))
                self.db_section.dbname_input.setText(db_config.get('database', ''))
                
                # 根据数据库类型显示/隐藏高级参数
                if db_type == 'sqlite':
                    self.db_section.advanced_widget.setVisible(False)
                else:
                    self.db_section.advanced_widget.setVisible(True)
            
            # 加载备份配置
            if hasattr(self, 'backup_section'):
                auto_backup = db_config.get('auto_backup', True)
                self.backup_section.auto_backup_check.setChecked(auto_backup)
                
                backup_interval = db_config.get('backup_interval', 7)
                self.backup_section.backup_interval_spin.setValue(backup_interval)
                
                backup_path = db_config.get('backup_path', './backup/')
                self.backup_section.backup_path_input.setText(backup_path)
            
            # 加载日志配置
            if hasattr(self, 'log_section'):
                log_level = config.get_log_setting('level', 'INFO')
                if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                    index = self.log_section.log_level_combo.findText(log_level)
                    if index >= 0:
                        self.log_section.log_level_combo.setCurrentIndex(index)
            
            # 加载AI配置
            if hasattr(self, 'ai_section'):
                ai_config = config.get('ai', {})
                if ai_config:
                    api_key = ai_config.get('api_key_encrypted', '')
                    if api_key:
                        self.ai_section.api_key_input.setText(api_key)
                    
                    model = ai_config.get('model', 'deepseek-chat')
                    model_index = self.ai_section.model_combo.findText(model)
                    if model_index >= 0:
                        self.ai_section.model_combo.setCurrentIndex(model_index)
                    
                    temperature = ai_config.get('temperaturef', 0.7)
                    self.ai_section.temp_spin.setValue(temperature)
            
            print("[系统设置] 设置加载成功")
            
        except Exception as e:
            print(f"[系统设置] 加载设置失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    
    def initUI(self):
        """初始化 UI — 带滚动区域"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {UIStyles.BG_GRAY_50}; }}
        """)

        main_container = QWidget()
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 标题
        title_label = QLabel("⚙️ 系统设置")
        title_label.setStyleSheet(f"font-family: '{UIStyles.FONT_FAMILY}f'; font-size: {UIStyles.FONT_SIZE_TITLE}px; font-weight: bold; color: {UIStyles.TEXT_PRIMARY}; padding-bottom: 4px;")
        layout.addWidget(title_label)

        # 数据库配置区域 — 全宽
        layout.addWidget(self.db_section)

        # 三栏布局：备份、日志、AI助手
        three_column_layout = QHBoxLayout()
        three_column_layout.setSpacing(16)
        three_column_layout.addWidget(self.backup_section, 1)
        three_column_layout.addWidget(self.log_section, 1)
        three_column_layout.addWidget(self.ai_section, 1)
        layout.addLayout(three_column_layout)

        # 底部操作按钮区域
        bottom_btn_layout = self._create_bottom_buttons()
        layout.addLayout(bottom_btn_layout)

        scroll_area.setWidget(main_container)

        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)
    
    def _create_bottom_buttons(self):
        """创建底部操作按钮区域"""
        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.setSpacing(10)

        # 导入设置按钮
        import_btn = QPushButton("📥 导入设置")
        import_btn.setMinimumHeight(42)
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet(UIStyles.secondary_button(UIStyles.FONT_SIZE_MEDIUM))
        import_btn.clicked.connect(self.import_settings)
        bottom_btn_layout.addWidget(import_btn)

        # 导出设置按钮
        export_btn = QPushButton("📤 导出设置")
        export_btn.setMinimumHeight(42)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(UIStyles.default_button(UIStyles.FONT_SIZE_MEDIUM))
        export_btn.clicked.connect(self.export_settings)
        bottom_btn_layout.addWidget(export_btn)

        bottom_btn_layout.addStretch()

        # 保存所有设置按钮
        save_btn = QPushButton("✅ 保存所有设置")
        save_btn.setMinimumHeight(42)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(UIStyles.primary_button(UIStyles.FONT_SIZE_LARGE))
        save_btn.clicked.connect(self.save_all_settings)
        bottom_btn_layout.addWidget(save_btn)

        return bottom_btn_layout

    def on_db_type_changed(self, db_type):
        """数据库类型切换"""
        print(f"[系统设置] 切换数据库类型：{db_type}")
        
        if db_type == "SQLite":
            self.db_section.sqlite_path_layout.setEnabled(True)
            self.db_section.browse_btn.setEnabled(True)
            self.db_section.advanced_widget.setVisible(False)
        else:
            self.db_section.sqlite_path_layout.setEnabled(False)
            self.db_section.browse_btn.setEnabled(False)
            self.db_section.advanced_widget.setVisible(True)
            
            # 如果是 Sybase，检测可用驱动
            if db_type == "Sybase Anywhere 9":
                self.check_sybase_drivers()
    
    def check_sybase_drivers(self):
        """检测 Sybase SQL Anywhere 9 可用驱动"""
        drivers_info = []
        
        # 检测 sqlanydb
        try:
            import sqlanydb
            drivers_info.append("✅ sqlanydb (已安装)")
            self.log_section.log_text.append("[INFO] 检测到 sqlanydb 驱动")
        except ImportError:
            drivers_info.append("❌ sqlanydb (未安装)")
            self.log_section.log_text.append("[WARN] 未检测到 sqlanydb 驱动")
        
        # 检测 pyodbc
        try:
            import pyodbc
            drivers_info.append("✅ pyodbc (已安装)")
            self.log_section.log_text.append("[INFO] 检测到 pyodbc 驱动")
            
            # 检查可用的 ODBC 驱动
            available_drivers = pyodbc.drivers()
            sybase_drivers = [d for d in available_drivers if 'SQL Anywhere' in d or 'Sybase' in d]
            if sybase_drivers:
                self.log_section.log_text.append(f"[INFO] 找到 Sybase ODBC 驱动: {', '.join(sybase_drivers)}")
            else:
                self.log_section.log_text.append("[WARN] 未找到 SQL Anywhere ODBC 驱动")
                
        except ImportError:
            drivers_info.append("❌ pyodbc (未安装)")
            self.log_section.log_text.append("[WARN] 未检测到 pyodbc 驱动")
        
        # 显示检测结果
        if not drivers_info:
            self.log_section.log_text.append("[ERROR] 未检测到任何 Sybase 数据库驱动")
        
        # 如果没有驱动，显示警告
        if all("❌" in info for info in drivers_info):
            QMessageBox.warning(
                self,
                "驱动未安装",
                "⚠️ 检测到 Sybase SQL Anywhere 9 数据库驱动未安装\n\n"
                "请选择以下任一方案：\n\n"
                "方案一（推荐）：安装 sqlanydb\n"
                "  pip install sqlanydb\n\n"
                "方案二：安装 pyodbc + ODBC 驱动\n"
                "  pip install pyodbc\n"
                "  并安装 SQL Anywhere 9 客户端\n\n"
                "点击 '❓ Sybase帮助' 查看详细说明"
            )
            self.log_section.log_text.append("[WARN] 建议安装数据库驱动")
    
    def on_backup_changed(self, state):
        """自动备份开关变化"""
        enabled = state == Qt.Checked
        self.backup_section.backup_interval_spin.setEnabled(enabled)
        self.backup_section.backup_path_input.setEnabled(enabled)
        self.backup_section.backup_browse_btn.setEnabled(enabled)
        print(f"[系统设置] 自动备份：{'启用' if enabled else '禁用'}")
    
    def browse_database(self):
        """浏览数据库文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据库文件",
            "",
            "SQLite Files (*.db);;All Files (*)"
        )
        
        if file_path:
            self.db_section.db_path_input.setText(file_path)
            print(f"[系统设置] 选择数据库：{file_path}")
    
    def browse_backup_path(self):
        """浏览备份路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择备份目录",
            "./backup/"
        )
        
        if dir_path:
            self.backup_section.backup_path_input.setText(dir_path)
            print(f"[系统设置] 选择备份路径：{dir_path}")
    
    def test_connection(self):
        """测试数据库连接"""
        # 从单选按钮组获取数据库类型
        if self.db_section.sqlite_radio.isChecked():
            db_type = "SQLite"
        elif self.db_section.mysql_radio.isChecked():
            db_type = "MySQL"
        elif self.db_section.sybase_radio.isChecked():
            db_type = "Sybase Anywhere 9"
        
        self.db_section.test_conn_btn.setEnabled(False)
        self.db_section.test_conn_btn.setText("⏳ 测试中...")
        self.log_section.log_text.append(f"[INFO] 正在测试 {db_type} 连接...")
        
        try:
            if db_type == "SQLite":
                self.test_sqlite_connection()
            elif db_type == "MySQL":
                self.test_mysql_connection()
            elif db_type == "Sybase Anywhere 9":
                self.test_sybase_connection()
        except Exception as e:
            self.log_section.log_text.append(f"[ERROR] 连接测试失败: {str(e)}")
            QMessageBox.critical(self, "连接失败", f"数据库连接测试失败:\n{str(e)}")
        finally:
            self.db_section.test_conn_btn.setEnabled(True)
            self.db_section.test_conn_btn.setText("🔌 测试连接")
    
    def test_sqlite_connection(self):
        """测试 SQLite 连接"""
        db_path = self.db_section.db_path_input.text()
        
        if not db_path:
            QMessageBox.warning(self, "警告", "请输入数据库路径")
            return
        
        self.log_section.log_text.append(f"[INFO] ========== SQLite 连接测试开始 ==========")
        self.log_section.log_text.append(f"[DEBUG] 数据库路径: {db_path}")
        
        # 检查文件是否存在
        import os
        if not os.path.exists(db_path):
            self.log_section.log_text.append(f"[WARN] 数据库文件不存在: {db_path}")
            reply = QMessageBox.question(
                self,
                "文件不存在",
                f"数据库文件不存在:\n{db_path}\n\n是否创建新数据库？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    # 创建目录（如果不存在）
                    dir_path = os.path.dirname(db_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                        self.log_section.log_text.append(f"[DEBUG] 已创建目录: {dir_path}")
                    
                    self.log_section.log_text.append(f"[INFO] 创建新数据库文件: {db_path}")
                    QMessageBox.information(self, "成功", f"SQLite 数据库文件已创建:\n{db_path}")
                    self.log_section.log_text.append(f"[INFO] ✅ SQLite 连接测试成功 (新建数据库)")
                    self.log_section.log_text.append(f"[INFO] ========== SQLite 连接测试结束 ==========")
                except Exception as e:
                    self.log_section.log_text.append(f"[ERROR] 创建数据库文件失败: {str(e)}")
                    raise
            else:
                self.log_section.log_text.append(f"[INFO] 用户取消创建数据库")
                return
        else:
            # 尝试连接
            from models.db_backend import db_manager
            try:
                self.log_section.log_text.append(f"[DEBUG] 正在建立数据库连接...")
                db_manager.connect_sqlite(db_path)
                
                if db_manager.is_connected():
                    self.log_section.log_text.append(f"[INFO] ✅ SQLite 连接成功建立")
                    
                    # 获取数据库信息
                    file_size = os.path.getsize(db_path)
                    self.log_section.log_text.append(f"[INFO] 数据库大小: {file_size / 1024:.2f} KB ({file_size:,} bytes)")
                    
                    cursor = db_manager._backend.conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                    self.log_section.log_text.append(f"[INFO] 数据库包含 {table_count} 个表")
                    
                    # 获取表名列表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                    tables = [row[0] for row in cursor.fetchall()]
                    if tables:
                        self.log_section.log_text.append(f"[DEBUG] 表列表: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
                    
                    QMessageBox.information(
                        self, 
                        "连接成功", 
                        f"✅ SQLite 连接测试成功！\n\n"
                        f"数据库路径: {db_path}\n"
                        f"数据库大小: {file_size / 1024:.2f} KB\n"
                        f"表数量: {table_count}"
                    )
                    self.log_section.log_text.append(f"[INFO] ========== SQLite 连接测试结束 ==========")
                else:
                    self.log_section.log_text.append(f"[ERROR] 连接对象存在但状态异常")
                    raise Exception("连接未成功建立")
            except Exception as e:
                self.log_section.log_text.append(f"[ERROR] ❌ SQLite 连接失败: {type(e).__name__}: {str(e)}")
                self.log_section.log_text.append(f"[INFO] ========== SQLite 连接测试结束 ==========")
                raise
    
    def test_mysql_connection(self):
        """测试 MySQL 连接（使用 EnhancedMySQLBackend 连接池，与实际使用一致）"""
        host = self.db_section.host_input.text() or 'localhost'
        port = self.db_section.port_input.text() or '3306'
        user = self.db_section.user_input.text()
        password = self.db_section.pwd_input.text()
        database = self.db_section.dbname_input.text()
        
        if not user:
            QMessageBox.warning(self, "警告", "请输入用户名")
            return
        
        if not database:
            QMessageBox.warning(self, "警告", "请输入数据库名")
            return
        
        self.log_section.log_text.append(f"[INFO] ========== MySQL 连接测试开始 ==========")
        self.log_section.log_text.append(f"[DEBUG] 主机: {host}:{port}")
        self.log_section.log_text.append(f"[DEBUG] 数据库: {database}")
        self.log_section.log_text.append(f"[DEBUG] 用户: {user}")
        
        backend = None
        try:
            from models.db_backend import EnhancedMySQLBackend
            
            self.log_section.log_text.append(f"[DEBUG] 正在初始化 MySQL 连接池...")
            backend = EnhancedMySQLBackend(pool_size=2, max_overflow=2)
            result = backend.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database
            )
            
            if not result:
                self.log_section.log_text.append(f"[ERROR] ❌ MySQL 连接池初始化失败")
                raise Exception("连接池初始化失败，请检查配置")
            
            self.log_section.log_text.append(f"[INFO] ✅ MySQL 连接池初始化成功")
            
            # 获取数据库信息
            backend.cursor.execute("SELECT VERSION()")
            version = backend.cursor.fetchone()[0]
            self.log_section.log_text.append(f"[INFO] MySQL 版本: {version}")
            
            backend.cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
                (database,)
            )
            table_count = backend.cursor.fetchone()[0]
            self.log_section.log_text.append(f"[INFO] 数据库 '{database}' 包含 {table_count} 个表")
            
            # 获取字符集信息
            backend.cursor.execute("SELECT @@character_set_database")
            charset = backend.cursor.fetchone()[0]
            self.log_section.log_text.append(f"[DEBUG] 数据库字符集: {charset}")
            
            # 获取连接池状态
            pool_status = backend.get_pool_status()
            self.log_section.log_text.append(f"[DEBUG] 连接池状态: {pool_status}")
            
            self.log_section.log_text.append(f"[INFO] ========== MySQL 连接测试结束 ==========")
            
            QMessageBox.information(
                self,
                "连接成功",
                f"✅ MySQL 连接测试成功！\n\n"
                f"主机: {host}:{port}\n"
                f"数据库: {database}\n"
                f"版本: {version}\n"
                f"表数量: {table_count}\n"
                f"连接池: PooledDB (已就绪)"
            )
            
        except ImportError as e:
            missing_pkg = "pymysql" if "pymysql" in str(e) else "DBUtils"
            self.log_section.log_text.append(f"[ERROR] ❌ 缺少依赖: {missing_pkg}")
            self.log_section.log_text.append(f"[INFO] ========== MySQL 连接测试结束 ==========")
            QMessageBox.critical(self, "错误", f"{missing_pkg} 库未安装\n\n请运行: pip install {missing_pkg}")
        except Exception as e:
            self.log_section.log_text.append(f"[ERROR] ❌ MySQL 连接失败: {type(e).__name__}: {str(e)}")
            self.log_section.log_text.append(f"[INFO] ========== MySQL 连接测试结束 ==========")
            raise
        finally:
            if backend:
                try:
                    backend.disconnect()
                    self.log_section.log_text.append(f"[DEBUG] MySQL 连接池已关闭")
                except Exception:
                    pass
    
    def test_sybase_connection(self):
        """测试 Sybase SQL Anywhere 9 连接（使用 EnhancedSybaseBackend，与实际使用一致）"""
        db_path = self.db_section.db_path_input.text()
        
        if not db_path:
            QMessageBox.warning(self, "警告", "请输入数据库文件路径")
            return
        
        self.log_section.log_text.append(f"[INFO] ========== Sybase SQL Anywhere 9 连接测试开始 ==========")
        self.log_section.log_text.append(f"[DEBUG] 数据库路径: {db_path}")
        
        import os
        if not os.path.exists(db_path):
            self.log_section.log_text.append(f"[ERROR] ❌ 数据库文件不存在: {db_path}")
            QMessageBox.critical(self, "错误", f"数据库文件不存在:\n{db_path}")
            self.log_section.log_text.append(f"[INFO] ========== Sybase 连接测试结束 ==========")
            return
        
        file_size = os.path.getsize(db_path)
        self.log_section.log_text.append(f"[DEBUG] 数据库文件大小: {file_size / 1024:.2f} KB ({file_size:,} bytes)")
        
        backend = None
        try:
            from models.db_backend import EnhancedSybaseBackend
            
            self.log_section.log_text.append("[DEBUG] 正在初始化 EnhancedSybaseBackend...")
            backend = EnhancedSybaseBackend()
            
            # EnhancedSybaseBackend.connect() 会按优先级尝试:
            # 1. sqlanydb（如果已安装）
            # 2. pyodbc DSN连接
            # 3. pyodbc DSN-less连接
            # 4. pyodbc 文件直连
            result = backend.connect(
                db_file=db_path,
                uid='DBA',
                pwd='sql',
                dbn='inex_db'
            )
            
            if not result:
                raise Exception("所有连接方式均失败，请检查驱动安装和数据库配置")
            
            # 获取数据库版本
            try:
                backend.cursor.execute("SELECT @@VERSION")
                version = backend.cursor.fetchone()[0]
                self.log_section.log_text.append(f"[INFO] SQL Anywhere 版本: {version}")
            except Exception as e:
                log_manager.debug(f"[设置页面] 获取Sybase版本失败: {e}")
                version = "未知"
            
            # 查询表数量
            try:
                backend.cursor.execute("SELECT COUNT(*) FROM SYSTABLE WHERE table_type = 'BASE'")
                table_count = backend.cursor.fetchone()[0]
                self.log_section.log_text.append(f"[INFO] 数据库包含 {table_count} 个表")
            except Exception as e:
                self.log_section.log_text.append(f"[WARN] 查询表数量失败: {str(e)}")
                table_count = "未知"
            
            # 获取驱动信息
            driver_name = type(backend.conn).__module__ if backend.conn else "未知"
            driver_display = {
                'sqlanydb': 'sqlanydb（原生驱动）',
                'pyodbc': 'pyodbc（ODBC驱动）',
            }.get(driver_name, driver_name)
            
            self.log_section.log_text.append(f"[INFO] ========== Sybase 连接测试结束 ==========")
            
            QMessageBox.information(
                self,
                "连接成功",
                f"✅ Sybase SQL Anywhere 9 连接测试成功！\n\n"
                f"数据库路径: {db_path}\n"
                f"版本: {version}\n"
                f"表数量: {table_count}\n"
                f"驱动: {driver_display}"
            )
            
        except ImportError as e:
            missing_pkg = "sqlanydb" if "sqlanydb" in str(e) else "pyodbc"
            self.log_section.log_text.append(f"[ERROR] ❌ 缺少依赖: {missing_pkg}")
            self.log_section.log_text.append(f"[INFO] ========== Sybase 连接测试结束 ==========")
            QMessageBox.critical(
                self,
                "错误",
                f"缺少依赖库: {missing_pkg}\n\n"
                f"请安装: pip install {missing_pkg}\n\n"
                f"推荐安装 sqlanydb（原生驱动，无需ODBC配置）"
            )
        except Exception as e:
            self.log_section.log_text.append(f"[ERROR] ❌ Sybase 连接失败: {type(e).__name__}: {str(e)}")
            self.log_section.log_text.append(f"[INFO] ========== Sybase 连接测试结束 ==========")
            
            # 提供更详细的错误信息
            error_msg = str(e)
            if "driver" in error_msg.lower() or "驱动" in error_msg.lower() or "odbc" in error_msg.lower():
                QMessageBox.critical(
                    self,
                    "驱动错误",
                    f"ODBC 驱动问题:\n{error_msg}\n\n"
                    f"解决方案:\n"
                    f"1. 确认已安装 SQL Anywhere 9 客户端\n"
                    f"2. 检查 ODBC 驱动名称是否为 'Adaptive Server Anywhere 9.0'\n"
                    f"3. 尝试安装 sqlanydb: pip install sqlanydb"
                )
            else:
                QMessageBox.critical(
                    self,
                    "连接失败",
                    f"Sybase SQL Anywhere 9 连接失败:\n{error_msg}"
                )
        finally:
            if backend:
                try:
                    backend.disconnect()
                    self.log_section.log_text.append(f"[DEBUG] Sybase 连接已关闭")
                except Exception:
                    pass
    
    def open_db_test_dialog(self):
        """打开数据库集成管理对话框"""
        from ui.dialogs.db_manager_dialog import DatabaseManagerDialog
        from models.db_backend import db_manager
        
        self.log_section.log_text.append("[INFO] 打开数据库集成管理工具...")
        
        dialog = DatabaseManagerDialog(db_manager, self)
        dialog.exec_()
        
        print("[系统设置] 打开数据库集成管理工具")
        
    def show_sybase_help(self):
        """显示 Sybase 连接帮助"""
        help_text = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h3 { color: #333; }
        b { color: #555; }
        ol, ul { margin-left: 20px; }
        li { margin-bottom: 10px; }
        code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 4px; }
    </style>
</head>
<body>
    <h3>Sybase SQL Anywhere 9 连接指南</h3>
    <b>方法一：使用 sqlanydb（推荐）</b>
    <ol>
        <li>安装驱动：<code>pip install sqlanydb</code></li>
        <li>确保已安装 SQL Anywhere 9 客户端</li>
        <li>输入数据库文件路径（.db）</li>
    </ol>
    <b>方法二：使用 pyodbc</b>
    <ol>
        <li>安装驱动：<code>pip install pyodbc</code></li>
        <li>安装 SQL Anywhere ODBC 驱动</li>
        <li>配置 ODBC 数据源</li>
    </ol>
    <b>默认凭据：</b>
    <ul>
        <li>用户名：DBA</li>
        <li>密码：sql</li>
    </ul>
    <b>常见问题：</b>
    <ul>
        <li>确保数据库文件路径正确</li>
        <li>检查数据库文件是否被其他程序占用</li>
        <li>确认 SQL Anywhere 服务正在运行</li>
    </ul>
</body>
</html>
        """
        
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Sybase SQL Anywhere 9 连接帮助")
        dialog.setMinimumSize(600, 480)
        
        layout = QVBoxLayout()
        
        browser = QTextBrowser()
        browser.setHtml(help_text)
        browser.setOpenExternalLinks(True)
        
        layout.addWidget(browser)
        dialog.setLayout(layout)
        
        dialog.exec_()

    def manual_backup(self):
        """手动执行数据库备份 - 真实备份逻辑"""
        print("[系统设置] 执行手动备份...")
        self.log_section.log_text.append("[INFO] ========== 开始手动备份数据库 ==========")
        
        import os
        import shutil
        from datetime import datetime
        
        # 获取数据库路径和备份目录
        db_path = self.db_section.db_path_input.text()
        backup_dir = self.backup_section.backup_path_input.text()
        
        # 验证数据库文件是否存在
        if not db_path:
            QMessageBox.warning(self, "警告", "请先配置数据库路径")
            self.log_section.log_text.append("[ERROR] 数据库路径未配置")
            return
        
        if not os.path.exists(db_path):
            QMessageBox.critical(self, "错误", f"数据库文件不存在:\n{db_path}")
            self.log_section.log_text.append(f"[ERROR] 数据库文件不存在: {db_path}")
            return
        
        # 验证备份目录
        if not backup_dir:
            backup_dir = "./backup/"
            self.backup_section.backup_path_input.setText(backup_dir)
            self.log_section.log_text.append(f"[INFO] 使用默认备份目录: {backup_dir}")
        
        try:
            # 创建备份目录（如果不存在）
            os.makedirs(backup_dir, exist_ok=True)
            self.log_section.log_text.append(f"[DEBUG] 备份目录: {backup_dir}")
            
            # 生成带时间戳的备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_filename = os.path.basename(db_path)
            db_name_without_ext = os.path.splitext(db_filename)[0]
            db_ext = os.path.splitext(db_filename)[1]
            backup_filename = f"{db_name_without_ext}_backup_{timestamp}{db_ext}"
            backup_file = os.path.join(backup_dir, backup_filename)
            
            self.log_section.log_text.append(f"[INFO] 正在复制数据库文件...")
            self.log_section.log_text.append(f"[DEBUG] 源文件: {db_path}")
            self.log_section.log_text.append(f"[DEBUG] 目标文件: {backup_file}")
            
            # 执行文件复制
            shutil.copy2(db_path, backup_file)
            
            # 获取备份文件大小
            file_size = os.path.getsize(backup_file)
            file_size_kb = file_size / 1024
            file_size_mb = file_size_kb / 1024
            
            if file_size_mb >= 1:
                size_str = f"{file_size_mb:.2f} MB"
            else:
                size_str = f"{file_size_kb:.2f} KB"
            
            self.log_section.log_text.append(f"[INFO] ✅ 备份成功")
            self.log_section.log_text.append(f"[INFO] 备份文件: {backup_file}")
            self.log_section.log_text.append(f"[INFO] 文件大小: {size_str} ({file_size:,} bytes)")
            self.log_section.log_text.append(f"[INFO] ========== 备份完成 ==========")
            
            # 显示成功消息
            success_msg = (
                f"✅ 数据库备份成功！\n\n"
                f"📁 备份文件:\n{backup_file}\n\n"
                f"📊 文件大小: {size_str}\n"
                f"⏰ 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            QMessageBox.information(self, "备份成功", success_msg)
            
        except PermissionError:
            error_msg = (
                "❌ 权限不足，无法执行备份\n\n"
                "可能原因：\n"
                "• 数据库文件被其他程序占用\n"
                "• 备份目录没有写入权限\n\n"
                "请关闭可能占用数据库的程序后重试"
            )
            self.log_section.log_text.append(f"[ERROR] 权限错误: 无法访问文件或目录")
            QMessageBox.critical(self, "备份失败", error_msg)
            
        except Exception as e:
            error_msg = f"备份过程中发生错误:\n{str(e)}"
            self.log_section.log_text.append(f"[ERROR] 备份失败: {type(e).__name__}: {str(e)}")
            self.log_section.log_text.append(f"[INFO] ========== 备份失败 ==========")
            QMessageBox.critical(self, "备份失败", error_msg)
    
    def clear_log(self):
        """清空日志"""
        print("[系统设置] 清空日志")
        self.log_section.log_text.clear()
        self.log_section.log_text.append("[INFO] 日志已清空")
    
    def test_ai_key(self):
        """测试 API Key 有效性 - 完整测试流程"""
        key = self.ai_section.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "警告", "请输入 API Key")
            return
        
        # 显示加载状态
        original_btn_text = self.ai_section.test_key_btn.text()
        self.ai_section.test_key_btn.setEnabled(False)
        self.ai_section.test_key_btn.setText("⏳ 测试中...")
        self.log_section.log_text.append("[INFO] ========== 开始测试 API Key ==========")
        
        try:
            import requests
            
            # 第一步：测试API连接
            self.log_section.log_text.append("[INFO] 步骤1: 测试 DeepSeek API 连接...")
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-v4-flash",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 50
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_section.log_text.append("[INFO] ✅ API 连接测试成功")
                
                # 第二步：保存到配置文件
                self.log_section.log_text.append("[INFO] 步骤2: 保存配置到本地...")
                
                from utils.ai_assistant import AIConfigManager
                ai_config_manager = AIConfigManager()
                
                model = self.ai_section.model_combo.currentText()
                temperature = self.ai_section.temp_spin.value()
                
                ai_config_manager.save_config(
                    api_key=key,
                    model=model,
                    temperature=temperature,
                    max_tokens=1000
                )
                
                self.log_section.log_text.append("[INFO] ✅ API Key 已加密保存")
                
                # 第三步：验证保存
                self.log_section.log_text.append("[INFO] 步骤3: 验证配置保存...")
                saved_key = ai_config_manager.get_api_key()
                
                if saved_key and saved_key == key:
                    self.log_section.log_text.append("[INFO] ✅ 配置验证成功")
                    
                    success_msg = "✅ API Key 测试成功！\n\n"
                    success_msg += f"🔑 API Key: {key[:8]}...{key[-4:] if len(key) > 12 else '***'}\n"
                    success_msg += f"🎯 模型: {model}\n"
                    success_msg += f"🌡️ 温度: {temperature}\n\n"
                    success_msg += "💡 提示：\n"
                    success_msg += "• 配置已加密保存到 config.json\n"
                    success_msg += "• 下次启动将自动加载\n"
                    success_msg += "• 点击「获取 AI 建议」即可使用\n\n"
                    success_msg += "✨ 您现在可以使用AI智能分析功能了！"
                    
                    QMessageBox.information(self, "测试成功", success_msg)
                    self.log_section.log_text.append("[INFO] ========== API Key 测试完成 ==========")
                else:
                    QMessageBox.critical(self, "配置失败", "配置验证失败，请查看日志")
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', '未知错误')
                
                if response.status_code == 401:
                    suggestion = "❌ API Key 无效或已过期\n\n请检查您的 API Key 是否正确"
                elif response.status_code == 403:
                    suggestion = "❌ 访问被拒绝\n\n请登录 DeepSeek 官网检查账户状态"
                elif response.status_code == 429:
                    suggestion = "⚠️ 请求频率超限\n\n请稍后再试"
                else:
                    suggestion = f"❌ API 测试失败\n\n错误信息：{error_msg}"
                
                QMessageBox.critical(self, "测试失败", suggestion)
                
        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "测试失败", "⏱️ 请求超时\n\n请检查网络连接后重试")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "测试失败", "🌐 网络连接失败\n\n请检查网络连接")
        except ImportError:
            QMessageBox.critical(self, "依赖缺失", "❌ requests 库未安装\n\n请运行: pip install requests")
        except Exception as e:
            QMessageBox.critical(self, "测试失败", f"测试异常:\n{type(e).__name__}: {str(e)}")
        finally:
            self.ai_section.test_key_btn.setEnabled(True)
            self.ai_section.test_key_btn.setText(original_btn_text)

    def get_ai_suggestions(self):
        """获取 AI 建议 - 优化加载状态显示"""
        # 检查API Key
        api_key = ""
        config_error = None
        
        try:
            from utils.ai_assistant import AIConfigManager
            ai_config = AIConfigManager()
            api_key = ai_config.get_api_key()
            
            if not api_key:
                self.log_section.log_text.append("[WARNING] 从配置文件读取API Key为空")
        except Exception as e:
            config_error = str(e)
            self.log_section.log_text.append(f"[ERROR] 读取AI配置失败: {e}")
        
        # 如果配置文件读取失败或为空，尝试从输入框读取
        if not api_key:
            api_key = self.ai_section.api_key_input.text().strip()
            if not api_key:
                error_msg = "请先配置 DeepSeek API Key\n\n"
                error_msg += "配置步骤：\n"
                error_msg += "1. 在上方输入框中输入您的 API Key\n"
                error_msg += "2. 点击「✅ 保存所有设置」按钮\n"
                error_msg += "3. 系统会自动加密保存，下次启动无需重复输入\n\n"
                
                if config_error:
                    error_msg += f"技术细节：{config_error}\n\n"
                
                error_msg += "💡 提示：配置后将自动保存，无需重复输入"
                
                QMessageBox.warning(self, "警告", error_msg)
                return
        
        from models.db_backend import db_manager
        from datetime import datetime, timedelta
        
        # 获取所有收支记录
        income_tuples = db_manager.get_income_records()
        expense_tuples = db_manager.get_expense_records()
        
        all_records = []
        
        for row in income_tuples:
            if len(row) >= 6:
                all_records.append({
                    'djh': row[0],
                    'rq': row[1],
                    'sr_name': row[2],
                    'je': row[3],
                    'zf_name': row[4],
                    'bz': row[5],
                    'sr_code': row[2]
                })
        
        for row in expense_tuples:
            if len(row) >= 6:
                all_records.append({
                    'djh': row[0],
                    'rq': row[1],
                    'zc_name': row[2],
                    'je': row[3],
                    'zf_name': row[4],
                    'bz': row[5],
                    'zc_code': row[2]
                })
        
        if not all_records:
            empty_html = f'''
            <div style=f"background: linear-gradient(135deg, {UIStyles.WARNING} 0%, #d97706 100%); 
                        color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
                <h3 style="margin: 0; font-size: 16px; font-weight: bold;">
                    ⚠️ 暂无数据
                </h3>
            </div>
            <div style="background-color: #fffbeb; padding: 20px; border-radius: 0 0 8px 8px;">
                <div style="text-align: center; color: #92400e; font-size: 14px; line-height: 1.6;">
                    💡 请先添加一些收支记录，AI才能为您生成个性化建议
                </div>
            </div>
            '''
            self.ai_section.ai_output_text.setHtml(empty_html)
            return
        
        self.log_section.log_text.append(f"[INFO] 共加载 {len(all_records)} 条收支记录")

        # 根据选择的时间范围过滤数据
        time_range = self.ai_section.time_range_combo.currentText()
        now = datetime.now()
        filtered_records = all_records
        
        if time_range == "本月":
            first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            first_day_str = first_day.strftime('%Y-%m-%d')
            filtered_records = [r for r in all_records if r.get('rq', '') >= first_day_str]
            
        elif time_range == "上月":
            first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            first_day_str = first_day_last_month.strftime('%Y-%m-%d')
            last_day_str = last_day_last_month.strftime('%Y-%m-%d')
            filtered_records = [r for r in all_records if first_day_str <= r.get('rq', '') <= last_day_str]
            
        elif time_range == "最近30天":
            start_date = now - timedelta(days=30)
            start_date_str = start_date.strftime('%Y-%m-%d')
            filtered_records = [r for r in all_records if r.get('rq', '') >= start_date_str]
            
        elif time_range == "最近90天":
            start_date = now - timedelta(days=90)
            start_date_str = start_date.strftime('%Y-%m-%d')
            filtered_records = [r for r in all_records if r.get('rq', '') >= start_date_str]
        
        records = filtered_records
        
        if not records:
            empty_html = f'''
            <div style=f"background: linear-gradient(135deg, {UIStyles.WARNING} 0%, #d97706 100%); 
                        color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
                <h3 style="margin: 0; font-size: 16px; font-weight: bold;">
                    ⚠️ {time_range}无数据
                </h3>
            </div>
            <div style="background-color: #fffbeb; padding: 20px; border-radius: 0 0 8px 8px;">
                <div style="text-align: center; color: #92400e; font-size: 14px; line-height: 1.6;">
                    💡 {time_range}没有收支记录，请尝试切换时间范围或添加新记录
                </div>
            </div>
            '''
            self.ai_section.ai_output_text.setHtml(empty_html)
            self.log_section.log_text.append(f"[WARNING] {time_range}无数据")
            return

        analysis_type = self.ai_section.analysis_type_combo.currentText()
        
        time_range_desc = time_range
        if time_range == "全部历史数据":
            time_range_desc = "全部历史"
        elif time_range == "本月":
            time_range_desc = f"本月（{datetime.now().strftime('%Y年%m月')}）"
        elif time_range == "上月":
            last_month = (datetime.now().replace(day=1) - timedelta(days=1))
            time_range_desc = f"上月（{last_month.strftime('%Y年%m月')}）"
        
        total_income = sum(r['je'] for r in records if 'sr_code' in r)
        total_expense = sum(r['je'] for r in records if 'zc_code' in r)
        balance = total_income - total_expense
        record_count = len(records)
        income_count = sum(1 for r in records if 'sr_code' in r)
        expense_count = sum(1 for r in records if 'zc_code' in r)
        
        prompt = f"""你是一位拥有10年经验的资深个人理财顾问。请根据用户{time_range_desc}的收支数据，针对【{analysis_type}】给出专业建议。

## 分析周期
- 时间范围：{time_range_desc}
- 总记录数：{record_count}笔（收入{income_count}笔，支出{expense_count}笔）

## 收支概况
- 总收入: {total_income:.2f}元
- 总支出: {total_expense:.2f}元
- 结余: {balance:.2f}元
- 收支比: {(total_income/total_expense*100) if total_expense > 0 else 0:.1f}%
- 平均单笔收入: {(total_income/income_count) if income_count > 0 else 0:.2f}元
- 平均单笔支出: {(total_expense/expense_count) if expense_count > 0 else 0:.2f}元

## 要求
1. **深度洞察**：不要只罗列数据，要指出数据背后的问题或机会。
2. **具体可执行**：建议必须包含具体的行动指南（如“将XX类支出控制在XX元以内”）。
3. **语气专业且亲切**：像朋友一样给出建议。
4. **格式要求**：每条建议一行，以emoji开头，控制在70字以内。
5. **优先级**：优先处理占比最高和增长最快的类别。

请直接输出建议内容，不要编号。
"""

        self.ai_section.get_suggestion_btn.setEnabled(False)
        self.ai_section.get_suggestion_btn.setText("⏳ AI 深度思考中...")
        
        loading_html = f'''
        <div style=f"background: linear-gradient(135deg, {UIStyles.PRIMARY} 0%, {UIStyles.ACCENT_PURPLE} 100%); 
                    color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
            <h3 style="margin: 0; font-size: 16px; font-weight: bold;">
                🚀 AI 深度分析中 (V4 Flash)
            </h3>
        </div>
        <div style=f"background-color: {UIStyles.BG_GRAY_50}; padding: 40px 20px; border-radius: 0 0 8px 8px;">
            <div style="text-align: center;">
                <div style="font-size: 48px; margin-bottom: 15px;">🧠</div>
                <div style=f"color: {UIStyles.TEXT_TERTIARY}; font-size: 14px; margin-bottom: 10px;">
                    正在进行多维度财务健康诊断...
                </div>
                <div style=f"color: {UIStyles.TEXT_DISABLED}; font-size: 12px;">
                    DeepSeek V4 Flash 引擎正在计算最优建议
                </div>
            </div>
        </div>
        '''
        self.ai_section.ai_output_text.setHtml(loading_html)
        self.log_section.log_text.append("[INFO] 正在请求 DeepSeek V4 Flash AI 建议...")

        self.ai_worker = AISuggestionsWorker(
            api_key=api_key,
            model=self.ai_section.model_combo.currentText(),
            prompt=prompt,
            temperature=self.ai_section.temp_spin.value()
        )
        self.ai_worker.finished.connect(self.on_ai_finished)
        self.ai_worker.error.connect(self.on_ai_error)
        self.ai_worker.start()

    def on_ai_finished(self, content):
        """AI 请求完成"""
        self.ai_section.get_suggestion_btn.setEnabled(True)
        self.ai_section.get_suggestion_btn.setText("🔍 获取 AI 建议")
        
        formatted_content = self._format_ai_response(content)
        self.ai_section.ai_output_text.setHtml(formatted_content)
        self.log_section.log_text.append("[INFO] AI 建议生成成功")

    def on_ai_error(self, error_msg):
        """AI 请求出错"""
        self.ai_section.get_suggestion_btn.setEnabled(True)
        self.ai_section.get_suggestion_btn.setText("🔍 获取 AI 建议")
        
        error_html = f'''
        <div style=f"background: linear-gradient(135deg, {UIStyles.DANGER} 0%, {UIStyles.DANGER_HOVER} 100%); 
                    color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
            <h3 style="margin: 0; font-size: 16px; font-weight: bold;">
                ❌ AI服务异常
            </h3>
        </div>
        <div style="background-color: #fef2f2; padding: 20px; border-radius: 0 0 8px 8px;">
            <div style=f"background-color: white; 
                        border-left: 4px solid {UIStyles.DANGER}; 
                        padding: 15px; 
                        border-radius: 6px;">
                <div style=f"color: {UIStyles.DANGER_HOVER}; font-size: 14px; font-weight: bold; margin-bottom: 8px;">
                    错误详情：
                </div>
                <div style="color: #374151; font-size: 13px; line-height: 1.6; word-wrap: break-word;">
                    {error_msg}
                </div>
            </div>
            <div style=f"margin-top: 15px; padding: 12px; background-color: #fffbeb; 
                        border-radius: 6px; border-left: 4px solid {UIStyles.WARNING};">
                <div style="color: #92400e; font-size: 12px; line-height: 1.5;">
                    💡 <strong>解决建议：</strong><br/>
                    • 检查网络连接是否正常<br/>
                    • 确认API Key是否正确配置<br/>
                    • 查看日志了解详细错误信息
                </div>
            </div>
        </div>
        '''
        
        self.ai_section.ai_output_text.setHtml(error_html)
        self.log_section.log_text.append(f"[ERROR] AI 请求失败: {error_msg}")

    def _format_ai_response(self, content):
        """格式化AI返回的内容"""
        if not content:
            return ""
        
        lines = content.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip():
                formatted_lines.append(line)
        
        if not formatted_lines:
            return ""
        
        return "\n".join(formatted_lines)

    def copy_suggestion(self):
        """复制建议内容"""
        content = self.ai_section.ai_output_text.toPlainText()
        if not content or content.strip() in ['暂无内容', '未获取到有效建议，请重试']:
            QMessageBox.warning(self, "提示", "没有可复制的内容")
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        
        from ui.widgets.toast import Toast
        Toast.success(self, "✅ 建议已复制到剪贴板", duration=2000)
        self.log_section.log_text.append("[INFO] 建议已复制到剪贴板")

    def export_suggestion(self):
        """导出建议为文本文件"""
        content = self.ai_section.ai_output_text.toPlainText()
        if not content or content.strip() in ['暂无内容', '未获取到有效建议，请重试']:
            QMessageBox.warning(self, "提示", "没有可导出的内容")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出AI建议", 
            f"AI理财建议_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                header = f"""# AI智能理财建议
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                分析类型: {self.ai_section.analysis_type_combo.currentText()}
                时间范围: {self.ai_section.time_range_combo.currentText()}
                {'='*60}

                """
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(header)
                    f.write(content)
                
                from ui.widgets.toast import Toast
                Toast.success(self, f"✅ 建议已导出至:\n{file_path}", duration=3000)
                self.log_section.log_text.append(f"[INFO] 建议已导出至: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文件时出错:\n{str(e)}")
                self.log_section.log_text.append(f"[ERROR] 导出失败: {e}")
    
    def save_api_settings(self):
        """保存 API 设置（加密存储）"""
        # 清理 API Key 的前后空白字符（包括换行符）
        api_key = self.ai_section.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入 API Key")
            return
        
        # 获取其他配置
        model = self.ai_section.model_combo.currentText()
        temperature = self.ai_section.temp_spin.value()
        
        try:
            # 使用 AIConfigManager 进行加密存储
            from utils.ai_assistant import AIConfigManager
            ai_config_manager = AIConfigManager()
            ai_config_manager.save_config(
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=1000
            )
            
            # 同时在 config.json 中保存非敏感配置
            config.set_api_setting('model', model)
            config.set_api_setting('temperature', temperature)
            
            QMessageBox.information(self, "成功", "✅ API 设置已保存（加密存储）\n\n下次启动将自动加载")
            self.log_section.log_text.append(f"[INFO] API 配置已保存: model={model}, temperature={temperature}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
            self.log_section.log_text.append(f"[ERROR] API 配置保存失败: {e}")

    def save_all_settings(self):
        """保存所有设置"""
        print("[系统设置] 保存所有设置...")
        
        # 获取所有设置值 - 从单选按钮组获取数据库类型
        if self.db_section.sqlite_radio.isChecked():
            db_type = 'sqlite'
        elif self.db_section.mysql_radio.isChecked():
            db_type = 'mysql'
        elif self.db_section.sybase_radio.isChecked():
            db_type = 'sybase'
        
        # 获取数据库路径
        db_path = self.db_section.db_path_input.text()
        
        # 获取MySQL/Sybase连接参数
        host = self.db_section.host_input.text()
        port = self.db_section.port_input.text()
        user = self.db_section.user_input.text()
        password = self.db_section.pwd_input.text()
        database = self.db_section.dbname_input.text()
        
        # 获取自动备份配置
        auto_backup = self.backup_section.auto_backup_check.isChecked()
        backup_interval = self.backup_section.backup_interval_spin.value()
        backup_path = self.backup_section.backup_path_input.text()
        
        # 获取日志配置
        log_level = self.log_section.log_level_combo.currentText()
        
        # 获取AI配置
        ai_config = config.get('ai', {})
        if ai_config:
            api_key = ai_config.get('api_key_encrypted', '')
            model = ai_config.get('model', 'deepseek-chat')
            temperature = ai_config.get('temperature', 0.85)
        else:
            api_key = ''
            model = 'deepseek-chat'
            temperature = 0.85
        
        try:
            # 保存数据库配置
            config.set_database_config(
                db_type,
                path=db_path,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                auto_backup=auto_backup,
                backup_interval=backup_interval,
                backup_path=backup_path
            )
            
            # 保存日志配置
            config.set_log_setting('level', log_level)
            
            # 保存AI配置
            config.set('ai', {
                'api_key_encrypted': api_key,
                'model': model,
                'temperature': temperature
            })
            
            QMessageBox.information(self, "成功", "✅ 所有设置已保存")
            self.log_section.log_text.append("[INFO] 所有设置已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存设置时出错:\n{str(e)}")
            self.log_section.log_text.append(f"[ERROR] 保存设置失败: {str(e)}")
