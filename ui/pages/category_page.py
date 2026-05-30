# -*- coding: utf-8 -*-
"""
分类管理页面
管理收入类型、支出类型和支付方式码表
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QTabWidget, QMessageBox,
                             QLineEdit, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt

from models.db_backend import db_manager
from ui.styles import UIStyles


class CategoryPage(QWidget):
    """分类管理页面"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_data()
    
    def initUI(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("📁 分类管理（码表）")
        title_label.setStyleSheet(UIStyles.page_title_style())
        layout.addWidget(title_label)

        # 创建 Tab 控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(UIStyles.tab_widget_style())
        
        # 收入类型标签页
        income_tab = self.create_income_type_tab()
        self.tab_widget.addTab(income_tab, "💰 收入类型")
        
        # 支出类型标签页
        expense_tab = self.create_expense_type_tab()
        self.tab_widget.addTab(expense_tab, "💸 支出类型")
        
        # 支付方式标签页
        payment_tab = self.create_payment_method_tab()
        self.tab_widget.addTab(payment_tab, "💳 支付方式")
        
        layout.addWidget(self.tab_widget)
        
        # 底部占比说明
        info_label = QLabel("💡 提示：编码采用两位数字，方便记忆和输入。修改分类后请重新加载数据。")
        info_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY}; font-size: {UIStyles.FONT_SIZE_NORMAL}px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def _style_table(self, table):
        """统一表格样式"""
        table.setStyleSheet(UIStyles.modern_table_style())
        table.setAlternatingRowColors(True)
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

    def _make_tab(self, table_setter, add_handler, delete_handler, refresh_handler):
        """创建带表格+按钮的标签页"""
        widget = QWidget()
        layout = QVBoxLayout()

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["编码", "名称", "操作"])
        table.setEditTriggers(QTableWidget.DoubleClicked)
        table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self._style_table(table)
        setattr(self, table_setter, table)
        layout.addWidget(table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ 添加")
        add_btn.setStyleSheet(UIStyles.success_button())
        add_btn.clicked.connect(add_handler)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("🗑️ 删除")
        del_btn.setStyleSheet(UIStyles.danger_button())
        del_btn.clicked.connect(delete_handler)
        btn_layout.addWidget(del_btn)

        ref_btn = QPushButton("🔄 刷新")
        ref_btn.setStyleSheet(UIStyles.default_button())
        ref_btn.clicked.connect(refresh_handler)
        btn_layout.addWidget(ref_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def create_income_type_tab(self):
        return self._make_tab(
            "income_table",
            lambda: self.add_category('income'),
            lambda: self.delete_category('income'),
            self.load_data
        )

    def create_expense_type_tab(self):
        return self._make_tab(
            "expense_table",
            lambda: self.add_category('expense'),
            lambda: self.delete_category('expense'),
            self.load_data
        )

    def create_payment_method_tab(self):
        return self._make_tab(
            "payment_table",
            lambda: self.add_category('payment'),
            lambda: self.delete_category('payment'),
            self.load_data
        )
    
    def load_data(self):
        """加载数据"""
        print("[分类管理] 加载数据...")
        
        # 加载收入类型
        self.income_table.setRowCount(0)
        income_types = db_manager.get_income_types()
        for code, name in income_types:
            row = self.income_table.rowCount()
            self.income_table.insertRow(row)
            self.income_table.setItem(row, 0, QTableWidgetItem(code))
            self.income_table.setItem(row, 1, QTableWidgetItem(name))
            self.income_table.setItem(row, 2, QTableWidgetItem("双击编辑"))
        
        # 加载支出类型
        self.expense_table.setRowCount(0)
        expense_types = db_manager.get_expense_types()
        for code, name in expense_types:
            row = self.expense_table.rowCount()
            self.expense_table.insertRow(row)
            self.expense_table.setItem(row, 0, QTableWidgetItem(code))
            self.expense_table.setItem(row, 1, QTableWidgetItem(name))
            self.expense_table.setItem(row, 2, QTableWidgetItem("双击编辑"))
        
        # 加载支付方式
        self.payment_table.setRowCount(0)
        payment_methods = db_manager.get_payment_methods()
        for code, name in payment_methods:
            row = self.payment_table.rowCount()
            self.payment_table.insertRow(row)
            self.payment_table.setItem(row, 0, QTableWidgetItem(code))
            self.payment_table.setItem(row, 1, QTableWidgetItem(name))
            self.payment_table.setItem(row, 2, QTableWidgetItem("双击编辑"))
        
        print(f"[分类管理] 加载完成 - 收入{len(income_types)}条，支出{len(expense_types)}条，支付{len(payment_methods)}条")
    
    def on_item_double_clicked(self, item):
        """双击编辑单元格"""
        row = item.row()
        col = item.column()
        table = self.sender().parent()
        
        # 确定当前表格对应的分类类型
        if table == self.income_table:
            category_type = 'income'
            update_item = db_manager.update_income_type
            get_items = db_manager.get_income_types
        elif table == self.expense_table:
            category_type = 'expense'
            update_item = db_manager.update_expense_type
            get_items = db_manager.get_expense_types
        else:  # payment_table
            category_type = 'payment'
            update_item = db_manager.update_payment_method
            get_items = db_manager.get_payment_methods
        
        if col < 2:  # 只允许编辑编码和名称列
            current_text = item.text()
            field_name = '编码' if col == 0 else '名称'
            
            new_text, ok = QLineEdit.getText(
                self, 
                "编辑分类", 
                f"请输入新{field_name}:",
                QLineEdit.Normal,
                current_text
            )
            
            if ok and new_text:
                # 获取当前行的编码
                code_item = table.item(row, 0)
                name_item = table.item(row, 1)
                
                current_code = code_item.text() if code_item else ""
                current_name = name_item.text() if name_item else ""
                
                # 根据列更新不同的字段
                if col == 0:  # 编辑编码
                    new_code = new_text
                    new_name = current_name
                else:  # 编辑名称
                    new_code = current_code
                    new_name = new_text
                
                # 调用数据库更新
                success = update_item(new_code, new_name)
                
                if success:
                    print(f"[分类管理] 更新成功：{new_code}-{new_name}")
                    item.setText(new_text)
                    QMessageBox.information(self, "成功", "分类信息已更新")
                else:
                    QMessageBox.warning(self, "失败", "更新失败，请检查编码是否重复")
    
    def add_category(self, category_type):
        """添加分类"""
        dialog = AddCategoryDialog(category_type, self)
        if dialog.exec_() == QDialog.Accepted:
            code = dialog.code_input.text()
            name = dialog.name_input.text()
            
            if not code or not name:
                QMessageBox.warning(self, "警告", "编码和名称不能为空！")
                return
            
            print(f"[分类管理] 添加{category_type}分类：{code} - {name}")
            
            # 根据分类类型调用对应的数据库添加方法
            if category_type == 'income':
                success = db_manager.add_income_type(code, name)
            elif category_type == 'expense':
                success = db_manager.add_expense_type(code, name)
            else:  # payment
                success = db_manager.add_payment_method(code, name)
            
            if success:
                QMessageBox.information(self, "成功", f"已添加{category_type}分类：{code} - {name}")
                self.load_data()
            else:
                QMessageBox.warning(self, "失败", "添加失败，请检查编码是否重复")
    
    def delete_category(self, category_type):
        """删除分类"""
        # 获取对应的表格和删除方法
        if category_type == 'income':
            table = self.income_table
            delete_item = db_manager.delete_income_type
        elif category_type == 'expense':
            table = self.expense_table
            delete_item = db_manager.delete_expense_type
        else:  # payment
            table = self.payment_table
            delete_item = db_manager.delete_payment_method
        
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的行！")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 条记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            fail_count = 0
            
            # 从后往前删除，避免行号变化
            for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                row = index.row()
                code = table.item(row, 0).text()
                name = table.item(row, 1).text()
                print(f"[分类管理] 删除{category_type}分类：{code} - {name}")
                
                # 调用数据库删除方法
                success = delete_item(code)
                
                if success:
                    success_count += 1
                    print(f"[分类管理] 删除成功：{code}")
                else:
                    fail_count += 1
                    print(f"[分类管理] 删除失败：{code}")
            
            # 刷新数据
            self.load_data()
            
            # 显示结果
            if fail_count == 0:
                QMessageBox.information(self, "成功", f"成功删除 {success_count} 条记录")
            elif success_count == 0:
                QMessageBox.warning(self, "失败", "删除失败，可能该分类已被使用")
            else:
                QMessageBox.warning(self, "部分成功", f"成功删除 {success_count} 条，失败 {fail_count} 条")


class AddCategoryDialog(QDialog):
    """添加分类对话框"""
    
    def __init__(self, category_type, parent=None):
        super().__init__(parent)
        self.category_type = category_type
        self.initUI()
    
    def initUI(self):
        """初始化 UI"""
        self.setWindowTitle(f"添加{'收入' if self.category_type == 'income' else '支出' if self.category_type == 'expense' else '支付'}分类")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 类型提示
        type_name = ""
        if self.category_type == 'income':
            type_name = "收入类型"
        elif self.category_type == 'expense':
            type_name = "支出类型"
        else:
            type_name = "支付方式"
        
        tip_label = QLabel(f"💡 请录入新的{type_name}信息")
        tip_label.setStyleSheet(f"color: {UIStyles.SIDEBAR_SELECTED}; font-weight: bold;")
        layout.addWidget(tip_label)

        # 编码输入
        code_layout = QHBoxLayout()
        code_label = QLabel("编码:")
        code_label.setFixedWidth(50)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("例如：06")
        self.code_input.setMaxLength(4)
        self.code_input.setStyleSheet(UIStyles.input_style())
        code_layout.addWidget(code_label)
        code_layout.addWidget(self.code_input)
        layout.addLayout(code_layout)

        # 名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("名称:")
        name_label.setFixedWidth(50)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(f"例如：兼职{type_name}")
        self.name_input.setMaxLength(20)
        self.name_input.setStyleSheet(UIStyles.input_style())
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.button(QDialogButtonBox.Ok).setStyleSheet(UIStyles.primary_button())
        button_box.button(QDialogButtonBox.Cancel).setStyleSheet(UIStyles.secondary_button())
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)