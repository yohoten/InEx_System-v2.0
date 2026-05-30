# -*- coding: utf-8 -*-
"""
AI 账单助手模块 - 基于 DeepSeek API
"""

import requests
import json
import os
from cryptography.fernet import Fernet
from PyQt5.QtCore import QThread, pyqtSignal
from utils.logger import log_manager


class AIConfigManager:
    """管理 AI 配置，支持加密存储"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        # 使用固定密钥或从环境变量获取，实际生产中应更安全地管理此密钥
        if not os.path.exists("secret.key"):
            self.key = Fernet.generate_key()
            with open("secret.key", "wb") as f:
                f.write(self.key)
        else:
            with open("secret.key", "rb") as f:
                self.key = f.read()
        self.cipher = Fernet(self.key)

    def save_config(self, api_key, model="deepseek-chat", temperature=0.7, max_tokens=1000):
        """保存配置，API Key 会被加密"""
        encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
        
        config = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        config['ai'] = {
            'api_key_encrypted': encrypted_key,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def get_api_key(self):
        """获取解密后的 API Key"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if 'ai' in config and 'api_key_encrypted' in config['ai']:
                # 去除可能的空白字符（包括换行符）
                api_key = self.cipher.decrypt(config['ai']['api_key_encrypted'].encode()).decode()
                return api_key.strip()
        except Exception as e:
            log_manager.warning(f"[AI Config] 读取密钥失败: {e}")
        return ""

    def get_full_config(self):
        """获取完整配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('ai', {})
        except Exception as e:
            log_manager.warning(f"[AI配置] 读取配置文件失败: {e}")
            return {}


class AISuggestionsWorker(QThread):
    """AI 建议生成工作线程"""
    finished = pyqtSignal(str)  # 成功信号
    error = pyqtSignal(str)     # 错误信号

    def __init__(self, api_key, model, prompt, temperature=0.7, max_tokens=1000, base_url="https://api.deepseek.com/v1"):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url

    def run(self):
        # 确保 API Key 没有前后空白字符
        clean_api_key = self.api_key.strip()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {clean_api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位拥有10年经验的资深个人理财顾问。请根据用户提供的收支数据，给出简洁、实用且富有洞察力的建议。"},
                {"role": "user", "content": self.prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                self.finished.emit(content)
            else:
                self.error.emit(f"API 错误: {response.status_code} - {response.text}")
        except Exception as e:
            self.error.emit(f"网络请求失败: {str(e)}")
