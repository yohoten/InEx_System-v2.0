# -*- coding: utf-8 -*-
"""
SQL方言适配器
统一不同数据库的SQL语法差异，实现跨数据库兼容
"""

import logging

logger = logging.getLogger('SQLDialect')


class SQLDialectAdapter:
    """SQL方言适配器 - 统一不同数据库的SQL语法差异"""
    
    @staticmethod
    def date_format(db_type, column, format_str='%Y-%m'):
        """
        日期格式化适配
        
        Args:
            db_type: 数据库类型 ('SQLite', 'MySQL', 'Sybase')
            column: 日期列名
            format_str: 格式字符串 (%Y-%m, %Y, %Y-%m-%d)
        
        Returns:
            适配后的SQL表达式
        """
        format_map = {
            'SQLite': {
                '%Y-%m': "strftime('%Y-%m', {col})",
                '%Y': "strftime('%Y', {col})",
                '%Y-%m-%d': "strftime('%Y-%m-%d', {col})",
                '%m': "strftime('%m', {col})",
            },
            'MySQL': {
                '%Y-%m': "DATE_FORMAT({col}, '%Y-%m')",
                '%Y': "DATE_FORMAT({col}, '%Y')",
                '%Y-%m-%d': "DATE_FORMAT({col}, '%Y-%m-%d')",
                '%m': "DATE_FORMAT({col}, '%m')",
            },
            'Sybase': {
                '%Y-%m': "CONVERT(VARCHAR(7), {col}, 120)",
                '%Y': "CONVERT(VARCHAR(4), {col}, 120)",
                '%Y-%m-%d': "CONVERT(VARCHAR(10), {col}, 120)",
                '%m': "MONTH({col})",
            }
        }
        
        # 标准化db_type名称
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        template = format_map.get(normalized_type, format_map['SQLite']).get(format_str)
        if not template:
            logger.warning(f"不支持的格式: {format_str}，使用默认")
            template = format_map[normalized_type]['%Y-%m']
        
        return template.format(col=column)
    
    @staticmethod
    def auto_increment(db_type):
        """自增主键语法适配"""
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        syntax = {
            'SQLite': 'AUTOINCREMENT',
            'MySQL': 'AUTO_INCREMENT',
            'Sybase': 'DEFAULT AUTOINCREMENT',
        }
        return syntax.get(normalized_type, 'AUTOINCREMENT')
    
    @staticmethod
    def limit_offset(db_type, limit, offset=0):
        """分页查询语法适配"""
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        if normalized_type in ('SQLite', 'MySQL'):
            return f"LIMIT {limit} OFFSET {offset}"
        elif normalized_type == 'Sybase':
            # Sybase需要使用TOP和ROW_NUMBER
            if offset == 0:
                return f"TOP {limit}"
            else:
                # 复杂分页需用子查询，这里返回标记
                return f"__SYBASE_PAGING__{limit}__{offset}__"
    
    @staticmethod
    def apply_sybase_paging(sql, limit, offset):
        """应用Sybase分页（需在查询外层包装）"""
        # Sybase复杂分页示例
        return f"""
            SELECT * FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY rq DESC) AS row_num, *
                FROM ({sql}) AS subquery
            ) AS paged
            WHERE row_num BETWEEN {offset + 1} AND {offset + limit}
        """
    
    @staticmethod
    def current_timestamp(db_type):
        """当前时间戳函数适配"""
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        functions = {
            'SQLite': "datetime('now')",
            'MySQL': "NOW()",
            'Sybase': "GETDATE()",
        }
        return functions.get(normalized_type, "NOW()")
    
    @staticmethod
    def ifnull(db_type, expr, default):
        """空值处理函数适配"""
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        functions = {
            'SQLite': f"IFNULL({expr}, {default})",
            'MySQL': f"IFNULL({expr}, {default})",
            'Sybase': f"ISNULL({expr}, {default})",
        }
        return functions.get(normalized_type, f"COALESCE({expr}, {default})")
    
    @staticmethod
    def concat(db_type, *args):
        """字符串拼接适配"""
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        if normalized_type in ('SQLite', 'MySQL'):
            return f"CONCAT({', '.join(args)})"
        elif normalized_type == 'Sybase':
            return ' + '.join(args)
    
    @staticmethod
    def year_month_groupby(db_type, date_column):
        """按年月分组适配"""
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        
        if normalized_type == 'SQLite':
            return f"strftime('%Y-%m', {date_column})"
        elif normalized_type == 'MySQL':
            return f"DATE_FORMAT({date_column}, '%Y-%m')"
        elif normalized_type == 'Sybase':
            return f"CONVERT(VARCHAR(7), {date_column}, 120)"
    
    @staticmethod
    def _normalize_db_type(db_type):
        """标准化数据库类型名称"""
        db_type_lower = db_type.lower()
        
        if 'sqlite' in db_type_lower:
            return 'SQLite'
        elif 'mysql' in db_type_lower:
            return 'MySQL'
        elif 'sybase' in db_type_lower or 'anywhere' in db_type_lower:
            return 'Sybase'
        else:
            logger.warning(f"未知数据库类型: {db_type}，默认使用SQLite语法")
            return 'SQLite'
    
    @staticmethod
    def build_compatible_query(base_sql, db_type, params=None):
        """
        构建兼容的SQL查询
        
        Args:
            base_sql: 基础SQL模板（使用占位符）
            db_type: 数据库类型
            params: 参数字典
        
        Returns:
            适配后的SQL语句
        """
        normalized_type = SQLDialectAdapter._normalize_db_type(db_type)
        sql = base_sql
        
        # 替换占位符
        if params:
            for key, value in params.items():
                placeholder = f"{{{key}}}"
                if callable(value):
                    # 如果是函数，调用它并传入db_type
                    sql = sql.replace(placeholder, value(normalized_type))
                else:
                    sql = sql.replace(placeholder, str(value))
        
        # 处理Sybase特殊分页
        if normalized_type == 'Sybase' and '__SYBASE_PAGING__' in sql:
            import re
            match = re.search(r'__SYBASE_PAGING__(\d+)__(\d+)__', sql)
            if match:
                limit = int(match.group(1))
                offset = int(match.group(2))
                sql = sql.replace(match.group(0), '')
                sql = SQLDialectAdapter.apply_sybase_paging(sql, limit, offset)
        
        return sql


