# -*- coding: utf-8 -*-
"""
收支月报表页面| 按月统计收支情况
"""

from collections import defaultdict
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QComboBox, QDateEdit, QLineEdit,
                             QMessageBox, QFileDialog, QFrame, QScrollArea,
                             QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from utils.logger import log_manager
#logger = log_manager  # 创建别名
from models.db_backend import db_manager
from ui.styles import UIStyles


class MonthlyReportPage(QWidget):
    """收支月报表页面（重构版 - 简洁专业风格）"""
    
    def __init__(self):
        super().__init__()
        self.current_year_month = "2025-12"
        self.report_data = []
        self._is_being_deleted = False  # 标记是否正在销毁
        self.initUI()
        self.load_data()
    
    def closeEvent(self, event):
        """页面关闭事件 - 清理资源"""
        self._cleanup_resources()
        super().closeEvent(event)
    
    def _cleanup_resources(self):
        """清理matplotlib资源"""
        if self._is_being_deleted:
            return
        
        self._is_being_deleted = True
        
        try:
            # 关闭figure，释放内存
            if hasattr(self, 'figure') and self.figure:
                from matplotlib.pyplot import close
                close(self.figure)
                self.figure = None
            
            # 清除canvas引用
            if hasattr(self, 'canvasf'):
                self.canvas = None
                
        except Exception as e:
            print(f"[月报表] 清理资源时出错: {e}")
    
    def initUI(self):
        """初始化 UI """
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        main_layout.setSpacing(12)
        
        # ========== 标题和月份选择区 ==========
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📊 收支月报表")
        title_label.setStyleSheet(UIStyles.page_title_style())
        header_layout.addWidget(title_label)
        
        # 月份导航
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        self.prev_month_btn = QPushButton("◀")
        self.prev_month_btn.setFixedWidth(40)
        self.prev_month_btn.setCursor(Qt.PointingHandCursor)
        self.prev_month_btn.setStyleSheet(UIStyles.secondary_button())
        self.prev_month_btn.clicked.connect(self.navigate_to_prev_month)
        nav_layout.addWidget(self.prev_month_btn)

        # ========== 月份选择器（新增）==========
        self.month_selector = QComboBox()
        self.month_selector.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.month_selector.setMinimumWidth(140)
        self.month_selector.setCursor(Qt.PointingHandCursor)
        self.month_selector.setStyleSheet(UIStyles.combo_box_style())
        self.month_selector.currentTextChanged.connect(self.on_month_selected)
        nav_layout.addWidget(self.month_selector)
        
        # 保留原有的月份显示标签（作为备用）
        self.month_display_label = QLabel("2025年12月")
        self.month_display_label.setFont(QFont(UIStyles.FONT_FAMILY, 13, QFont.Bold))
        self.month_display_label.setAlignment(Qt.AlignCenter)
        self.month_display_label.setMinimumWidth(120)
        self.month_display_label.setVisible(False)  # 隐藏，使用下拉框代替
        nav_layout.addWidget(self.month_display_label)
        
        self.next_month_btn = QPushButton("▶")
        self.next_month_btn.setFixedWidth(40)
        self.next_month_btn.setCursor(Qt.PointingHandCursor)
        self.next_month_btn.setStyleSheet(UIStyles.secondary_button())
        self.next_month_btn.clicked.connect(self.navigate_to_next_month)
        nav_layout.addWidget(self.next_month_btn)
        
        header_layout.addLayout(nav_layout)
        header_layout.addStretch()
        
        # 操作按钮
        self.generate_btn = QPushButton("🔄 生成月报")
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.setStyleSheet(UIStyles.primary_button())
        self.generate_btn.clicked.connect(self.generate_monthly_report)
        header_layout.addWidget(self.generate_btn)
        
        self.query_btn = QPushButton("🔍 刷新")
        self.query_btn.setCursor(Qt.PointingHandCursor)
        self.query_btn.setStyleSheet(UIStyles.secondary_button())
        self.query_btn.clicked.connect(self.query_data)
        header_layout.addWidget(self.query_btn)
        
        main_layout.addLayout(header_layout)
        
        # ========== 关键指标区（简洁横条）==========
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet(UIStyles.gray_background())
        metrics_layout = QHBoxLayout(metrics_frame)
        metrics_layout.setSpacing(20)
        
        # 四个指标
        self.income_label = self._create_simple_metric("总收入:", "¥0.00", f"{UIStyles.SUCCESS}")
        self.expense_label = self._create_simple_metric("总支出:", "¥0.00", f"{UIStyles.DANGER}")
        self.balance_label = self._create_simple_metric("净结余:", "¥0.00", f"{UIStyles.INFO}")
        self.avg_daily_label = self._create_simple_metric("日均支出:", "¥0.00", f"{UIStyles.WARNING}")
        
        metrics_layout.addWidget(self.income_label)
        metrics_layout.addWidget(self.expense_label)
        metrics_layout.addWidget(self.balance_label)
        metrics_layout.addWidget(self.avg_daily_label)
        metrics_layout.addStretch()
        
        main_layout.addWidget(metrics_frame)
        
        # ========== 图表分析区 ==========
        chart_section_label = QLabel("📈 数据分析图表")
        chart_section_label.setStyleSheet(f"font-size: {UIStyles.FONT_SIZE_XLARGE}px; font-weight: bold; color: {UIStyles.TEXT_PRIMARY};")
        main_layout.addWidget(chart_section_label)

        # 图表类型选择
        chart_type_layout = QHBoxLayout()
        chart_type_layout.setSpacing(10)
        
        self.chart_tab_group = QButtonGroup(self)
        self.bar_chart_radio = QRadioButton("收支对比")
        self.pie_chart_radio = QRadioButton("支出占比")
        self.trend_chart_radio = QRadioButton("趋势分析")
        self.category_trend_radio = QRadioButton("分类消费趋势")
        
        for i, radio in enumerate([self.bar_chart_radio, self.pie_chart_radio, self.trend_chart_radio, self.category_trend_radio]):
            radio.setCursor(Qt.PointingHandCursor)
            radio.setChecked(i == 0)
            self.chart_tab_group.addButton(radio, i)
            chart_type_layout.addWidget(radio)
        
        self.chart_tab_group.buttonClicked.connect(self.switch_chart_type)
        chart_type_layout.addStretch()
        main_layout.addLayout(chart_type_layout)
        
        # ========== 分类消费趋势筛选区（新增）==========
        self.filter_frame = QFrame()
        self.filter_frame.setStyleSheet(UIStyles.filter_frame_style())
        filter_layout = QVBoxLayout(self.filter_frame)
        filter_layout.setSpacing(8)
        
        # 第一行：账套号和日期范围
        filter_row1 = QHBoxLayout()
        filter_row1.setSpacing(10)
        
        # 账套号选择
        account_label = QLabel("账套号:")
        account_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        filter_row1.addWidget(account_label)
        
        self.account_filter_combo = QComboBox()
        self.account_filter_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.account_filter_combo.setMinimumWidth(150)
        self.account_filter_combo.setCursor(Qt.PointingHandCursor)
        self.account_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: white;
                border: 1px solid {UIStyles.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border-color: {UIStyles.INFO};
            }}
        """)
        self._load_account_options()
        filter_row1.addWidget(self.account_filter_combo)
        
        # 起始日期
        start_date_label = QLabel("起始日期:")
        start_date_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        filter_row1.addWidget(start_date_label)
        
        self.start_date_filter = QDateEdit()
        self.start_date_filter.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setMinimumWidth(120)
        self.start_date_filter.setDate(QDate.currentDate().addMonths(-3))
        self.start_date_filter.setStyleSheet(f"""
            QDateEdit {{
                background-color: white;
                border: 1px solid {UIStyles.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QDateEdit:hover {{
                border-color: {UIStyles.INFO};
            }}
        """)
        filter_row1.addWidget(self.start_date_filter)
        
        # 结束日期
        end_date_label = QLabel("结束日期:")
        end_date_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        filter_row1.addWidget(end_date_label)
        
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setMinimumWidth(120)
        self.end_date_filter.setDate(QDate.currentDate())
        self.end_date_filter.setStyleSheet(f"""
            QDateEdit {{
                background-color: white;
                border: 1px solid {UIStyles.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QDateEdit:hover {{
                border-color: {UIStyles.INFO};
            }}
        """)
        filter_row1.addWidget(self.end_date_filter)
        
        filter_row1.addStretch()
        filter_layout.addLayout(filter_row1)
        
        # 第二行：消费类型和刷新按钮
        filter_row2 = QHBoxLayout()
        filter_row2.setSpacing(10)
        
        # 消费类型选择
        type_label = QLabel("消费类型:")
        type_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        filter_row2.addWidget(type_label)
        
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.type_filter_combo.setMinimumWidth(150)
        self.type_filter_combo.setCursor(Qt.PointingHandCursor)
        self.type_filter_combo.addItem("全部类型", "all")
        self._load_expense_type_options()
        self.type_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: white;
                border: 1px solid {UIStyles.BORDER_MEDIUM};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox:hover {{
                border-color: {UIStyles.INFO};
            }}
        """)
        filter_row2.addWidget(self.type_filter_combo)
        
        # 刷新按钮
        self.refresh_chart_btn = QPushButton("🔄 刷新图表")
        self.refresh_chart_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_chart_btn.setStyleSheet(UIStyles.primary_button())
        self.refresh_chart_btn.clicked.connect(self.update_chart)
        filter_row2.addWidget(self.refresh_chart_btn)
        
        filter_row2.addStretch()
        filter_layout.addLayout(filter_row2)
        
        # 默认隐藏筛选区，只在选中"分类消费趋势"时显示
        self.filter_frame.setVisible(False)
        main_layout.addWidget(self.filter_frame)
        
        # 图表容器
        self.chart_frame = QFrame()
        self.chart_frame.setStyleSheet(UIStyles.white_background())
        self.chart_frame.setMinimumHeight(320)
        chart_layout = QVBoxLayout(self.chart_frame)
        chart_layout.setContentsMargins(10, 10, 10, 10)
        
        # Matplotlib 画布
        self.figure = Figure(figsize=(10, 3.5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        chart_layout.addWidget(self.canvas)
        
        main_layout.addWidget(self.chart_frame)
        
        # ========== 详细数据表格 ==========
        table_section_label = QLabel("📋 详细数据")
        table_section_label.setStyleSheet(f"font-size: {UIStyles.FONT_SIZE_XLARGE}px; font-weight: bold; color: {UIStyles.TEXT_PRIMARY};")
        main_layout.addWidget(table_section_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "账套号", "期初日期", "期末日期", "支付编码",
            "期初余额", "收入金额", "支出金额", "期末余额"
        ])
        
        # 表格样式
        self.table.setStyleSheet(UIStyles.modern_table_style())
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        # 交替行颜色
        self.table.setAlternatingRowColors(True)
        
        main_layout.addWidget(self.table)
        
        # ========== 底部操作按钮栏 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_meta = [
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

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
    
    def _create_simple_metric(self, label_text, value_text, color):
        """创建简洁的指标标签"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        layout.addWidget(label)
        
        value = QLabel(value_text)
        value.setFont(QFont(UIStyles.FONT_FAMILY, 13, QFont.Bold))
        value.setStyleSheet(f"color: {color};")
        layout.addWidget(value)
        
        container.value_label = value  # 存储引用以便更新
        
        return container
    
    def load_data(self):
        """加载月度报表数据"""
        print("[月报表] 加载数据...")
        
        self.table.setRowCount(0)
        records = db_manager.get_monthly_report(self.current_year_month)
        self.report_data = records
        
        total_income = 0
        total_expense = 0
        
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # record: (qsrq, jsrq, zf_code, qcye, srje, zcje, qmye)
            qsrq, jsrq, zf_code, qcye, srje, zcje, qmye = record
            
            # 累加总额
            if srje:
                total_income += srje
            if zcje:
                total_expense += zcje
            
            self.table.setItem(row, 0, QTableWidgetItem(db_manager.current_account))
            self.table.setItem(row, 1, QTableWidgetItem(str(qsrq)))
            self.table.setItem(row, 2, QTableWidgetItem(str(jsrq)))
            self.table.setItem(row, 3, QTableWidgetItem(zf_code))
            self.table.setItem(row, 4, QTableWidgetItem(f"¥{qcye:.2f}" if qcye else "¥0.00"))
            self.table.setItem(row, 5, QTableWidgetItem(f"¥{srje:.2f}" if srje else "¥0.00"))
            self.table.setItem(row, 6, QTableWidgetItem(f"¥{zcje:.2f}" if zcje else "¥0.00"))
            self.table.setItem(row, 7, QTableWidgetItem(f"¥{qmye:.2f}" if qmye else "¥0.00"))
        
        print(f"[月报表] 加载完成，共{len(records)}条记录")
        
        # 更新指标
        total_balance = total_income - total_expense
        days_in_month = self._get_days_in_month(self.current_year_month)
        daily_avg = total_expense / days_in_month if days_in_month > 0 else 0
        
        self.income_label.value_label.setText(f"¥{total_income:.2f}")
        self.expense_label.value_label.setText(f"¥{total_expense:.2f}")
        self.balance_label.value_label.setText(f"¥{total_balance:.2f}")
        self.avg_daily_label.value_label.setText(f"¥{daily_avg:.2f}")
        
        # 更新月份显示
        try:
            if '-' in self.current_year_month:
                year, month = self.current_year_month.split('-')
                self.month_display_label.setText(f"{year}年{int(month)}月")
            else:
                # 如果格式不正确，使用当前日期
                from datetime import datetime
                now = datetime.now()
                self.month_display_label.setText(f"{now.year}年{now.month}月")
                self.current_year_month = now.strftime('%Y-%m')
        except Exception as e:
            print(f"[月报表] 更新月份显示失败: {e}")
            from datetime import datetime
            now = datetime.now()
            self.month_display_label.setText(f"{now.year}年{now.month}月")
            self.current_year_month = now.strftime('%Y-%m')
        
        # 更新月份选择器（新增）
        self.update_month_selector()
        
        # 重新加载筛选选项，确保数据正确
        self._load_account_options()
        self._load_expense_type_options()
        
        # 如果当前选中的是分类消费趋势图，自动刷新
        if hasattr(self, 'chart_type_group'):
            for btn in self.chart_type_group.buttons():
                if btn.isChecked() and "分类消费趋势" in btn.text():
                    self._draw_category_trend_chart()
                    break
        
    def _get_days_in_month(self, year_month):
        """获取月份的天数"""
        try:
            year, month = map(int, year_month.split('-'))
            if month == 12:
                next_month = QDate(year + 1, 1, 1)
            else:
                next_month = QDate(year, month + 1, 1)
            current_month = QDate(year, month, 1)
            return current_month.daysTo(next_month)
        except Exception as e:
            log_manager.warning(f"[月报表] 计算月份天数失败: {e}")
            return 30
    
    def navigate_to_prev_month(self):
        """导航到上个月"""
        try:
            year, month = map(int, self.current_year_month.split('-'))
            if month == 1:
                year -= 1
                month = 12
            else:
                month -= 1
            self.current_year_month = f"{year}-{month:02d}"
            self.load_data()
        except Exception as e:
            print(f"[月报表] 导航失败: {e}")
    
    def navigate_to_next_month(self):
        """导航到下个月"""
        try:
            year, month = map(int, self.current_year_month.split('-'))
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            self.current_year_month = f"{year}-{month:02d}"
            self.update_month_selector()
            self.load_data()
        except Exception as e:
            print(f"[月报表] 导航失败: {e}")
    
    def update_month_selector(self):
        """更新月份选择器选项"""
        try:
            # 临时断开信号，防止递归调用
            self.month_selector.blockSignals(True)
            
            # 清空现有选项
            self.month_selector.clear()
            
            # 获取数据库中所有有数据的月份
            sql = """
                SELECT DISTINCT strftime('%Y-%m', rq) as month
                FROM sz_table_lsz
                WHERE zth = ?
                ORDER BY month DESC
            """
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            
            # 添加月份选项
            months_with_data = [row[0] for row in rows]
            
            # 如果没有数据，添加当前月份
            if not months_with_data:
                from datetime import datetime
                current = datetime.now()
                months_with_data = [current.strftime('%Y-%m')]
            
            # 确保当前选中的月份在列表中
            if self.current_year_month not in months_with_data:
                months_with_data.insert(0, self.current_year_month)
            
            # 填充下拉框
            for month_str in months_with_data:
                try:
                    # 确保月份格式正确
                    if '-' in month_str:
                        parts = month_str.split('-')
                        if len(parts) == 2:
                            year, month = int(parts[0]), int(parts[1])
                            display_text = f"{year}年{month}月"
                            normalized_month = f"{year}-{month:02d}"
                            self.month_selector.addItem(display_text, normalized_month)
                        else:
                            # 格式不正确，跳过
                            print(f"[月报表] 跳过无效月份格式: {month_str}")
                    else:
                        # 没有分隔符，跳过
                        print(f"[月报表] 跳过无效月份格式: {month_str}")
                except Exception as e:
                    print(f"[月报表] 解析月份失败 {month_str}: {e}")
            
            # 设置当前选中项
            index = self.month_selector.findData(self.current_year_month)
            if index >= 0:
                self.month_selector.setCurrentIndex(index)
            elif months_with_data:
                # 如果当前月份不在列表中，选中第一个
                self.month_selector.setCurrentIndex(0)
                # 更新current_year_month为选中的值
                selected_data = self.month_selector.currentData()
                if selected_data and '-' in selected_data:
                    self.current_year_month = selected_data
            
        except Exception as e:
            print(f"[月报表] 更新月份选择器失败: {e}")
        finally:
            # 恢复信号连接
            self.month_selector.blockSignals(False)
    
    def on_month_selected(self, display_text):
        """月份选择器切换事件"""
        try:
            # 从显示文本中提取年月数据
            # 格式："2025年12月" -> "2025-12"
            if '年' in display_text and '月' in display_text:
                parts = display_text.replace('年', '-').replace('月', '').split('-')
                year = int(parts[0])
                month = int(parts[1])
                self.current_year_month = f"{year}-{month:02d}"
            else:
                # 直接是 YYYY-MM 格式
                self.current_year_month = display_text
            
            # 临时阻止信号，防止递归
            self.month_selector.blockSignals(True)
            
            # 重新加载数据（会调用update_month_selector）
            self.load_data()
            
        except Exception as e:
            print(f"[月报表] 月份选择失败: {e}")
            QMessageBox.warning(self, "错误", f"月份选择失败：{str(e)}")
        finally:
            # 恢复信号
            self.month_selector.blockSignals(False)
    
    def generate_monthly_report(self):
        """生成月度报表"""
        print("[月报表] 生成月报...")
        
        reply = QMessageBox.question(
            self,
            "确认生成",
            f"确定要重新生成 {self.current_year_month} 的月报表吗？\n这将清空现有报表数据并重新计算。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            db_manager.generate_monthly_report(self.current_year_month)
            QMessageBox.information(self, "成功", f"{self.current_year_month} 月报表已重新生成")
            self.load_data()
    
    def query_data(self):
        """查询数据"""
        print("[月报表] 执行查询...")
        self.load_data()
    
    def switch_chart_type(self, button):
        """切换图表类型"""
        # 先检查canvas是否有效
        if not hasattr(self, 'canvas') or self.canvas is None:
            return
        
        try:
            _ = self.canvas.width()
        except (RuntimeError, AttributeError):
            return
        
        # 根据选中的图表类型显示/隐藏筛选区
        if self.category_trend_radio.isChecked():
            self.filter_frame.setVisible(True)
        else:
            self.filter_frame.setVisible(False)
        
        # 清空图表，避免canvas已删除的错误
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, '加载中...', ha='center', va='center', 
                   fontsize=14, color=UIStyles.TEXT_DISABLED, transform=ax.transAxes)
            ax.axis('off')
            self.canvas.draw()
        except (RuntimeError, AttributeError) as e:
            if "wrapped C/C++ object" in str(e) or "has been deleted" in str(e):
                return
            raise
        
        # 然后更新图表
        self.update_chart()
    
    def update_chart(self):
        """更新图表"""
        # 检查canvas是否仍然有效
        if not hasattr(self, 'canvas') or self.canvas is None:
            return  # 静默返回，不输出日志
        
        try:
            # 检查canvas的底层C++对象是否仍然有效
            _ = self.canvas.width()
        except (RuntimeError, AttributeError) as e:
            if "wrapped C/C++ object" in str(e) or "has been deleted" in str(e):
                return  # 静默返回，这是正常的页面切换行为
            raise  # 其他异常继续抛出
        
        if not self.report_data:
            self._show_empty_chart()
            return
        
        # 根据选中的图表类型绘制
        try:
            if self.bar_chart_radio.isChecked():
                self._draw_bar_chart()
            elif self.pie_chart_radio.isChecked():
                self._draw_pie_chart()
            elif self.trend_chart_radio.isChecked():
                self._draw_trend_chart()
            elif self.category_trend_radio.isChecked():
                self._draw_category_trend_chart()
        except RuntimeError as e:
            # 如果canvas已被删除，静默忽略（这是正常现象）
            if "wrapped C/C++ object" in str(e) or "has been deleted" in str(e):
                pass  # 完全静默，不输出任何日志
            else:
                raise
        except Exception:
            # 捕获所有其他异常，避免崩溃
            pass
    
    def _draw_bar_chart(self):
        """绘制收支对比柱状图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 准备数据
        payment_codes = [record[2] for record in self.report_data]
        incomes = [record[4] or 0 for record in self.report_data]
        expenses = [record[5] or 0 for record in self.report_data]
        
        x = range(len(payment_codes))
        width = 0.35
        
        # 绘制柱状图
        bars1 = ax.bar([i - width/2 for i in x], incomes, width, 
                       label='收入', color=UIStyles.SUCCESS, alpha=0.85, edgecolor='white', linewidth=1)
        bars2 = ax.bar([i + width/2 for i in x], expenses, width, 
                       label='支出', color=UIStyles.DANGER, alpha=0.85, edgecolor='white', linewidth=1)
        
        # 添加数值标签
        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}', ha='center', va='bottom', fontsize=7, fontweight='bold')
        
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}', ha='center', va='bottom', fontsize=7, fontweight='bold')
        
        # 设置标签
        ax.set_xlabel('支付方式', fontsize=9, fontweight='bold', color=UIStyles.TEXT_TERTIARY)
        ax.set_ylabel('金额 (元)', fontsize=9, fontweight='bold', color=UIStyles.TEXT_TERTIARY)
        ax.set_title(f'{self.current_year_month} 各支付方式收支对比', 
                    fontsize=11, fontweight='bold', color=UIStyles.TEXT_PRIMARY, pad=10)
        ax.set_xticks(list(x))
        ax.set_xticklabels(payment_codes, fontsize=8, rotation=45, ha='right')
        ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
        
        # 美化
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(UIStyles.BG_GRAY_200)
        ax.spines['bottom'].set_color(UIStyles.BG_GRAY_200)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=UIStyles.BORDER_MEDIUM)
        ax.set_axisbelow(True)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _draw_pie_chart(self):
        """绘制支出占比饼图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 准备数据
        payment_codes = [record[2] for record in self.report_data]
        expenses = [record[5] or 0 for record in self.report_data]
        
        # 过滤掉支出为0的项目
        filtered_data = [(code, exp) for code, exp in zip(payment_codes, expenses) if exp > 0]
        
        if not filtered_data:
            self._show_empty_chart()
            return
        
        codes, exps = zip(*filtered_data)
        colors = [UIStyles.DANGER, UIStyles.WARNING, UIStyles.SUCCESS, UIStyles.INFO, '#8b5cf6', UIStyles.ACCENT_PINK, '#06b6d4']
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(exps, labels=codes, autopct='%1.1f%%',
                                          colors=colors[:len(codes)], startangle=90,
                                          pctdistance=0.85, wedgeprops=dict(width=0.5, edgecolor='white'))
        
        # 设置字体
        for text in texts:
            text.set_fontsize(8)
            text.set_fontweight('bold')
        for autotext in autotexts:
            autotext.set_fontsize(7)
            autotext.set_fontweight('bold')
            autotext.set_color('white')
        
        ax.set_title(f'{self.current_year_month} 各支付方式支出占比', 
                    fontsize=11, fontweight='bold', color=UIStyles.TEXT_PRIMARY, pad=10)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _draw_trend_chart(self):
        """绘制趋势分析图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 模拟每日趋势数据
        days_in_month = self._get_days_in_month(self.current_year_month)
        days = list(range(1, days_in_month + 1))
        
        # 简化：假设均匀分布
        total_expense = sum(record[5] or 0 for record in self.report_data)
        daily_avg = total_expense / days_in_month if days_in_month > 0 else 0
        daily_expenses = [daily_avg * (0.8 + 0.4 * (i % 7) / 7) for i in range(days_in_month)]
        
        # 绘制折线图
        ax.plot(days, daily_expenses, marker='o', markersize=3, linewidth=1.5,
               color=UIStyles.WARNING, markerfacecolor='white', markeredgewidth=1.5, markeredgecolor=UIStyles.WARNING)
        ax.fill_between(days, daily_expenses, alpha=0.15, color=UIStyles.WARNING)
        
        # 设置标签
        ax.set_xlabel('日期', fontsize=9, fontweight='bold', color=UIStyles.TEXT_TERTIARY)
        ax.set_ylabel('日均支出 (元)', fontsize=9, fontweight='bold', color=UIStyles.TEXT_TERTIARY)
        ax.set_title(f'{self.current_year_month} 每日支出趋势（估算）', 
                    fontsize=11, fontweight='bold', color=UIStyles.TEXT_PRIMARY, pad=10)
        
        # 美化
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(UIStyles.BG_GRAY_200)
        ax.spines['bottom'].set_color(UIStyles.BG_GRAY_200)
        ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=UIStyles.BORDER_MEDIUM)
        ax.set_axisbelow(True)
        
        self.figure.tight_layout()
        self.canvas.draw()

    def _load_account_options(self):
        """加载账套号选项（含姓名）"""
        try:
            # 从 sz_d_zt 获取所有账套（含姓名），只列出有数据的
            sql = """
                SELECT d.zth, d.xm, d.ztmc
                FROM sz_d_zt d
                WHERE d.zth IN (
                    SELECT DISTINCT zth FROM sz_sheet_sr
                    UNION SELECT DISTINCT zth FROM sz_sheet_zc
                )
                ORDER BY d.zth
            """
            db_manager._backend.execute(sql)
            rows = db_manager._backend.fetchall()

            self.account_filter_combo.clear()
            if rows:
                for row in rows:
                    zth = row[0]
                    xm = row[1] if len(row) > 1 else ""
                    ztmc = row[2] if len(row) > 2 else ""
                    name = xm or ztmc or ""
                    display = f"{zth} - {name}" if name else zth
                    self.account_filter_combo.addItem(display, zth)

                current_index = self.account_filter_combo.findData(db_manager.current_account)
                if current_index >= 0:
                    self.account_filter_combo.setCurrentIndex(current_index)
                else:
                    self.account_filter_combo.setCurrentIndex(0)
            else:
                # 无数据时显示当前登录账套
                self.account_filter_combo.addItem(db_manager.current_account, db_manager.current_account)
        except Exception as e:
            print(f"[月报表] 加载账套号失败: {e}")
            self.account_filter_combo.addItem(db_manager.current_account, db_manager.current_account)
    
    def _load_expense_type_options(self):
        """加载支出类型选项"""
        try:
            # 获取所有支出类型
            sql = "SELECT zc_code, zc_name FROM sz_c_zc ORDER BY zc_code"
            db_manager._backend.execute(sql)
            rows = db_manager._backend.fetchall()
            
            print(f"[月报表-调试] 加载支出类型，找到 {len(rows)} 个类型")
            
            # 清空并重新填充（保留"全部类型"）
            self.type_filter_combo.clear()
            self.type_filter_combo.addItem("全部类型", "all")
            
            for code, name in rows:
                self.type_filter_combo.addItem(name, code)
                
            if rows:
                print(f"[月报表-调试] 支出类型示例: {[(r[0], r[1]) for r in rows[:3]]}")
        except Exception as e:
            print(f"[月报表] 加载支出类型失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_category_trend_chart(self):
        """绘制分类消费趋势图（折线/曲线风格）"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 获取筛选条件
        account = self.account_filter_combo.currentData()
        start_date = self.start_date_filter.date().toString("yyyy-MM-dd")
        end_date = self.end_date_filter.date().toString("yyyy-MM-dd")
        expense_type = self.type_filter_combo.currentData()
        
        print(f"[月报表-调试] 筛选条件 - 账套号: {account}, 起始日期: {start_date}, 结束日期: {end_date}, 消费类型: {expense_type}")
        
        # 构建查询 - 从支出表获取记录
        sql = """
            SELECT s.rq, c.zc_name, s.je 
            FROM sz_sheet_zc s
            LEFT JOIN sz_c_zc c ON s.zc_code = c.zc_code
            WHERE s.zth = ? 
            AND s.rq >= ? 
            AND s.rq <= ?
        """
        params = [account, start_date, end_date]
        
        if expense_type != "all":
            # 使用zc_code进行筛选，因为type_filter_combo存储的是代码
            sql += " AND s.zc_code = ?"
            params.append(expense_type)
            
        sql += " ORDER BY s.rq ASC"
        
        print(f"[月报表-调试] SQL查询: {sql}")
        print(f"[月报表-调试] 参数: {params}")
        
        try:
            if hasattr(db_manager, '_backend'):
                db_manager._backend.execute(sql, tuple(params))
                rows = db_manager._backend.fetchall()
                print(f"[月报表-调试] 查询结果: {len(rows)} 条记录")
                if rows:
                    print(f"[月报表-调试] 示例数据: {rows[:3]}")
            else:
                rows = []
                print(f"[月报表-调试] db_manager没有_backend属性")
        except Exception as e:
            print(f"[月报表] 查询趋势数据失败: {e}")
            import traceback
            traceback.print_exc()
            rows = []
            
        if not rows:
            print(f"[月报表-调试] 无数据，显示空白图表")
            self._show_empty_chart()
            return
            
        print(f"[月报表-调试] 开始数据处理...")
        
        # 数据处理：按日期和类别聚合
        import pandas as pd
        import numpy as np
        
        try:
            df = pd.DataFrame(rows, columns=['date', 'category', 'amount'])
            print(f"[月报表-调试] DataFrame创建成功，形状: {df.shape}")
            
            df['date'] = pd.to_datetime(df['date'])
            print(f"[月报表-调试] 日期转换完成")
            
            # 按日期和类别分组求和
            grouped = df.groupby(['date', 'category'])['amount'].sum().reset_index()
            print(f"[月报表-调试] 分组聚合完成，形状: {grouped.shape}")
            
            # 获取所有唯一的类别
            categories = grouped['category'].unique()
            print(f"[月报表-调试] 找到 {len(categories)} 个消费类型: {categories.tolist()}f")
            
            # 定义颜色调色板
            colors = [UIStyles.DANGER, UIStyles.INFO, UIStyles.SUCCESS, UIStyles.WARNING, '#8b5cf6', UIStyles.ACCENT_PINK, '#06b6d4', '#f97316']
            
            # 为每个类别绘制折线
            for idx, category in enumerate(categories):
                category_data = grouped[grouped['category'] == category]
                category_data = category_data.sort_values('date')
                
                # 转换为numpy数组以避免matplotlib的FutureWarning
                dates = np.array(category_data['date'])
                amounts = np.array(category_data['amount'])
                
                print(f"[月报表-调试] 绘制类型 '{category}': {len(dates)} 个数据点")
                
                color = colors[idx % len(colors)]
                ax.plot(dates, amounts, 
                       marker='o', markersize=4, linewidth=2, 
                       label=category, color=color, alpha=0.85)
            
            print(f"[月报表-调试] 所有曲线绘制完成，正在设置图表属性...f")
            
            # 设置标签和标题
            ax.set_xlabel('日期', fontsize=10, fontweight='bold', color=UIStyles.TEXT_TERTIARY)
            ax.set_ylabel('支出金额 (元)', fontsize=10, fontweight='bold', color=UIStyles.TEXT_TERTIARY)
            
            type_desc = "全部类型" if expense_type == "allf" else expense_type
            ax.set_title(f'{start_date} 至 {end_date} 分类消费趋势 ({type_desc})', 
                        fontsize=12, fontweight='bold', color=UIStyles.TEXT_PRIMARY, pad=10)
            
            # 旋转x轴标签以便阅读
            ax.tick_params(axis='x', rotation=45)
            
            # 美化图表
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            # 移除title_fontsize参数以兼容旧版本matplotlib
            ax.legend(title="消费类型f", bbox_to_anchor=(1.05, 1), loc='upper left', 
                     fontsize=8)
            ax.yaxis.grid(True, linestyle='--', alpha=0.3, color=UIStyles.BORDER_MEDIUM)
            ax.set_axisbelow(True)
            
            # 格式化y轴为货币格式
            from matplotlib.ticker import FuncFormatter
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'¥{x:,.0f}'))
            
            print(f"[月报表-调试] 图表属性设置完成，正在渲染...")
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            print(f"[月报表-调试] 图表渲染完成！")
            
        except Exception as e:
            print(f"[月报表] 数据处理或绘图失败: {e}")
            import traceback
            traceback.print_exc()
            self._show_empty_chart()
    
    def _calculate_financial_health_scores(self, income_records, expense_records):
        """计算财务健康各维度得分（0-100）"""
        from collections import defaultdict
        
        # 1. 收入稳定性
        income_stability = self._calc_income_stability(income_records)
        
        # 2. 支出控制
        expense_control = self._calc_expense_control(expense_records)
        
        # 3. 储蓄率
        savings_rate = self._calc_savings_rate(income_records, expense_records)
        
        # 4. 支出多样性
        expense_diversity = self._calc_expense_diversity(expense_records)
        
        # 5. 财务安全度
        financial_safety = self._calc_financial_safety(income_records, expense_records)
        
        return [income_stability, expense_control, savings_rate, expense_diversity, financial_safety]
    
    def _calc_income_stability(self, income_records):
        """计算收入稳定性得分"""
        if not income_records:
            return 30
        
        # 按收入类型统计
        income_by_type = defaultdict(float)
        for record in income_records:
            sr_name = record[2] or "其他"
            je = record[3] or 0
            income_by_type[sr_name] += je
        
        # 收入来源越多越稳定
        num_sources = len(income_by_type)
        score = min(100, num_sources * 20)
        
        return round(score, 1)
    
    def _calc_expense_control(self, expense_records):
        """计算支出控制得分"""
        if not expense_records:
            return 50
        
        # 按支出类型统计
        expense_by_type = defaultdict(float)
        for record in expense_records:
            zc_name = record[2] or "其他"
            je = record[3] or 0
            expense_by_type[zc_name] += je
        
        # 计算最大单项支出占比
        total_expense = sum(expense_by_type.values())
        if total_expense == 0:
            return 100
        
        max_single = max(expense_by_type.values())
        max_ratio = max_single / total_expense
        
        # 最大单项占比越低，控制越好
        if max_ratio < 0.3:
            score = 90
        elif max_ratio < 0.5:
            score = 80 - (max_ratio - 0.3) * 50
        elif max_ratio < 0.7:
            score = 70 - (max_ratio - 0.5) * 100
        else:
            score = max(0, 50 - (max_ratio - 0.7) * 100)
        
        return round(score, 1)
    
    def _calc_savings_rate(self, income_records, expense_records):
        """计算储蓄率得分"""
        total_income = sum(r[3] or 0 for r in income_records)
        total_expense = sum(r[3] or 0 for r in expense_records)
        
        if total_income == 0:
            return 0
        
        savings_rate = (total_income - total_expense) / total_income
        
        # 储蓄率转换为得分
        if savings_rate >= 0.3:
            score = 90 + min(10, (savings_rate - 0.3) * 33)
        elif savings_rate >= 0.2:
            score = 75 + (savings_rate - 0.2) * 150
        elif savings_rate >= 0.1:
            score = 60 + (savings_rate - 0.1) * 150
        elif savings_rate >= 0:
            score = 40 + savings_rate * 200
        else:
            score = max(0, 40 + savings_rate * 100)
        
        return round(score, 1)
    
    def _calc_expense_diversity(self, expense_records):
        """计算支出多样性得分"""
        if not expense_records:
            return 0
        
        # 统计支出类型数量
        expense_types = set()
        for record in expense_records:
            zc_name = record[2]
            if zc_name:
                expense_types.add(zc_name)
        
        num_types = len(expense_types)
        score = min(100, num_types * 12.5)  # 8种类型得满分
        
        return round(score, 1)
    
    def _calc_financial_safety(self, income_records, expense_records):
        """计算财务安全度得分"""
        total_income = sum(r[3] or 0 for r in income_records)
        total_expense = sum(r[3] or 0 for r in expense_records)
        
        if total_income == 0:
            return 0
        
        expense_ratio = total_expense / total_income
        
        # 支出占比越低越安全
        if expense_ratio < 0.5:
            score = 90 + (0.5 - expense_ratio) * 20
        elif expense_ratio < 0.7:
            score = 70 + (0.7 - expense_ratio) * 100
        elif expense_ratio < 0.9:
            score = 50 + (0.9 - expense_ratio) * 100
        elif expense_ratio < 1.0:
            score = 30 + (1.0 - expense_ratio) * 200
        else:
            score = max(0, 30 - (expense_ratio - 1.0) * 100)
        
        return round(score, 1)
    
    def clear_layout(self, layout):
        """清空布局中的所有组件"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _show_empty_chart(self):
        """显示空图表提示"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
               fontsize=14, color=UIStyles.TEXT_DISABLED, transform=ax.transAxes)
        ax.axis('off')
        self.canvas.draw()
    
    def delete_records(self):
        """删除选中的记录"""
        selected_rows = self.table.selectionModel().selectedRows()
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
            for index in sorted(selected_rows, key=lambda x: x.row(), reverse=True):
                row = index.row()
                zf_code = self.table.item(row, 3).text()
                print(f"[月报表] 删除记录：支付编码={zf_code}")
                self.table.removeRow(row)
            
            QMessageBox.information(self, "成功", "删除成功\n（数据库操作待开发）")
    
    def add_record(self):
        """添加记录"""
        print("[月报表] 添加记录")
        QMessageBox.information(self, "提示", 
            "月报表由系统自动生成，不支持手动添加\n请通过收入/支出记账功能添加记录后再生成月报")
    
    def init_data(self):
        """初始化数据"""
        print("[月报表] 初始化数据")
        QMessageBox.information(self, "提示", "初始化功能待开发")

    def reset_filters(self):
        """重置筛选条件"""
        print("[月报表] 重置筛选")
        self.current_year_month = "2025-12"
        self.load_data()
    
    def select_all(self):
        """全选"""
        print("[月报表] 全选")
        self.table.selectAll()
    
    def save_changes(self):
        """保存修改"""
        print("[月报表] 保存修改")
        QMessageBox.information(self, "提示", "保存功能待开发")
    
    def cancel_changes(self):
        """取消修改"""
        print("[月报表] 取消修改")
        self.load_data()
    
    def exit_page(self):
        """退出页面"""
        print("[月报表] 退出页面")
        from PyQt5.QtWidgets import QStackedWidget
        parent = self.parent()
        while parent and not isinstance(parent, QWidget):
            parent = parent.parent()
        
        if parent:
            stacked_widget = parent.findChild(QStackedWidget)
            if stacked_widget:
                stacked_widget.setCurrentIndex(0)
    
    def import_data(self):
        """导入数据"""
        print("[月报表] 导入数据")
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "导入 Excel 文件", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            print(f"[月报表] 选择文件：{file_path}")
            QMessageBox.information(self, "导入", 
                f"准备从 {file_path} 导入数据\n导入功能待开发")
    
    def export_data(self):
        """导出数据"""
        print("[月报表] 导出数据")
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出 Excel 文件", 
            f"月报表_{self.current_year_month}.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            print(f"[月报表] 导出到：{file_path}")
            QMessageBox.information(self, "导出", 
                f"数据将导出到 {file_path}\n导出功能待开发")