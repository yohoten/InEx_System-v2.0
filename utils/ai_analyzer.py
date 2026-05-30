# -*- coding: utf-8 -*-
"""
智能消费分析模块| 基于历史数据进行消费习惯分析、趋势预测和异常检测
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger('SpendingAnalyzer')


class SpendingAnalyzer:
    """智能消费分析器
    
    功能:
    - 分析消费习惯（Top类别、趋势）
    - 检测异常消费
    - 生成AI建议
    - 提供可视化数据
    """
    
    def __init__(self, db_manager, ai_assistant=None):
        """初始化消费分析器
        
        Args:
            db_manager: 数据库管理器实例
            ai_assistant: AI助手实例
        """
        self.db_manager = db_manager
        self.ai_assistant = ai_assistant
    
    def analyze_spending_habits(self, months: int = 3) -> Dict:
        """分析消费习惯
        
        Args:
            months: 分析的月数，默认3个月
            
        Returns:
            Dict: 包含各类分析结果的字典
        """
        if not self.db_manager.is_connected():
            logger.warning("[智能分析] 数据库未连接")
            return {}
        
        try:
            # 获取最近N个月的支出数据
            data = self._get_expense_data_last_months(months)
            
            if not data:
                logger.info("[智能分析] 无支出数据")
                return {
                    'period': f'最近{months}个月',
                    'total_records': 0,
                    'message': '暂无支出数据'
                }
            
            logger.info(f"[智能分析] 开始分析，共{len(data)}条记录")
            
            analysis = {
                'period': f'最近{months}个月',
                'total_records': len(data),
                'top_categories': self.get_top_categories(data),
                'spending_trend': self.calculate_trend(data),
                'anomalies': self.detect_anomalies(data),
                'monthly_summary': self.get_monthly_summary(data),
                'payment_analysis': self.analyze_payment_methods(data),
                'suggestions': []
            }
            
            # 如果有AI助手，生成智能建议
            if self.ai_assistant:
                try:
                    suggestions = self._generate_ai_suggestions(analysis)
                    analysis['suggestions'] = suggestions
                except Exception as e:
                    logger.error(f"[智能分析] AI建议生成失败: {e}")
                    analysis['suggestions'] = self._generate_basic_suggestions(analysis)
            else:
                analysis['suggestions'] = self._generate_basic_suggestions(analysis)
            
            logger.info("[智能分析] 分析完成")
            return analysis
            
        except Exception as e:
            logger.error(f"[智能分析] 分析失败: {e}")
            return {'error': str(e)}
    
    def _get_expense_data_last_months(self, months: int) -> List[Dict]:
        """获取最近N个月的支出数据
        
        Args:
            months: 月数
            
        Returns:
            List[Dict]: 支出记录列表
        """
        if not self.db_manager.is_connected():
            return []
        
        try:
            backend = self.db_manager.get_backend()
            
            # 计算起始日期
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # 查询支出记录
            sql = '''
                SELECT s.djh, s.rq, c.zc_name, s.je, z.zf_name, s.bz
                FROM sz_sheet_zc s
                LEFT JOIN sz_c_zc c ON s.zc_code = c.zc_code
                LEFT JOIN sz_c_zf z ON s.zf_code = z.zf_code
                WHERE s.zth=? AND s.rq >= ? AND s.rq <= ?
                ORDER BY s.rq DESC
            '''
            
            backend.execute(sql, (self.db_manager.current_account, start_str, end_str))
            results = backend.fetchall()
            
            data = []
            for row in results:
                data.append({
                    'djh': row[0],
                    'rq': row[1],
                    'category': row[2] or '未知',
                    'amount': row[3],
                    'payment_method': row[4] or '未知',
                    'remark': row[5] or ''
                })
            
            logger.debug(f"[智能分析] 获取到{len(data)}条支出记录")
            return data
            
        except Exception as e:
            logger.error(f"[智能分析] 获取数据失败: {e}")
            return []
    
    def get_top_categories(self, data: List[Dict], top_n: int = 5) -> List[Dict]:
        """获取Top消费类别
        
        Args:
            data: 支出数据列表
            top_n: 返回前N个类别
            
        Returns:
            List[Dict]: Top类别列表
        """
        if not data:
            return []
        
        # 按类别统计
        category_stats = {}
        for record in data:
            category = record['category']
            amount = record['amount']
            
            if category not in category_stats:
                category_stats[category] = {
                    'category': category,
                    'total_amount': 0,
                    'count': 0,
                    'avg_amount': 0
                }
            
            category_stats[category]['total_amount'] += amount
            category_stats[category]['count'] += 1
        
        # 计算平均值
        for stats in category_stats.values():
            stats['avg_amount'] = stats['total_amount'] / stats['count'] if stats['count'] > 0 else 0
        
        # 按总金额排序
        sorted_categories = sorted(
            category_stats.values(),
            key=lambda x: x['total_amount'],
            reverse=True
        )
        
        # 计算总额用于百分比
        total_amount = sum(item['total_amount'] for item in sorted_categories)
        
        # 添加百分比并返回Top N
        result = []
        for item in sorted_categories[:top_n]:
            item['percentage'] = (item['total_amount'] / total_amount * 100) if total_amount > 0 else 0
            result.append(item)
        
        logger.debug(f"[智能分析] Top {top_n} 消费类别: {[r['category'] for r in result]}")
        return result
    
    def calculate_trend(self, data: List[Dict]) -> Dict:
        """计算消费趋势
        
        Args:
            data: 支出数据列表
            
        Returns:
            Dict: 趋势分析结果
        """
        if not data:
            return {'trend': 'unknown', 'message': '数据不足'}
        
        # 按月份分组
        monthly_data = {}
        for record in data:
            try:
                date = datetime.strptime(record['rq'], '%Y-%m-%d')
                month_key = date.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'month': month_key,
                        'total': 0,
                        'count': 0
                    }
            
                monthly_data[month_key]['total'] += record['amount']
                monthly_data[month_key]['count'] += 1
            except Exception as e:
                logger.warning(f"[AI分析] 处理月度数据时出错: {e}")
                continue
        
        if len(monthly_data) < 2:
            return {
                'trend': 'insufficient_data',
                'message': '数据不足以分析趋势',
                'monthly_data': list(monthly_data.values())
            }
        
        # 按月份排序
        sorted_months = sorted(monthly_data.values(), key=lambda x: x['month'])
        
        # 计算趋势
        amounts = [m['total'] for m in sorted_months]
        
        # 简单线性回归判断趋势
        n = len(amounts)
        if n >= 2:
            x_mean = (n - 1) / 2
            y_mean = sum(amounts) / n
            
            numerator = sum((i - x_mean) * (amounts[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            slope = numerator / denominator if denominator != 0 else 0
            
            # 判断趋势
            if slope > amounts[-1] * 0.05:  # 增长超过5%
                trend = 'increasing'
                message = '消费呈上升趋势'
            elif slope < -amounts[-1] * 0.05:  # 下降超过5%
                trend = 'decreasing'
                message = '消费呈下降趋势'
            else:
                trend = 'stable'
                message = '消费相对稳定'
        else:
            trend = 'unknown'
            message = '无法判断趋势'
            slope = 0
        
        result = {
            'trend': trend,
            'message': message,
            'slope': slope,
            'monthly_data': sorted_months,
            'avg_monthly': sum(amounts) / len(amounts),
            'max_monthly': max(amounts),
            'min_monthly': min(amounts)
        }
        
        logger.debug(f"[智能分析] 消费趋势: {trend}")
        return result
    
    def detect_anomalies(self, data: List[Dict], std_multiplier: float = 2.0) -> List[Dict]:
        """检测异常消费
        
        Args:
            data: 支出数据列表
            std_multiplier: 标准差倍数，默认2倍
            
        Returns:
            List[Dict]: 异常记录列表
        """
        if len(data) < 3:
            return []
        
        # 提取金额
        amounts = [record['amount'] for record in data]
        
        # 计算统计值
        mean_amount = statistics.mean(amounts)
        std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        threshold = mean_amount + std_multiplier * std_amount
        
        anomalies = []
        for record in data:
            if record['amount'] > threshold:
                anomaly_score = (record['amount'] - mean_amount) / std_amount if std_amount > 0 else 0
                anomalies.append({
                    'djh': record['djh'],
                    'rq': record['rq'],
                    'category': record['category'],
                    'amount': record['amount'],
                    'payment_method': record['payment_method'],
                    'remark': record['remark'],
                    'anomaly_score': round(anomaly_score, 2),
                    'mean': round(mean_amount, 2),
                    'threshold': round(threshold, 2),
                    'reason': f'金额 {record["amount"]:.2f} 超过阈值 {threshold:.2f}'
                })
        
        # 按异常分数排序
        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        
        logger.info(f"[智能分析] 检测到 {len(anomalies)} 笔异常消费")
        return anomalies
    
    def get_monthly_summary(self, data: List[Dict]) -> List[Dict]:
        """获取月度汇总
        
        Args:
            data: 支出数据列表
            
        Returns:
            List[Dict]: 月度汇总列表
        """
        if not data:
            return []
        
        # 按月份分组
        monthly_summary = {}
        for record in data:
            try:
                date = datetime.strptime(record['rq'], '%Y-%m-%d')
                month_key = date.strftime('%Y-%m')
                
                if month_key not in monthly_summary:
                    monthly_summary[month_key] = {
                        'month': month_key,
                        'total_amount': 0,
                        'transaction_count': 0,
                        'categories': {},
                        'avg_transaction': 0
                    }
                
                monthly_summary[month_key]['total_amount'] += record['amount']
                monthly_summary[month_key]['transaction_count'] += 1
                
                # 按类别统计
                category = record['category']
                if category not in monthly_summary[month_key]['categories']:
                    monthly_summary[month_key]['categories'][category] = 0
                monthly_summary[month_key]['categories'][category] += record['amount']
                
            except Exception as e:
                logger.warning(f"[AI分析] 处理分类数据时出错: {e}")
                continue
        
        # 计算平均值
        for summary in monthly_summary.values():
            summary['avg_transaction'] = (
                summary['total_amount'] / summary['transaction_count']
                if summary['transaction_count'] > 0 else 0
            )
        
        # 按月份排序
        result = sorted(monthly_summary.values(), key=lambda x: x['month'])
        return result
    
    def analyze_payment_methods(self, data: List[Dict]) -> List[Dict]:
        """分析支付方式使用情况
        
        Args:
            data: 支出数据列表
            
        Returns:
            List[Dict]: 支付方式分析结果
        """
        if not data:
            return []
        
        # 按支付方式统计
        payment_stats = {}
        for record in data:
            method = record['payment_method']
            
            if method not in payment_stats:
                payment_stats[method] = {
                    'method': method,
                    'total_amount': 0,
                    'count': 0,
                    'percentage': 0
                }
            
            payment_stats[method]['total_amount'] += record['amount']
            payment_stats[method]['count'] += 1
        
        # 计算总额和百分比
        total_amount = sum(stats['total_amount'] for stats in payment_stats.values())
        
        for stats in payment_stats.values():
            stats['percentage'] = (
                (stats['total_amount'] / total_amount * 100) if total_amount > 0 else 0
            )
            stats['avg_amount'] = (
                stats['total_amount'] / stats['count'] if stats['count'] > 0 else 0
            )
        
        # 按金额排序
        result = sorted(payment_stats.values(), key=lambda x: x['total_amount'], reverse=True)
        
        logger.debug(f"[智能分析] 支付方式分析: {[r['method'] for r in result]}")
        return result
    
    def _generate_ai_suggestions(self, analysis: Dict) -> List[str]:
        """使用AI生成智能建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[str]: 建议列表
        """
        if not self.ai_assistant:
            return []
        
        # 计算衍生指标以辅助AI决策
        top_cats = analysis.get('top_categories', [])
        trend = analysis.get('spending_trend', {})
        monthly_avg = trend.get('avg_monthly', 0)
        
        # 构建结构化提示词 - 遵循专家角色设定与深度洞察要求
        prompt = f"""你是一位拥有15年经验的资深个人理财顾问（CFP认证）。请根据以下消费数据，提供一份专业的财务诊断报告。

