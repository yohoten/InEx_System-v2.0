# -*- coding: utf-8 -*-
"""
登录和注册对话框模块
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QCheckBox, QMessageBox,
                             QFrame, QSpacerItem, QSizePolicy, QWidget, QComboBox)
from PyQt5.QtCore import Qt, QRect, QSettings, pyqtSignal, QUrl, QTimer
from PyQt5.QtGui import QFont, QLinearGradient, QPainter, QColor, QBrush, QIcon
from PyQt5.QtGui import QDesktopServices
import os
from ui.styles import UIStyles
from utils.auth_manager import AuthManager
from models.db_backend import db_manager


class GradientFrame(QFrame):
    """自定义渐变背景框架"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 创建垂直渐变：深蓝 → 中蓝 → 浅蓝
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#2C3E50"))      # 深蓝
        gradient.setColorAt(0.5, QColor("#34495E"))     # 中蓝
        gradient.setColorAt(1, QColor("#2980B9"))       # 浅蓝

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


class SwitchButton(QWidget):
    """右上角切换按钮（双圆点单选样式：● 登录 / ● 注册）"""

    login_clicked = pyqtSignal()
    register_clicked = pyqtSignal()

    def __init__(self, is_login_mode=True, parent=None):
        super().__init__(parent)
        self.is_login_mode = is_login_mode
        self.setFixedSize(140, 28)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 左半：登录
        login_active = self.is_login_mode
        dot = "●" if login_active else "○"
        color = "#10b981" if login_active else "#d1d5db"
        painter.setPen(QColor(color))
        font = QFont(UIStyles.FONT_FAMILY, 12, QFont.Bold if login_active else QFont.Normal)
        painter.setFont(font)
        painter.drawText(QRect(0, 0, 70, 20), Qt.AlignCenter, f"{dot} 登录")

        # 右半：注册
        reg_active = not self.is_login_mode
        dot = "●" if reg_active else "○"
        color = "#10b981" if reg_active else "#d1d5db"
        painter.setPen(QColor(color))
        font = QFont(UIStyles.FONT_FAMILY, 12, QFont.Bold if reg_active else QFont.Normal)
        painter.setFont(font)
        painter.drawText(QRect(70, 0, 70, 20), Qt.AlignCenter, f"{dot} 注册")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.x()
            if x < 70:
                # 点击登录
                if not self.is_login_mode:
                    self.is_login_mode = True
                    self.login_clicked.emit()
                    self.update()
            else:
                # 点击注册
                if self.is_login_mode:
                    self.is_login_mode = False
                    self.register_clicked.emit()
                    self.update()


