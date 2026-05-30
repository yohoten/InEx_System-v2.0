# -*- coding: utf-8 -*-
"""Toast提示组件 - 美化版（类型着色 + 左侧指示条 + 滑入动效）"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont
from ui.styles import UIStyles


class Toast(QFrame):
    """Toast提示组件（美化版）"""

    # 类型 → (背景色, 文字色, 指示条色, 默认图标)
    _STYLES = {
        "success": ("#ecfdf5", "#065f46", "#10b981", "✓"),
        "error": ("#fef2f2", "#991b1b", "#ef4444", "✗"),
        "warning": ("#fffbeb", "#92400e", "#f59e0b", "⚠"),
        "info": ("#eff6ff", "#1e40af", "#3b82f6", "ℹ"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setMaximumWidth(440)
        self.setMinimumWidth(260)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 6, 14, 6)
        layout.setSpacing(10)

        # 左侧彩色指示条
        self.indicator = QFrame()
        self.indicator.setFixedWidth(4)
        self.indicator.setFixedHeight(32)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFont(QFont("Segoe UI Emoji", 13))

        # 消息文字
        self.message_label = QLabel()
        self.message_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.message_label.setWordWrap(True)

        layout.addWidget(self.indicator)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.message_label)
        layout.addStretch()

        self.hide()
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._animate_out)

    def _apply_type_style(self, toast_type):
        """按类型应用配色"""
        bg, fg, accent, _ = self._STYLES.get(toast_type, self._STYLES["info"])
        self.indicator.setStyleSheet(f"background-color: {accent}; border-radius: 2px;")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {accent}33;
                border-radius: 10px;
            }}
        """)
        self.message_label.setStyleSheet(f"color: {fg}; font-weight: 500;")

    def _animate_in(self):
        """底部滑入动画"""
        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
            center_x = (pw - self.width()) // 2
            target_y = ph - 80
            start_y = ph + 10
            self.move(center_x, start_y)
            self.show()
            self.raise_()
            anim = QPropertyAnimation(self, b"pos")
            anim.setDuration(280)
            anim.setStartValue(QPoint(center_x, start_y))
            anim.setEndValue(QPoint(center_x, target_y))
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.start()
        else:
            self.show()

    def _animate_out(self):
        """淡出隐藏"""
        self.hide()

    def show_message(self, message, toast_type="info", icon="", duration=2500):
        """
        显示Toast消息

        Args:
            message: 消息文本
            toast_type: 类型 (success/error/warning/info)
            icon: 图标emoji，为空则使用默认图标
            duration: 显示时长(ms)，0表示不自动隐藏
        """
        self._apply_type_style(toast_type)

        # 图标
        _, _, _, default_icon = self._STYLES.get(toast_type, self._STYLES["info"])
        self.icon_label.setText(icon or default_icon)

        self.message_label.setText(message)
        self._animate_in()

        if duration > 0:
            self.hide_timer.start(duration)

    def success(self, message, duration=2000):
        self.show_message(message, "success", duration=duration)

    def error(self, message, duration=3500):
        self.show_message(message, "error", duration=duration)

    def warning(self, message, duration=3000):
        self.show_message(message, "warning", duration=duration)

    def info(self, message, duration=2000):
        self.show_message(message, "info", duration=duration)

    def loading(self, message="处理中..."):
        self.show_message(message, "info", "⏳", 0)
