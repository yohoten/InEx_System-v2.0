# -*- coding: utf-8 -*-
"""
备份管理区域组件
负责自动备份配置、手动备份、备份历史查看等功能
"""

import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QLineEdit, QPushButton, QCheckBox,
                             QSpinBox, QMessageBox, QFileDialog, QFrame,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from models.config import config
from ui.styles import UIStyles


class BackupManagementSection(QWidget):
    """备份管理区域组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        
        # UI组件
        self.auto_backup_check = None
        self.backup_interval_spin = None
        self.backup_path_input = None
        self.backup_browse_btn = None
        
        self.initUI()
    
    def initUI(self):
        """初始化备份管理区域UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 自动备份分组
        backup_group = QGroupBox("💾 自动备份")
        backup_group.setStyleSheet(UIStyles.group_box_style())
        backup_layout = QVBoxLayout()
        backup_layout.setSpacing(10)
        
        # 启用自动备份
        self.auto_backup_check = QCheckBox("启用自动备份")
        self.auto_backup_check.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.auto_backup_check.stateChanged.connect(self.on_backup_changed)
        backup_layout.addWidget(self.auto_backup_check)
        
        # 备份间隔
        interval_frame = QFrame()
        interval_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 8px;")
        interval_layout = QHBoxLayout(interval_frame)
        interval_layout.setSpacing(8)
        
        interval_label = QLabel("⏰ 间隔:")
        interval_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        interval_layout.addWidget(interval_label)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 365)
        self.backup_interval_spin.setValue(7)
        self.backup_interval_spin.setSuffix(" 天")
        self.backup_interval_spin.setFixedHeight(32)
        self.backup_interval_spin.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.backup_interval_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 3px 8px;
                background-color: white;
            }
            QSpinBox:focus {
                border: 2px solid #667eea;
            }
        """)
        interval_layout.addWidget(self.backup_interval_spin)
        interval_layout.addStretch()
        backup_layout.addWidget(interval_frame)
        
        # 备份路径
        path_frame = QFrame()
        path_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 8px;")
        path_layout = QHBoxLayout(path_frame)
        path_layout.setSpacing(8)
        
        path_label = QLabel("📁 路径:")
        path_label.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        path_layout.addWidget(path_label)
        
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setPlaceholderText("./backup/")
        self.backup_path_input.setFixedHeight(32)
        self.backup_path_input.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.backup_path_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 3px 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        path_layout.addWidget(self.backup_path_input)
        
        self.backup_browse_btn = QPushButton("浏览")
        self.backup_browse_btn.setCursor(Qt.PointingHandCursor)
        self.backup_browse_btn.setFixedWidth(50)
        self.backup_browse_btn.setFixedHeight(32)
        self.backup_browse_btn.setFont(QFont(UIStyles.FONT_FAMILY, 9))
        self.backup_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton:pressed {
                background-color: #4a5ab5;
            }
        """)
        self.backup_browse_btn.clicked.connect(self.browse_backup_path)
        path_layout.addWidget(self.backup_browse_btn)
        backup_layout.addWidget(path_frame)
        
        # 立即备份按钮
        manual_backup_btn = QPushButton("📦 立即备份")
        manual_backup_btn.setCursor(Qt.PointingHandCursor)
        manual_backup_btn.setFixedHeight(35)
        manual_backup_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        manual_backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        manual_backup_btn.clicked.connect(self.manual_backup)
        backup_layout.addWidget(manual_backup_btn)
        
        # 查看备份历史按钮
        view_history_btn = QPushButton("📋 备份历史")
        view_history_btn.setCursor(Qt.PointingHandCursor)
        view_history_btn.setFixedHeight(35)
        view_history_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        view_history_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #6d28d9;
            }
        """)
        view_history_btn.clicked.connect(self.view_backup_history)
        backup_layout.addWidget(view_history_btn)
        
        backup_layout.addStretch()
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        self.setLayout(layout)
    
    def on_backup_changed(self, state):
        """自动备份开关变化"""
        enabled = state == Qt.Checked
        self.backup_interval_spin.setEnabled(enabled)
        self.backup_path_input.setEnabled(enabled)
        self.backup_browse_btn.setEnabled(enabled)
        
        if hasattr(self.parent_page, 'log_text'):
            self.parent_page.log_text.append(f"[INFO] 自动备份：{'启用' if enabled else '禁用'}")
    
    def browse_backup_path(self):
        """浏览备份路径"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择备份目录",
            "./backup/"
        )
        
        if dir_path:
            self.backup_path_input.setText(dir_path)
            if hasattr(self.parent_page, 'log_text'):
                self.parent_page.log_text.append(f"[INFO] 选择备份路径：{dir_path}")
    
    def manual_backup(self):
        """手动执行数据库备份"""
        if hasattr(self.parent_page, 'manual_backup'):
            self.parent_page.manual_backup()
    
    def view_backup_history(self):
        """查看备份历史记录"""
        if hasattr(self.parent_page, 'view_backup_history'):
            self.parent_page.view_backup_history()
    
    def is_auto_backup_enabled(self):
        """获取自动备份是否启用"""
        return self.auto_backup_check.isChecked()
    
    def get_backup_interval(self):
        """获取备份间隔（天）"""
        return self.backup_interval_spin.value()
    
    def get_backup_path(self):
        """获取备份路径"""
        return self.backup_path_input.text() or './backup/'
    
    def load_config(self, config_data):
        """加载备份配置"""
        auto_backup = config_data.get('auto_backup', False)
        self.auto_backup_check.setChecked(auto_backup)
        self.backup_interval_spin.setValue(config_data.get('backup_interval', 7))
        self.backup_path_input.setText(config_data.get('backup_path', './backup/'))
        
        # 更新UI状态
        self.on_backup_changed(Qt.Checked if auto_backup else Qt.Unchecked)
