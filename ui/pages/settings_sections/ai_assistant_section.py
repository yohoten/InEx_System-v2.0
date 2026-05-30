# -*- coding: utf-8 -*-
"""
AI助手区域组件
负责API Key配置、模型选择、AI建议获取等功能
"""

import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGroupBox, QLineEdit, QPushButton, QComboBox,
                             QDoubleSpinBox, QTextEdit, QFrame, QMessageBox,
                             QFileDialog, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils.ai_assistant import AISuggestionsWorker
from ui.styles import UIStyles


class AIAssistantSection(QWidget):
    """AI助手区域组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_page = parent
        
        # UI组件
        self.api_key_input = None
        self.test_key_btn = None
        self.model_combo = None
        self.temp_spin = None
        self.analysis_type_combo = None
        self.time_range_combo = None
        self.get_suggestion_btn = None
        self.copy_btn = None
        self.export_btn = None
        self.ai_output_text = None
        
        self.initUI()
    
    def initUI(self):
        """初始化AI助手区域UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # AI助手分组
        ai_group = QGroupBox("🤖 AI账单助手")
        ai_group.setStyleSheet(UIStyles.group_box_style())
        ai_layout = QVBoxLayout()
        ai_layout.setSpacing(12)
        
        # API Key 输入
        key_frame = QFrame()
        key_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 10px;")
        key_layout = QHBoxLayout(key_frame)
        key_layout.setSpacing(10)
        
        key_label = QLabel("🔑 API Key:")
        key_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        key_layout.addWidget(key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setFixedHeight(35)
        self.api_key_input.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
        """)
        key_layout.addWidget(self.api_key_input)
        
        self.test_key_btn = QPushButton("🧪 测试")
        self.test_key_btn.setCursor(Qt.PointingHandCursor)
        self.test_key_btn.setFixedWidth(70)
        self.test_key_btn.setFixedHeight(35)
        self.test_key_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        self.test_key_btn.setStyleSheet("""
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
        self.test_key_btn.clicked.connect(self.test_ai_key)
        key_layout.addWidget(self.test_key_btn)
        ai_layout.addWidget(key_frame)
        
        # 模型与参数设置
        param_frame = QFrame()
        param_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 10px;")
        param_layout = QHBoxLayout(param_frame)
        param_layout.setSpacing(10)
        
        model_label = QLabel("🎯 模型:")
        model_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        param_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek-chat", "deepseek-v3", "deepseek-r1", "deepseek-v4-flash"])
        self.model_combo.setFixedHeight(35)
        self.model_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
        """)
        param_layout.addWidget(self.model_combo)
        
        temp_label = QLabel("创意度:")
        temp_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        param_layout.addWidget(temp_label)
        
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0, 1)
        self.temp_spin.setValue(0.7)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setFixedHeight(35)
        self.temp_spin.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.temp_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #667eea;
            }
        """)
        param_layout.addWidget(self.temp_spin)
        param_layout.addStretch()
        ai_layout.addWidget(param_frame)
        
        # 分析参数设置
        analysis_frame = QFrame()
        analysis_frame.setStyleSheet("background-color: #f9fafb; border-radius: 8px; padding: 10px;")
        analysis_layout = QHBoxLayout(analysis_frame)
        analysis_layout.setSpacing(10)
        
        type_label = QLabel("📈 分析类型:")
        type_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        analysis_layout.addWidget(type_label)
        
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(["消费分析", "省钱建议", "收入趋势", "异常检测"])
        self.analysis_type_combo.setFixedHeight(35)
        self.analysis_type_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.analysis_type_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
        """)
        analysis_layout.addWidget(self.analysis_type_combo)
        
        range_label = QLabel("时间范围:")
        range_label.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        analysis_layout.addWidget(range_label)
        
        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["全部历史数据", "本月", "上月", "最近30天", "最近90天"])
        self.time_range_combo.setFixedHeight(35)
        self.time_range_combo.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.time_range_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #667eea;
            }
        """)
        analysis_layout.addWidget(self.time_range_combo)
        analysis_layout.addStretch()
        ai_layout.addWidget(analysis_frame)
        
        # 操作按钮组
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background-color: #fffbeb; border-radius: 8px; padding: 10px;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(8)
        
        self.get_suggestion_btn = QPushButton("🚀 获取 AI 深度建议")
        self.get_suggestion_btn.setCursor(Qt.PointingHandCursor)
        self.get_suggestion_btn.setFixedHeight(38)
        self.get_suggestion_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        self.get_suggestion_btn.setStyleSheet("""
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5568d3;
            }
            QPushButton:pressed {
                background-color: #4a5ab5;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
                color: #e5e7eb;
            }
        """)
        self.get_suggestion_btn.clicked.connect(self.get_ai_suggestions)
        btn_layout.addWidget(self.get_suggestion_btn)
        
        self.copy_btn = QPushButton("📋 复制")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setFixedHeight(38)
        self.copy_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
            QPushButton:pressed {
                background-color: #b45309;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_suggestion)
        btn_layout.addWidget(self.copy_btn)
        
        self.export_btn = QPushButton("💾 导出")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setFixedHeight(38)
        self.export_btn.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #ec4899;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #db2777;
            }
            QPushButton:pressed {
                background-color: #be185d;
            }
        """)
        self.export_btn.clicked.connect(self.export_suggestion)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        ai_layout.addWidget(btn_frame)
        
        # AI输出文本框
        ai_output_label = QLabel("💬 AI 回复:")
        ai_output_label.setFont(QFont(UIStyles.FONT_FAMILY, 10, QFont.Bold))
        ai_output_label.setStyleSheet("color: #374151;")
        ai_layout.addWidget(ai_output_label)
        
        self.ai_output_text = QTextEdit()
        self.ai_output_text.setReadOnly(True)
        self.ai_output_text.setPlaceholderText("点击下方按钮获取 AI 建议...\n\n* 您的收支数据将被发送至 DeepSeek API，请勿包含敏感个人信息")
        self.ai_output_text.setMaximumHeight(280)
        self.ai_output_text.setMinimumHeight(200)
        self.ai_output_text.setFont(QFont(UIStyles.FONT_FAMILY, 10))
        self.ai_output_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 0px;
                color: #374151;
            }
            QTextEdit:focus {
                border-color: #667eea;
            }
            QTextEdit::verticalScrollBar {
                width: 10px;
                background-color: #f3f4f6;
                border-radius: 5px;
            }
            QTextEdit::verticalScrollBar::handle {
                background-color: #9ca3af;
                border-radius: 5px;
                min-height: 30px;
            }
            QTextEdit::verticalScrollBar::handle:hover {
                background-color: #6b7280;
            }
        """)
        ai_layout.addWidget(self.ai_output_text)
        
        ai_layout.addStretch()
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        self.setLayout(layout)
    
    def test_ai_key(self):
        """测试 API Key 有效性"""
        if hasattr(self.parent_page, 'test_ai_key'):
            self.parent_page.test_ai_key()
    
    def get_ai_suggestions(self):
        """获取 AI 建议"""
        if hasattr(self.parent_page, 'get_ai_suggestions'):
            self.parent_page.get_ai_suggestions()
    
    def on_ai_finished(self, content):
        """AI 请求完成回调"""
        formatted_content = self._format_ai_response(content)
        self.ai_output_text.setHtml(formatted_content)
        if hasattr(self.parent_page, 'log_text'):
            self.parent_page.log_text.append("[INFO] AI 建议生成成功")
    
    def _format_ai_response(self, content: str) -> str:
        """格式化AI回复为HTML"""
        if not content or not content.strip():
            return '<div style="color: #9ca3af; padding: 20px; text-align: center;">暂无内容</div>'
        
        content = content.strip()
        html_parts = []
        
        html_parts.append('''
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 15px 20px; border-radius: 8px 8px 0 0; margin-bottom: 0;">
            <h3 style="margin: 0; font-size: 16px; font-weight: bold;">
                ✨ AI智能理财建议
            </h3>
            <p style="margin: 5px 0 0 0; font-size: 12px; opacity: 0.9;">
                基于您的收支数据生成的个性化建议
            </p>
        </div>
        ''')
        
        lines = content.split('\n')
        suggestions = [line.strip() for line in lines if line.strip()]
        
        if suggestions:
            html_parts.append('<div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px;">')
            
            for idx, suggestion in enumerate(suggestions, 1):
                emoji = ""
                text = suggestion
                
                emoji_prefixes = ['💡', '⚠️', '✅', '📈', '📉', '🔍', '💰', '🎯', '⭐', '👉']
                for prefix in emoji_prefixes:
                    if suggestion.startswith(prefix):
                        emoji = prefix
                        text = suggestion[len(prefix):].strip()
                        break
                
                if not emoji:
                    emoji_icons = ['💡', '🎯', '⭐', '👉', '✨']
                    emoji = emoji_icons[(idx - 1) % len(emoji_icons)]
                
                html_parts.append(f'''
                <div style="background-color: white; 
                            border-left: 4px solid #667eea; 
                            margin-bottom: 12px; 
                            padding: 12px 15px; 
                            border-radius: 6px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="display: flex; align-items: flex-start;">
                        <span style="font-size: 20px; margin-right: 10px; flex-shrink: 0;">{emoji}</span>
                        <div style="flex: 1;">
                            <div style="color: #374151; font-size: 13px; line-height: 1.6;">
                                {text}
                            </div>
                        </div>
                    </div>
                </div>
                ''')
            
            html_parts.append('</div>')
        else:
            html_parts.append('''
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px; 
                        color: #6b7280; text-align: center;">
                未获取到有效建议，请重试
            </div>
            ''')
        
        return ''.join(html_parts)
    
    def copy_suggestion(self):
        """复制建议内容"""
        content = self.ai_output_text.toPlainText()
        if not content or content.strip() in ['暂无内容', '未获取到有效建议，请重试']:
            QMessageBox.warning(self, "提示", "没有可复制的内容")
            return
            
        clipboard = QApplication.clipboard()
        clipboard.setText(content)
        
        from ui.widgets.toast import Toast
        Toast.success(self, "✅ 建议已复制到剪贴板", duration=2000)
        if hasattr(self.parent_page, 'log_text'):
            self.parent_page.log_text.append("[INFO] 建议已复制到剪贴板")
    
    def export_suggestion(self):
        """导出建议为文本文件"""
        content = self.ai_output_text.toPlainText()
        if not content or content.strip() in ['暂无内容', '未获取到有效建议，请重试']:
            QMessageBox.warning(self, "提示", "没有可导出的内容")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "导出AI建议", 
            f"AI理财建议_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                header = f"""# AI智能理财建议
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析类型: {self.analysis_type_combo.currentText()}
时间范围: {self.time_range_combo.currentText()}
{'='*60}

