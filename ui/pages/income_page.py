# -*- coding: utf-8 -*-
"""
收入记账管理页面 - 优化版（智能默认值）
记录和管理收入数据
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QComboBox, QDateEdit, QLineEdit,
                             QMessageBox, QFileDialog, QFrame, QInputDialog,
                             QStackedWidget, QDialog, QFormLayout, QDoubleSpinBox,
                             QToolButton)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator

from models.db_backend import db_manager
from models.config import config
from ui.styles import UIStyles
from utils.excel_utils import excel_handler
from utils.csv_utils import csv_handler
from utils.logger import log_manager
from utils.ai_classifier import AIClassifier
from ui.widgets.toast import Toast


class IncomePage(QWidget):
    """收入记账管理页面"""
    
    def __init__(self):
        super().__init__()
        self.ai_classifier = AIClassifier()
        self.initUI()
        # 创建Toast组件
        self.toast = Toast(self)
        self.load_data()
    
    def initUI(self):
        """初始化 UI - 智能默认值"""
        layout = QVBoxLayout()
        layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("💰 收入记账管理")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 18, QFont.Bold))
        layout.addWidget(title_label)
        # ========== 筛选栏 ==========
        filter_frame = QFrame()
        filter_frame.setStyleSheet(UIStyles.filter_frame_style())
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        # 日期范围 - 智能默认本月
        today = QDate.currentDate()
        first_day = QDate(today.year(), today.month(), 1)
        last_day = QDate(today.year(), today.month(), today.daysInMonth())
        
        filter_layout.addWidget(QLabel("起始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(first_day)  # 默认本月第一天
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(last_day)  # 默认本月最后一天
        self.end_date.setCalendarPopup(True)
        filter_layout.addWidget(self.end_date)
        
        # 金额范围 - 智能提示平均值
        filter_layout.addWidget(QLabel("金额:"))
        self.min_amount = QLineEdit()
        avg_amount = self._get_average_amount()
        if avg_amount:
            self.min_amount.setPlaceholderText(f"最小 (平均: ¥{avg_amount:.0f})")
        else:
            self.min_amount.setPlaceholderText("最小")
        self.min_amount.setFixedWidth(100)
        self.min_amount.setValidator(QDoubleValidator())
        filter_layout.addWidget(self.min_amount)
        
        filter_layout.addWidget(QLabel("-"))
        
        self.max_amount = QLineEdit()
        if avg_amount:
            self.max_amount.setPlaceholderText(f"最大 (平均: ¥{avg_amount:.0f})")
        else:
            self.max_amount.setPlaceholderText("最大")
        self.max_amount.setFixedWidth(100)
        self.max_amount.setValidator(QDoubleValidator())
        filter_layout.addWidget(self.max_amount)
        
        # 支付方式下拉框 - 记住上次选择
        filter_layout.addWidget(QLabel("支付:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItem("全部", "all")
        payment_methods = db_manager.get_payment_methods()
        for code, name in payment_methods:
            self.payment_combo.addItem(name, code)
        
        # 恢复上次选择的支付方式
        last_payment = config.get('last_income_payment_method', 'all')
        self.payment_combo.setCurrentText(last_payment)
        
        filter_layout.addWidget(self.payment_combo)
        
        # 收入类型下拉框 - 记住上次选择
        filter_layout.addWidget(QLabel("类型:"))
        self.income_type_combo = QComboBox()
        self.income_type_combo.addItem("全部", "all")
        income_types = db_manager.get_income_types()
        for code, name in income_types:
            self.income_type_combo.addItem(name, code)
        
        # 恢复上次选择的收入类型
        last_type = config.get('last_income_type', 'all')
        self.income_type_combo.setCurrentText(last_type)
        
        filter_layout.addWidget(self.income_type_combo)
        
        # 查询按钮
        self.query_btn = QPushButton("🔍 查询")
        self.query_btn.clicked.connect(self.query_data)
        filter_layout.addWidget(self.query_btn)
        
        filter_layout.addStretch()
        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)
        
        # ========== 数据表格 ==========
        self.table = QTableWidget()
        self.table.setColumnCount(10)  # 增加一列用于复选框
        self.table.setHorizontalHeaderLabels([
            "选择", "账套号", "单据号", "日期", "收入类型编码", 
            "收入类型名称", "金额", "支付方式编码", 
            "支付方式名称", "备注"
        ])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 选择列
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Stretch)
        
        # 启用编辑
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # 交替行颜色
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # ========== 按钮栏（分组布局）==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_meta = [
            ("🔄 初始化", self.load_data, UIStyles.INFO),
            ("➕ 增加", self.add_record, UIStyles.SUCCESS),
            ("🔃 复位", self.reset_filters, UIStyles.TEXT_TERTIARY),
            ("🗑️ 批量删除", self.batch_delete, UIStyles.DANGER),
            ("💳 改支付", self.batch_change_payment, UIStyles.INFO),
            ("📂 改类型", self.batch_change_type, UIStyles.SUCCESS),
            ("☑️ 全选", self.select_all, UIStyles.INFO),
            ("📥 导入", self.import_data, UIStyles.WARNING),
            ("📤 导出", self.export_data, UIStyles.WARNING),
        ]

        for text, handler, color in btn_meta:
            btn = QPushButton(text)
            btn.setStyleSheet(UIStyles.btn_style(color))
            btn.clicked.connect(handler)
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def load_data(self):
        """加载收入数据（分页：首次500条，避免全量加载）"""
        print("[收入管理] 加载数据...")

        self.table.setRowCount(0)
        records = db_manager.get_income_records(limit=500)

        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # record: (djh, rq, sr_name, je, zf_name, bz, sr_code, zf_code) - 8个字段
            djh, rq, sr_name, je, zf_name, bz, sr_code, zf_code = record
            
            # 第0列：复选框
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, checkbox)
            
            # 其他列（索引+1）
            self.table.setItem(row, 1, QTableWidgetItem(db_manager.current_account))  # zth
            self.table.setItem(row, 2, QTableWidgetItem(djh))
            self.table.setItem(row, 3, QTableWidgetItem(str(rq)))
            # 使用从数据库获取的编码
            self.table.setItem(row, 4, QTableWidgetItem(sr_code if sr_code else "--"))  # sr_code
            self.table.setItem(row, 5, QTableWidgetItem(sr_name if sr_name else ""))
            self.table.setItem(row, 6, QTableWidgetItem(f"¥{je:.2f}" if je else "¥0.00"))
            self.table.setItem(row, 7, QTableWidgetItem(zf_code if zf_code else "--"))  # zf_code
            self.table.setItem(row, 8, QTableWidgetItem(zf_name if zf_name else ""))
            self.table.setItem(row, 9, QTableWidgetItem(bz if bz else ""))
        
        print(f"[收入管理] 加载完成，共{len(records)}条记录")
    
    def get_selected_rows(self):
        """获取所有选中的行号"""
        selected_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                selected_rows.append(row)
        return selected_rows
    
    def batch_delete(self):
        """批量删除选中记录"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            self.toast.warning("请先勾选要删除的记录！", 2000)
            return
        
        reply = QMessageBox.question(
            self,
            "确认批量删除",
            f"⚠️ 确定要删除选中的 {len(selected_rows)} 条记录吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                deleted_count = 0
                failed_count = 0
                
                for row in selected_rows:
                    # 获取单据号（第2列，索引从0开始）
                    djh_item = self.table.item(row, 2)
                    if djh_item:
                        djh = djh_item.text()
                        # 调用数据库删除方法
                        if db_manager.delete_income_record(djh):
                            deleted_count += 1
                        else:
                            failed_count += 1
                
                # 刷新表格
                self.load_data()
                
                if failed_count == 0:
                    self.toast.success(f"✅ 成功删除 {deleted_count} 条记录", 2000)
                else:
                    self.toast.warning(f"已删除 {deleted_count} 条，失败 {failed_count} 条", 3000)
                    
            except Exception as e:
                log_manager.error(f"[收入管理] 批量删除失败: {e}")
                QMessageBox.critical(self, "错误", f"批量删除失败：{str(e)}")
    
    def batch_change_payment(self):
        """批量修改支付方式"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            self.toast.warning("请先勾选要修改的记录！", 2000)
            return
        
        # 创建支付方式选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("🔄 批量修改支付方式")
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.BG_GRAY_50};
            }}
            QPushButton {{
                background-color: {UIStyles.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.PRIMARY_HOVER};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # 说明文字
        info_label = QLabel(f"将为选中的 <b>{len(selected_rows)}</b> 条记录统一修改支付方式")
        info_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        info_label.setStyleSheet(f"color: {UIStyles.SIDEBAR_BG}; padding: 10px; background-color: white; border-radius: 6px;")
        layout.addWidget(info_label)
        
        # 支付方式选择
        form_layout = QFormLayout()
        payment_combo = QComboBox()
        payment_methods = db_manager.get_payment_methods()
        for code, name in payment_methods:
            payment_combo.addItem(name, code)
        payment_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        form_layout.addRow("选择新的支付方式：", payment_combo)
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet(UIStyles.secondary_button())
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("✅ 确定")
        ok_btn.setStyleSheet(UIStyles.primary_button())

        def on_ok():
            new_payment_code = payment_combo.currentData()
            new_payment_name = payment_combo.currentText()
            
            try:
                updated_count = 0
                failed_count = 0
                
                for row in selected_rows:
                    djh_item = self.table.item(row, 2)
                    if djh_item:
                        djh = djh_item.text()
                        # 调用数据库更新方法
                        if db_manager.update_income_payment(djh, new_payment_code):
                            updated_count += 1
                        else:
                            failed_count += 1
                
                # 刷新表格
                self.load_data()
                
                if failed_count == 0:
                    QMessageBox.information(
                        dialog, 
                        "成功", 
                        f"✅ 已更新 {updated_count} 条记录的支付方式为：<b>{new_payment_name}</b>"
                    )
                    dialog.accept()
                else:
                    QMessageBox.warning(
                        dialog, 
                        "部分成功", 
                        f"已更新 {updated_count} 条，失败 {failed_count} 条"
                    )
                    
            except Exception as e:
                log_manager.error(f"[收入管理] 批量修改支付方式失败: {e}")
                QMessageBox.critical(dialog, "错误", f"批量修改失败：{str(e)}")
        
        ok_btn.clicked.connect(on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def batch_change_type(self):
        """批量修改收入类型"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            self.toast.warning("请先勾选要修改的记录！", 2000)
            return
        
        # 创建收入类型选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("🔄 批量修改收入类型")
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.BG_GRAY_50};
            }}
            QPushButton {{
                background-color: {UIStyles.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.SUCCESS_HOVER};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # 说明文字
        info_label = QLabel(f"将为选中的 <b>{len(selected_rows)}</b> 条记录统一修改收入类型")
        info_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        info_label.setStyleSheet(f"color: {UIStyles.SIDEBAR_BG}; padding: 10px; background-color: white; border-radius: 6px;")
        layout.addWidget(info_label)
        
        # 收入类型选择
        form_layout = QFormLayout()
        type_combo = QComboBox()
        income_types = db_manager.get_income_types()
        for code, name in income_types:
            type_combo.addItem(name, code)
        type_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        form_layout.addRow("选择新的收入类型：", type_combo)
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet(UIStyles.secondary_button())
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("✅ 确定")
        ok_btn.setStyleSheet(UIStyles.success_button())

        def on_ok():
            new_type_code = type_combo.currentData()
            new_type_name = type_combo.currentText()
            
            try:
                updated_count = 0
                failed_count = 0
                
                for row in selected_rows:
                    djh_item = self.table.item(row, 2)
                    if djh_item:
                        djh = djh_item.text()
                        # 调用数据库更新方法
                        if db_manager.update_income_type(djh, new_type_code):
                            updated_count += 1
                        else:
                            failed_count += 1
                
                # 刷新表格
                self.load_data()
                
                if failed_count == 0:
                    QMessageBox.information(
                        dialog, 
                        "成功", 
                        f"✅ 已更新 {updated_count} 条记录的收入类型为：<b>{new_type_name}</b>"
                    )
                    dialog.accept()
                else:
                    QMessageBox.warning(
                        dialog, 
                        "部分成功", 
                        f"已更新 {updated_count} 条，失败 {failed_count} 条"
                    )
                    
            except Exception as e:
                log_manager.error(f"[收入管理] 批量修改收入类型失败: {e}")
                QMessageBox.critical(dialog, "错误", f"批量修改失败：{str(e)}")
        
        ok_btn.clicked.connect(on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def query_data(self):
        """查询数据 - 实现数据库筛选"""
        print("[收入管理] 执行查询...")
        
        # 获取筛选条件
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        min_amount_text = self.min_amount.text()
        max_amount_text = self.max_amount.text()
        payment_code = self.payment_combo.currentData()
        income_type_code = self.income_type_combo.currentData()
        
        # 保存用户的选择，下次使用
        config.set_ui_setting('last_income_payment_method', self.payment_combo.currentText())
        config.set_ui_setting('last_income_type', self.income_type_combo.currentText())
        
        print(f"[收入管理] 查询条件:")
        print(f"  日期：{start_date} 至 {end_date}")
        print(f"  金额：{min_amount_text} - {max_amount_text}")
        print(f"  支付方式：{payment_code}")
        print(f"  收入类型：{income_type_code}")
        
        # 构建筛选条件
        filters = {}
        if start_date and start_date != "1970-01-01":
            filters['start_date'] = start_date
        if end_date and end_date != "2038-01-19":
            filters['end_date'] = end_date
        if min_amount_text:
            try:
                filters['min_amount'] = float(min_amount_text)
            except ValueError:
                pass
        if max_amount_text:
            try:
                filters['max_amount'] = float(max_amount_text)
            except ValueError:
                pass
        if payment_code:
            filters['payment_code'] = payment_code
        if income_type_code:
            filters['income_type_code'] = income_type_code
        
        # 调用数据库查询方法
        records = db_manager.get_income_records(filters=filters if filters else None)
        
        # 更新表格显示
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            djh, rq, sr_name, je, zf_name, bz, sr_code, zf_code = record
            
            # 第0列：复选框
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, checkbox)
            
            # 其他列
            self.table.setItem(row, 1, QTableWidgetItem(db_manager.current_account))  # zth
            self.table.setItem(row, 2, QTableWidgetItem(djh))
            self.table.setItem(row, 3, QTableWidgetItem(str(rq)))
            self.table.setItem(row, 4, QTableWidgetItem(sr_code if sr_code else "--"))
            self.table.setItem(row, 5, QTableWidgetItem(sr_name if sr_name else ""))
            self.table.setItem(row, 6, QTableWidgetItem(f"¥{je:.2f}" if je else "¥0.00"))
            self.table.setItem(row, 7, QTableWidgetItem(zf_code if zf_code else "--"))
            self.table.setItem(row, 8, QTableWidgetItem(zf_name if zf_name else ""))
            self.table.setItem(row, 9, QTableWidgetItem(bz if bz else ""))
        
        # 显示查询结果提示
        row_count = len(records)
        if row_count > 0:
            self.toast.success(f"查询完成，共 {row_count} 条记录", 2000)
        else:
            self.toast.warning("未找到符合条件的记录", 2500)
    
    def add_record(self):
        """新增记录 - 智能填充对话框"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                     QComboBox, QDateEdit, QLineEdit, QPushButton,
                                     QDoubleSpinBox, QFormLayout)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("💰 新增收入记录")
        dialog.setFixedSize(500, 400)
        dialog.setStyleSheet(f"QDialog {{ background-color: {UIStyles.BG_GRAY_50}; }}")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📝 填写收入信息")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 14, QFont.Bold))
        title_label.setStyleSheet(f"color: {UIStyles.SUCCESS};")
        layout.addWidget(title_label)
        
        # 表单区域
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 日期 - 默认今天
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        form_layout.addRow("📅 日期：", date_edit)
        
        # 收入类型 - 记住上次选择 + AI 推荐按钮
        type_row = QHBoxLayout()
        type_combo = QComboBox()
        income_types = db_manager.get_income_types()
        last_type_code = config.get('last_income_type', '')
        last_type_index = 0

        for i, (code, name) in enumerate(income_types):
            type_combo.addItem(name, code)
            if code == last_type_code:
                last_type_index = i

        type_combo.setCurrentIndex(last_type_index)
        type_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        type_row.addWidget(type_combo, 1)

        ai_recommend_btn = QToolButton()
        ai_recommend_btn.setText("✨")
        ai_recommend_btn.setToolTip("AI 智能推荐分类")
        ai_recommend_btn.setCursor(Qt.PointingHandCursor)
        ai_recommend_btn.setFixedSize(30, 30)
        ai_recommend_btn.setStyleSheet(f"""
            QToolButton {{
                border: none;
                background-color: {UIStyles.PRIMARY_LIGHT};
                border-radius: 15px;
                font-size: 16px;
            }}
            QToolButton:hover {{
                background-color: {UIStyles.PRIMARY};
            }}
        """)
        ai_recommend_btn.clicked.connect(lambda: self._ai_recommend_category(remark_input, type_combo, is_income=True))
        type_row.addWidget(ai_recommend_btn)

        form_layout.addRow("📂 类型：", type_row)
        
        # 金额 - 光标自动定位
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0.01, 999999.99)
        amount_spin.setValue(0.0)
        amount_spin.setPrefix("¥ ")
        amount_spin.setDecimals(2)
        amount_spin.setFont(QFont(UIStyles.FONT_FAMILY, 12, QFont.Bold))
        amount_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                padding: 8px;
                border: 2px solid {UIStyles.SUCCESS};
                border-radius: 6px;
                background-color: white;
            }}
            QDoubleSpinBox:focus {{
                border-color: {UIStyles.SUCCESS_HOVER};
            }}
        """)
        form_layout.addRow("💵 金额：", amount_spin)
        
        # 支付方式 - 记住上次选择
        payment_combo = QComboBox()
        payment_methods = db_manager.get_payment_methods()
        last_payment_code = config.get('last_income_payment_method', '')
        last_payment_index = 0
        
        for i, (code, name) in enumerate(payment_methods):
            payment_combo.addItem(name, code)
            if code == last_payment_code:
                last_payment_index = i
        
        payment_combo.setCurrentIndex(last_payment_index)
        payment_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        form_layout.addRow("💳 支付：", payment_combo)
        
        # 备注
        remark_input = QLineEdit()
        remark_input.setPlaceholderText("可选备注信息...")
        remark_input.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        remark_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 6px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {UIStyles.SUCCESS};
            }}
        """)
        form_layout.addRow("📝 备注：", remark_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✅ 确定")
        ok_btn.setStyleSheet(UIStyles.success_button())

        def on_ok():
            """确定按钮 - 保存到数据库"""
            # 获取表单数据
            rq = date_edit.date().toString("yyyy-MM-dd")
            sr_code = type_combo.currentData()
            je = amount_spin.value()
            zf_code = payment_combo.currentData()
            bz = remark_input.text().strip()
            
            # 验证
            if je <= 0:
                QMessageBox.warning(dialog, "验证失败", "❌ 金额必须大于0！")
                amount_spin.setFocus()
                return
            
            if not sr_code:
                QMessageBox.warning(dialog, "验证失败", "❌ 请选择收入类型！")
                return
            
            if not zf_code:
                QMessageBox.warning(dialog, "验证失败", "❌ 请选择支付方式！")
                return
            
            try:
                # 保存到数据库
                success = db_manager.add_income_record(
                    rq=rq,
                    sr_code=sr_code,
                    je=je,
                    zf_code=zf_code,
                    bz=bz
                )
                
                if success:
                    # 保存用户选择，下次使用
                    config.set_ui_setting('last_income_type', sr_code)
                    config.set_ui_setting('last_income_payment_method', zf_code)
                    
                    QMessageBox.information(
                        dialog, 
                        "成功", 
                        f"✅ 收入记录添加成功！\n\n"
                        f"日期：{rq}\n"
                        f"类型：{type_combo.currentText()}\n"
                        f"金额：¥{je:.2f}\n"
                        f"支付：{payment_combo.currentText()}"
                    )
                    dialog.accept()

                    # 审计日志
                    from utils.auth_manager import AuthManager
                    AuthManager()._write_audit_log(db_manager.current_account, "add_income", "", f"金额: {je:.2f}, 类型: {sr_code}")

                    # 刷新表格
                    self.load_data()
                else:
                    QMessageBox.critical(dialog, "错误", "❌ 保存失败，请重试！")
                    
            except Exception as e:
                log_manager.error(f"[收入管理] 新增记录失败: {e}")
                QMessageBox.critical(dialog, "错误", f"❌ 保存失败：\n{str(e)}")
        
        ok_btn.clicked.connect(on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # 光标自动定位到金额输入框
        amount_spin.setFocus()
        amount_spin.selectAll()
        
        dialog.exec_()

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
                djh_item = self.table.item(row, 2)  # 单据号在第2列（索引从0开始）
                if djh_item:
                    try:
                        djh = djh_item.text()
                        if db_manager.delete_income_record(djh):
                            self.table.removeRow(row)
                            deleted_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        log_manager.error(f"[收入管理] 删除失败：行{row}, 错误：{e}")
                        failed_count += 1
            
            if failed_count == 0:
                self.toast.success(f"✅ 成功删除 {deleted_count} 条记录", 2000)
            else:
                self.toast.warning(f"已删除 {deleted_count} 条，失败 {failed_count} 条", 3000)
    
    def on_item_double_clicked(self, item):
        """双击编辑单元格并保存到数据库"""
        row = item.row()
        col = item.column()
        
        # 只允许编辑特定字段（收入类型名称、金额、支付方式名称、备注）
        if col in [5, 6, 8, 9]:  # 列索引：5=收入类型名称, 6=金额, 8=支付方式名称, 9=备注
            current_text = item.text()
            
            # 根据列类型设置不同的输入方式
            if col == 6:  # 金额列 - 使用数字输入
                from PyQt5.QtWidgets import QDoubleSpinBox
                dialog = QDialog(self)
                dialog.setWindowTitle("✏️ 编辑金额")
                dialog.setFixedSize(350, 180)
                
                layout = QVBoxLayout(dialog)
                layout.setContentsMargins(20, 15, 20, 15)
                
                label = QLabel("请输入新的金额：")
                label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
                layout.addWidget(label)
                
                amount_spin = QDoubleSpinBox()
                amount_spin.setRange(0.01, 999999.99)
                amount_spin.setValue(float(current_text.replace('¥', '').strip()) if current_text else 0)
                amount_spin.setPrefix("¥ ")
                amount_spin.setDecimals(2)
                amount_spin.setFont(QFont(UIStyles.FONT_FAMILY, 12, QFont.Bold))
                layout.addWidget(amount_spin)
                
                btn_layout = QHBoxLayout()
                cancel_btn = QPushButton("取消")
                cancel_btn.clicked.connect(dialog.reject)
                ok_btn = QPushButton("确定")
                ok_btn.setStyleSheet(UIStyles.success_button())
                
                def save_amount():
                    new_value = f"¥{amount_spin.value():.2f}"
                    item.setText(new_value)
                    
                    # 保存到数据库
                    djh_item = self.table.item(row, 2)
                    if djh_item:
                        djh = djh_item.text()
                        try:
                            # 获取当前记录的完整数据
                            sr_code_item = self.table.item(row, 4)
                            zf_code_item = self.table.item(row, 7)
                            bz_item = self.table.item(row, 9)
                            
                            update_data = {
                                'rq': self.table.item(row, 3).text(),
                                'sr_code': sr_code_item.text() if sr_code_item else '',
                                'je': amount_spin.value(),
                                'zf_code': zf_code_item.text() if zf_code_item else '',
                                'bz': bz_item.text() if bz_item else ''
                            }
                            
                            if db_manager.update_income_record(djh, update_data):
                                self.toast.success("✅ 金额已更新", 1500)
                            else:
                                self.toast.warning("⚠️ 保存失败", 2000)
                        except Exception as e:
                            log_manager.error(f"[收入管理] 保存金额失败: {e}")
                            self.toast.error(f"❌ 保存失败: {str(e)}", 3000)
                    
                    dialog.accept()
                
                ok_btn.clicked.connect(save_amount)
                btn_layout.addWidget(cancel_btn)
                btn_layout.addWidget(ok_btn)
                layout.addLayout(btn_layout)
                
                dialog.exec_()
                
            else:  # 文本列 - 使用文本输入
                new_text, ok = QInputDialog.getText(
                    self, 
                    "✏️ 编辑收入记录", 
                    "请输入新值：",
                    QLineEdit.Normal,
                    current_text
                )
                
                if ok and new_text:
                    item.setText(new_text)
                    
                    # 保存到数据库
                    djh_item = self.table.item(row, 2)
                    if djh_item:
                        djh = djh_item.text()
                        try:
                            # 根据列确定要更新的字段
                            if col == 5:  # 收入类型名称（需要找到对应的编码）
                                # 这里简化处理，实际应该通过名称查找编码
                                self.toast.info("💡 提示：请直接修改收入类型编码列", 2000)
                            elif col == 8:  # 支付方式名称
                                self.toast.info("💡 提示：请直接修改支付方式编码列", 2000)
                            elif col == 9:  # 备注
                                # 获取当前记录的完整数据
                                rq_item = self.table.item(row, 3)
                                sr_code_item = self.table.item(row, 4)
                                je_item = self.table.item(row, 6)
                                zf_code_item = self.table.item(row, 7)
                                
                                update_data = {
                                    'rq': rq_item.text() if rq_item else '',
                                    'sr_code': sr_code_item.text() if sr_code_item else '',
                                    'je': float(je_item.text().replace('¥', '').strip()) if je_item else 0,
                                    'zf_code': zf_code_item.text() if zf_code_item else '',
                                    'bz': new_text
                                }
                                
                                if db_manager.update_income_record(djh, update_data):
                                    self.toast.success("✅ 备注已更新", 1500)
                                else:
                                    self.toast.warning("⚠️ 保存失败", 2000)
                                    
                        except Exception as e:
                            log_manager.error(f"[收入管理] 保存修改失败: {e}")
                            self.toast.error(f"❌ 保存失败: {str(e)}", 3000)
    
    def init_data(self):
        """初始化数据"""
        print("[收入管理] 初始化数据")
        self.load_data()
    
    def reset_filters(self):
        """重置筛选条件"""
        print("[收入管理] 重置筛选")
        self.start_date.setDate(QDate(2025, 9, 1))
        self.end_date.setDate(QDate(2025, 12, 31))
        self.min_amount.clear()
        self.max_amount.clear()
        self.payment_combo.setCurrentIndex(0)
        self.income_type_combo.setCurrentIndex(0)
    
    def select_all(self):
        """全选"""
        print("[收入管理] 全选")
        self.table.selectAll()
    
    def save_changes(self):
        """保存修改 - 刷新数据"""
        print("[收入管理] 保存修改")
        
        # 由于双击编辑时已经实时保存到数据库，这里只需要刷新显示
        try:
            self.load_data()
            self.toast.success("✅ 数据已刷新", 1500)
        except Exception as e:
            log_manager.error(f"[收入管理] 刷新数据失败: {e}")
            self.toast.error(f"❌ 刷新失败: {str(e)}", 2000)
    
    def cancel_changes(self):
        """取消修改"""
        print("[收入管理] 取消修改")
        self.load_data()
    
    def exit_page(self):
        """退出页面"""
        print("[收入管理] 退出页面")
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
        print("[收入管理] 导入数据")
        
        # 选择文件类型
        reply = QMessageBox.question(
            self,
            "选择文件格式",
            "请选择导入文件的格式:",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        if reply == QMessageBox.Yes:
            # Excel 导入
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "导入 Excel 文件",
                "",
                "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
            
            if file_path:
                try:
                    # 读取 Excel
                    ws = excel_handler.read_workbook(file_path)
                    data = excel_handler.get_all_data(min_row=2)
                    
                    print(f"[收入管理] 读取 Excel：{len(data)}条记录")
                    
                    # TODO: 解析数据并添加到数据库
                    QMessageBox.information(
                        self, 
                        "导入成功", 
                        f"成功读取 {len(data)} 条记录\n数据添加功能待开发"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "导入失败",
                        f"读取文件失败:\n{str(e)}"
                    )
        else:
            # CSV 导入
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "导入 CSV 文件",
                "",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                try:
                    # 检测编码
                    encoding = csv_handler.detect_encoding(file_path)
                    print(f"[收入管理] 检测到编码：{encoding}")
                    
                    # 读取 CSV
                    records = csv_handler.import_income_records(file_path, encoding)
                    
                    QMessageBox.information(
                        self,
                        "导入成功",
                        f"成功导入 {len(records)} 条有效记录\n数据添加功能待开发"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "导入失败",
                        f"读取文件失败:\n{str(e)}"
                    )
    
    def export_data(self):
        """导出数据"""
        print("[收入管理] 导出数据")
        
        # 选择导出格式
        reply = QMessageBox.question(
            self,
            "选择导出格式",
            "请选择导出文件的格式:",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        if reply == QMessageBox.Yes:
            # Excel 导出
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出 Excel 文件",
                "收入记录.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                try:
                    # 获取当前表格数据
                    records = []
                    for row in range(self.table.rowCount()):
                        record = []
                        for col in range(1, 7):  # 跳过账套号
                            item = self.table.item(row, col)
                            record.append(item.text() if item else "")
                        records.append(tuple(record))
                    
                    # 使用 excel_handler 导出
                    excel_handler.export_income_records(records, file_path)
                    
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"数据已导出到:\n{file_path}"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "导出失败",
                        f"导出文件失败:\n{str(e)}"
                    )
        else:
            # CSV 导出
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出 CSV 文件",
                "收入记录.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                try:
                    # 获取当前表格数据
                    records = []
                    for row in range(self.table.rowCount()):
                        record = []
                        for col in range(1, 7):
                            item = self.table.item(row, col)
                            record.append(item.text() if item else "")
                        records.append(tuple(record))
                    
                    # 使用 csv_handler 导出
                    csv_handler.export_income_records(records, file_path)
                    
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"数据已导出到:\n{file_path}"
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "导出失败",
                        f"导出文件失败:\n{str(e)}"
                    )

    def _ai_recommend_category(self, remark_input, type_combo, is_income=True):
        """AI 智能推荐分类"""
        remark = remark_input.text().strip()
        if not remark:
            self.toast.warning("请先输入备注信息", 2000)
            return

        categories = [type_combo.itemText(i) for i in range(type_combo.count())]
        if not categories:
            return

        self.toast.loading("AI 正在分析...")
        result = self.ai_classifier.recommend_category(remark, categories, is_income=is_income)
        if result:
            idx = type_combo.findText(result)
            if idx >= 0:
                type_combo.setCurrentIndex(idx)
                self.toast.success(f"AI 推荐: {result}", 2500)
            else:
                self.toast.warning("AI 推荐结果不在列表中", 2500)
        else:
            self.toast.info("AI 无法推荐，请手动选择", 2500)

    def _get_average_amount(self):
        """获取平均金额（用于智能提示——SQL AVG避免全表扫描）"""
        try:
            avg = db_manager.get_income_avg_amount()
            return avg if avg > 0 else None
        except Exception as e:
            log_manager.debug(f"[收入管理] 计算平均金额失败: {e}")
            return None
