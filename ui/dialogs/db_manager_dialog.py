# -*- coding: utf-8 -*-
"""
数据库集成管理对话框| 提供表结构浏览、SQL 执行、数据导入导出等高级功能
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QTextEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox, QFileDialog,
                             QLabel, QGroupBox, QWidget, QTabWidget, QToolBar,
                             QAction, QFrame, QComboBox, QLineEdit, QProgressBar,
                             QHeaderView, QCheckBox, QSpinBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSortFilterProxyModel, QAbstractTableModel, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QTextCharFormat, QSyntaxHighlighter, QTextCursor
import csv
import time
import re
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ui.styles import UIStyles


class SQLSyntaxHighlighter(QSyntaxHighlighter):
    """SQL 语法高亮器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # SQL 关键字格式
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(UIStyles.INFO))
        self.keyword_format.setFontWeight(QFont.Bold)
        
        # 字符串格式
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(UIStyles.DANGER))
        
        # 注释格式
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(UIStyles.SUCCESS))
        self.comment_format.setFontItalic(True)
        
        # 数字格式
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(UIStyles.WARNING))
        
        # SQL 关键字列表
        self.keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'DROP', 'ALTER', 'TABLE', 'INDEX', 'VIEW',
            'INTO', 'VALUES', 'SET', 'ORDER BY', 'GROUP BY', 'HAVING',
            'LIMIT', 'OFFSET', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
            'ON', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'LIKE',
            'BETWEEN', 'EXISTS', 'DISTINCT', 'AS', 'COUNT', 'SUM',
            'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
        ]
    
    def highlightBlock(self, text):
        """高亮文本块"""
        # 高亮注释
        comment_pattern = r'(--.*)$'
        for match in re.finditer(comment_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.comment_format)
        
        # 高亮字符串
        string_pattern = r"('[^']*'|\"[^\"]*\")"
        for match in re.finditer(string_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)
        
        # 高亮关键字
        for keyword in self.keywords:
            pattern = r'\b' + keyword + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)
        
        # 高亮数字
        number_pattern = r'\b\d+(\.\d+)?\b'
        for match in re.finditer(number_pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)


