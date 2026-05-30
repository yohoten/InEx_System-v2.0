# -*- coding: utf-8 -*-
"""
首页-数据概况
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
                             QFrame, QSpacerItem, QSizePolicy, QTabWidget, QScrollArea,
                             QButtonGroup, QProgressDialog)
from PyQt5.QtCore import Qt, QUrl, QTimer

from PyQt5.QtGui import QFont, QColor, QDesktopServices, QCursor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from models.db_backend import db_manager
from models.budget_manager import BudgetManager, BudgetAlert
from ui.styles import UIStyles
from utils.logger import log_manager
from utils.ai_analyzer import SpendingAnalyzer
from datetime import datetime


class HomePage(QWidget):
    """首页 - 数据概况"""
    
    def __init__(self):
        super().__init__()
        # 初始化预算管理
        self.budget_manager = BudgetManager(db_manager)
        self.budget_alert = BudgetAlert(self.budget_manager)
        self.spending_analyzer = SpendingAnalyzer(db_manager)

        self.initUI()
        # 延迟加载图表，避免阻塞启动
        QTimer.singleShot(300, self._deferred_load)

    def _deferred_load(self):
        """延迟加载——先显示UI骨架，再加载数据"""
        self.load_data()
    
    def initUI(self):
        """初始化 UI"""
        
        # 创建滚动区域以支持更多内容
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff if hasattr(Qt, 'ScrollBarAlwaysOff') else 0)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {UIStyles.CONTENT_BG};
            }}
            QScrollBar:vertical {{
                border: none;
                background: {UIStyles.CONTENT_BG};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {UIStyles.BORDER_MEDIUM};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {UIStyles.TEXT_TERTIARY};
            }}
        """)
        
        # 主容器
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        main_layout.setSpacing(20)
        
        # ========== 欢迎标题区域 ==========
        header_frame = self.create_header_section()
        main_layout.addWidget(header_frame)
        
        # ========== 核心数据卡片区域（4列等宽）==========
        cards_grid = self.create_cards_section()
        main_layout.addWidget(cards_grid)
        
        # ========== 预算状态卡片 ==========
        budget_card = self.create_budget_card()
        main_layout.addWidget(budget_card)
        
        # ========== 图表分析区域（左右分栏）==========
        charts_section = self.create_charts_section()
        main_layout.addWidget(charts_section)
        
        # ========== 下部区域：占比分析 + 最近交易（左右分栏）==========
        bottom_section = self.create_bottom_split_section()
        main_layout.addWidget(bottom_section)
        
        # ========== 快捷操作按钮 ==========
        actions_section = self.create_actions_section()
        main_layout.addWidget(actions_section)
        
        main_layout.addStretch()
        
        scroll_area.setWidget(main_container)
        
        # 主布局
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)
        self.setLayout(outer_layout)
    
    def create_header_section(self):
        """创建欢迎标题区域"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:0.5 #8b5cf6, stop:1 #a78bfa);
                border-radius: 14px;
                padding: 4px;
            }
        """)
        header_frame.setFixedHeight(100)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 15, 30, 15)
        header_layout.setSpacing(5)
        
        # 标题
        title_label = QLabel("📊 数据概况")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 18, QFont.Bold))
        title_label.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(title_label)

        # 副标题 - 显示当前账套
        self.header_subtitle = QLabel()
        self.header_subtitle.setFont(QFont(UIStyles.FONT_FAMILY, 12))
        self.header_subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.85); background: transparent;")
        header_layout.addWidget(self.header_subtitle)
        self._refresh_header_subtitle()

        return header_frame

    def _refresh_header_subtitle(self):
        """刷新头部副标题（显示当前账套名称）"""
        try:
            account = db_manager.current_account
            accounts = db_manager.get_accounts()
            name = ""
            for acc in accounts:
                if acc[0] == account:
                    xm = acc[3] if len(acc) > 3 else ""
                    bj = acc[7] if len(acc) > 7 else ""
                    name = f"{xm} ({bj})" if xm else account
                    break
            self.header_subtitle.setText(f"当前账套：{name or account}")
        except Exception:
            self.header_subtitle.setText(f"当前账套：{db_manager.current_account}")
    
    def create_cards_section(self):
        """创建核心数据卡片区域"""
        cards_frame = QFrame()
        cards_frame.setStyleSheet("background-color: transparent;")
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(15)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建四个数据卡片（统一高度和样式）
        self.total_balance_card = self.create_modern_card("💰 总余额", "¥0.00", "#667eea", "#f0f3ff")
        self.total_income_card = self.create_modern_card("📈 总收入", "¥0.00", "#10b981", "#ecfdf5")
        self.total_expense_card = self.create_modern_card("📉 总支出", "¥0.00", "#ef4444", "#fef2f2")
        self.net_balance_card = self.create_modern_card("💵 净结余", "¥0.00", "#f59e0b", "#fffbeb")
        
        cards_layout.addWidget(self.total_balance_card, 0, 0)
        cards_layout.addWidget(self.total_income_card, 0, 1)
        cards_layout.addWidget(self.total_expense_card, 0, 2)
        cards_layout.addWidget(self.net_balance_card, 0, 3)
        
        return cards_frame
    
    def create_modern_card(self, title, value, color, bg_color):
        """创建现代化数据卡片（渐变背景 + hover微动效）"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_color}, stop:1 white);
                border-radius: 14px;
                border-left: 4px solid {color};
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 white, stop:0.9 {bg_color});
                border-left: 5px solid {color};
                margin-top: -2px;
            }}
        """)
        card.setMinimumHeight(110)
        card.setMaximumHeight(110)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(6)

        # 图标和标题
        title_label = QLabel(title)
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        title_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(title_label)

        # 数值（加大加粗）
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setFont(QFont(UIStyles.FONT_FAMILY, 22, QFont.Bold))
        value_label.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(value_label)

        layout.addStretch()

        return card
    
    def create_charts_section(self):
        """创建图表分析区域 - 支持多维度时间统计"""
        charts_frame = QFrame()
        charts_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        charts_layout = QVBoxLayout(charts_frame)
        charts_layout.setContentsMargins(20, 20, 20, 20)
        charts_layout.setSpacing(15)
        
        # 标题栏（包含时间维度选择器）
        title_layout = QHBoxLayout()
        
        section_title = QLabel("📊 收支趋势分析")
        section_title.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        section_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; background: transparent;")
        title_layout.addWidget(section_title)
        
        title_layout.addStretch()
        
        # ========== 时间范围选择器（）==========
        time_filter_frame = QFrame()
        time_filter_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.05),
                    stop:1 rgba(118, 75, 162, 0.05));
                border-radius: 10px;
                padding: 10px;
            }
        """)
        time_filter_layout = QHBoxLayout(time_filter_frame)
        time_filter_layout.setContentsMargins(15, 10, 15, 10)
        time_filter_layout.setSpacing(10)
        
        # 标签
        filter_label = QLabel("📅 时间范围:")
        filter_label.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        filter_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; background: transparent;")
        time_filter_layout.addWidget(filter_label)
        
        self.quick_range_group = QButtonGroup(self)
        
        # 快捷时间按钮样式函数
        def create_time_button(text, button_id, is_default=False):
            btn = QPushButton(text)
            btn.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Medium if is_default else QFont.Normal))
            btn.setCheckable(True)
            if is_default:
                btn.setChecked(True)
            btn.setCursor(QCursor(Qt.PointingHandCursor) if hasattr(Qt, 'PointingHandCursor') else QCursor())
            
            # 更明显的选中和悬停效果
            base_color = "#10b981" if is_default else "#667eea"
            hover_color = "#059669" if is_default else "#5568d3"
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: {UIStyles.TEXT_TERTIARY};
                    border: 2px solid {UIStyles.BORDER_LIGHT};
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: {{'bold' if is_default else 'normal'}};
                    min-width: 80px;
                }}
                QPushButton:checked {{
                    background-color: {base_color};
                    color: white;
                    border: 2px solid {base_color};
                    font-weight: bold;
                }}
                QPushButton:hover:!checked {{
                    background-color: {UIStyles.BG_GRAY_50};
                    border: 2px solid {hover_color};
                    color: {hover_color};
                }}
                QPushButton:hover:checked {{
                    background-color: {hover_color};
                    border: 2px solid {hover_color};
                }}
            """)
            self.quick_range_group.addButton(btn, button_id)
            return btn
        
        self.btn_all = create_time_button("📊 全部", 0, is_default=True)
        time_filter_layout.addWidget(self.btn_all)
        
        self.btn_week = create_time_button("📅 本周", 1)
        time_filter_layout.addWidget(self.btn_week)
        
        self.btn_month = create_time_button("📆 本月", 2)
        time_filter_layout.addWidget(self.btn_month)
        
        self.btn_year = create_time_button("📈 本年", 3)
        time_filter_layout.addWidget(self.btn_year)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #d1d5db;")
        time_filter_layout.addWidget(separator)
        
        # 时间维度标签
        dimension_label = QLabel("📐 显示方式:")
        dimension_label.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        dimension_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; background: transparent;")
        time_filter_layout.addWidget(dimension_label)
        
        self.time_range_group = QButtonGroup(self)
        
        # 时间维度按钮样式函数
        def create_dimension_button(text, icon, button_id, is_default=False):
            btn = QPushButton(f"{icon} {text}")
            btn.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Medium if is_default else QFont.Normal))
            btn.setCheckable(True)
            if is_default:
                btn.setChecked(True)
            btn.setCursor(QCursor(Qt.PointingHandCursor) if hasattr(Qt, 'PointingHandCursor') else QCursor())
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: #6b7280;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-weight: {'bold' if is_default else 'normal'};
                }}
                QPushButton:checked {{
                    background-color: #667eea;
                    color: white;
                    border: 2px solid #667eea;
                    font-weight: bold;
                }}
                QPushButton:hover:!checked {{
                    background-color: #f9fafb;
                    border: 2px solid #5568d3;
                    color: #5568d3;
                }}
                QPushButton:hover:checked {{
                    background-color: #5568d3;
                    border: 2px solid #5568d3;
                }}
            """)
            self.time_range_group.addButton(btn, button_id)
            return btn
        
        self.btn_daily = create_dimension_button("按日", "📅", 0)
        time_filter_layout.addWidget(self.btn_daily)
        
        self.btn_monthly = create_dimension_button("按月", "📆", 1, is_default=True)
        time_filter_layout.addWidget(self.btn_monthly)
        
        self.btn_yearly = create_dimension_button("按年", "📊", 2)
        time_filter_layout.addWidget(self.btn_yearly)
        
        time_filter_layout.addStretch()
        
        # 连接信号
        self.quick_range_group.buttonClicked.connect(self.on_quick_range_changed)
        self.time_range_group.buttonClicked.connect(self.on_time_range_changed)
        
        title_layout.addWidget(time_filter_frame)
        
        charts_layout.addLayout(title_layout)
        
        # 图表容器（全宽双轴图）
        chart_container = QFrame()
        chart_container.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border-radius: 10px;
            }
        """)
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(15, 15, 15, 15)
        chart_layout.setSpacing(10)
        
        # 动态标题
        self.chart_title_label = QLabel("📈 全部历史数据趋势")
        self.chart_title_label.setFont(QFont(UIStyles.FONT_FAMILY, 12, QFont.Bold))
        self.chart_title_label.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; background: transparent;")
        chart_layout.addWidget(self.chart_title_label)
        
        # 当前时间范围提示标签
        self.time_range_hint_label = QLabel("")
        self.time_range_hint_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.time_range_hint_label.setStyleSheet(f"""
            color: {UIStyles.TEXT_TERTIARY};
            background: transparent;
            padding: 4px 8px;
            border-radius: 4px;
        """)
        chart_layout.addWidget(self.time_range_hint_label)
        
        # 双轴图表：柱状图+折线图
        self.trend_dual_canvas = FigureCanvas(Figure(figsize=(12, 4.5)))
        self.trend_dual_canvas.setStyleSheet("background-color: transparent;")
        chart_layout.addWidget(self.trend_dual_canvas)
        
        charts_layout.addWidget(chart_container)
        
        return charts_frame
    
    def on_quick_range_changed(self, button):
        """快捷时间范围切换事件"""
        button_id = self.quick_range_group.id(button)
        
        # 更新图表标题并重新加载图表
        if button_id == 0:  # 全部历史
            self.chart_title_label.setText("📈 全部历史数据趋势")
            self.time_range_hint_label.setText("")
        elif button_id == 1:  # 本周
            from datetime import datetime, timedelta
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            self.chart_title_label.setText("📈 本周每日收支趋势")
            self.time_range_hint_label.setText(f"📅 {start_of_week.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}")
        elif button_id == 2:  # 本月
            from datetime import datetime
            today = datetime.now()
            start_of_month = today.replace(day=1)
            self.chart_title_label.setText("📈 本月每日收支趋势")
            self.time_range_hint_label.setText(f"📅 {start_of_month.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}")
        elif button_id == 3:  # 本年
            from datetime import datetime
            today = datetime.now()
            start_of_year = today.replace(month=1, day=1)
            self.chart_title_label.setText("📈 本年每月收支趋势")
            self.time_range_hint_label.setText(f"📅 {start_of_year.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}")
        
        # 重新加载图表
        self.load_trend_chart()
    
    def on_time_range_changed(self, button):
        """时间维度切换事件"""
        button_id = self.time_range_group.id(button)
        
        # 获取当前的快捷范围ID，用于组合显示
        quick_range_id = self.quick_range_group.checkedId()
        
        # 构建时间范围描述
        if quick_range_id == 0:
            range_desc = "全部历史数据"
        elif quick_range_id == 1:
            from datetime import datetime, timedelta
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            range_desc = f"{start_of_week.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}"
        elif quick_range_id == 2:
            from datetime import datetime
            today = datetime.now()
            start_of_month = today.replace(day=1)
            range_desc = f"{start_of_month.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}"
        elif quick_range_id == 3:
            from datetime import datetime
            today = datetime.now()
            start_of_year = today.replace(month=1, day=1)
            range_desc = f"{start_of_year.strftime('%Y-%m-%d')} 至 {today.strftime('%Y-%m-%d')}"
        else:
            range_desc = "全部历史数据"
        
        # 更新图表标题
        if button_id == 0:  # 按日
            self.chart_title_label.setText(f"📈 每日收支趋势")
            if quick_range_id != 0:
                self.time_range_hint_label.setText(f"📅 {range_desc}")
            else:
                self.time_range_hint_label.setText("")
        elif button_id == 1:  # 按月
            self.chart_title_label.setText(f"📈 每月收支趋势")
            if quick_range_id != 0:
                self.time_range_hint_label.setText(f"📅 {range_desc}")
            else:
                self.time_range_hint_label.setText("")
        elif button_id == 2:  # 按年
            self.chart_title_label.setText(f"📈 每年收支趋势")
            if quick_range_id != 0:
                self.time_range_hint_label.setText(f"📅 {range_desc}")
            else:
                self.time_range_hint_label.setText("")
        
        # 重新加载图表
        self.load_trend_chart()
    
    def load_trend_chart(self):
        """加载收支趋势双轴图（支持按日/月/年）"""
        try:
            # 获取当前选中的时间维度
            button_id = self.time_range_group.checkedId()
            
            if button_id == 0:  # 按日
                self._load_daily_trend()
            elif button_id == 1:  # 按月
                self._load_monthly_trend()
            elif button_id == 2:  # 按年
                self._load_yearly_trend()
                
        except Exception as e:
            print(f"[首页] 趋势图加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_date_range_filter(self):
        """根据快捷时间范围获取SQL WHERE条件"""
        from datetime import datetime, timedelta
        
        quick_range_id = self.quick_range_group.checkedId()
        
        if quick_range_id == 0:  # 全部历史数据
            return ""  # 不添加日期过滤
        elif quick_range_id == 1:  # 本周
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            return f" AND rq >= '{start_of_week.strftime('%Y-%m-%d')}'"
        elif quick_range_id == 2:  # 本月
            today = datetime.now()
            start_of_month = today.replace(day=1)
            return f" AND rq >= '{start_of_month.strftime('%Y-%m-%d')}'"
        elif quick_range_id == 3:  # 本年
            today = datetime.now()
            start_of_year = today.replace(month=1, day=1)
            return f" AND rq >= '{start_of_year.strftime('%Y-%m-%d')}'"
        else:
            return ""  # 默认全部历史数据
    
    def _load_daily_trend(self):
        """加载每日趋势"""
        try:
            # 获取日期范围过滤条件
            date_filter = self._get_date_range_filter()
            
            # 获取数据，按日统计（SQLite语法）
            sql = f"""
                SELECT DATE(rq) as day, 
                       SUM(CASE WHEN srzc = 'SR' THEN srje ELSE 0 END) as income,
                       SUM(CASE WHEN srzc = 'ZC' THEN zcje ELSE 0 END) as expense
                FROM sz_table_lsz 
                WHERE zth = ?{date_filter}
                GROUP BY DATE(rq)
                ORDER BY day
            """
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            
            print(f"[首页] 每日趋势图查询结果: {len(rows)} 条记录")
            
            if rows:
                days = [row[0][-5:] for row in rows]  # 取 MM-DD
                incomes = [row[1] for row in rows]
                expenses = [row[2] for row in rows]
                
                print(f"[首页] 渲染每日趋势图 - 日期范围: {days[0]} ~ {days[-1]}")
                self._render_dual_axis_chart(days, incomes, expenses, '日期', '每日')
            else:
                # 无数据时，检查是否有其他时间的数据
                has_any_data = self._check_if_has_any_data()
                if has_any_data:
                    # 有数据但不在当前时间范围内，显示提示
                    self._render_empty_chart_with_suggestion('每日')
                else:
                    # 完全无数据
                    self._render_dual_axis_chart([], [], [], '日期', '每日')
        except Exception as e:
            print(f"[首页] 每日趋势图加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _check_if_has_any_data(self):
        """检查数据库中是否有任何收支数据"""
        try:
            sql = "SELECT COUNT(*) FROM sz_table_lsz WHERE zth = ?"
            db_manager._backend.execute(sql, (db_manager.current_account,))
            count = db_manager._backend.fetchone()[0]
            print(f"[首页] 数据库总记录数: {count}")
            return count > 0
        except Exception as e:
            print(f"[首页] 检查数据失败: {e}")
            return False
    
    def _render_empty_chart_with_suggestion(self, time_unit):
        """渲染带建议的空图表"""
        try:
            fig = self.trend_dual_canvas.figure
            fig.clear()
            
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.7, f'暂无{time_unit}数据', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=14, color='#9ca3af', fontweight='bold')
            ax.text(0.5, 0.5, '💡 提示：', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=11, color='#6b7280')
            ax.text(0.5, 0.4, '当前时间范围可能没有数据', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10, color='#9ca3af')
            ax.text(0.5, 0.3, '请尝试切换“快捷范围”按钮', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10, color='#9ca3af')
            ax.text(0.5, 0.2, '或选择“按日/月/年”查看全部历史数据', ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10, color='#9ca3af')
            
            ax.set_title(f'{time_unit}收入与支出趋势', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_facecolor('#fafafa')
            ax.set_xticks([])
            ax.set_yticks([])
            
            self.trend_dual_canvas.draw()
        except Exception as e:
            print(f"[首页] 渲染建议图表失败: {e}")
    
    def _load_monthly_trend(self):
        """加载每月趋势（根据快捷范围过滤）"""
        try:
            # 获取日期范围过滤条件
            date_filter = self._get_date_range_filter()
            
            # 获取数据，按月统计（SQLite语法）
            sql = f"""
                SELECT strftime('%Y-%m', rq) as month, 
                       SUM(CASE WHEN srzc = 'SR' THEN srje ELSE 0 END) as income,
                       SUM(CASE WHEN srzc = 'ZC' THEN zcje ELSE 0 END) as expense
                FROM sz_table_lsz 
                WHERE zth = ?{date_filter}
                GROUP BY strftime('%Y-%m', rq)
                ORDER BY month
            """
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            
            if rows:
                months = [row[0] for row in rows]  # YYYY-MM
                incomes = [row[1] for row in rows]
                expenses = [row[2] for row in rows]
                
                self._render_dual_axis_chart(months, incomes, expenses, '月份', '每月')
            else:
                # 无数据时显示空图表
                self._render_dual_axis_chart([], [], [], '月份', '每月')
        except Exception as e:
            print(f"[首页] 每月趋势图加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_yearly_trend(self):
        """加载每年趋势（根据快捷范围过滤）"""
        try:
            # 获取日期范围过滤条件
            date_filter = self._get_date_range_filter()
            
            # 获取数据，按年统计（SQLite语法）
            sql = f"""
                SELECT strftime('%Y', rq) as year, 
                       SUM(CASE WHEN srzc = 'SR' THEN srje ELSE 0 END) as income,
                       SUM(CASE WHEN srzc = 'ZC' THEN zcje ELSE 0 END) as expense
                FROM sz_table_lsz 
                WHERE zth = ?{date_filter}
                GROUP BY strftime('%Y', rq)
                ORDER BY year
            """
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            
            if rows:
                years = [row[0] for row in rows]  # YYYY
                incomes = [row[1] for row in rows]
                expenses = [row[2] for row in rows]
                
                self._render_dual_axis_chart(years, incomes, expenses, '年份', '每年')
            else:
                # 无数据时显示空图表
                self._render_dual_axis_chart([], [], [], '年份', '每年')
        except Exception as e:
            print(f"[首页] 每年趋势图加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _render_dual_axis_chart(self, labels, incomes, expenses, x_label, title_prefix):
        """渲染双轴图表（通用方法）"""
        try:
            # 创建双轴图
            fig = self.trend_dual_canvas.figure
            fig.clear()
            
            if labels:
                ax1 = fig.add_subplot(111)
                
                # 左侧Y轴：柱状图显示收入和支出
                bar_width = 0.35
                x = range(len(labels))
                
                bars1 = ax1.bar([i - bar_width/2 for i in x], incomes, bar_width, 
                               label='收入', color='#10b981', alpha=0.8, edgecolor='white', linewidth=1.5)
                bars2 = ax1.bar([i + bar_width/2 for i in x], expenses, bar_width, 
                               label='支出', color='#ef4444', alpha=0.8, edgecolor='white', linewidth=1.5)
                
                ax1.set_xlabel(x_label, fontsize=11, color='#6b7280', fontweight='bold')
                ax1.set_ylabel('金额 (元)', fontsize=11, color='#6b7280', fontweight='bold')
                ax1.set_title(f'{title_prefix}收入与支出趋势', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                ax1.set_xticks(list(x))
                
                # 根据数据量调整标签显示
                if len(labels) <= 15:
                    ax1.set_xticklabels(labels, fontsize=10)
                elif len(labels) <= 30:
                    # 每隔一个显示
                    display_labels = [label if i % 2 == 0 else '' for i, label in enumerate(labels)]
                    ax1.set_xticklabels(display_labels, fontsize=9, rotation=45, ha='right')
                else:
                    # 只显示部分标签
                    step = len(labels) // 10
                    display_labels = [label if i % step == 0 else '' for i, label in enumerate(labels)]
                    ax1.set_xticklabels(display_labels, fontsize=8, rotation=45, ha='right')
                
                ax1.tick_params(axis='y', labelsize=9)
                
                # 添加数值标签（仅在数据点较少时显示）
                if len(labels) <= 20:
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            if height > 0:
                                ax1.text(bar.get_x() + bar.get_width()/2., height,
                                        f'{height:.0f}',
                                        ha='center', va='bottom', fontsize=8, fontweight='bold')
                
                # 右侧Y轴：折线图显示净结余
                ax2 = ax1.twinx()
                net_balance = [inc - exp for inc, exp in zip(incomes, expenses)]
                line = ax2.plot(x, net_balance, marker='D', linewidth=2.5, markersize=7,
                               label='净结余', color='#f59e0b', markerfacecolor='white',
                               markeredgewidth=2, markeredgecolor='#f59e0b', linestyle='--')
                
                ax2.set_ylabel('净结余 (元)', fontsize=11, color='#6b7280', fontweight='bold')
                ax2.tick_params(axis='y', labelsize=9)
                
                # 合并图例
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', 
                          fontsize=10, framealpha=0.95, edgecolor='#e5e7eb', 
                          facecolor='white', shadow=True)
                
                # 美化坐标轴
                ax1.spines['top'].set_visible(False)
                ax1.spines['right'].set_visible(False)
                ax1.spines['left'].set_color('#e5e7eb')
                ax1.spines['bottom'].set_color('#e5e7eb')
                ax2.spines['top'].set_visible(False)
                
                # 添加网格
                ax1.grid(True, linestyle='--', alpha=0.3, color='#d1d5db', axis='y')
                
                # 设置背景色
                ax1.set_facecolor('#fafafa')
                ax2.set_facecolor('#fafafa')
            else:
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, '暂无趋势数据', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=12, color='#9ca3af')
                ax.set_title(f'{title_prefix}收入与支出趋势', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.set_facecolor('#fafafa')
            
            self.trend_dual_canvas.draw()
        except Exception as e:
            print(f"[首页] 图表渲染失败: {e}")
            import traceback
            traceback.print_exc()
    
    def create_budget_card(self):
        """创建预算状态卡片"""
        budget_frame = QFrame()
        budget_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #e5e7eb;
            }
        """)
        
        budget_layout = QVBoxLayout(budget_frame)
        budget_layout.setContentsMargins(20, 15, 20, 15)
        budget_layout.setSpacing(10)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("💰 本月预算")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 预算状态标签
        self.budget_status_label = QLabel("未设置")
        self.budget_status_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.budget_status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {UIStyles.BG_GRAY_100};
                color: {UIStyles.TEXT_TERTIARY};
                padding: 4px 12px;
                border-radius: 12px;
            }}
        """)
        title_layout.addWidget(self.budget_status_label)
        budget_layout.addLayout(title_layout)
        
        # 预算金额显示
        amount_layout = QHBoxLayout()
        amount_layout.setSpacing(20)
        
        # 预算总额
        budget_amount_frame = QFrame()
        budget_amount_frame.setStyleSheet(UIStyles.info_box())
        budget_amount_layout = QVBoxLayout(budget_amount_frame)
        budget_amount_layout.setSpacing(5)
        
        budget_label = QLabel("预算总额")
        budget_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        budget_label.setStyleSheet(f"color: {UIStyles.INFO_HOVER};")
        budget_amount_layout.addWidget(budget_label)
        
        self.budget_total_value = QLabel("¥0.00")
        self.budget_total_value.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        self.budget_total_value.setStyleSheet(f"color: {UIStyles.INFO};")
        budget_amount_layout.addWidget(self.budget_total_value)
        
        amount_layout.addWidget(budget_amount_frame)
        
        # 已用金额
        spent_amount_frame = QFrame()
        spent_amount_frame.setStyleSheet(UIStyles.warning_box())
        spent_amount_layout = QVBoxLayout(spent_amount_frame)
        spent_amount_layout.setSpacing(5)
        
        spent_label = QLabel("已使用")
        spent_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        spent_label.setStyleSheet(f"color: #92400e;")
        spent_amount_layout.addWidget(spent_label)
        
        self.budget_spent_value = QLabel("¥0.00")
        self.budget_spent_value.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        self.budget_spent_value.setStyleSheet(f"color: {UIStyles.WARNING};")
        spent_amount_layout.addWidget(self.budget_spent_value)
        
        amount_layout.addWidget(spent_amount_frame)
        
        # 剩余金额
        remaining_amount_frame = QFrame()
        remaining_amount_frame.setStyleSheet(UIStyles.success_box())
        remaining_amount_layout = QVBoxLayout(remaining_amount_frame)
        remaining_amount_layout.setSpacing(5)
        
        remaining_label = QLabel("剩余额度")
        remaining_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        remaining_label.setStyleSheet(f"color: #065f46;")
        remaining_amount_layout.addWidget(remaining_label)
        
        self.budget_remaining_value = QLabel("¥0.00")
        self.budget_remaining_value.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        self.budget_remaining_value.setStyleSheet(f"color: {UIStyles.SUCCESS};")
        remaining_amount_layout.addWidget(self.budget_remaining_value)
        
        amount_layout.addWidget(remaining_amount_frame)
        
        budget_layout.addLayout(amount_layout)
        
        # 进度条
        progress_frame = QFrame()
        progress_frame.setStyleSheet(UIStyles.gray_background())
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(8)
        
        # 进度信息
        progress_info_layout = QHBoxLayout()
        self.progress_percent_label = QLabel("0%")
        self.progress_percent_label.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
        self.progress_percent_label.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY};")
        progress_info_layout.addWidget(self.progress_percent_label)
        progress_info_layout.addStretch()
        
        self.progress_detail_label = QLabel("¥0.00 / ¥0.00")
        self.progress_detail_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.progress_detail_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        progress_info_layout.addWidget(self.progress_detail_label)
        
        progress_layout.addLayout(progress_info_layout)
        
        # 进度条背景
        progress_bar_bg = QFrame()
        progress_bar_bg.setFixedHeight(12)
        progress_bar_bg.setStyleSheet(f"""
            QFrame {{
                background-color: {UIStyles.BORDER_LIGHT};
                border-radius: 6px;
            }}
        """)
        progress_layout.addWidget(progress_bar_bg)
        
        # 进度条
        self.progress_bar = QFrame()
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QFrame {
                background-color: #e5e7eb;
                border-radius: 6px;
            }
        """)
        progress_bar_layout = QHBoxLayout(progress_bar_bg)
        progress_bar_layout.setContentsMargins(0, 0, 0, 0)
        progress_bar_layout.setSpacing(0)
        
        # 进度条填充
        self.progress_bar_fill = QFrame()
        self.progress_bar_fill.setFixedHeight(12)
        self.progress_bar_fill.setMinimumWidth(0)
        self.progress_bar_fill.setStyleSheet("""
            QFrame {
                background-color: #10b981;
                border-radius: 6px;
            }
        """)
        progress_bar_layout.addWidget(self.progress_bar_fill)
        
        progress_layout.addWidget(progress_bar_bg)
        budget_layout.addWidget(progress_frame)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        set_budget_btn = QPushButton("⚙️ 设置预算")
        set_budget_btn.setCursor(Qt.PointingHandCursor)
        set_budget_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        set_budget_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
        """)
        set_budget_btn.clicked.connect(self.open_budget_settings)
        btn_layout.addWidget(set_budget_btn)
        
        btn_layout.addStretch()
        budget_layout.addLayout(btn_layout)
        
        return budget_frame
    
    def open_budget_settings(self):
        """打开预算设置对话框"""
        from PyQt5.QtWidgets import QInputDialog, QDoubleSpinBox, QDialog, QVBoxLayout, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("设置月度预算")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 月份显示 - 修复编码问题
        current_month = datetime.now().strftime('%Y-%m')
        month_label = QLabel(f"📅 当前月份：{current_month}")
        month_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        layout.addWidget(month_label)
        
        # 预算输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("💰 预算金额："))
        
        budget_spin = QDoubleSpinBox()
        budget_spin.setRange(0, 999999)
        budget_spin.setValue(0)
        budget_spin.setPrefix("¥ ")
        budget_spin.setDecimals(2)
        budget_spin.setFont(QFont(UIStyles.FONT_FAMILY, 12))
        input_layout.addWidget(budget_spin)
        
        layout.addLayout(input_layout)
        
        # 提示
        hint_label = QLabel("💡 建议设置为月收入的80%-90%")
        hint_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        hint_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        layout.addWidget(hint_label)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()

        ai_recommend_btn = QPushButton("🤖 AI 推荐")
        ai_recommend_btn.setStyleSheet(UIStyles.btn_style("#8b5cf6"))
        ai_recommend_btn.clicked.connect(lambda: self._ai_recommend_budget(budget_spin, dialog, current_month))
        btn_layout.addWidget(ai_recommend_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(UIStyles.btn_style("#10b981"))
        ok_btn.clicked.connect(lambda: self.save_budget(budget_spin.value(), dialog))
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def save_budget(self, amount, dialog):
        """保存预算设置"""
        current_month = datetime.now().strftime('%Y-%m')
        
        if self.budget_manager.set_monthly_budget(current_month, amount):
            QMessageBox.information(self, "成功", f"✅ 本月预算已设置为：¥{amount:.2f}")
            dialog.accept()
            # 审计日志
            from utils.auth_manager import AuthManager
            AuthManager()._write_audit_log(db_manager.current_account, "set_budget", current_month, f"¥{amount:.2f}")
            # 刷新预算卡片
            self.update_budget_card()
        else:
            QMessageBox.critical(self, "失败", "❌ 预算设置失败，请查看日志")
    
    def _ai_recommend_budget(self, budget_spin, dialog, current_month):
        """AI 智能推荐预算"""
        from utils.ai_assistant import AIConfigManager, AISuggestionsWorker

        # 收集历史预算数据
        budgets = self.budget_manager.get_all_budgets()
        history_lines = []
        for b in budgets[-6:]:
            history_lines.append(f"- {b['month']}: ¥{b['budget_amount']:.2f}")

        history_text = "\n".join(history_lines) if history_lines else "无历史预算记录"

        # 获取月均支出
        stats = db_manager.get_statistics()
        monthly_avg = stats.get('total_expense', 0) if stats else 0

        ai_config = AIConfigManager()
        api_key = ai_config.get_api_key()
        if not api_key:
            QMessageBox.warning(dialog, "提示", "请先在系统设置中配置 DeepSeek API Key")
            return

        prompt = f"""用户历史月度预算记录：
{history_text}

当前月均支出约: ¥{monthly_avg:.2f}

请根据以上数据，为用户推荐 {current_month} 的合理月度预算金额。
只返回一个数字（保留2位小数），不要包含任何其他文字。"""

        self._ai_worker = AISuggestionsWorker(
            api_key=api_key,
            model="deepseek-chat",
            prompt=prompt,
            temperature=0.3
        )

        def on_finished(content):
            try:
                amount = float(content.strip().replace('¥', '').replace(',', ''))
                budget_spin.setValue(amount)
                QMessageBox.information(dialog, "AI 推荐", f"AI 推荐预算: ¥{amount:.2f}")
            except ValueError:
                QMessageBox.warning(dialog, "解析失败", f"AI 返回无法解析: {content}")

        self._ai_worker.finished.connect(on_finished)
        self._ai_worker.error.connect(lambda e: QMessageBox.warning(dialog, "AI 错误", f"请求失败: {e}"))
        self._ai_worker.start()

    def update_budget_card(self):
        """更新预算卡片显示"""
        current_month = datetime.now().strftime('%Y-%m')
        
        # 获取预算状态
        status = self.budget_alert.get_budget_status_summary(current_month)
        
        if not status or status.get('status') == 'not_set':
            # 未设置预算
            self.budget_status_label.setText("未设置")
            self.budget_status_label.setStyleSheet("""
                QLabel {
                    background-color: #f3f4f6;
                    color: #6b7280;
                    padding: 4px 12px;
                    border-radius: 12px;
                }
            """)
            self.budget_total_value.setText("¥0.00")
            self.budget_spent_value.setText("¥0.00")
            self.budget_remaining_value.setText("¥0.00")
            self.progress_percent_label.setText("0%")
            self.progress_detail_label.setText("¥0.00 / ¥0.00")
            self.progress_bar_fill.setFixedWidth(0)
            self.progress_bar_fill.setStyleSheet("""
                QFrame {
                    background-color: #10b981;
                    border-radius: 6px;
                }
            """)
        else:
            budget = status['budget']
            actual = status['actual']
            remaining = status['remaining']
            usage_rate = status['usage_rate']
            status_type = status['status']
            
            # 更新数值
            self.budget_total_value.setText(f"¥{budget:.2f}")
            self.budget_spent_value.setText(f"¥{actual:.2f}")
            self.budget_remaining_value.setText(f"¥{remaining:.2f}")
            self.progress_percent_label.setText(f"{usage_rate:.1f}%")
            self.progress_detail_label.setText(f"¥{actual:.2f} / ¥{budget:.2f}")
            
            # 更新状态标签
            status_text_map = {
                'healthy': ('良好', '#10b981', '#ecfdf5'),
                'normal': ('正常', '#3b82f6', '#eff6ff'),
                'warning': ('即将超支', '#f59e0b', '#fffbeb'),
                'overrun': ('已超支', '#ef4444', '#fef2f2')
            }
            
            status_text, status_color, status_bg = status_text_map.get(status_type, ('未知', '#6b7280', '#f3f4f6'))
            self.budget_status_label.setText(status_text)
            self.budget_status_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {status_bg};
                    color: {status_color};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                }}
            """)
            
            # 更新进度条颜色和宽度
            progress_width = min(int(usage_rate * 3), 300)  # 最大宽度300px
            self.progress_bar_fill.setFixedWidth(max(progress_width, 0))
            
            if status_type == 'overrun':
                bar_color = '#ef4444'  # 红色
            elif status_type == 'warning':
                bar_color = '#f59e0b'  # 橙色
            elif status_type == 'normal':
                bar_color = '#3b82f6'  # 蓝色
            else:
                bar_color = '#10b981'  # 绿色
            
            self.progress_bar_fill.setStyleSheet(f"""
                QFrame {{
                    background-color: {bar_color};
                    border-radius: 6px;
                }}
            """)

    def create_bottom_split_section(self):
        """创建下部区域：占比分析 + 最近交易（优化布局）"""
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("background-color: transparent;")
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(15)
        
        # 左侧：占比分析（45%宽度）
        left_panel = self.create_analysis_panel()
        bottom_layout.addWidget(left_panel, 45)
        
        # 右侧：最近交易（55%宽度）
        right_panel = self.create_transactions_panel()
        bottom_layout.addWidget(right_panel, 55)
        
        return bottom_frame
    
    def create_analysis_panel(self):
        """创建左侧占比分析面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)

        # 标题
        section_title = QLabel("📊 分类占比分析")
        section_title.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        section_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; background: transparent;")
        panel_layout.addWidget(section_title)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {UIStyles.BG_GRAY_50};
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {UIStyles.BORDER_LIGHT};
                color: {UIStyles.TEXT_TERTIARY};
                padding: 10px 18px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: 11px;
                font-weight: 600;
                min-width: 80px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                color: {UIStyles.PRIMARY};
                border-bottom: 2px solid {UIStyles.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {UIStyles.BORDER_MEDIUM};
            }}
        """)
        
        # 收入占比标签页
        income_tab = self.create_ratio_tab("income")
        self.tab_widget.addTab(income_tab, "💰 收入")
        
        # 支出占比标签页
        expense_tab = self.create_ratio_tab("expense")
        self.tab_widget.addTab(expense_tab, "💸 支出")
        
        # 支付占比标签页
        payment_tab = self.create_ratio_tab("payment")
        self.tab_widget.addTab(payment_tab, "💳 支付")
        
        panel_layout.addWidget(self.tab_widget)
        
        return panel
    
    def create_transactions_panel(self):
        """创建右侧最近交易面板"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)
        
        # 标题栏
        title_layout = QHBoxLayout()
        
        section_title = QLabel("📝 最近交易记录")
        section_title.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        section_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; background: transparent;")
        title_layout.addWidget(section_title)
        
        title_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        refresh_btn.setCursor(QCursor(Qt.PointingHandCursor) if hasattr(Qt, 'PointingHandCursor') else QCursor())
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UIStyles.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {UIStyles.PRIMARY};
            }}
        """)
        refresh_btn.clicked.connect(self.load_data)
        title_layout.addWidget(refresh_btn)
        
        panel_layout.addLayout(title_layout)
        
        # 表格 - 优化样式
        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(5)
        self.recent_table.setHorizontalHeaderLabels(["日期", "类型", "类别", "金额", "备注"])
        
        # 安全访问 header
        h_header = self.recent_table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QHeaderView.Stretch)
            h_header.setMinimumSectionSize(60)
        
        v_header = self.recent_table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
            v_header.setDefaultSectionSize(35)
        
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 8px;
                gridline-color: {UIStyles.BG_GRAY_100};
                background-color: white;
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 8px 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {UIStyles.PRIMARY_LIGHT};
                color: {UIStyles.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {UIStyles.BG_GRAY_50};
                color: {UIStyles.TEXT_PRIMARY};
                font-weight: bold;
                padding: 10px 5px;
                border: none;
                border-bottom: 2px solid {UIStyles.BORDER_LIGHT};
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: 11px;
            }}
        """)
        self.recent_table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        panel_layout.addWidget(self.recent_table)
        
        return panel
    

    def create_ratio_tab(self, tab_type):
        """创建占比分析标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 饼图 - 调整大小
        pie_canvas = FigureCanvas(Figure(figsize=(6, 4)))
        layout.addWidget(pie_canvas)
        
        # 说明文字 - 优化样式
        info_label = QLabel()
        info_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        info_label.setStyleSheet("""
            QLabel {
                color: #4b5563;
                background-color: #f9fafb;
                padding: 12px;
                border-radius: 6px;
                border-left: 3px solid #667eea;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 保存引用
        if tab_type == "income":
            self.income_pie_canvas = pie_canvas
            self.income_ratio_label = info_label
        elif tab_type == "expense":
            self.expense_pie_canvas = pie_canvas
            self.expense_ratio_label = info_label
        else:
            self.payment_pie_canvas = pie_canvas
            self.payment_ratio_label = info_label
        
        return tab
    
    def create_actions_section(self):
        """创建快捷操作按钮区域 """
        actions_frame = QFrame()
        actions_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {UIStyles.BG_WHITE};
                border-radius: {UIStyles.BORDER_RADIUS_XLARGE}px;
            }}
        """)
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(15)
        
        # ========== 标题行 ==========
        title_layout = QHBoxLayout()
        actions_title = QLabel("⚡ 快捷操作")
        actions_title.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_TITLE, QFont.Bold))
        actions_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; background: transparent;")
        title_layout.addWidget(actions_title)
        title_layout.addStretch()
        actions_layout.addLayout(title_layout)
        
        # ========== 第一行：快速记账 ==========
        record_layout = QHBoxLayout()
        record_layout.setSpacing(12)
        
        btn_income = self._create_quick_action_button("💰 快速记收入", "#10b981", self.quick_add_income)
        record_layout.addWidget(btn_income)
        
        btn_expense = self._create_quick_action_button("💸 快速记支出", "#ef4444", self.quick_add_expense)
        record_layout.addWidget(btn_expense)
        
        actions_layout.addLayout(record_layout)
        
        # ========== 第二行：快速查询 ==========
        query_layout = QHBoxLayout()
        query_layout.setSpacing(12)
        
        btn_monthly = self._create_quick_action_button("📅 本月账单", "#3b82f6", lambda: self._switch_to_page(5))
        query_layout.addWidget(btn_monthly)
        
        btn_yearly = self._create_quick_action_button("📊 年度统计", "#8b5cf6", lambda: self._switch_to_page(6))
        query_layout.addWidget(btn_yearly)
        
        actions_layout.addLayout(query_layout)
        
        # ========== 第三行：数据管理 ==========
        data_layout = QHBoxLayout()
        data_layout.setSpacing(12)
        
        btn_budget = self._create_quick_action_button("🎯 预算管理", "#f59e0b", self.open_budget_management)
        data_layout.addWidget(btn_budget)
        
        btn_import = self._create_quick_action_button("📥 数据导入", "#06b6d4", self.open_data_import)
        data_layout.addWidget(btn_import)
        
        btn_export = self._create_quick_action_button("📤 数据导出", "#ec4899", self.open_data_export)
        data_layout.addWidget(btn_export)
        
        actions_layout.addLayout(data_layout)
        
        return actions_frame
    
    def _create_quick_action_button(self, text, color, callback):
        """创建快捷操作按钮"""
        btn = QPushButton(text)
        btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        btn.setCursor(QCursor(Qt.PointingHandCursor) if hasattr(Qt, 'PointingHandCursor') else QCursor())
        btn.setMinimumHeight(45)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._adjust_color(color, -20)};
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color(color, -40)};
            }}
        """)
        btn.clicked.connect(callback)
        return btn
    
    def _adjust_color(self, hex_color, amount):
        """调整颜色亮度"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _switch_to_page(self, index):
        """切换到指定页面"""
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page_by_index'):
            main_window.switch_to_page_by_index(index)
    
    def quick_add_income(self):
        """快速记收入 - 切换到收入记账页面"""
        self._switch_to_page(2)  # 收入记账页面索引为2
    
    def quick_add_expense(self):
        """快速记支出 - 切换到支出记账页面"""
        self._switch_to_page(3)  # 支出记账页面索引为3
    
    def open_budget_management(self):
        """打开预算管理 - 切换到系统设置页面"""
        self._switch_to_page(8)  # 系统设置页面索引为8
    
    def open_data_import(self):
        """打开数据导入"""
        try:
            from ui.dialogs.data_import_dialog import DataImportDialog
            dialog = DataImportDialog(self)
            if dialog.exec_():
                budget_warning = self.budget_alert.check_and_alert()
                if budget_warning:
                    QMessageBox.warning(self, "预算警告", budget_warning)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据导入失败：{str(e)}")
    
    def open_data_export(self):
        """打开数据导出"""
        try:
            from PyQt5.QtWidgets import QInputDialog
            choice, ok = QInputDialog.getItem(
                self, "选择导出格式", "请选择导出格式:",
                ["Excel (.xlsx)", "CSV (.csv)", "PDF报告 (.pdf)"], 0, False
            )
            if ok and choice:
                main_window = self.window()
                if hasattr(main_window, 'on_menu_action'):
                    if "Excel" in choice:
                        main_window.on_menu_action("导出 Excel")
                    elif "CSV" in choice:
                        main_window.on_menu_action("导出 CSV")
                    elif "PDF" in choice:
                        self.export_pdf_report()
        except Exception as e:
            log_manager.error(f"打开数据导出失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "错误", f"打开数据导出失败：{str(e)}")
    
    def load_pie_charts(self):
        """加载所有占比分析饼图"""
        try:
            # 加载收入占比饼图
            self._load_income_pie_chart()
            
            # 加载支出占比饼图
            self._load_expense_pie_chart()
            
            # 加载支付方式占比饼图
            self._load_payment_pie_chart()
            
            print("[首页] 饼图加载完成")
        except Exception as e:
            print(f"[首页] 饼图加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_income_pie_chart(self):
        """加载收入占比饼图 - """
        try:
            # 获取收入类型统计
            sql = """
                SELECT c.sr_name, SUM(s.je) as total
                FROM sz_sheet_sr s
                LEFT JOIN sz_c_sr c ON s.sr_code = c.sr_code
                WHERE s.zth = ?
                GROUP BY c.sr_name
                ORDER BY total DESC
            """
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            
            ax = self.income_pie_canvas.figure.subplots()
            ax.clear()
            
            if rows and any(row[1] > 0 for row in rows):
                labels = [row[0] or '未分类' for row in rows]
                sizes = [row[1] for row in rows]
                colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
                
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                   colors=colors[:len(labels)], startangle=90,
                                                   pctdistance=0.75, labeldistance=1.1)
                
                # 美化饼图
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')
                    autotext.set_color('white')
                
                for text in texts:
                    text.set_fontsize(10)
                
                ax.set_title('收入类型占比', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                
                # 更新说明文字
                total_income = sum(sizes)
                info_text = f"<b>总收入:</b> ¥{total_income:.2f}<br><br>"
                info_text += "<br>".join([f"• {label}: <b>¥{size:.2f}</b> ({size/total_income*100:.1f}%)" 
                                         for label, size in zip(labels, sizes)])
                self.income_ratio_label.setText(info_text)
            else:
                ax.text(0.5, 0.5, '暂无收入数据', ha='center', va='center', transform=ax.transAxes,
                       fontsize=12, color='#9ca3af')
                ax.set_title('收入类型占比', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                self.income_ratio_label.setText("💡 提示：添加收入记录后将在此处显示分析")
            
            self.income_pie_canvas.draw()
        except Exception as e:
            print(f"[首页] 收入饼图加载失败: {e}")
    
    def _load_expense_pie_chart(self):
        """加载支出占比饼图 - """
        try:
            # 获取支出类型统计
            sql = """
                SELECT c.zc_name, SUM(s.je) as total
                FROM sz_sheet_zc s
                LEFT JOIN sz_c_zc c ON s.zc_code = c.zc_code
                WHERE s.zth = ?
                GROUP BY c.zc_name
                ORDER BY total DESC
            """
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            
            ax = self.expense_pie_canvas.figure.subplots()
            ax.clear()
            
            if rows and any(row[1] > 0 for row in rows):
                labels = [row[0] or '未分类' for row in rows]
                sizes = [row[1] for row in rows]
                colors = ['#ef4444', '#f97316', '#f59e0b', '#eab308', '#6b7280', '#374151']
                
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                   colors=colors[:len(labels)], startangle=90,
                                                   pctdistance=0.75, labeldistance=1.1)
                
                # 美化饼图
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')
                    autotext.set_color('white')
                
                for text in texts:
                    text.set_fontsize(10)
                
                ax.set_title('支出类型占比', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                
                # 更新说明文字
                total_expense = sum(sizes)
                info_text = f"<b>总支出:</b> ¥{total_expense:.2f}<br><br>"
                info_text += "<br>".join([f"• {label}: <b>¥{size:.2f}</b> ({size/total_expense*100:.1f}%)" 
                                         for label, size in zip(labels, sizes)])
                self.expense_ratio_label.setText(info_text)
            else:
                ax.text(0.5, 0.5, '暂无支出数据', ha='center', va='center', transform=ax.transAxes,
                       fontsize=12, color='#9ca3af')
                ax.set_title('支出类型占比', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                self.expense_ratio_label.setText("💡 提示：添加支出记录后将在此处显示分析")
            
            self.expense_pie_canvas.draw()
        except Exception as e:
            print(f"[首页] 支出饼图加载失败: {e}")
    
    def _load_payment_pie_chart(self):
        """加载支付方式占比饼图 - """
        try:
            # 获取支付方式统计（合并收入和支出）
            sql = """
                SELECT z.zf_name, SUM(amount) as total
                FROM (
                    SELECT zf_code, je as amount FROM sz_sheet_sr WHERE zth = ?
                    UNION ALL
                    SELECT zf_code, je as amount FROM sz_sheet_zc WHERE zth = ?
                ) t
                LEFT JOIN sz_c_zf z ON t.zf_code = z.zf_code
                GROUP BY z.zf_name
                ORDER BY total DESC
            """
            db_manager._backend.execute(sql, (db_manager.current_account, db_manager.current_account))
            rows = db_manager._backend.fetchall()
            
            ax = self.payment_pie_canvas.figure.subplots()
            ax.clear()
            
            if rows and any(row[1] > 0 for row in rows):
                labels = [row[0] or '未分类' for row in rows]
                sizes = [row[1] for row in rows]
                colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6']
                
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                   colors=colors[:len(labels)], startangle=90,
                                                   pctdistance=0.75, labeldistance=1.1)
                
                # 美化饼图
                for autotext in autotexts:
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')
                    autotext.set_color('white')
                
                for text in texts:
                    text.set_fontsize(10)
                
                ax.set_title('支付方式占比', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                
                # 更新说明文字
                total_amount = sum(sizes)
                info_text = f"<b>总交易额:</b> ¥{total_amount:.2f}<br><br>"
                info_text += "<br>".join([f"• {label}: <b>¥{size:.2f}</b> ({size/total_amount*100:.1f}%)" 
                                         for label, size in zip(labels, sizes)])
                self.payment_ratio_label.setText(info_text)
            else:
                ax.text(0.5, 0.5, '暂无支付数据', ha='center', va='center', transform=ax.transAxes,
                       fontsize=12, color='#9ca3af')
                ax.set_title('支付方式占比', fontsize=13, fontweight='bold', pad=15, color='#1f2937')
                self.payment_ratio_label.setText("💡 提示：添加交易记录后将在此处显示分析")
            
            self.payment_pie_canvas.draw()
        except Exception as e:
            print(f"[首页] 支付方式饼图加载失败: {e}")
    
    def load_data(self, *args):
        """加载数据"""
        print("[首页] 开始加载数据...")

        try:
            self._refresh_header_subtitle()
            # 检查数据库连接
            if not db_manager.is_connected():
                print("[首页] ⚠️ 数据库未连接")
                QMessageBox.warning(self, "警告", "数据库未连接，无法加载数据")
                return
            
            # 获取统计数据
            stats = db_manager.get_statistics()
            
            if stats:
                # 更新卡片数据
                for card in [self.total_balance_card, self.total_income_card, 
                            self.total_expense_card, self.net_balance_card]:
                    value_label = card.findChild(QLabel, "value_label")
                    if value_label:
                        if card == self.total_balance_card:
                            value_label.setText(f"¥{stats['balance']:.2f}")
                        elif card == self.total_income_card:
                            value_label.setText(f"¥{stats['total_income']:.2f}")
                        elif card == self.total_expense_card:
                            value_label.setText(f"¥{stats['total_expense']:.2f}")
                        elif card == self.net_balance_card:
                            value_label.setText(f"¥{stats['balance']:.2f}")
                
                print(f"[首页] 统计数据 - 总收入: {stats['total_income']:.2f}, 总支出: {stats['total_expense']:.2f}, 结余: {stats['balance']:.2f}")
            else:
                print("[首页] 未获取到统计数据")
                return
            
            # 加载最近交易记录
            self._load_recent_transactions()
            
            # 加载趋势图
            self.load_trend_chart()
            
            # 加载占比分析饼图
            self.load_pie_charts()
            
            # 更新预算卡片
            self.update_budget_card()

            # 异常消费检测
            self._check_spending_anomalies()

            print("[首页] 数据加载完成")
            
        except Exception as e:
            print(f"[首页] ❌ 加载数据失败：{str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载数据失败：\n{str(e)}")
    
    def _check_spending_anomalies(self):
        """检查异常消费并显示警告"""
        try:
            analysis = self.spending_analyzer.analyze_spending_habits(months=1)
            anomalies = analysis.get('anomalies', [])
            if anomalies and len(anomalies) > 0:
                if not hasattr(self, 'toast'):
                    from ui.widgets.toast import Toast
                    self.toast = Toast(self)
                top = anomalies[0]
                msg = f"发现 {len(anomalies)} 笔异常消费 | 最大: {top['category']} ¥{top['amount']:.2f}"
                self.toast.warning(msg, duration=5000)
        except Exception as e:
            log_manager.warning(f"[首页] 异常检测失败: {e}")

    def _load_recent_transactions(self):
        """加载最近交易记录 - """
        try:
            # 获取最近 10 条流水记录（SQL LIMIT，不加载全表）
            recent_records = db_manager.get_cash_flow(limit=10)

            if not recent_records:
                self.recent_table.setRowCount(0)
                print("[首页] 无交易记录")
                return
            
            self.recent_table.setRowCount(len(recent_records))
            
            for row, record in enumerate(recent_records):
                rq = record[0] or ""
                srzc = record[2] or ""
                srje = record[5] or 0
                zcje = record[7] or 0
                bz = record[10] if len(record) > 10 else ""
                
                # 格式化显示
                type_text = "收入" if srzc == 'SR' else "支出"
                amount = f"+¥{srje:.2f}" if srzc == 'SR' else f"-¥{zcje:.2f}"
                category = sr_code_to_name(srzc, record[4]) if srzc == 'SR' else zc_code_to_name(record[6])
                
                # 设置单元格
                items = [rq, type_text, category, amount, bz or "-"]
                for col, value in enumerate(items):
                    item = QTableWidgetItem(str(value))
                    if hasattr(Qt, 'AlignCenter'):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        from PyQt5.QtCore import Qt as QtCore
                        item.setTextAlignment(QtCore.AlignCenter)
                    
                    # 根据类型设置颜色
                    if col == 1:  # 类型列
                        if srzc == 'SR':
                            item.setForeground(QColor("#10b981"))
                            item.setBackground(QColor("#d1fae5"))
                            item.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
                        else:
                            item.setForeground(QColor("#ef4444"))
                            item.setBackground(QColor("#fee2e2"))
                            item.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
                    elif col == 3:  # 金额列
                        if srzc == 'SR':
                            item.setForeground(QColor("#10b981"))
                            item.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
                        else:
                            item.setForeground(QColor("#ef4444"))
                            item.setFont(QFont(UIStyles.FONT_FAMILY, 11, QFont.Bold))
                    else:
                        item.setForeground(QColor("#374151"))
                    
                    self.recent_table.setItem(row, col, item)
            
            print(f"[首页] 最近交易记录加载完成（{len(recent_records)} 条）")
                
        except Exception as e:
            print(f"[首页] ❌ 加载交易记录失败：{str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载交易记录失败：\n{str(e)}")
    
    def on_item_double_clicked(self, item):
        """处理单元格双击编辑"""
        print(f"[首页] 编辑单元格：行{item.row()+1}, 列{item.column()+1}, 值={item.text()}")
    
    def export_pdf_report(self):
        """导出增强版 PDF 财务分析报告"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存 PDF 报告", "收支分析报告.pdf", "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            # 使用增强版PDF报告生成器
            from utils.pdf_report_generator import PDFReportGenerator

            # 创建进度条对话框
            progress = QProgressDialog("正在生成报告，请稍候...", "取消", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle("生成PDF报告")
            progress.setMinimumDuration(500)  # 500ms后显示
            progress.setValue(0)
            progress.show()
            
            # 模拟进度更新（因为PDF生成是同步操作）
            from PyQt5.QtCore import QTimer
            progress_step = [0]
            
            def update_progress():
                progress_step[0] += 10
                if progress_step[0] <= 90:
                    progress.setValue(progress_step[0])
                    progress.setLabelText(f"正在生成报告... {progress_step[0]}%")
                    QTimer.singleShot(200, update_progress)
            
            # 启动进度动画
            QTimer.singleShot(200, update_progress)
            
            # 生成报告
            generator = PDFReportGenerator()
            generator.generate_report(file_path)
            
            # 完成进度
            progress.setValue(100)
            progress.setLabelText("报告生成完成！")
            
            QMessageBox.information(self, "成功", f"报告已导出至:\n{file_path}")
            log_manager.info(f"[首页] 增强版PDF报告导出成功: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
            log_manager.error(f"[首页] PDF导出错误: {str(e)}")


def sr_code_to_name(srzc, code):
    """收入代码转名称"""
    if not code:
        return "未分类"
    
    from models.db_backend import db_manager
    types = db_manager.get_income_types()
    for c, name in types:
        if c == code:
            return name
    return "未知"


def zc_code_to_name(code):
    """支出代码转名称"""
    if not code:
        return "未分类"
    
    from models.db_backend import db_manager
    types = db_manager.get_expense_types()
    for c, name in types:
        if c == code:
            return name
    return "未知"