class LoginDialog(QDialog):
    """登录对话框"""

    login_success = pyqtSignal(str, str)  # account, password

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("收支管理系统 - 密码验证")
        self.setFixedSize(850, 520)  # 优化：增大窗口尺寸，提供更好的视觉体验

        # 窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "InEx_System.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 仅保留关闭按钮，不允许最小化/最大化
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)

        # 初始化设置
        self.settings = QSettings('InExSystem', 'Login')

        # 初始化认证管理器（替代硬编码凭据）
        self.auth_manager = AuthManager()

        # 首次运行时初始化默认凭据
        if not self.auth_manager.has_credentials():
            self.auth_manager.initialize_default_credentials()
            QMessageBox.information(
                self,
                "首次运行提示",
                "系统已使用默认凭据初始化：\n"
                "账号：2501033401\n"
                "密码：admin0457\n\n"
                "为了安全起见，建议登录后立即修改密码。"
            )

        self.initUI()
        self.connectSignals()

        # 加载记住的密码
        self.load_remembered_password()

    def initUI(self):
        """初始化 UI - 左右分栏布局"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== 中间内容区域（左右分栏）==========
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_widget.setLayout(content_layout)

        # ===== 左侧区域（45%）=====
        left_frame = GradientFrame()
        left_frame.setMinimumWidth(382)  # 850 * 45% ≈ 382
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(40, 50, 40, 50)  # 优化：增加内边距
        left_layout.setSpacing(25)  # 优化：增加间距
        left_frame.setLayout(left_layout)

        # 主标题
        title_label = QLabel("收支管理系统")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 24, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white;")
        left_layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("InEx_System v2.0")
        subtitle_label.setFont(QFont(UIStyles.FONT_FAMILY, 16))  # 优化：字体从15增加到16
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #E0E0E0;")
        left_layout.addWidget(subtitle_label)

        # 装饰文案
        # decor_label = QLabel("("记账 · 科学理财")
        # decor_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        # decor_label.setAlignment(Qt.AlignCenter)
        # decor_label.setStyleSheet("color: #B0B0B0;")
        # left_layout.addWidget(decor_label)

        left_layout.addStretch()

        # 底部标识
        course_label = QLabel('"数智经管 · 创见未来"\n创意作品设计大赛参赛作品')
        course_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))  # 优化：字体从10增加到11
        course_label.setAlignment(Qt.AlignCenter)
        course_label.setStyleSheet("color: #B0B0B0;")
        course_label.setWordWrap(True)
        left_layout.addWidget(course_label)

        left_layout.addStretch()

        content_layout.addWidget(left_frame, 45)  # 优化：拉伸因子调整为45

        # ===== 右侧区域（55%）=====
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(45, 50, 45, 50)  # 优化：水平边距从50调整为45
        right_layout.setSpacing(20)  # 优化：调整间距从25回退到20
        right_frame.setLayout(right_layout)

        # 右上角切换按钮
        switch_row = QHBoxLayout()
        switch_row.addStretch()
        self.switch_btn = SwitchButton(is_login_mode=True)
        self.switch_btn.register_clicked.connect(self.show_register_dialog)
        switch_row.addWidget(self.switch_btn)
        right_layout.addLayout(switch_row)

        # 登录标题
        login_title = QLabel("账号登录")
        login_title.setFont(QFont(UIStyles.FONT_FAMILY, 22, QFont.Bold))  # 优化：字体从20增加到22
        login_title.setStyleSheet("color: #2C3E50;")
        right_layout.addWidget(login_title)

        right_layout.addSpacing(12)  # 优化：标题与表单间距调整为12

        # 账套号输入
        account_label = QLabel("账套号：")
        account_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))  # 优化：字体从10增加到11
        account_label.setStyleSheet("color: #2C3E50;")

        self.account_input = QComboBox()
        self.account_input.setEditable(True)
        self.account_input.setInsertPolicy(QComboBox.NoInsert)
        self.account_input.lineEdit().setPlaceholderText("选择或搜索账套（输入姓名/账套号）")
        self.account_input.lineEdit().setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.account_input.setFixedHeight(42)
        self.account_input.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus, QComboBox:focus-within {
                border: 2px solid #3498DB;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #E0E0E0;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox QAbstractItemView {
                font-size: 13px;
                padding: 4px;
                selection-background-color: #3498DB;
            }
        """)
        # 延迟加载账套列表（确保数据库已连接）
        QTimer.singleShot(100, self._load_account_list)

        account_form_layout = QVBoxLayout()
        account_form_layout.setSpacing(6)  # 优化：label与input间距调整为6
        account_form_layout.addWidget(account_label)
        account_form_layout.addWidget(self.account_input)
        right_layout.addLayout(account_form_layout)

        # 密码输入
        password_label = QLabel("密 码：")
        password_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))  # 优化：字体从10增加到11
        password_label.setStyleSheet("color: #2C3E50;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont(UIStyles.FONT_FAMILY, 11))  # 优化：字体从10增加到11
        self.password_input.setFixedHeight(42)  # 优化：高度从35增加到42，更易点击
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
        """)

        password_form_layout = QVBoxLayout()
        password_form_layout.setSpacing(6)  # 优化：label与input间距调整为6
        password_form_layout.addWidget(password_label)
        password_form_layout.addWidget(self.password_input)
        right_layout.addLayout(password_form_layout)

        # 选项区域：记住密码 + 忘记密码
        option_row_layout = QHBoxLayout()
        option_row_layout.setSpacing(10)

        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.remember_checkbox.setStyleSheet("color: #555555;")
        option_row_layout.addWidget(self.remember_checkbox)

        option_row_layout.addStretch()

        self.forgot_button = QPushButton("忘记密码？")
        self.forgot_button.setFlat(True)
        self.forgot_button.setCursor(Qt.PointingHandCursor)
        self.forgot_button.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.forgot_button.setStyleSheet(f"color: {UIStyles.PRIMARY}; border: none;")
        option_row_layout.addWidget(self.forgot_button)

        right_layout.addLayout(option_row_layout)

        right_layout.addSpacing(15)  # 优化：增加间距从10到15

        # 登录按钮
        self.login_button = QPushButton("登 录")
        self.login_button.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setFixedHeight(48)
        self.login_button.setStyleSheet(UIStyles.primary_button(font_size=16, font_weight="bold"))
        right_layout.addWidget(self.login_button)

        right_layout.addStretch()

        content_layout.addWidget(right_frame, 55)  # 优化：拉伸因子调整为55

        main_layout.addWidget(content_widget)

        # ========== 底部版权栏 ==========
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(45)  # 优化：底部版权栏高度从42调整为45
        bottom_frame.setStyleSheet(f"background-color: {UIStyles.BG_GRAY_100};")
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(15, 12, 15, 12)  # 优化：调整内边距
        bottom_layout.setSpacing(5)
        bottom_frame.setLayout(bottom_layout)

        author_text = QLabel('@2026 | Author：yohoten | S-ID：12607320270457')
        author_text.setFont(QFont(UIStyles.FONT_FAMILY, 11))  # 优化：字体从10增加到11
        author_text.setAlignment(Qt.AlignCenter)
        author_text.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")

        bottom_layout.addWidget(author_text)

        main_layout.addWidget(bottom_frame)

        self.setLayout(main_layout)

    def connectSignals(self):
        """连接信号槽"""
        self.login_button.clicked.connect(self.accept_login)
        self.forgot_button.clicked.connect(self.show_forgot_password)
        self.account_input.lineEdit().returnPressed.connect(lambda: self.password_input.setFocus())
        self.password_input.returnPressed.connect(self.accept_login)

    def load_remembered_password(self):
        """加载记住的密码"""
        if self.settings.value('remember', 'false') == 'true':
            self.account_input.setEditText(self.settings.value('account', ''))
            self.password_input.setText(self.settings.value('password', ''))
            self.remember_checkbox.setChecked(True)
        else:
            # 不清除用户手动输入，保持空白或上次输入
            pass

    def save_remembered_password(self):
        """记住密码"""
        if self.remember_checkbox.isChecked():
            self.settings.setValue('remember', 'true')
            self.settings.setValue('account', self.account_input.currentText())
            self.settings.setValue('password', self.password_input.text())
        else:
            self.settings.setValue('remember', 'false')
            self.settings.remove('account')
            self.settings.remove('password')

    def _load_account_list(self):
        """从数据库加载所有账套到下拉列表"""
        try:
            if not db_manager.is_connected():
                return
            accounts = db_manager.get_accounts()
            if not accounts:
                return

            self.account_input.clear()
            # account tuple: zth, ztmc, xh, xm, rq, xb, csd, bj, xz, mm, bz
            for acc in accounts:
                zth = acc[0] if len(acc) > 0 else ""
                ztmc = acc[1] if len(acc) > 1 else ""
                xm = acc[3] if len(acc) > 3 else ""
                bj = acc[7] if len(acc) > 7 else ""
                display = f"{zth} - {xm or ztmc or '未知'}"
                if bj:
                    display += f" ({bj})"
                self.account_input.addItem(display, zth)

            # 恢复上次登录的账套
            last_account = self.settings.value("last_account", "")
            if last_account:
                idx = self.account_input.findData(last_account)
                if idx >= 0:
                    self.account_input.setCurrentIndex(idx)

        except Exception as e:
            print(f"[登录] 加载账套列表失败: {e}")

    def accept_login(self):
        """处理登录"""
        # 优先取选中项的 data（zth），否则取输入的文本
        current_data = self.account_input.currentData()
        if current_data:
            account = str(current_data).strip()
        else:
            account = self.account_input.currentText().strip()

        password = self.password_input.text().strip()

        if not account:
            QMessageBox.warning(self, "警告", "请输入或选择账套号！")
            self.account_input.setFocus()
            return

        if not password:
            QMessageBox.warning(self, "警告", "请输入密码！")
            self.password_input.setFocus()
            return

        # 使用认证管理器验证凭据
        if self.auth_manager.verify_user_credentials(account, password):
            self.save_remembered_password()
            # 记住最后登录的账套
            self.settings.setValue("last_account", account)
            print(f"[登录] 用户 {account} 登录成功")

            self.login_success.emit(account, password)

            self.accept()
        else:
            QMessageBox.warning(self, "登录失败", "账套号或密码错误，请重新输入！")
            print(f"[登录] 用户 {account} 登录失败")
            self.password_input.clear()
            self.password_input.setFocus()


    def show_forgot_password(self):
        """显示忘记密码提示，并添加打开帐套数据登记表的按钮"""
        msg = QMessageBox(self)
        msg.setWindowTitle("提示")
        msg.setText(
            "请联系管理员重置密码\n"
            "管理员联系方式:\n"
            "邮箱：yoho12138 @qq .com\n"
            "电话：17324059727"
        )
        msg.setInformativeText("访问帐套数据登记表：\nhttps://www.kdocs.cn/l/cvrnsGrWjSgp")

        open_btn = msg.addButton("打开帐套数据登记表", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.kdocs.cn/l/cvrnsGrWjSgp")))

        msg.exec_()
        print("[登录] 用户点击忘记密码")

    def show_change_password_dialog(self):
        """显示修改密码对话框"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

        dialog = QDialog(self)
        dialog.setWindowTitle("修改密码")
        dialog.setFixedSize(400, 250)
        dialog.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 20, 30, 20)

        # 旧密码输入
        old_pwd_label = QLabel("当前密码：")
        old_pwd_input = QLineEdit()
        old_pwd_input.setEchoMode(QLineEdit.Password)
        old_pwd_input.setPlaceholderText("请输入当前密码")
        layout.addWidget(old_pwd_label)
        layout.addWidget(old_pwd_input)

        # 新密码输入
        new_pwd_label = QLabel("新密码：")
        new_pwd_input = QLineEdit()
        new_pwd_input.setEchoMode(QLineEdit.Password)
        new_pwd_input.setPlaceholderText("请输入新密码（至少6位）")
        layout.addWidget(new_pwd_label)
        layout.addWidget(new_pwd_input)

        # 确认新密码
        confirm_pwd_label = QLabel("确认新密码：")
        confirm_pwd_input = QLineEdit()
        confirm_pwd_input.setEchoMode(QLineEdit.Password)
        confirm_pwd_input.setPlaceholderText("请再次输入新密码")
        layout.addWidget(confirm_pwd_label)
        layout.addWidget(confirm_pwd_input)

        # 按钮区域
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(UIStyles.primary_button())
        cancel_btn.setStyleSheet(UIStyles.secondary_button())

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)

        # 确定按钮事件
        def on_confirm():
            old_password = old_pwd_input.text().strip()
            new_password = new_pwd_input.text().strip()
            confirm_password = confirm_pwd_input.text().strip()

            # 验证输入
            if not old_password:
                QMessageBox.warning(dialog, "警告", "请输入当前密码！")
                return

            if not new_password:
                QMessageBox.warning(dialog, "警告", "请输入新密码！")
                return

            if len(new_password) < 6:
                QMessageBox.warning(dialog, "警告", "新密码长度不能少于6位！")
                return

            if new_password != confirm_password:
                QMessageBox.warning(dialog, "警告", "两次输入的新密码不一致！")
                return

            # 调用认证管理器修改密码
            if self.auth_manager.change_password(old_password, new_password):
                QMessageBox.information(dialog, "成功", "密码修改成功！请使用新密码重新登录。")
                dialog.accept()
                # 清空当前登录界面，要求重新登录
                self.account_input.clear()
                self.password_input.clear()
                self.account_input.setFocus()
            else:
                QMessageBox.critical(dialog, "失败", "密码修改失败，请检查当前密码是否正确！")

        ok_btn.clicked.connect(on_confirm)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()
        print("[登录] 用户尝试修改密码")

    def show_register_dialog(self):
        """显示注册新账号对话框"""
        register_dialog = RegisterDialog(self.auth_manager, self)
        if register_dialog.exec_() == QDialog.Accepted:
            # 如果注册成功，自动填充账号密码
            account = register_dialog.get_registered_account()
            password = register_dialog.get_registered_password()
            if account and password:
                self.account_input.setEditText(account)
                self.password_input.setText(password)
                self.password_input.setFocus()


