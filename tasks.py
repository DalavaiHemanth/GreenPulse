from celery import Celery
import sqlite3
import datetime

import os

celery_app = Celery('tasks', broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

@celery_app.task
def log_appliance_usage():
    db_path = os.environ.get('DATABASE_PATH', 'users.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    now = datetime.datetime.now()
    # Get all appliances that are ON
    c.execute('SELECT id, gmail, name, count, watts, last_on_time, accumulated_on_seconds FROM user_appliances WHERE is_on=1')
    for row in c.fetchall():
        appliance_id, gmail, name, count, watts, last_on_time, accumulated = row
        if last_on_time:
            # Log incremental usage for the last 30 seconds
            interval_kwh = (watts * count * 30 / 3600) / 1000
            c2 = conn.cursor()
            c2.execute('''INSERT INTO user_usage (gmail, appliance_name, date, hours_on, energy_kwh, date_time) VALUES (?, ?, ?, ?, ?, ?)''',
                (gmail, name, now.date().isoformat(), 30/3600, interval_kwh, now.strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
    conn.close()

# Celery beat schedule
celery_app.conf.beat_schedule = {
    'log-usage-every-30-seconds': {
        'task': 'tasks.log_appliance_usage',
        'schedule': 30.0,
    },
}
celery_app.conf.timezone = 'UTC'
