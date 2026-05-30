# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 sz_d_zt 表添加 ztmc（账套名称）字段

执行方式：python utils/migrate_add_ztmc.py

注意：执行前请备份 data/inex.db 文件
"""

import sqlite3
import os


def migrate_database(db_path='data/inex.db'):
    """为 sz_d_zt 表添加 ztmc 字段"""
    
    print("=" * 70)
    print("           数据库迁移：添加账套名称字段")
    print("=" * 70)
    print(f"\n数据库路径：{db_path}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"\n❌ 错误：数据库文件不存在：{db_path}")
        return False
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ 数据库连接成功")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(sz_d_zt)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'ztmc' in columns:
            print("✅ ztmc 字段已存在，无需迁移")
            return True
        
        print("📝 开始添加 ztmc 字段...")
        
        # 添加 ztmc 字段
        cursor.execute("ALTER TABLE sz_d_zt ADD COLUMN ztmc CHAR(50)")
        conn.commit()
        print("✅ 字段添加成功")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(sz_d_zt)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'ztmc' in columns:
            print("✅ 验证通过：ztmc 字段已成功添加")
            
            # 显示当前账套信息
            cursor.execute("SELECT zth, ztmc, xm FROM sz_d_zt")
            accounts = cursor.fetchall()
            
            if accounts:
                print(f"\n📊 当前账套信息（共 {len(accounts)} 个）：")
                for zth, ztmc, xm in accounts:
                    display_name = ztmc if ztmc else xm
                    print(f"   - 账套号：{zth} | 名称：{display_name}")
            
            print("\n" + "=" * 70)
            print("           ✅ 迁移完成！")
            print("=" * 70)
            print("\n💡 提示：")
            print("  1. 现在可以在个人中心修改账套名称")
            print("  2. 建议重启应用程序以应用更改")
            
            return True
        else:
            print("❌ 验证失败：ztmc 字段未找到")
            return False
            
    except sqlite3.Error as e:
        print(f"\n❌ 数据库错误：{str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ 迁移失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
            print("\n🔒 数据库连接已关闭")


def main():
    """主函数"""
    print("\n⚠️ 重要提示：")
    print("  在执行迁移前，请务必备份数据库文件！")
    print("  备份命令：copy data\\inex.db data\\inex.db.backup\n")
    
    response = input("是否继续执行迁移？(y/n): ")
    
    if response.lower() == 'y':
        success = migrate_database()
        if success:
            print("\n✅ 迁移成功完成！")
        else:
            print("\n❌ 迁移失败，请检查错误信息")
    else:
        print("\n❌ 已取消迁移")


if __name__ == '__main__':
    main()
