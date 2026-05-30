# -*- coding: utf-8 -*-
"""
CSV 处理工具模块
支持 CSV 文件的读写，用于数据导入导出
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Tuple


class CSVHandler:
    """CSV 文件处理器"""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self.file_path = None
    
    def write_csv(self, filename: str, headers: List[str], data: List[Tuple], 
                  encoding: str = 'utf-8-sig'):
        """写入 CSV 文件（带 BOM 头，Excel 可识别中文）"""
        # 确保目录存在
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(filename, 'w', newline='', encoding=encoding) as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow(headers)
            
            # 写入数据
            for row in data:
                writer.writerow(row)
        
        print(f"[CSV] 保存文件成功：{filename}")
        return True
    
    def read_csv(self, filename: str, encoding: str = 'utf-8-sig') -> List[List[str]]:
        """读取 CSV 文件"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"文件不存在：{filename}")
        
        data = []
        with open(filename, 'r', newline='', encoding=encoding) as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # 跳过空行
                    data.append(row)
        
        print(f"[CSV] 读取文件成功：{filename}，共{len(data)}行")
        return data
    
    def read_csv_as_dict(self, filename: str, encoding: str = 'utf-8-sig') -> List[Dict]:
        """读取 CSV 文件并转换为字典列表"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"文件不存在：{filename}")
        
        data = []
        with open(filename, 'r', newline='', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        
        print(f"[CSV] 读取文件成功：{filename}，共{len(data)}条记录")
        return data
    
    def detect_encoding(self, filename: str) -> str:
        """检测文件编码（简单实现）"""
        # 尝试常见编码
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030']
        
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前 1KB
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        return 'utf-8-sig'  # 默认返回带 BOM 的 UTF-8
    
    def import_income_records(self, filename: str, encoding: str = None) -> List[Dict]:
        """导入收入记录 CSV"""
        if encoding is None:
            encoding = self.detect_encoding(filename)
        
        data = self.read_csv_as_dict(filename, encoding)
        
        # 验证字段
        required_fields = ['djh', 'rq', 'sr_code', 'je', 'zf_code']
        valid_records = []
        
        for record in data:
            # 检查必需字段
            if all(field in record for field in required_fields):
                valid_records.append(record)
            else:
                print(f"[CSV] 跳过无效记录：{record}")
        
        print(f"[CSV] 导入收入记录：{len(valid_records)}/{len(data)} 条有效")
        return valid_records
    
    def import_expense_records(self, filename: str, encoding: str = None) -> List[Dict]:
        """导入支出记录 CSV"""
        if encoding is None:
            encoding = self.detect_encoding(filename)
        
        data = self.read_csv_as_dict(filename, encoding)
        
        # 验证字段
        required_fields = ['djh', 'rq', 'zc_code', 'je', 'zf_code']
        valid_records = []
        
        for record in data:
            if all(field in record for field in required_fields):
                valid_records.append(record)
            else:
                print(f"[CSV] 跳过无效记录：{record}")
        
        print(f"[CSV] 导入支出记录：{len(valid_records)}/{len(data)} 条有效")
        return valid_records
    
    def export_income_records(self, records: List[Tuple], filename: str = None):
        """导出收入记录到 CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/exports/收入记录_{timestamp}.csv"
        
        headers = ["单据号", "日期", "收入类型编码", "收入类型名称", "金额", "支付方式编码", "备注"]
        
        self.write_csv(filename, headers, records)
        return filename
    
    def export_expense_records(self, records: List[Tuple], filename: str = None):
        """导出支出记录到 CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/exports/支出记录_{timestamp}.csv"
        
        headers = ["单据号", "日期", "支出类型编码", "支出类型名称", "金额", "支付方式编码", "备注"]
        
        self.write_csv(filename, headers, records)
        return filename
    
    def export_cash_flow(self, records: List[Tuple], filename: str = None):
        """导出流水账到 CSV"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/exports/收支流水账_{timestamp}.csv"
        
        headers = ["日期", "序号", "收支类型", "单据号", "收入类型", "收入金额", 
                   "支出类型", "支出金额", "余额", "支付方式", "备注"]
        
        self.write_csv(filename, headers, records)
        return filename
    
    def export_monthly_report(self, records: List[Tuple], year_month: str, filename: str = None):
        """导出月报表到 CSV"""
        if filename is None:
            filename = f"data/exports/月报表_{year_month}.csv"
        
        headers = ["账套号", "期初日期", "期末日期", "支付编码", 
                   "期初余额", "收入金额", "支出金额", "期末余额"]
        
        self.write_csv(filename, headers, records)
        return filename


# 全局 CSV 处理器实例
csv_handler = CSVHandler()
