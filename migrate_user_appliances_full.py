import sqlite3

def migrate_user_appliances_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # 1. Create new table with correct schema
    c.execute('''CREATE TABLE IF NOT EXISTS user_appliances_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        name TEXT NOT NULL,
        count INTEGER NOT NULL,
        watts REAL NOT NULL,
        is_on INTEGER DEFAULT 0,
        last_on_time TEXT,
        accumulated_on_seconds INTEGER DEFAULT 0,
        FOREIGN KEY (gmail) REFERENCES users(gmail)
    )''')
    # 2. Copy data from old table to new table
    c.execute('SELECT id, gmail, name, count, watts, is_on FROM user_appliances')
    for row in c.fetchall():
        c.execute('''INSERT INTO user_appliances_new (id, gmail, name, count, watts, is_on, last_on_time, accumulated_on_seconds)
                     VALUES (?, ?, ?, ?, ?, ?, NULL, 0)''', row)
    # 3. Drop old table
    c.execute('DROP TABLE user_appliances')
    # 4. Rename new table
    c.execute('ALTER TABLE user_appliances_new RENAME TO user_appliances')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate_user_appliances_table()
    print('user_appliances table migrated successfully.')