## 📊 核心数据概览
- **分析周期**：{analysis.get('period', '未知')}
- **总交易笔数**：{analysis.get('total_records', 0)}笔
- **月均支出**：{monthly_avg:.2f}元
- **支出波动**：{trend.get('min_monthly', 0):.2f}元 ~ {trend.get('max_monthly', 0):.2f}元

## 🎯 重点消费类别（Top 3）
{chr(10).join([f"- {c['category']}: {c['total_amount']:.2f}元 (占比{c['percentage']:.1f}%)" for c in top_cats[:3]])}

## ⚠️ 异常与风险点
- **趋势预警**：{trend.get('message', '平稳')}
- **异常交易**：发现 {len(analysis.get('anomalies', []))} 笔超出常规阈值的消费

## 💡 你的任务
请给出3-5条极具针对性的理财建议。
**必须遵守以下准则：**
1. **拒绝泛泛而谈**：不要说“建议节约开支”，而要说“建议将‘餐饮’类支出从目前的1500元压缩至1000元以内”。
2. **量化行动指南**：每条建议必须包含具体的数字目标或百分比限制。
3. **多维度视角**：结合恩格尔系数、储蓄率等概念进行简要点评。
4. **格式规范**：每条建议以Emoji开头，控制在80字以内，直接输出建议内容。

