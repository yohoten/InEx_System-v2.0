# -*- coding: utf-8 -*-
"""
数据库数据分析与建议工具
基于真实数据库记录提供财务分析和改进建议
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db_backend import db_manager
from collections import defaultdict
from datetime import datetime


class DataAnalyzer:
    """数据分析与建议生成器"""
    
    def __init__(self):
        self.income_records = []
        self.expense_records = []
        self.load_data()
    
    def load_data(self):
        """从数据库加载数据"""
        print("正在从数据库加载数据...")
        self.income_records = db_manager.get_income_records()
        self.expense_records = db_manager.get_expense_records()
        print(f"已加载 {len(self.income_records)} 条收入记录，{len(self.expense_records)} 条支出记录")
    
    def analyze_data_quality(self):
        """分析数据质量"""
        print("\n" + "="*60)
        print("📊 数据质量分析报告")
        print("="*60)
        
        issues = []
        
        # 1. 检查数据量
        total_records = len(self.income_records) + len(self.expense_records)
        if total_records < 10:
            issues.append(f"⚠️  数据量不足：仅有 {total_records} 条记录，建议至少积累30条以上记录以获得准确的分析结果")
        elif total_records < 30:
            issues.append(f"💡 数据量一般：{total_records} 条记录，可以继续积累更多数据")
        else:
            print(f"✅ 数据量充足：共 {total_records} 条记录")
        
        # 2. 检查时间跨度
        if self.income_records or self.expense_records:
            all_dates = []
            for record in self.income_records + self.expense_records:
                rq = record[1]
                if rq:
                    try:
                        if ' ' in str(rq):
                            dt = datetime.strptime(str(rq), '%Y-%m-%d %H:%M:%S')
                        else:
                            dt = datetime.strptime(str(rq), '%Y-%m-%d')
                        all_dates.append(dt)
                    except Exception as e:
                        logger.debug(f"[数据分析] 日期解析失败: {rq}, 错误: {e}")
                        pass
            
            if all_dates:
                min_date = min(all_dates)
                max_date = max(all_dates)
                days_span = (max_date - min_date).days
                
                if days_span < 7:
                    issues.append(f"⚠️  时间跨度过短：仅 {days_span} 天，建议至少覆盖1个月的数据")
                elif days_span < 30:
                    issues.append(f"💡 时间跨度较短：{days_span} 天，建议覆盖更长时间段")
                else:
                    months_span = days_span / 30
                    print(f"✅ 时间跨度良好：覆盖 {months_span:.1f} 个月（{days_span} 天）")
                
                # 检查是否有时间信息
                has_time_info = any(' ' in str(record[1]) for record in self.income_records + self.expense_records if record[1])
                if not has_time_info:
                    issues.append("⚠️  缺少时间信息：日期字段不包含具体时间，热力图将无法准确显示消费时段分布")
                    issues.append("   建议：录入时使用完整日期时间格式（如：2025-12-15 14:30:00）")
                else:
                    print("✅ 包含时间信息：可以生成准确的热力图")
            else:
                issues.append("❌ 无法解析日期信息：请检查日期格式是否正确")
        
        # 3. 检查分类多样性
        income_types = set(record[2] for record in self.income_records if record[2])
        expense_types = set(record[2] for record in self.expense_records if record[2])
        
        if len(income_types) < 2 and self.income_records:
            issues.append(f"💡 收入类型单一：仅 {len(income_types)} 种类型，建议多元化收入来源")
        elif len(income_types) >= 2:
            print(f"✅ 收入类型多样：{len(income_types)} 种收入来源")
        
        if len(expense_types) < 3 and self.expense_records:
            issues.append(f"💡 支出类型较少：仅 {len(expense_types)} 种类型，建议完善支出分类")
        elif len(expense_types) >= 5:
            print(f"✅ 支出分类丰富：{len(expense_types)} 种支出类型")
        
        # 4. 检查金额合理性
        if self.expense_records:
            expenses = [record[3] for record in self.expense_records if record[3]]
            if expenses:
                avg_expense = sum(expenses) / len(expenses)
                max_expense = max(expenses)
                
                if max_expense > avg_expense * 10:
                    issues.append(f"⚠️  存在异常大额支出：最大支出 ¥{max_expense:.2f} 是平均值 ¥{avg_expense:.2f} 的 {max_expense/avg_expense:.1f} 倍")
                    issues.append("   建议：检查是否为误录，或考虑将大额支出分期记录")
        
        # 输出问题列表
        if issues:
            print("\n📋 发现的问题与建议：")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\n🎉 数据质量优秀！可以生成准确的图表分析")
        
        return len(issues) == 0
    
    def generate_chart_suggestions(self):
        """根据数据情况生成图表使用建议"""
        print("\n" + "="*60)
        print("📈 图表使用建议")
        print("="*60)
        
        suggestions = []
        
        # 热力图建议
        has_time_info = any(' ' in str(record[1]) for record in self.expense_records if record[1])
        if has_time_info and len(self.expense_records) >= 20:
            suggestions.append("✅ 🔥 消费热力图：数据充足，可以准确展示消费时间段分布")
        elif has_time_info:
            suggestions.append("💡 🔥 消费热力图：数据量较少，建议积累更多记录后再查看")
        else:
            suggestions.append("❌ 🔥 消费热力图：缺少时间信息，请在录入时添加具体时间")
        
        # 桑基图建议
        income_types = set(record[2] for record in self.income_records if record[2])
        expense_types = set(record[2] for record in self.expense_records if record[2])
        
        if len(income_types) >= 2 and len(expense_types) >= 3:
            suggestions.append("✅ 🌊 资金流向桑基图：收支类型丰富，可以清晰展示资金流动")
        elif self.income_records and self.expense_records:
            suggestions.append("💡 🌊 资金流向桑基图：可以生成，但建议增加收支类型以获得更清晰的展示")
        else:
            suggestions.append("❌ 🌊 资金流向桑基图：需要同时有收入和支出记录")
        
        # 雷达图建议
        total_income = sum(record[3] or 0 for record in self.income_records)
        total_expense = sum(record[3] or 0 for record in self.expense_records)
        
        if total_income > 0 and total_expense > 0:
            savings_rate = (total_income - total_expense) / total_income * 100
            suggestions.append(f"✅ 🎯 财务健康评估：可以生成五维度评分（当前储蓄率：{savings_rate:.1f}%）")
        elif total_income > 0:
            suggestions.append("💡 🎯 财务健康评估：仅有收入记录，建议添加支出记录以进行全面评估")
        else:
            suggestions.append("❌ 🎯 财务健康评估：需要收支记录才能进行评估")
        
        for suggestion in suggestions:
            print(suggestion)
    
    def generate_improvement_suggestions(self):
        """生成财务改进建议"""
        print("\n" + "="*60)
        print("💡 财务改进建议")
        print("="*60)
        
        if not self.income_records and not self.expense_records:
            print("暂无数据，请先添加收支记录")
            return
        
        total_income = sum(record[3] or 0 for record in self.income_records)
        total_expense = sum(record[3] or 0 for record in self.expense_records)
        
        if total_income == 0:
            print("⚠️  警告：暂无收入记录，请尽快添加收入数据")
            return
        
        # 1. 储蓄率分析
        savings_rate = (total_income - total_expense) / total_income * 100
        print(f"\n📊 储蓄率分析：")
        print(f"   总收入：¥{total_income:.2f}")
        print(f"   总支出：¥{total_expense:.2f}")
        print(f"   净结余：¥{total_income - total_expense:.2f}")
        print(f"   储蓄率：{savings_rate:.1f}%")
        
        if savings_rate >= 30:
            print("   ✅ 储蓄率优秀！继续保持")
        elif savings_rate >= 20:
            print("   ✅ 储蓄率良好，可以尝试提高到30%以上")
        elif savings_rate >= 10:
            print("   ⚠️  储蓄率偏低，建议控制非必要支出")
        elif savings_rate >= 0:
            print("   ⚠️  储蓄率较低，需要认真审视支出结构")
        else:
            print("   ❌ 入不敷出！立即制定预算计划，削减开支")
        
        # 2. 支出结构分析
        if self.expense_records:
            print(f"\n📋 支出结构分析：")
            expense_by_type = defaultdict(float)
            for record in self.expense_records:
                zc_name = record[2] or "未分类"
                je = record[3] or 0
                expense_by_type[zc_name] += je
            
            sorted_expenses = sorted(expense_by_type.items(), key=lambda x: x[1], reverse=True)
            
            for i, (zc_type, amount) in enumerate(sorted_expenses[:5], 1):
                percentage = amount / total_expense * 100 if total_expense > 0 else 0
                bar = "█" * int(percentage / 2)
                print(f"   {i}. {zc_type}: ¥{amount:.2f} ({percentage:.1f}%) {bar}")
            
            # 检查是否有单一支出过高的情况
            if sorted_expenses:
                top_expense = sorted_expenses[0]
                if top_expense[1] / total_expense > 0.5:
                    print(f"\n   ⚠️  警告：'{top_expense[0]}' 占总支出的 {top_expense[1]/total_expense*100:.1f}%，占比过高")
                    print("   建议：寻找替代方案或降低该项支出")
        
        # 3. 收入结构分析
        if self.income_records:
            print(f"\n💰 收入结构分析：")
            income_by_type = defaultdict(float)
            for record in self.income_records:
                sr_name = record[2] or "未分类"
                je = record[3] or 0
                income_by_type[sr_name] += je
            
            sorted_incomes = sorted(income_by_type.items(), key=lambda x: x[1], reverse=True)
            
            for i, (sr_type, amount) in enumerate(sorted_incomes, 1):
                percentage = amount / total_income * 100 if total_income > 0 else 0
                print(f"   {i}. {sr_type}: ¥{amount:.2f} ({percentage:.1f}%)")
            
            if len(sorted_incomes) == 1:
                print("\n   💡 建议：目前只有单一收入来源，考虑发展副业或被动收入")
            elif len(sorted_incomes) >= 3:
                print("\n   ✅ 收入来源多样化，抗风险能力强")
        
        # 4. 记账习惯建议
        print(f"\n📝 记账习惯建议：")
        
        if self.income_records or self.expense_records:
            # 检查是否有备注
            has_notes = any(record[5] for record in self.income_records + self.expense_records if record[5])
            if not has_notes:
                print("   💡 建议：添加备注信息，方便后续查询和分析")
            else:
                print("   ✅ 已使用备注功能，便于追踪详细信息")
            
            # 检查支付方式多样性
            payment_methods = set()
            for record in self.income_records + self.expense_records:
                if record[4]:
                    payment_methods.add(record[4])
            
            if len(payment_methods) >= 3:
                print(f"   ✅ 使用 {len(payment_methods)} 种支付方式，资金管理灵活")
            else:
                print(f"   💡 仅使用 {len(payment_methods)} 种支付方式，可以考虑多样化")
        
        print("\n" + "="*60)


def main():
    """运行数据分析"""
    print("\n" + "🔍 " * 20)
    print("数据库数据分析与建议工具")
    print("🔍 " * 20)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    analyzer = DataAnalyzer()
    
    # 1. 数据质量分析
    is_good_quality = analyzer.analyze_data_quality()
    
    # 2. 图表使用建议
    analyzer.generate_chart_suggestions()
    
    # 3. 财务改进建议
    analyzer.generate_improvement_suggestions()
    
    print("\n" + "="*60)
    print("分析完成！")
    print("="*60)
    
    if not is_good_quality:
        print("\n⚠️  检测到数据质量问题，建议先改善数据质量再查看图表")
    else:
        print("\n✅ 数据质量良好，可以前往'账单分析'页面查看高级图表")


if __name__ == '__main__':
    main()
