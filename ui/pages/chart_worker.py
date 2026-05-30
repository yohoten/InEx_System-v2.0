# -*- coding: utf-8 -*-
"""
异步图表加载工作线程
避免图表生成阻塞UI主线程
"""

from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib
matplotlib.use('Agg')  # 非GUI后端,适合后台线程
from matplotlib.figure import Figure


class ChartWorker(QThread):
    """图表生成工作线程"""
    
    # 信号: 图表生成完成
    chart_ready = pyqtSignal(Figure)
    # 信号: 发生错误
    error_occurred = pyqtSignal(str)
    # 信号: 进度更新
    progress_updated = pyqtSignal(int, str)
    
    def __init__(self, chart_type, data, **kwargs):
        super().__init__()
        self.chart_type = chart_type  # 'trend', 'category', 'payment'等
        self.data = data
        self.kwargs = kwargs
        self._is_cancelled = False
    
    def run(self):
        """在后台线程中生成图表"""
        try:
            self.progress_updated.emit(10, "正在准备数据...")
            
            if self._is_cancelled:
                return
            
            self.progress_updated.emit(30, "正在生成图表...")
            
            # 根据图表类型生成不同的图表
            figure = self._generate_chart()
            
            if self._is_cancelled:
                return
            
            self.progress_updated.emit(90, "正在优化显示...")
            
            # 发送完成的图表
            self.chart_ready.emit(figure)
            self.progress_updated.emit(100, "完成")
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _generate_chart(self):
        """根据类型生成图表"""
        if self.chart_type == 'trend':
            return self._generate_trend_chart()
        elif self.chart_type == 'category_pie':
            return self._generate_category_pie_chart()
        elif self.chart_type == 'payment_bar':
            return self._generate_payment_bar_chart()
        else:
            raise ValueError(f"未知的图表类型: {self.chart_type}")
    
    def _generate_trend_chart(self):
        """生成趋势图"""
        from utils.chart_utils import ChartGenerator
        
        dates = self.data.get('dates', [])
        income_data = self.data.get('income', [])
        expense_data = self.data.get('expense', [])
        
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # 使用ChartGenerator生成趋势图
        ChartGenerator.create_dual_axis_line_chart(
            ax, dates, income_data, expense_data,
            title="收支趋势",
            xlabel="日期",
            ylabel="金额"
        )
        
        fig.tight_layout()
        return fig
    
    def _generate_category_pie_chart(self):
        """生成分类饼图"""
        from utils.chart_utils import ChartGenerator
        
        categories = self.data.get('categories', [])
        values = self.data.get('values', [])
        colors = self.data.get('colors', None)
        
        fig = Figure(figsize=(8, 8), dpi=100)
        ax = fig.add_subplot(111)
        
        ChartGenerator.create_pie_chart(
            ax, categories, values,
            title="分类占比",
            colors=colors
        )
        
        fig.tight_layout()
        return fig
    
    def _generate_payment_bar_chart(self):
        """生成支付方式柱状图"""
        from utils.chart_utils import ChartGenerator
        
        payments = self.data.get('payments', [])
        amounts = self.data.get('amounts', [])
        
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        ChartGenerator.create_bar_chart(
            ax, payments, amounts,
            title="支付方式统计",
            xlabel="支付方式",
            ylabel="金额"
        )
        
        fig.tight_layout()
        return fig
    
    def cancel(self):
        """取消图表生成"""
        self._is_cancelled = True
