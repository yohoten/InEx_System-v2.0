# -*- coding: utf-8 -*-
"""
账单分析页面
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QFrame, QPushButton, QMessageBox,
                             QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from models.db_backend import db_manager
from ui.styles import UIStyles
from utils.chart_utils import chart_generator


class StatisticsPage(QWidget):
    """账单分析页面"""

    def __init__(self):
        super().__init__()
        self._cache = {}  # 数据缓存 {account: {records, timestamp}}
        self.initUI()
        self.load_charts()
    
    def initUI(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("📉 账单分析")
        title_label.setStyleSheet(UIStyles.page_title_style())
        layout.addWidget(title_label)
        
        # ========== Tab 切换 ==========
        self.tab_widget = QTabWidget()
        
        # 月度趋势标签页
        trend_tab = self.create_trend_tab()
        self.tab_widget.addTab(trend_tab, "📈 月度趋势")
        
        # 分类占比标签页
        pie_tab = self.create_pie_tab()
        self.tab_widget.addTab(pie_tab, "🥧 分类占比")
        
        # 高级分析标签页（新增）
        advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(advanced_tab, "🎯 高级分析")
        
        layout.addWidget(self.tab_widget)
        
        # ========== 底部按钮 ==========
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新图表")
        self.refresh_btn.setStyleSheet(UIStyles.primary_button())
        self.refresh_btn.clicked.connect(self.refresh_charts)
        btn_layout.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("📤 导出图表")
        self.export_btn.setStyleSheet(UIStyles.success_button())
        self.export_btn.clicked.connect(self.export_charts)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_trend_tab(self):
        """创建月度趋势标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 图表容器
        self.trend_container = QFrame()
        self.trend_container.setStyleSheet(UIStyles.white_background())
        trend_layout = QVBoxLayout()
        trend_layout.setContentsMargins(10, 10, 10, 10)
        self.trend_container.setLayout(trend_layout)
        layout.addWidget(self.trend_container)

        # 说明文字
        desc_label = QLabel(
            "📌 <b>图表说明：</b>折线图展示各月收入、支出和结余的变化趋势，"
            "帮助识别消费模式和储蓄能力。"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; padding: {UIStyles.PADDING_MEDIUM}px;")
        layout.addWidget(desc_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_pie_tab(self):
        """创建分类占比标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 图表容器
        self.pie_container = QFrame()
        self.pie_container.setStyleSheet(UIStyles.white_background())
        pie_layout = QVBoxLayout()
        pie_layout.setContentsMargins(10, 10, 10, 10)
        self.pie_container.setLayout(pie_layout)
        layout.addWidget(self.pie_container)

        # 说明文字
        desc_label = QLabel(
            "📌 <b>图表说明：</b>饼图展示各类支出的占比情况，"
            "帮助了解消费结构，优化支出分配。"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; padding: {UIStyles.PADDING_MEDIUM}px;")
        layout.addWidget(desc_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        """创建高级分析标签页（新增）"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 图表类型选择
        chart_type_layout = QHBoxLayout()
        chart_type_label = QLabel("📊 选择图表类型:")
        chart_type_label.setStyleSheet(f"font-weight: bold; color: {UIStyles.TEXT_SECONDARY};")
        chart_type_layout.addWidget(chart_type_label)
        
        # 图表类型单选按钮组
        self.advanced_chart_group = QButtonGroup()
        
        self.heatmap_radio = QRadioButton("🔥 消费热力图")
        self.calendar_heatmap_radio = QRadioButton("📅 日历热力图")
        self.sankey_radio = QRadioButton("🌊 资金流向图")
        self.radar_radio = QRadioButton("🎯 财务健康评估")
        
        for i, radio in enumerate([self.heatmap_radio, self.calendar_heatmap_radio, 
                                   self.sankey_radio, self.radar_radio]):
            radio.setCursor(Qt.PointingHandCursor)
            radio.setChecked(i == 0)
            self.advanced_chart_group.addButton(radio, i)
            chart_type_layout.addWidget(radio)
        
        self.advanced_chart_group.buttonClicked.connect(self.switch_advanced_chart)
        chart_type_layout.addStretch()
        layout.addLayout(chart_type_layout)
        
        # 图表容器
        self.advanced_container = QFrame()
        self.advanced_container.setStyleSheet(UIStyles.white_background())
        advanced_layout = QVBoxLayout()
        advanced_layout.setContentsMargins(10, 10, 10, 10)
        self.advanced_container.setLayout(advanced_layout)
        layout.addWidget(self.advanced_container)

        # 说明文字
        self.advanced_desc_label = QLabel(
            "📌 <b>热力图说明：</b>展示一周内不同时间段的消费分布情况，颜色越深表示消费金额越高。"
            "帮助识别消费高峰时段，优化消费习惯。"
        )
        self.advanced_desc_label.setWordWrap(True)
        self.advanced_desc_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; padding: {UIStyles.PADDING_MEDIUM}px;")
        layout.addWidget(self.advanced_desc_label)
        
        widget.setLayout(layout)
        return widget
    
    def switch_advanced_chart(self, button):
        """切换高级分析图表类型"""
        button_id = self.advanced_chart_group.id(button)
        
        if button_id == 0:
            self.advanced_desc_label.setText(
                "📌 <b>热力图说明：</b>展示一周内不同时间段的消费分布情况，颜色越深表示消费金额越高。"
                "帮助识别消费高峰时段，优化消费习惯。"
            )
        elif button_id == 1:
            self.advanced_desc_label.setText(
                "📌 <b>日历热力图说明：</b>展示一年内各日期的消费分布情况，颜色越深表示消费金额越高。"
                "帮助识别消费高峰日期，优化消费习惯。"
            )
        elif button_id == 2:
            self.advanced_desc_label.setText(
                "📌 <b>桑基图说明：</b>展示资金的流入和流出关系，直观呈现收入来源和支出去向。"
                "帮助理解资金流向，优化收支结构。"
            )
        else:
            self.advanced_desc_label.setText(
                "📌 <b>雷达图说明：</b>从多个维度评估财务健康状况，包括收入稳定性、支出控制、储蓄率等。"
                "得分范围0-100分，帮助您全面了解财务状况。"
            )
        
        # 重新加载对应的图表
        self.load_advanced_chart()
    
    def load_advanced_chart(self):
        """加载高级分析图表"""
        print("[高级分析] 加载图表...")
        
        button_id = self.advanced_chart_group.checkedId()
        
        try:
            if button_id == 0:
                # 热力图
                self._load_heatmap()
            elif button_id == 1:
                # 日历热力图
                self._load_calendar_heatmap()
            elif button_id == 2:
                # 桑基图
                self._load_sankey_chart()
            else:
                # 雷达图
                self._load_radar_chart()
        except Exception as e:
            print(f"[高级分析] 加载图表失败：{str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载图表失败:\n{str(e)}")
    
    def _load_heatmap(self):
        """加载热力图 - 消费时间段分析（基于数据库真实数据）"""
        from datetime import datetime
        import numpy as np
        
        print("[高级分析] 正在从数据库加载热力图数据...")
        
        # 获取所有支出记录
        expense_records = db_manager.get_expense_records()
        
        if not expense_records:
            print("[高级分析] 警告：数据库中暂无支出记录")
            QMessageBox.information(self, "提示", 
                "暂无支出数据生成热力图。\n\n请先添加一些支出记录后再查看。")
            self._show_empty_advanced_chart("暂无支出数据")
            return
        
        # 初始化 7天 x 24小时的数据矩阵
        heatmap_data = np.zeros((7, 24))
        record_count = 0
        
        # 统计每个时间段的消费金额
        for record in expense_records:
            # record: (djh, rq, zc_name, je, zf_name, bz)
            rq = record[1]  # 日期
            je = record[3] or 0  # 金额
            
            if rq and je > 0:
                try:
                    # 尝试解析日期时间
                    # 支持格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
                    if ' ' in str(rq):
                        dt = datetime.strptime(str(rq), '%Y-%m-%d %H:%M:%S')
                    else:
                        dt = datetime.strptime(str(rq), '%Y-%m-%d')
                    
                    weekday = dt.weekday()  # 0=周一, 6=周日
                    hour = dt.hour if hasattr(dt, 'hour') else 12  # 如果没有时间部分，默认中午
                    
                    # 累加该时间段的消费金额
                    heatmap_data[weekday, hour] += je
                    record_count += 1
                    
                except Exception as e:
                    print(f"[高级分析] 日期解析失败: {rq}, 错误: {e}")
                    continue
        
        print(f"[高级分析] 成功处理 {record_count} 条支出记录")
        
        # 检查是否有有效数据
        if np.sum(heatmap_data) == 0:
            print("[高级分析] 警告：所有记录的时间信息无法解析")
            QMessageBox.warning(self, "提示", 
                "支出记录中缺少有效的时间信息。\n\n"
                "请确保日期字段包含时间部分（如：2025-12-15 14:30:00）")
            self._show_empty_advanced_chart("时间信息缺失")
            return
        
        # 创建热力图
        x_labels = [f"{h}时" for h in range(24)]
        y_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        print("[高级分析] 正在生成热力图...")
        fig = chart_generator.create_heatmap(
            data=heatmap_data,
            x_labels=x_labels,
            y_labels=y_labels,
            title="消费时间段热力图",
            x_label="时间段",
            y_label="星期",
            figsize=(12, 7)
        )
        
        # 清除旧图表并嵌入新图表
        self.clear_layout(self.advanced_container.layout())
        canvas = chart_generator.embed_chart_in_widget(fig, self.advanced_container)
        self.advanced_container.layout().addWidget(canvas)
        
        print("[高级分析] 热力图加载完成")
    
    def _show_empty_advanced_chart(self, message: str = "暂无数据"):
        """显示空的高级分析图表提示"""
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        
        self.clear_layout(self.advanced_container.layout())
        
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha='center', va='center', 
               fontsize=14, color=UIStyles.TEXT_DISABLED, transform=ax.transAxes)
        ax.axis('off')
        
        canvas = FigureCanvas(fig)
        canvas.setParent(self.advanced_container)
        self.advanced_container.layout().addWidget(canvas)
    
    def _load_calendar_heatmap(self):
        """加载日历热力图 - 类似 GitHub 贡献图（基于数据库真实数据）"""
        from datetime import datetime
        
        print("[高级分析] 正在从数据库加载日历热力图数据...")
        
        # 获取所有支出记录
        expense_records = db_manager.get_expense_records()
        
        if not expense_records:
            print("[高级分析] 警告：数据库中暂无支出记录")
            QMessageBox.information(self, "提示", 
                "暂无支出数据生成日历热力图。\n\n请先添加一些支出记录后再查看。")
            self._show_empty_advanced_chart("暂无支出数据")
            return
        
        # 按日期聚合支出金额
        daily_expense = {}
        record_count = 0
        
        for record in expense_records:
            # record: (djh, rq, zc_name, je, zf_name, bz)
            rq = record[1]  # 日期
            je = record[3] or 0  # 金额
            
            if rq and je > 0:
                try:
                    # 尝试解析日期
                    # 支持格式：YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS
                    if ' ' in str(rq):
                        dt = datetime.strptime(str(rq), '%Y-%m-%d %H:%M:%S')
                    else:
                        dt = datetime.strptime(str(rq), '%Y-%m-%d')
                    
                    date_str = dt.strftime('%Y-%m-%d')
                    
                    # 累加该日期的消费金额
                    if date_str in daily_expense:
                        daily_expense[date_str] += je
                    else:
                        daily_expense[date_str] = je
                    
                    record_count += 1
                    
                except Exception as e:
                    print(f"[高级分析] 日期解析失败: {rq}, 错误: {e}")
                    continue
        
        print(f"[高级分析] 成功处理 {record_count} 条支出记录，涉及 {len(daily_expense)} 个日期")
        
        # 检查是否有有效数据
        if not daily_expense:
            print("[高级分析] 警告：所有记录的日期信息无法解析")
            QMessageBox.warning(self, "提示", 
                "支出记录中缺少有效的日期信息。\n\n"
                "请确保日期字段格式正确（如：2025-12-15）")
            self._show_empty_advanced_chart("日期信息缺失")
            return
        
        # 创建日历热力图
        print("[高级分析] 正在生成日历热力图...")
        fig = chart_generator.create_calendar_heatmap(
            daily_data=daily_expense,
            title="每日支出热力图",
            figsize=(14, 8)
        )
        
        # 清除旧图表并嵌入新图表
        self.clear_layout(self.advanced_container.layout())
        canvas = chart_generator.embed_chart_in_widget(fig, self.advanced_container)
        self.advanced_container.layout().addWidget(canvas)
        
        print("[高级分析] 日历热力图加载完成")
    
    def _load_sankey_chart(self):
        """加载桑基图 - 资金流向分析（基于数据库真实数据）"""
        print("[高级分析] 正在从数据库加载桑基图数据...")
        
        # 获取收入和支出数据
        income_records = db_manager.get_income_records()
        expense_records = db_manager.get_expense_records()
        
        if not income_records and not expense_records:
            print("[高级分析] 警告：数据库中暂无收支记录")
            QMessageBox.information(self, "提示", 
                "暂无收支数据生成桑基图。\n\n请先添加一些收支记录后再查看。")
            self._show_empty_advanced_chart("暂无收支数据")
            return
        
        # 按收入类型分组统计
        from collections import defaultdict
        income_by_type = defaultdict(float)
        for record in income_records:
            # record: (djh, rq, sr_name, je, zf_name, bz)
            sr_name = record[2] or "其他收入"
            je = record[3] or 0
            if je > 0:
                income_by_type[sr_name] += je
        
        # 按支出类型分组统计
        expense_by_type = defaultdict(float)
        for record in expense_records:
            # record: (djh, rq, zc_name, je, zf_name, bz)
            zc_name = record[2] or "其他支出"
            je = record[3] or 0
            if je > 0:
                expense_by_type[zc_name] += je
        
        print(f"[高级分析] 收入类型数: {len(income_by_type)}, 支出类型数: {len(expense_by_type)}")
        
        # 构建桑基图数据流
        flows = []
        
        # 计算总额
        total_income = sum(income_by_type.values())
        total_expense = sum(expense_by_type.values())
        
        # 收入流向总收入节点
        for source, value in income_by_type.items():
            if value > 0:
                flows.append({
                    'source': source,
                    'target': '总收入',
                    'value': round(value, 2)
                })
        
        # 总支出流向各支出类型
        for target, value in expense_by_type.items():
            if value > 0:
                flows.append({
                    'source': '总支出',
                    'target': target,
                    'value': round(value, 2)
                })
        
        # 如果有结余，显示从总收入到结余的流向
        if total_income > total_expense and total_income > 0:
            surplus = round(total_income - total_expense, 2)
            if surplus > 0:
                flows.append({
                    'source': '总收入',
                    'target': '净结余',
                    'value': surplus
                })
        
        # 如果支出大于收入，显示赤字
        elif total_expense > total_income and total_expense > 0:
            deficit = round(total_expense - total_income, 2)
            flows.append({
                'source': '赤字',
                'target': '总支出',
                'value': deficit
            })
        
        # 检查是否有足够的数据
        if not flows:
            print("[高级分析] 警告：无有效的资金流向数据")
            QMessageBox.warning(self, "提示", "暂无足够的收支数据生成桑基图")
            self._show_empty_advanced_chart("无有效资金流向")
            return
        
        # 收集所有节点
        nodes = set()
        for flow in flows:
            nodes.add(flow['source'])
            nodes.add(flow['target'])
        
        print(f"[高级分析] 生成 {len(flows)} 条资金流向，{len(nodes)} 个节点")
        
        # 创建桑基图
        print("[高级分析] 正在生成桑基图...")
        fig = chart_generator.create_sankey_chart(
            flows=flows,
            nodes=list(nodes),
            title="资金流向桑基图",
            figsize=(12, 7)
        )
        
        # 清除旧图表并嵌入新图表
        self.clear_layout(self.advanced_container.layout())
        canvas = chart_generator.embed_chart_in_widget(fig, self.advanced_container)
        self.advanced_container.layout().addWidget(canvas)
        
        print("[高级分析] 桑基图加载完成")
    
    def _load_radar_chart(self):
        """加载雷达图 - 财务健康评估（基于数据库真实数据）"""
        print("[高级分析] 正在从数据库加载财务健康评估数据...")
        
        # 获取所有收支记录
        income_records = db_manager.get_income_records()
        expense_records = db_manager.get_expense_records()
        
        if not income_records and not expense_records:
            print("[高级分析] 警告：数据库中暂无收支记录")
            QMessageBox.information(self, "提示", 
                "暂无收支数据生成财务健康评估。\n\n请先添加一些收支记录后再查看。")
            self._show_empty_advanced_chart("暂无收支数据")
            return
        
        # 数据统计
        total_income = sum(record[3] or 0 for record in income_records)
        total_expense = sum(record[3] or 0 for record in expense_records)
        
        print(f"[高级分析] 总收入: ¥{total_income:.2f}, 总支出: ¥{total_expense:.2f}")
        
        # 计算各维度得分（0-100）
        dimensions = [
            '收入稳定性',
            '支出控制',
            '储蓄率',
            '支出多样性',
            '财务安全度'
        ]
        
        values = [
            self._calculate_income_stability(income_records),
            self._calculate_expense_control(expense_records),
            self._calculate_savings_rate(income_records, expense_records),
            self._calculate_expense_diversity(expense_records),
            self._calculate_debt_ratio(income_records, expense_records)
        ]
        
        print(f"[高级分析] 五维度评分: {values}")
        
        # 创建雷达图
        print("[高级分析] 正在生成雷达图...")
        fig = chart_generator.create_radar_chart(
            dimensions=dimensions,
            values=values,
            title="财务健康评估雷达图",
            figsize=(8, 8)
        )
        
        # 清除旧图表并嵌入新图表
        self.clear_layout(self.advanced_container.layout())
        canvas = chart_generator.embed_chart_in_widget(fig, self.advanced_container)
        self.advanced_container.layout().addWidget(canvas)
        
        # 显示评分详情
        self._show_radar_score_details(dimensions, values)
        
        print("[高级分析] 雷达图加载完成")
    
    def _show_radar_score_details(self, dimensions: list, values: list):
        """显示雷达图评分详情（在图表下方添加文本说明）"""
        from PyQt5.QtWidgets import QTextEdit
        
        # 创建评分详情文本
        detail_text = "<b>📊 财务健康评分详情：</b><br><br>"
        
        for dim, val in zip(dimensions, values):
            if val >= 90:
                status = f"<span style='color: {UIStyles.SUCCESS}; font-weight: bold;'>优秀</span>"
                icon = "🟢"
            elif val >= 70:
                status = f"<span style='color: {UIStyles.INFO_HOVER}; font-weight: bold;'>良好</span>"
                icon = "🔵"
            elif val >= 50:
                status = f"<span style='color: {UIStyles.WARNING}; font-weight: bold;'>一般</span>"
                icon = "🟡"
            else:
                status = f"<span style='color: {UIStyles.DANGER}; font-weight: bold;'>需改进</span>"
                icon = "🔴"
            
            detail_text += f"{icon} <b>{dim}</b>: {val}分 - {status}<br>"
        
        avg_score = sum(values) / len(values)
        detail_text += f"<br><b>📈 综合评分</b>: <span style='font-size: 16px; color: {UIStyles.SIDEBAR_BG}; font-weight: bold;'>{avg_score:.1f}分</span>"
        
        # 添加建议
        detail_text += "<br><br><b>💡 改进建议：</b><br>"
        
        # 找出最低分的维度
        min_idx = values.index(min(values))
        suggestions = {
            0: "• 增加收入来源，发展副业或被动收入",
            1: "• 制定预算计划，控制大额支出",
            2: "• 提高储蓄比例，建议达到收入的20%以上",
            3: "• 多元化消费结构，避免单一类型支出过高",
            4: "• 控制支出在收入的70%以内，建立应急基金"
        }
        
        detail_text += suggestions.get(min_idx, "• 继续保持良好的财务习惯")
        
        # 创建文本框显示
        detail_label = QTextEdit()
        detail_label.setHtml(detail_text)
        detail_label.setReadOnly(True)
        detail_label.setMaximumHeight(180)
        detail_label.setStyleSheet(f"""
            QTextEdit {{
                background-color: {UIStyles.BG_GRAY_50};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 5px;
                padding: 10px;
                font-size: 11px;
            }}
        """)
        
        self.advanced_container.layout().addWidget(detail_label)
    
    def _calculate_income_stability(self, income_records):
        """计算收入稳定性得分（0-100）"""
        if not income_records:
            return 0
        
        # 按月统计收入
        from collections import defaultdict
        monthly_income = defaultdict(float)
        
        for record in income_records:
            rq = record[1]
            je = record[3] or 0
            if rq:
                month = rq[:7]
                monthly_income[month] += je
        
        if len(monthly_income) < 2:
            return 50  # 数据不足，给中等分数
        
        # 计算收入的变异系数（越小越稳定）
        values = list(monthly_income.values())
        mean_income = sum(values) / len(values)
        if mean_income == 0:
            return 0
        
        variance = sum((x - mean_income) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / mean_income  # 变异系数
        
        # 转换为得分：CV越小，得分越高
        # CV < 0.1 -> 90-100分
        # CV 0.1-0.3 -> 70-90分
        # CV 0.3-0.5 -> 50-70分
        # CV > 0.5 -> 0-50分
        if cv < 0.1:
            score = 95
        elif cv < 0.3:
            score = 80 - (cv - 0.1) * 50
        elif cv < 0.5:
            score = 70 - (cv - 0.3) * 100
        else:
            score = max(0, 50 - (cv - 0.5) * 50)
        
        return round(score, 1)
    
    def _calculate_expense_control(self, expense_records):
        """计算支出控制得分（0-100）"""
        if not expense_records:
            return 50
        
        # 按月统计支出
        from collections import defaultdict
        monthly_expense = defaultdict(float)
        
        for record in expense_records:
            rq = record[1]
            je = record[3] or 0
            if rq:
                month = rq[:7]
                monthly_expense[month] += je
        
        if len(monthly_expense) < 2:
            return 50
        
        # 计算支出的变异系数
        values = list(monthly_expense.values())
        mean_expense = sum(values) / len(values)
        if mean_expense == 0:
            return 100
        
        variance = sum((x - mean_expense) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / mean_expense
        
        # 支出越稳定，控制越好
        if cv < 0.15:
            score = 90
        elif cv < 0.3:
            score = 85 - (cv - 0.15) * 33
        elif cv < 0.5:
            score = 75 - (cv - 0.3) * 75
        else:
            score = max(0, 60 - (cv - 0.5) * 60)
        
        return round(score, 1)
    
    def _calculate_savings_rate(self, income_records, expense_records):
        """计算储蓄率得分（0-100）"""
        total_income = sum(record[3] or 0 for record in income_records)
        total_expense = sum(record[3] or 0 for record in expense_records)
        
        if total_income == 0:
            return 0
        
        savings_rate = (total_income - total_expense) / total_income
        
        # 储蓄率转换为得分
        # 储蓄率 >= 30% -> 90-100分
        # 20%-30% -> 75-90分
        # 10%-20% -> 60-75分
        # 0%-10% -> 40-60分
        # < 0% -> 0-40分
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
    
    def _calculate_expense_diversity(self, expense_records):
        """计算支出多样性得分（0-100）"""
        if not expense_records:
            return 0
        
        # 统计支出类型数量
        expense_types = set()
        for record in expense_records:
            zc_name = record[2]
            if zc_name:
                expense_types.add(zc_name)
        
        num_types = len(expense_types)
        
        # 类型越多，多样性越好（最多10种类型得满分）
        score = min(100, num_types * 10)
        
        return round(score, 1)
    
    def _calculate_debt_ratio(self, income_records, expense_records):
        """计算财务安全度得分（0-100）"""
        total_income = sum(record[3] or 0 for record in income_records)
        total_expense = sum(record[3] or 0 for record in expense_records)
        
        if total_income == 0:
            return 0
        
        expense_ratio = total_expense / total_income
        
        # 支出占比越低，财务越安全
        # 支出占比 < 50% -> 90-100分
        # 50%-70% -> 70-90分
        # 70%-90% -> 50-70分
        # 90%-100% -> 30-50分
        # > 100% -> 0-30分
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

    def load_charts(self, force=False):
        """加载图表数据（带缓存）"""
        account = db_manager.current_account
        cache_key = f"charts_{account}"
        if not force and cache_key in self._cache:
            print(f"[账单分析] 使用缓存数据")
            return
        self._cache[cache_key] = True
        print("[账单分析] 加载图表数据...")
        
        # 获取账单数据
        stats = db_manager.get_statistics()
        
        if not stats:
            print("[账单分析] 暂无数据")
            QMessageBox.warning(self, "提示", "暂无账单数据f")
            return
        
        # ========== 生成月度趋势图（从真实数据）==========
        try:
            # 获取所有月份的收入和支出
            months_data = self._get_monthly_data()
            
            if months_data:
                months = [item['month'] for item in months_data]
                income_data = [item['income'] for item in months_data]
                expense_data = [item['expense'] for item in months_data]
                balance_data = [item['balance'] for item in months_data]
                
                series_list = [
                    {'name': '收入', 'data': income_data, 'color': UIStyles.SUCCESS},
                    {'name': '支出', 'data': expense_data, 'color': UIStyles.DANGER},
                    {'name': '结余', 'data': balance_data, 'color': UIStyles.INFO}
                ]
                
                fig = chart_generator.create_line_chart(
                    categories=months,
                    series_list=series_list,
                    title='月度收支趋势分析',
                    x_label='月份',
                    y_label='金额（元）',
                    figsize=(10, 6)
                )
                
                # 清除旧图表
                self.clear_layout(self.trend_container.layout())
                
                # 嵌入新图表
                canvas = chart_generator.embed_chart_in_widget(fig, self.trend_container)
                self.trend_container.layout().addWidget(canvas)
            else:
                print("[账单分析] 无月度数据")
                
        except Exception as e:
            print(f"[账单分析] 生成趋势图失败：{str(e)}")
            import traceback
            traceback.print_exc()
        
        # ========== 生成支出占比饼图 ==========
        try:
            # 获取支出类型统计
            expense_types = db_manager.get_expense_types()
            expense_records = db_manager.get_expense_records()
            
            # 按支出类型分组统计
            type_amounts = {}
            for record in expense_records:
                # record: (djh, rq, zc_name, je, zf_name, bz)
                zc_name = record[2] or "未分类f"
                je = record[3] or 0
                type_amounts[zc_name] = type_amounts.get(zc_name, 0) + je
            
            if type_amounts:
                labels = list(type_amounts.keys())
                values = list(type_amounts.values())
                
                fig_pie = chart_generator.create_pie_chart(
                    labels=labels,
                    values=values,
                    title='支出分类占比',
                    figsize=(8, 8),
                    colors=[UIStyles.DANGER, UIStyles.INFO, UIStyles.SUCCESS, UIStyles.WARNING, UIStyles.ACCENT_PURPLE, UIStyles.SIDEBAR_SELECTED, UIStyles.WARNING]
                )
                
                # 清除旧图表
                self.clear_layout(self.pie_container.layout())
                
                # 嵌入新图表
                canvas_pie = chart_generator.embed_chart_in_widget(fig_pie, self.pie_container)
                self.pie_container.layout().addWidget(canvas_pie)
            else:
                print("[账单分析] 无支出数据")
                
        except Exception as e:
            print(f"[账单分析] 生成饼图失败：{str(e)}")
            import traceback
            traceback.print_exc()
        
        # ========== 加载高级分析图表（默认热力图）==========
        try:
            self.load_advanced_chart()
        except Exception as e:
            print(f"[账单分析] 加载高级分析图表失败：{str(e)}")
        
        print("[账单分析] 图表加载完成")
    
    def _get_monthly_data(self):
        """获取月度收支数据（从数据库）
        
        Returns:
            List[Dict]: 包含 month, income, expense, balance 的列表
        """
        from collections import defaultdict
        
        # 获取所有收入记录
        income_records = db_manager.get_income_records()
        # 获取所有支出记录
        expense_records = db_manager.get_expense_records()
        
        # 按月统计收入
        monthly_income = defaultdict(float)
        for record in income_records:
            # record: (djh, rq, sr_name, je, zf_name, bz)
            rq = record[1]  # 日期
            je = record[3]  # 金额
            if rq:
                month = rq[:7]  # YYYY-MM
                monthly_income[month] += je
        
        # 按月统计支出
        monthly_expense = defaultdict(float)
        for record in expense_records:
            # record: (djh, rq, zc_name, je, zf_name, bz)
            rq = record[1]
            je = record[3]
            if rq:
                month = rq[:7]
                monthly_expense[month] += je
        
        # 合并所有月份
        all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))
        
        result = []
        for month in all_months:
            income = monthly_income.get(month, 0)
            expense = monthly_expense.get(month, 0)
            balance = income - expense
            
            # 格式化月份显示（如 2025-09 -> 9月）
            month_display = f"{int(month.split('-')[1])}月"
            
            result.append({
                'month': month_display,
                'income': round(income, 2),
                'expense': round(expense, 2),
                'balance': round(balance, 2)
            })
        
        return result
    
    def clear_layout(self, layout):
        """清空布局中的所有组件"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def refresh_charts(self):
        """刷新图表"""
        print("[账单分析] 刷新图表...")
        self.load_charts()
        QMessageBox.information(self, "刷新完成", "图表已刷新")
    
    def export_charts(self):
        """导出图表"""
        print("[账单分析] 导出图表...")
        
        from PyQt5.QtWidgets import QFileDialog
        import tempfile
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出图表",
            "",
            "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                # 根据当前选中的Tab导出对应的图表
                current_tab = self.tab_widget.currentIndex()
                
                if current_tab == 0:
                    # 导出趋势图
                    if hasattr(self, 'trend_container'):
                        for i in range(self.trend_container.layout().count()):
                            item = self.trend_container.layout().itemAt(i)
                            if item.widget():
                                canvas = item.widget()
                                if hasattr(canvas, 'figure'):
                                    canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                                    break
                elif current_tab == 1:
                    # 导出饼图
                    if hasattr(self, 'pie_container'):
                        for i in range(self.pie_container.layout().count()):
                            item = self.pie_container.layout().itemAt(i)
                            if item.widget():
                                canvas = item.widget()
                                if hasattr(canvas, 'figure'):
                                    canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                                    break
                else:
                    # 导出高级分析图表
                    if hasattr(self, 'advanced_container'):
                        for i in range(self.advanced_container.layout().count()):
                            item = self.advanced_container.layout().itemAt(i)
                            if item.widget():
                                canvas = item.widget()
                                if hasattr(canvas, 'figure'):
                                    canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                                    break
                
                QMessageBox.information(self, "导出成功", f"图表已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出图表失败:\n{str(e)}")
