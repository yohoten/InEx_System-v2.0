# -*- coding: utf-8 -*-
"""
批量重新生成所有账套的流水账(sz_table_lsz)和月报表(sz_report_srzc)
同时修复 sz_d_zt.ztmc 字段（从 xm 复制）
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'inex.db')


def fix_ztmc(conn):
    """用姓名填充 ztmc 字段"""
    cur = conn.cursor()
    cur.execute("UPDATE sz_d_zt SET ztmc = xm WHERE ztmc IS NULL OR ztmc = ''")
    affected = cur.rowcount
    conn.commit()
    print(f"[ztmc] 修复完成，更新 {affected} 条记录")


def generate_cash_flow_for_all(conn):
    """为所有账套生成流水账"""
    cur = conn.cursor()

    # 获取所有账套号
    cur.execute("SELECT zth FROM sz_d_zt")
    zth_list = [row[0] for row in cur.fetchall()]

    total_inserted = 0
    for zth in zth_list:
        # 清空该账套的旧流水账
        cur.execute("DELETE FROM sz_table_lsz WHERE zth = ?", (zth,))

        # 合并收入和支出数据
        cur.execute("""
            SELECT rq, 'SR' as srzc, djh, sr_code as code, je as srje, 0 as zcje, zf_code, bz
            FROM sz_sheet_sr WHERE zth = ?
            UNION ALL
            SELECT rq, 'ZC' as srzc, djh, zc_code as code, 0 as srje, je as zcje, zf_code, bz
            FROM sz_sheet_zc WHERE zth = ?
            ORDER BY rq, srzc DESC, djh
        """, (zth, zth))

        records = cur.fetchall()

        if not records:
            print(f"  {zth}: 无收支数据，跳过")
            continue

        balance = 0.0
        xh = 0
        for record in records:
            xh += 1
            rq, srzc, djh, code, srje, zcje, zf_code, bz = record

            if srzc == 'SR':
                balance += float(srje or 0)
            else:
                balance -= float(zcje or 0)

            cur.execute("""
                INSERT INTO sz_table_lsz (zth, rq, xh, srzc, djh, sr_code, srje, zc_code, zcje, ye, zf_code, bz)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (zth, rq, xh, srzc, djh,
                  code if srzc == 'SR' else None, srje,
                  code if srzc == 'ZC' else None, zcje,
                  round(balance, 2), zf_code, bz))

        total_inserted += xh
        if len(zth_list) <= 5 or len(zth_list) - zth_list.index(zth) <= 3:
            print(f"  {zth}: {xh} 条流水记录")
        elif zth_list.index(zth) % 10 == 0:
            print(f"  ... 进度 {zth_list.index(zth) + 1}/{len(zth_list)} ...")

    conn.commit()
    print(f"[流水账] 完成: {len(zth_list)} 个账套, 共 {total_inserted} 条记录")


