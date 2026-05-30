# -*- coding: utf-8 -*-
"""
记账页面基类 - 封装收入和支出页面的通用逻辑
消除代码重复,提高可维护性
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QComboBox, QDateEdit, QLineEdit,
                             QMessageBox, QFileDialog, QFrame, QInputDialog,
                             QProgressDialog)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QDoubleValidator

from models.db_backend import db_manager
from models.config import config
from utils.excel_utils import excel_handler
from utils.csv_utils import csv_handler
from utils.form_validator import FormValidator  # 新增:导入表单验证器
from utils.logger import log_manager  # 新增:导入日志管理器
from ui.styles import UIStyles  # 新增:导入样式管理模块
from ui.widgets.toast import Toast


class BaseRecordPage(QWidget):
    """记账页面基类 - 收入和支出的通用逻辑"""
    
    # 子类必须重写的属性
    PAGE_TITLE = ""  # 页面标题
    RECORD_TYPE = ""  # 'income' 或 'expense'
    
    def __init__(self):
        super().__init__()
        self.toast = Toast(self)
        self.initUI()
        self.load_data()
    
    def initUI(self):
        """初始化 UI - 使用智能默认值"""
        layout = QVBoxLayout()
        layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel(self.PAGE_TITLE)
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 18, QFont.Bold))
        layout.addWidget(title_label)
        
        # ========== 筛选栏 ==========
        filter_frame = QFrame()
        filter_frame.setStyleSheet(UIStyles.gray_background())
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        # 日期范围 - 智能默认本月
        today = QDate.currentDate()
        first_day = QDate(today.year(), today.month(), 1)
        last_day = QDate(today.year(), today.month(), today.daysInMonth())
        
        filter_layout.addWidget(QLabel("起始日期:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(first_day)
        self.start_date.setCalendarPopup(True)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(last_day)
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
        self.min_amount.textChanged.connect(self._validate_min_amount)  # 新增:实时验证
        filter_layout.addWidget(self.min_amount)
        
        filter_layout.addWidget(QLabel("-"))
        
        self.max_amount = QLineEdit()
        if avg_amount:
            self.max_amount.setPlaceholderText(f"最大 (平均: ¥{avg_amount:.0f})")
        else:
            self.max_amount.setPlaceholderText("最大")
        self.max_amount.setFixedWidth(100)
        self.max_amount.textChanged.connect(self._validate_max_amount)  # 新增:实时验证
        filter_layout.addWidget(self.max_amount)
        
        # 支付方式下拉框 - 记住上次选择
        filter_layout.addWidget(QLabel("支付:"))
        self.payment_combo = QComboBox()
        self.payment_combo.addItem("全部", "all")
        payment_methods = db_manager.get_payment_methods()
        for code, name in payment_methods:
            self.payment_combo.addItem(name, code)
        
        # 恢复上次选择的支付方式
        last_payment_key = f'last_{self.RECORD_TYPE}_payment_method'
        last_payment = config.get(last_payment_key, 'allf')
        self.payment_combo.setCurrentText(last_payment)
        
        filter_layout.addWidget(self.payment_combo)
        
        # 类型下拉框 - 由子类实现
        self.type_combo = self._create_type_combo()
        if self.type_combo:
            filter_layout.addWidget(self.type_combo)
        
        # 备注搜索
        filter_layout.addWidget(QLabel("备注:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("搜索备注...")
        self.keyword_input.setFixedWidth(120)
        filter_layout.addWidget(self.keyword_input)
        
        filter_layout.addStretch()
        filter_frame.setLayout(filter_layout)
        layout.addWidget(filter_frame)
        
        # ========== 按钮工具栏（四组布局）==========
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {UIStyles.BG_GRAY_200};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        
        # 第1组：主操作区
        self.add_btn = QPushButton("➕ 新增记录")
        self.add_btn.setStyleSheet(self._get_button_style(f"{UIStyles.SUCCESS}"))
        self.add_btn.clicked.connect(self.add_record)
        toolbar_layout.addWidget(self.add_btn)
        
        self.save_btn = QPushButton("💾 保存修改")
        self.save_btn.setStyleSheet(self._get_button_style(f"{UIStyles.INFO}"))
        self.save_btn.clicked.connect(self.save_changes)
        toolbar_layout.addWidget(self.save_btn)
        
        # 分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet(f"color: {UIStyles.BG_GRAY_200};")
        toolbar_layout.addWidget(separator1)
        
        # 第2组：查询筛选区
        self.query_btn = QPushButton("🔍 查询")
        self.query_btn.setStyleSheet(self._get_button_style("#8b5cf6"))
        self.query_btn.clicked.connect(self.load_data)
        toolbar_layout.addWidget(self.query_btn)
        
        self.reset_btn = QPushButton("🔄 重置")
        self.reset_btn.setStyleSheet(self._get_button_style(f"{UIStyles.TEXT_TERTIARY}"))
        self.reset_btn.clicked.connect(self.reset_filters)
        toolbar_layout.addWidget(self.reset_btn)
        
        # 分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet(f"color: {UIStyles.BG_GRAY_200};")
        toolbar_layout.addWidget(separator2)
        
        # 第3组：导入导出区
        self.import_btn = QPushButton("📥 导入")
        self.import_btn.setStyleSheet(self._get_button_style(f"{UIStyles.WARNING}"))
        self.import_btn.clicked.connect(self.import_data)
        toolbar_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("📤 导出")
        self.export_btn.setStyleSheet(self._get_button_style(f"{UIStyles.WARNING}"))
        self.export_btn.clicked.connect(self.export_data)
        toolbar_layout.addWidget(self.export_btn)
        
        # 分隔线
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.VLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setStyleSheet(f"color: {UIStyles.BG_GRAY_200};")
        toolbar_layout.addWidget(separator3)
        
        # 第4组：系统操作区
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setStyleSheet(self._get_button_style(f"{UIStyles.TEXT_DISABLED}"))
        self.cancel_btn.clicked.connect(self.cancel_edit)
        toolbar_layout.addWidget(self.cancel_btn)
        
        self.back_btn = QPushButton("⬅️ 返回")
        self.back_btn.setStyleSheet(self._get_button_style("#64748b"))
        self.back_btn.clicked.connect(self.go_back)
        toolbar_layout.addWidget(self.back_btn)
        
        toolbar_layout.addStretch()
        toolbar_frame.setLayout(toolbar_layout)
        layout.addWidget(toolbar_frame)
        
        # ========== 批量操作栏 ==========
        batch_frame = QFrame()
        batch_frame.setStyleSheet(UIStyles.warning_box())
        batch_layout = QHBoxLayout()
        batch_layout.setSpacing(8)
        
        batch_label = QLabel("📦 批量操作:")
        batch_label.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        batch_layout.addWidget(batch_label)
        
        self.batch_delete_btn = QPushButton("🗑️ 批量删除")
        self.batch_delete_btn.setStyleSheet(self._get_button_style(f"{UIStyles.DANGER}", smaller=True))
        self.batch_delete_btn.clicked.connect(self.batch_delete)
        batch_layout.addWidget(self.batch_delete_btn)
        
        self.batch_payment_btn = QPushButton("💳 批量修改支付")
        self.batch_payment_btn.setStyleSheet(self._get_button_style(f"{UIStyles.INFO}", smaller=True))
        self.batch_payment_btn.clicked.connect(self.batch_change_payment)
        batch_layout.addWidget(self.batch_payment_btn)
        
        self.batch_type_btn = QPushButton("🏷️ 批量修改类型")
        self.batch_type_btn.setStyleSheet(self._get_button_style(f"{UIStyles.SUCCESS}", smaller=True))
        self.batch_type_btn.clicked.connect(self.batch_change_type)
        batch_layout.addWidget(self.batch_type_btn)
        
        batch_layout.addStretch()
        batch_frame.setLayout(batch_layout)
        layout.addWidget(batch_frame)
        
        # ========== 数据表格 ==========
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {UIStyles.BG_GRAY_200};
                border-radius: 5px;
                gridline-color: {UIStyles.BG_GRAY_200};
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {UIStyles.BG_GRAY_100};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {UIStyles.BG_GRAY_200};
                font-weight: bold;
            }}
        """)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def _get_button_style(self, color, smaller=False):
        """获取按钮样式"""
        padding = "5px 10px" if smaller else "8px 16px"
        font_size = "11px" if smaller else "12px"
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: {padding};
                font-size: {font_size};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color, 20)};
            }}
        """

    def _darken_color(self, color, amount=10):
        """颜色变暗"""
        # 简单的颜色变暗处理
        color = color.lstrip('#')
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
        r = max(0, r - amount)
        g = max(0, g - amount)
        b = max(0, b - amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_average_amount(self):
        """获取平均金额（用于智能提示）"""
        try:
            records = self._get_all_records()
            if records:
                total = sum(r['je'] for r in records)
                return total / len(records)
        except Exception as e:
            logger.debug(f"[{self.page_name}] 计算平均金额失败: {e}")
            pass
        return None
    
    def _get_all_records(self):
        """获取所有记录（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _create_type_combo(self):
        """创建类型下拉框（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def load_data(self):
        """加载数据 - 增强表单验证"""
        try:
            # ========== 表单验证 ==========
            # 1. 验证日期范围
            is_valid, error_msg = FormValidator.validate_date_range(
                self.start_date.date(), 
                self.end_date.date(),
                "日期"
            )
            if not is_valid:
                self.toast.show_warning(error_msg)
                return
            
            # 2. 验证金额范围
            min_amount_str = self.min_amount.text().strip()
            max_amount_str = self.max_amount.text().strip()
            
            min_amt = None
            max_amt = None
            
            if min_amount_str:
                is_valid, result = FormValidator.validate_amount(min_amount_str, "最小金额")
                if not is_valid:
                    self.toast.show_warning(result)
                    self.min_amount.setStyleSheet(FormValidator.get_validation_style(False))
                    return
                else:
                    min_amt = float(result)
                    self.min_amount.setStyleSheet(FormValidator.get_validation_style(True))
            
            if max_amount_str:
                is_valid, result = FormValidator.validate_amount(max_amount_str, "最大金额")
                if not is_valid:
                    self.toast.show_warning(result)
                    self.max_amount.setStyleSheet(FormValidator.get_validation_style(False))
                    return
                else:
                    max_amt = float(result)
                    self.max_amount.setStyleSheet(FormValidator.get_validation_style(True))
            
            # 3. 验证金额逻辑(最小值不能大于最大值)
            if min_amt is not None and max_amt is not None and min_amt > max_amt:
                self.toast.show_warning("最小金额不能大于最大金额")
                self.min_amount.setStyleSheet(FormValidator.get_validation_style(False))
                self.max_amount.setStyleSheet(FormValidator.get_validation_style(False))
                return
            
            # 重置样式为默认
            self.min_amount.setStyleSheet("")
            self.max_amount.setStyleSheet("")
            
            # ========== 获取筛选条件 ==========
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            payment_code = self.payment_combo.currentData()
            type_code = self.type_combo.currentData() if self.type_combo else None
            keyword = self.keyword_input.text()
            
            # 调用子类方法获取数据
            records = self._fetch_records(
                start_date, end_date, payment_code, type_code, keyword, min_amt, max_amt
            )
            
            # 渲染表格
            self._render_table(records)
            
            # 保存筛选条件
            self._save_filter_preferences()
            
        except Exception as e:
            import logging
            logging.error(f"[{self.PAGE_TITLE}] 加载数据失败: {str(e)}", exc_info=True)
            self.toast.show_error(f"加载数据失败: {str(e)}")
    
    def _fetch_records(self, start_date, end_date, payment_code, type_code, keyword, min_amt, max_amt):
        """获取记录数据（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _render_table(self, records):
        """渲染表格"""
        # 设置表头
        headers = self._get_table_headers()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(records))
        
        # 填充数据
        for row_idx, record in enumerate(records):
            for col_idx, field in enumerate(self._get_table_fields()):
                value = record.get(field, '')
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)
        
        # 调整列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
    
    def _get_table_headers(self):
        """获取表格表头（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _get_table_fields(self):
        """获取表格字段（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _save_filter_preferences(self):
        """保存筛选偏好"""
        payment_code = self.payment_combo.currentData()
        config.set(f'last_{self.RECORD_TYPE}_payment_method', payment_code)
        
        if self.type_combo:
            type_code = self.type_combo.currentData()
            config.set(f'last_{self.RECORD_TYPE}_type', type_code)
    
    def reset_filters(self):
        """重置筛选条件"""
        today = QDate.currentDate()
        first_day = QDate(today.year(), today.month(), 1)
        last_day = QDate(today.year(), today.month(), today.daysInMonth())
        
        self.start_date.setDate(first_day)
        self.end_date.setDate(last_day)
        self.min_amount.clear()
        self.max_amount.clear()
        self.payment_combo.setCurrentIndex(0)
        if self.type_combo:
            self.type_combo.setCurrentIndex(0)
        self.keyword_input.clear()
        
        self.load_data()
        self.toast.show_success("筛选条件已重置")
    
    def add_record(self):
        """新增记录（子类实现对话框）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def save_changes(self):
        """保存修改"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            self.toast.show_warning("请先选择要修改的记录")
            return
        
        # 获取选中的行号（去重）
        row_numbers = list(set(item.row() for item in selected_rows))
        
        if len(row_numbers) > 1:
            self.toast.show_warning("一次只能修改一条记录")
            return
        
        row = row_numbers[0]
        record_id = self.table.item(row, 0).text()
        
        # 子类实现编辑对话框
        self._edit_record_dialog(record_id)
    
    def _edit_record_dialog(self, record_id):
        """编辑记录对话框（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def cancel_edit(self):
        """取消编辑"""
        self.table.clearSelection()
        self.toast.show_info("已取消选择")
    
    def go_back(self):
        """返回上一页"""
        # 由主窗口处理
        pass
    
    def get_selected_rows(self):
        """获取选中的行数据"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return []
        
        row_numbers = list(set(item.row() for item in selected_items))
        rows_data = []
        
        for row in row_numbers:
            record_id = self.table.item(row, 0).text()
            rows_data.append({
                'row': row,
                'id': record_id
            })
        
        return rows_data
    
    def batch_delete(self):
        """批量删除"""
        selected = self.get_selected_rows()
        if not selected:
            self.toast.show_warning("请先选择要删除的记录")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected)} 条记录吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 创建非模态进度条
            progress = QProgressDialog("正在删除记录...", "取消", 0, len(selected), self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)  # 立即显示
            progress.setValue(0)
            
            success_count = 0
            for i, item in enumerate(selected):
                if progress.wasCanceled():
                    break
                try:
                    if self._delete_record(item['id']):
                        success_count += 1
                except Exception as e:
                    log_manager.error(f"[{self.PAGE_TITLE}] 批量删除记录 {item['id']} 失败: {e}", exc_info=True)
                
                progress.setValue(i + 1)
            
            progress.close()
            self.toast.show_success(f"成功删除 {success_count} 条记录")
            self.load_data()
    
    def _delete_record(self, record_id):
        """删除记录（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def batch_change_payment(self):
        """批量修改支付方式"""
        selected = self.get_selected_rows()
        if not selected:
            self.toast.show_warning("请先选择要修改的记录")
            return
        
        # 选择新的支付方式
        payment_methods = db_manager.get_payment_methods()
        payment_names = [name for code, name in payment_methods]
        
        new_payment, ok = QInputDialog.getItem(
            self,
            "批量修改支付方式",
            "选择新的支付方式:",
            payment_names,
            0,
            False
        )
        
        if ok and new_payment:
            # 找到对应的code
            payment_code = None
            for code, name in payment_methods:
                if name == new_payment:
                    payment_code = code
                    break
            
            if payment_code:
                # 创建非模态进度条
                progress = QProgressDialog("正在修改支付方式...", "取消", 0, len(selected), self)
                progress.setWindowModality(Qt.WindowModal)
                progress.setMinimumDuration(0)
                progress.setValue(0)
                
                success_count = 0
                for i, item in enumerate(selected):
                    if progress.wasCanceled():
                        break
                    try:
                        if self._update_record_payment(item['id'], payment_code):
                            success_count += 1
                    except Exception as e:
                        log_manager.error(f"[{self.PAGE_TITLE}] 批量修改支付方式记录 {item['id']} 失败: {e}", exc_info=True)
                    
                    progress.setValue(i + 1)
                
                progress.close()
                self.toast.show_success(f"成功修改 {success_count} 条记录的支付方式")
                self.load_data()
    
    def _update_record_payment(self, record_id, payment_code):
        """更新记录支付方式（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def batch_change_type(self):
        """批量修改类型"""
        selected = self.get_selected_rows()
        if not selected:
            self.toast.show_warning("请先选择要修改的记录")
            return
        
        # 子类实现类型选择对话框
        self._batch_change_type_dialog(selected)
    
    def _batch_change_type_dialog(self, selected_rows):
        """批量修改类型对话框（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def import_data(self):
        """导入数据"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入数据",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.csv'):
                records = csv_handler.read_csv(file_path)
            else:
                records = excel_handler.read_excel(file_path)
            
            if not records:
                self.toast.show_warning("文件中没有数据")
                return
            
            # 导入到数据库
            success_count = self._import_records_to_db(records)
            
            self.toast.show_success(f"成功导入 {success_count} 条记录")
            self.load_data()
            
        except Exception as e:
            self.toast.show_error(f"导入失败: {str(e)}")
    
    def _import_records_to_db(self, records):
        """导入记录到数据库（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def export_data(self):
        """导出数据"""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "导出数据",
            f"{self.RECORD_TYPE}_export.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            # 获取当前显示的数据
            records = self._get_current_displayed_records()
            
            if not records:
                self.toast.show_warning("没有数据可导出")
                return
            
            # 导出
            if selected_filter.startswith("CSV"):
                csv_handler.write_csv(file_path, records, self._get_table_headers())
            else:
                excel_handler.write_excel(file_path, records, self._get_table_headers())
            
            self.toast.show_success(f"数据已导出到: {file_path}")
            
        except Exception as e:
            self.toast.show_error(f"导出失败: {str(e)}")
    
    def _get_current_displayed_records(self):
        """获取当前显示的记录（子类实现）"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _validate_min_amount(self, text):
        """实时验证最小金额
        
        Args:
            text: 输入的文本
        """
        if not text or not text.strip():
            self.min_amount.setStyleSheet("")
            return
        
        is_valid, result = FormValidator.validate_amount(text, "最小金额")
        if is_valid:
            self.min_amount.setStyleSheet(FormValidator.get_validation_style(True))
        else:
            self.min_amount.setStyleSheet(FormValidator.get_validation_style(False))
    
    def _validate_max_amount(self, text):
        """实时验证最大金额
        
        Args:
            text: 输入的文本
        """
        if not text or not text.strip():
            self.max_amount.setStyleSheet("")
            return
        
        is_valid, result = FormValidator.validate_amount(text, "最大金额")
        if is_valid:
            self.max_amount.setStyleSheet(FormValidator.get_validation_style(True))
        else:
            self.max_amount.setStyleSheet(FormValidator.get_validation_style(False))
