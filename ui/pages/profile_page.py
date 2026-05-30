# -*- coding: utf-8 -*-
"""
个人中心页面：管理账套信息和查看统计分布
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
                             QGroupBox, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QFrame, QTabWidget, QFileDialog,
                             QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sqlite3
from datetime import datetime

from models.db_backend import db_manager
from models.budget_manager import BudgetManager, BudgetAlert
from ui.widgets.toast import Toast
from ui.utils.error_handler import ErrorLevel, show_error, show_technical_error
from ui.styles import UIStyles


class ProfilePage(QWidget):
    """个人中心页面 - 账套管理与统计分析"""
    
    def __init__(self):
        super().__init__()
        # 初始化预算管理
        self.budget_manager = BudgetManager(db_manager)
        self.budget_alert = BudgetAlert(self.budget_manager)
        
        self.initUI()
        # 创建Toast组件
        self.toast = Toast(self)
        self.load_data_from_database()
    
    def initUI(self):
        """初始化界面"""
        main_layout = QVBoxLayout()
        # 统一 margins/spacing 为 24/15
        main_layout.setContentsMargins(UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING, UIStyles.PAGE_PADDING)
        main_layout.setSpacing(15)
        
        # 创建标题区域（与其他页面风格统一，无副标题）
        title_label = QLabel("👤 个人中心")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_TITLE, QFont.Bold))
        title_label.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; "
                                  f"padding: 0px 0px {UIStyles.PADDING_SMALL}px 0px;")
        main_layout.addWidget(title_label)
        
        # ========== 主内容区域（使用现代 Tab 组织）==========
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet(self._modern_tab_style())
        
        # 我的账套标签页
        profile_tab = self.create_profile_tab()
        tab_widget.addTab(profile_tab, "👤 我的账套")
        
        # 账套管理标签页
        list_tab = self.create_list_tab()
        tab_widget.addTab(list_tab, "📋 账套管理")
        
        # 统计分析标签页
        stats_tab = self.create_stats_tab()
        tab_widget.addTab(stats_tab, "📊 统计分析")
        
        # 预算管理标签页
        budget_tab = self.create_budget_tab()
        tab_widget.addTab(budget_tab, "💰 预算管理")
        
        main_layout.addWidget(tab_widget)
        
        self.setLayout(main_layout)
    
    def _modern_tab_style(self):
        """增强版现代标签页样式"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                background-color: {UIStyles.BG_WHITE};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {UIStyles.BG_GRAY_50};
                color: {UIStyles.TEXT_TERTIARY};
                padding: {UIStyles.PADDING_MEDIUM}px {UIStyles.PADDING_XLARGE}px;
                margin-right: 2px;
                border-top-left-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                border-top-right-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                font-weight: bold;
                font-size: {UIStyles.FONT_SIZE_MEDIUM}px;
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-bottom: none;
                min-width: 100px;
            }}
            QTabBar::tab:selected {{
                background-color: {UIStyles.BG_WHITE};
                color: {UIStyles.TEXT_PRIMARY};
                border-bottom: 2px solid {UIStyles.PRIMARY};
                margin-bottom: -1px;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {UIStyles.BG_GRAY_100};
            }}
        """
    
    def load_data_from_database(self):
        """从数据库加载账套数据 - 优化错误提示"""
        # 检查数据库连接
        if not db_manager.is_connected():
            self.show_empty_state()
            if hasattr(self, 'toast'):
                self.toast.warning(
                    "数据库未连接\n请在「系统设置」中配置数据库",
                    5000
                )
            else:
                QMessageBox.warning(
                    self,
                    "数据库未连接",
                    "⚠️ 数据库未连接\n\n"
                    "请在「系统设置」中配置数据库连接",
                    QMessageBox.Ok
                )
            return
        
        try:
            # 获取所有账套信息
            accounts = db_manager.get_accounts()
            
            # 清空表格
            if hasattr(self, 'table'):
                self.table.setRowCount(0)
            
            if not accounts:
                self.show_empty_state()
                # 清空账套输入框
                if hasattr(self, 'zth_input'):
                    self.zth_input.clear()
                if hasattr(self, 'xm_input'):
                    self.xm_input.clear()
                
                # 显示友好提示
                if hasattr(self, 'toast'):
                    self.toast.info("暂无账套数据，请点击「新增账套」创建", 3000)
                return
            
            # 填充表格：账套号、姓名、班级、小组
            for account in accounts:
                row = self.table.rowCount()
                self.table.insertRow(row)
                zth = str(account[0]) if len(account) > 0 else ""
                xm = str(account[3]) if len(account) > 3 else ""
                bj = str(account[7]) if len(account) > 7 else ""
                xz = str(account[8]) if len(account) > 8 else ""
                for col, val in enumerate([zth, xm, bj, xz]):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)
                # 存储zth用于切换
                if self.table.item(row, 0):
                    self.table.item(row, 0).setData(Qt.UserRole, zth)

            # 加载当前登录账套的信息到编辑区
            current_zth = db_manager.current_account
            found = False
            for acc in accounts:
                zth = str(acc[0]) if len(acc) > 0 else ""
                if zth == current_zth:
                    self._fill_account_form(acc)
                    found = True
                    break
            if not found and accounts:
                self._fill_account_form(accounts[0])

            if hasattr(self, 'status_label'):
                self.status_label.setText(f"✅ 已加载 {len(accounts)} 个账套")
            
            # 更新统计数据
            self.update_statistics()
            
            # 显示成功提示
            if hasattr(self, 'toast'):
                self.toast.success(f"成功加载 {len(accounts)} 个账套", 2000)
            
        except sqlite3.OperationalError as e:
            # 数据库表缺失错误
            if "no such table" in str(e):
                QMessageBox.warning(
                    self,
                    "数据库表缺失",
                    "⚠️ 检测到数据库表结构不完整\n\n"
                    "可能原因:\n"
                    "1. 数据库文件损坏\n"
                    "2. 未执行初始化脚本\n\n"
                    "解决方法:\n"
                    "1. 关闭应用\n"
                    "2. 运行: python utils/db_initializer.py\n"
                    "3. 重新启动应用\n\n"
                    "或者在「系统设置」中重新初始化数据库",
                    QMessageBox.Ok
                )
            else:
                self.show_technical_error(e)
        
        except Exception as e:
            # 其他异常
            self.show_technical_error(e)
    
    def show_technical_error(self, error):
        """显示技术性错误"""
        reply = QMessageBox.question(
            self,
            "发生错误",
            f"❌ 操作失败\n\n"
            f"错误信息: {str(error)}\n\n"
            f"是否查看详细技术信息？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.critical(
                self,
                "技术详情",
                f"错误类型: {type(error).__name__}\n"
                f"错误信息: {str(error)}\n"
                f"时间: {datetime.now()}\n\n"
                f"建议:\n"
                f"1. 检查数据库连接\n"
                f"2. 查看日志文件: data/app.log\n"
                f"3. 联系技术支持"
            )
        else:
            # 即使用户选择不查看详情，也显示简要提示
            if hasattr(self, 'toast'):
                self.toast.error("操作失败，请查看日志或联系技术支持")
    
    def show_empty_state(self):
        """显示空数据状态"""
        if hasattr(self, 'table'):
            self.table.setRowCount(0)
        if hasattr(self, 'status_label'):
            self.status_label.setText("暂无账套数据，请先创建账套")
        
        # 清空统计 - 直接更新已知的指标标签（现在是真正的 QLabel 对象）
        if hasattr(self, 'total_accounts_label') and isinstance(self.total_accounts_label, QLabel):
            self.total_accounts_label.setText("0")
        if hasattr(self, 'active_accounts_label') and isinstance(self.active_accounts_label, QLabel):
            self.active_accounts_label.setText("0")
        if hasattr(self, 'recent_label') and isinstance(self.recent_label, QLabel):
            self.recent_label.setText("-")
        
        # 安全地更新预算概览卡片中的数值标签
        if hasattr(self, 'budget_overview_cards'):
            for key, card in self.budget_overview_cards.items():
                if isinstance(card, QFrame):
                    for child in card.children():
                        if isinstance(child, QLabel):
                            try:
                                if child.font().bold():
                                    child.setText("0" if key != 'usage' else "0%")
                                    break
                            except (AttributeError, TypeError):
                                continue
    
    def update_statistics(self):
        """更新统计信息"""
        if not hasattr(self, 'table'):
            return
        
        total_count = self.table.rowCount()
        
        # 计算活跃账套数（假设最近30天有操作的为活跃账套）
        active_count = self._calculate_active_accounts()
        
        # 获取最近创建的账套
        recent_account = self._get_recent_account()
        
        # 更新指标标
        if hasattr(self, 'total_accounts_label'):
            self.total_accounts_label.setText(
                f"<b>总账套数:</b> <span style='color:#667eea;font-size:14px;font-weight:bold;'>{total_count}</span>"
            )
        
        if hasattr(self, 'active_accounts_label'):
            self.active_accounts_label.setText(
                f"<b>活跃账套:</b> <span style='color:#10b981;font-size:14px;font-weight:bold;'>{active_count}</span>"
            )
        
        if hasattr(self, 'recent_label'):
            self.recent_label.setText(
                f"<b>最近创建:</b> <span style='color:#f59e0b;font-size:14px;font-weight:bold;'>{recent_account}</span>"
            )
        
        # 更新状态栏
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"统计已更新 | 总计: {total_count}个账套 | 活跃: {active_count}个")
        
        # 更新图表
        self._update_charts()
    
    def _calculate_active_accounts(self):
        """计算活跃账套数（最近30天有收支记录）"""
        try:
            query = """
                SELECT COUNT(DISTINCT zth) 
                FROM (
                    SELECT zth FROM sz_sheet_sr WHERE rq >= date('now', '-30 days')
                    UNION
                    SELECT zth FROM sz_sheet_zc WHERE rq >= date('now', '-30 days')
                )
            """
            db_manager._backend.execute(query)
            result = db_manager._backend.fetchall()
            if result and len(result) > 0:
                return result[0][0]
        except Exception as e:
            print(f"[个人中心] 计算活跃账套失败: {e}")
        
        return 0
    
    def _get_recent_account(self):
        """获取最近创建的账套名称"""
        try:
            # 使用xm(姓名)字段作为账套名称,如果为空则使用zth(账套号)
            query = "SELECT xm, zth FROM sz_d_zt ORDER BY zth DESC LIMIT 1"
            db_manager._backend.execute(query)
            result = db_manager._backend.fetchall()
            if result and len(result) > 0:
                xm, zth = result[0]
                # 优先使用姓名,如果为空则使用账套号
                return str(xm) if xm and str(xm).strip() else str(zth)
        except Exception as e:
            print(f"[个人中心] 获取最近账套失败: {e}")
        
        return "-"
    
    def _update_charts(self):
        """更新图表显示"""
        if hasattr(self, 'pie_figure'):
            self._draw_account_type_pie_chart()
        
        if hasattr(self, 'line_figure'):
            self._draw_account_creation_trend()
    
    def _draw_account_type_pie_chart(self):
        """绘制账套类型分布饼图"""
        try:
            self.pie_figure.clear()
            ax = self.pie_figure.add_subplot(111)
            
            # 示例数据：按账套号前缀分类
            accounts = db_manager.get_accounts()
            if not accounts:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                       fontsize=14, color='#9ca3af', transform=ax.transAxes)
                ax.axis('off')
                self.pie_canvas.draw()
                return
            
            # 简单分类：按账套号范围分组
            type_counts = {'教学账套': 0, '实训账套': 0, '其他': 0}
            for account in accounts:
                zth = str(account[0])
                if zth.startswith('2501'):
                    type_counts['教学账套'] += 1
                elif zth.startswith('2502'):
                    type_counts['实训账套'] += 1
                else:
                    type_counts['其他'] += 1
            
            labels = list(type_counts.keys())
            sizes = list(type_counts.values())
            colors = ['#667eea', '#10b981', '#f59e0b']
            
            # 过滤掉数量为0的分类
            filtered_data = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
            if not filtered_data:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                       fontsize=14, color='#9ca3af', transform=ax.transAxes)
                ax.axis('off')
                self.pie_canvas.draw()
                return
            
            labels, sizes, colors = zip(*filtered_data)
            
            # 绘制饼图
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.0f%%',
                                              colors=colors, startangle=90,
                                              pctdistance=0.75, wedgeprops=dict(width=0.5, edgecolor='white'))
            
            # 设置字体
            for text in texts:
                text.set_fontsize(9)
                text.set_fontweight('bold')
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_fontweight('bold')
                autotext.set_color('white')
            
            ax.set_title('账套类型分布', fontsize=11, fontweight='bold', color='#374151', pad=8)
            
            self.pie_figure.tight_layout()
            self.pie_canvas.draw()
            
        except Exception as e:
            print(f"[个人中心] 绘制饼图失败: {e}")
            self.pie_figure.clear()
            ax = self.pie_figure.add_subplot(111)
            ax.text(0.5, 0.5, '数据加载失败', ha='center', va='center', 
                   fontsize=12, color='#ef4444', transform=ax.transAxes)
            ax.axis('off')
            self.pie_canvas.draw()
    
    def _draw_account_creation_trend(self):
        """绘制账套创建趋势折线图"""
        try:
            self.line_figure.clear()
            ax = self.line_figure.add_subplot(111)
            
            # 获取账套数据并按月份统计
            accounts = db_manager.get_accounts()
            if not accounts:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                       fontsize=14, color='#9ca3af', transform=ax.transAxes)
                ax.axis('off')
                self.line_canvas.draw()
                return
            
            # 简化处理：按账套号前4位（年份）分组
            year_counts = {}
            for account in accounts:
                zth = str(account[0])
                if len(zth) >= 4:
                    year = zth[:4]
                    year_counts[year] = year_counts.get(year, 0) + 1
            
            if not year_counts:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                       fontsize=14, color='#9ca3af', transform=ax.transAxes)
                ax.axis('off')
                self.line_canvas.draw()
                return
            
            # 排序
            sorted_years = sorted(year_counts.keys())
            years = [y[-2:] for y in sorted_years]  # 取后两位
            counts = [year_counts[y] for y in sorted_years]
            
            # 绘制折线图
            ax.plot(range(len(years)), counts, marker='o', linewidth=2, 
                   markersize=6, color='#667eea', markerfacecolor='#667eea',
                   markeredgecolor='white', markeredgewidth=2)
            
            # 填充区域
            ax.fill_between(range(len(years)), counts, alpha=0.1, color='#667eea')
            
            # 添加数值标签
            for i, (year, count) in enumerate(zip(years, counts)):
                ax.annotate(str(count), xy=(i, count), xytext=(0, 8),
                           textcoords='offset points', ha='center',
                           fontsize=9, fontweight='bold', color='#667eea')
            
            # 设置标签
            ax.set_xlabel('年份', fontsize=9, fontweight='bold', color='#6b7280')
            ax.set_ylabel('账套数量', fontsize=9, fontweight='bold', color='#6b7280')
            ax.set_title('账套创建趋势', fontsize=11, fontweight='bold', color='#374151', pad=8)
            ax.set_xticks(range(len(years)))
            ax.set_xticklabels([f'{y}年' for y in years], fontsize=8)
            
            # 美化
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e5e7eb')
            ax.spines['bottom'].set_color('#e5e7eb')
            ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='#d1d5db')
            ax.set_axisbelow(True)
            
            self.line_figure.tight_layout()
            self.line_canvas.draw()
            
        except Exception as e:
            print(f"[个人中心] 绘制折线图失败: {e}")
            self.line_figure.clear()
            ax = self.line_figure.add_subplot(111)
            ax.text(0.5, 0.5, '数据加载失败', ha='center', va='center', 
                   fontsize=12, color='#ef4444', transform=ax.transAxes)
            ax.axis('off')
            self.line_canvas.draw()
    
    def create_profile_tab(self):
        """我的账套Tab - 完整个人信息卡片"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # ========== 个人信息卡片 ==========
        info_card = QFrame()
        info_card.setObjectName("profileInfoCard")
        info_card.setStyleSheet(f"""
            QFrame#profileInfoCard {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """)
        card_layout = QVBoxLayout(info_card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(24, 20, 24, 20)

        # 卡片标题
        card_title = QLabel("📋 个人信息")
        card_title.setFont(QFont(UIStyles.FONT_FAMILY, 18, QFont.Bold))
        card_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; border: none;")
        card_layout.addWidget(card_title)

        # 表单（2列网格，显示完整字段）
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 5, 0, 5)

        fields = [
            ("账套号", "zth_input", True),
            ("姓名", "xm_input", False),
            ("出生日期", "rq_input", False),
            ("性别", "xb_input", False),
            ("出生地", "csd_input", False),
            ("班级", "bj_input", False),
            ("小组", "xz_input", False),
            ("密码", "mm_input", False),
        ]

        readonly_style = f"""
            QLineEdit {{
                background-color: {UIStyles.BG_GRAY_50};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                padding: 8px 12px;
                font-size: 13px;
                color: {UIStyles.TEXT_SECONDARY};
            }}
        """

        for i, (label_text, attr_name, readonly) in enumerate(fields):
            row, col = i // 2, (i % 2) * 2
            lbl = QLabel(label_text)
            lbl.setFont(QFont(UIStyles.FONT_FAMILY, 12))
            lbl.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; border: none;")
            form_layout.addWidget(lbl, row, col)

            inp = QLineEdit()
            inp.setReadOnly(readonly)
            inp.setFixedHeight(38)
            inp.setFont(QFont(UIStyles.FONT_FAMILY, 13))
            if readonly:
                inp.setStyleSheet(readonly_style)
            else:
                inp.setStyleSheet(UIStyles.input_style())
            form_layout.addWidget(inp, row, col + 1)
            setattr(self, attr_name, inp)

        card_layout.addLayout(form_layout)

        # 隐藏的学号字段（内部使用，不显示）
        self.xh_hidden = ""

        # ========== 操作按钮 ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        save_btn = QPushButton("💾 保存修改")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(38)
        save_btn.setMinimumWidth(120)
        save_btn.setFont(QFont(UIStyles.FONT_FAMILY, 13, QFont.Bold))
        save_btn.setStyleSheet(UIStyles.success_button(font_size=13, font_weight="bold"))
        save_btn.clicked.connect(self.save_account_info)
        btn_layout.addWidget(save_btn)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(38)
        refresh_btn.setMinimumWidth(100)
        refresh_btn.setFont(QFont(UIStyles.FONT_FAMILY, 13))
        refresh_btn.setStyleSheet(UIStyles.default_button())
        refresh_btn.clicked.connect(self.refresh_account_info)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)

        layout.addWidget(info_card)

        # ========== 数据统计概览卡片 ==========
        summary_card = QFrame()
        summary_card.setObjectName("summaryCard")
        summary_card.setStyleSheet(f"""
            QFrame#summaryCard {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """)
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(24, 16, 24, 16)
        summary_layout.setSpacing(30)

        self.lbl_income = QLabel("收入: --")
        self.lbl_income.setFont(QFont(UIStyles.FONT_FAMILY, 13, QFont.Bold))
        self.lbl_income.setStyleSheet(f"color: #10b981; border: none;")
        summary_layout.addWidget(self.lbl_income)

        self.lbl_expense = QLabel("支出: --")
        self.lbl_expense.setFont(QFont(UIStyles.FONT_FAMILY, 13, QFont.Bold))
        self.lbl_expense.setStyleSheet(f"color: #ef4444; border: none;")
        summary_layout.addWidget(self.lbl_expense)

        self.lbl_balance = QLabel("结余: --")
        self.lbl_balance.setFont(QFont(UIStyles.FONT_FAMILY, 13, QFont.Bold))
        self.lbl_balance.setStyleSheet(f"color: {UIStyles.PRIMARY}; border: none;")
        summary_layout.addWidget(self.lbl_balance)

        self.lbl_record_count = QLabel("记录: --")
        self.lbl_record_count.setFont(QFont(UIStyles.FONT_FAMILY, 13))
        self.lbl_record_count.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY}; border: none;")
        summary_layout.addWidget(self.lbl_record_count)

        summary_layout.addStretch()
        layout.addWidget(summary_card)
        layout.addStretch()

        return tab
    
    def create_list_tab(self):
        """账套管理Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 搜索和筛选区 ==========
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_frame.setStyleSheet(f"""
            QFrame#searchFrame {{
                background-color: {UIStyles.BG_GRAY_50};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                padding: {UIStyles.PADDING_SMALL}px {UIStyles.PADDING_MEDIUM}px;
            }}
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 8, 10, 8)
        search_layout.setSpacing(8)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索账套号或名称...")
        self.search_input.setFixedHeight(34)
        self.search_input.setStyleSheet(UIStyles.input_style())
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        
        # 清除搜索按钮
        clear_btn = QPushButton("✖ 清除")
        clear_btn.setFixedWidth(80)
        clear_btn.setFixedHeight(34)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        clear_btn.setStyleSheet(UIStyles.secondary_button())
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(clear_btn)
        
        layout.addWidget(search_frame)
        
        # ========== 数据表格 ==========
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["账套号", "姓名", "班级", "小组"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_table_row_double_clicked)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(UIStyles.modern_table_style())
        layout.addWidget(self.table)
        
        # ========== 底部操作按钮（使用 UIStyles 统一风格）==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        add_btn = QPushButton("➕ 新增账套")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(38)
        add_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM, QFont.Bold))
        add_btn.setStyleSheet(UIStyles.success_button(font_size=UIStyles.FONT_SIZE_MEDIUM, font_weight="bold"))
        add_btn.clicked.connect(self.add_account)
        btn_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setFixedHeight(38)
        delete_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM))
        delete_btn.setStyleSheet(UIStyles.danger_button())
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)
        
        export_btn = QPushButton("📤 导出Excel")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setFixedHeight(38)
        export_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM))
        export_btn.setStyleSheet(UIStyles.primary_button())
        export_btn.clicked.connect(self.export_to_excel)
        btn_layout.addWidget(export_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return tab
    
    def filter_table(self):
        """根据搜索关键词过滤表格"""
        keyword = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            show_row = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and keyword in item.text().lower():
                    show_row = True
                    break
            
            self.table.setRowHidden(row, not show_row)
    
    def add_account(self):
        """新增账套 - 优化错误提示"""
        ztmc, ok = QInputDialog.getText(self, "新增账套", "请输入账套名称:")
        if ok and ztmc:
            try:
                # 显示加载提示
                self.toast.loading("正在创建账套...")
                
                # 生成新账套号（简单递增）
                accounts = db_manager.get_accounts()
                max_zth = max([int(acc[0]) for acc in accounts]) if accounts else 2501033400
                new_zth = str(max_zth + 1)
                
                db_manager._backend.execute(
                    "INSERT INTO sz_d_zt (zth, ztmc) VALUES (?, ?)",
                    (new_zth, ztmc)
                )
                
                # 显示成功提示
                self.toast.success(f"账套创建成功！账套号：{new_zth}", 3000)
                self.load_data_from_database()
                
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    QMessageBox.warning(
                        self,
                        "数据库表缺失",
                        "⚠️ 检测到数据库表结构不完整\n\n"
                        "可能原因:\n"
                        "1. 数据库文件损坏\n"
                        "2. 未执行初始化脚本\n\n"
                        "解决方法:\n"
                        "1. 关闭应用\n"
                        "2. 运行: python utils/db_initializer.py\n"
                        "3. 重新启动应用\n\n"
                        "或者在「系统设置」中重新初始化数据库",
                        QMessageBox.Ok
                    )
                else:
                    show_technical_error(self, e, self.toast)
            
            except Exception as e:
                show_technical_error(self, e, self.toast)
    
    def delete_selected(self):
        """删除选中的账套 - 优化错误提示"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.toast.warning("请先选择要删除的账套", 2000)
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 个账套吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            failed_list = []
            
            for index in selected_rows:
                row = index.row()
                zth = self.table.item(row, 0).text()
                try:
                    db_manager._backend.execute(
                        "DELETE FROM sz_d_zt WHERE zth = ?",
                        (zth,)
                    )
                    deleted_count += 1
                except Exception as e:
                    failed_list.append(f"{zth}: {str(e)}")
            
            # 显示结果
            if failed_list:
                error_msg = f"成功删除 {deleted_count} 个账套\n\n以下账套删除失败:\n" + "\n".join(failed_list)
                QMessageBox.warning(self, "部分删除失败", error_msg)
            else:
                self.toast.success(f"已成功删除 {deleted_count} 个账套", 3000)
            
            self.load_data_from_database()
    
    def export_to_excel(self):
        """导出账套列表到Excel - 优化错误提示"""
        from utils.excel_utils import excel_handler
        
        # 收集表格数据
        data = []
        headers = ["账套号", "账套名称", "创建时间"]
        
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(tuple(row_data))
        
        if not data:
            self.toast.warning("没有可导出的数据", 2000)
            return
        
        # 导出
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出Excel", "", "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                # 显示加载提示
                self.toast.loading("正在导出...")
                
                excel_handler.export_generic(data, headers, file_path, "账套列表")
                
                # 显示成功提示
                self.toast.success(f"导出成功！\n{file_path}", 3000)
                
            except Exception as e:
                show_technical_error(self, e, self.toast)
    
    def create_stats_tab(self):
        """统计分析Tab - 统一卡片风格"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 关键指标卡片横条 ==========
        metrics_card = QFrame()
        metrics_card.setObjectName("metricsCard")
        metrics_card.setStyleSheet(f"""
            QFrame#metricsCard {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """)
        metrics_layout = QHBoxLayout(metrics_card)
        metrics_layout.setContentsMargins(20, 16, 20, 16)
        metrics_layout.setSpacing(20)
        
        # 三个指标（使用分割线分隔）
        # _create_metric_label 返回 (container, value_label) 元组
        total_container, self.total_accounts_label = self._create_metric_label("总账套数", "0", "#667eea")
        metrics_layout.addWidget(total_container)
        
        # 分割线
        divider1 = self._create_vertical_divider()
        metrics_layout.addWidget(divider1)
        
        active_container, self.active_accounts_label = self._create_metric_label("活跃账套", "0", "#10b981")
        metrics_layout.addWidget(active_container)
        
        # 分割线
        divider2 = self._create_vertical_divider()
        metrics_layout.addWidget(divider2)
        
        recent_container, self.recent_label = self._create_metric_label("最近创建", "-", "#f59e0b")
        metrics_layout.addWidget(recent_container)
        
        metrics_layout.addStretch()
        
        layout.addWidget(metrics_card)
        
        # ========== 图表区域（左右分栏）==========
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(15)
        
        # 左侧：账套类型分布饼图
        pie_card = QFrame()
        pie_card.setObjectName("pieCard")
        pie_card.setStyleSheet(f"""
            QFrame#pieCard {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """)
        pie_layout = QVBoxLayout(pie_card)
        pie_layout.setSpacing(10)
        pie_layout.setContentsMargins(16, 16, 16, 16)
        
        pie_title = QLabel("🥧 账套类型分布")
        pie_title.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE, QFont.Bold))
        pie_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; border: none;")
        pie_layout.addWidget(pie_title)
        
        self.pie_figure = Figure(figsize=(4, 3), dpi=100)
        self.pie_canvas = FigureCanvas(self.pie_figure)
        self.pie_canvas.setStyleSheet("border: none; background-color: transparent;")
        pie_layout.addWidget(self.pie_canvas)
        
        charts_layout.addWidget(pie_card)
        
        # 右侧：账套创建趋势折线图
        line_card = QFrame()
        line_card.setObjectName("lineCard")
        line_card.setStyleSheet(f"""
            QFrame#lineCard {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """)
        line_layout = QVBoxLayout(line_card)
        line_layout.setSpacing(10)
        line_layout.setContentsMargins(16, 16, 16, 16)
        
        line_title = QLabel("📈 账套创建趋势")
        line_title.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE, QFont.Bold))
        line_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; border: none;")
        line_layout.addWidget(line_title)
        
        self.line_figure = Figure(figsize=(4, 3), dpi=100)
        self.line_canvas = FigureCanvas(self.line_figure)
        self.line_canvas.setStyleSheet("border: none; background-color: transparent;")
        line_layout.addWidget(self.line_canvas)
        
        charts_layout.addWidget(line_card)
        
        layout.addLayout(charts_layout)
        layout.addStretch()
        
        return tab
    
    def _create_metric_label(self, label_text, value_text, color):
        """创建简洁指标标签 - 卡片风格，返回 (container, value_label) 元组"""
        container = QFrame()
        container.setObjectName("metricItem")
        container.setStyleSheet("QFrame#metricItem { border: none; background: transparent; }")
        clayout = QVBoxLayout(container)
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setSpacing(4)
        
        # 指标名称
        name_label = QLabel(label_text)
        name_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        name_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY}; border: none; background: transparent;")
        clayout.addWidget(name_label)
        
        # 指标数值
        value_label = QLabel(value_text)
        value_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_XXLARGE, QFont.Bold))
        value_label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        clayout.addWidget(value_label)
        
        return container, value_label
    
    def _create_vertical_divider(self):
        """创建垂直分割线"""
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet(f"color: {UIStyles.BORDER_LIGHT};")
        divider.setFixedWidth(1)
        return divider
    
    def create_budget_tab(self):
        """创建预算管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # ========== 本月预算概览卡片（渐变背景）==========
        overview_frame = QFrame()
        overview_frame.setStyleSheet(UIStyles.gradient_card([UIStyles.PRIMARY, "#764ba2"]))
        overview_layout = QVBoxLayout(overview_frame)
        overview_layout.setSpacing(15)
        
        # 标题（不含冗余的Tab名）
        overview_title = QLabel("📅 本月预算概览")
        overview_title.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE, QFont.Bold))
        overview_title.setStyleSheet(f"color: {UIStyles.TEXT_WHITE};")
        overview_layout.addWidget(overview_title)
        
        # 数据网格
        data_grid = QGridLayout()
        data_grid.setSpacing(15)
        
        # 预算总额
        budget_total_card = self.create_budget_stat_card("预算总额", "¥0.00", "#fbbf24")
        data_grid.addWidget(budget_total_card, 0, 0)
        
        # 已使用
        spent_card = self.create_budget_stat_card("已使用", "¥0.00", "#f87171")
        data_grid.addWidget(spent_card, 0, 1)
        
        # 剩余额度
        remaining_card = self.create_budget_stat_card("剩余额度", "¥0.00", "#34d399")
        data_grid.addWidget(remaining_card, 0, 2)
        
        # 使用率
        usage_card = self.create_budget_stat_card("使用率", "0%", "#a78bfa")
        data_grid.addWidget(usage_card, 0, 3)
        
        overview_layout.addLayout(data_grid)
        layout.addWidget(overview_frame)
        
        # 保存引用以便更新
        self.budget_overview_cards = {
            'total': budget_total_card,
            'spent': spent_card,
            'remaining': remaining_card,
            'usage': usage_card
        }
        
        # ========== 历史预算列表卡片 ==========
        history_card = QFrame()
        history_card.setObjectName("historyCard")
        history_card.setStyleSheet(f"""
            QFrame#historyCard {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """)
        history_layout = QVBoxLayout(history_card)
        history_layout.setSpacing(12)
        history_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片标题（含操作按钮行）
        history_header = QHBoxLayout()
        
        history_title = QLabel("📋 历史预算记录")
        history_title.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE, QFont.Bold))
        history_title.setStyleSheet(f"color: {UIStyles.TEXT_PRIMARY}; border: none;")
        history_header.addWidget(history_title)
        
        history_header.addStretch()
        
        # 刷新按钮（放在标题右侧）
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setFixedHeight(34)
        refresh_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        refresh_btn.setStyleSheet(UIStyles.default_button())
        refresh_btn.clicked.connect(self.refresh_budget_data)
        history_header.addWidget(refresh_btn)
        
        history_layout.addLayout(history_header)
        
        # 预算表格
        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(5)
        self.budget_table.setHorizontalHeaderLabels(["月份", "预算金额", "实际支出", "剩余额度", "状态"])
        self.budget_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.budget_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.budget_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.budget_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.budget_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.budget_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.budget_table.setAlternatingRowColors(True)
        self.budget_table.setStyleSheet(UIStyles.modern_table_style())
        history_layout.addWidget(self.budget_table)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        set_budget_btn = QPushButton("⚙️ 设置本月预算")
        set_budget_btn.setCursor(Qt.PointingHandCursor)
        set_budget_btn.setFixedHeight(38)
        set_budget_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM, QFont.Bold))
        set_budget_btn.setStyleSheet(UIStyles.success_button(font_size=UIStyles.FONT_SIZE_MEDIUM, font_weight="bold"))
        set_budget_btn.clicked.connect(lambda: self.open_budget_settings_from_profile())
        btn_layout.addWidget(set_budget_btn)
        
        delete_budget_btn = QPushButton("🗑️ 删除选中")
        delete_budget_btn.setCursor(Qt.PointingHandCursor)
        delete_budget_btn.setFixedHeight(38)
        delete_budget_btn.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM))
        delete_budget_btn.setStyleSheet(UIStyles.danger_button())
        delete_budget_btn.clicked.connect(self.delete_selected_budget)
        btn_layout.addWidget(delete_budget_btn)
        
        btn_layout.addStretch()
        history_layout.addLayout(btn_layout)
        
        layout.addWidget(history_card)
        
        return tab
    
    def create_budget_stat_card(self, label_text, value_text, color):
        """创建预算统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: {UIStyles.PADDING_MEDIUM}px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        label = QLabel(label_text)
        label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE))
        label.setStyleSheet(f"color: rgba(255, 255, 255, 0.9);")
        layout.addWidget(label)
        
        value = QLabel(value_text)
        value.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_XXLARGE, QFont.Bold))
        value.setStyleSheet(f"color: {color};")
        layout.addWidget(value)
        
        return card
    
    def open_budget_settings_from_profile(self):
        """从个人中心打开预算设置对话框"""
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
        month_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM))
        layout.addWidget(month_label)
        
        # 预算输入
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("💰 预算金额："))
        
        budget_spin = QDoubleSpinBox()
        budget_spin.setRange(0, 999999)
        budget_spin.setValue(0)
        budget_spin.setPrefix("¥ ")
        budget_spin.setDecimals(2)
        budget_spin.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_LARGE))
        input_layout.addWidget(budget_spin)
        
        layout.addLayout(input_layout)
        
        # 提示
        hint_label = QLabel("💡 建议设置为月收入的80%-90%")
        hint_label.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL))
        hint_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        layout.addWidget(hint_label)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(UIStyles.success_button())
        ok_btn.clicked.connect(lambda: self.save_budget_from_profile(budget_spin.value(), dialog))
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec_()
    
    def save_budget_from_profile(self, amount, dialog):
        """从个人中心保存预算"""
        current_month = datetime.now().strftime('%Y-%m')
        
        if self.budget_manager.set_monthly_budget(current_month, amount):
            QMessageBox.information(self, "成功", f"✅ 本月预算已设置为：¥{amount:.2f}")
            dialog.accept()
            # 刷新预算数据
            self.refresh_budget_data()
        else:
            QMessageBox.critical(self, "失败", "❌ 预算设置失败，请查看日志")
    
    def refresh_budget_data(self):
        """刷新预算数据"""
        current_month = datetime.now().strftime('%Y-%m')
        
        # 获取预算状态
        status = self.budget_alert.get_budget_status_summary(current_month)
        
        if status and status.get('status') != 'not_set':
            # 更新概览卡片
            budget = status['budget']
            actual = status['actual']
            remaining = status['remaining']
            usage_rate = status['usage_rate']
            
            self._update_budget_card_value(self.budget_overview_cards['total'], f"¥{budget:.2f}")
            self._update_budget_card_value(self.budget_overview_cards['spent'], f"¥{actual:.2f}")
            self._update_budget_card_value(self.budget_overview_cards['remaining'], f"¥{remaining:.2f}")
            self._update_budget_card_value(self.budget_overview_cards['usage'], f"{usage_rate:.1f}%")
        else:
            # 未设置预算
            self._update_budget_card_value(self.budget_overview_cards['total'], "¥0.00")
            self._update_budget_card_value(self.budget_overview_cards['spent'], "¥0.00")
            self._update_budget_card_value(self.budget_overview_cards['remaining'], "¥0.00")
            self._update_budget_card_value(self.budget_overview_cards['usage'], "0%")
        
        # 加载历史预算列表
        self.load_budget_history()
    
    def _update_budget_card_value(self, card, value):
        """更新预算卡片的数值"""
        # 安全地遍历卡片中的所有子控件
        for child in card.children():
            # 确保是 QLabel 类型才调用 setText
            if isinstance(child, QLabel):
                try:
                    # 检查是否是数值标签（通过字体粗细判断）
                    if child.font().bold():
                        child.setText(value)
                        break
                except (AttributeError, TypeError):
                    # 如果访问 font() 失败，跳过该控件
                    continue
    
    def load_budget_history(self):
        """加载历史预算记录"""
        budgets = self.budget_manager.get_all_budgets()
        
        self.budget_table.setRowCount(len(budgets))
        
        for row, budget in enumerate(budgets):
            month = budget['month']
            budget_amount = budget['budget_amount']
            
            # 获取实际支出
            actual = self.budget_manager.get_monthly_expense(month)
            remaining = budget_amount - actual
            usage_rate = (actual / budget_amount * 100) if budget_amount > 0 else 0
            
            # 确定状态
            if budget_amount <= 0:
                status_text = "未设置"
                status_color = "#6b7280"
            elif actual > budget_amount:
                status_text = "已超支"
                status_color = "#ef4444"
            elif actual > budget_amount * 0.8:
                status_text = "即将超支"
                status_color = "#f59e0b"
            else:
                status_text = "正常"
                status_color = "#10b981"
            
            # 填充表格
            self.budget_table.setItem(row, 0, QTableWidgetItem(month))
            
            budget_item = QTableWidgetItem(f"¥{budget_amount:.2f}")
            budget_item.setTextAlignment(Qt.AlignCenter)
            self.budget_table.setItem(row, 1, budget_item)
            
            actual_item = QTableWidgetItem(f"¥{actual:.2f}")
            actual_item.setTextAlignment(Qt.AlignCenter)
            self.budget_table.setItem(row, 2, actual_item)
            
            remaining_item = QTableWidgetItem(f"¥{remaining:.2f}")
            remaining_item.setTextAlignment(Qt.AlignCenter)
            self.budget_table.setItem(row, 3, remaining_item)
            
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(status_color))
            status_item.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_NORMAL, QFont.Bold))
            self.budget_table.setItem(row, 4, status_item)
    
    def delete_selected_budget(self):
        """删除选中的预算记录"""
        selected_rows = self.budget_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的预算记录！")
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 条预算记录吗？\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            for index in selected_rows:
                row = index.row()
                month_item = self.budget_table.item(row, 0)
                if month_item:
                    month = month_item.text()
                    if self.budget_manager.delete_budget(month):
                        success_count += 1
            
            QMessageBox.information(self, "成功", f"✅ 成功删除 {success_count} 条预算记录")
            self.refresh_budget_data()

    def _fill_account_form(self, acc):
        """用账套数据填充个人信息表单"""
        # acc tuple: zth, ztmc, xh, xm, rq, xb, csd, bj, xz, mm, bz
        if hasattr(self, 'zth_input'):
            self.zth_input.setText(str(acc[0]) if len(acc) > 0 and acc[0] else "")
        if hasattr(self, 'xm_input'):
            self.xm_input.setText(str(acc[3]) if len(acc) > 3 and acc[3] else "")
        if hasattr(self, 'rq_input'):
            self.rq_input.setText(str(acc[4]) if len(acc) > 4 and acc[4] else "")
        if hasattr(self, 'xb_input'):
            self.xb_input.setText(str(acc[5]) if len(acc) > 5 and acc[5] else "")
        if hasattr(self, 'csd_input'):
            self.csd_input.setText(str(acc[6]) if len(acc) > 6 and acc[6] else "")
        if hasattr(self, 'bj_input'):
            self.bj_input.setText(str(acc[7]) if len(acc) > 7 and acc[7] else "")
        if hasattr(self, 'xz_input'):
            self.xz_input.setText(str(acc[8]) if len(acc) > 8 and acc[8] else "")
        if hasattr(self, 'mm_input'):
            self.mm_input.setText(str(acc[9]) if len(acc) > 9 and acc[9] else "")
        self.xh_hidden = str(acc[2]) if len(acc) > 2 and acc[2] else ""

    def _refresh_summary_stats(self):
        """刷新底部统计概览"""
        try:
            cur_zth = db_manager.current_account
            db_manager._backend.execute("SELECT COALESCE(SUM(je), 0) FROM sz_sheet_sr WHERE zth=?", (cur_zth,))
            income = float(db_manager._backend.fetchone()[0] or 0)
            db_manager._backend.execute("SELECT COALESCE(SUM(je), 0) FROM sz_sheet_zc WHERE zth=?", (cur_zth,))
            expense = float(db_manager._backend.fetchone()[0] or 0)
            balance = income - expense
            db_manager._backend.execute("SELECT COUNT(*) FROM sz_table_lsz WHERE zth=?", (cur_zth,))
            count = db_manager._backend.fetchone()[0]
            if hasattr(self, 'lbl_income'):
                self.lbl_income.setText(f"💰 收入: ¥{income:,.2f}")
            if hasattr(self, 'lbl_expense'):
                self.lbl_expense.setText(f"💸 支出: ¥{expense:,.2f}")
            if hasattr(self, 'lbl_balance'):
                color = "#10b981" if balance >= 0 else "#ef4444"
                self.lbl_balance.setStyleSheet(f"color: {color}; border: none;")
                self.lbl_balance.setText(f"📊 结余: ¥{balance:,.2f}")
            if hasattr(self, 'lbl_record_count'):
                self.lbl_record_count.setText(f"📝 记录: {count} 条")
        except Exception as e:
            print(f"[个人中心] 统计失败: {e}")

    def _on_table_row_double_clicked(self, row, col):
        """双击表格行时切换到对应账套"""
        item = self.table.item(row, 0)
        if item and item.data(Qt.UserRole):
            zth = item.data(Qt.UserRole)
            reply = QMessageBox.question(self, "切换账套",
                f"是否切换到账套 {zth}？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                # 通知主窗口切换
                parent = self.window()
                if hasattr(parent, '_do_switch_account'):
                    parent._do_switch_account(zth)

    def save_account_info(self):
        """保存账套信息到数据库"""
        zth = self.zth_input.text().strip()
        xm = (self.xm_input.text().strip() if hasattr(self, 'xm_input') else "")
        mm = (self.mm_input.text().strip() if hasattr(self, 'mm_input') else "")

        if not zth:
            self.toast.warning("账套号不存在，无法保存", 2000)
            return

        try:
            self.toast.loading("正在保存...")
            updates = []
            params = []
            if xm:
                updates.append("xm = ?")
                params.append(xm)
            if mm:
                updates.append("mm = ?")
                params.append(mm)
            if not updates:
                self.toast.info("没有需要保存的修改", 2000)
                return
            params.append(zth)
            db_manager._backend.execute(
                f"UPDATE sz_d_zt SET {', '.join(updates)} WHERE zth = ?",
                tuple(params)
            )
            # 同步更新 ztmc
            if xm:
                db_manager._backend.execute("UPDATE sz_d_zt SET ztmc = xm WHERE zth = ?", (zth,))

            self.toast.success("个人信息保存成功", 2000)
            self.load_data_from_database()

        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                QMessageBox.warning(self, "数据库表缺失",
                    "请在「系统设置」中重新初始化数据库", QMessageBox.Ok)
            else:
                show_technical_error(self, e, self.toast)
        except Exception as e:
            show_technical_error(self, e, self.toast)
    
    def refresh_account_info(self):
        """刷新账套信息 - 优化提示"""
        self.toast.info("正在刷新数据...", 1500)
        self.load_data_from_database()
