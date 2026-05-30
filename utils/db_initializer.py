# -*- coding: utf-8 -*-
"""
数据库初始化工具
仅创建数据库表结构和基础码表数据
不包含任何示例收支数据，数据由用户新增、SQL导入或连接已有数据库文件提供
"""

import sqlite3
import os
from datetime import datetime


class DatabaseInitializer:
    """数据库初始化工具"""
    
    def __init__(self, db_path: str = 'data/inex.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"[数据库] 已连接到：{self.db_path}")
            return True
        except Exception as e:
            print(f"[数据库] 连接失败：{str(e)}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("[数据库] 已断开连接")
    
    def create_tables(self):
        """创建所有数据表"""
        print("\n" + "=" * 60)
        print("步骤 1: 创建数据表结构")
        print("=" * 60)
        
        tables_sql = [
            # 收入类型码表
            '''CREATE TABLE IF NOT EXISTS sz_c_sr (
                sr_code CHAR(4) NOT NULL,
                sr_name CHAR(20),
                PRIMARY KEY (sr_code)
            )''',
            
            # 支出类型码表
            '''CREATE TABLE IF NOT EXISTS sz_c_zc (
                zc_code CHAR(4) NOT NULL,
                zc_name CHAR(20),
                PRIMARY KEY (zc_code)
            )''',
            
            # 支付方式码表
            '''CREATE TABLE IF NOT EXISTS sz_c_zf (
                zf_code CHAR(4) NOT NULL,
                zf_name CHAR(20),
                PRIMARY KEY (zf_code)
            )''',
            
            # 账套信息表
            '''CREATE TABLE IF NOT EXISTS sz_d_zt (
                zth CHAR(10) NOT NULL,
                ztmc CHAR(50),
                xh CHAR(20),
                xm CHAR(10),
                rq DATE,
                xb CHAR(2),
                csd CHAR(20),
                bj CHAR(20),
                xz CHAR(10),
                mm CHAR(10),
                bz CHAR(200),
                PRIMARY KEY (zth)
            )''',
            
            # 收入单表
            '''CREATE TABLE IF NOT EXISTS sz_sheet_sr (
                zth CHAR(10) NOT NULL,
                djh CHAR(13) NOT NULL,
                rq DATE,
                sr_code CHAR(4),
                je DECIMAL(12,2),
                zf_code CHAR(4),
                bz CHAR(200),
                PRIMARY KEY (djh)
            )''',
            
            # 支出单表
            '''CREATE TABLE IF NOT EXISTS sz_sheet_zc (
                zth CHAR(10) NOT NULL,
                djh CHAR(13) NOT NULL,
                rq DATE,
                zc_code CHAR(4),
                je DECIMAL(12,2),
                zf_code CHAR(4),
                bz CHAR(200),
                PRIMARY KEY (djh)
            )''',
            
            # 流水账表
            '''CREATE TABLE IF NOT EXISTS sz_table_lsz (
                zth CHAR(10) NOT NULL,
                rq DATE NOT NULL,
                xh INTEGER NOT NULL,
                srzc CHAR(10) NOT NULL,
                djh CHAR(13) NOT NULL,
                sr_code CHAR(4),
                srje DECIMAL(12,2),
                zc_code CHAR(4),
                zcje DECIMAL(12,2),
                ye DECIMAL(12,2),
                zf_code CHAR(4),
                bz CHAR(200),
                PRIMARY KEY (zth, rq, xh, srzc, djh)
            )''',
            
            # 月报表
            '''CREATE TABLE IF NOT EXISTS sz_report_srzc (
                zth CHAR(10) NOT NULL,
                qsrq DATE NOT NULL,
                jsrq DATE,
                zf_code CHAR(4) NOT NULL,
                qcye DECIMAL(12,2),
                srje DECIMAL(12,2),
                zcje DECIMAL(12,2),
                qmye INTEGER,
                PRIMARY KEY (zth, qsrq, zf_code)
            )''',
            
            # 预算表
            '''CREATE TABLE IF NOT EXISTS sz_budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zth CHAR(10) NOT NULL,
                budget_month CHAR(7) NOT NULL,
                budget_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(zth, budget_month)
            )''',
            
            # 预算历史表
            '''CREATE TABLE IF NOT EXISTS sz_budget_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zth CHAR(10) NOT NULL,
                budget_month CHAR(7) NOT NULL,
                old_amount DECIMAL(12,2),
                new_amount DECIMAL(12,2),
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by CHAR(20)
            )''',

            # 用户表（支持多用户注册）
            '''CREATE TABLE IF NOT EXISTS sys_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account CHAR(20) NOT NULL UNIQUE,
                password_hash CHAR(100) NOT NULL,
                display_name CHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )''',

            # 审计日志表
            '''CREATE TABLE IF NOT EXISTS sys_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account CHAR(20) NOT NULL,
                action CHAR(50) NOT NULL,
                target CHAR(100),
                detail TEXT,
                ip_address CHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        for i, sql in enumerate(tables_sql, 1):
            try:
                self.cursor.execute(sql)
                table_name = sql.split()[5] if len(sql.split()) > 5 else f"表{i}"
                print(f"  ✅ {table_name} 创建成功")
            except Exception as e:
                print(f"  ❌ {sql.split()[5] if len(sql.split()) > 5 else '未知表'} 创建失败：{str(e)}")
                return False
        
        self.conn.commit()
        print("\n✅ 所有数据表创建完成")
        return True
    
    def init_code_tables(self):
        """初始化码表数据"""
        print("\n" + "=" * 60)
        print("步骤 2: 初始化码表数据")
        print("=" * 60)
        
        # 清空旧数据
        self.cursor.execute("DELETE FROM sz_c_sr")
        self.cursor.execute("DELETE FROM sz_c_zc")
        self.cursor.execute("DELETE FROM sz_c_zf")
        
        # 收入类型
        income_types = [
            ('01', '生活费'),
            ('02', '助学贷款'),
            ('03', '奖学金'),
            ('04', '补助'),
            ('05', '其他收入')
        ]
        
        for code, name in income_types:
            self.cursor.execute(
                "INSERT INTO sz_c_sr (sr_code, sr_name) VALUES (?, ?)",
                (code, name)
            )
        print(f"  ✅ 收入类型：{len(income_types)} 条")
        
        # 支出类型
        expense_types = [
            ('01', '餐饮费'),
            ('02', '通讯费'),
            ('03', '学习资料'),
            ('04', '购物'),
            ('05', '交通费'),
            ('06', '水电费'),
            ('07', '其他支出')
        ]
        
        for code, name in expense_types:
            self.cursor.execute(
                "INSERT INTO sz_c_zc (zc_code, zc_name) VALUES (?, ?)",
                (code, name)
            )
        print(f"  ✅ 支出类型：{len(expense_types)} 条")
        
        # 支付方式
        payment_methods = [
            ('01', '现金'),
            ('02', '银行存款'),
            ('03', '微信'),
            ('04', '支付宝'),
            ('05', '其他支付方式')
        ]
        
        for code, name in payment_methods:
            self.cursor.execute(
                "INSERT INTO sz_c_zf (zf_code, zf_name) VALUES (?, ?)",
                (code, name)
            )
        print(f"  ✅ 支付方式：{len(payment_methods)} 条")
        
        self.conn.commit()
        print("\n✅ 码表数据初始化完成")
        return True
    
    def init_account_info(self):
        """初始化默认账套信息"""
        print("\n" + "=" * 60)
        print("步骤 3: 初始化默认账套信息")
        print("=" * 60)
        
        # 清空旧数据
        self.cursor.execute("DELETE FROM sz_d_zt")
        
        # 插入默认账套
        account_data = (
            '2501033401',  # 账套号
            '12607320270457',  # 学号
            '滕宇豪',  # 姓名
            '2004-05-23',  # 日期
            '男',  # 性别
            '江苏',  # 城市
            '大数据与财务管理03班',  # 班级
            '34',  # 小组
            'admin0457',  # 密码
            '/'  # 备注
        )
        
        self.cursor.execute('''
            INSERT INTO sz_d_zt (zth, xh, xm, rq, xb, csd, bj, xz, mm, bz)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', account_data)
        
        self.conn.commit()
        print("  ✅ 默认账套：2501033401 - 滕宇豪")
        print("\n✅ 账套信息初始化完成")
        return True
    
    def verify_data(self):
        """验证数据完整性"""
        print("\n" + "=" * 60)
        print("步骤 4: 验证数据完整性")
        print("=" * 60)
        
        checks = [
            ("收入类型", "SELECT COUNT(*) FROM sz_c_sr"),
            ("支出类型", "SELECT COUNT(*) FROM sz_c_zc"),
            ("支付方式", "SELECT COUNT(*) FROM sz_c_zf"),
            ("账套信息", "SELECT COUNT(*) FROM sz_d_zt"),
            ("收入记录", "SELECT COUNT(*) FROM sz_sheet_sr"),
            ("支出记录", "SELECT COUNT(*) FROM sz_sheet_zc"),
            ("流水账", "SELECT COUNT(*) FROM sz_table_lsz"),
            ("月报表", "SELECT COUNT(*) FROM sz_report_srzc"),
        ]
        
        all_ok = True
        for name, sql in checks:
            self.cursor.execute(sql)
            count = self.cursor.fetchone()[0]
            status = "✅" if count > 0 else "⚠️"
            print(f"  {status} {name}：{count} 条")
            if count == 0 and name not in ["流水账", "月报表"]:
                all_ok = False
        
        return all_ok
    
    def initialize_database(self):
        """
        完整初始化数据库（仅创建表结构和基础码表）
        
        注意：此方法不会导入任何示例收支数据
        用户可以通过以下方式添加数据：
        1. 在程序界面中手动新增收支记录
        2. 通过 SQL 脚本导入数据
        3. 连接已有的 .db 数据库文件
        """
        print("=" * 70)
        print("           收支管理系统 - 数据库初始化工具")
        print("=" * 70)
        print(f"\n数据库路径：{self.db_path}")
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 连接数据库
            if not self.connect():
                return False
            
            # 创建表结构
            if not self.create_tables():
                return False
            
            # 初始化码表
            if not self.init_code_tables():
                return False
            
            # 初始化账套
            if not self.init_account_info():
                return False
            
            # 验证数据
            if not self.verify_data():
                print("\n⚠️ 部分数据验证未通过，请检查")
            
            print("\n" + "=" * 70)
            print("           ✅ 数据库初始化完成！")
            print("=" * 70)
            print(f"\n完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\n📊 数据结构:")
            print("  - 收入类型：5 种（已预置）")
            print("  - 支出类型：7 种（已预置）")
            print("  - 支付方式：5 种（已预置）")
            print("  - 账套信息：1 个（2501033401）")
            print("  - 收支记录：0 条（等待用户添加）")
            print("  - 流水账：待生成")
            print("  - 月报表：待生成")
            
            print("\n🔐 登录信息:")
            print("  - 账套号：2501033401")
            print("  - 密码：admin0457")
            
            print("\n💡 提示:")
            print("  1. 运行 python main.py 启动程序")
            print("  2. 在程序中通过界面新增收支数据")
            print("  3. 或通过 SQL 脚本导入数据")
            print("  4. 或导入现有的 .db 数据库文件")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 初始化失败：{str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()


def main():
    """主函数"""
    print("\n📝 数据库初始化 - 仅创建表结构和基础码表\n")
    print("   不会导入任何示例收支数据")
    print("   数据由用户通过界面新增、SQL导入或连接已有数据库文件提供\n")
    
    initializer = DatabaseInitializer('data/inex.db')
    initializer.initialize_database()


if __name__ == '__main__':
    main()
