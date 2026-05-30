# -*- coding: utf-8 -*-
"""收支管理系统 - 主入口| 基于 PyQt5 + SQLite/pymysql/Sybase"""
import sys
import os

# ========== 必须在导入任何GUI库之前设置 ==========
# 启用高 DPI 缩放支持
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
# 抑制Qt警告（某些版本支持）
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.*=false'

from PyQt5.QtCore import Qt
# 必须在创建 QApplication 之前设置高 DPI 属性
try:
    from PyQt5.QtWidgets import QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
except Exception:
    pass  # 如果已经创建则忽略

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Windows 特定设置：设置 AppUserModelID 以确保任务栏显示正确的图标
if sys.platform == 'win32':
    import ctypes
    # 设置应用程序的 AppUserModelID
    myappid = 'InExSystem.InEx_System.2.0'  # 任意字符串，建议格式：组织名.应用名.版本号
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import QRect

from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from models.db_backend import db_manager
from models.config import config
from utils.logger import log_manager  # 新增:导入日志管理器


def create_splash_screen():
    """QSplashScreen: 启动画面对象"""
    SPLASH_W, SPLASH_H = 600, 400
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "InEx_System.ico")

    # 创建背景画布
    pixmap = QPixmap(SPLASH_W, SPLASH_H)
    pixmap.fill(Qt.transparent)  # 透明背景

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 居中绘制图标（如果存在）
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        icon_size = 120
        icon_pixmap = icon.pixmap(icon_size, icon_size)
        icon_x = (SPLASH_W - icon_size) // 2
        icon_y = (SPLASH_H - icon_size) // 2 - 40
        painter.drawPixmap(icon_x, icon_y, icon_pixmap)

    # 标题文字
    painter.setPen(QColor("#7c8aff"))
    title_font = QFont("Microsoft YaHei", 26, QFont.Bold)
    painter.setFont(title_font)
    painter.drawText(QRect(0, icon_y + icon_size + 10 if os.path.exists(icon_path) else 140, SPLASH_W, 50), Qt.AlignCenter, "InEx System v2.0")

    # 副标题
    painter.setPen(QColor("#a0a8d0"))
    sub_font = QFont("Microsoft YaHei", 12)
    painter.setFont(sub_font)
    painter.drawText(QRect(0, SPLASH_H - 50, SPLASH_W, 30), Qt.AlignCenter, "个人收支管理系统 · 加载中...")

    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

    return splash


def main():
    """主函数"""
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("收支管理系统")
        app.setOrganizationName("InEx_System")
        app.setApplicationVersion("2.0")
        
        # 设置应用程序图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "InEx_System.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            log_manager.info(f"应用程序图标已加载: {icon_path}")
        else:
            log_manager.warning(f"应用程序图标文件不存在: {icon_path}")
        
        # 设置全局字体
        font = QFont("微软雅黑", 10)
        app.setFont(font)
        
        # 设置应用样式
        app.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)
        
        # 显示启动画面
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        # 模拟初始化
        QTimer.singleShot(800, lambda: None)  #  0.8秒
        # 显示登录对话框
        login_dialog = LoginDialog()
        # 连接登录成功信号
        login_dialog.login_success.connect(lambda account, password: log_manager.info(f"准备加载账套: {account}"))
        # 关闭启动画面
        splash.finish(login_dialog)
        
        log_manager.info("开始显示登录对话框...")
        result = login_dialog.exec_()
        log_manager.info(f"登录对话框返回值: {result}, Accepted={LoginDialog.Accepted}")
        
        if result == LoginDialog.Accepted:
            # 登录成功，获取账套号
            account = login_dialog.account_input.currentText().strip()
            log_manager.info(f"登录成功,准备创建主窗口,账套号: {account}")
            
            try:
                # 创建并显示主窗口
                log_manager.info("正在创建MainWindow...")
                main_window = MainWindow(account)
                log_manager.info("MainWindow创建成功")
                
                log_manager.info("正在显示主窗口...")
                main_window.show()
                main_window.raise_()  # 确保窗口在最前面
                main_window.activateWindow()  # 激活窗口
                log_manager.info("主窗口已显示")
                
                # 检查数据库连接状态
                if not db_manager.is_connected():
                    log_manager.info("使用演示模式")
                
                log_manager.info("进入事件循环...")
                sys.exit(app.exec_())
            except Exception as e:
                log_manager.error(f"主窗口创建或显示失败: {str(e)}", exc_info=True)
                import traceback
                traceback.print_exc()
                raise
        else:
            # 取消
            log_manager.info("用户取消登录")
            sys.exit(0)
            
    except Exception as e:
        log_manager.error(f"程序启动失败: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
