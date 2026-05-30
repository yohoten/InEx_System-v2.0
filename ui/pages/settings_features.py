# -*- coding: utf-8 -*-
"""
系统设置：真实日志显示、备份历史记录、设置导入/导出
"""

import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (QMessageBox, QFileDialog, QDialog, QVBoxLayout, 
                             QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from models.config import config


class SettingsFeaturesMixin:
    """系统设置功能混入类"""
    
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
    
    def export_settings(self):
        """导出系统设置到JSON文件"""
        try:
            # 获取保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出系统设置",
                f"settings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json)"
            )
            
            if not file_path:
                return
            
            # 收集所有配置
            db_config = config.get_database_config()
            log_level = config.get_log_setting('level', 'INFO')
            ui_font_size = config.get_ui_setting('font_size', 11)
            
            settings_data = {
                "export_time": datetime.now().isoformat(),
                "version": "2.0",
                "database": {
                    "type": db_config.get('type', 'SQLite'),
                    "path": db_config.get('path', ''),
                    "auto_backup": db_config.get('auto_backup', False),
                    "backup_interval": db_config.get('backup_interval', 7),
                    "backup_path": db_config.get('backup_path', '')
                },
                "log": {
                    "level": log_level
                },
                "ui": {
                    "font_size": ui_font_size
                }
            }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(
                self,
                "导出成功",
                f"✅ 系统设置已成功导出到:\n{file_path}"
            )
            
            self.log_text.append(f"[INFO] 设置已导出: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"❌ 导出设置失败:\n{str(e)}")
            self.log_text.append(f"[ERROR] 导出设置失败: {str(e)}")
    
    def import_settings(self):
        """从JSON文件导入系统设置"""
        try:
            # 获取文件路径
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "导入系统设置",
                "",
                "JSON Files (*.json)"
            )
            
            if not file_path:
                return
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            
            # 确认导入
            reply = QMessageBox.question(
                self,
                "确认导入",
                f"⚠️ 确定要导入以下设置吗？\n\n"
                f"导出时间: {settings_data.get('export_time', '未知')}\n"
                f"版本: {settings_data.get('version', '未知')}\n\n"
                f"当前设置将被覆盖！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # 应用设置
            if 'database' in settings_data:
                db_config = settings_data['database']
                config.set_database_config(
                    db_config.get('type', 'SQLite'),
                    path=db_config.get('path', ''),
                    auto_backup=db_config.get('auto_backup', False),
                    backup_interval=db_config.get('backup_interval', 7),
                    backup_path=db_config.get('backup_path', '')
                )
            
            if 'log' in settings_data:
                config.set_log_setting('level', settings_data['log'].get('level', 'INFO'))
            
            if 'ui' in settings_data:
                ui_config = settings_data['ui']
                config.set_ui_setting('font_size', ui_config.get('font_size', 11))
            
            QMessageBox.information(
                self,
                "导入成功",
                f"✅ 系统设置已成功导入\n\n请重启应用以使更改生效"
            )
            
            self.log_text.append(f"[INFO] 设置已从 {file_path} 导入")
            
            # 重新加载设置显示
            self.load_settings()
            
        except json.JSONDecodeError:
            QMessageBox.critical(self, "导入失败", "❌ 文件格式错误，不是有效的JSON文件")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"❌ 导入设置失败:\n{str(e)}")
            self.log_text.append(f"[ERROR] 导入设置失败: {str(e)}")
    
    def view_backup_history(self):
        """查看备份历史记录"""
        try:
            # 获取备份目录
            db_config = config.get_database_config()
            backup_path = db_config.get('backup_path', 'data/backups')
            if not os.path.exists(backup_path):
                QMessageBox.information(self, "提示", f"备份目录不存在:\n{backup_path}")
                return
            
            # 获取备份文件列表
            backup_files = []
            for filename in os.listdir(backup_path):
                if filename.endswith('.db') or filename.endswith('.sqlite'):
                    filepath = os.path.join(backup_path, filename)
                    stat = os.stat(filepath)
                    backup_files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            if not backup_files:
                QMessageBox.information(self, "提示", "暂无备份记录")
                return
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            
            # 创建对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("📦 备份历史记录")
            dialog.setFixedSize(800, 500)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # 标题
            title_label = QLabel(f"📦 备份历史记录 (共 {len(backup_files)} 个)")
            title_label.setFont(QFont(UIStyles.FONT_FAMILY, 14, QFont.Bold))
            layout.addWidget(title_label)
            
            # 表格
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["文件名", "大小", "备份时间", "操作"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setAlternatingRowColors(True)
            
            table.setRowCount(len(backup_files))
            for row, backup in enumerate(backup_files):
                # 文件名
                filename_item = QTableWidgetItem(backup['filename'])
                table.setItem(row, 0, filename_item)
                
                # 大小
                size_mb = backup['size'] / (1024 * 1024)
                size_item = QTableWidgetItem(f"{size_mb:.2f} MB")
                size_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 1, size_item)
                
                # 时间
                time_str = backup['modified'].strftime('%Y-%m-%d %H:%M:%S')
                time_item = QTableWidgetItem(time_str)
                time_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, 2, time_item)
                
                # 操作按钮
                delete_btn = QPushButton("🗑️ 删除")
                delete_btn.setFixedWidth(80)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ef4444;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #dc2626;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, fp=os.path.join(backup_path, backup['filename']): self.delete_backup_file(fp, dialog))
                table.setCellWidget(row, 3, delete_btn)
            
            layout.addWidget(table)
            
            # 底部按钮
            btn_layout = QHBoxLayout()
            
            refresh_btn = QPushButton("🔄 刷新")
            refresh_btn.clicked.connect(lambda: self.refresh_backup_history(dialog, table, backup_path))
            btn_layout.addWidget(refresh_btn)
            
            btn_layout.addStretch()
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"查看备份历史失败:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def delete_backup_file(self, filepath, dialog):
        """删除备份文件"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"⚠️ 确定要删除此备份文件吗？\n\n{os.path.basename(filepath)}\n\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(filepath)
                QMessageBox.information(self, "成功", "✅ 备份文件已删除")
                dialog.accept()
                # 重新打开对话框
                self.view_backup_history()
            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"❌ 删除失败:\n{str(e)}")
    
    def refresh_backup_history(self, dialog, table, backup_path):
        """刷新备份历史"""
        dialog.accept()
        self.view_backup_history()