class LineNumberArea(QWidget):
    """行号显示区域"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)
    
    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class PaginatedTableModel(QAbstractTableModel):
    """支持分页的表格数据模型"""
    
    def __init__(self, data=None, headers=None, page_size=100):
        super().__init__()
        self.all_data = data or []
        self.headers = headers or []
        self.page_size = page_size
        self.current_page = 0
        self.total_pages = max(1, (len(self.all_data) + self.page_size - 1) // self.page_size)
    
    def rowCount(self, parent=None):
        start = self.current_page * self.page_size
        end = min(start + self.page_size, len(self.all_data))
        return end - start
    
    def columnCount(self, parent=None):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            start = self.current_page * self.page_size
            row = start + index.row()
            if row < len(self.all_data):
                value = self.all_data[row][index.column()]
                return str(value) if value is not None else "NULL"
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal and section < len(self.headers):
                return self.headers[section]
            elif orientation == Qt.Vertical:
                start = self.current_page * self.page_size
                return str(start + section + 1)
        return None
    
    def setPage(self, page):
        """设置当前页"""
        if 0 <= page < self.total_pages:
            self.current_page = page
            self.layoutChanged.emit()
            return True
        return False
    
    def getTotalRows(self):
        return len(self.all_data)
    
    def getTotalPages(self):
        return self.total_pages


class DatabaseManagerDialog(QDialog):
    """数据库管理主界面"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("🗄️ 数据库集成管理")
        self.setMinimumSize(1400, 900)
        
        # SQL 执行历史
        self.sql_history = []
        self.max_history = 50
        
        # 自动补全数据
        self.table_names = []
        self.column_names = {}
        
        # 分页相关
        self.current_model = None
        self.proxy_model = None
        
        self.initUI()
        self.load_database_structure()
        self.update_statistics()
    
    def initUI(self):
        """初始化现代化 UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # ========== 顶部状态栏（卡片式设计）==========
        status_card = self.create_status_card()
        main_layout.addWidget(status_card)
        
        # ========== 主分割器 ==========
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(3)
        self.main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {UIStyles.BORDER_MEDIUM};
            }}
            QSplitter::handle:hover {{
                background-color: {UIStyles.INFO};
            }}
        """)
        
        # 左侧：数据库浏览器（可折叠）
        left_widget = self.create_database_browser()
        self.left_panel = QFrame()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(left_widget)
        self.left_panel.setLayout(left_layout)
        self.left_panel.setMinimumWidth(250)
        self.left_panel.setMaximumWidth(500)
        self.main_splitter.addWidget(self.left_panel)
        
        # 右侧：多标签页（SQL 编辑器 + 结果 + 日志）
        right_widget = self.create_right_panel()
        self.main_splitter.addWidget(right_widget)
        
        # 设置比例
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 3)
        self.main_splitter.setSizes([300, 1100])  # 初始宽度
        
        main_layout.addWidget(self.main_splitter)
        
        # ========== 底部状态栏 ==========
        bottom_bar = self.create_bottom_bar()
        main_layout.addWidget(bottom_bar)
        
        self.setLayout(main_layout)
        
        # 应用全局样式
        self.apply_styles()
    
    def create_status_card(self):
        """创建状态卡片"""
        card = QFrame()
        card.setObjectName("statusCard")
        card.setFixedHeight(70)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 数据库类型图标
        type_icon = QLabel("🗄️")
        type_icon.setFont(QFont("Segoe UI Emoji", 24))
        layout.addWidget(type_icon)
        
        # 连接信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)
        
        backend_type = type(self.db_manager._backend).__name__.replace('Backend', '')
        self.type_label = QLabel(f"数据库类型: {backend_type}")
        self.type_label.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        self.type_label.setStyleSheet(f"color: {UIStyles.SIDEBAR_BG};")
        
        self.status_label = QLabel("● 已连接")
        self.status_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.status_label.setStyleSheet(f"color: {UIStyles.SUCCESS};")
        
        info_layout.addWidget(self.type_label)
        info_layout.addWidget(self.status_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # 切换侧边栏按钮
        toggle_btn = QPushButton("◀ 隐藏面板")
        toggle_btn.setFixedSize(110, 35)
        toggle_btn.clicked.connect(lambda: self.toggle_sidebar(toggle_btn))
        toggle_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(toggle_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFixedSize(100, 35)
        refresh_btn.clicked.connect(self.load_database_structure)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(refresh_btn)
        
        card.setLayout(layout)
        return card
    
    def toggle_sidebar(self, button):
        """切换侧边栏显示/隐藏"""
        if self.left_panel.isVisible():
            self.left_panel.hide()
            button.setText("▶ 显示面板")
            self.main_splitter.setSizes([0, 1400])
        else:
            self.left_panel.show()
            button.setText("◀ 隐藏面板")
            self.main_splitter.setSizes([300, 1100])
    
    def create_database_browser(self):
        """数据库浏览器"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 标题
        title = QLabel("📊 数据库对象浏览")
        title.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        title.setStyleSheet(f"color: {UIStyles.SIDEBAR_BG}; padding: 5px;")
        layout.addWidget(title)
        
        # 树形视图
        self.db_tree = QTreeWidget()
        self.db_tree.setHeaderLabel("数据库结构")
        self.db_tree.itemDoubleClicked.connect(self.on_tree_item_clicked)
        self.db_tree.itemClicked.connect(self.on_tree_item_selected)
        self.db_tree.setStyleSheet(f"""
            QTreeWidget {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 5px;
                background-color: white;
                outline: none;
            }}
            QTreeWidget::item {{
                height: 25px;
                padding: 2px;
            }}
            QTreeWidget::item:hover {{
                background-color: {UIStyles.SIDEBAR_TEXT};
            }}
            QTreeWidget::item:selected {{
                background-color: {UIStyles.INFO};
                color: white;
            }}
        """)
        layout.addWidget(self.db_tree)
        
        # 表信息面板
        info_group = QGroupBox("表信息")
        info_layout = QVBoxLayout()
        
        self.table_info_label = QLabel("选择一个表查看详情")
        self.table_info_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.table_info_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY}; padding: 10px;")
        self.table_info_label.setWordWrap(True)
        info_layout.addWidget(self.table_info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        container.setLayout(layout)
        return container
    
    def create_right_panel(self):
        """创建右侧多标签面板"""
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 5px;
                background-color: white;
            }}
            QTabBar::tab {{
                background-color: {UIStyles.SIDEBAR_TEXT};
                color: {UIStyles.TEXT_TERTIARY};
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                color: {UIStyles.SIDEBAR_BG};
                border-bottom: 2px solid {UIStyles.INFO};
            }}
            QTabBar::tab:hover {{
                background-color: {UIStyles.BG_GRAY_200};
            }}
        """)
        
        # SQL 编辑器标签页
        sql_tab = self.create_sql_editor_tab()
        tab_widget.addTab(sql_tab, "✏️ SQL 编辑器")
        
        # 查询结果标签页
        result_tab = self.create_result_tab()
        tab_widget.addTab(result_tab, "📋 查询结果")
        
        # 执行日志标签页
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "📝 执行日志")
        
        # 数据统计标签页
        stats_tab = self.create_statistics_tab()
        tab_widget.addTab(stats_tab, "📊 数据统计")
        
        return tab_widget
    
    def create_sql_editor_tab(self):
        """创建 SQL 编辑器标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 快捷工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        # 常用 SQL 模板
        template_combo = QComboBox()
        template_combo.addItem("📝 选择 SQL 模板...")
        template_combo.addItem("SELECT * FROM 表名")
        template_combo.addItem("INSERT INTO 表名 VALUES (...)")
        template_combo.addItem("UPDATE 表名 SET ... WHERE ...")
        template_combo.addItem("DELETE FROM 表名 WHERE ...")
        template_combo.addItem("COUNT(*) 统计记录数")
        template_combo.currentIndexChanged.connect(self.on_template_selected)
        template_combo.setFixedWidth(200)
        toolbar.addWidget(template_combo)
        
        toolbar.addStretch()
        
        # 格式化按钮
        format_btn = QPushButton("✨ 格式化")
        format_btn.setFixedSize(80, 30)
        format_btn.clicked.connect(self.format_sql)
        toolbar.addWidget(format_btn)
        
        # 历史记录按钮
        history_btn = QPushButton("🕒 历史")
        history_btn.setFixedSize(80, 30)
        history_btn.clicked.connect(self.show_sql_history)
        toolbar.addWidget(history_btn)
        
        layout.addLayout(toolbar)
        
        # SQL 编辑器（带行号和语法高亮）
        editor_container = QFrame()
        editor_container.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {UIStyles.INFO};
                border-radius: 5px;
                background-color: {UIStyles.BG_GRAY_50};
            }}
        """)
        editor_layout = QHBoxLayout()
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        
        # 行号区域
        self.line_number_area = QWidget()
        self.line_number_area.setFixedWidth(50)
        self.line_number_area.setStyleSheet(f"""
            QWidget {{
                background-color: {UIStyles.BG_GRAY_100};
                border-right: 1px solid {UIStyles.BORDER_LIGHT};
            }}
        """)
        self.line_number_layout = QVBoxLayout()
        self.line_number_layout.setContentsMargins(5, 5, 5, 5)
        self.line_number_layout.setAlignment(Qt.AlignTop)
        self.line_numbers_label = QLabel()
        self.line_numbers_label.setFont(QFont("Consolas", 11))
        self.line_numbers_label.setStyleSheet(f"color: {UIStyles.TEXT_DISABLED};")
        self.line_number_layout.addWidget(self.line_numbers_label)
        self.line_number_area.setLayout(self.line_number_layout)
        editor_layout.addWidget(self.line_number_area)
        
        # SQL 编辑器
        self.sql_editor = QTextEdit()
        self.sql_editor.setFont(QFont("Consolas", 11))
        self.sql_editor.setPlaceholderText("-- 在此输入 SQL 语句\n-- 支持批量执行，每条语句以分号结尾\n\n示例:\nSELECT * FROM sz_c_sr;\nSELECT COUNT(*) FROM sz_sheet_sr;")
        
        # 应用语法高亮
        self.highlighter = SQLSyntaxHighlighter(self.sql_editor.document())
        
        # 连接信号
        self.sql_editor.textChanged.connect(self.update_line_numbers)
        
        editor_layout.addWidget(self.sql_editor)
        
        editor_container.setLayout(editor_layout)
        layout.addWidget(editor_container)
        
        # 操作按钮组
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        exec_btn = QPushButton("▶ 执行 SQL")
        exec_btn.setFixedHeight(35)
        exec_btn.clicked.connect(self.execute_sql)
        exec_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.SUCCESS};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.SUCCESS_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {UIStyles.SUCCESS_HOVER};
            }}
        """)
        btn_layout.addWidget(exec_btn)
        
        import_btn = QPushButton("📂 导入 SQL 文件")
        import_btn.setFixedHeight(35)
        import_btn.clicked.connect(self.import_sql_file)
        btn_layout.addWidget(import_btn)
        
        save_btn = QPushButton("💾 保存 SQL")
        save_btn.setFixedHeight(35)
        save_btn.clicked.connect(self.save_sql_to_file)
        btn_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setFixedHeight(35)
        clear_btn.clicked.connect(self.sql_editor.clear)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def update_line_numbers(self):
        """更新行号显示"""
        line_count = self.sql_editor.document().blockCount()
        line_numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers_label.setText(line_numbers)
    
    def create_result_tab(self):
        """创建查询结果标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 结果信息栏和控制面板
        control_layout = QHBoxLayout()
        
        # 记录数标签
        self.result_count_label = QLabel("记录数: 0")
        self.result_count_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.result_count_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        control_layout.addWidget(self.result_count_label)
        
        control_layout.addStretch()
        
        # 分页控制
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(5)
        
        prev_btn = QPushButton("◀ 上一页")
        prev_btn.setFixedHeight(28)
        prev_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(prev_btn)
        
        self.page_label = QLabel("第 1/1 页")
        self.page_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        pagination_layout.addWidget(self.page_label)
        
        next_btn = QPushButton("下一页 ▶")
        next_btn.setFixedHeight(28)
        next_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(next_btn)
        
        page_size_label = QLabel("每页:")
        pagination_layout.addWidget(page_size_label)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["50", "100", "200", "500"])
        self.page_size_combo.setCurrentText("100")
        self.page_size_combo.setFixedWidth(60)
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        pagination_layout.addWidget(self.page_size_combo)
        
        control_layout.addLayout(pagination_layout)
        
        export_btn = QPushButton("📤 导出为 CSV")
        export_btn.setFixedHeight(30)
        export_btn.clicked.connect(self.export_results_to_csv)
        control_layout.addWidget(export_btn)
        
        layout.addLayout(control_layout)
        
        # 筛选和排序控制面板
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("🔍 输入关键词筛选数据...")
        self.filter_input.setFixedHeight(30)
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input)
        
        clear_filter_btn = QPushButton("清除筛选")
        clear_filter_btn.setFixedHeight(30)
        clear_filter_btn.clicked.connect(self.clear_filter)
        filter_layout.addWidget(clear_filter_btn)
        
        layout.addLayout(filter_layout)
        
        # 结果表格（支持排序和自定义模型）
        from PyQt5.QtWidgets import QTableView
        self.result_table = QTableView()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableView.SelectRows)
        self.result_table.setSortingEnabled(True)  # 启用排序
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.result_table.setStyleSheet(f"""
            QTableView {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 5px;
                gridline-color: {UIStyles.SIDEBAR_TEXT};
                background-color: white;
            }}
            QTableView::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {UIStyles.SIDEBAR_ITEM_BORDER};
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }}
            QTableView::item:selected {{
                background-color: {UIStyles.INFO};
                color: white;
            }}
        """)
        layout.addWidget(self.result_table)
        
        widget.setLayout(layout)
        return widget
    
    def prev_page(self):
        """上一页"""
        if self.current_model:
            current_page = self.current_model.current_page
            if current_page > 0:
                self.current_model.setPage(current_page - 1)
                self.update_pagination_info()
    
    def next_page(self):
        """下一页"""
        if self.current_model:
            current_page = self.current_model.current_page
            if current_page < self.current_model.total_pages - 1:
                self.current_model.setPage(current_page + 1)
                self.update_pagination_info()
    
    def change_page_size(self, size_text):
        """更改每页显示数量"""
        page_size = int(size_text)
        if self.current_model:
            old_page = self.current_model.current_page
            self.current_model.page_size = page_size
            self.current_model.total_pages = max(1, (self.current_model.getTotalRows() + page_size - 1) // page_size)
            new_page = min(old_page, self.current_model.total_pages - 1)
            self.current_model.setPage(new_page)
            self.update_pagination_info()
    
    def update_pagination_info(self):
        """更新分页信息显示"""
        if self.current_model:
            current = self.current_model.current_page + 1
            total = self.current_model.total_pages
            self.page_label.setText(f"第 {current}/{total} 页")
    
    def apply_filter(self, text):
        """应用筛选"""
        if hasattr(self, 'proxy_model') and self.proxy_model:
            self.proxy_model.setFilterRegExp(text)
    
    def clear_filter(self):
        """清除筛选"""
        if hasattr(self, 'filter_input'):
            self.filter_input.clear()
    
    def create_log_tab(self):
        """创建执行日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 5px;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }}
        """)
        layout.addWidget(self.log_text)
        
        # 清空日志按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        clear_log_btn = QPushButton("🗑️ 清空日志")
        clear_log_btn.setFixedHeight(30)
        clear_log_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(clear_log_btn)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_statistics_tab(self):
        """创建数据统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 统计卡片网格
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(10)
        
        # 总表数
        self.tables_card = self.create_stat_card("📊 总表数", "0", "{UIStyles.INFO}")
        stats_grid.addWidget(self.tables_card)
        
        # 总收入记录
        self.income_card = self.create_stat_card("💰 收入记录", "0", "{UIStyles.SUCCESS}")
        stats_grid.addWidget(self.income_card)
        
        # 总支出记录
        self.expense_card = self.create_stat_card("💸 支出记录", "0", "{UIStyles.DANGER}")
        stats_grid.addWidget(self.expense_card)
        
        # 流水账记录
        self.flow_card = self.create_stat_card("📝 流水账", "0", "{UIStyles.WARNING}")
        stats_grid.addWidget(self.flow_card)
        
        layout.addLayout(stats_grid)
        
        # 详细信息区域
        detail_group = QGroupBox("详细统计信息")
        detail_layout = QVBoxLayout()
        
        self.detail_stats_label = QLabel("点击刷新按钮更新统计数据")
        self.detail_stats_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.detail_stats_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY}; padding: 10px;")
        self.detail_stats_label.setWordWrap(True)
        detail_layout.addWidget(self.detail_stats_label)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        # 刷新按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        refresh_btn = QPushButton("🔄 刷新统计")
        refresh_btn.setFixedHeight(35)
        refresh_btn.clicked.connect(self.update_statistics)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_stat_card(self, title, value, color):
        """创建统计卡片"""
        from PyQt5.QtCore import QSize
        card = QFrame()
        card.setFixedHeight(100)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        title_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setFont(QFont(UIStyles.FONT_FAMILY, 20, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        card.setLayout(layout)
        return card
    
    def create_bottom_bar(self):
        """创建底部状态栏"""
        bar = QFrame()
        bar.setFixedHeight(35)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {UIStyles.SIDEBAR_ITEM_BORDER};
                border-radius: 3px;
            }}
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5)
        
        self.bottom_status = QLabel("就绪")
        self.bottom_status.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.bottom_status.setStyleSheet(f"color: {UIStyles.SIDEBAR_TEXT};")
        layout.addWidget(self.bottom_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 4px;
                background-color: {UIStyles.BG_GRAY_50};
                text-align: center;
                font-size: 9px;
            }}
            QProgressBar::chunk {{
                background-color: {UIStyles.PRIMARY};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        self.exec_time_label = QLabel("")
        self.exec_time_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.exec_time_label.setStyleSheet(f"color: {UIStyles.BORDER_MEDIUM};")
        layout.addWidget(self.exec_time_label)
        
        bar.setLayout(layout)
        return bar
    
    def apply_styles(self):
        """应用全局样式"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.CONTENT_BG};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {UIStyles.SIDEBAR_BG};
            }}
            QPushButton {{
                background-color: {UIStyles.INFO};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.INFO_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {UIStyles.INFO_HOVER};
            }}
            #statusCard {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {UIStyles.SIDEBAR_TEXT}, stop:1 {UIStyles.BG_WHITE});
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 8px;
            }}
        """)
    
    def load_database_structure(self):
        """加载数据库树形结构"""
        if not self.db_manager.is_connected():
            return
            
        self.db_tree.clear()
        try:
            cursor = self.db_manager._backend.conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            
            tables_root = QTreeWidgetItem(self.db_tree, ["📊 数据表"])
            tables_root.setFont(0, QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
            
            # 清空并重建表名和列名缓存
            self.table_names = []
            self.column_names = {}
            
            for table in tables:
                table_name = table[0]
                self.table_names.append(table_name)
                table_item = QTreeWidgetItem(tables_root, [f"📋 {table_name}"])
                
                # 获取表的列信息
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                col_names = []
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    not_null = "NOT NULL" if col[3] else "NULL"
                    col_item = QTreeWidgetItem(table_item, [f"🔹 {col_name} ({col_type}, {not_null})"])
                    col_item.setFont(0, QFont("Consolas", 9))
                    col_names.append(col_name)
                
                self.column_names[table_name] = col_names
                
                # 获取记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_item.setToolTip(0, f"记录数: {count}")
            
            self.db_tree.expandAll()
            self.append_log(f"[✓] 数据库结构加载成功，共 {len(tables)} 个表")
            
        except Exception as e:
            self.append_log(f"[✗] 加载结构失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载数据库结构失败:\n{str(e)}")

    def on_tree_item_selected(self, item, column):
        """选择树节点时显示表信息"""
        text = item.text(0)
        if "📋" in text:
            table_name = text.replace("📋 ", "").strip()
            self.show_table_info(table_name)

    def show_table_info(self, table_name):
        """显示表的详细信息"""
        try:
            cursor = self.db_manager._backend.conn.cursor()
            
            # 获取列信息
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # 构建信息文本
            info_text = f"表名: {table_name}\n"
            info_text += f"记录数: {count}\n\n"
            info_text += "字段列表:\n"
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = "NOT NULL" if col[3] else "NULL"
                default = f" DEFAULT {col[4]}" if col[4] else ""
                pk = " [主键]" if col[5] else ""
                info_text += f"  • {col_name}: {col_type} {not_null}{default}{pk}\n"
            
            self.table_info_label.setText(info_text)
            
        except Exception as e:
            self.table_info_label.setText(f"获取表信息失败: {str(e)}")

    def on_tree_item_clicked(self, item, column):
        """双击树节点生成查询 SQL"""
        text = item.text(0)
        if "📋" in text:
            table_name = text.replace("📋 ", "").strip()
            sql = f"SELECT * FROM [{table_name}] LIMIT 100;"
            self.sql_editor.setText(sql)
            self.update_line_numbers()
            self.append_log(f"[→] 生成查询: {sql}")

    def on_template_selected(self, index):
        """SQL 模板选择"""
        if index == 0:
            return
        
        template = self.sender().currentText()
        sql = ""
        
        if "SELECT *" in template:
            sql = "SELECT * FROM table_name;\n"
        elif "INSERT" in template:
            sql = "INSERT INTO table_name (column1, column2) VALUES (value1, value2);\n"
        elif "UPDATE" in template:
            sql = "UPDATE table_name SET column1 = value1 WHERE condition;\n"
        elif "DELETE" in template:
            sql = "DELETE FROM table_name WHERE condition;\n"
        elif "COUNT" in template:
            sql = "SELECT COUNT(*) as total FROM table_name;\n"
        
        if sql:
            self.sql_editor.setText(sql)
            self.update_line_numbers()
            self.append_log(f"[→] 加载模板: {template}")

    def format_sql(self):
        """简单格式化 SQL"""
        sql = self.sql_editor.toPlainText()
        if not sql:
            return
        
        # 简单的关键字大写处理
        keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 
                   'INTO', 'VALUES', 'SET', 'ORDER BY', 'GROUP BY', 'LIMIT']
        
        formatted = sql
        for keyword in keywords:
            formatted = formatted.replace(keyword.lower(), keyword)
            formatted = formatted.replace(keyword.capitalize(), keyword)
        
        self.sql_editor.setText(formatted)
        self.update_line_numbers()
        self.append_log("[✓] SQL 格式化完成")

    def import_sql_file(self):
        """导入 SQL 文件并执行"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择 SQL 文件", 
            "", 
            "SQL Files (*.sql);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self.append_log(f"[→] 正在导入 SQL 文件: {file_path}")
            
            # 检测文件编码
            encoding = self.detect_file_encoding(file_path)
            self.append_log(f"[ℹ] 检测到文件编码: {encoding}")
            
            # 读取 SQL 文件
            with open(file_path, 'r', encoding=encoding) as f:
                sql_content = f.read()
            
            # 加载到编辑器
            self.sql_editor.setText(sql_content)
            self.update_line_numbers()
            self.append_log(f"[✓] SQL 文件加载成功 ({len(sql_content)} 字节)")
            
            # 询问是否立即执行
            reply = QMessageBox.question(
                self,
                "确认执行",
                f"已成功加载 SQL 文件:\n{file_path}\n\n是否立即执行？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.execute_sql()
                
        except Exception as e:
            self.append_log(f"[✗] 导入失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导入失败:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def detect_file_encoding(self, file_path):
        """检测文件编码"""
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 'utf-8'

    def save_sql_to_file(self):
        """保存 SQL 到文件"""
        sql = self.sql_editor.toPlainText()
        if not sql:
            QMessageBox.warning(self, "警告", "没有可保存的 SQL 内容")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存 SQL 文件", "", "SQL Files (*.sql);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sql)
                self.append_log(f"[✓] SQL 已保存到: {file_path}")
                QMessageBox.information(self, "成功", f"SQL 已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")

    def show_sql_history(self):
        """显示 SQL 执行历史"""
        if not self.sql_history:
            QMessageBox.information(self, "提示", "暂无执行历史")
            return
        
        history_text = "SQL 执行历史（最近 {} 条）:\n\n".format(len(self.sql_history))
        for i, sql in enumerate(reversed(self.sql_history[-10:]), 1):
            preview = sql[:80].replace('\n', ' ')
            history_text += f"{i}. {preview}...\n\n"
        
        QMessageBox.information(self, "执行历史", history_text)

    def execute_sql(self):
        """执行 SQL 并显示结果"""
        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "警告", "请输入 SQL 语句")
            return
        
        # 记录到历史
        self.sql_history.append(sql)
        if len(self.sql_history) > self.max_history:
            self.sql_history.pop(0)
        
        start_time = time.time()
        self.append_log(f"\n{'='*60}")
        self.append_log(f"[▶] 开始执行 SQL ({time.strftime('%H:%M:%S')})")
        self.append_log(f"{'='*60}")
        
        try:
            # 分割多条 SQL 语句
            sql_statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            
            if not sql_statements:
                QMessageBox.warning(self, "警告", "没有有效的 SQL 语句")
                return
            
            self.append_log(f"[ℹ] 共 {len(sql_statements)} 条语句 — 正在执行...")
            is_bulk = len(sql_statements) > 10
            if is_bulk:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.bottom_status.setText("正在执行...")

            total_affected = 0
            last_results = []
            last_headers = []
            total_count = len(sql_statements)
            log_interval = max(1, total_count // 5)
            data_tables_modified = False  # 追踪是否修改了收支数据表

            try:
                if is_bulk:
                    self.db_manager._backend.begin_transaction()

                for i, statement in enumerate(sql_statements, 1):
                    if is_bulk:
                        self.db_manager._backend.cursor.execute(statement)
                    else:
                        self.db_manager._backend.execute(statement)

                    # 进度条 + 偶发日志（减少UI开销）
                    if i % 100 == 0 and is_bulk:
                        pct = int(i * 100 / total_count)
                        self.progress_bar.setValue(pct)
                    if i % log_interval == 0:
                        self.bottom_status.setText(f"执行中... {i}/{total_count} ({int(i*100/total_count)}%)")
                        QApplication.processEvents()

                    try:
                        results = self.db_manager._backend.fetchall()
                        if results:
                            last_results = results
                            if hasattr(self.db_manager._backend.cursor, 'description') and self.db_manager._backend.cursor.description:
                                last_headers = [d[0] for d in self.db_manager._backend.cursor.description]
                            total_affected += len(results)
                    except Exception:
                        if hasattr(self.db_manager._backend.cursor, 'rowcount'):
                            a = self.db_manager._backend.cursor.rowcount
                            if a >= 0:
                                total_affected += a

                # 追踪数据表修改
                for stmt in sql_statements:
                    if any(t in stmt.upper() for t in ('SZ_SHEET_SR', 'SZ_SHEET_ZC', 'SZ_D_ZT')):
                        data_tables_modified = True
                        break

                if is_bulk:
                    self.db_manager._backend.commit_transaction()
                    self.progress_bar.setValue(100)
                    QApplication.processEvents()

                    # 自动重建派生表
                    if data_tables_modified:
                        self.bottom_status.setText("正在重建流水账和月报表...")
                        QApplication.processEvents()
                        try:
                            from models.db_backend import SQLFileImporter
                            imp = SQLFileImporter(self.db_manager._backend)
                            imp._rebuild_derived_tables()
                            self.append_log("[OK] 流水账和月报表已自动重建")
                        except Exception as rebuild_err:
                            self.append_log(f"[WARN] 自动重建失败: {rebuild_err}")

            except Exception as stmt_error:
                if is_bulk:
                    try:
                        self.db_manager._backend.rollback_transaction()
                    except Exception:
                        pass
                self.progress_bar.setVisible(False)
                error_msg = f"执行失败: {str(stmt_error)[:200]}"
                self.append_log(f"      ✗ {str(stmt_error)[:100]}")
                QMessageBox.critical(self, "错误", error_msg)
                return
            
            exec_time = time.time() - start_time

            self.progress_bar.setVisible(False)
            self.bottom_status.setText(f"✓ 执行成功 | {len(sql_statements)} 条语句 | {exec_time:.1f}秒")

            # 显示结果
            if last_results:
                self.display_results_with_pagination(last_results, last_headers)
                self.append_log(f"\n[✓] 批量执行成功！返回 {len(last_results)} 条记录")
                QMessageBox.information(
                    self, "成功", 
                    f"批量执行成功！\n共执行 {len(sql_statements)} 条语句\n返回 {len(last_results)} 条记录"
                )
            else:
                # 清空表格（QTableView使用空模型）
                self.current_model = None
                self.proxy_model = None
                from PyQt5.QtGui import QStandardItemModel
                empty_model = QStandardItemModel()
                self.result_table.setModel(empty_model)
                self.result_count_label.setText("记录数: 0")
                self.page_label.setText("第 1/1 页")
                self.append_log(f"\n[✓] 批量执行成功！影响 {total_affected} 行数据")
                QMessageBox.information(
                    self, "成功", 
                    f"批量执行成功！\n共执行 {len(sql_statements)} 条语句\n影响 {total_affected} 行数据"
                )
            
            self.exec_time_label.setText(f"耗时 {exec_time:.1f}s")

        except Exception as e:
            self.progress_bar.setVisible(False)
            exec_time = time.time() - start_time
            self.append_log(f"\n[✗] 执行失败: {str(e)}")
            self.exec_time_label.setText(f"执行失败")
            self.bottom_status.setText(f"✗ 执行失败")
            QMessageBox.critical(self, "错误", f"执行失败:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def display_results_with_pagination(self, results, headers=None):
        """使用分页模型显示查询结果"""
        if not results:
            return
        
        # 如果没有提供表头，使用默认表头
        if not headers:
            headers = [f"列{i+1}" for i in range(len(results[0]))]
        
        # 创建分页模型
        page_size = int(self.page_size_combo.currentText())
        self.current_model = PaginatedTableModel(results, headers, page_size)
        
        # 创建代理模型用于筛选
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.current_model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)  # 在所有列中筛选
        
        # 设置表格模型
        self.result_table.setModel(self.proxy_model)
        
        # 更新记录数和分页信息
        self.result_count_label.setText(f"记录数: {len(results)}")
        self.update_pagination_info()
        
        self.append_log(f"[ℹ] 结果已显示在表格中（分页模式）")

    def append_log(self, message):
        """追加日志"""
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.append(log_entry)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def export_results_to_csv(self):
        """将当前查询结果导出为 CSV 文件"""
        if not self.current_model or self.current_model.getTotalRows() == 0:
            QMessageBox.warning(self, "提示", "没有可导出的数据")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存 CSV 文件", 
            f"export_{time.strftime('%Y%m%d_%H%M%S')}.csv", 
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow(self.current_model.headers)
                
                # 写入所有数据（不分页）
                for row_data in self.current_model.all_data:
                    writer.writerow([str(cell) if cell is not None else "" for cell in row_data])
            
            self.append_log(f"[✓] 数据已导出至: {file_path}")
            QMessageBox.information(self, "成功", f"数据已导出至:\n{file_path}")
        except Exception as e:
            self.append_log(f"[✗] 导出失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def update_statistics(self):
        """更新数据统计"""
        if not self.db_manager.is_connected():
            return
        
        try:
            cursor = self.db_manager._backend.conn.cursor()
            
            # 统计表数量
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # 统计各表记录数
            cursor.execute("SELECT COUNT(*) FROM sz_sheet_sr")
            income_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sz_sheet_zc")
            expense_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sz_table_lsz")
            flow_count = cursor.fetchone()[0]
            
            # 更新卡片
            for card in [self.tables_card, self.income_card, self.expense_card, self.flow_card]:
                value_label = card.findChild(QLabel, "value_label")
                if value_label:
                    if card == self.tables_card:
                        value_label.setText(str(table_count))
                    elif card == self.income_card:
                        value_label.setText(str(income_count))
                    elif card == self.expense_card:
                        value_label.setText(str(expense_count))
                    elif card == self.flow_card:
                        value_label.setText(str(flow_count))
            
            # 更新详细信息
            detail_text = f"数据库统计详情:\n\n"
            detail_text += f"• 总表数: {table_count}\n"
            detail_text += f"• 收入记录: {income_count}\n"
            detail_text += f"• 支出记录: {expense_count}\n"
            detail_text += f"• 流水账记录: {flow_count}\n"
            detail_text += f"• 总交易数: {income_count + expense_count}\n\n"
            
            # 计算总金额
            cursor.execute("SELECT COALESCE(SUM(je), 0) FROM sz_sheet_sr")
            total_income = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(je), 0) FROM sz_sheet_zc")
            total_expense = cursor.fetchone()[0]
            
            detail_text += f"财务汇总:\n"
            detail_text += f"• 总收入: ¥{total_income:,.2f}\n"
            detail_text += f"• 总支出: ¥{total_expense:,.2f}\n"
            detail_text += f"• 净结余: ¥{total_income - total_expense:,.2f}\n"
            
            self.detail_stats_label.setText(detail_text)
            self.append_log(f"[✓] 统计数据已更新")
            
        except Exception as e:
            self.append_log(f"[✗] 统计更新失败: {str(e)}")
            QMessageBox.warning(self, "警告", f"更新统计失败:\n{str(e)}")
