import sqlite3

# Path to your SQLite database
DB_PATH = 'users.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check if 'date_time' column exists
c.execute("PRAGMA table_info(user_usage)")
columns = [row[1] for row in c.fetchall()]

if 'date_time' not in columns:
    print("Adding 'date_time' column to user_usage table...")
    c.execute("ALTER TABLE user_usage ADD COLUMN date_time TEXT")
    conn.commit()
    print("Column added.")
else:
    print("'date_time' column already exists.")

conn.close()
