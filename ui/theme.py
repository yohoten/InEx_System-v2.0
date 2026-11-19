# -*- coding: utf-8 -*-
"""主题引擎 | 集中管理浅色/深色两套配色与全局 QSS。

设计目标
- 以一份全局 QSS 统一所有标准控件的外观（基础层）。
- 控件自身的 setStyleSheet 仍然可以覆盖（Qt 优先级规则），因此页面内联样式
  继续生效；切换主题时同步 UIStyles 色板，使随后重刷的样式使用新配色。
- 主题持久化到 config.json 的 ui.theme，跟随用户选择。
"""
from __future__ import annotations

import threading
from typing import Dict

# ── 语义色板 ─────────────────────────────────────────────
# 两套主题共享同一套语义键，便于 QSS 模板与 UIStyles 同步。
PALETTES: Dict[str, Dict[str, str]] = {
    "light": {
        "primary": "#6366f1", "primary_hover": "#4f46e5", "primary_light": "#eef2ff",
        "success": "#10b981", "success_hover": "#059669", "success_light": "#ecfdf5",
        "danger": "#ef4444", "danger_hover": "#dc2626", "danger_light": "#fef2f2",
        "warning": "#f59e0b", "warning_hover": "#d97706", "warning_light": "#fffbeb",
        "info": "#3b82f6", "info_hover": "#2563eb", "info_light": "#eff6ff",
        "text_primary": "#1f2937", "text_secondary": "#4b5563", "text_tertiary": "#6b7280",
        "text_disabled": "#9ca3af", "text_on_accent": "#ffffff",
        "border": "#e5e7eb", "border_strong": "#d1d5db",
        "bg_base": "#f5f5f7", "bg_surface": "#ffffff", "bg_subtle": "#f9fafb",
        "bg_hover": "#f3f4f6", "bg_selected": "#eef2ff",
        "sidebar_bg": "#1e293b", "sidebar_text": "#e2e8f0",
        "sidebar_hover": "#334155", "sidebar_selected": "#6366f1",
        "shadow": "rgba(15,23,42,0.08)",
    },
    "dark": {
        "primary": "#818cf8", "primary_hover": "#6366f1", "primary_light": "#312e81",
        "success": "#34d399", "success_hover": "#10b981", "success_light": "#064e3b",
        "danger": "#f87171", "danger_hover": "#ef4444", "danger_light": "#7f1d1d",
        "warning": "#fbbf24", "warning_hover": "#f59e0b", "warning_light": "#78350f",
        "info": "#60a5fa", "info_hover": "#3b82f6", "info_light": "#1e3a8a",
        "text_primary": "#e5e7eb", "text_secondary": "#cbd5e1", "text_tertiary": "#94a3b8",
        "text_disabled": "#64748b", "text_on_accent": "#ffffff",
        "border": "#334155", "border_strong": "#475569",
        "bg_base": "#0f172a", "bg_surface": "#1e293b", "bg_subtle": "#172033",
        "bg_hover": "#334155", "bg_selected": "#312e81",
        "sidebar_bg": "#0b1120", "sidebar_text": "#cbd5e1",
        "sidebar_hover": "#1e293b", "sidebar_selected": "#6366f1",
        "shadow": "rgba(0,0,0,0.4)",
    },
}

ALIASES = {
    "light": "light", "浅色": "light", "default": "light", "默认": "light",
    "dark": "dark", "深色": "dark",
}


def normalize(name: str) -> str:
    """把中文/别名主题名归一到 light/dark（未知值一律回退 light）。"""
    name = (name or "light").strip().lower()
    if name in ALIASES:
        return ALIASES[name]
    if "深" in name or "dark" in name:
        return "dark"
    return "light"


