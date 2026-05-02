import sqlite3
import random
from datetime import datetime, timedelta

# 1.データベースに接続
conn = sqlite3.connect('spending_data.db')
cursor = conn.cursor()

# テーブルが存在しない場合は作成する
cursor.execute('''
    CREATE TABLE IF NOT EXISTS monthly_expenses(
        year_month INTEGER PRIMARY KEY,
        food INTEGER,
        transport INTEGER,
        hobby INTEGER,
        other INTEGER
    )
''')

# 2. 240か月（20年) 分のデータを作成
start_year = datetime(2006, 5, 1)
start_month = 5
print("データ生成中...")

for i in range(240):
    total_months = (start_month - 1) + i
    year = start_year + (total_months // 12)
    month = (total_months % 12) + 1

    #形式を整えて数値化(例: 200605)
    ym_key = int(f"{year}{month:02d}")

    # ランダムな支出データ(平均的な数値を設定)
    food = random.randint(30000, 50000)
    transport = random.randint(5000, 15000)
    hobby = random.randint(10000, 30000)
    other = random.randint(10000, 40000)

    #挿入（既にある場合は上書き）
    cursor.execute('''
        INSERT OR REPLACE INTO monthly_expenses (year_month, food, transport, hobby, other)
        VALUES (?,?,?,?,?)
    ''', (ym_key, food, transport, hobby, other))

conn.commit()
conn.close()
print("完了！240か月分のデータがDBに書き込まれました。")