Please directly output suggestion list,无需开场白.
"""
        
        try:
            # 调用AI助手
            if hasattr(self.ai_assistant, 'generate_suggestions'):
                suggestions_text = self.ai_assistant.generate_suggestions(prompt)
                # 过滤并格式化建议
                suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and len(s.strip()) > 5]
                return suggestions[:5]  # 最多5条
            else:
                logger.warning("[智能分析] AI助手不支持generate_suggestions方法")
                return self._generate_basic_suggestions(analysis)
        except Exception as e:
            logger.error(f"[智能分析] AI建议生成异常: {e}", exc_info=True)
            return self._generate_basic_suggestions(analysis)
    
    def _generate_basic_suggestions(self, analysis: Dict) -> List[str]:
        """生成基础建议
        
        Args:
            analysis: 分析结果
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        # 基于Top类别的建议
        top_categories = analysis.get('top_categories', [])
        if top_categories:
            top_category = top_categories[0]
            if top_category['percentage'] > 40:
                suggestions.append(
                    f"⚠️ {top_category['category']}支出占比{top_category['percentage']:.1f}%，建议适当控制"
                )
        
        # 基于趋势的建议
        trend = analysis.get('spending_trend', {})
        if trend.get('trend') == 'increasing':
            suggestions.append("📈 消费呈上升趋势，建议制定预算计划")
        elif trend.get('trend') == 'decreasing':
            suggestions.append("✅ 消费控制良好，继续保持")
        
        # 基于异常消费的建议
        anomalies = analysis.get('anomalies', [])
        if anomalies:
            suggestions.append(
                f"🔍 发现{len(anomalies)}笔异常消费，建议检查是否有必要支出"
            )
        
        # 通用建议
        monthly_avg = trend.get('avg_monthly', 0)
        if monthly_avg > 0:
            suggestions.append(f"💡 月均支出{monthly_avg:.2f}元，建议建立应急基金")
        
        if not suggestions:
            suggestions.append("💰 继续保持良好的消费习惯")
        
        return suggestions[:5]
