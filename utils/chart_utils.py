# -*- coding: utf-8 -*-
"""
Matplotlib 图表工具模块
提供常用的图表生成功能
"""
import logging
logger = logging.getLogger(__name__)

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
import numpy as np
matplotlib.style.use('default')  # 使用默认样式，避免用户自定义样式冲突
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 支持中文
matplotlib.rcParams['axes.unicode_minus'] = False  # 支持负号


class ChartGenerator:
    """图表生成器"""
    
    @staticmethod
    def create_line_chart(categories: list, series_list: list, 
                         title: str = "", x_label: str = "", y_label: str = "",
                         figsize: tuple = (10, 6), palette: list = None):
        """创建折线图
        
        Args:
            categories: X 轴分类列表，如 ['9 月', '10 月', '11 月', '12 月']
            series_list: 系列数据列表，每个元素为 {'name': '收入', 'data': [5000, 6000, ...], 'color': '#2ecc71'}
            title: 图表标题
            x_label: X 轴标签
            y_label: Y 轴标签
            figsize: 图表大小
            palette: 颜色调色板
        
        Returns:
            Figure 对象
        """
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        default_palette = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12', '#9b59b6']
        if palette is None:
            palette = default_palette
        
        for idx, series in enumerate(series_list):
            color = series.get('color', palette[idx % len(palette)])
            ax.plot(categories, series['data'], label=series['name'], 
                   marker='o', linewidth=2, color=color)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.legend(loc='best')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # 旋转 X 轴标签
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_pie_chart(labels: list, values: list, 
                        title: str = "", figsize: tuple = (8, 8),
                        colors: list = None, autopct: str = '%1.1f%%'):
        """创建饼图
        
        Args:
            labels: 标签列表
            values: 数值列表
            title: 图表标题
            figsize: 图表大小
            colors: 颜色列表
            autopct: 百分比格式
        
        Returns:
            Figure 对象
        """
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        default_colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        if colors is None:
            colors = default_colors
        
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels,
            colors=colors[:len(labels)],
            autopct=autopct,
            startangle=90,
            pctdistance=0.85
        )
        
        # 设置字体
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('equal')  # 保证饼图为圆形
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_bar_chart(categories: list, values: list,
                        title: str = "", x_label: str = "", y_label: str = "",
                        figsize: tuple = (10, 6), color: str = '#3498db'):
        """创建柱状图
        
        Args:
            categories: X 轴分类列表
            values: 数值列表
            title: 图表标题
            x_label: X 轴标签
            y_label: Y 轴标签
            figsize: 图表大小
            color: 柱子颜色
        
        Returns:
            Figure 对象
        """
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        x_pos = range(len(categories))
        ax.bar(x_pos, values, color=color, alpha=0.8)
        
        # 添加数值标签
        for i, v in enumerate(values):
            ax.text(i, v + max(values) * 0.01, f'{v:.0f}', 
                   ha='center', va='bottom', fontsize=9)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_stacked_bar_chart(categories: list, data_dict: dict,
                                title: str = "", x_label: str = "", y_label: str = "",
                                figsize: tuple = (10, 6), palette: list = None):
        """创建堆叠柱状图
        
        Args:
            categories: X 轴分类列表
            data_dict: 数据字典，{'系列 1': [值 1, 值 2, ...], '系列 2': [...]}
            title: 图表标题
            x_label: X 轴标签
            y_label: Y 轴标签
            figsize: 图表大小
            palette: 颜色调色板
        
        Returns:
            Figure 对象
        """
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        default_palette = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12']
        if palette is None:
            palette = default_palette
        
        x_pos = range(len(categories))
        bottom = [0] * len(categories)
        
        for idx, (series_name, values) in enumerate(data_dict.items()):
            color = palette[idx % len(palette)]
            ax.bar(x_pos, values, bottom=bottom, label=series_name, 
                  color=color, alpha=0.8)
            
            # 更新底部
            bottom = [b + v for b, v in zip(bottom, values)]
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(loc='best')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_heatmap(data: np.ndarray, x_labels: list, y_labels: list,
                      title: str = "消费时间段热力图", x_label: str = "时间段",
                      y_label: str = "星期", figsize: tuple = (12, 8),
                      cmap: str = 'YlOrRd'):
        """创建热力图 - 展示消费时间分布
        
        Args:
            data: 二维数组，表示不同时间段的消费金额
            x_labels: X 轴标签（时间段）
            y_labels: Y 轴标签（星期或日期）
            title: 图表标题
            x_label: X 轴标签
            y_label: Y 轴标签
            figsize: 图表大小
            cmap: 颜色映射
        
        Returns:
            Figure 对象
        """
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        # 绘制热力图
        im = ax.imshow(data, cmap=cmap, aspect='auto')
        
        # 设置刻度
        ax.set_xticks(range(len(x_labels)))
        ax.set_yticks(range(len(y_labels)))
        ax.set_xticklabels(x_labels, rotation=45, ha='right')
        ax.set_yticklabels(y_labels)
        
        # 添加数值标注
        for i in range(len(y_labels)):
            for j in range(len(x_labels)):
                value = data[i, j]
                if value > 0:
                    text_color = 'white' if data[i, j] > np.max(data) * 0.6 else 'black'
                    ax.text(j, i, f'{value:.0f}', ha='center', va='center',
                           color=text_color, fontsize=8)
        
        # 添加颜色条
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('消费金额', rotation=270, labelpad=15)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_sankey_chart(flows: list, nodes: list,
                           title: str = "资金流向桑基图",
                           figsize: tuple = (12, 8)):
        """创建桑基图 - 展示资金流向
        
        Args:
            flows: 流量列表，每个元素为 {'source': '来源', 'target': '目标', 'value': 金额}
            nodes: 节点列表，所有出现的节点名称
            title: 图表标题
            figsize: 图表大小
        
        Returns:
            Figure 对象
        """
        try:
            from matplotlib.sankey import Sankey
            
            fig = Figure(figsize=figsize)
            ax = fig.add_subplot(111, xticks=[], yticks=[])
            
            # 准备 Sankey 数据
            # Sankey 需要特定的格式：flows, orientations, labels
            sankey_data = []
            orientations = []
            labels = []
            
            # 简化版本：使用基本的 Sankey 图
            # 注意：Matplotlib 的 Sankey 功能有限，这里提供一个基础实现
            # 对于复杂的桑基图，建议使用 pySankey 库
            
            # 提取唯一的源和目标
            sources = set()
            targets = set()
            for flow in flows:
                sources.add(flow['source'])
                targets.add(flow['target'])
            
            all_nodes = list(sources | targets)
            
            # 创建简化的流向图（使用条形图模拟）
            node_values = {}
            for flow in flows:
                source = flow['source']
                target = flow['target']
                value = flow['value']
                
                if source not in node_values:
                    node_values[source] = {'in': 0, 'out': 0}
                if target not in node_values:
                    node_values[target] = {'in': 0, 'out': 0}
                
                node_values[source]['out'] += value
                node_values[target]['in'] += value
            
            # 绘制简化的资金流向图
            categories = list(node_values.keys())
            inflows = [node_values[c]['in'] for c in categories]
            outflows = [node_values[c]['out'] for c in categories]
            
            x_pos = range(len(categories))
            width = 0.35
            
            ax.bar([p - width/2 for p in x_pos], inflows, width, 
                  label='流入', color='#2ecc71', alpha=0.8)
            ax.bar([p + width/2 for p in x_pos], outflows, width,
                  label='流出', color='#e74c3c', alpha=0.8)
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel('节点', fontsize=12)
            ax.set_ylabel('金额', fontsize=12)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            ax.grid(axis='y', linestyle='--', alpha=0.3)
            
            fig.tight_layout()
            
            return fig
            
        except ImportError:
            logger.warning("Sankey 图需要 matplotlib 完整安装")
            # 返回一个提示图
            fig = Figure(figsize=figsize)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, '桑基图功能需要安装完整的 matplotlib\n建议升级到最新版本',
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xticks([])
            ax.set_yticks([])
            return fig
    
    @staticmethod
    def create_radar_chart(dimensions: list, values: list,
                          title: str = "财务健康评估雷达图",
                          figsize: tuple = (8, 8),
                          fill_color: str = '#3498db',
                          line_color: str = '#2980b9'):
        """创建雷达图 - 多维度财务健康评估
        
        Args:
            dimensions: 维度列表，如 ['收入稳定性', '支出控制', '储蓄率', '投资回报', '负债率']
            values: 各维度得分列表（0-100）
            title: 图表标题
            figsize: 图表大小
            fill_color: 填充颜色
            line_color: 线条颜色
        
        Returns:
            Figure 对象
        """
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='polar')
        
        # 计算角度
        num_vars = len(dimensions)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        
        # 闭合图形
        values_closed = values + values[:1]
        angles_closed = angles + angles[:1]
        
        # 绘制雷达图
        ax.plot(angles_closed, values_closed, 'o-', linewidth=2, color=line_color, label='当前状态')
        ax.fill(angles_closed, values_closed, alpha=0.25, color=fill_color)
        
        # 设置维度标签
        ax.set_xticks(angles)
        ax.set_xticklabels(dimensions, fontsize=10)
        
        # 设置 Y 轴范围
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=8)
        
        # 添加网格
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # 添加标题
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # 添加图例
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_calendar_heatmap(daily_data: dict, 
                                title: str = "每日支出热力图",
                                figsize: tuple = (14, 8),
                                year: int = None):
        """创建日历热力图 - 类似 GitHub 贡献图
        
        Args:
            daily_data: 字典，键为日期字符串 'YYYY-MM-DD'，值为金额
                       例如：{'2025-01-15': 150.5, '2025-01-16': 200.0}
            title: 图表标题
            figsize: 图表大小
            year: 指定年份，None 表示使用数据中的年份
        
        Returns:
            Figure 对象
        """
        from datetime import datetime, timedelta
        from calendar import month_name, day_name
        
        if not daily_data:
            # 返回空提示图
            fig = Figure(figsize=figsize)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', 
                   fontsize=16, color='#9ca3af', transform=ax.transAxes)
            ax.axis('off')
            return fig
        
        # 确定年份
        if year is None:
            dates = [datetime.strptime(d, '%Y-%m-%d') for d in daily_data.keys()]
            year = max(d.year for d in dates)
        
        # 生成该年的所有日期
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        # 构建完整的数据矩阵（53周 x 7天）
        # 找到第一个周一作为起始点
        days_from_monday = start_date.weekday()
        calendar_start = start_date - timedelta(days=days_from_monday)
        
        # 计算需要的周数
        total_days = (end_date - calendar_start).days + 1
        num_weeks = (total_days + 6) // 7
        
        # 初始化数据矩阵
        heatmap_matrix = np.zeros((7, num_weeks))
        date_matrix = [[None for _ in range(num_weeks)] for _ in range(7)]
        
        # 填充数据
        current_date = calendar_start
        for week in range(num_weeks):
            for day in range(7):
                if current_date <= end_date:
                    date_str = current_date.strftime('%Y-%m-%d')
                    date_matrix[day][week] = current_date
                    
                    # 获取该日期的支出金额
                    if date_str in daily_data:
                        heatmap_matrix[day][week] = daily_data[date_str]
                
                current_date += timedelta(days=1)
        
        # 创建图表
        fig = Figure(figsize=figsize)
        ax = fig.add_subplot(111)
        
        # 自定义颜色映射 - 从浅绿到深绿（类似 GitHub）
        from matplotlib.colors import LinearSegmentedColormap
        
        colors = ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39']
        cmap = LinearSegmentedColormap.from_list('github_green', colors, N=256)
        
        # 绘制热力图
        im = ax.imshow(heatmap_matrix, cmap=cmap, aspect='auto', interpolation='nearest')
        
        # 设置坐标轴
        ax.set_xticks(range(num_weeks))
        ax.set_yticks(range(7))
        
        # 设置 Y 轴标签（星期）
        weekday_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        ax.set_yticklabels(weekday_labels, fontsize=9)
        
        # 设置 X 轴标签（月份）
        month_positions = []
        month_labels = []
        current_month = None
        
        for week in range(num_weeks):
            # 找到该周中间的日期
            mid_day = 3  # 周四
            if date_matrix[mid_day][week]:
                date_obj = date_matrix[mid_day][week]
                month = date_obj.month
                
                if month != current_month:
                    current_month = month
                    month_positions.append(week)
                    month_labels.append(f'{month}月')
        
        ax.set_xticks(month_positions)
        ax.set_xticklabels(month_labels, fontsize=9)
        
        # 添加数值标注（仅在有数据的格子显示）
        for day in range(7):
            for week in range(num_weeks):
                value = heatmap_matrix[day, week]
                if value > 0 and date_matrix[day][week]:
                    # 根据背景色决定文字颜色
                    text_color = 'white' if value > np.max(heatmap_matrix) * 0.6 else '#24292e'
                    ax.text(week, day, f'{value:.0f}', 
                           ha='center', va='center',
                           color=text_color, fontsize=6, fontweight='bold')
        
        # 添加颜色条
        cbar = fig.colorbar(im, ax=ax, pad=0.02)
        cbar.set_label('支出金额（元）', rotation=270, labelpad=15, fontsize=10)
        
        # 设置标题
        ax.set_title(f'{title} - {year}年', fontsize=14, fontweight='bold', pad=15)
        
        # 添加统计信息
        total_expense = sum(daily_data.values())
        avg_daily = total_expense / len(daily_data) if daily_data else 0
        max_day = max(daily_data.items(), key=lambda x: x[1]) if daily_data else ('N/A', 0)
        
        stats_text = f'总支出: ¥{total_expense:.2f} | 日均: ¥{avg_daily:.2f} | 最高: ¥{max_day[1]:.2f} ({max_day[0]})'
        fig.text(0.5, 0.02, stats_text, ha='center', fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # 调整布局
        fig.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        return fig
    
    @staticmethod
    def embed_chart_in_widget(fig: Figure, widget):
        """将图表嵌入到 PyQt5 组件中
        
        Args:
            fig: Matplotlib Figure 对象
            widget: PyQt5 容器组件
        
        Returns:
            FigureCanvas 对象
        """
        canvas = FigureCanvas(fig)
        canvas.setParent(widget)
        return canvas


# 全局图表生成器实例
chart_generator = ChartGenerator()