# 使用示例
if __name__ == "__main__":
    # 测试SQL方言适配
    adapter = SQLDialectAdapter()
    
    print("=" * 60)
    print("SQL方言适配器测试")
    print("=" * 60)
    
    # 测试日期格式化
    print("\n1. 日期格式化适配:")
    for db_type in ['SQLite', 'MySQL', 'Sybase']:
        result = adapter.date_format(db_type, 'rq', '%Y-%m')
        print(f"  {db_type:10s}: {result}")
    
    # 测试分页
    print("\n2. 分页查询适配:")
    for db_type in ['SQLite', 'MySQL', 'Sybase']:
        result = adapter.limit_offset(db_type, 10, 20)
        print(f"  {db_type:10s}: {result}")
    
    # 测试空值处理
    print("\n3. 空值处理适配:")
    for db_type in ['SQLite', 'MySQL', 'Sybase']:
        result = adapter.ifnull(db_type, 'amount', '0')
        print(f"  {db_type:10s}: {result}")
    
    # 测试构建兼容查询
    print("\n4. 构建兼容查询:")
    template = """
        SELECT 
            {date_func} as month,
            {ifnull_func} as total
        FROM sz_table_lsz
        WHERE zth=?
        GROUP BY {date_func}
        {limit_clause}
    """
    
    params = {
        'date_func': lambda db_type: adapter.year_month_groupby(db_type, 'rq'),
        'ifnull_func': lambda db_type: adapter.ifnull(db_type, 'SUM(srje)', '0'),
        'limit_clause': lambda db_type: adapter.limit_offset(db_type, 12, 0),
    }
    
    for db_type in ['SQLite', 'MySQL', 'Sybase']:
        sql = adapter.build_compatible_query(template, db_type, params)
        print(f"\n  {db_type}:")
        print(f"  {sql[:200]}...")
