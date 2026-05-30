# -*- coding: utf-8 -*-
"""
支出记账管理页面| 记录和管理支出数据
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QComboBox, QDateEdit, QLineEdit,
                             QMessageBox, QFileDialog, QFrame, QStackedWidget, QDialog,
                             QFormLayout, QDoubleSpinBox, QToolButton)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QDoubleValidator

from models.db_backend import db_manager
from models.config import config
from models.budget_manager import BudgetManager, BudgetAlert
from ui.styles import UIStyles
from utils.logger import log_manager
from utils.ai_classifier import AIClassifier
from ui.widgets.toast import Toast


class ExpensePage(QWidget):
    """支出记账管理页面"""
    
    def __init__(self):
        super().__init__()
        # 初始化预算管理
        self.budget_manager = BudgetManager(db_manager)
        self.budget_alert = BudgetAlert(self.budget_manager)
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
        title_label = QLabel("💸 支出记账管理")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 18, QFont.Bold))
        layout.addWidget(title_label)
        
        # ========== 筛选栏 ==========
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background-color: {UIStyles.BG_GRAY_50}; border-radius: 5px; padding: 10px;")
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
        last_payment = config.get('last_expense_payment_method', 'all')
        self.payment_combo.setCurrentText(last_payment)
        
        filter_layout.addWidget(self.payment_combo)
        
        # 支出类型下拉框 - 记住上次选择
        filter_layout.addWidget(QLabel("类型:"))
        self.expense_type_combo = QComboBox()
        self.expense_type_combo.addItem("全部", "all")
        expense_types = db_manager.get_expense_types()
        for code, name in expense_types:
            self.expense_type_combo.addItem(name, code)
        
        # 恢复上次选择的支出类型
        last_type = config.get('last_expense_type', 'all')
        self.expense_type_combo.setCurrentText(last_type)
        
        filter_layout.addWidget(self.expense_type_combo)
        
        # 查询按钮
        self.query_btn = QPushButton("🔍 查询")
        self.query_btn.clicked.connect(self.query_data)
        filter_layout.addWidget(self.query_btn)
        
        filter_layout.addStretch()
        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)
        
        # ========== 数据表格 ==========
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "", "账套号", "单据号", "日期", "支出类型编码",
            "支出类型名称", "金额", "支付方式编码",
            "支付方式名称", "备注"
        ])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        
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
            ("💾 保存", self.save_changes, UIStyles.INFO),
            ("🔃 复位", self.reset_filters, UIStyles.TEXT_TERTIARY),
            ("🗑️ 删除", self.batch_delete, UIStyles.DANGER),
            ("💳 改支付", self.batch_change_payment, UIStyles.INFO),
            ("📂 改类型", self.batch_change_type, UIStyles.SUCCESS),
            ("☑️ 全选", self.select_all, UIStyles.INFO),
            ("❌ 取消", self.cancel_changes, UIStyles.TEXT_DISABLED),
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
        """加载支出数据（分页：首次500条）"""
        print("[支出管理] 加载数据...")

        self.table.setRowCount(0)
        records = db_manager.get_expense_records(limit=500)
        
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # record: (djh, rq, zc_name, je, zf_name, bz, zc_code, zf_code) - 8个字段
            djh, rq, zc_name, je, zf_name, bz, zc_code, zf_code = record
            
            # 第0列：复选框
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, checkbox)

            # 第1列：账套号
            self.table.setItem(row, 1, QTableWidgetItem(db_manager.current_account))
            self.table.setItem(row, 2, QTableWidgetItem(djh))
            self.table.setItem(row, 3, QTableWidgetItem(str(rq)))
            self.table.setItem(row, 4, QTableWidgetItem(zc_code if zc_code else "--"))  # zc_code
            self.table.setItem(row, 5, QTableWidgetItem(zc_name if zc_name else ""))
            self.table.setItem(row, 6, QTableWidgetItem(f"¥{je:.2f}" if je else "¥0.00"))
            self.table.setItem(row, 7, QTableWidgetItem(zf_code if zf_code else "--"))  # zf_code
            self.table.setItem(row, 8, QTableWidgetItem(zf_name if zf_name else ""))
            self.table.setItem(row, 9, QTableWidgetItem(bz if bz else ""))
        
        print(f"[支出管理] 加载完成，共{len(records)}条记录")
    
    def query_data(self):
        """查询数据 - 实现数据库筛选"""
        print("[支出管理] 执行查询...")
        
        # 获取筛选条件
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        min_amount_text = self.min_amount.text()
        max_amount_text = self.max_amount.text()
        payment_code = self.payment_combo.currentData()
        expense_type_code = self.expense_type_combo.currentData()
        
        # 保存用户的选择，下次使用
        config.set_ui_setting('last_expense_payment_method', self.payment_combo.currentText())
        config.set_ui_setting('last_expense_type', self.expense_type_combo.currentText())
        
        print(f"[支出管理] 查询条件:")
        print(f"  日期：{start_date} 至 {end_date}")
        print(f"  金额：{min_amount_text} - {max_amount_text}")
        print(f"  支付方式：{payment_code}")
        print(f"  支出类型：{expense_type_code}")
        
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
        if expense_type_code:
            filters['expense_type_code'] = expense_type_code
        
        # 调用数据库查询方法
        records = db_manager.get_expense_records(filters=filters if filters else None)
        
        # 更新表格显示
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            djh, rq, zc_name, je, zf_name, bz, zc_code, zf_code = record
            
            # 第0列：复选框
            checkbox = QTableWidgetItem()
            checkbox.setCheckState(Qt.Unchecked)
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, 0, checkbox)

            # 其他列
            self.table.setItem(row, 1, QTableWidgetItem(db_manager.current_account))
            self.table.setItem(row, 2, QTableWidgetItem(djh))
            self.table.setItem(row, 3, QTableWidgetItem(str(rq)))
            self.table.setItem(row, 4, QTableWidgetItem(zc_code if zc_code else "--"))
            self.table.setItem(row, 5, QTableWidgetItem(zc_name if zc_name else ""))
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
        """添加支出记录 - 集成预算预警和智能填充"""
        from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                     QComboBox, QDateEdit, QLineEdit, QPushButton,
                                     QDoubleSpinBox, QFormLayout, QToolButton)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("💸 新增支出记录")
        dialog.setFixedSize(500, 420)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.BG_GRAY_50};
            }}
            QLabel {{
                color: {UIStyles.TEXT_PRIMARY};
                font-weight: bold;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📝 填写支出信息")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE, QFont.Bold))
        title_label.setStyleSheet(f"color: {UIStyles.DANGER};")
        layout.addWidget(title_label)
        
        # 表单区域
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        # 日期 - 默认今天
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        form_layout.addRow("📅 日期：", date_edit)
        
        # 支出类型 - 记住上次选择 + AI 推荐按钮
        type_row = QHBoxLayout()
        type_combo = QComboBox()
        expense_types = db_manager.get_expense_types()
        last_type_code = config.get('last_expense_type', '')
        last_type_index = 0
        
        for i, (code, name) in enumerate(expense_types):
            type_combo.addItem(name, code)
            if code == last_type_code:
                last_type_index = i
        
        type_combo.setCurrentIndex(last_type_index)
        type_combo.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
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
        ai_recommend_btn.clicked.connect(lambda: self._ai_recommend_category(remark_input, type_combo, is_income=False))
        type_row.addWidget(ai_recommend_btn)
        
        form_layout.addRow("📂 类型：", type_row)
        
        # 金额 - 光标自动定位
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0.01, 999999.99)
        amount_spin.setValue(0.0)
        amount_spin.setPrefix("¥ ")
        amount_spin.setDecimals(2)
        amount_spin.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE, QFont.Bold))
        amount_spin.setStyleSheet(UIStyles.input_style(border_color=UIStyles.DANGER, focus_color=UIStyles.DANGER_HOVER))
        form_layout.addRow("💵 金额：", amount_spin)
        
        # 支付方式 - 记住上次选择
        payment_combo = QComboBox()
        payment_methods = db_manager.get_payment_methods()
        last_payment_code = config.get('last_expense_payment_method', '')
        last_payment_index = 0
        
        for i, (code, name) in enumerate(payment_methods):
            payment_combo.addItem(name, code)
            if code == last_payment_code:
                last_payment_index = i
        
        payment_combo.setCurrentIndex(last_payment_index)
        payment_combo.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        form_layout.addRow("💳 支付：", payment_combo)
        
        # 备注
        remark_input = QLineEdit()
        remark_input.setPlaceholderText("可选备注信息...")
        remark_input.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        remark_input.setStyleSheet(UIStyles.input_style())
        form_layout.addRow("📝 备注：", remark_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet(UIStyles.secondary_button())
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✅ 确定")
        ok_btn.setStyleSheet(UIStyles.danger_button())
        
        def on_ok():
            """确定按钮 - 检查预算并保存到数据库"""
            # 获取表单数据
            rq = date_edit.date().toString("yyyy-MM-dd")
            zc_code = type_combo.currentData()
            je = amount_spin.value()
            zf_code = payment_combo.currentData()
            bz = remark_input.text().strip()
            
            # 验证
            if je <= 0:
                QMessageBox.warning(dialog, "验证失败", "❌ 金额必须大于0！")
                amount_spin.setFocus()
                return
            
            if not zc_code:
                QMessageBox.warning(dialog, "验证失败", "❌ 请选择支出类型！")
                return
            
            if not zf_code:
                QMessageBox.warning(dialog, "验证失败", "❌ 请选择支付方式！")
                return
            
            # 检查预算预警
            current_month = QDate.currentDate().toString("yyyy-MM")
            category_name = type_combo.currentText()
            warnings = self.budget_alert.check_category_budget(
                category=category_name,
                amount=je,
                month=current_month
            )
            
            # 如果有预警，显示警告但允许继续
            if warnings:
                warning = warnings[0]  # 取第一个预警
                
                warning_msg = f"⚠️ {warning['message']}\n\n"
                
                if warning['level'] == 2:  # 危险级别 - 已超支
                    warning_msg += "🚨 该支出将导致预算超支！\n\n是否继续添加？"
                    reply = QMessageBox.warning(
                        dialog, 
                        "预算超支警告", 
                        warning_msg,
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply != QMessageBox.Yes:
                        return  # 用户选择取消
                else:  # 警告级别 - 即将超支
                    warning_msg += "💡 建议控制支出，避免超支。\n\n是否继续添加？"
                    reply = QMessageBox.information(
                        dialog, 
                        "预算预警", 
                        warning_msg,
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply != QMessageBox.Yes:
                        return  # 用户选择取消
            
            try:
                # 保存到数据库
                success = db_manager.add_expense_record(
                    rq=rq,
                    zc_code=zc_code,
                    je=je,
                    zf_code=zf_code,
                    bz=bz
                )
                
                if success:
                    # 保存用户选择，下次使用
                    config.set_ui_setting('last_expense_type', zc_code)
                    config.set_ui_setting('last_expense_payment_method', zf_code)
                    
                    QMessageBox.information(
                        dialog, 
                        "成功", 
                        f"✅ 支出记录添加成功！\n\n"
                        f"日期：{rq}\n"
                        f"类型：{type_combo.currentText()}\n"
                        f"金额：¥{je:.2f}\n"
                        f"支付：{payment_combo.currentText()}"
                    )
                    dialog.accept()

                    # 审计日志
                    from utils.auth_manager import AuthManager
                    AuthManager()._write_audit_log(db_manager.current_account, "add_expense", djh, f"金额: {je:.2f}, 类型: {zc_code}")

                    # 刷新表格
                    self.load_data()
                else:
                    QMessageBox.critical(dialog, "错误", "❌ 保存失败，请重试！")
                    
            except Exception as e:
                log_manager.error(f"[支出管理] 新增记录失败: {e}")
                QMessageBox.critical(dialog, "错误", f"❌ 保存失败：\n{str(e)}")
        
        ok_btn.clicked.connect(on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # 光标自动定位到金额输入框
        amount_spin.setFocus()
        amount_spin.selectAll()
        
        dialog.exec_()
    
    def get_selected_rows(self):
        """获取所有选中的行号（通过复选框）"""
        selected_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # 第0列是复选框
            if item and item.checkState() == Qt.Checked:
                selected_rows.append(row)
        return selected_rows

    def batch_delete(self):
        """批量删除选中记录"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先勾选要删除的记录！")
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
                    djh_item = self.table.item(row, 1)  # 单据号在第1列
                    if djh_item:
                        djh = djh_item.text()
                        if db_manager.delete_expense_record(djh):
                            deleted_count += 1
                        else:
                            failed_count += 1
                
                # 刷新表格
                self.load_data()
                
                if failed_count == 0:
                    self.toast.success(f"✅ 成功删除 {deleted_count} 条记录", 2000)
                    from utils.auth_manager import AuthManager
                    AuthManager()._write_audit_log(db_manager.current_account, "delete_expense", "", f"删除 {deleted_count} 条")
                else:
                    self.toast.warning(f"已删除 {deleted_count} 条，失败 {failed_count} 条", 3000)
                    
            except Exception as e:
                log_manager.error(f"[支出管理] 批量删除失败: {e}")
                QMessageBox.critical(self, "错误", f"批量删除失败：{str(e)}")

    def delete_records(self):
        """兼容旧接口，重定向到 batch_delete"""
        self.batch_delete()

    def batch_change_payment(self):
        """批量修改支付方式"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先勾选要修改的记录！")
            return
        
        from PyQt5.QtWidgets import QDialog, QFormLayout
        
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
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.TEXT_TERTIARY};
                color: white;
                border: none;
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: {UIStyles.PADDING_SMALL}px {UIStyles.PADDING_MEDIUM}px;
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✅ 确定")
        
        def on_ok():
            new_payment_code = payment_combo.currentData()
            new_payment_name = payment_combo.currentText()
            
            try:
                updated_count = 0
                failed_count = 0
                
                for row in selected_rows:
                    djh_item = self.table.item(row, 1)
                    if djh_item:
                        djh = djh_item.text()
                        if db_manager.update_expense_payment(djh, new_payment_code):
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
                log_manager.error(f"[支出管理] 批量修改支付方式失败: {e}")
                QMessageBox.critical(dialog, "错误", f"批量修改失败：{str(e)}")
        
        ok_btn.clicked.connect(on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def batch_change_type(self):
        """批量修改支出类型"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先勾选要修改的记录！")
            return
        
        from PyQt5.QtWidgets import QDialog, QFormLayout
        
        # 创建支出类型选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("🔄 批量修改支出类型")
        dialog.setFixedSize(400, 250)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {UIStyles.BG_GRAY_50};
            }}
            QPushButton {{
                background-color: {UIStyles.DANGER};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.DANGER_HOVER};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)
        
        # 说明文字
        info_label = QLabel(f"将为选中的 <b>{len(selected_rows)}</b> 条记录统一修改支出类型")
        info_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        info_label.setStyleSheet(f"color: {UIStyles.SIDEBAR_BG}; padding: 10px; background-color: white; border-radius: 6px;")
        layout.addWidget(info_label)
        
        # 支出类型选择
        form_layout = QFormLayout()
        type_combo = QComboBox()
        expense_types = db_manager.get_expense_types()
        for code, name in expense_types:
            type_combo.addItem(name, code)
        type_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        form_layout.addRow("选择新的支出类型：", type_combo)
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.TEXT_TERTIARY};
                color: white;
                border: none;
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: {UIStyles.PADDING_SMALL}px {UIStyles.PADDING_MEDIUM}px;
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("✅ 确定")
        
        def on_ok():
            new_type_code = type_combo.currentData()
            new_type_name = type_combo.currentText()
            
            try:
                updated_count = 0
                failed_count = 0
                
                for row in selected_rows:
                    djh_item = self.table.item(row, 1)
                    if djh_item:
                        djh = djh_item.text()
                        if db_manager.update_expense_type(djh, new_type_code):
                            updated_count += 1
                        else:
                            failed_count += 1
                
                # 刷新表格
                self.load_data()
                
                if failed_count == 0:
                    QMessageBox.information(
                        dialog, 
                        "成功", 
                        f"✅ 已更新 {updated_count} 条记录的支出类型为：<b>{new_type_name}</b>"
                    )
                    dialog.accept()
                else:
                    QMessageBox.warning(
                        dialog, 
                        "部分成功", 
                        f"已更新 {updated_count} 条，失败 {failed_count} 条"
                    )
                    
            except Exception as e:
                log_manager.error(f"[支出管理] 批量修改支出类型失败: {e}")
                QMessageBox.critical(dialog, "错误", f"批量修改失败：{str(e)}")
        
        ok_btn.clicked.connect(on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def on_item_double_clicked(self, item):
        """双击编辑单元格并保存到数据库"""
        row = item.row()
        col = item.column()
        
        # 只允许编辑特定字段（支出类型名称、金额、支付方式名称、备注）
        if col in [4, 5, 7, 8]:  # 列索引：4=支出类型名称, 5=金额, 7=支付方式名称, 8=备注
            current_text = item.text()
            
            # 根据列类型设置不同的输入方式
            if col == 5:  # 金额列 - 使用数字输入
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
                ok_btn.setStyleSheet(UIStyles.danger_button())
                
                def save_amount():
                    new_value = f"¥{amount_spin.value():.2f}"
                    item.setText(new_value)
                    
                    # 保存到数据库
                    djh_item = self.table.item(row, 1)
                    if djh_item:
                        djh = djh_item.text()
                        try:
                            # 获取当前记录的完整数据
                            zc_code_item = self.table.item(row, 3)
                            zf_code_item = self.table.item(row, 6)
                            bz_item = self.table.item(row, 8)
                            
                            update_data = {
                                'rq': self.table.item(row, 2).text(),
                                'zc_code': zc_code_item.text() if zc_code_item else '',
                                'je': amount_spin.value(),
                                'zf_code': zf_code_item.text() if zf_code_item else '',
                                'bz': bz_item.text() if bz_item else ''
                            }
                            
                            if db_manager.update_expense_record(djh, update_data):
                                self.toast.success("✅ 金额已更新", 1500)
                            else:
                                self.toast.warning("⚠️ 保存失败", 2000)
                        except Exception as e:
                            log_manager.error(f"[支出管理] 保存金额失败: {e}")
                            self.toast.error(f"❌ 保存失败: {str(e)}", 3000)
                    
                    dialog.accept()
                
                ok_btn.clicked.connect(save_amount)
                btn_layout.addWidget(cancel_btn)
                btn_layout.addWidget(ok_btn)
                layout.addLayout(btn_layout)
                
                dialog.exec_()
                
            else:  # 文本列 - 使用文本输入
                from PyQt5.QtWidgets import QInputDialog
                new_text, ok = QInputDialog.getText(
                    self, 
                    "✏️ 编辑支出记录", 
                    "请输入新值：",
                    QLineEdit.Normal,
                    current_text
                )
                
                if ok and new_text:
                    item.setText(new_text)
                    
                    # 保存到数据库
                    djh_item = self.table.item(row, 1)
                    if djh_item:
                        djh = djh_item.text()
                        try:
                            # 根据列确定要更新的字段
                            if col == 4:  # 支出类型名称
                                self.toast.info("💡 提示：请直接修改支出类型编码列", 2000)
                            elif col == 7:  # 支付方式名称
                                self.toast.info("💡 提示：请直接修改支付方式编码列", 2000)
                            elif col == 8:  # 备注
                                # 获取当前记录的完整数据
                                rq_item = self.table.item(row, 2)
                                zc_code_item = self.table.item(row, 3)
                                je_item = self.table.item(row, 5)
                                zf_code_item = self.table.item(row, 6)
                                
                                update_data = {
                                    'rq': rq_item.text() if rq_item else '',
                                    'zc_code': zc_code_item.text() if zc_code_item else '',
                                    'je': float(je_item.text().replace('¥', '').strip()) if je_item else 0,
                                    'zf_code': zf_code_item.text() if zf_code_item else '',
                                    'bz': new_text
                                }
                                
                                if db_manager.update_expense_record(djh, update_data):
                                    self.toast.success("✅ 备注已更新", 1500)
                                else:
                                    self.toast.warning("⚠️ 保存失败", 2000)
                                    
                        except Exception as e:
                            log_manager.error(f"[支出管理] 保存修改失败: {e}")
                            self.toast.error(f"❌ 保存失败: {str(e)}", 3000)
    
    def init_data(self):
        """初始化数据"""
        print("[支出管理] 初始化数据")
        self.load_data()
    
    def reset_filters(self):
        """重置筛选条件"""
        print("[支出管理] 重置筛选")
        self.start_date.setDate(QDate(2025, 9, 1))
        self.end_date.setDate(QDate(2025, 12, 31))
        self.min_amount.clear()
        self.max_amount.clear()
        self.payment_combo.setCurrentIndex(0)
        self.expense_type_combo.setCurrentIndex(0)
    
    def select_all(self):
        """全选"""
        print("[支出管理] 全选")
        self.table.selectAll()
    
    def save_changes(self):
        """保存修改 - 刷新数据"""
        print("[支出管理] 保存修改")
        
        # 由于双击编辑时已经实时保存到数据库，这里只需要刷新显示
        try:
            self.load_data()
            self.toast.success("✅ 数据已刷新", 1500)
        except Exception as e:
            log_manager.error(f"[支出管理] 刷新数据失败: {e}")
            self.toast.error(f"❌ 刷新失败: {str(e)}", 2000)
    
    def cancel_changes(self):
        """取消修改"""
        print("[支出管理] 取消修改")
        self.load_data()
    
    def exit_page(self):
        """退出页面"""
        print("[支出管理] 退出页面")
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
        print("[支出管理] 导入数据")
        QMessageBox.information(self, "提示", "导入功能待开发")
    
    def _ai_recommend_category(self, remark_input, type_combo, is_income=False):
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
            avg = db_manager.get_expense_avg_amount()
            return avg if avg > 0 else None
        except Exception as e:
            log_manager.debug(f"[支出管理] 计算平均金额失败: {e}")
            return None
    
    def export_data(self):
        """导出数据"""
        print("[支出管理] 导出数据")
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出 Excel 文件", 
            "支出记录.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            print(f"[支出管理] 导出到：{file_path}")
            QMessageBox.information(self, "导出", f"数据将导出到 {file_path}\n导出功能待开发")
