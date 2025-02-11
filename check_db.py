import sqlite3

conn = sqlite3.connect('instance/data.db')
cursor = conn.cursor()

# 檢查表格是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cursor.fetchall())

# 檢查 users 表格結構
cursor.execute("PRAGMA table_info(users)")
print("Users table columns:", cursor.fetchall())

conn.close() 