# -*- coding: utf-8 -*-
"""
PDF财务分析报告生成器
复用应用内已有的图表、AI分析能力，生成完整的专业财务分析报告
"""

import os
import io
import locale
import logging
from datetime import datetime
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String

from models.db_backend import db_manager
from utils.ai_analyzer import SpendingAnalyzer
from utils.logger import log_manager

logger = logging.getLogger('PDFReportGenerator')


class PDFReportGenerator:
    """PDF财务分析报告生成器"""

    # 颜色方案
    PRIMARY_COLOR = HexColor('#667eea')
    SECONDARY_COLOR = HexColor('#764ba2')
    SUCCESS_COLOR = HexColor('#10b981')
    DANGER_COLOR = HexColor('#ef4444')
    WARNING_COLOR = HexColor('#f59e0b')
    INFO_COLOR = HexColor('#3b82f6')
    TEXT_DARK = HexColor('#1f2937')
    TEXT_MEDIUM = HexColor('#4b5563')
    TEXT_LIGHT = HexColor('#6b7280')
    BG_LIGHT = HexColor('#f9fafb')
    BG_WHITE = HexColor('#ffffff')
    BORDER_COLOR = HexColor('#e5e7eb')

    def __init__(self):
        self.font_registered = False
        self.font_name = 'ChineseFont'
        self._register_fonts()
        self._init_styles()

    def _register_fonts(self):
        """注册中文字体 - 双重策略：
        1. 优先注册 CID 字体 (STSong-Light)，不嵌入字体文件，依赖PDF阅读器内置字体
        2. 同时注册 TTFont (SimSun)，嵌入字体子集作为后备
        """
        # === 策略1: 注册CID字体 (Adobe STSong-Light) ===
        # CID字体不嵌入字体文件，PDF阅读器使用内置字体渲染
        # 支持完整Unicode范围，文件体积小
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            self.font_name = 'STSong-Light'
            self.font_registered = True
            logger.info("[PDF报告] 成功注册CID中文字体: STSong-Light")
        except Exception as e:
            logger.warning(f"[PDF报告] CID字体注册失败: {e}")

        # === 策略2: 同时注册TTFont (嵌入字体子集作为后备) ===
        # TTC字体需要指定索引，TTF可以直接注册
        # simsun.ttc(宋体) 对 reportlab 兼容性最好
        font_candidates = [
            # (路径, 是否TTC, TTC索引)
            (r"C:\Windows\Fonts\simsun.ttc", True, 0),
            (r"C:\Windows\Fonts\simfang.ttf", False, None),
            (r"C:\Windows\Fonts\msyh.ttc", True, 0),
            (r"C:\Windows\Fonts\msyhbd.ttc", True, 0),
            (r"C:\Windows\Fonts\msyhl.ttc", True, 0),
            (r"C:\Windows\Fonts\yahei.ttf", False, None),
            (r"C:\Windows\Fonts\SIMLI.TTF", False, None),
            (r"C:\Windows\Fonts\STZHONGS.TTF", False, None),
            ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", False, None),
            ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", False, None),
        ]

        for font_path, is_ttc, ttc_index in font_candidates:
            if os.path.exists(font_path):
                try:
                    if is_ttc:
                        pdfmetrics.registerFont(
                            TTFont('ChineseFont', font_path, subfontIndex=ttc_index))
                    else:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    # TTFont注册成功，但保留CID字体作为主要字体
                    # 这样PDF阅读器优先使用内置CID字体，不支持时使用嵌入的TTF子集
                    logger.info(f"[PDF报告] 成功注册TTF后备字体: {font_path}")
                    break
                except Exception as e:
                    logger.warning(f"[PDF报告] TTF字体注册失败 {font_path}: {e}")
                    continue

        if not self.font_registered:
            logger.warning("[PDF报告] 未找到中文字体，将使用Helvetica")

    def _init_styles(self):
        """初始化段落样式"""
        self.styles = getSampleStyleSheet()

        font = self.font_name if self.font_registered else 'Helvetica'
        font_bold = self.font_name if self.font_registered else 'Helvetica-Bold'

        self.styles.add(ParagraphStyle(
            'ReportTitle', parent=self.styles['Title'],
            fontName=font_bold, fontSize=26, leading=32,
            textColor=self.PRIMARY_COLOR, alignment=TA_CENTER,
            spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            'ReportSubtitle', parent=self.styles['Normal'],
            fontName=font, fontSize=11, leading=16,
            textColor=self.TEXT_LIGHT, alignment=TA_CENTER,
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            'SectionTitle', parent=self.styles['Heading1'],
            fontName=font_bold, fontSize=16, leading=22,
            textColor=self.TEXT_DARK, spaceBefore=20, spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            'SubSectionTitle', parent=self.styles['Heading2'],
            fontName=font_bold, fontSize=13, leading=18,
            textColor=self.TEXT_MEDIUM, spaceBefore=14, spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            'BodyText2', parent=self.styles['Normal'],
            fontName=font, fontSize=10, leading=16,
            textColor=self.TEXT_MEDIUM, spaceAfter=6
        ))
        self.styles.add(ParagraphStyle(
            'SmallText', parent=self.styles['Normal'],
            fontName=font, fontSize=8, leading=12,
            textColor=self.TEXT_LIGHT
        ))
        self.styles.add(ParagraphStyle(
            'CardTitle', parent=self.styles['Normal'],
            fontName=font_bold, fontSize=11, leading=15,
            textColor=self.TEXT_DARK
        ))
        self.styles.add(ParagraphStyle(
            'CardValue', parent=self.styles['Normal'],
            fontName=font_bold, fontSize=18, leading=24,
            textColor=self.TEXT_DARK
        ))
        self.styles.add(ParagraphStyle(
            'AIAdvice', parent=self.styles['Normal'],
            fontName=font, fontSize=10, leading=17,
            textColor=self.TEXT_MEDIUM, leftIndent=10,
            spaceAfter=8
        ))
        self.styles.add(ParagraphStyle(
            'FooterStyle', parent=self.styles['Normal'],
            fontName=font, fontSize=8, leading=10,
            textColor=self.TEXT_LIGHT, alignment=TA_CENTER
        ))

    # ==================== 数据采集方法 ====================

    def _collect_all_data(self) -> Dict:
        """采集所有需要的数据"""
        data = {}

        # 1. 基本统计数据
        data['statistics'] = db_manager.get_statistics() or {}

        # 2. 收支记录
        data['income_records'] = db_manager.get_income_records() or []
        data['expense_records'] = db_manager.get_expense_records() or []

        # 3. 流水账
        data['cash_flow'] = db_manager.get_cash_flow() or []

        # 4. 月度数据
        data['monthly_data'] = self._get_monthly_data()

        # 5. 分类数据
        data['income_by_category'] = self._get_income_by_category()
        data['expense_by_category'] = self._get_expense_by_category()
        data['payment_by_method'] = self._get_payment_by_method()

        # 6. 预算状态
        data['budget_status'] = self._get_budget_status()

        # 7. 时间跨度
        data['date_range'] = self._get_date_range()

        # 8. AI分析
        data['ai_analysis'] = self._get_ai_analysis()

        return data

    def _get_monthly_data(self) -> List[Dict]:
        """获取月度收支数据"""
        monthly_income = defaultdict(float)
        monthly_expense = defaultdict(float)

        for record in db_manager.get_income_records() or []:
            rq = record[1]
            je = record[3] or 0
            if rq:
                monthly_income[rq[:7]] += je

        for record in db_manager.get_expense_records() or []:
            rq = record[1]
            je = record[3] or 0
            if rq:
                monthly_expense[rq[:7]] += je

        all_months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))
        result = []
        for month in all_months:
            income = monthly_income.get(month, 0)
            expense = monthly_expense.get(month, 0)
            result.append({
                'month': month,
                'income': round(income, 2),
                'expense': round(expense, 2),
                'balance': round(income - expense, 2)
            })
        return result

    def _get_income_by_category(self) -> List[Dict]:
        """获取按类别统计的收入"""
        sql = """
            SELECT c.sr_name, SUM(s.je) as total
            FROM sz_sheet_sr s
            LEFT JOIN sz_c_sr c ON s.sr_code = c.sr_code
            WHERE s.zth = ?
            GROUP BY c.sr_name
            ORDER BY total DESC
        """
        try:
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            return [{'name': r[0] or '未分类', 'amount': r[1]} for r in rows if r[1] > 0]
        except Exception as e:
            logger.error(f"[PDF报告] 获取收入分类失败: {e}")
            return []

    def _get_expense_by_category(self) -> List[Dict]:
        """获取按类别统计的支出"""
        sql = """
            SELECT c.zc_name, SUM(s.je) as total
            FROM sz_sheet_zc s
            LEFT JOIN sz_c_zc c ON s.zc_code = c.zc_code
            WHERE s.zth = ?
            GROUP BY c.zc_name
            ORDER BY total DESC
        """
        try:
            db_manager._backend.execute(sql, (db_manager.current_account,))
            rows = db_manager._backend.fetchall()
            return [{'name': r[0] or '未分类', 'amount': r[1]} for r in rows if r[1] > 0]
        except Exception as e:
            logger.error(f"[PDF报告] 获取支出分类失败: {e}")
            return []

    def _get_payment_by_method(self) -> List[Dict]:
        """获取按支付方式统计"""
        sql = """
            SELECT z.zf_name, SUM(amount) as total
            FROM (
                SELECT zf_code, je as amount FROM sz_sheet_sr WHERE zth = ?
                UNION ALL
                SELECT zf_code, je as amount FROM sz_sheet_zc WHERE zth = ?
            ) t
            LEFT JOIN sz_c_zf z ON t.zf_code = z.zf_code
            GROUP BY z.zf_name
            ORDER BY total DESC
        """
        try:
            db_manager._backend.execute(
                sql, (db_manager.current_account, db_manager.current_account)
            )
            rows = db_manager._backend.fetchall()
            return [{'name': r[0] or '未分类', 'amount': r[1]} for r in rows if r[1] > 0]
        except Exception as e:
            logger.error(f"[PDF报告] 获取支付方式统计失败: {e}")
            return []

    def _get_budget_status(self) -> Optional[Dict]:
        """获取预算状态"""
        try:
            from models.budget_manager import BudgetManager, BudgetAlert
            budget_manager = BudgetManager(db_manager)
            budget_alert = BudgetAlert(budget_manager)
            current_month = datetime.now().strftime('%Y-%m')
            return budget_alert.get_budget_status_summary(current_month)
        except Exception as e:
            logger.error(f"[PDF报告] 获取预算状态失败: {e}")
            return None

    def _get_date_range(self) -> Tuple[str, str]:
        """获取数据时间跨度"""
        all_dates = []
        for record in (db_manager.get_income_records() or []) + \
                      (db_manager.get_expense_records() or []):
            rq = record[1]
            if rq:
                try:
                    if ' ' in str(rq):
                        dt = datetime.strptime(str(rq), '%Y-%m-%d %H:%M:%S')
                    else:
                        dt = datetime.strptime(str(rq), '%Y-%m-%d')
                    all_dates.append(dt)
                except Exception:
                    pass
        if all_dates:
            return (min(all_dates).strftime('%Y-%m-%d'),
                    max(all_dates).strftime('%Y-%m-%d'))
        return ('-', '-')

    def _get_ai_analysis(self) -> Dict:
        """获取AI分析结果"""
        try:
            analyzer = SpendingAnalyzer(db_manager)
            analysis = analyzer.analyze_spending_habits(months=6)
            return analysis
        except Exception as e:
            logger.error(f"[PDF报告] AI分析失败: {e}")
            return {}

    # ==================== 图表生成方法 ====================

    def _generate_trend_chart(self, monthly_data: List[Dict]) -> Optional[Image]:
        """生成月度趋势图（更大尺寸、更好的可读性）"""
        if not monthly_data or len(monthly_data) < 1:
            return None

        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax1 = plt.subplots(figsize=(8.5, 4))
            fig.patch.set_facecolor('white')

            months = [d['month'][-2:] + '月' for d in monthly_data]
            incomes = [d['income'] for d in monthly_data]
            expenses = [d['expense'] for d in monthly_data]
            balances = [d['balance'] for d in monthly_data]

            x = range(len(months))
            bar_width = 0.35

            bars1 = ax1.bar([i - bar_width/2 for i in x], incomes, bar_width,
                           label='收入', color='#10b981', alpha=0.9,
                           edgecolor='#059669', linewidth=0.5)
            bars2 = ax1.bar([i + bar_width/2 for i in x], expenses, bar_width,
                           label='支出', color='#ef4444', alpha=0.9,
                           edgecolor='#dc2626', linewidth=0.5)

            # 在柱状图上标注金额
            for bar, val in zip(bars1, incomes):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(incomes)*0.02,
                        f'{val/10000:.1f}w' if val >= 10000 else f'{val:.0f}',
                        ha='center', va='bottom', fontsize=7, color='#059669', fontweight='bold')
            for bar, val in zip(bars2, expenses):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(expenses)*0.02,
                        f'{val/10000:.1f}w' if val >= 10000 else f'{val:.0f}',
                        ha='center', va='bottom', fontsize=7, color='#dc2626', fontweight='bold')

            ax1.set_ylabel('金额 (元)', fontsize=10, color='#374151', fontweight='bold')
            ax1.set_xticks(list(x))
            ax1.set_xticklabels(months, fontsize=9)
            ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v/10000:.1f}万' if v >= 10000 else f'{v:.0f}'))

            ax2 = ax1.twinx()
            ax2.plot(x, balances, 'o-', color='#f59e0b', linewidth=2.5,
                     markersize=7, markerfacecolor='white',
                     markeredgewidth=2, markeredgecolor='#f59e0b',
                     label='净结余', zorder=5)
            for i, bal in enumerate(balances):
                ax2.annotate(f'{bal/10000:.1f}w' if abs(bal) >= 10000 else f'{bal:.0f}',
                            (i, bal), textcoords="offset points",
                            xytext=(0, 12), ha='center', fontsize=7,
                            color='#d97706', fontweight='bold')
            ax2.set_ylabel('净结余 (元)', fontsize=10, color='#374151', fontweight='bold')

            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
                       fontsize=9, framealpha=0.95, edgecolor='#d1d5db')

            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax1.grid(True, linestyle='--', alpha=0.4, axis='y')
            ax1.set_facecolor('#f9fafb')

            fig.tight_layout(pad=1.5)

            buf = io.BytesIO()
            fig.savefig(buf, dpi=200, bbox_inches='tight',
                        facecolor='white', format='png')
            plt.close(fig)
            buf.seek(0)

            return Image(buf, width=6.8*inch, height=3.2*inch)
        except Exception as e:
            logger.error(f"[PDF报告] 生成趋势图失败: {e}")
            return None

    def _generate_pie_chart(self, data: List[Dict], title: str,
                            colors: List[str]) -> Optional[Image]:
        """生成饼图并返回reportlab Image对象"""
        if not data:
            return None

        try:
            # 切换到Agg后端以确保无头渲染
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(4.5, 3.5))
            fig.patch.set_facecolor('white')

            labels = [d['name'] for d in data]
            values = [d['amount'] for d in data]

            if len(labels) > 6:
                other_value = sum(values[6:])
                labels = labels[:6] + ['其他']
                values = values[:6] + [other_value]

            ax.pie(values, labels=labels, autopct='%1.1f%%',
                   colors=colors[:len(labels)], startangle=90,
                   pctdistance=0.75, labeldistance=1.15)

            ax.set_title(title, fontsize=11, fontweight='bold',
                         pad=10, color='#1f2937')

            plt.tight_layout()

            # 保存到内存字节流
            buf = io.BytesIO()
            fig.savefig(buf, dpi=200, bbox_inches='tight',
                        facecolor='white', format='png')
            plt.close(fig)
            buf.seek(0)

            return Image(buf, width=3.8*inch, height=3*inch)
        except Exception as e:
            logger.error(f"[PDF报告] 生成饼图失败: {e}")
            return None

    # ==================== 高级图表生成方法 ====================

    def _generate_heatmap(self, data: Dict) -> Optional[Image]:
        """生成消费时间段热力图"""
        try:
            expense_records = data.get('expense_records', [])
            if not expense_records:
                return None

            import numpy as np
            heatmap_data = np.zeros((7, 24))

            for record in expense_records:
                rq = record[1]
                je = record[3] or 0
                if rq and je > 0:
                    try:
                        if ' ' in str(rq):
                            dt = datetime.strptime(str(rq), '%Y-%m-%d %H:%M:%S')
                        else:
                            dt = datetime.strptime(str(rq), '%Y-%m-%d')
                        weekday = dt.weekday()
                        hour = dt.hour if hasattr(dt, 'hour') else 12
                        heatmap_data[weekday, hour] += je
                    except Exception:
                        pass

            if np.sum(heatmap_data) == 0:
                return None

            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(7.5, 3.5))
            fig.patch.set_facecolor('white')

            # 对数归一化
            log_data = np.log1p(heatmap_data)
            im = ax.imshow(log_data, cmap='YlOrRd', aspect='auto')

            x_labels = [f"{h}时" for h in range(24)]
            y_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

            ax.set_xticks(range(24))
            ax.set_yticks(range(7))
            ax.set_xticklabels(x_labels, fontsize=6, rotation=45)
            ax.set_yticklabels(y_labels, fontsize=8)
            ax.set_xlabel('时间段', fontsize=9)
            ax.set_ylabel('星期', fontsize=9)

            plt.colorbar(im, ax=ax, shrink=0.8, label='消费金额')
            ax.set_title('消费时间段热力图', fontsize=11, fontweight='bold', pad=8)

            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, dpi=200, bbox_inches='tight',
                        facecolor='white', format='png')
            plt.close(fig)
            buf.seek(0)
            return Image(buf, width=6.5*inch, height=3*inch)
        except Exception as e:
            logger.error(f"[PDF报告] 生成热力图失败: {e}")
            return None

    def _generate_sankey_chart(self, data: Dict) -> Optional[Image]:
        """生成资金流向桑基图"""
        try:
            income_records = data.get('income_records', [])
            expense_records = data.get('expense_records', [])

            if not income_records and not expense_records:
                return None

            from collections import defaultdict
            income_by_type = defaultdict(float)
            for record in income_records:
                sr_name = record[2] or "其他收入"
                je = record[3] or 0
                if je > 0:
                    income_by_type[sr_name] += je

            expense_by_type = defaultdict(float)
            for record in expense_records:
                zc_name = record[2] or "其他支出"
                je = record[3] or 0
                if je > 0:
                    expense_by_type[zc_name] += je

            total_income = sum(income_by_type.values())
            total_expense = sum(expense_by_type.values())

            # 构建桑基图数据
            labels = []
            source_indices = []
            target_indices = []
            values_list = []

            # 收入类型 -> 总收入
            for src_name, val in income_by_type.items():
                if val > 0:
                    if src_name not in labels:
                        labels.append(src_name)
                    if '总收入' not in labels:
                        labels.append('总收入')
                    source_indices.append(labels.index(src_name))
                    target_indices.append(labels.index('总收入'))
                    values_list.append(val)

            # 总支出 -> 支出类型
            for tgt_name, val in expense_by_type.items():
                if val > 0:
                    if '总支出' not in labels:
                        labels.append('总支出')
                    if tgt_name not in labels:
                        labels.append(tgt_name)
                    source_indices.append(labels.index('总支出'))
                    target_indices.append(labels.index(tgt_name))
                    values_list.append(val)

            # 结余
            if total_income > total_expense:
                surplus = total_income - total_expense
                if '净结余' not in labels:
                    labels.append('净结余')
                source_indices.append(labels.index('总收入'))
                target_indices.append(labels.index('净结余'))
                values_list.append(surplus)

            if len(labels) < 3:
                return None

            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from matplotlib.sankey import Sankey

            # 使用简单的饼图代替桑基图（桑基图在matplotlib中较复杂）
            # 显示收入来源和支出去向的对比
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5))
            fig.patch.set_facecolor('white')

            # 收入饼图
            if income_by_type:
                inc_labels = list(income_by_type.keys())
                inc_values = list(income_by_type.values())
                colors = plt.cm.Greens(np.linspace(0.3, 0.8, len(inc_labels)))
                ax1.pie(inc_values, labels=inc_labels, autopct='%1.1f%%',
                        colors=colors, startangle=90)
                ax1.set_title('收入来源', fontsize=10, fontweight='bold')

            # 支出饼图
            if expense_by_type:
                exp_labels = list(expense_by_type.keys())
                exp_values = list(expense_by_type.values())
                colors = plt.cm.Reds(np.linspace(0.3, 0.8, len(exp_labels)))
                ax2.pie(exp_values, labels=exp_labels, autopct='%1.1f%%',
                        colors=colors, startangle=90)
                ax2.set_title('支出去向', fontsize=10, fontweight='bold')

            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, dpi=200, bbox_inches='tight',
                        facecolor='white', format='png')
            plt.close(fig)
            buf.seek(0)
            return Image(buf, width=6.5*inch, height=3*inch)
        except Exception as e:
            logger.error(f"[PDF报告] 生成资金流向图失败: {e}")
            return None

    def _generate_radar_chart(self, data: Dict) -> Optional[Image]:
        """生成财务健康评估雷达图"""
        try:
            income_records = data.get('income_records', [])
            expense_records = data.get('expense_records', [])

            if not income_records and not expense_records:
                return None

            total_income = sum(r[3] or 0 for r in income_records)
            total_expense = sum(r[3] or 0 for r in expense_records)

            # 计算五维度得分
            # 1. 收入稳定性 - 基于收入记录数/月数
            months = set()
            for r in income_records:
                rq = r[1]
                if rq:
                    months.add(str(rq)[:7])
            num_months = max(len(months), 1)
            income_stability = min(100, len(income_records) / num_months * 20)

            # 2. 支出控制
            if total_income > 0:
                expense_ratio = total_expense / total_income
                expense_control = max(0, 100 - expense_ratio * 100)
            else:
                expense_control = 50

            # 3. 储蓄率
            if total_income > 0:
                savings_rate = (total_income - total_expense) / total_income * 100
                savings_score = max(0, min(100, savings_rate * 2))
            else:
                savings_score = 0

            # 4. 支出多样性
            expense_types = set()
            for r in expense_records:
                zc_name = r[2]
                if zc_name:
                    expense_types.add(zc_name)
            diversity = min(100, len(expense_types) * 20)

            # 5. 财务安全度
            if total_expense > 0:
                safety_ratio = total_income / total_expense if total_expense > 0 else 1
                safety = min(100, safety_ratio * 50)
            else:
                safety = 100 if total_income > 0 else 0

            dimensions = ['收入稳定性', '支出控制', '储蓄率', '支出多样性', '财务安全度']
            values = [income_stability, expense_control, savings_score, diversity, safety]

            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np

            angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
            fig.patch.set_facecolor('white')

            ax.fill(angles, values, color='#667eea', alpha=0.25)
            ax.plot(angles, values, color='#667eea', linewidth=2)

            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(dimensions, fontsize=9)
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=7)
            ax.set_title('财务健康评估', fontsize=11, fontweight='bold', pad=15)

            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, dpi=200, bbox_inches='tight',
                        facecolor='white', format='png')
            plt.close(fig)
            buf.seek(0)
            return Image(buf, width=4.5*inch, height=4.5*inch)
        except Exception as e:
            logger.error(f"[PDF报告] 生成雷达图失败: {e}")
            return None

    # ==================== 报告构建方法 ====================

    def _build_cover(self, data: Dict) -> List:
        """构建封面（含账套信息、储蓄率、月度均值）"""
        elements = []
        stats = data['statistics']

        # 顶部装饰条
        d = Drawing(500, 6)
        d.add(Rect(0, 0, 500, 6, fillColor=self.PRIMARY_COLOR))
        elements.append(d)
        elements.append(Spacer(1, 30))

        # 账套信息
        acc_info = self._get_account_info()
        if acc_info:
            elements.append(Paragraph(
                f"账套：{acc_info.get('zth','')} — {acc_info.get('xm','')} ({acc_info.get('bj','')})",
                ParagraphStyle('AccInfo', parent=self.styles['ReportSubtitle'],
                               fontSize=11, textColor=self.TEXT_MEDIUM)))
            elements.append(Spacer(1, 15))

        # 标题
        elements.append(Paragraph("InEx System", self.styles['ReportTitle']))
        elements.append(Paragraph("财务分析报告", ParagraphStyle(
            'MainTitle', parent=self.styles['ReportTitle'],
            fontSize=32, leading=40, textColor=self.TEXT_DARK
        )))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="40%", thickness=2,
                                   color=self.PRIMARY_COLOR,
                                   spaceAfter=12, spaceBefore=3, hAlign='CENTER'))

        # 报告时间
        now = datetime.now()
        elements.append(Paragraph(
            f"报告周期：{data['date_range'][0]} 至 {data['date_range'][1]}",
            self.styles['ReportSubtitle']
        ))
        elements.append(Paragraph(
            f"生成时间：{now.strftime('%Y年%m月%d日 %H:%M')}",
            self.styles['ReportSubtitle']
        ))
        elements.append(Spacer(1, 25))

        # 核心数据卡片（4卡片：收入、支出、结余、储蓄率）
        total_income = stats.get('total_income', 0) or 0
        total_expense = stats.get('total_expense', 0) or 0
        balance = total_income - total_expense
        savings_rate = round(balance / total_income * 100, 1) if total_income > 0 else 0
        months_count = len(data.get('monthly_data', []))
        avg_income = round(total_income / months_count, 2) if months_count > 0 else 0
        avg_expense = round(total_expense / months_count, 2) if months_count > 0 else 0

        card_data = [
            ('总收入', f'¥{total_income:,.2f}', self.SUCCESS_COLOR),
            ('总支出', f'¥{total_expense:,.2f}', self.DANGER_COLOR),
            ('净结余', f'¥{balance:,.2f}',
             self.WARNING_COLOR if balance >= 0 else self.DANGER_COLOR),
            ('储蓄率', f'{savings_rate}%',
             self.SUCCESS_COLOR if balance >= 0 else self.DANGER_COLOR),
            ('月均收入', f'¥{avg_income:,.2f}', self.INFO_COLOR),
            ('月均支出', f'¥{avg_expense:,.2f}', self.WARNING_COLOR),
        ]

        card_table_data = []
        for i in range(0, len(card_data), 2):
            row = []
            for j in range(2):
                if i + j < len(card_data):
                    ctitle, value, color = card_data[i + j]
                    row.append(Paragraph(
                        f'<font color="{color.hexval()}">{ctitle}</font>',
                        self.styles['CardTitle']))
                    row.append(Paragraph(
                        f'<font color="{color.hexval()}">{value}</font>',
                        self.styles['CardValue']))
            card_table_data.append(row)

        card_table = Table(card_table_data, colWidths=[0.9*inch, 1.2*inch, 0.9*inch, 1.2*inch])
        card_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name if self.font_registered else 'Helvetica'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(card_table)
        elements.append(Spacer(1, 25))

        # 底部信息
        elements.append(HRFlowable(width="100%", thickness=0.5,
                                   color=self.BORDER_COLOR, spaceAfter=10))
        elements.append(Paragraph(
            "本报告由 InEx System v2.0 自动生成 · 数据来源于本地数据库",
            self.styles['FooterStyle']))
        elements.append(Paragraph(
            "报告包含：财务概况 · 收支趋势 · 分类分析 · AI智能建议",
            self.styles['FooterStyle']))

        return elements

    def _create_bar(self, pct: float, color: str) -> Drawing:
        """创建图形化百分比进度条（填充矩形 + 百分比数字）"""
        bar_w = max(4, int(pct * 1.2))
        d = Drawing(160, 14)
        # 灰色背景条
        d.add(Rect(0, 3, 120, 8, fillColor=HexColor('#f3f4f6'),
                    strokeColor=HexColor('#e5e7eb'), strokeWidth=0.3))
        # 彩色填充条
        if bar_w > 0:
            d.add(Rect(0, 3, min(bar_w, 120), 8, fillColor=HexColor(color),
                        strokeColor=None))
        # 百分比数字
        d.add(String(125, 9, f'{pct:.1f}%', fontSize=7,
                     fillColor=HexColor('#374151'), textAnchor='start'))
        return d

    def _get_account_info(self) -> Dict:
        """获取当前账套的基本信息"""
        try:
            accounts = db_manager.get_accounts()
            for acc in accounts:
                if str(acc[0]) == db_manager.current_account:
                    return {'zth': acc[0], 'xm': acc[3], 'bj': acc[7]}
        except Exception:
            pass
        return {}

    def _build_financial_overview(self, data: Dict) -> List:
        """构建财务概况章节"""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("一、财务概况", self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=self.PRIMARY_COLOR,
                                   spaceAfter=12, spaceBefore=0))

        stats = data['statistics']
        total_income = stats.get('total_income', 0)
        total_expense = stats.get('total_expense', 0)
        balance = stats.get('balance', 0)

        # 概述文字
        savings_rate = ((total_income - total_expense) / total_income * 100) \
                       if total_income > 0 else 0
        expense_ratio = (total_expense / total_income * 100) \
                        if total_income > 0 else 0

        overview_text = (
            f"截至报告生成日，您的财务概况如下："
            f"累计总收入 <b>¥{total_income:,.2f}</b>，"
            f"累计总支出 <b>¥{total_expense:,.2f}</b>，"
            f"净结余 <b>¥{balance:,.2f}</b>。"
            f"储蓄率为 <b>{savings_rate:.1f}%</b>，"
            f"支出占收入比例为 <b>{expense_ratio:.1f}%</b>。"
        )

        if savings_rate >= 30:
            overview_text += "您的储蓄状况良好，建议继续保持。"
        elif savings_rate >= 20:
            overview_text += "储蓄率处于合理区间，仍有提升空间。"
        elif savings_rate >= 10:
            overview_text += "储蓄率偏低，建议适当控制非必要支出。"
        elif savings_rate >= 0:
            overview_text += "储蓄率较低，需要审视支出结构。"
        else:
            overview_text += "当前入不敷出，建议立即制定预算计划。"

        elements.append(Paragraph(overview_text, self.styles['BodyText2']))
        elements.append(Spacer(1, 8))

        # 详细数据表格（含颜色标识和更多指标）
        months_count = len(data.get('monthly_data', []))
        avg_income = round(total_income / months_count, 0) if months_count > 0 else 0
        avg_expense = round(total_expense / months_count, 0) if months_count > 0 else 0
        balance_color = '#10b981' if balance >= 0 else '#ef4444'
        sr_color = '#10b981' if savings_rate >= 20 else ('#f59e0b' if savings_rate >= 0 else '#ef4444')

        detail_data = [
            ['指标', '金额', '说明'],
            ['累计收入', f'¥{total_income:,.2f}', f'{len(data["income_records"])} 条记录'],
            ['累计支出', f'¥{total_expense:,.2f}', f'{len(data["expense_records"])} 条记录'],
            ['净结余',
             Paragraph(f'<font color="{balance_color}">¥{balance:,.2f}</font>',
                       self.styles['BodyText2']),
             f'储蓄率 {savings_rate:.1f}%'],
            ['月均收入', f'¥{avg_income:,.0f}', f'覆盖 {months_count} 个月'],
            ['月均支出', f'¥{avg_expense:,.0f}', f'日均 ¥{round(avg_expense/30,0):,.0f}'],
            ['收支比', f'{expense_ratio:.1f}%',
             '健康' if expense_ratio < 80 else ('关注' if expense_ratio < 100 else '超支')],
        ]

        detail_table = Table(detail_data, colWidths=[1.3*inch, 1.8*inch, 2.2*inch])
        detail_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1),
             self.font_name if self.font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [0xFFFFFF, 0xF9FAFB]),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 10))

        # 数据时间跨度 + 彩色状态标签
        status_text = "财务状况良好" if balance >= 0 else "需要关注支出"
        status_color = self.SUCCESS_COLOR if balance >= 0 else self.DANGER_COLOR
        elements.append(Paragraph(
            f"数据跨度：<b>{data['date_range'][0]}</b> 至 <b>{data['date_range'][1]}</b>  |  "
            f"收入 {len(data['income_records'])} 条 / 支出 {len(data['expense_records'])} 条  |  "
            f"状态：<font color='{status_color.hexval()}'><b>{status_text}</b></font>",
            self.styles['BodyText2']
        ))

        # 预算状态
        budget = data.get('budget_status')
        if budget and budget.get('status') != 'not_set':
            elements.append(Spacer(1, 8))
            elements.append(Paragraph("本月预算状态",
                                      self.styles['SubSectionTitle']))
            budget_text = (
                f"预算总额：<b>¥{budget['budget']:,.2f}</b> | "
                f"已使用：<b>¥{budget['actual']:,.2f}</b> | "
                f"剩余：<b>¥{budget['remaining']:,.2f}</b> | "
                f"使用率：<b>{budget['usage_rate']:.1f}%</b>"
            )
            elements.append(Paragraph(budget_text, self.styles['BodyText2']))

        return elements

    def _build_trend_analysis(self, data: Dict) -> List:
        """构建收支趋势分析章节"""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("二、收支趋势分析",
                                  self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=self.PRIMARY_COLOR,
                                   spaceAfter=12, spaceBefore=0))

        monthly_data = data['monthly_data']
        if not monthly_data:
            elements.append(Paragraph(
                "暂无月度数据，无法生成趋势分析。",
                self.styles['BodyText2']))
            return elements

        # 趋势图（直接返回Image对象，无需文件路径）
        trend_img = self._generate_trend_chart(monthly_data)
        if trend_img:
            try:
                elements.append(trend_img)
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(
                    "▲ 月度收支趋势图（柱状图：收入/支出，折线图：净结余）",
                    self.styles['SmallText']
                ))
                elements.append(Spacer(1, 10))
            except Exception as e:
                logger.error(f"[PDF报告] 嵌入趋势图失败: {e}")

        # 趋势分析文字
        if len(monthly_data) >= 2:
            first_month = monthly_data[0]
            last_month = monthly_data[-1]

            income_change = last_month['income'] - first_month['income']
            expense_change = last_month['expense'] - first_month['expense']

            trend_text = (
                f"<b>趋势分析：</b>"
                f"从 {first_month['month']} 到 {last_month['month']}，"
            )

            if income_change > 0:
                trend_text += (
                    f"收入呈上升趋势（增长 ¥{income_change:,.2f}），")
            elif income_change < 0:
                trend_text += (
                    f"收入呈下降趋势（减少 ¥{abs(income_change):,.2f}），")
            else:
                trend_text += "收入保持稳定，"

            if expense_change > 0:
                trend_text += (
                    f"支出呈上升趋势（增长 ¥{expense_change:,.2f}）。")
            elif expense_change < 0:
                trend_text += (
                    f"支出呈下降趋势（减少 ¥{abs(expense_change):,.2f}）。")
            else:
                trend_text += "支出保持稳定。"

            elements.append(Paragraph(trend_text, self.styles['BodyText2']))
            elements.append(Spacer(1, 6))

        # 月度数据表格
        elements.append(Paragraph("月度收支明细",
                                  self.styles['SubSectionTitle']))

        table_data = [['月份', '收入', '支出', '净结余']]
        for m in monthly_data:
            month_display = (m['month'][:4] + '年' +
                             str(int(m['month'][5:7])) + '月')
            table_data.append([
                month_display,
                f"¥{m['income']:,.2f}",
                f"¥{m['expense']:,.2f}",
                f"¥{m['balance']:,.2f}"
            ])

        month_table = Table(table_data,
                            colWidths=[1.8*inch, 1.5*inch,
                                       1.5*inch, 1.5*inch])
        month_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1),
             self.font_name if self.font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [0xFFFFFF, 0xF9FAFB]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(month_table)

        return elements

    def _build_category_analysis(self, data: Dict) -> List:
        """构建分类占比分析章节"""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("三、分类占比分析",
                                  self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=self.PRIMARY_COLOR,
                                   spaceAfter=12, spaceBefore=0))

        # === 支出分类分析 ===
        expense_cats = data['expense_by_category']
        if expense_cats:
            elements.append(Paragraph("支出分类占比",
                                      self.styles['SubSectionTitle']))

            # 饼图
            expense_colors = ['#ef4444', '#f97316', '#f59e0b',
                              '#eab308', '#6b7280', '#374151', '#9ca3af']
            pie_img = self._generate_pie_chart(
                expense_cats, '支出分类占比', expense_colors)
            if pie_img:
                try:
                    elements.append(pie_img)
                    elements.append(Spacer(1, 6))
                except Exception as e:
                    logger.error(f"[PDF报告] 嵌入支出饼图失败: {e}")

            # 支出分类表格（含图形化进度条）
            total_expense = sum(c['amount'] for c in expense_cats)
            expense_table_data = [['排名', '支出类别', '金额', '占比', '占比图示']]
            for i, cat in enumerate(expense_cats[:10], 1):
                pct = (cat['amount'] / total_expense * 100) \
                      if total_expense > 0 else 0
                expense_table_data.append([
                    str(i),
                    cat['name'],
                    f"¥{cat['amount']:,.0f}",
                    f"{pct:.1f}%",
                    self._create_bar(pct, '#ef4444')
                ])

            exp_table = Table(expense_table_data,
                              colWidths=[0.5*inch, 1.5*inch,
                                         1.1*inch, 0.8*inch, 2.0*inch])
            exp_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1),
                 self.font_name if self.font_registered else 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), self.DANGER_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.3, self.BORDER_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [0xFFFFFF, 0xF9FAFB]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(exp_table)


            # 支出分析文字
            if expense_cats:
                top_cat = expense_cats[0]
                top_pct = (top_cat['amount'] / total_expense * 100) \
                          if total_expense > 0 else 0
                analysis_text = (
                    f"<b>支出分析：</b>"
                    f"支出最高的类别是「{top_cat['name']}」，"
                    f"共支出 ¥{top_cat['amount']:,.2f}，"
                    f"占总支出 {top_pct:.1f}%。"
                )
                if top_pct > 50:
                    analysis_text += "该类别占比较高，建议重点关注并寻找优化空间。"
                elif top_pct > 30:
                    analysis_text += "该类别占比较高，可关注是否有优化空间。"
                else:
                    analysis_text += "支出分布较为分散，整体结构合理。"

                if len(expense_cats) > 1:
                    second_cat = expense_cats[1]
                    second_pct = (second_cat['amount'] / total_expense * 100) \
                                 if total_expense > 0 else 0
                    analysis_text += (
                        f"其次为「{second_cat['name']}」"
                        f"（¥{second_cat['amount']:,.2f}，{second_pct:.1f}%）。"
                    )

                elements.append(Paragraph(analysis_text,
                                          self.styles['BodyText2']))
                elements.append(Spacer(1, 10))

        # === 收入分类分析 ===
        income_cats = data['income_by_category']
        if income_cats:
            elements.append(Paragraph("收入分类占比",
                                      self.styles['SubSectionTitle']))

            # 饼图
            income_colors = ['#10b981', '#34d399', '#6ee7b7',
                             '#a7f3d0', '#059669', '#047857', '#065f46']
            pie_img = self._generate_pie_chart(
                income_cats, '收入分类占比', income_colors)
            if pie_img:
                try:
                    elements.append(pie_img)
                    elements.append(Spacer(1, 6))
                except Exception as e:
                    logger.error(f"[PDF报告] 嵌入收入饼图失败: {e}")

            # 收入分类表格（含图形化进度条）
            total_income = sum(c['amount'] for c in income_cats)
            income_table_data = [['排名', '收入类别', '金额', '占比', '占比图示']]
            for i, cat in enumerate(income_cats[:10], 1):
                pct = (cat['amount'] / total_income * 100) \
                      if total_income > 0 else 0
                income_table_data.append([
                    str(i),
                    cat['name'],
                    f"¥{cat['amount']:,.0f}",
                    f"{pct:.1f}%",
                    self._create_bar(pct, '#10b981')
                ])

            inc_table = Table(income_table_data,
                              colWidths=[0.5*inch, 1.5*inch,
                                         1.1*inch, 0.8*inch, 2.0*inch])
            inc_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1),
                 self.font_name if self.font_registered else 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), self.SUCCESS_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (2, -1), 'RIGHT'),
                ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.3, self.BORDER_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [0xFFFFFF, 0xF9FAFB]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(inc_table)

            # 收入分析文字
            if income_cats:
                top_inc = income_cats[0]
                top_inc_pct = (top_inc['amount'] / total_income * 100) \
                              if total_income > 0 else 0
                inc_analysis = (
                    f"<b>收入分析：</b>"
                    f"收入最高的来源是「{top_inc['name']}」，"
                    f"共 ¥{top_inc['amount']:,.2f}，"
                    f"占总收入 {top_inc_pct:.1f}%。"
                )
                if len(income_cats) > 1:
                    second_inc = income_cats[1]
                    second_inc_pct = (second_inc['amount'] / total_income * 100) \
                                     if total_income > 0 else 0
                    inc_analysis += (
                        f"其次为「{second_inc['name']}」"
                        f"（¥{second_inc['amount']:,.2f}，{second_inc_pct:.1f}%）。"
                    )
                elements.append(Paragraph(inc_analysis,
                                          self.styles['BodyText2']))
                elements.append(Spacer(1, 10))

        # === 支付方式分析 ===
        payment_data = data['payment_by_method']
        if payment_data:
            elements.append(Paragraph("支付方式分析",
                                      self.styles['SubSectionTitle']))

            total_payment = sum(p['amount'] for p in payment_data)
            payment_table_data = [['支付方式', '金额', '占比']]
            for p in payment_data[:6]:
                pct = (p['amount'] / total_payment * 100) \
                      if total_payment > 0 else 0
                payment_table_data.append([
                    p['name'],
                    f"¥{p['amount']:,.2f}",
                    f"{pct:.1f}%"
                ])

            if len(payment_data) > 6:
                other_amt = sum(p['amount'] for p in payment_data[6:])
                other_pct = (other_amt / total_payment * 100) \
                            if total_payment > 0 else 0
                payment_table_data.append(
                    ['其他', f"¥{other_amt:,.2f}", f"{other_pct:.1f}%"])

            pay_table = Table(payment_table_data,
                              colWidths=[2*inch, 2*inch, 1.5*inch])
            pay_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1),
                 self.font_name if self.font_registered else 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), self.INFO_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [0xFFFFFF, 0xF9FAFB]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(pay_table)

            # 支付方式分析文字
            if payment_data:
                top_pay = payment_data[0]
                top_pay_pct = (top_pay['amount'] / total_payment * 100) \
                              if total_payment > 0 else 0
                pay_analysis = (
                    f"<b>支付方式分析：</b>"
                    f"最常用的支付方式是「{top_pay['name']}」，"
                    f"交易金额 ¥{top_pay['amount']:,.2f}，"
                    f"占比 {top_pay_pct:.1f}%。"
                )
                elements.append(Paragraph(pay_analysis,
                                          self.styles['BodyText2']))

        return elements

    def _build_advanced_analysis(self, data: Dict) -> List:
        """构建高级分析章节（热力图、资金流向、财务健康评估）"""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("五、高级分析",
                                  self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=self.PRIMARY_COLOR,
                                   spaceAfter=12, spaceBefore=0))

        # === 5.1 消费时间段热力图 ===
        elements.append(Paragraph("5.1 消费时间段分析",
                                  self.styles['SubSectionTitle']))
        heatmap_img = self._generate_heatmap(data)
        if heatmap_img:
            try:
                elements.append(heatmap_img)
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(
                    "▲ 热力图展示了不同星期、不同时间段的消费金额分布，"
                    "颜色越深表示消费金额越高。",
                    self.styles['SmallText']))
                elements.append(Spacer(1, 10))
            except Exception as e:
                logger.error(f"[PDF报告] 嵌入热力图失败: {e}")
        else:
            elements.append(Paragraph(
                "暂无足够的时间数据生成消费热力图。",
                self.styles['BodyText2']))
            elements.append(Spacer(1, 6))

        # 热力图分析文字
        elements.append(Paragraph(
            "<b>消费时间规律：</b>"
            "通过分析不同时间段和星期几的消费分布，"
            "可以帮助您了解自己的消费习惯和规律，"
            "从而更好地规划支出。",
            self.styles['BodyText2']))
        elements.append(Spacer(1, 10))

        # === 5.2 资金流向分析 ===
        elements.append(Paragraph("5.2 资金流向分析",
                                  self.styles['SubSectionTitle']))
        sankey_img = self._generate_sankey_chart(data)
        if sankey_img:
            try:
                elements.append(sankey_img)
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(
                    "▲ 左右对比图展示了收入来源和支出去向的构成比例。",
                    self.styles['SmallText']))
                elements.append(Spacer(1, 10))
            except Exception as e:
                logger.error(f"[PDF报告] 嵌入资金流向图失败: {e}")
        else:
            elements.append(Paragraph(
                "暂无足够的收支数据生成资金流向分析。",
                self.styles['BodyText2']))
            elements.append(Spacer(1, 6))

        # 资金流向分析文字
        income_records = data.get('income_records', [])
        expense_records = data.get('expense_records', [])
        total_income = sum(r[3] or 0 for r in income_records)
        total_expense = sum(r[3] or 0 for r in expense_records)
        balance = total_income - total_expense

        flow_text = (
            f"<b>资金流向总结：</b>"
            f"总收入 <b>¥{total_income:,.2f}</b>，"
            f"总支出 <b>¥{total_expense:,.2f}</b>，"
            f"净结余 <b>¥{balance:,.2f}</b>。"
        )
        if balance > 0:
            flow_text += "收入大于支出，财务状况健康。"
        elif balance < 0:
            flow_text += "支出超过收入，建议审视消费结构。"
        else:
            flow_text += "收支平衡。"
        elements.append(Paragraph(flow_text, self.styles['BodyText2']))
        elements.append(Spacer(1, 10))

        # === 5.3 财务健康评估 ===
        elements.append(Paragraph("5.3 财务健康评估",
                                  self.styles['SubSectionTitle']))
        radar_img = self._generate_radar_chart(data)
        if radar_img:
            try:
                elements.append(radar_img)
                elements.append(Spacer(1, 6))
                elements.append(Paragraph(
                    "▲ 雷达图从五个维度评估您的财务健康状况，"
                    "得分越高表示该维度表现越好。",
                    self.styles['SmallText']))
                elements.append(Spacer(1, 10))
            except Exception as e:
                logger.error(f"[PDF报告] 嵌入雷达图失败: {e}")
        else:
            elements.append(Paragraph(
                "暂无足够的收支数据生成财务健康评估。",
                self.styles['BodyText2']))
            elements.append(Spacer(1, 6))

        # 财务健康评分详情
        if income_records or expense_records:
            months = set()
            for r in income_records + expense_records:
                rq = r[1]
                if rq:
                    months.add(str(rq)[:7])
            num_months = max(len(months), 1)

            inc_stability = min(100, len(income_records) / num_months * 20)
            exp_control = max(0, 100 - (total_expense / max(total_income, 1)) * 100) if total_income > 0 else 50
            savings_score = max(0, min(100, (total_income - total_expense) / max(total_income, 1) * 200)) if total_income > 0 else 0

            score_text = (
                f"<b>评分说明：</b><br/>"
                f"• <b>收入稳定性</b>：{inc_stability:.0f}/100 分"
                f"（基于{num_months}个月内的收入记录频率）<br/>"
                f"• <b>支出控制</b>：{exp_control:.0f}/100 分"
                f"（支出占收入比例越低，得分越高）<br/>"
                f"• <b>储蓄率</b>：{savings_score:.0f}/100 分"
                f"（储蓄率越高，得分越高）<br/>"
                f"• <b>支出多样性</b>：基于支出类型的丰富程度<br/>"
                f"• <b>财务安全度</b>：基于收入对支出的覆盖能力"
            )
            elements.append(Paragraph(score_text, self.styles['AIAdvice']))

        return elements

    def _build_ai_analysis(self, data: Dict) -> List:
        """构建AI智能分析章节"""
        elements = []
        elements.append(PageBreak())
        elements.append(Paragraph("六、AI 智能分析",
                                  self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=self.PRIMARY_COLOR,
                                   spaceAfter=12, spaceBefore=0))

        ai_analysis = data.get('ai_analysis', {})
        if not ai_analysis:
            elements.append(Paragraph(
                "暂无AI分析数据。请确保已配置AI API密钥并连接网络。",
                self.styles['BodyText2']))
            return elements

        # 1. 消费习惯总结
        suggestions = ai_analysis.get('suggestions', [])
        if suggestions:
            elements.append(Paragraph("智能建议",
                                      self.styles['SubSectionTitle']))
            for i, suggestion in enumerate(suggestions, 1):
                elements.append(Paragraph(
                    f"<b>{i}. </b>{suggestion}",
                    self.styles['AIAdvice']))
            elements.append(Spacer(1, 8))

        # 2. 异常检测
        anomalies = ai_analysis.get('anomalies', [])
        if anomalies:
            elements.append(Paragraph("异常支出检测",
                                      self.styles['SubSectionTitle']))
            anomaly_text = (
                f"在分析周期内，共检测到 <b>{len(anomalies)}</b> 笔异常支出记录。"
                f"以下为异常明细："
            )
            elements.append(Paragraph(anomaly_text, self.styles['BodyText2']))

            anomaly_table_data = [['日期', '类别', '金额', '说明']]
            for a in anomalies[:10]:
                anomaly_table_data.append([
                    str(a.get('date', '-')),
                    a.get('category', '-'),
                    f"¥{a.get('amount', 0):,.2f}",
                    a.get('reason', '-')
                ])
            if anomalies:
                a_table = Table(anomaly_table_data,
                                colWidths=[1.2*inch, 1.5*inch,
                                           1.2*inch, 2*inch])
                a_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1),
                     self.font_name if self.font_registered else 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), self.DANGER_COLOR),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [0xFFFFFF, 0xF9FAFB]),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(a_table)
                elements.append(Spacer(1, 8))

        # 3. 月度摘要
        monthly_summary = ai_analysis.get('monthly_summary', [])
        if monthly_summary:
            elements.append(Paragraph("月度消费摘要",
                                      self.styles['SubSectionTitle']))
            for ms in monthly_summary[:6]:
                ms_text = (
                    f"<b>{ms.get('month', '-')}：</b>"
                    f"支出 ¥{ms.get('total', 0):,.2f}，"
                    f"日均 ¥{ms.get('daily_avg', 0):,.2f}，"
                    f"交易 {ms.get('count', 0)} 笔"
                )
                elements.append(Paragraph(ms_text, self.styles['AIAdvice']))
            elements.append(Spacer(1, 8))

        # 4. 趋势分析
        trend = ai_analysis.get('trend', {})
        if trend:
            elements.append(Paragraph("消费趋势评估",
                                      self.styles['SubSectionTitle']))
            trend_direction = trend.get('direction', 'stable')
            trend_pct = trend.get('change_pct', 0)
            trend_text = (
                f"整体消费呈 <b>{trend_direction}</b> 趋势，"
                f"变化幅度为 {trend_pct:.1f}%。"
            )
            if trend_direction == 'up':
                trend_text += "建议关注支出增长原因，合理控制消费。"
            elif trend_direction == 'down':
                trend_text += "支出控制良好，建议继续保持。"
            else:
                trend_text += "支出水平较为稳定。"
            elements.append(Paragraph(trend_text, self.styles['BodyText2']))

        # 5. 支付方式分析
        payment_analysis = ai_analysis.get('payment_analysis', [])
        if payment_analysis:
            elements.append(Paragraph("支付方式偏好",
                                      self.styles['SubSectionTitle']))
            for pa in payment_analysis[:4]:
                pa_text = (
                    f"<b>{pa.get('method', '-')}：</b>"
                    f"¥{pa.get('total', 0):,.2f}，"
                    f"{pa.get('count', 0)} 笔交易"
                )
                elements.append(Paragraph(pa_text, self.styles['AIAdvice']))

        return elements

    def _build_top_expenses(self, data: Dict) -> List:
        """TOP20 大额支出明细"""
        elements = []
        expense_records = data.get('expense_records', [])
        if not expense_records:
            return elements

        elements.append(PageBreak())
        elements.append(Paragraph("TOP 大额支出明细", self.styles['SectionTitle']))
        elements.append(Spacer(1, 6))

        # 取金额最大的20条
        sorted_exp = sorted(expense_records, key=lambda r: float(r[3] or 0), reverse=True)[:20]
        table_data = [['日期', '类型', '金额', '备注']]
        for r in sorted_exp:
            rq = str(r[1])[:10] if r[1] else '-'
            zc_name = str(r[2]) if len(r) > 2 and r[2] else '-'
            je = float(r[3]) if len(r) > 3 and r[3] else 0
            bz = str(r[5])[:20] if len(r) > 5 and r[5] else '-'
            table_data.append([rq, zc_name, f'¥{je:,.2f}', bz])

        t = Table(table_data, colWidths=[1.3*inch, 1.8*inch, 1.2*inch, 2.2*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name if self.font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, self.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t)
        elements.append(Paragraph(
            f"共 {len(sorted_exp)} 条大额支出记录（按金额降序）",
            self.styles['FooterStyle']
        ))
        return elements

    def _build_monthly_comparison(self, data: Dict) -> List:
        """月度环比变化分析"""
        elements = []
        monthly_data = data.get('monthly_data', [])
        if len(monthly_data) < 2:
            return elements

        elements.append(Spacer(1, 12))
        elements.append(Paragraph("月度环比变化", self.styles['SectionTitle']))
        elements.append(Spacer(1, 6))

        table_data = [['月份', '收入', '支出', '结余', '收入环比', '支出环比']]
        prev = None
        for item in monthly_data:
            inc = item.get('income', 0)
            exp = item.get('expense', 0)
            bal = item.get('balance', 0)
            inc_chg = f"{round((inc - prev['income']) / prev['income'] * 100, 1)}%" if prev and prev.get('income', 0) > 0 else '-'
            exp_chg = f"{round((exp - prev['expense']) / prev['expense'] * 100, 1)}%" if prev and prev.get('expense', 0) > 0 else '-'
            table_data.append([item['month'], f'¥{inc:,.0f}', f'¥{exp:,.0f}',
                               f'¥{bal:,.0f}', inc_chg, exp_chg])
            prev = item

        t = Table(table_data, colWidths=[1.0*inch, 1.1*inch, 1.1*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name if self.font_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, self.BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        return elements

    def _build_summary_recommendations(self, data: Dict) -> List:
        """综合总结与AI智能建议"""
        elements = []
        ai_analysis = data.get('ai_analysis', {})
        stats = data.get('statistics', {})
        monthly_data = data.get('monthly_data', [])
        expense_cats = data.get('expense_by_category', [])

        elements.append(PageBreak())
        elements.append(Paragraph("总结与AI建议", self.styles['SectionTitle']))
        elements.append(HRFlowable(width="100%", thickness=1,
                                   color=self.PRIMARY_COLOR, spaceAfter=12))
        elements.append(Spacer(1, 6))

        total_income = stats.get('total_income', 0) or 0
        total_expense = stats.get('total_expense', 0) or 0
        balance = total_income - total_expense
        total_records = len(data.get('income_records', [])) + len(data.get('expense_records', []))

        # === 财务健康评分 ===
        elements.append(Paragraph("财务健康评分", self.styles['SubSectionTitle']))
        score = self._calculate_health_score(data)
        elements.append(self._create_score_bar(score))
        elements.append(Paragraph(
            self._health_score_description(score),
            ParagraphStyle('ScoreDesc', parent=self.styles['BodyText2'],
                           fontSize=10, leading=16, textColor=self.TEXT_MEDIUM,
                           spaceBefore=4, spaceAfter=10)))
        elements.append(Spacer(1, 8))

        # === AI智能建议（优先使用DeepSeek AI）===
        suggestions = ai_analysis.get('suggestions', [])
        if suggestions:
            elements.append(Paragraph("AI 智能建议",
                                       self.styles['SubSectionTitle']))
            elements.append(Paragraph(
                "以下建议由 AI 分析引擎基于您的收支数据自动生成：",
                self.styles['BodyText2']))
            elements.append(Spacer(1, 4))

            for i, s in enumerate(suggestions, 1):
                # 根据关键词判断严重程度
                severity = 'info'
                s_lower = s.lower()
                if any(w in s_lower for w in ('警告', '严重', '超支', '赤字', '风险', '立即')):
                    severity = 'danger'
                elif any(w in s_lower for w in ('优化', '减少', '控制', '降低', '关注')):
                    severity = 'warning'
                elif any(w in s_lower for w in ('良好', '优秀', '健康', '保持', '不错')):
                    severity = 'success'

                colors = {'danger': '#ef4444', 'warning': '#f59e0b',
                         'success': '#10b981', 'info': '#3b82f6'}
                icons = {'danger': '!', 'warning': '~', 'success': '+', 'info': '>'}
                color = colors.get(severity, '#3b82f6')
                icon = icons.get(severity, '>')

                elements.append(Paragraph(
                    f'<font color="{color}"><b>[{icon}]</b></font> {s}',
                    ParagraphStyle(f'AISug{i}', parent=self.styles['BodyText2'],
                                   fontSize=10, leading=18,
                                   leftIndent=12, spaceAfter=5,
                                   textColor=self.TEXT_MEDIUM)))
            elements.append(Spacer(1, 12))
        else:
            # 无AI建议时使用基础分析
            elements.append(Paragraph("数据分析洞察",
                                       self.styles['SubSectionTitle']))
            insights = self._generate_basic_insights(data)
            for ins in insights:
                elements.append(Paragraph(f"• {ins}", ParagraphStyle(
                    'Insight', parent=self.styles['BodyText2'],
                    fontSize=10, leading=16, textColor=self.TEXT_MEDIUM,
                    leftIndent=10, spaceAfter=4)))

        # === 数据概况 ===
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=0.5,
                                   color=self.BORDER_COLOR, spaceAfter=8))
        elements.append(Paragraph(
            f"本报告覆盖 <b>{len(monthly_data)}</b> 个月数据，共 <b>{total_records}</b> 条交易记录"
            f"（收入 {len(data.get('income_records', []))} 条 / 支出 {len(data.get('expense_records', []))} 条）。"
            f"累计结余 <b>¥{balance:,.2f}</b>，"
            f"月度平均支出 <b>¥{round(total_expense / max(len(monthly_data), 1), 0):,.0f}</b>。",
            self.styles['BodyText2']
        ))
        elements.append(Paragraph(
            "—— InEx System v2.0 · AI 智能分析引擎 ——",
            self.styles['FooterStyle']
        ))
        return elements

    def _calculate_health_score(self, data: Dict) -> int:
        """计算财务健康评分 (0-100)"""
        stats = data.get('stats', data.get('statistics', {}))
        ti = stats.get('total_income', 0) or 0
        te = stats.get('total_expense', 0) or 0
        monthly = data.get('monthly_data', [])
        score = 50  # 基础分

        # 储蓄率评分 (0-30分)
        if ti > 0:
            sr = (ti - te) / ti
            score += min(30, int(sr * 50))  # 储蓄率每2%得1分，上限30

        # 收支比评分 (0-20分)
        if ti > 0:
            ratio = te / ti
            if ratio < 0.5: score += 20
            elif ratio < 0.7: score += 15
            elif ratio < 0.9: score += 10
            elif ratio < 1.1: score += 5
            else: score += 0

        # 趋势评分 (0-20分，支出下降趋势加分)
        if len(monthly) >= 2:
            recent_exp = [m.get('expense', 0) for m in monthly[-3:]]
            if len(recent_exp) >= 2:
                if all(recent_exp[i] < recent_exp[i-1] for i in range(1, len(recent_exp))):
                    score += 20
                elif recent_exp[-1] < recent_exp[-2]:
                    score += 10

        # 数据充分度 (0-10分)
        records = len(data.get('income_records', [])) + len(data.get('expense_records', []))
        score += min(10, records // 500)

        # 支出多样性 (0-10分)
        cats = data.get('expense_by_category', [])
        score += min(10, len(cats) * 2)

        return min(100, max(0, score))

    def _health_score_description(self, score: int) -> str:
        """健康评分描述"""
        if score >= 80:
            return "财务状况优秀，收支管理良好，建议继续保持当前的理财习惯。"
        elif score >= 60:
            return "财务状况良好，仍有优化空间，建议关注支出结构和储蓄率。"
        elif score >= 40:
            return "财务状况一般，建议制定预算计划，控制非必要支出。"
        else:
            return "财务需要关注，建议立即审视支出结构，制定严格的预算计划。"

    def _create_score_bar(self, score: int) -> Drawing:
        """创建评分进度条"""
        colors = ['#ef4444', '#f59e0b', '#10b981']
        if score >= 80: color = colors[2]
        elif score >= 50: color = colors[1]
        else: color = colors[0]

        d = Drawing(380, 24)
        d.add(Rect(0, 6, 200, 14, fillColor=HexColor('#f3f4f6'),
                    strokeColor=HexColor('#d1d5db'), strokeWidth=0.5))
        d.add(Rect(0, 6, int(score * 2), 14, fillColor=HexColor(color), strokeColor=None))
        d.add(String(210, 13, f'{score}/100 分', fontSize=10,
                     fillColor=HexColor('#374151'), textAnchor='start', fontName=self.font_name))
        return d

    def _generate_basic_insights(self, data: Dict) -> List[str]:
        """基于基础规则生成洞察（无AI时备用）"""
        insights = []
        stats = data.get('statistics', {})
        monthly_data = data.get('monthly_data', [])
        expense_cats = data.get('expense_by_category', [])

        ti = stats.get('total_income', 0) or 0
        te = stats.get('total_expense', 0) or 0
        balance = ti - te

        if ti > 0:
            sr = round(balance / ti * 100, 1)
            if sr >= 30: insights.append(f"储蓄率达 {sr}%，财务管理优秀。")
            elif sr >= 10: insights.append(f"储蓄率 {sr}%，处于健康水平。")
            elif sr >= 0: insights.append(f"储蓄率仅 {sr}%，建议控制支出。")
            else: insights.append(f"赤字 ¥{abs(balance):,.2f}，需立即审视支出。")

        if expense_cats:
            top = expense_cats[0]
            top_pct = round(top['amount'] / te * 100, 1) if te > 0 else 0
            if top_pct > 50:
                insights.append(f"支出集中在「{top['name']}」({top_pct}%)，建议优化。")

        if len(monthly_data) >= 3:
            recent = [m.get('expense', 0) for m in monthly_data[-3:]]
            if all(recent[i] > recent[i-1] for i in range(1, len(recent))):
                insights.append("近3个月支出持续上升，需要关注。")
            elif all(recent[i] < recent[i-1] for i in range(1, len(recent))):
                insights.append("近3个月支出持续下降，节流有效。")

        return insights

    def generate_report(self, file_path: str):
        """生成完整的PDF财务分析报告"""
        logger.info(f"[PDF报告] 开始生成报告: {file_path}")

        # 设置locale为UTF-8以支持中文编码
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except Exception:
            try:
                locale.setlocale(locale.LC_ALL, 'Chinese_China.936')
            except Exception:
                try:
                    locale.setlocale(locale.LC_ALL, '.UTF-8')
                except Exception:
                    pass

        # 1. 采集数据
        data = self._collect_all_data()

        # 2. 创建PDF文档
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            topMargin=0.8*inch,
            bottomMargin=0.8*inch,
            leftMargin=0.8*inch,
            rightMargin=0.8*inch,
            title='InEx System - 财务分析报告',
            author='InEx System v2.0'
        )

        # 3. 构建所有章节
        elements = []
        elements.extend(self._build_cover(data))
        elements.extend(self._build_financial_overview(data))
        elements.extend(self._build_trend_analysis(data))
        elements.extend(self._build_category_analysis(data))
        elements.extend(self._build_top_expenses(data))
        elements.extend(self._build_monthly_comparison(data))
        elements.extend(self._build_advanced_analysis(data))
        elements.extend(self._build_ai_analysis(data))
        elements.extend(self._build_summary_recommendations(data))

        # 4. 生成PDF
        try:
            doc.build(elements)
            logger.info(f"[PDF报告] 报告生成成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"[PDF报告] 报告生成失败: {e}")
            raise
