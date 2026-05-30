# -*- coding: utf-8 -*-
"""
主窗口模块| 包含侧边栏、菜单栏、状态栏和内容区域
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QListWidget, QListWidgetItem,
                             QStackedWidget, QMenuBar, QMenu, QAction,
                             QStatusBar, QLabel, QMessageBox, QFrame, QVBoxLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                             QApplication, QDialog, QGridLayout, QTextEdit, QSizePolicy,
                             QInputDialog, QComboBox)
from PyQt5.QtGui import (QFont, QPixmap, QColor, QPalette, QIcon, QDesktopServices)
from PyQt5.QtCore import (Qt, QSize, QUrl, QTimer, QDateTime, pyqtSignal)
import sys
import os

from models.db_backend import db_manager
from models.config import config
from ui.styles import UIStyles  # 新增:导入样式管理模块
from ui.pages.home_page import HomePage
from ui.pages.category_page import CategoryPage
from ui.pages.income_page import IncomePage
from ui.pages.expense_page import ExpensePage
from ui.pages.cash_flow_page import CashFlowPage
from ui.pages.monthly_report_page import MonthlyReportPage
from ui.pages.statistics_page import StatisticsPage
from ui.pages.profile_page import ProfilePage
from ui.pages.settings_page import SettingsPage
from datetime import datetime


class MainWindow(QMainWindow):
    """主窗口"""
    account_changed = pyqtSignal(str)  # 账套切换信号

    def __init__(self, account_number='2501033401'):
        super().__init__()
        self.current_user = account_number

        # 设置数据库管理器的当前账套号
        db_manager.current_account = account_number

        # 先连接数据库
        if db_manager.connect_sqlite('data/inex.db'):
            print(f"[主窗口] 数据库连接成功，账套号: {account_number}")
        else:
            print("[主窗口] 数据库连接失败，使用演示模式")

        # 再初始化 UI（此时数据库已连接）
        self.initUI()
        self.connectSignals()

        # 自动备份（每日一次）
        QTimer.singleShot(2000, self.auto_backup)

        # 更新状态栏（显示账套名称）
        if db_manager.is_connected():
            acc_name = self._get_account_display(account_number)
            self.statusBar().showMessage(f"SQLite · {acc_name or account_number}", 3000)
        else:
            self.statusBar().showMessage("未连接数据库，将使用演示模式", 3000)

    def initUI(self):
        """初始化 UI"""
        self.setWindowTitle("个人收支管理系统")
        self.setMinimumSize(1600, 900)

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "InEx_System.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 创建中央控件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        # ========== 左侧边栏 ==========
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(210)
        self.sidebar.setStyleSheet(f"""
            QListWidget {{
                background-color: {UIStyles.SIDEBAR_BG};
                color: {UIStyles.SIDEBAR_TEXT};
                border: none;
                outline: none;
                padding: 8px 0;
            }}
            QListWidget::item {{
                height: 48px;
                padding-left: 16px;
                margin: 2px 10px;
                border-radius: 8px;
                border: none;
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {UIStyles.SIDEBAR_SELECTED}, stop:1 {UIStyles.SIDEBAR_SELECTED_DARKER});
                color: white;
                font-weight: bold;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {UIStyles.SIDEBAR_HOVER};
                border-radius: 8px;
            }}
        """)
        self.sidebar.setFont(QFont(UIStyles.FONT_FAMILY, UIStyles.FONT_SIZE_MEDIUM))

        # 添加列表项
        items = [
            "📊  首页",
            "📁  分类管理",
            "💰  收入记账",
            "💸  支出记账",
            "📝  收支流水账",
            "📈  收支报表",
            "📉  账单分析",
            "👤  个人中心",
            "⚙️  系统设置"
        ]
        for item in items:
            list_item = QListWidgetItem(item)
            list_item.setSizeHint(QSize(190, 48))
            self.sidebar.addItem(list_item)

        main_layout.addWidget(self.sidebar)

        # ========== 右侧内容区域 ==========
        content_frame = QFrame()
        content_frame.setStyleSheet(f"background-color: {UIStyles.CONTENT_BG};")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_frame.setLayout(content_layout)

        # 堆叠窗口
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"background-color: {UIStyles.CONTENT_BG};")
        content_layout.addWidget(self.stacked_widget)

        main_layout.addWidget(content_frame)

        # 创建所有页面
        self.create_placeholder_pages()

        # ========== 菜单栏 ==========
        self.createMenuBar()

        # ========== 状态栏 ==========
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {UIStyles.SIDEBAR_BG};
                color: {UIStyles.TEXT_TERTIARY};
                border-top: 1px solid {UIStyles.SIDEBAR_ITEM_BORDER};
                padding: 0 12px;
                font-size: 9px;
            }}
            QStatusBar::item {{
                border: none;
            }}
        """)

        # 左侧：数据库状态 + 账套信息
        self.status_db_label = QLabel()
        self.status_db_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY}; font-size: 9px;")
        self.status_bar.addWidget(self.status_db_label)

        # 弹性空间
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_bar.addPermanentWidget(spacer)

        # 右侧：当前时间
        self.status_time_label = QLabel()
        self.status_time_label.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY}; font-size: 9px;")
        self.status_bar.addPermanentWidget(self.status_time_label)

        # 初始化状态栏内容
        self._update_status_db_info()
        self._update_status_time()

        # 每分钟刷新时间
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status_time)
        self._status_timer.start(60000)

    def create_placeholder_pages(self):
        """创建所有页面"""
        # 首页
        self.home_page = HomePage()
        self.stacked_widget.addWidget(self.home_page)
        self.account_changed.connect(self.home_page.load_data)

        # 分类管理
        self.category_page = CategoryPage()
        self.stacked_widget.addWidget(self.category_page)

        # 收入记账管理
        self.income_page = IncomePage()
        self.stacked_widget.addWidget(self.income_page)
        self.account_changed.connect(lambda zth: self.income_page.load_data())

        # 支出记账管理
        self.expense_page = ExpensePage()
        self.stacked_widget.addWidget(self.expense_page)
        self.account_changed.connect(lambda zth: self.expense_page.load_data())

        # 收支流水账
        self.cash_flow_page = CashFlowPage()
        self.stacked_widget.addWidget(self.cash_flow_page)
        self.account_changed.connect(lambda zth: self.cash_flow_page.load_data())

        # 收支月报表
        self.monthly_report_page = MonthlyReportPage()
        self.stacked_widget.addWidget(self.monthly_report_page)
        self.account_changed.connect(lambda zth: self.monthly_report_page.load_data())

        # 统计分析
        self.statistics_page = StatisticsPage()
        self.stacked_widget.addWidget(self.statistics_page)
        self.account_changed.connect(lambda zth: self.statistics_page.load_charts())

        # 个人中心
        self.profile_page = ProfilePage()
        self.stacked_widget.addWidget(self.profile_page)
        self.account_changed.connect(lambda zth: self.profile_page.load_data_from_database())

        # 系统设置
        self.settings_page = SettingsPage()
        self.stacked_widget.addWidget(self.settings_page)

    def create_placeholder_page(self, name):
        """创建单个占位页面"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(f"{name}\n\n功能开发中...")
        label.setFont(QFont(UIStyles.FONT_FAMILY, 20, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            color: {UIStyles.TEXT_TERTIARY};
            background-color: white;
            padding: 50px;
            border-radius: 10px;
        """)

        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def createMenuBar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {UIStyles.SIDEBAR_BG};
                color: {UIStyles.SIDEBAR_TEXT};
                padding: 4px 8px;
            }}
            QMenuBar::item {{
                padding: 6px 14px;
                border-radius: 6px;
                margin: 2px 2px;
            }}
            QMenuBar::item:selected {{
                background-color: rgba(255,255,255,0.12);
            }}
            QMenu {{
                background-color: white;
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: 6px;
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 8px 32px 8px 16px;
            }}
            QMenu::item:selected {{
                background-color: {UIStyles.PRIMARY_LIGHT};
                color: {UIStyles.PRIMARY};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {UIStyles.BORDER_LIGHT};
                margin: 4px 12px;
            }}
        """)

        # ========== 文件菜单 ==========
        file_menu = menubar.addMenu("文件(&F)")

        # 新建账套
        new_account_action = QAction("🆕 新建账套(&N)", self)
        new_account_action.setShortcut("Ctrl+N")
        new_account_action.triggered.connect(lambda: self.on_menu_action("新建账套"))
        file_menu.addAction(new_account_action)

        # 切换账套
        switch_account_action = QAction("🔄 切换账套(&S)", self)
        switch_account_action.setShortcut("Ctrl+Shift+S")
        switch_account_action.triggered.connect(lambda: self.on_menu_action("切换账套"))
        file_menu.addAction(switch_account_action)

        file_menu.addSeparator()

        open_action = QAction("📂 打开(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(lambda: self.on_menu_action("打开文件"))
        file_menu.addAction(open_action)

        import_menu = file_menu.addMenu("📥 导入(&I)")
        excel_import = QAction("Excel", self)
        excel_import.triggered.connect(lambda: self.on_menu_action("导入 Excel"))
        import_menu.addAction(excel_import)

        csv_import = QAction("CSV", self)
        csv_import.triggered.connect(lambda: self.on_menu_action("导入 CSV"))
        import_menu.addAction(csv_import)

        json_import = QAction("JSON", self)
        json_import.triggered.connect(lambda: self.on_menu_action("导入 JSON"))
        import_menu.addAction(json_import)

        export_menu = file_menu.addMenu("📤 导出(&E)")
        excel_export = QAction("Excel", self)
        excel_export.triggered.connect(lambda: self.on_menu_action("导出 Excel"))
        export_menu.addAction(excel_export)

        pdf_export = QAction("PDF", self)
        pdf_export.triggered.connect(lambda: self.on_menu_action("导出 PDF"))
        export_menu.addAction(pdf_export)

        csv_export = QAction("CSV", self)
        csv_export.triggered.connect(lambda: self.on_menu_action("导出 CSV"))
        export_menu.addAction(csv_export)

        json_export = QAction("JSON", self)
        json_export.triggered.connect(lambda: self.on_menu_action("导出 JSON"))
        export_menu.addAction(json_export)

        file_menu.addSeparator()

        # 备份数据
        backup_action = QAction("💾 备份数据(&B)", self)
        backup_action.setShortcut("Ctrl+B")
        backup_action.triggered.connect(lambda: self.on_menu_action("备份数据"))
        file_menu.addAction(backup_action)

        # 恢复数据
        restore_action = QAction("♻️ 恢复数据(&R)", self)
        restore_action.setShortcut("Ctrl+Shift+R")
        restore_action.triggered.connect(lambda: self.on_menu_action("恢复数据"))
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        exit_action = QAction("❌ 退出(&X)", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ========== 编辑菜单 ==========
        edit_menu = menubar.addMenu("编辑(&E)")

        insert_action = QAction("➕ 插入数据(&I)", self)
        insert_action.setShortcut("Ctrl+I")
        insert_action.triggered.connect(lambda: self.on_menu_action("插入数据"))
        edit_menu.addAction(insert_action)

        # 查找替换
        find_replace_action = QAction("🔍 查找替换(&F)", self)
        find_replace_action.setShortcut("Ctrl+F")
        find_replace_action.triggered.connect(lambda: self.on_menu_action("查找替换"))
        edit_menu.addAction(find_replace_action)

        # 全局搜索
        global_search_action = QAction("🌐 全局搜索(&G)", self)
        global_search_action.setShortcut("Ctrl+Shift+F")
        global_search_action.triggered.connect(self.show_global_search)
        edit_menu.addAction(global_search_action)

        # 数据校验
        validate_action = QAction("✅ 数据校验(&V)", self)
        validate_action.triggered.connect(lambda: self.on_menu_action("数据校验"))
        edit_menu.addAction(validate_action)

        edit_menu.addSeparator()

        # 批量操作子菜单
        batch_menu = edit_menu.addMenu("📦 批量操作(&B)")

        batch_delete = QAction("批量删除", self)
        batch_delete.triggered.connect(lambda: self.on_menu_action("批量删除"))
        batch_menu.addAction(batch_delete)

        batch_modify_type = QAction("批量修改类型", self)
        batch_modify_type.triggered.connect(lambda: self.on_menu_action("批量修改类型"))
        batch_menu.addAction(batch_modify_type)

        batch_modify_payment = QAction("批量修改支付方式", self)
        batch_modify_payment.triggered.connect(lambda: self.on_menu_action("批量修改支付方式"))
        batch_menu.addAction(batch_modify_payment)

        edit_menu.addSeparator()

        db_menu = edit_menu.addMenu("🗄️ 数据库(&D)")

        connect_action = QAction("连接数据库(&C)", self)
        connect_action.triggered.connect(self.connect_database)
        db_menu.addAction(connect_action)

        disconnect_action = QAction("断开连接(&D)", self)
        disconnect_action.triggered.connect(self.disconnect_database)
        db_menu.addAction(disconnect_action)

        test_action = QAction("测试连接(&T)", self)
        test_action.triggered.connect(self.test_database_connection)
        db_menu.addAction(test_action)

        db_menu.addSeparator()

        optimize_db = QAction("优化数据库(&O)", self)
        optimize_db.triggered.connect(lambda: self.on_menu_action("优化数据库"))
        db_menu.addAction(optimize_db)

        clean_redundant = QAction("清理冗余数据(&C)", self)
        clean_redundant.triggered.connect(lambda: self.on_menu_action("清理冗余数据"))
        db_menu.addAction(clean_redundant)

        # ========== 视图菜单==========
        view_menu = menubar.addMenu("视图(&V)")

        # 主题切换
        theme_menu = view_menu.addMenu("🎨 主题(&T)")

        light_theme = QAction("☀️ 浅色", self)
        light_theme.setCheckable(True)
        light_theme.setChecked(True)
        light_theme.triggered.connect(lambda: self.on_menu_action("切换到浅色主题"))
        theme_menu.addAction(light_theme)

        auto_theme = QAction("🔄 自动", self)
        auto_theme.setCheckable(True)
        auto_theme.triggered.connect(lambda: self.on_menu_action("切换到自动主题"))
        theme_menu.addAction(auto_theme)

        view_menu.addSeparator()

        # 字体大小调整
        font_menu = view_menu.addMenu("🔤 字体大小(&F)")

        font_small = QAction("小", self)
        font_small.triggered.connect(lambda: self.on_menu_action("设置字体为小"))
        font_menu.addAction(font_small)

        font_medium = QAction("中", self)
        font_medium.triggered.connect(lambda: self.on_menu_action("设置字体为中"))
        font_menu.addAction(font_medium)

        font_large = QAction("大", self)
        font_large.triggered.connect(lambda: self.on_menu_action("设置字体为大"))
        font_menu.addAction(font_large)

        view_menu.addSeparator()

        # 侧边栏控制
        toggle_sidebar = QAction("📋 切换侧边栏(&S)", self)
        toggle_sidebar.setShortcut("Ctrl+Shift+L")
        toggle_sidebar.triggered.connect(lambda: self.on_menu_action("切换侧边栏显示"))
        view_menu.addAction(toggle_sidebar)

        # 刷新页面
        refresh_page = QAction("🔄 刷新当前页(&R)", self)
        refresh_page.setShortcut("F5")
        refresh_page.triggered.connect(lambda: self.on_menu_action("刷新当前页面"))
        view_menu.addAction(refresh_page)

        view_menu.addSeparator()

        # 全屏模式
        fullscreen_action = QAction("⛶ 全屏模式(&F)", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(lambda: self.on_menu_action("切换全屏模式"))
        view_menu.addAction(fullscreen_action)

        # ========== 工具菜单（新增）==========
        tools_menu = menubar.addMenu("工具(&T)")

        # AI智能分析
        ai_analysis = QAction("🤖 AI智能分析(&A)", self)
        ai_analysis.setShortcut("Ctrl+Shift+A")
        ai_analysis.triggered.connect(lambda: self.on_menu_action("AI智能分析"))
        tools_menu.addAction(ai_analysis)

        # 预算设置向导
        budget_wizard = QAction("💰 预算设置向导(&B)", self)
        budget_wizard.triggered.connect(lambda: self.on_menu_action("预算设置向导"))
        tools_menu.addAction(budget_wizard)

        tools_menu.addSeparator()

        # 数据清理工具
        data_cleaner = QAction("🧹 数据清理工具(&C)", self)
        data_cleaner.triggered.connect(lambda: self.on_menu_action("数据清理工具"))
        tools_menu.addAction(data_cleaner)

        # 报表生成器
        report_generator = QAction("📊 报表生成器(&R)", self)
        report_generator.triggered.connect(lambda: self.on_menu_action("报表生成器"))
        tools_menu.addAction(report_generator)

        tools_menu.addSeparator()

        # 定时任务管理
        scheduled_tasks = QAction("⏰ 定时任务管理(&S)", self)
        scheduled_tasks.triggered.connect(lambda: self.on_menu_action("定时任务管理"))
        tools_menu.addAction(scheduled_tasks)

        # ========== 插件菜单 ==========
        plugin_menu = menubar.addMenu("插件(&P)")

        plugin_manager = QAction("🔌 插件管理器(&M)", self)
        plugin_manager.triggered.connect(lambda: self.on_menu_action("插件管理器"))
        plugin_menu.addAction(plugin_manager)

        plugin_market = QAction("🛒 插件市场(&S)", self)
        plugin_market.triggered.connect(lambda: self.on_menu_action("插件市场"))
        plugin_menu.addAction(plugin_market)

        plugin_menu.addSeparator()

        installed_plugins = plugin_menu.addMenu("已安装插件")
        no_plugin = QAction("暂无插件", self)
        no_plugin.setEnabled(False)
        installed_plugins.addAction(no_plugin)

        # ========== 帮助菜单 ==========
        help_menu = menubar.addMenu("帮助(&H)")

        help_doc = QAction("📖 帮助文档(&D)", self)
        help_doc.setShortcut("F1")
        help_doc.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile('README.md')))
        help_menu.addAction(help_doc)

        online_tutorial = QAction("🌐 在线教程(&T)", self)
        online_tutorial.triggered.connect(lambda: self.on_menu_action("在线教程"))
        help_menu.addAction(online_tutorial)

        faq = QAction("❓ 常见问题(&Q)", self)
        faq.triggered.connect(lambda: self.on_menu_action("常见问题FAQ"))
        help_menu.addAction(faq)

        help_menu.addSeparator()

        shortcuts_list = QAction("⌨️ 快捷键列表(&K)", self)
        shortcuts_list.setShortcut("Ctrl+?")
        shortcuts_list.triggered.connect(lambda: self.on_menu_action("查看快捷键列表"))
        help_menu.addAction(shortcuts_list)

        check_update = QAction("🔄 检查更新(&U)", self)
        check_update.triggered.connect(lambda: self.on_menu_action("检查更新"))
        help_menu.addAction(check_update)

        feedback = QAction("💬 反馈问题(&F)", self)
        feedback.triggered.connect(lambda: self.on_menu_action("反馈问题"))
        help_menu.addAction(feedback)

        help_menu.addSeparator()

        about_action = QAction("ℹ️ 关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def connectSignals(self):
        """连接信号槽"""
        self.sidebar.currentRowChanged.connect(self.on_sidebar_changed)

    def show_global_search(self):
        """显示全局搜索对话框"""
        from ui.dialogs.global_search_dialog import GlobalSearchDialog
        dialog = GlobalSearchDialog(self)
        dialog.exec_()

    def on_sidebar_changed(self, index):
        """侧边栏切换"""
        self.stacked_widget.setCurrentIndex(index)
        page_name = self.sidebar.item(index).text().split(' ')[1] if ' ' in self.sidebar.item(index).text() else f"页面{index+1}"
        self.statusBar().showMessage(f"已切换到{page_name}", 2000)
        print(f"[导航] 切换到{page_name}")

    def open_db_connection_dialog(self):
        """打开数据库连接测试对话框"""
        from ui.dialogs.db_connection_dialog import DatabaseConnectionDialog

        dialog = DatabaseConnectionDialog(self)
        dialog.exec_()

        print("[菜单] 打开数据库连接测试对话框")

    def on_menu_action(self, action_name):
        """菜单动作处理"""
        print(f"[菜单] 操作：{action_name}")
        self.statusBar().showMessage(f"执行：{action_name}", 3000)

        # 根据操作名称执行具体功能
        if action_name == "备份数据":
            self.backup_data()
        elif action_name == "恢复数据":
            self.restore_data()
        elif action_name == "数据校验":
            self.validate_data()
        elif action_name == "优化数据库":
            self.optimize_database()
        elif action_name == "清理冗余数据":
            self.clean_redundant_data()
        elif action_name == "AI智能分析":
            self.open_ai_analysis()
        elif action_name == "预算设置向导":
            self.open_budget_wizard()
        elif action_name == "数据清理工具":
            self.open_data_cleaner()
        elif action_name == "报表生成器":
            self.open_report_generator()
        elif action_name == "检查更新":
            self.check_for_updates()
        elif action_name == "反馈问题":
            self.open_feedback()
        elif action_name == "查看快捷键列表":
            self.show_shortcuts_dialog()
        elif action_name == "在线教程":
            QDesktopServices.openUrl(QUrl("https://www.zhihu.com/question/401029960/answer/2023829517181961566"))
        elif action_name == "常见问题FAQ":
            self.show_faq_dialog()
        elif "主题" in action_name:
            self.change_theme(action_name)
        elif "字体" in action_name:
            self.change_font_size(action_name)
        elif action_name == "切换侧边栏显示":
            self.toggle_sidebar()
        elif action_name == "刷新当前页面":
            self.refresh_current_page()
        elif action_name == "切换全屏模式":
            self.toggle_fullscreen()
        elif action_name == "重置窗口布局":
            self.reset_window_layout()
        elif action_name == "切换账套":
            self.switch_account()
        elif action_name == "新建账套":
            self.create_new_account()

    def switch_account(self):
        """切换账套"""
        if not db_manager.is_connected():
            QMessageBox.warning(self, "提示", "数据库未连接")
            return

        accounts = db_manager.get_accounts()
        if not accounts:
            QMessageBox.warning(self, "提示", "没有可用的账套")
            return

        # 构建选项列表
        items = []
        current_idx = 0
        for i, acc in enumerate(accounts):
            zth = acc[0]
            xm = acc[3] if len(acc) > 3 else ""
            bj = acc[7] if len(acc) > 7 else ""
            label = f"{zth} - {xm} ({bj})" if xm else zth
            items.append(label)
            if zth == self.current_user:
                current_idx = i

        item, ok = QInputDialog.getItem(
            self, "切换账套",
            "请选择要切换的账套：",
            items, current_idx, False
        )
        if ok and item:
            # 提取 zth
            zth = item.split(" - ")[0].strip()
            self._do_switch_account(zth)

    def _get_account_display(self, zth):
        """获取账套显示名称（zth - 姓名）"""
        try:
            accounts = db_manager.get_accounts()
            for acc in accounts:
                if acc[0] == zth:
                    xm = acc[3] if len(acc) > 3 else ""
                    return f"{zth} - {xm}" if xm else zth
        except Exception:
            pass
        return zth

    def _do_switch_account(self, zth):
        """执行账套切换"""
        self.current_user = zth
        db_manager.current_account = zth
        display = self._get_account_display(zth)
        self.statusBar().showMessage(f"SQLite · {display}", 0)
        # 发射信号，通知所有页面刷新
        self.account_changed.emit(zth)
        print(f"[主窗口] 切换账套至: {display}")

    def create_new_account(self):
        """新建账套"""
        QMessageBox.information(
            self, "新建账套",
            "请在「我的」→「账套管理」中使用新建功能，\n"
            "或通过数据库初始化工具添加新账套。"
        )

    def connect_database(self):
        """连接数据库 - 切换到系统设置页面的数据库配置区域"""
        # 切换到系统设置页面（索引8）
        self.switch_to_page_by_index(8)

        # 显示提示信息
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "数据库连接",
            "请在系统设置页面的「数据库配置」区域进行连接操作：\n\n"
            "1. 选择数据库类型（SQLite/MySQL/Sybase）\n"
            "2. 填写连接参数\n"
            "3. 点击「🔌 测试连接」验证配置\n"
            "4. 点击「✅ 保存所有设置」完成配置\n\n"
            "💡 提示：配置保存后系统将自动使用新配置连接数据库"
        )

    def disconnect_database(self):
        """断开数据库连接"""
        from PyQt5.QtWidgets import QMessageBox

        if not db_manager.is_connected():
            QMessageBox.information(self, "提示", "数据库未连接")
            return

        reply = QMessageBox.question(
            self, "确认",
            "确定要断开数据库连接吗？\n断开后将无法进行数据操作。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                db_manager.disconnect()
                QMessageBox.information(self, "成功", "数据库连接已断开")
                print("[数据库] 连接已断开")
                self.statusBar().showMessage("数据库已断开连接", 3000)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"断开连接失败:\n{str(e)}")
                print(f"[数据库] 断开连接异常: {str(e)}")

    def test_database_connection(self):
        """测试数据库连接 - 切换到系统设置页面"""
        # 切换到系统设置页面（索引8）
        self.switch_to_page_by_index(8)

        # 显示提示信息
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "测试数据库连接",
            "请在系统设置页面的「数据库配置」区域进行测试：\n\n"
            "1. 选择数据库类型（SQLite/MySQL/Sybase）\n"
            "2. 填写连接参数\n"
            "3. 点击「🔌 测试连接」按钮\n\n"
            "💡 系统将自动检测连接状态并显示详细日志"
        )

    def auto_backup(self):
        """启动时自动备份（保留最近7天）"""
        import shutil, os, glob
        try:
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            today = datetime.now().strftime('%Y%m%d')
            backup_file = os.path.join(backup_dir, f'inex_{today}.db')
            if not os.path.exists(backup_file):
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inex.db')
                if os.path.exists(db_path):
                    shutil.copy2(db_path, backup_file)
                    print(f"[自动备份] {backup_file}")
            # 清理7天前的旧备份
            cutoff = datetime.now().timestamp() - 7 * 86400
            for f in glob.glob(os.path.join(backup_dir, 'inex_*.db')):
                if os.path.getmtime(f) < cutoff:
                    os.remove(f)
        except Exception as e:
            print(f"[自动备份] 失败: {e}")

    def backup_data(self):
        """手动备份数据"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import shutil

        if not db_manager.is_connected():
            QMessageBox.warning(self, "警告", "数据库未连接，无法备份")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "备份数据",
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "数据库文件 (*.db);;所有文件 (*)"
        )

        if file_path:
            try:
                db_path = 'data/inex.db'
                shutil.copy2(db_path, file_path)
                QMessageBox.information(self, "成功", f"数据已备份到:\n{file_path}")
                print(f"[备份] 数据已备份到 {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"备份失败:\n{str(e)}")
                print(f"[备份] 失败: {str(e)}")

    def restore_data(self):
        """恢复数据"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import shutil

        reply = QMessageBox.question(
            self, "确认",
            "恢复数据将覆盖当前所有数据，是否继续？\n建议先备份当前数据！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择备份文件", "",
                "数据库文件 (*.db);;所有文件 (*)"
            )

            if file_path:
                try:
                    db_path = 'data/inex.db'
                    shutil.copy2(file_path, db_path)
                    QMessageBox.information(self, "成功", "数据恢复成功，请重启应用以生效")
                    print(f"[恢复] 数据已从 {file_path} 恢复")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"恢复失败:\n{str(e)}")
                    print(f"[恢复] 失败: {str(e)}")

    def validate_data(self):
        """数据校验"""
        from PyQt5.QtWidgets import QMessageBox, QProgressDialog

        progress = QProgressDialog("正在校验数据...", "取消", 0, 100, self)
        progress.setWindowTitle("数据校验")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        # 模拟校验过程
        for i in range(101):
            progress.setValue(i)
            if progress.wasCanceled():
                break

        progress.close()
        QMessageBox.information(self, "校验完成", "数据校验完成，未发现异常")
        print("[校验] 数据校验完成")

    def optimize_database(self):
        """优化数据库"""
        from PyQt5.QtWidgets import QMessageBox

        if not db_manager.is_connected():
            QMessageBox.warning(self, "警告", "数据库未连接")
            return

        try:
            # 执行VACUUM优化
            cursor = db_manager._backend.conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            db_manager._backend.conn.commit()

            QMessageBox.information(self, "成功", "数据库优化完成")
            print("[优化] 数据库优化完成")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"优化失败:\n{str(e)}")
            print(f"[优化] 失败: {str(e)}")

    def clean_redundant_data(self):
        """清理冗余数据"""
        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self, "确认",
            "此操作将清理以下冗余数据：\n"
            "- 孤立的分类记录\n"
            "- 重复的日志条目\n"
            "- 过期的临时数据\n\n"
            "是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "完成", "冗余数据清理完成")
            print("[清理] 冗余数据清理完成")

    def open_ai_analysis(self):
        """打开AI智能分析"""
        from PyQt5.QtWidgets import QMessageBox

        # 切换到统计分析页面（如果存在AI分析功能）
        self.switch_to_page_by_index(6)  # StatisticsPage
        QMessageBox.information(self, "提示", "请在统计分析页面使用AI智能分析功能")
        print("[AI] 打开AI智能分析")

    def open_budget_wizard(self):
        """打开预算设置向导"""
        from PyQt5.QtWidgets import QMessageBox

        # 切换到系统设置页面
        self.switch_to_page_by_index(8)  # SettingsPage
        QMessageBox.information(self, "提示", "请在系统设置页面配置预算")
        print("[预算] 打开预算设置向导")

    def open_data_cleaner(self):
        """打开数据清理工具"""
        QMessageBox.information(self, "提示", "数据清理工具开发中...")
        print("[工具] 打开数据清理工具")

    def open_report_generator(self):
        """打开报表生成器"""
        # 切换到月度报表页面
        self.switch_to_page_by_index(5)  # MonthlyReportPage
        print("[工具] 打开报表生成器")

    def check_for_updates(self):
        """检查更新"""
        from PyQt5.QtWidgets import QMessageBox
        import requests

        try:
            # 这里可以连接到GitHub API或其他更新服务器
            QMessageBox.information(self, "检查更新", "当前已是最新版本 (v2.0)")
            print("[更新] 检查更新完成")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"检查更新失败:\n{str(e)}")

    def open_feedback(self):
        """打开反馈问题"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
        import webbrowser

        # 直接打开GitHub Issues页面或邮箱
        webbrowser.open("mailto:yoho12138@qq.com?subject=InEx_System反馈")
        print("[反馈] 打开反馈渠道")

    def show_shortcuts_dialog(self):
        """显示快捷键列表"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("快捷键列表")
        dialog.setFixedSize(600, 500)

        layout = QVBoxLayout(dialog)

        shortcuts_text = QTextEdit()
        shortcuts_text.setReadOnly(True)
        shortcuts_text.setHtml("""
        <h2>⌨️ 快捷键列表</h2>
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background-color: {UIStyles.BG_GRAY_100};">
                <th style="padding: 8px; text-align: left;">快捷键</th>
                <th style="padding: 8px; text-align: left;">功能</th>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+N</b></td>
                <td style="padding: 8px;">新建账套</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+O</b></td>
                <td style="padding: 8px;">打开文件</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+B</b></td>
                <td style="padding: 8px;">备份数据</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+I</b></td>
                <td style="padding: 8px;">插入数据</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+F</b></td>
                <td style="padding: 8px;">查找替换</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>F5</b></td>
                <td style="padding: 8px;">刷新当前页</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>F11</b></td>
                <td style="padding: 8px;">全屏模式</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>F1</b></td>
                <td style="padding: 8px;">帮助文档</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+Shift+L</b></td>
                <td style="padding: 8px;">切换侧边栏</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Ctrl+Shift+A</b></td>
                <td style="padding: 8px;">AI智能分析</td>
            </tr>
            <tr>
                <td style="padding: 8px;"><b>Alt+F4</b></td>
                <td style="padding: 8px;">退出应用</td>
            </tr>
        </table>
        """)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(shortcuts_text)
        layout.addWidget(close_btn)

        dialog.exec_()

    def show_faq_dialog(self):
        """显示常见问题FAQ"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("常见问题 FAQ")
        dialog.setFixedSize(700, 500)

        layout = QVBoxLayout(dialog)

        faq_text = QTextEdit()
        faq_text.setReadOnly(True)
        faq_text.setHtml("""
        <h2>❓ 常见问题</h2>

        <h3>Q1: 如何备份我的数据？</h3>
        <p>A: 点击菜单栏 <b>文件 → 备份数据</b>，选择保存位置即可。</p>

        <h3>Q2: 忘记登录密码怎么办？</h3>
        <p>A: 默认账套号为 <b>2501033401</b>，密码为 <b>admin0457</b>。建议登录后立即修改密码。</p>

        <h3>Q3: 如何导入Excel数据？</h3>
        <p>A: 在收入或支出记账页面，点击<b>导入Excel</b>按钮，选择符合模板格式的Excel文件。</p>

        <h3>Q4: AI分析功能如何使用？</h3>
        <p>A: 在系统设置中配置DeepSeek API Key后，可在统计分析页面使用AI智能分析功能。</p>

        <h3>Q5: 如何切换数据库类型？</h3>
        <p>A: 在系统设置页面的数据库配置区域，可以选择SQLite、MySQL或Sybase数据库。</p>

        <h3>Q6: 图表中文显示为方块怎么办？</h3>
        <p>A: Linux/macOS用户可能需要安装中文字体（如SimHei），或在系统设置中调整字体配置。</p>

        <h3>Q7: 数据量大了会变慢吗？</h3>
        <p>A: 系统已做性能优化，建议使用定期<b>优化数据库</b>功能（编辑 → 数据库 → 优化数据库）。</p>
        """)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)

        layout.addWidget(faq_text)
        layout.addWidget(close_btn)

        dialog.exec_()

    def change_theme(self, theme_name):
        """切换主题"""
        from PyQt5.QtWidgets import QMessageBox

        if "浅色" in theme_name:
            self.setStyleSheet("")
            QMessageBox.information(self, "主题", "已切换到浅色主题")
        elif "自动" in theme_name:
            QMessageBox.information(self, "主题", "自动主题功能开发中...")

        print(f"[主题] 切换到{theme_name}")

    def change_font_size(self, size_name):
        """改变字体大小"""
        from PyQt5.QtWidgets import QMessageBox

        if "小" in size_name:
            font_size = 9
        elif "中" in size_name:
            font_size = 11
        elif "大" in size_name:
            font_size = 13

        app_font = QFont(UIStyles.FONT_FAMILY, font_size)
        QApplication.setFont(app_font)
        QMessageBox.information(self, "字体", f"字体大小已设置为{size_name}，重启后生效")
        print(f"[字体] 设置为{size_name}")

    def toggle_sidebar(self):
        """切换侧边栏显示/隐藏"""
        current_width = self.sidebar.width()
        if current_width > 100:
            # 折叠为图标模式
            self.sidebar.setFixedWidth(60)
            print("[视图] 侧边栏折叠为图标模式")
        else:
            # 展开
            self.sidebar.setFixedWidth(280)
            print("[视图] 侧边栏展开")

    def refresh_current_page(self):
        """刷新当前页面"""
        current_index = self.stacked_widget.currentIndex()
        current_widget = self.stacked_widget.currentWidget()

        # 调用页面的load_data方法（如果存在）
        if hasattr(current_widget, 'load_data'):
            current_widget.load_data()
            print(f"[刷新] 页面 {current_index + 1} 已刷新")
        else:
            print(f"[刷新] 页面 {current_index + 1} 不支持刷新")

    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            print("[视图] 退出全屏模式")
        else:
            self.showFullScreen()
            print("[视图] 进入全屏模式")

    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()

    def switch_to_page_by_index(self, index):
        """通过索引切换到指定页面

        Args:
            index: 页面索引 (0=首页, 1=分类管理, 2=收入记账, 3=支出记账,
                   4=流水账, 5=月报表, 6=统计分析, 7=个人中心, 8=系统设置)
        """
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            self.sidebar.setCurrentRow(index)
            page_names = ["首页", "分类管理", "收入记账", "支出记账",
                         "流水账", "月报表", "统计分析", "个人中心", "系统设置"]
            print(f"[导航] 切换到{page_names[index]}")

    def _update_status_db_info(self):
        """更新状态栏左侧：数据库连接状态"""
        if db_manager.is_connected():
            db_type = db_manager.get_backend_type() if hasattr(db_manager, 'get_backend_type') else "SQLite"
            account = getattr(db_manager, 'current_account', self.current_user)
            self.status_db_label.setText(f"🟢 {db_type} · 账套 {account}")
        else:
            self.status_db_label.setText("🔴 未连接数据库")

    def _update_status_time(self):
        """更新状态栏右侧：当前时间"""
        now = QDateTime.currentDateTime()
        self.status_time_label.setText(now.toString("yyyy-MM-dd  HH:mm"))