"""
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(header)
                    f.write(content)
                
                from ui.widgets.toast import Toast
                Toast.success(self, f"✅ 建议已导出至:\n{file_path}", duration=3000)
                if hasattr(self.parent_page, 'log_text'):
                    self.parent_page.log_text.append(f"[INFO] 建议已导出至: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出文件时出错:\n{str(e)}")
    
    def get_api_key(self):
        """获取API Key"""
        return self.api_key_input.text().strip()
    
    def load_config(self):
        """加载AI配置"""
        try:
            from utils.ai_assistant import AIConfigManager
            ai_config_manager = AIConfigManager()
            
            # 获取加密的 API Key
            api_key = ai_config_manager.get_api_key()
            if api_key:
                self.api_key_input.setText(api_key)
            
            # 获取其他 AI 配置
            full_config = ai_config_manager.get_full_config()
            if full_config:
                # 模型选择
                model = full_config.get('model', 'deepseek-chat')
                index = self.model_combo.findText(model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                
                # 温度参数
                temperature = full_config.get('temperature', 0.85)
                self.temp_spin.setValue(temperature)
        except Exception as e:
            print(f"[AI助手] 加载配置失败: {e}")
    
    def save_config(self):
        """保存AI配置"""
        try:
            from utils.ai_assistant import AIConfigManager
            ai_config_manager = AIConfigManager()
            
            api_key = self.api_key_input.text().strip()
            model = self.model_combo.currentText()
            temperature = self.temp_spin.value()
            
            if api_key:
                ai_config_manager.save_config(
                    api_key=api_key,
                    model=model,
                    temperature=temperature,
                    max_tokens=1000
                )
        except Exception as e:
            print(f"[AI助手] 保存配置失败: {e}")
