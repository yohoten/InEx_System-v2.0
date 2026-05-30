# -*- coding: utf-8 -*-
"""
全局搜索对话框
支持在收入、支出、分类、支付方式中搜索关键字
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QTabWidget, QWidget, QMessageBox, QFrame, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
from models.db_backend import db_manager
from ui.styles import UIStyles
from utils.logger import log_manager


class GlobalSearchDialog(QDialog):
    """全局搜索对话框 - 简约高效版"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 全局搜索")
        self.setFixedSize(950, 700)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.BG_GRAY_50};
            }}
        """)
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 顶部标题栏 ==========
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title_label = QLabel("🔍 全局搜索")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_XXLARGE, QFont.Bold))
        title_label.setStyleSheet(f"color: {UIStyles.PRIMARY}; padding: 5px 0;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 快捷键提示
        shortcut_label = QLabel("Ctrl+F 快速聚焦")
        shortcut_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        shortcut_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        header_layout.addWidget(shortcut_label)
        
        main_layout.addLayout(header_layout)
        
        # ========== 搜索输入区 ==========
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_container.setStyleSheet(f"""
            QFrame#searchContainer {{
                background-color: white;
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
                border: 2px solid {UIStyles.BORDER_LIGHT};
                padding: 15px;
            }}
        """)
        search_layout = QVBoxLayout()
        search_layout.setSpacing(12)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索输入框 + 按钮
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入单据号、日期、金额、备注、分类名称等关键词...")
        self.search_input.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM))
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet(UIStyles.input_style())
        self.search_input.returnPressed.connect(self.perform_search)
        input_row.addWidget(self.search_input)
        
        self.search_btn = QPushButton("🔍 搜索")
        self.search_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL, QFont.Bold))
        self.search_btn.setFixedHeight(40)
        self.search_btn.setFixedWidth(100)
        self.search_btn.setStyleSheet(UIStyles.primary_button(font_size=UIStyles.FONT_SIZE_NORMAL, font_weight="bold"))
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.clicked.connect(self.perform_search)
        input_row.addWidget(self.search_btn)
        
        search_layout.addLayout(input_row)
        
        # 搜索范围选择（使用水平排列的现代按钮）
        scope_layout = QHBoxLayout()
        scope_layout.setSpacing(8)
        
        scope_label = QLabel("搜索范围:")
        scope_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        scope_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY};")
        scope_layout.addWidget(scope_label)
        
        # 使用可勾选按钮替代复选框
        self.btn_income = QPushButton("💰 收入")
        self.btn_income.setCheckable(True)
        self.btn_income.setChecked(True)
        self.btn_income.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        self.btn_income.setFixedHeight(28)
        self.btn_income.setCursor(Qt.PointingHandCursor)
        self.btn_income.setStyleSheet(UIStyles.modern_checkable_button(is_default=False))
        scope_layout.addWidget(self.btn_income)
        
        self.btn_expense = QPushButton("💸 支出")
        self.btn_expense.setCheckable(True)
        self.btn_expense.setChecked(True)
        self.btn_expense.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        self.btn_expense.setFixedHeight(28)
        self.btn_expense.setCursor(Qt.PointingHandCursor)
        self.btn_expense.setStyleSheet(UIStyles.modern_checkable_button(is_default=False))
        scope_layout.addWidget(self.btn_expense)
        
        self.btn_category = QPushButton("📂 分类")
        self.btn_category.setCheckable(True)
        self.btn_category.setChecked(True)
        self.btn_category.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        self.btn_category.setFixedHeight(28)
        self.btn_category.setCursor(Qt.PointingHandCursor)
        self.btn_category.setStyleSheet(UIStyles.modern_checkable_button(is_default=False))
        scope_layout.addWidget(self.btn_category)
        
        self.btn_payment = QPushButton("💳 支付")
        self.btn_payment.setCheckable(True)
        self.btn_payment.setChecked(True)
        self.btn_payment.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        self.btn_payment.setFixedHeight(28)
        self.btn_payment.setCursor(Qt.PointingHandCursor)
        self.btn_payment.setStyleSheet(UIStyles.modern_checkable_button(is_default=False))
        scope_layout.addWidget(self.btn_payment)
        
        scope_layout.addStretch()
        
        search_layout.addLayout(scope_layout)
        
        search_container.setLayout(search_layout)
        main_layout.addWidget(search_container)
        
        # ========== 结果区域 ==========
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        self.tab_widget.setStyleSheet(UIStyles.tab_widget_style())
        
        # 创建四个结果表格
        self.income_table = self.create_result_table([
            "单据号", "日期", "类型", "金额", "支付方式", "备注"
        ])
        self.tab_widget.addTab(self.income_table, f"💰 收入 (0)")
        
        self.expense_table = self.create_result_table([
            "单据号", "日期", "类型", "金额", "支付方式", "备注"
        ])
        self.tab_widget.addTab(self.expense_table, f"💸 支出 (0)")
        
        self.category_table = self.create_result_table([
            "编码", "名称", "类型"
        ])
        self.tab_widget.addTab(self.category_table, f"📂 分类 (0)")
        
        self.payment_table = self.create_result_table([
            "编码", "名称"
        ])
        self.tab_widget.addTab(self.payment_table, f"💳 支付方式 (0)")
        
        main_layout.addWidget(self.tab_widget)
        
        # ========== 底部操作栏 ==========
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: 10px 15px;
            }}
        """)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.setStyleSheet(UIStyles.secondary_button())
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        
        # 结果显示统计
        self.result_count_label = QLabel("共 0 条结果")
        self.result_count_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        self.result_count_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY};")
        btn_layout.addWidget(self.result_count_label)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL, QFont.Bold))
        self.close_btn.setFixedHeight(32)
        self.close_btn.setFixedWidth(80)
        self.close_btn.setStyleSheet(UIStyles.primary_button())
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        bottom_frame.setLayout(btn_layout)
        main_layout.addWidget(bottom_frame)
        
        self.setLayout(main_layout)
        
        # 聚焦到搜索输入框
        self.search_input.setFocus()
    
    def create_result_table(self, headers):
        """创建结果表格"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # 设置表头样式
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL, QFont.Bold))
        
        # 隐藏垂直表头
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(32)
        
        # 启用交替行颜色
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 设置字体
        table.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_SMALL))
        
        # 应用样式
        table.setStyleSheet(UIStyles.table_style())
        
        return table
    
    def perform_search(self):
        """执行搜索"""
        keyword = self.search_input.text().strip()
        
        if not keyword:
            QMessageBox.warning(self, "警告", "请输入搜索关键字!")
            self.search_input.setFocus()
            return
        
        # 构建搜索类型列表
        search_types = []
        if self.btn_income.isChecked():
            search_types.append('income')
        if self.btn_expense.isChecked():
            search_types.append('expense')
        if self.btn_category.isChecked():
            search_types.append('category')
        if self.btn_payment.isChecked():
            search_types.append('payment')
        
        if not search_types:
            QMessageBox.warning(self, "警告", "请至少选择一个搜索范围!")
            return
        
        # 更新按钮文本显示加载状态
        original_text = self.search_btn.text()
        self.search_btn.setText("⏳ 搜索中...")
        self.search_btn.setEnabled(False)
        
        try:
            # 执行搜索
            log_manager.info(f"开始全局搜索: 关键字='{keyword}', 范围={search_types}")
            results = db_manager.global_search(keyword, search_types)
            
            # 显示结果
            self.display_results(results)
            
            # 统计总数
            total_count = sum(len(v) for v in results.values())
            self.result_count_label.setText(f"共 {total_count} 条结果")
            log_manager.info(f"搜索完成: 共找到 {total_count} 条结果")
            
        except Exception as e:
            log_manager.error(f"搜索失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"搜索失败: {str(e)}")
        finally:
            # 恢复按钮状态
            self.search_btn.setText(original_text)
            self.search_btn.setEnabled(True)
    
    def display_results(self, results):
        """显示搜索结果"""
        # 1. 收入结果
        income_data = results.get('income', [])
        self.income_table.setRowCount(len(income_data))
        for i, item in enumerate(income_data):
            self._set_table_item(self.income_table, i, 0, item['djh'])
            self._set_table_item(self.income_table, i, 1, item['rq'])
            self._set_table_item(self.income_table, i, 2, item['type_name'] or '')
            self._set_table_item(self.income_table, i, 3, str(item['je']), align_right=True)
            self._set_table_item(self.income_table, i, 4, item['payment_name'] or '')
            self._set_table_item(self.income_table, i, 5, item['bz'] or '')
        self.tab_widget.setTabText(0, f"💰 收入 ({len(income_data)})")
        
        # 2. 支出结果
        expense_data = results.get('expense', [])
        self.expense_table.setRowCount(len(expense_data))
        for i, item in enumerate(expense_data):
            self._set_table_item(self.expense_table, i, 0, item['djh'])
            self._set_table_item(self.expense_table, i, 1, item['rq'])
            self._set_table_item(self.expense_table, i, 2, item['type_name'] or '')
            self._set_table_item(self.expense_table, i, 3, str(item['je']), align_right=True)
            self._set_table_item(self.expense_table, i, 4, item['payment_name'] or '')
            self._set_table_item(self.expense_table, i, 5, item['bz'] or '')
        self.tab_widget.setTabText(1, f"💸 支出 ({len(expense_data)})")
        
        # 3. 分类结果
        category_data = results.get('category', [])
        self.category_table.setRowCount(len(category_data))
        for i, item in enumerate(category_data):
            self._set_table_item(self.category_table, i, 0, item['code'])
            self._set_table_item(self.category_table, i, 1, item['name'])
            self._set_table_item(self.category_table, i, 2, item['type'])
        self.tab_widget.setTabText(2, f"📂 分类 ({len(category_data)})")
        
        # 4. 支付方式结果
        payment_data = results.get('payment', [])
        self.payment_table.setRowCount(len(payment_data))
        for i, item in enumerate(payment_data):
            self._set_table_item(self.payment_table, i, 0, item['code'])
            self._set_table_item(self.payment_table, i, 1, item['name'])
        self.tab_widget.setTabText(3, f"💳 支付方式 ({len(payment_data)})")
        
        # 如果有结果,自动切换到第一个有结果的tab
        if income_data:
            self.tab_widget.setCurrentIndex(0)
        elif expense_data:
            self.tab_widget.setCurrentIndex(1)
        elif category_data:
            self.tab_widget.setCurrentIndex(2)
        elif payment_data:
            self.tab_widget.setCurrentIndex(3)
    
    def _set_table_item(self, table, row, col, text, align_right=False):
        """设置表格项（辅助方法）"""
        item = QTableWidgetItem(text)
        if align_right:
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.setItem(row, col, item)
    
    def highlight_keyword_in_table(self, table, keyword):
        """在表格中高亮显示关键字（预留扩展）"""
        # 未来可以实现更复杂的富文本高亮
        pass

    def clear_results(self):
        """清空搜索结果"""
        self.search_input.clear()
        self.income_table.setRowCount(0)
        self.expense_table.setRowCount(0)
        self.category_table.setRowCount(0)
        self.payment_table.setRowCount(0)
        self.tab_widget.setTabText(0, "💰 收入 (0)")
        self.tab_widget.setTabText(1, "💸 支出 (0)")
        self.tab_widget.setTabText(2, "📂 分类 (0)")
        self.tab_widget.setTabText(3, "💳 支付方式 (0)")
        self.result_count_label.setText("共 0 条结果")
        self.search_input.setFocus()