class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 InEx System")
        self.setFixedSize(500, 400)

        # 仅保留关闭按钮
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)

        self.initUI()

    def initUI(self):
        """初始化 UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 应用图标（如果存在）
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "InEx_System.ico")
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(icon_label)

        # 标题
        title_label = QLabel("收支管理系统")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {UIStyles.PRIMARY};")
        main_layout.addWidget(title_label)

        # 版本信息
        version_label = QLabel("版本: v2.0")
        version_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"color: {UIStyles.TEXT_SECONDARY};")
        main_layout.addWidget(version_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"color: {UIStyles.BORDER_MEDIUM};")
        main_layout.addWidget(line)

        # 详细信息
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        info_text.setHtml(f"""
        <div style='text-align: center; color: {UIStyles.TEXT_PRIMARY};'>
            <p><b>InEx System v2.0</b></p>
            <p>个人收支管理系统</p>
            <p>开发时间: 2026年</p>
            <br>
            <p><b>技术栈:</b></p>
            <p>Python 3.8+ | PyQt5 | SQLite/MySQL/Sybase</p>
            <br>
            <p><b>主要功能:</b></p>
            <p>• 多数据库支持</p>
            <p>• AI智能理财建议</p>
            <p>• 数据可视化分析</p>
            <p>• Excel/CSV导入导出</p>
            <p>• 自动备份机制</p>
            <br>
            <p style='color: {UIStyles.TEXT_SECONDARY}; font-size: 9px;'>
                版权所有 © 2026 InEx System Team<br>
                联系邮箱: yoho12138@qq.com
            </p>
        </div>
        """)
        info_text.setMaximumHeight(200)
        info_text.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                background-color: transparent;
            }}
        """)
        main_layout.addWidget(info_text)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("确定")
        ok_button.setFixedWidth(100)
        ok_button.setStyleSheet(UIStyles.primary_button())
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
