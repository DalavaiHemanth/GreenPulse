import sqlite3

def patch_old_usage_data():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Find all records with hours_on > 24
    c.execute('SELECT id, hours_on FROM user_usage WHERE hours_on > 24')
    rows = c.fetchall()
    for row in rows:
        record_id, hours_on = row
        capped_hours = 24
        # Update only hours_on
        c.execute('UPDATE user_usage SET hours_on=? WHERE id=?', (capped_hours, record_id))
    conn.commit()
    conn.close()
    print(f"Patched {len(rows)} records with hours_on > 24.")

if __name__ == "__main__":
    patch_old_usage_data()