def generate_monthly_report_for_all(conn):
    """为所有账套所有月份生成月报表"""
    cur = conn.cursor()

    # 获取所有账套
    cur.execute("SELECT zth FROM sz_d_zt")
    zth_list = [row[0] for row in cur.fetchall()]

    # 获取所有有数据的月份范围
    cur.execute("SELECT MIN(rq), MAX(rq) FROM sz_sheet_sr UNION ALL SELECT MIN(rq), MAX(rq) FROM sz_sheet_zc")
    ranges = cur.fetchall()
    min_date = None
    max_date = None
    for row in ranges:
        if row[0]:
            d = datetime.strptime(row[0], '%Y-%m-%d') if isinstance(row[0], str) else datetime.strptime(str(row[0]), '%Y-%m-%d')
            if min_date is None or d < min_date: min_date = d
        if row[1]:
            d = datetime.strptime(row[1], '%Y-%m-%d') if isinstance(row[1], str) else datetime.strptime(str(row[1]), '%Y-%m-%d')
            if max_date is None or d > max_date: max_date = d

    if not min_date or not max_date:
        print("[月报表] 无数据，跳过")
        return

    months = []
    current = datetime(min_date.year, min_date.month, 1)
    end = datetime(max_date.year, max_date.month, 1)
    while current <= end:
        months.append(current.strftime('%Y-%m'))
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    print(f"[月报表] 时间范围: {min_date.strftime('%Y-%m')} ~ {end.strftime('%Y-%m')}, 共 {len(months)} 个月")

    total = 0
    for zth in zth_list:
        for ym in months:
            qsrq = f"{ym}-01"
            year, month = int(ym.split('-')[0]), int(ym.split('-')[1])
            if month == 12:
                jsrq = f"{year + 1}-01-01"
            else:
                jsrq = f"{year}-{month + 1:02d}-01"

            # Delete old report
            cur.execute("DELETE FROM sz_report_srzc WHERE zth=? AND qsrq=?", (zth, qsrq))

            # Calculate by payment method
            cur.execute("""
                SELECT
                    zf_code,
                    (SELECT COALESCE(SUM(je), 0) FROM sz_sheet_sr WHERE zth = sz.zth AND zf_code = sz.zf_code AND rq < ?) -
                    (SELECT COALESCE(SUM(je), 0) FROM sz_sheet_zc WHERE zth = sz.zth AND zf_code = sz.zf_code AND rq < ?) as qcye,
                    COALESCE(SUM(CASE WHEN srzc = 'SR' THEN je END), 0) as srje,
                    COALESCE(SUM(CASE WHEN srzc = 'ZC' THEN je END), 0) as zcje
                FROM (
                    SELECT zth, zf_code, je, 'SR' as srzc FROM sz_sheet_sr WHERE zth = ? AND rq >= ? AND rq < ?
                    UNION ALL
                    SELECT zth, zf_code, je, 'ZC' as srzc FROM sz_sheet_zc WHERE zth = ? AND rq >= ? AND rq < ?
                ) sz
                GROUP BY zf_code
            """, (zth, zth, zth, qsrq, jsrq, zth, qsrq, jsrq))

            rows = cur.fetchall()
            for row in rows:
                zf_code, qcye, srje, zcje = row
                qcye = float(qcye or 0)
                srje = float(srje or 0)
                zcje = float(zcje or 0)
                qmye = round(qcye + srje - zcje, 2)

                # Check if record exists
                cur.execute("SELECT COUNT(*) FROM sz_report_srzc WHERE zth=? AND qsrq=? AND zf_code=?", (zth, qsrq, zf_code))
                if cur.fetchone()[0] == 0:
                    cur.execute("""
                        INSERT INTO sz_report_srzc (zth, qsrq, jsrq, zf_code, qcye, srje, zcje, qmye)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (zth, qsrq, jsrq, zf_code, round(qcye, 2), round(srje, 2), round(zcje, 2), qmye))
                    total += 1

    conn.commit()
    print(f"[月报表] 完成: {len(zth_list)} 个账套 × {len(months)} 个月, 共 {total} 条记录")


def main():
    print("=" * 60)
    print("  InEx System - 批量数据重建工具")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  数据库: {DB_PATH}")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"\n[ERR] 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    try:
        print("\n[1/3] 修复 ztmc 字段...")
        fix_ztmc(conn)

        print("\n[2/3] 生成流水账...")
        generate_cash_flow_for_all(conn)

        print("\n[3/3] 生成月报表...")
        generate_monthly_report_for_all(conn)

        # 验证
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sz_table_lsz")
        lsz_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sz_report_srzc")
        report_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sz_d_zt WHERE ztmc IS NOT NULL AND ztmc != ''")
        ztmc_ok = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sz_d_zt")
        zt_total = cur.fetchone()[0]

        print("\n" + "=" * 60)
        print("  验证结果")
        print("=" * 60)
        print(f"  sz_d_zt (ztmc已填充): {ztmc_ok}/{zt_total}")
        print(f"  sz_table_lsz (流水账): {lsz_count}")
        print(f"  sz_report_srzc (月报表): {report_count}")
        print(f"\n[OK] 批量重建完成!")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
