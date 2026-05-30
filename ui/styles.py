# -*- coding: utf-8 -*-
"""
UI样式集中化管理模块
提供统一的样式常量、模板和工厂方法,减少代码冗余
"""


class UIStyles:
    """UI样式常量和管理类"""
    
    # ==================== 主题色系 ====================
    # 主色调
    PRIMARY = "#667eea"
    PRIMARY_HOVER = "#5568d3"
    PRIMARY_LIGHT = "#f0f3ff"
    
    # 成功色
    SUCCESS = "#10b981"
    SUCCESS_HOVER = "#059669"
    SUCCESS_LIGHT = "#ecfdf5"
    
    # 危险/错误色
    DANGER = "#ef4444"
    DANGER_HOVER = "#dc2626"
    DANGER_LIGHT = "#fef2f2"
    
    # 警告色
    WARNING = "#f59e0b"
    WARNING_HOVER = "#d97706"
    WARNING_LIGHT = "#fffbeb"
    
    # 信息色
    INFO = "#3b82f6"
    INFO_HOVER = "#2563eb"
    INFO_LIGHT = "#eff6ff"
    
    # 中性色
    TEXT_PRIMARY = "#1f2937"
    TEXT_SECONDARY = "#4b5563"
    TEXT_TERTIARY = "#6b7280"
    TEXT_DISABLED = "#9ca3af"
    TEXT_WHITE = "#ffffff"
    
    BORDER_LIGHT = "#e5e7eb"
    BORDER_MEDIUM = "#d1d5db"
    BG_WHITE = "#ffffff"
    BG_GRAY_50 = "#f9fafb"
    BG_GRAY_100 = "#f3f4f6"
    BG_GRAY_200 = "#e5e7eb"
    CONTENT_BG = "#F5F5F7"

    # 扩展色
    ACCENT_PURPLE = "#764ba2"
    ACCENT_PINK = "#ec4899"

    # 侧边栏色系
    SIDEBAR_BG = "#2c3e50"
    SIDEBAR_ITEM_BORDER = "#34495e"
    SIDEBAR_HOVER = "#34495e"
    SIDEBAR_SELECTED = "#1abc9c"
    SIDEBAR_SELECTED_DARKER = "#16a085"
    SIDEBAR_TEXT = "#ecf0f1"
    
    # ==================== 字体规范 ====================
    FONT_FAMILY = "微软雅黑"
    FONT_SIZE_XS = 8
    FONT_SIZE_SMALL = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_MEDIUM = 11
    FONT_SIZE_LARGE = 12
    FONT_SIZE_XLARGE = 14
    FONT_SIZE_XXLARGE = 16
    FONT_SIZE_TITLE = 18
    FONT_SIZE_HERO = 20
    
    # ==================== 尺寸规范 ====================
    BORDER_RADIUS_SMALL = 6
    BORDER_RADIUS_MEDIUM = 8
    BORDER_RADIUS_LARGE = 10
    BORDER_RADIUS_XLARGE = 12
    
    PADDING_SMALL = 8
    PADDING_MEDIUM = 12
    PADDING_LARGE = 15
    PADDING_XLARGE = 20
    
    PAGE_PADDING = 24

    SPACING_SMALL = 8
    SPACING_MEDIUM = 10
    SPACING_LARGE = 15
    SPACING_XLARGE = 20
    
    # ==================== 样式模板 ====================
    
    # 卡片样式模板
    CARD_TEMPLATE = """
        QFrame {{
            background-color: {bg_color};
            border-radius: {radius}px;
            border-left: 4px solid {color};
        }}
        QFrame:hover {{
            background-color: white;
            border-left: 4px solid {color};
        }}
    """
    
    # 按钮基础样式
    BUTTON_BASE = """
        QPushButton {{
            background-color: {bg_color};
            color: {text_color};
            border: none;
            border-radius: {radius}px;
            padding: {padding_v}px {padding_h}px;
            font-family: '{font}';
            font-size: {font_size}px;
            font-weight: {font_weight};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
    """
    
    # 现代按钮样式(带边框)
    BUTTON_MODERN = """
        QPushButton {{
            background-color: white;
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: {radius}px;
            padding: {padding_v}px {padding_h}px;
            font-family: '{font}';
            font-size: {font_size}px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            border: 2px solid {hover_border};
            color: {hover_text};
        }}
        QPushButton:checked {{
            background-color: {checked_bg};
            color: white;
            border: 2px solid {checked_border};
            font-weight: bold;
        }}
    """
    
    # 标签页样式
    TAB_WIDGET = """
        QTabWidget::pane {{
            border: none;
            background-color: {bg_color};
            border-radius: {radius}px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {tab_bg};
            color: {tab_text};
            padding: {padding_v}px {padding_h}px;
            margin-right: {spacing}px;
            border-top-left-radius: {radius}px;
            border-top-right-radius: {radius}px;
            font-family: '{font}';
            font-size: {font_size}px;
            font-weight: {font_weight};
            min-width: {min_width}px;
        }}
        QTabBar::tab:selected {{
            background-color: white;
            color: {selected_color};
            border-bottom: 2px solid {selected_color};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {hover_color};
        }}
    """
    
    # 表格样式
    TABLE_BASE = """
        QTableWidget {{
            background-color: white;
            border: 1px solid {border_color};
            border-radius: {radius}px;
            gridline-color: {grid_color};
            selection-background-color: {selection_bg};
            selection-color: {selection_text};
        }}
        QTableWidget::item {{
            padding: {padding}px;
        }}
        QHeaderView::section {{
            background-color: {header_bg};
            color: {header_text};
            padding: {padding}px;
            border: none;
            border-bottom: 2px solid {border_color};
            font-family: '{font}';
            font-size: {font_size}px;
            font-weight: bold;
        }}
    """
    
    # 滚动条样式
    SCROLLBAR_VERTICAL = """
        QScrollBar:vertical {{
            border: none;
            background: {bg_color};
            width: {width}px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle_color};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {hover_color};
        }}
    """
    
    # 输入框样式
    INPUT_BASE = """
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
            background-color: white;
            border: 2px solid {border_color};
            border-radius: {radius}px;
            padding: {padding_v}px {padding_h}px;
            font-family: '{font}';
            font-size: {font_size}px;
            color: {text_color};
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {focus_color};
        }}
    """
    
    # 进度条背景
    PROGRESS_BAR_BG = """
        QFrame {{
            background-color: {bg_color};
            border-radius: {radius}px;
        }}
    """
    
    # 进度条填充
    PROGRESS_BAR_FILL = """
        QFrame {{
            background-color: {fill_color};
            border-radius: {radius}px;
        }}
    """
    
    # 状态标签
    STATUS_BADGE = """
        QLabel {{
            background-color: {bg_color};
            color: {text_color};
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
        }}
    """
    
    # 信息提示框
    INFO_BOX = """
        QLabel {{
            color: {text_color};
            background-color: {bg_color};
            padding: {padding}px;
            border-radius: {radius}px;
            border-left: 3px solid {border_color};
        }}
    """
    
    # ==================== 工厂方法 ====================
    
    @staticmethod
    def card_style(color, bg_color, radius=BORDER_RADIUS_XLARGE):
        """生成卡片样式"""
        return UIStyles.CARD_TEMPLATE.format(
            color=color,
            bg_color=bg_color,
            radius=radius
        )
    
    @staticmethod
    def primary_button(font_size=FONT_SIZE_NORMAL, padding_v=PADDING_SMALL, padding_h=PADDING_MEDIUM, font_weight="normal"):
        """生成主色调按钮样式"""
        return UIStyles.BUTTON_BASE.format(
            bg_color=UIStyles.PRIMARY,
            text_color="white",
            hover_color=UIStyles.PRIMARY_HOVER,
            pressed_color=UIStyles.PRIMARY,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=padding_v,
            padding_h=padding_h,
            font=UIStyles.FONT_FAMILY,
            font_size=font_size,
            font_weight=font_weight
        )
    
    @staticmethod
    def success_button(font_size=FONT_SIZE_NORMAL, padding_v=PADDING_SMALL, padding_h=PADDING_MEDIUM, font_weight="normal"):
        """生成成功色按钮样式"""
        return UIStyles.BUTTON_BASE.format(
            bg_color=UIStyles.SUCCESS,
            text_color="white",
            hover_color=UIStyles.SUCCESS_HOVER,
            pressed_color=UIStyles.SUCCESS,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=padding_v,
            padding_h=padding_h,
            font=UIStyles.FONT_FAMILY,
            font_size=font_size,
            font_weight=font_weight
        )
    
    @staticmethod
    def danger_button(font_size=FONT_SIZE_NORMAL):
        """生成危险色按钮样式"""
        return UIStyles.BUTTON_BASE.format(
            bg_color=UIStyles.DANGER,
            text_color="white",
            hover_color=UIStyles.DANGER_HOVER,
            pressed_color=UIStyles.DANGER,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            font=UIStyles.FONT_FAMILY,
            font_size=font_size,
            font_weight="normal"
        )
    
    @staticmethod
    def secondary_button(font_size=FONT_SIZE_NORMAL):
        """生成次要按钮样式（灰色）"""
        return UIStyles.BUTTON_BASE.format(
            bg_color=UIStyles.BG_GRAY_200,
            text_color=UIStyles.TEXT_PRIMARY,
            hover_color=UIStyles.BORDER_MEDIUM,
            pressed_color=UIStyles.BG_GRAY_200,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            font=UIStyles.FONT_FAMILY,
            font_size=font_size,
            font_weight="normal"
        )
    
    @staticmethod
    def default_button(font_size=FONT_SIZE_NORMAL):
        """生成默认按钮样式（白色背景带边框）"""
        return f"""
            QPushButton {{
                background-color: white;
                color: {UIStyles.TEXT_PRIMARY};
                border: 2px solid {UIStyles.BORDER_MEDIUM};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: {UIStyles.PADDING_SMALL}px {UIStyles.PADDING_MEDIUM}px;
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.BG_GRAY_50};
                border: 2px solid {UIStyles.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {UIStyles.BG_GRAY_100};
            }}
        """
    
    @staticmethod
    def tab_style_modern():
        """现代标签页样式（用于个人中心等页面）"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                background-color: {UIStyles.BG_WHITE};
            }}
            QTabBar::tab {{
                background-color: {UIStyles.BG_GRAY_50};
                color: {UIStyles.TEXT_TERTIARY};
                padding: {UIStyles.PADDING_MEDIUM}px {UIStyles.PADDING_XLARGE}px;
                margin-right: 2px;
                border-top-left-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                border-top-right-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                font-weight: bold;
                font-size: {UIStyles.FONT_SIZE_NORMAL}px;
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {UIStyles.BG_WHITE};
                color: {UIStyles.TEXT_PRIMARY};
                border-bottom: 2px solid {UIStyles.PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {UIStyles.BG_GRAY_100};
            }}
        """
    
    @staticmethod
    def group_box_style():
        """分组框样式"""
        return f"""
            QGroupBox {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {UIStyles.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def gradient_card(colors):
        """渐变背景卡片
        
        Args:
            colors: 颜色列表，如 ['#667eea', '#764ba2']
        """
        if len(colors) == 2:
            return f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 {colors[0]}, stop:1 {colors[1]});
                    border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
                    padding: {UIStyles.PADDING_XLARGE}px;
                }}
            """
        elif len(colors) == 1:
            return f"""
                QFrame {{
                    background-color: {colors[0]};
                    border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
                    padding: {UIStyles.PADDING_XLARGE}px;
                }}
            """
        return ""
    
    @staticmethod
    def search_frame_style():
        """搜索区域框架样式"""
        return f"""
            QFrame {{
                background-color: {UIStyles.BG_GRAY_50};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                padding: {UIStyles.PADDING_SMALL}px;
            }}
        """
    
    @staticmethod
    def modern_table_style():
        """现代化表格样式"""
        return f"""
            QTableWidget {{
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                gridline-color: {UIStyles.BG_GRAY_100};
            }}
            QHeaderView::section {{
                background-color: {UIStyles.BG_GRAY_50};
                padding: {UIStyles.PADDING_MEDIUM}px;
                border: none;
                border-bottom: 2px solid {UIStyles.BORDER_LIGHT};
                font-weight: bold;
                color: {UIStyles.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: {UIStyles.PADDING_SMALL}px;
            }}
            QTableWidget::item:selected {{
                background-color: {UIStyles.PRIMARY_LIGHT};
                color: {UIStyles.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def metric_label_style(color=None):
        """指标标签样式
        
        Args:
            color: 文字颜色，默认使用主题色
        """
        if color is None:
            color = UIStyles.PRIMARY
        return f"""
            QLabel {{
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: {UIStyles.FONT_SIZE_MEDIUM}px;
                color: {color};
            }}
        """
    
    @staticmethod
    def modern_checkable_button(text_color="#6b7280", border_color="#e5e7eb", 
                                  checked_bg=None, is_default=False):
        """生成现代可勾选按钮样式"""
        if checked_bg is None:
            checked_bg = UIStyles.SUCCESS if is_default else UIStyles.PRIMARY
        
        checked_border = checked_bg
        hover_bg = "#f9fafb"
        hover_border = UIStyles.PRIMARY_HOVER if not is_default else UIStyles.SUCCESS_HOVER
        hover_text = hover_border
        
        return UIStyles.BUTTON_MODERN.format(
            text_color=text_color,
            border_color=border_color,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            font=UIStyles.FONT_FAMILY,
            font_size=UIStyles.FONT_SIZE_NORMAL,
            hover_bg=hover_bg,
            hover_border=hover_border,
            hover_text=hover_text,
            checked_bg=checked_bg,
            checked_border=checked_border
        )
    
    @staticmethod
    def tab_widget_style(bg_color=None, selected_color=None, 
                         tab_bg=None, tab_text=None):
        """生成标签页样式"""
        if bg_color is None:
            bg_color = UIStyles.BG_GRAY_50
        if selected_color is None:
            selected_color = UIStyles.PRIMARY
        if tab_bg is None:
            tab_bg = UIStyles.BORDER_LIGHT
        if tab_text is None:
            tab_text = UIStyles.TEXT_TERTIARY
        
        return UIStyles.TAB_WIDGET.format(
            bg_color=bg_color,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            tab_bg=tab_bg,
            tab_text=tab_text,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            spacing=UIStyles.SPACING_SMALL,
            font=UIStyles.FONT_FAMILY,
            font_size=UIStyles.FONT_SIZE_NORMAL,
            font_weight="normal",
            min_width=80,
            selected_color=selected_color,
            hover_color=UIStyles.BG_GRAY_100
        )
    
    @staticmethod
    def table_style(border_color=None, header_bg=None):
        """生成表格样式"""
        if border_color is None:
            border_color = UIStyles.BORDER_LIGHT
        if header_bg is None:
            header_bg = UIStyles.BG_GRAY_100
        
        return UIStyles.TABLE_BASE.format(
            border_color=border_color,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            grid_color=border_color,
            selection_bg=UIStyles.PRIMARY_LIGHT,
            selection_text=UIStyles.TEXT_PRIMARY,
            padding=UIStyles.PADDING_SMALL,
            header_bg=header_bg,
            header_text=UIStyles.TEXT_PRIMARY,
            font=UIStyles.FONT_FAMILY,
            font_size=UIStyles.FONT_SIZE_NORMAL
        )
    
    @staticmethod
    def scrollbar_style(bg_color=None, handle_color=None, 
                        hover_color=None, width=8):
        """生成滚动条样式"""
        if bg_color is None:
            bg_color = UIStyles.BG_GRAY_100
        if handle_color is None:
            handle_color = UIStyles.BORDER_MEDIUM
        if hover_color is None:
            hover_color = UIStyles.TEXT_TERTIARY
        
        return UIStyles.SCROLLBAR_VERTICAL.format(
            bg_color=bg_color,
            handle_color=handle_color,
            hover_color=hover_color,
            width=width
        )
    
    @staticmethod
    def input_style(border_color=None, focus_color=None):
        """生成输入框样式"""
        if border_color is None:
            border_color = UIStyles.BORDER_MEDIUM
        if focus_color is None:
            focus_color = UIStyles.PRIMARY
        
        return UIStyles.INPUT_BASE.format(
            border_color=border_color,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            font=UIStyles.FONT_FAMILY,
            font_size=UIStyles.FONT_SIZE_NORMAL,
            text_color=UIStyles.TEXT_PRIMARY,
            focus_color=focus_color
        )
    
    @staticmethod
    def warning_button(font_size=FONT_SIZE_NORMAL):
        """生成警告色按钮样式"""
        return UIStyles.BUTTON_BASE.format(
            bg_color=UIStyles.WARNING,
            text_color="white",
            hover_color=UIStyles.WARNING_HOVER,
            pressed_color=UIStyles.WARNING,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            font=UIStyles.FONT_FAMILY,
            font_size=font_size,
            font_weight="normal"
        )

    @staticmethod
    def info_button(font_size=FONT_SIZE_NORMAL):
        """生成信息色按钮样式"""
        return UIStyles.BUTTON_BASE.format(
            bg_color=UIStyles.INFO,
            text_color="white",
            hover_color=UIStyles.INFO_HOVER,
            pressed_color=UIStyles.INFO,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            padding_v=UIStyles.PADDING_SMALL,
            padding_h=UIStyles.PADDING_MEDIUM,
            font=UIStyles.FONT_FAMILY,
            font_size=font_size,
            font_weight="normal"
        )

    @staticmethod
    def page_title_style():
        """统一的页面标题样式"""
        return f"""
            QLabel {{
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: {UIStyles.FONT_SIZE_TITLE}px;
                font-weight: bold;
                color: {UIStyles.TEXT_PRIMARY};
                padding: 0px 0px {UIStyles.PADDING_SMALL}px 0px;
            }}
        """

    @staticmethod
    def filter_frame_style():
        """筛选/搜索区域框架样式"""
        return f"""
            QFrame {{
                background-color: {UIStyles.BG_GRAY_50};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: {UIStyles.PADDING_MEDIUM}px;
            }}
        """

    @staticmethod
    def icon_button_style(color=None, size=32):
        """小图标按钮样式 (无边框, hover变色)"""
        if color is None:
            color = UIStyles.TEXT_TERTIARY
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                border: none;
                border-radius: {UIStyles.BORDER_RADIUS_SMALL}px;
                font-size: {UIStyles.FONT_SIZE_LARGE}px;
                min-width: {size}px;
                min-height: {size}px;
            }}
            QPushButton:hover {{
                background-color: {UIStyles.BG_GRAY_100};
                color: {UIStyles.PRIMARY};
            }}
        """

    @staticmethod
    def combo_box_style():
        """统一的下拉框样式"""
        return f"""
            QComboBox {{
                background-color: white;
                border: 2px solid {UIStyles.BORDER_MEDIUM};
                border-radius: {UIStyles.BORDER_RADIUS_MEDIUM}px;
                padding: {UIStyles.PADDING_SMALL}px {UIStyles.PADDING_MEDIUM}px;
                font-family: '{UIStyles.FONT_FAMILY}';
                font-size: {UIStyles.FONT_SIZE_NORMAL}px;
                color: {UIStyles.TEXT_PRIMARY};
                min-width: 100px;
            }}
            QComboBox:hover {{
                border: 2px solid {UIStyles.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """

    @staticmethod
    def card_with_shadow():
        """白卡带阴影样式"""
        return f"""
            QFrame {{
                background-color: {UIStyles.BG_WHITE};
                border: 1px solid {UIStyles.BORDER_LIGHT};
                border-radius: {UIStyles.BORDER_RADIUS_XLARGE}px;
            }}
        """

    @staticmethod
    def white_background():
        """白色背景样式"""
        return f"""
            QFrame {{
                background-color: {UIStyles.BG_WHITE};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """
    
    @staticmethod
    def gray_background():
        """灰色背景样式"""
        return f"""
            QFrame {{
                background-color: {UIStyles.BG_GRAY_50};
                border-radius: {UIStyles.BORDER_RADIUS_LARGE}px;
            }}
        """
    
    @staticmethod
    def info_box(bg_color=None, border_color=None, text_color=None):
        """生成信息提示框样式"""
        if bg_color is None:
            bg_color = UIStyles.INFO_LIGHT
        if border_color is None:
            border_color = UIStyles.INFO
        if text_color is None:
            text_color = UIStyles.TEXT_PRIMARY
        
        return UIStyles.INFO_BOX.format(
            text_color=text_color,
            bg_color=bg_color,
            padding=UIStyles.PADDING_MEDIUM,
            radius=UIStyles.BORDER_RADIUS_MEDIUM,
            border_color=border_color
        )
    
    @staticmethod
    def warning_box(bg_color=None, border_color=None):
        """生成警告框样式"""
        if bg_color is None:
            bg_color = UIStyles.WARNING_LIGHT
        if border_color is None:
            border_color = UIStyles.WARNING
        return UIStyles.info_box(bg_color, border_color, UIStyles.TEXT_PRIMARY)
    
    @staticmethod
    def danger_box(bg_color=None, border_color=None):
        """生成危险框样式"""
        if bg_color is None:
            bg_color = UIStyles.DANGER_LIGHT
        if border_color is None:
            border_color = UIStyles.DANGER
        return UIStyles.info_box(bg_color, border_color, UIStyles.TEXT_PRIMARY)
    
    @staticmethod
    def success_box(bg_color=None, border_color=None):
        """生成成功框样式"""
        if bg_color is None:
            bg_color = UIStyles.SUCCESS_LIGHT
        if border_color is None:
            border_color = UIStyles.SUCCESS
        return UIStyles.info_box(bg_color, border_color, UIStyles.TEXT_PRIMARY)

    # ==================== 工具方法 ====================

    @staticmethod
    def darken_color(hex_color, amount=10):
        """将十六进制颜色变暗指定数值"""
        hex_color = hex_color.lstrip('#')
        r = max(0, int(hex_color[0:2], 16) - amount)
        g = max(0, int(hex_color[2:4], 16) - amount)
        b = max(0, int(hex_color[4:6], 16) - amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def btn_style(color):
        """生成统一按钮样式（14px bold, hover/pressed 自动暗化）"""
        hover = UIStyles.darken_color(color, 15)
        pressed = UIStyles.darken_color(color, 30)
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
        """
