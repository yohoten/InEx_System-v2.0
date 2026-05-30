# -*- coding: utf-8 -*-
"""
AI 智能分类引擎
根据用户输入的备注信息，利用 DeepSeek API 推荐最匹配的收入/支出分类。
"""

import json
import logging
from typing import List, Optional

from models.config import ConfigManager
from utils.logger import LogManager

log_manager = LogManager()
logger = logging.getLogger('AIClassifier')


class AIClassifier:
    """AI 智能分类器"""

    def __init__(self):
        self.config = ConfigManager()
        self.api_key = None
        self.model = "deepseek-chat"  # 默认模型，可根据配置调整

    def _get_api_key(self) -> str:
        """获取加密的 API Key（通过 AIConfigManager）"""
        if not self.api_key:
            try:
                from utils.ai_assistant import AIConfigManager
                ai_config = AIConfigManager()
                self.api_key = ai_config.get_api_key()
            except Exception as e:
                log_manager.error(f"[AI分类] 获取API Key失败: {e}", exc_info=True)
        return self.api_key or ""

    def recommend_category(self, remark: str, categories: List[str], is_income: bool = False) -> Optional[str]:
        """根据备注推荐分类
        
        Args:
            remark: 用户输入的备注信息
            categories: 可选的分类列表（如：餐饮, 交通, 购物...）
            is_income: 是否为收入类型
            
        Returns:
            推荐的分类名称，若无法推荐则返回 None
        """
        if not remark or not categories:
            return None

        api_key = self._get_api_key()
        if not api_key:
            logger.warning("[AI分类] API Key 未配置，跳过推荐")
            return None

        prompt = f"""你是一个专业的财务分类助手。请根据用户的记账备注，从给定的分类列表中选择最合适的一个。

## 记账类型
{'收入' if is_income else '支出'}

## 备注内容
"{remark}"

## 可选分类列表
{json.dumps(categories, ensure_ascii=False)}

## 要求
1. 只输出分类名称，不要包含任何解释或其他文字。
2. 如果备注与任何分类都不相关，输出 "其他"。
3. 确保输出的分类名称严格存在于上述列表中。
"""

        try:
            import requests
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1  # 低温度以确保结果确定性
            }

            response = requests.post(url, headers=headers, json=payload, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # 验证返回的分类是否在列表中
            if content in categories:
                logger.info(f"[AI分类] 成功推荐分类: {content} (备注: {remark})")
                return content
            else:
                logger.warning(f"[AI分类] AI 返回了无效分类: {content}")
                log_manager.warning(f"[AI分类] AI 返回了不在列表中的分类: {content}, 期望列表: {categories}")
                return None

        except Exception as e:
            log_manager.error(f"[AI分类] 调用 DeepSeek API 失败: {e}", exc_info=True)
            return None
