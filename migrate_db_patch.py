import sqlite3
def migrate_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in c.fetchall()]
    try:
        if 'join_date' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN join_date TEXT")
            c.execute("UPDATE users SET join_date = date('now') WHERE join_date IS NULL")
    except Exception as e:
        print('join_date migration:', e)
    try:
        if 'last_login' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except Exception as e:
        print('last_login migration:', e)
    try:
        if 'is_active' not in columns:
            c.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    except Exception as e:
        print('is_active migration:', e)
    # Patch user_appliances for last_on_time and accumulated_on_seconds
    c.execute("PRAGMA table_info(user_appliances)")
    ua_columns = [row[1] for row in c.fetchall()]
    try:
        if 'last_on_time' not in ua_columns:
            c.execute("ALTER TABLE user_appliances ADD COLUMN last_on_time TEXT")
    except Exception as e:
        print('last_on_time migration:', e)
    try:
        if 'accumulated_on_seconds' not in ua_columns:
            c.execute("ALTER TABLE user_appliances ADD COLUMN accumulated_on_seconds INTEGER")
            c.execute("UPDATE user_appliances SET accumulated_on_seconds=0 WHERE accumulated_on_seconds IS NULL")
    except Exception as e:
        print('accumulated_on_seconds migration:', e)
    conn.commit()
    conn.close()
