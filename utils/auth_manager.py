# -*- coding: utf-8 -*-
"""
认证管理模块 - 安全存储和验证用户凭据
"""

import os
import json
import bcrypt
from cryptography.fernet import Fernet
from utils.logger import log_manager


class AuthManager:
    """管理用户认证，支持加密存储和密码哈希"""
    
    def __init__(self, config_path="config.json"):

        """
        初始化方法，用于设置配置文件路径和密钥文件路径，并确保密钥文件存在
        
        参数:
            config_path (str): 配置文件的路径，默认为"config.json"
        """
        self.config_path = config_path  # 存储配置文件路径
        self.key_file = "secret.key"
        self._ensure_key_exists()
        
    def _ensure_key_exists(self):
        """确保加密密钥文件存在"""
        if not os.path.exists(self.key_file):
            log_manager.info("[Auth] 生成新的加密密钥")
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
        
        with open(self.key_file, "rb") as f:
            self.key = f.read()
        self.cipher = Fernet(self.key)
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_config(self, config):
        """保存配置文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def hash_password(self, password: str) -> str:
        """
        对密码进行bcrypt哈希处理
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码字符串
        """
        # bcrypt需要bytes类型
        password_bytes = password.encode('utf-8')
        # 生成salt并哈希（rounds=12是推荐的安全级别）
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        验证密码是否匹配哈希值
        
        Args:
            password: 用户输入的明文密码
            hashed_password: 存储的哈希密码
            
        Returns:
            True如果密码匹配，否则False
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            log_manager.error(f"[Auth] 密码验证失败: {e}")
            return False
    
    def encrypt_text(self, text: str) -> str:
        """
        加密文本
        
        Args:
            text: 要加密的明文
            
        Returns:
            加密后的文本（Base64编码）
        """
        return self.cipher.encrypt(text.encode('utf-8')).decode('utf-8')
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """
        解密文本
        
        Args:
            encrypted_text: 加密的文本
            
        Returns:
            解密后的明文
        """
        try:
            return self.cipher.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            log_manager.error(f"[Auth] 解密失败: {e}")
            raise ValueError("解密失败，可能是密钥不匹配或数据损坏")
    
    def save_credentials(self, account: str, password: str):
        """
        保存用户凭据到配置文件
        
        Args:
            account: 账号（加密存储）
            password: 密码（哈希存储）
        """
        config = self._load_config()
        
        # 加密账号
        encrypted_account = self.encrypt_text(account)
        # 哈希密码
        hashed_password = self.hash_password(password)
        
        # 保存到配置
        if 'login' not in config:
            config['login'] = {}
        
        config['login']['account_encrypted'] = encrypted_account
        config['login']['password_hash'] = hashed_password
        
        self._save_config(config)
        log_manager.info(f"[Auth] 凭据已安全保存 (账号: {account})")
    
    def verify_credentials(self, account: str, password: str) -> bool:
        """
        验证用户凭据
        
        Args:
            account: 用户输入的账号
            password: 用户输入的密码
            
        Returns:
            True如果凭据正确，否则False
        """
        config = self._load_config()
        
        # 检查是否有保存的凭据
        if 'login' not in config:
            log_manager.warning("[Auth] 未找到保存的凭据，使用默认凭据")
            return self._verify_default_credentials(account, password)
        
        try:
            # 解密存储的账号
            stored_account = self.decrypt_text(config['login']['account_encrypted'])
            # 获取哈希密码
            stored_password_hash = config['login']['password_hash']
            
            # 验证账号和密码
            if account == stored_account and self.verify_password(password, stored_password_hash):
                log_manager.info(f"[Auth] 用户 {account} 登录成功")
                return True
            else:
                log_manager.warning(f"[Auth] 用户 {account} 登录失败")
                return False
                
        except Exception as e:
            log_manager.error(f"[Auth] 凭据验证出错: {e}")
            # 降级到默认凭据
            return self._verify_default_credentials(account, password)
    
    def _verify_default_credentials(self, account: str, password: str) -> bool:
        """
        验证默认凭据（向后兼容）
        
        Args:
            account: 用户输入的账号
            password: 用户输入的密码
            
        Returns:
            True如果匹配默认凭据
        """
        default_account = "2501033401"
        default_password = "admin0457"
        
        if account == default_account and password == default_password:
            log_manager.info("[Auth] 使用默认凭据登录成功")
            # 首次使用默认凭据后，提示用户修改
            log_manager.warning("[Auth] 检测到使用默认凭据，建议立即修改密码")
            return True
        return False
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        修改密码
        
        Args:
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            True如果修改成功
        """
        config = self._load_config()
        
        if 'login' not in config:
            log_manager.error("[Auth] 无法修改密码：未找到凭据配置")
            return False
        
        try:
            # 解密账号
            account = self.decrypt_text(config['login']['account_encrypted'])
            # 验证旧密码
            if not self.verify_password(old_password, config['login']['password_hash']):
                log_manager.warning("[Auth] 旧密码验证失败")
                return False
            
            # 保存新密码
            self.save_credentials(account, new_password)
            log_manager.info(f"[Auth] 用户 {account} 密码修改成功")
            return True
            
        except Exception as e:
            log_manager.error(f"[Auth] 密码修改失败: {e}")
            return False
    
    def initialize_default_credentials(self):
        """
        初始化默认凭据（仅在配置不存在时调用）
        """
        config = self._load_config()
        
        if 'login' not in config:
            log_manager.info("[Auth] 初始化默认凭据")
            self.save_credentials("2501033401", "admin0457")
            return True
        return False
    
    def has_credentials(self) -> bool:
        """检查是否存在已保存的凭据"""
        config = self._load_config()
        return 'login' in config and 'account_encrypted' in config['login']

    def register_user(self, account: str, password: str) -> bool:
        """注册新用户到数据库 sys_users 表"""
        from models.db_backend import db_manager
        if not db_manager.is_connected():
            log_manager.error("[Auth] 注册失败: 数据库未连接")
            return False

        hashed = self.hash_password(password)
        try:
            backend = db_manager.get_backend()
            backend.execute(
                "INSERT INTO sys_users (account, password_hash) VALUES (?, ?)",
                (account, hashed)
            )
            log_manager.info(f"[Auth] 注册新用户: {account}")
            self._write_audit_log(account, "user_register", account)
            return True
        except Exception as e:
            log_manager.error(f"[Auth] 注册失败: {e}")
            return False

    # 登录限流：{account: (fail_count, lock_until_timestamp)}
    _login_attempts = {}

    def verify_user_credentials(self, account: str, password: str) -> bool:
        """验证用户凭据（带登录限流：5次失败锁定30秒）"""
        import time

        # 检查是否在锁定期内
        if account in self._login_attempts:
            fail_count, lock_until = self._login_attempts[account]
            if time.time() < lock_until:
                remaining = int(lock_until - time.time())
                log_manager.warning(f"[Auth] 账号 {account} 已锁定，剩余 {remaining}s")
                return False

        # 先查 config.json（兼容旧版单用户）
        if self.has_credentials():
            if self.verify_credentials(account, password):
                self._login_attempts.pop(account, None)
                return True

        # 再查 sys_users 表
        from models.db_backend import db_manager
        if not db_manager.is_connected():
            return False

        try:
            backend = db_manager.get_backend()
            backend.execute(
                "SELECT password_hash FROM sys_users WHERE account=? AND is_active=1",
                (account,)
            )
            row = backend.fetchone()
            if row and self.verify_password(password, row[0]):
                backend.execute(
                    "UPDATE sys_users SET last_login=CURRENT_TIMESTAMP WHERE account=?",
                    (account,)
                )
                self._login_attempts.pop(account, None)
                log_manager.info(f"[Auth] 用户 {account} 数据库验证成功")
                self._write_audit_log(account, "login", account, "登录成功")
                return True
        except Exception as e:
            log_manager.warning(f"[Auth] 数据库验证失败: {e}")

        # 记录失败尝试
        fail_count = self._login_attempts.get(account, (0, 0))[0] + 1
        lock_until = time.time() + 30 if fail_count >= 5 else 0
        self._login_attempts[account] = (fail_count, lock_until)
        if fail_count >= 5:
            log_manager.warning(f"[Auth] 账号 {account} 锁定30秒（{fail_count}次失败）")
        return False

    def _write_audit_log(self, account: str, action: str, target: str = None, detail: str = None):
        """写入审计日志到 sys_audit_log 表"""
        from models.db_backend import db_manager
        if not db_manager.is_connected():
            return
        try:
            backend = db_manager.get_backend()
            backend.execute(
                "INSERT INTO sys_audit_log (account, action, target, detail) VALUES (?, ?, ?, ?)",
                (account, action, target or "", detail or "")
            )
        except Exception as e:
            log_manager.error(f"[Auth] 审计日志写入失败: {e}")
