import sqlite3

conn = sqlite3.connect('study_agent_info.db')
cursor = conn.cursor()

# 先检查表是否存在,如果存在则删除
cursor.execute("DROP TABLE IF EXISTS user_info")

# 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stuID TEXT NOT NULL UNIQUE,
    stuName TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_history TEXT,
    knowledge_framework TEXT,
    learn_process TEXT
)
''')

conn.commit()
conn.close()