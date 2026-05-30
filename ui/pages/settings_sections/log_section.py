# -*- coding: utf-8 -*-
"""
日志配置区域组件
负责日志级别设置、日志显示、加载真实日志等功能
"""

import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QComboBox, QPushButton, QTextEdit, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.styles import UIStyles


class LogConfigurationSection(QWidget):
    """日志配置区域组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        
        # UI组件
        self.log_level_combo = None
        self.log_text = None
        
        self.initUI()
    
    def initUI(self):
        """初始化日志配置区域UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 日志配置分组
        log_group = QGroupBox("📝 日志配置")
        log_group.setStyleSheet(UIStyles.group_box_style())
        log_layout = QVBoxLayout()
        log_layout.setSpacing(12)
        
        # 日志级别
        level_frame = QFrame()
        level_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 10px;")
        level_layout = QHBoxLayout(level_frame)
        level_layout.setSpacing(10)
        
        level_label = QLabel("📊 日志级别:")
        level_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        level_layout.addWidget(level_label)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setFixedHeight(35)
        self.log_level_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.log_level_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
            QComboBox:focus {
                border: 2px solid #667eea;
            }
        """)
        level_layout.addWidget(self.log_level_combo)
        level_layout.addStretch()
        log_layout.addWidget(level_frame)
        
        # 日志查看区域标题
        log_view_title = QLabel("📋 最近日志:")
        log_view_title.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        log_view_title.setStyleSheet("color: #374151;")
        log_layout.addWidget(log_view_title)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        self.log_text.setMinimumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 10px;
                color: #374151;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # 清空日志按钮
        clear_log_btn = QPushButton("🗑️ 清空日志")
        clear_log_btn.setCursor(Qt.PointingHandCursor)
        clear_log_btn.setFixedHeight(35)
        clear_log_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
        """)
        clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_btn)
        
        # 加载真实日志按钮
        load_real_logs_btn = QPushButton("📄 加载真实日志")
        load_real_logs_btn.setCursor(Qt.PointingHandCursor)
        load_real_logs_btn.setFixedHeight(35)
        load_real_logs_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        load_real_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        load_real_logs_btn.clicked.connect(self.load_real_logs)
        log_layout.addWidget(load_real_logs_btn)

        # 查看审计日志按钮
        audit_btn = QPushButton("📋 查看审计日志")
        audit_btn.setCursor(Qt.PointingHandCursor)
        audit_btn.setFixedHeight(35)
        audit_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        audit_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
        """)
        audit_btn.clicked.connect(self.show_audit_log)
        log_layout.addWidget(audit_btn)

        log_layout.addStretch()
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_text.append("[INFO] 日志已清空")
        if hasattr(self.parent_page, 'log_text') and self.parent_page.log_text != self.log_text:
            self.parent_page.log_text.append("[INFO] 日志已清空")
    
    def load_real_logs(self):
        """加载真实日志文件内容"""
        try:
            # 获取日志目录
            log_dir = "logs"
            if not os.path.exists(log_dir):
                self.log_text.append("[WARN] 日志目录不存在")
                return
            
            # 获取今天的日志文件
            today = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(log_dir, f"InEx_system_{today}.log")
            
            if not os.path.exists(log_file):
                self.log_text.append(f"[INFO] 今日日志文件不存在: {log_file}")
                self.log_text.append("[INFO] 尝试查找最近的日志文件...")
                
                # 查找最近的日志文件
                log_files = [f for f in os.listdir(log_dir) if f.startswith("InEx_system_") and f.endswith(".log")]
                if log_files:
                    log_files.sort(reverse=True)
                    log_file = os.path.join(log_dir, log_files[0])
                    self.log_text.append(f"[INFO] 找到最近日志: {log_files[0]}")
                else:
                    self.log_text.append("[WARN] 未找到任何日志文件")
                    return
            
            # 读取日志文件
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 显示最后100行
            display_lines = lines[-100:] if len(lines) > 100 else lines
            
            self.log_text.clear()
            self.log_text.append(f"[INFO] ========== 加载日志文件: {os.path.basename(log_file)} ==========")
            self.log_text.append(f"[INFO] 共 {len(lines)} 条记录，显示最后 {len(display_lines)} 条\n")
            
            for line in display_lines:
                self.log_text.append(line.rstrip())
            
            self.log_text.append(f"\n[INFO] ========== 日志加载完成 ==========")
            
        except Exception as e:
            self.log_text.append(f"[ERROR] 加载日志失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_log_level(self):
        """获取当前日志级别"""
        return self.log_level_combo.currentText()
    
    def set_log_level(self, level):
        """设置日志级别"""
        index = self.log_level_combo.findText(level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)

    def show_audit_log(self):
        """显示审计日志对话框"""
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QDialogButtonBox, QHeaderView, QDialog
        from models.db_backend import db_manager

        if not db_manager.is_connected():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "数据库未连接，无法查看审计日志")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("操作审计日志")
        dialog.setFixedSize(700, 450)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("📋 最近操作记录（100条）")
        title.setFont(QFont(UIStyles.FONT_FAMILY, 14, QFont.Bold))
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["时间", "账号", "操作", "目标", "详情"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)

        try:
            backend = db_manager.get_backend()
            backend.execute(
                "SELECT account, action, target, detail, created_at FROM sys_audit_log "
                "ORDER BY created_at DESC LIMIT 100"
            )
            rows = backend.fetchall()
            table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                account, action, target, detail, created_at = row
                table.setItem(i, 0, QTableWidgetItem(str(created_at) if created_at else ""))
                table.setItem(i, 1, QTableWidgetItem(str(account)))
                table.setItem(i, 2, QTableWidgetItem(str(action)))
                table.setItem(i, 3, QTableWidgetItem(str(target)))
                table.setItem(i, 4, QTableWidgetItem(str(detail) if detail else ""))
        except Exception as e:
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem(f"查询失败: {e}"))

        layout.addWidget(table)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec_()
    
    def append_log(self, message):
        """追加日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
