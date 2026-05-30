# -*- coding: utf-8 -*-
"""
收支流水账页面
按时间顺序展示所有收支记录，自动计算余额
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QComboBox, QDateEdit, QLineEdit,
                             QMessageBox, QFileDialog, QFrame, QStackedWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from models.db_backend import db_manager
from ui.styles import UIStyles
from utils.logger import log_manager
from ui.widgets.toast import Toast


class CashFlowPage(QWidget):
    """收支流水账页面"""
    
    def __init__(self):
        super().__init__()
        self.toast = Toast(self)  # 初始化Toast
        self.initUI()
        self.load_data()
    
    def initUI(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📝 收支流水账")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 18, QFont.Bold))
        layout.addWidget(title_label)
        
        # ========== 查询区域 ==========
        query_frame = QFrame()
        query_frame.setStyleSheet(UIStyles.gray_background())
        query_layout = QHBoxLayout()
        query_layout.setSpacing(10)
        
        # 字段选择
        query_layout.addWidget(QLabel("查询字段:"))
        self.field_combo = QComboBox()
        self.field_combo.addItems(["日期", "单据号", "收支类型", "金额"])
        query_layout.addWidget(self.field_combo)
        
        # 起始日期
        query_layout.addWidget(QLabel("起始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate(2025, 9, 1))
        self.start_date.setCalendarPopup(True)
        query_layout.addWidget(self.start_date)
        
        query_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate(2025, 12, 31))
        self.end_date.setCalendarPopup(True)
        query_layout.addWidget(self.end_date)
        
        # 金额输入
        query_layout.addWidget(QLabel("金额:"))
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("输入金额")
        self.amount_input.setFixedWidth(100)
        query_layout.addWidget(self.amount_input)
        
        # 查询按钮
        self.query_btn = QPushButton("🔍 查询")
        self.query_btn.clicked.connect(self.query_data)
        query_layout.addWidget(self.query_btn)
        
        # 生成流水账按钮
        self.generate_btn = QPushButton("🔄 生成流水账")
        self.generate_btn.clicked.connect(self.generate_cash_flow)
        query_layout.addWidget(self.generate_btn)
        
        query_layout.addStretch()
        query_frame.setLayout(query_layout)
        layout.addWidget(query_frame)
        
        # ========== 数据表格 ==========
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "日期", "序号", "收支类型", "单据号", 
            "收入类型", "收入金额", "支出类型", "支出金额",
            "余额", "支付方式", "备注"
        ])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.Stretch)
        
        # 启用编辑
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # 交替行颜色
        self.table.setAlternatingRowColors(True)
        
        self.table.setStyleSheet(f"""
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {UIStyles.SIDEBAR_SELECTED};
                color: white;
            }}
        """)
        
        layout.addWidget(self.table)
        
        # ========== 底部按钮栏 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_meta = [
            ("🔄 初始化", self.init_data, UIStyles.INFO),
            ("🗑️ 删除", self.delete_records, UIStyles.DANGER),
            ("➕ 增加", self.add_record, UIStyles.SUCCESS),
            ("🔃 复位", self.reset_filters, UIStyles.TEXT_TERTIARY),
            ("☑️ 全选", self.select_all, UIStyles.INFO),
            ("💾 保存", self.save_changes, UIStyles.SUCCESS),
            ("❌ 取消", self.cancel_changes, UIStyles.TEXT_DISABLED),
            ("🚪 退出", self.exit_page, UIStyles.DANGER),
            ("📥 导入", self.import_data, UIStyles.WARNING),
            ("📤 导出", self.export_data, UIStyles.WARNING),
        ]

        for text, handler, color in btn_meta:
            btn = QPushButton(text)
            btn.setStyleSheet(UIStyles.btn_style(color))
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """加载流水账数据（分页：首次500条）"""
        print("[流水账] 加载数据...")

        self.table.setRowCount(0)
        records = db_manager.get_cash_flow(limit=500)
        
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # record: (rq, xh, srzc, djh, sr_code, srje, zc_code, zcje, ye, zf_code, bz)
            rq, xh, srzc, djh, sr_code, srje, zc_code, zcje, ye, zf_code, bz = record
            
            # 日期
            self.table.setItem(row, 0, QTableWidgetItem(str(rq)))
            # 序号
            self.table.setItem(row, 1, QTableWidgetItem(str(xh)))
            # 收支类型
            type_text = "收入" if srzc == 'SR' else "支出"
            type_item = QTableWidgetItem(type_text)
            if srzc == 'SR':
                type_item.setForeground(Qt.darkGreen)
            else:
                type_item.setForeground(Qt.darkRed)
            self.table.setItem(row, 2, type_item)
            # 单据号
            self.table.setItem(row, 3, QTableWidgetItem(djh))
            # 收入类型
            self.table.setItem(row, 4, QTableWidgetItem(sr_code if sr_code else ""))
            # 收入金额
            srje_item = QTableWidgetItem(f"¥{srje:.2f}" if srje else "")
            if srje:
                srje_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 5, srje_item)
            # 支出类型
            self.table.setItem(row, 6, QTableWidgetItem(zc_code if zc_code else ""))
            # 支出金额
            zcje_item = QTableWidgetItem(f"¥{zcje:.2f}" if zcje else "")
            if zcje:
                zcje_item.setForeground(Qt.darkRed)
            self.table.setItem(row, 7, zcje_item)
            # 余额
            ye_item = QTableWidgetItem(f"¥{ye:.2f}" if ye else "¥0.00")
            ye_item.setForeground(Qt.blue)
            self.table.setItem(row, 8, ye_item)
            # 支付方式
            self.table.setItem(row, 9, QTableWidgetItem(zf_code if zf_code else ""))
            # 备注
            self.table.setItem(row, 10, QTableWidgetItem(bz if bz else ""))
        
        print(f"[流水账] 加载完成，共{len(records)}条记录")
    
    def generate_cash_flow(self):
        """生成流水账"""
        print("[流水账] 生成流水账...")
        
        reply = QMessageBox.question(
            self,
            "确认生成",
            "确定要重新生成流水账吗？\n这将清空现有流水账数据并重新计算。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db_manager.generate_cash_flow()
            QMessageBox.information(self, "成功", "流水账已重新生成")
            self.load_data()
    
    def query_data(self):
        """查询数据 - 实现数据库过滤"""
        print("[流水账] 执行查询...")
        
        # 获取筛选条件
        field = self.field_combo.currentText()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        amount = self.amount_input.text()
        
        print(f"[流水账] 查询条件:")
        print(f"  字段：{field}")
        print(f"  日期：{start_date} 至 {end_date}")
        print(f"  金额：{amount}")
        
        # 解析金额范围
        min_amount = None
        max_amount = None
        if amount:
            try:
                if '-' in amount:
                    parts = amount.split('-')
                    min_amount = float(parts[0].strip()) if parts[0].strip() else None
                    max_amount = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
                else:
                    min_amount = float(amount)
                    max_amount = float(amount)
            except ValueError:
                QMessageBox.warning(self, "警告", "金额格式不正确，请输入数字或范围（如：100-500）")
                return
        
        # 调用数据库查询方法
        records = db_manager.get_cash_flow_filtered(
            start_date=start_date if start_date != "1970-01-01" else None,
            end_date=end_date if end_date != "2038-01-19" else None,
            min_amount=min_amount,
            max_amount=max_amount
        )
        
        # 更新表格显示
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            rq, xh, srzc, djh, sr_code, srje, zc_code, zcje, ye, zf_code, bz = record
            
            self.table.setItem(row, 0, QTableWidgetItem(str(rq)))
            self.table.setItem(row, 1, QTableWidgetItem(str(xh)))
            type_text = "收入" if srzc == 'SR' else "支出"
            type_item = QTableWidgetItem(type_text)
            type_item.setForeground(Qt.darkGreen if srzc == 'SR' else Qt.darkRed)
            self.table.setItem(row, 2, type_item)
            self.table.setItem(row, 3, QTableWidgetItem(djh))
            self.table.setItem(row, 4, QTableWidgetItem(sr_code if sr_code else ""))
            srje_item = QTableWidgetItem(f"¥{srje:.2f}" if srje else "")
            if srje:
                srje_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 5, srje_item)
            self.table.setItem(row, 6, QTableWidgetItem(zc_code if zc_code else ""))
            zcje_item = QTableWidgetItem(f"¥{zcje:.2f}" if zcje else "")
            if zcje:
                zcje_item.setForeground(Qt.darkRed)
            self.table.setItem(row, 7, zcje_item)
            ye_item = QTableWidgetItem(f"¥{ye:.2f}" if ye else "¥0.00")
            ye_item.setForeground(Qt.blue)
            self.table.setItem(row, 8, ye_item)
            self.table.setItem(row, 9, QTableWidgetItem(zf_code if zf_code else ""))
            self.table.setItem(row, 10, QTableWidgetItem(bz if bz else ""))
        
        # 显示查询结果提示
        row_count = len(records)
        if row_count > 0:
            self.toast.success(f"查询完成，共 {row_count} 条记录", 2000)
        else:
            self.toast.warning("未找到符合条件的记录", 2500)
    
    def delete_records(self):
        """删除选中的记录 - 连接数据库"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的行！")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 条记录吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            failed_count = 0
            
            for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                row = index.row()
                xh_item = self.table.item(row, 1)
                if xh_item:
                    try:
                        xh = int(xh_item.text())
                        if db_manager.delete_cash_flow_by_xh(xh):
                            self.table.removeRow(row)
                            deleted_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        log_manager.error(f"[流水账] 删除失败：行{row}, 错误：{e}")
                        failed_count += 1
            
            if failed_count == 0:
                self.toast.success(f"✅ 成功删除 {deleted_count} 条记录", 2000)
            else:
                self.toast.warning(f"已删除 {deleted_count} 条，失败 {failed_count} 条", 3000)
    
    def add_record(self):
        """添加记录"""
        print("[流水账] 添加记录")
        QMessageBox.information(self, "提示", "流水账由系统自动生成，不支持手动添加\n请通过收入/支出记账功能添加记录后再生成流水账")
    
    def on_item_double_clicked(self, item):
        """双击编辑单元格 - 连接数据库"""
        row = item.row()
        col = item.column()
        
        if col >= 10:  # 只允许编辑备注字段（第11列，索引10）
            current_text = item.text()
            new_text, ok = QLineEdit.getText(
                self, 
                "编辑流水账", 
                "请输入新备注：",
                QLineEdit.Normal,
                current_text
            )
            
            if ok and new_text:
                # 获取序号
                xh_item = self.table.item(row, 1)
                if xh_item:
                    try:
                        xh = int(xh_item.text())
                        # 调用数据库更新方法
                        if db_manager.update_cash_flow_remark(xh, new_text):
                            item.setText(new_text)
                            self.toast.success("备注已更新", 1500)
                        else:
                            QMessageBox.warning(self, "警告", "更新失败，请检查数据库连接")
                    except Exception as e:
                        log_manager.error(f"[流水账] 更新备注失败：{e}")
                        QMessageBox.critical(self, "错误", f"更新失败：{str(e)}")
    
    def init_data(self):
        """初始化数据"""
        print("[流水账] 初始化数据")
        self.load_data()
    
    def reset_filters(self):
        """重置筛选条件"""
        print("[流水账] 重置筛选")
        self.start_date.setDate(QDate(2025, 9, 1))
        self.end_date.setDate(QDate(2025, 12, 31))
        self.amount_input.clear()
        self.field_combo.setCurrentIndex(0)
    
    def select_all(self):
        """全选"""
        print("[流水账] 全选")
        self.table.selectAll()
    
    def save_changes(self):
        """保存修改"""
        print("[流水账] 保存修改")
        QMessageBox.information(self, "提示", "保存功能待开发")
    
    def cancel_changes(self):
        """取消修改"""
        print("[流水账] 取消修改")
        self.load_data()
    
    def exit_page(self):
        """退出页面"""
        print("[流水账] 退出页面")
        # 切换到首页
        parent = self.parent()
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()
        
        if parent:
            stacked_widget = parent.findChild(QStackedWidget)
            if stacked_widget:
                stacked_widget.setCurrentIndex(0)
    
    def import_data(self):
        """导入数据"""
        print("[流水账] 导入数据")
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "导入 Excel 文件", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            print(f"[流水账] 选择文件：{file_path}")
            QMessageBox.information(self, "导入", f"准备从 {file_path} 导入数据\n导入功能待开发")
    
    def export_data(self):
        """导出数据"""
        print("[流水账] 导出数据")
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出 Excel 文件", 
            "收支流水账.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            print(f"[流水账] 导出到：{file_path}")
            QMessageBox.information(self, "导出", f"数据将导出到 {file_path}\n导出功能待开发")