class RegisterDialog(QDialog):
    """注册对话框"""
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.registered_account = None
        self.registered_password = None
        
        self.setWindowTitle("收支管理系统 - 注册账号")
        self.setFixedSize(850, 520)
        
        # 窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "InEx_System.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # 仅保留关闭按钮
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        
        self.initUI()
        self.connectSignals()
        
    def initUI(self):
        """初始化注册界面 UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ========== 中间内容区域（左右分栏）==========
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_widget.setLayout(content_layout)
        
        # ===== 左侧区域（45%）=====
        left_frame = GradientFrame()
        left_frame.setMinimumWidth(382)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(40, 50, 40, 50)
        left_layout.setSpacing(25)
        left_frame.setLayout(left_layout)
        
        # 主标题
        title_label = QLabel("收支管理系统")
        title_label.setFont(QFont(UIStyles.FONT_FAMILY, 26, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white;")
        left_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("InEx_System v2.0")
        subtitle_label.setFont(QFont(UIStyles.FONT_FAMILY, 16))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #E0E0E0;")
        left_layout.addWidget(subtitle_label)
        
        left_layout.addStretch()
        
        # 注册提示
        tip_label = QLabel("创建新账号\n开启您的财务管理之旅")
        tip_label.setFont(QFont(UIStyles.FONT_FAMILY, 12))
        tip_label.setAlignment(Qt.AlignCenter)
        tip_label.setStyleSheet("color: #E0E0E0;")
        tip_label.setWordWrap(True)
        left_layout.addWidget(tip_label)
        
        left_layout.addStretch()
        
        # 底部标识
        course_label = QLabel('"数智经管 · 创见未来"\n创意作品设计大赛参赛作品')
        course_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        course_label.setAlignment(Qt.AlignCenter)
        course_label.setStyleSheet("color: #B0B0B0;")
        course_label.setWordWrap(True)
        left_layout.addWidget(course_label)
        
        left_layout.addStretch()
        
        content_layout.addWidget(left_frame, 45)
        
        # ===== 右侧区域（55%）=====
        right_frame = QFrame()
        right_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(45, 50, 45, 50)
        right_layout.setSpacing(20)
        right_frame.setLayout(right_layout)

        # 右上角切换按钮
        switch_row_reg = QHBoxLayout()
        switch_row_reg.addStretch()
        self.switch_btn_reg = SwitchButton(is_login_mode=False)
        self.switch_btn_reg.login_clicked.connect(self.accept)
        switch_row_reg.addWidget(self.switch_btn_reg)
        right_layout.addLayout(switch_row_reg)
        
        # 注册标题
        register_title = QLabel("创建新账号")
        register_title.setFont(QFont(UIStyles.FONT_FAMILY, 22, QFont.Bold))
        register_title.setStyleSheet("color: #2C3E50;")
        right_layout.addWidget(register_title)
        
        right_layout.addSpacing(10)
        
        # 账套号输入
        account_label = QLabel("账套号：")
        account_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        account_label.setStyleSheet("color: #2C3E50;")
        
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("请输入账套号（4-20位）")
        self.account_input.setMaxLength(20)
        self.account_input.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.account_input.setFixedHeight(42)
        self.account_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
        """)
        
        account_form_layout = QVBoxLayout()
        account_form_layout.setSpacing(6)
        account_form_layout.addWidget(account_label)
        account_form_layout.addWidget(self.account_input)
        right_layout.addLayout(account_form_layout)
        
        # 密码输入
        password_label = QLabel("密码：")
        password_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        password_label.setStyleSheet("color: #2C3E50;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码（至少6位）")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.password_input.setFixedHeight(42)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
        """)
        
        password_form_layout = QVBoxLayout()
        password_form_layout.setSpacing(6)
        password_form_layout.addWidget(password_label)
        password_form_layout.addWidget(self.password_input)
        right_layout.addLayout(password_form_layout)
        
        # 确认密码输入
        confirm_label = QLabel("确认密码：")
        confirm_label.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        confirm_label.setStyleSheet("color: #2C3E50;")
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("请再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setFont(QFont(UIStyles.FONT_FAMILY, 11))
        self.confirm_input.setFixedHeight(42)
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
        """)
        
        confirm_form_layout = QVBoxLayout()
        confirm_form_layout.setSpacing(6)
        confirm_form_layout.addWidget(confirm_label)
        confirm_form_layout.addWidget(self.confirm_input)
        right_layout.addLayout(confirm_form_layout)
        
        right_layout.addSpacing(10)
        
        # 注册按钮
        self.register_button = QPushButton("注 册")
        self.register_button.setFont(QFont(UIStyles.FONT_FAMILY, 16, QFont.Bold))
        self.register_button.setCursor(Qt.PointingHandCursor)
        self.register_button.setFixedHeight(48)
        self.register_button.setStyleSheet(UIStyles.success_button(font_size=16, font_weight="bold"))
        right_layout.addWidget(self.register_button)
        
        right_layout.addStretch()
        
        content_layout.addWidget(right_frame, 55)
        
        main_layout.addWidget(content_widget)
        
        # ========== 底部版权栏 ==========
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(45)
        bottom_frame.setStyleSheet(f"background-color: {UIStyles.BG_GRAY_100};")
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(15, 12, 15, 12)
        bottom_layout.setSpacing(5)
        bottom_frame.setLayout(bottom_layout)
        
        author_text = QLabel('@2026 | Author：yohoten | S-ID：12607320270457')
        author_text.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        author_text.setAlignment(Qt.AlignCenter)
        author_text.setStyleSheet(f"color: {UIStyles.TEXT_TERTIARY};")
        
        bottom_layout.addWidget(author_text)
        
        main_layout.addWidget(bottom_frame)
        
        self.setLayout(main_layout)
        
    def connectSignals(self):
        """连接信号槽"""
        self.register_button.clicked.connect(self.handle_register)
        self.account_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.password_input.returnPressed.connect(lambda: self.confirm_input.setFocus())
        self.confirm_input.returnPressed.connect(self.handle_register)
        
    def handle_register(self):
        """处理注册"""
        account = self.account_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        
        # 验证输入
        if not account or len(account) < 4:
            QMessageBox.warning(self, "警告", "账套号至少需要4位！")
            self.account_input.setFocus()
            return
            
        if len(account) > 20:
            QMessageBox.warning(self, "警告", "账套号不能超过20位！")
            self.account_input.setFocus()
            return
            
        if not password or len(password) < 6:
            QMessageBox.warning(self, "警告", "密码至少需要6位！")
            self.password_input.setFocus()
            return
            
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次密码输入不一致！")
            self.confirm_input.clear()
            self.confirm_input.setFocus()
            return
            
        # 调用认证管理器注册用户
        if self.auth_manager.register_user(account, password):
            self.registered_account = account
            self.registered_password = password
            QMessageBox.information(self, "成功", f"账号 {account} 注册成功！\n即将跳转到登录界面。")
            self.accept()
        else:
            QMessageBox.critical(self, "失败", "注册失败，可能账号已存在或数据库未连接")
            
    def get_registered_account(self):
        """获取注册的账号"""
        return self.registered_account
        
    def get_registered_password(self):
        """获取注册的密码"""
        return self.registered_password