GLOBAL_QSS = """
QWidget {{
    background-color: {bg_base};
    color: {text_primary};
    font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
}}
QMainWindow, QDialog {{ background-color: {bg_base}; }}
QFrame {{ background-color: {bg_surface}; border-radius: 8px; }}
QLabel {{ color: {text_primary}; background: transparent; }}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    background-color: {bg_surface};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: {primary};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 1px solid {primary};
}}
QPushButton {{
    background-color: {bg_surface};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 6px 12px;
}}
QPushButton:hover {{ background-color: {bg_hover}; border-color: {primary}; }}
QPushButton:pressed {{ background-color: {bg_selected}; }}
QPushButton:disabled {{ color: {text_disabled}; background-color: {bg_subtle}; }}
QComboBox {{
    background-color: {bg_surface};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {bg_surface};
    color: {text_primary};
    selection-background-color: {primary};
    border: 1px solid {border};
}}
QCheckBox, QRadioButton {{ color: {text_primary}; background: transparent; spacing: 6px; }}
QGroupBox {{
    color: {text_primary};
    background-color: {bg_surface};
    border: 1px solid {border};
    border-radius: 8px;
    margin-top: 12px;
    padding: 8px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QTableWidget, QTableView {{
    background-color: {bg_surface};
    color: {text_primary};
    alternate-background-color: {bg_subtle};
    gridline-color: {border};
    border: 1px solid {border};
    border-radius: 8px;
    selection-background-color: {primary_light};
    selection-color: {text_primary};
}}
QHeaderView::section {{
    background-color: {bg_subtle};
    color: {text_secondary};
    border: none;
    border-bottom: 1px solid {border};
    padding: 6px;
    font-weight: bold;
}}
QListWidget, QTreeWidget {{
    background-color: {bg_surface};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 8px;
}}
QTabWidget::pane {{ border: 1px solid {border}; background-color: {bg_surface}; border-radius: 8px; }}
QTabBar::tab {{
    background-color: {bg_subtle};
    color: {text_secondary};
    padding: 6px 14px;
    border: 1px solid {border};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}
QTabBar::tab:selected {{ background-color: {bg_surface}; color: {primary}; border-bottom: 2px solid {primary}; }}
QScrollBar:vertical {{ background: {bg_base}; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {border_strong}; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: {primary}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QMenuBar {{ background-color: {bg_surface}; color: {text_primary}; border-bottom: 1px solid {border}; }}
QMenuBar::item:selected {{ background-color: {bg_hover}; }}
QMenu {{ background-color: {bg_surface}; color: {text_primary}; border: 1px solid {border}; }}
QMenu::item:selected {{ background-color: {primary}; color: {text_on_accent}; }}
QStatusBar {{ background-color: {bg_surface}; color: {text_tertiary}; border-top: 1px solid {border}; }}
QToolTip {{
    background-color: {bg_surface};
    color: {text_primary};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 4px;
}}
QProgressBar {{
    background-color: {bg_subtle};
    border: 1px solid {border};
    border-radius: 6px;
    text-align: center;
    color: {text_primary};
}}
QProgressBar::chunk {{ background-color: {primary}; border-radius: 6px; }}
QToolButton {{
    background-color: transparent;
    color: {text_primary};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px;
}}
QToolButton:hover {{ background-color: {bg_hover}; border-color: {border}; }}
QToolButton:pressed {{ background-color: {bg_selected}; }}
QDialogButtonBox QPushButton {{ min-width: 80px; }}
QLineEdit::placeholder, QTextEdit::placeholder {{ color: {text_disabled}; }}
QAbstractItemView {{ outline: none; }}
QTreeWidget::item {{ padding: 4px; border-radius: 4px; }}
QTreeWidget::item:hover {{ background-color: {bg_hover}; }}
QTreeWidget::item:selected {{ background-color: {primary}; color: {text_on_accent}; }}
QSplitter::handle {{ background-color: {border}; }}
QFrame[frameShape="4"] {{ color: {border}; }}
"""


class ThemeManager:
    """主题管理器（线程安全单例）。"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._current = "light"
                    cls._instance._app = None
        return cls._instance

    @property
    def current(self) -> str:
        return self._current

    @property
    def palette(self) -> Dict[str, str]:
        return PALETTES[self._current]

    def color(self, key: str, default: str = "") -> str:
        return self.palette.get(key, default)

    def qss(self) -> str:
        return GLOBAL_QSS.format(**self.palette)

    def apply(self, app=None, theme_name: str = None) -> str:
        """应用主题到 QApplication，返回归一化后的主题名。"""
        if app is not None:
            self._app = app
        if theme_name is not None:
            self._current = normalize(theme_name)
        if self._app is None:
            from PyQt5.QtWidgets import QApplication
            self._app = QApplication.instance()
        if self._app is not None:
            self._app.setStyleSheet(self.qss())
        self._sync_uistyles()
        return self._current

    def set_theme(self, theme_name: str) -> str:
        """切换主题并持久化到 config.json。"""
        name = self.apply(theme_name=theme_name)
        try:
            from models.config import config
            config.set("ui.theme", name)
        except Exception:
            pass
        return name

    def _sync_uistyles(self):
        """把当前色板同步到 UIStyles 类常量，使新生成的 f-string 样式跟随主题。"""
        try:
            from ui.styles import UIStyles
            p = self.palette
            mapping = {
                "PRIMARY": "primary", "PRIMARY_HOVER": "primary_hover", "PRIMARY_LIGHT": "primary_light",
                "SUCCESS": "success", "SUCCESS_HOVER": "success_hover", "SUCCESS_LIGHT": "success_light",
                "DANGER": "danger", "DANGER_HOVER": "danger_hover", "DANGER_LIGHT": "danger_light",
                "WARNING": "warning", "WARNING_HOVER": "warning_hover", "WARNING_LIGHT": "warning_light",
                "INFO": "info", "INFO_HOVER": "info_hover", "INFO_LIGHT": "info_light",
                "TEXT_PRIMARY": "text_primary", "TEXT_SECONDARY": "text_secondary",
                "TEXT_TERTIARY": "text_tertiary", "TEXT_DISABLED": "text_disabled",
                "TEXT_WHITE": "text_on_accent", "BORDER_LIGHT": "border", "BORDER_MEDIUM": "border_strong",
                "BG_WHITE": "bg_surface", "BG_GRAY_50": "bg_subtle", "BG_GRAY_100": "bg_hover",
                "BG_GRAY_200": "border", "CONTENT_BG": "bg_base",
                "SIDEBAR_BG": "sidebar_bg", "SIDEBAR_TEXT": "sidebar_text",
                "SIDEBAR_HOVER": "sidebar_hover", "SIDEBAR_SELECTED": "sidebar_selected",
            }
            for attr, key in mapping.items():
                if hasattr(UIStyles, attr):
                    setattr(UIStyles, attr, p[key])
        except Exception:
            pass


theme_manager = ThemeManager()
