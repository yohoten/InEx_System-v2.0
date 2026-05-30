# -*- coding: utf-8 -*-
"""
数据库连接测试与修复工具
用于诊断和修复数据库连接问题
"""

import sqlite3
import os
import sys


def check_database_file(db_path):
    """检查数据库文件是否存在且有效"""
    print(f"\n{'='*60}")
    print(f"检查数据库文件: {db_path}")
    print(f"{'='*60}")
    
    # 1. 检查文件是否存在
    if not os.path.exists(db_path):
        print(f"❌ 文件不存在: {db_path}")
        return False
    
    print(f"✅ 文件存在")
    
    # 2. 检查文件大小
    file_size = os.path.getsize(db_path)
    print(f"📊 文件大小: {file_size / 1024:.2f} KB")
    
    if file_size == 0:
        print("❌ 文件大小为0，可能是空文件或已损坏")
        return False
    
    # 3. 尝试连接数据库
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 4. 检查是否可以执行查询
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ 数据库连接成功")
        print(f"📋 数据表数量: {len(tables)}")
        
        if tables:
            print("\n数据表列表:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} 条记录")
        
        conn.close()
        print(f"\n✅ 数据库文件正常")
        return True
        
    except sqlite3.DatabaseError as e:
        print(f"❌ 数据库错误: {str(e)}")
        print(f"💡 可能原因:")
        print(f"   1. 文件已损坏")
        print(f"   2. 不是有效的SQLite数据库文件")
        print(f"   3. 文件正在被其他程序占用")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {str(e)}")
        return False


def list_available_databases(data_dir='data'):
    """列出所有可用的数据库文件"""
    print(f"\n{'='*60}")
    print(f"可用的数据库文件")
    print(f"{'='*60}")
    
    if not os.path.exists(data_dir):
        print(f"❌ 目录不存在: {data_dir}")
        return []
    
    db_files = [f for f in os.listdir(data_dir) if f.endswith('.db')]
    
    if not db_files:
        print(f"⚠️  未找到任何 .db 文件")
        return []
    
    print(f"\n找到 {len(db_files)} 个数据库文件:\n")
    
    available_dbs = []
    for db_file in sorted(db_files):
        db_path = os.path.join(data_dir, db_file)
        file_size = os.path.getsize(db_path)
        
        # 快速检查是否有效
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            
            status = "✅ 有效" if result else "⚠️  空数据库"
            available_dbs.append(db_path)
        except Exception as e:
            status = f"❌ 无效/损坏 ({e})"
        
        print(f"  {status} | {db_file:30s} | {file_size / 1024:8.2f} KB")
    
    return available_dbs


def fix_config_db_path(config_path='config.json', correct_db_path=None):
    """修复配置文件中的数据库路径"""
    import json
    
    print(f"\n{'='*60}")
    print(f"修复配置文件中的数据库路径")
    print(f"{'='*60}")
    
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 使用正确的配置结构
        db_config = config_data.get('database', {})
        current_db = db_config.get('path', '') if isinstance(db_config, dict) else ''
        if current_db:
            print(f"\n{'='*60}")
            print(f"当前配置的数据库")
            print(f"{'='*60}")
            is_valid = check_database_file(current_db)
            
            if not is_valid:
                print(f"\n⚠️  当前配置的数据库无效！")
                choice = input("\n是否自动修复配置？(y/n): ").strip().lower()
                if choice == 'y':
                    fix_config_db_path(config_path)
    except Exception as e:
        print(f"❌ 修复配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "🔧 " * 20)
    print("数据库连接测试与修复工具")
    print("🔧 " * 20)
    
    # 1. 列出所有可用的数据库
    available_dbs = list_available_databases()
    
    if not available_dbs:
        print("\n❌ 没有可用的数据库文件，请先运行数据库初始化")
        print("   命令: python utils/db_initializer.py")
        return
    
    # 2. 检查当前配置的数据库
    config_path = 'config.json'
    if os.path.exists(config_path):
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 使用正确的配置结构
        db_config = config_data.get('database', {})
        current_db = db_config.get('path', '') if isinstance(db_config, dict) else ''
        if current_db:
            print(f"\n{'='*60}")
            print(f"当前配置的数据库")
            print(f"{'='*60}")
            is_valid = check_database_file(current_db)
            
            if not is_valid:
                print(f"\n⚠️  当前配置的数据库无效！")
                choice = input("\n是否自动修复配置？(y/n): ").strip().lower()
                if choice == 'y':
                    fix_config_db_path(config_path)
    else:
        print(f"\n⚠️  配置文件不存在: {config_path}")
    
    print(f"\n{'='*60}")
    print(f"操作完成")
    print(f"{'='*60}")
    print("\n💡 提示:")
    print("   1. 如果数据库文件损坏，可以删除后重新初始化")
    print("   2. 命令: del data\\inex.db && python utils/db_initializer.py")
    print("   3. 或者手动在系统设置中选择正确的数据库文件")


if __name__ == '__main__':
    main()
