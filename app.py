from flask import Flask, session, request, jsonify, render_template, redirect, url_for, flash
import sqlite3
import random
import smtplib
import time
import os
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash
from services.weather_service import get_weather
# Helper to get the current user's or admin's profile icon for navbar
def get_profile_icon():
    import sqlite3
    # User session
    if 'user' in session:
        gmail = session['user']
        db_path = os.environ.get('DATABASE_PATH', 'users.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT profile_icon FROM users WHERE gmail=?', (gmail,))
        row = c.fetchone()
        conn.close()
        if row and row['profile_icon']:
            return row['profile_icon']
        return 'icons/icon1.png'
    # Admin session (optional: you can customize admin icon)
    if 'admin' in session:
        return 'icons/icon1.png'
    # Not logged in
    return 'icons/icon1.png'
# Overuse alert email sender
def send_overuse_email(gmail, status, usage, threshold, appliance=None):
    subject = f"Green Pulse: {status.title()} Energy Usage Alert"
    appliance_info = f"\nSuspected appliance: {appliance}" if appliance else ""
    message = (
        f"Dear user,\n\n"
        f"Your energy usage has reached a {status.upper()} level.\n"
        f"Current usage: {usage} kWh\n"
        f"Threshold: {threshold} kWh"
        f"{appliance_info}\n\n"
        f"Please take action to reduce your consumption.\n\n"
        f"Thank you for using Green Pulse."
    )
    return send_email(gmail, subject, message)
import sqlite3
from services.weather_service import get_weather
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_here') # Use environment variable for production

# --- WEATHER API ENDPOINT ---
@app.route('/api/weather')
def api_weather():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    gmail = session['user']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT location FROM users WHERE gmail=?', (gmail,))
    row = c.fetchone()
    city = 'Nandyal'
    if row and row['location']:
        parts = [p.strip() for p in row['location'].split(',') if p.strip()]
        # Try to match city from location_data
        known_cities = set()
        for state in location_data.values():
            for district_cities in state.values():
                known_cities.update([c.lower() for c in district_cities])
        for part in parts:
            if part.lower() in known_cities:
                city = part
                break
        else:
            city = parts[0] if parts else city
    weather = get_weather(city)
    conn.close()
    return jsonify(weather)
# --- Robust DB Migration for Existing Users Table ---
def migrate_db():
    db_path = os.environ.get('DATABASE_PATH', 'users.db')
    conn = sqlite3.connect(db_path)
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
    conn.commit()
    conn.close()

migrate_db()


# General email sender
def send_email(gmail, subject, message):
    sender = 'greenpulsergmcet@gmail.com'
    password = 'pdemqkndubfxtosf'  # Gmail App Password
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = gmail
    print(f"[DEBUG] Attempting to send email to: {gmail}, subject: {subject}, sender: {sender}")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("[DEBUG] Connecting to SMTP server...")
            server.login(sender, password)
            print("[DEBUG] Logged in to SMTP server.")
            server.sendmail(sender, [gmail], msg.as_string())
            print(f"[DEBUG] Email sent successfully to {gmail}")
        return True
    except Exception as e:
        print(f'[ERROR] Email sending failed for {gmail}:', e)
        return False

# OTP email sender
def send_otp_email(gmail, otp):
    subject = 'Green Pulse OTP Verification'
    message = f"Your Green Pulse OTP is: {otp}\n\nPlease use this code to verify your account."
    return send_email(gmail, subject, message)

# Power goal notification email
def send_power_goal_email(gmail, goal_kwh):
    subject = 'Green Pulse: Power Goal Reached!'
    message = f"Congratulations!\n\nYou have reached your monthly power goal of {goal_kwh} kWh. Consider increasing your goal for next month!\n\nThank you for using Green Pulse."
    print(f"[DEBUG] Attempting to send power goal email to: {gmail}, goal: {goal_kwh}")
    result = send_email(gmail, subject, message)
    print(f"[DEBUG] Power goal email send result: {result}")
    return result

def send_power_goal_warning_email(gmail, goal_kwh):
    subject = 'Green Pulse: Power Goal Warning'
    message = f"Heads up!\n\nYou have already reached your monthly power goal of {goal_kwh} kWh before the month is over. Try to save more energy for the rest of the month!\n\nThank you for using Green Pulse."
    print(f"[DEBUG] Attempting to send power goal warning email to: {gmail}, goal: {goal_kwh}")
    result = send_email(gmail, subject, message)
    print(f"[DEBUG] Power goal warning email send result: {result}")
    return result

# Alarm notification email
def send_alarm_email(gmail, appliance_name):
    subject = f"Alarm: {appliance_name} Timer Complete!"
    message = (
        f"Timer for {appliance_name} completed! Please turn off your appliance.\n\n"
        "---\n"
        "This is an automated reminder from Green Pulse.\n"
        "Green Pulse helps you monitor and optimize your home energy usage, set smart alarms, and save on your electricity bills.\n"
        "Thank you for using Green Pulse!\n"
        "Contact us: greenpulsergmcet@gmail.com"
    )
    return send_email(gmail, subject, message)

# Weather alert email
def send_weather_alert_email(gmail, weather_desc):
    subject = f'Green Pulse: Weather Alert - {weather_desc}'
    message = (
        f"Bad weather condition ({weather_desc}) detected in your area. "
        "Please consider turning off sensitive electronic appliances to prevent damage from power surges or outages."
        "\n\n---\n"
        "This is an automated alert from Green Pulse.\n"
        "Stay safe!"
    )
    return send_email(gmail, subject, message)

from flask import flash

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import sqlite3
import random
import smtplib
import time
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app = Flask(__name__)
import os
app.secret_key = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_here') # Use environment variable for production

# --- API ENDPOINTS FOR USAGE DATA (for dashboard charts) ---
@app.route('/api/hourly_usage')
def api_hourly_usage():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    gmail = session['user']
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'Missing date parameter'}), 400
    conn = get_db()
    c = conn.cursor()
    hourly_usage = [0]*24
    c.execute('SELECT strftime("%H", date_time) as hour, SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=? GROUP BY hour', (gmail, date))
    for row in c.fetchall():
        hour = int(row[0])
        hourly_usage[hour] = row[1] or 0
    conn.close()
    return jsonify({'date': date, 'hourly_usage': hourly_usage})

@app.route('/api/weekly_usage')
def api_weekly_usage():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    gmail = session['user']
    start_date = request.args.get('start_date')
    if not start_date:
        return jsonify({'error': 'Missing start_date parameter'}), 400
    import datetime
    start = datetime.date.fromisoformat(start_date)
    week_dates = [(start + datetime.timedelta(days=i)).isoformat() for i in range(7)]
    conn = get_db()
    c = conn.cursor()
    daily_usage = []
    for d in week_dates:
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=?', (gmail, d))
        total = c.fetchone()[0] or 0
        daily_usage.append(total)
    conn.close()
    return jsonify({'start_date': start_date, 'week_dates': week_dates, 'daily_usage': daily_usage})

@app.route('/api/usage_data')
def api_usage_data():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    gmail = session['user']
    import datetime
    today = datetime.date.today()
    week_dates = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    conn = get_db()
    c = conn.cursor()
    # Daily usage (for weekly chart)
    daily_usage = []
    for d in week_dates:
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=?', (gmail, d))
        total = c.fetchone()[0] or 0
        daily_usage.append(total)
    # Hourly usage for today (for daily chart)
    hourly_usage = [0]*24
    c.execute('SELECT strftime("%H", date_time) as hour, SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=? GROUP BY hour', (gmail, today.isoformat()))
    for row in c.fetchall():
        hour = int(row[0])
        hourly_usage[hour] = row[1] or 0
    # Yearly usage (monthly totals)
    year = today.year
    monthly_usage = []
    for m in range(1, 13):
        month_str = f"{year}-{m:02d}"
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date LIKE ?', (gmail, f"{month_str}%"))
        total = c.fetchone()[0] or 0
        monthly_usage.append(total)
    # Growth/fall % for monthly chart
    monthly_growth = [0]
    for i in range(1, 12):
        prev = monthly_usage[i-1] or 1
        curr = monthly_usage[i]
        pct = ((curr - prev) / prev) * 100 if prev else 0
        monthly_growth.append(round(pct, 1))
    conn.close()
    return jsonify({
        'hourly_usage': hourly_usage,
        'week_dates': week_dates,
        'daily_usage': daily_usage,
        'monthly_usage': monthly_usage,
        'monthly_growth': monthly_growth
    })
import os
app.secret_key = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_here') # Use environment variable for production

# --- USER DATABASE SETUP ---
def get_db():
    db_path = os.environ.get('DATABASE_PATH', 'users.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT UNIQUE NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        location TEXT,
        profile_icon TEXT,
        role TEXT DEFAULT 'user',
        otp TEXT,
        otp_valid_until INTEGER,
        join_date TEXT DEFAULT (date('now')),
        last_login TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        ip TEXT,
        user_agent TEXT,
        login_time TEXT DEFAULT (datetime('now'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_appliances (
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
    # Migrate: add last_on_time and accumulated_on_seconds if missing
    c.execute("PRAGMA table_info(user_appliances)")
    columns = [row[1] for row in c.fetchall()]
    if 'last_on_time' not in columns:
        c.execute("ALTER TABLE user_appliances ADD COLUMN last_on_time TEXT")
    if 'accumulated_on_seconds' not in columns:
        c.execute("ALTER TABLE user_appliances ADD COLUMN accumulated_on_seconds INTEGER DEFAULT 0")
    c.execute('''CREATE TABLE IF NOT EXISTS user_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        appliance_name TEXT NOT NULL,
        date TEXT NOT NULL,
        hours_on REAL NOT NULL,
        energy_kwh REAL NOT NULL,
        FOREIGN KEY (gmail) REFERENCES users(gmail)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_alarms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        appliance_name TEXT NOT NULL,
        end_time TEXT NOT NULL,
        notified INTEGER DEFAULT 0,
        FOREIGN KEY (gmail) REFERENCES users(gmail)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        month TEXT NOT NULL,
        goal_kwh REAL NOT NULL,
        notified INTEGER DEFAULT 0,
        FOREIGN KEY (gmail) REFERENCES users(gmail)
    )''')


# --- USER REGISTRATION ROUTE ---
@app.route('/register', methods=['GET', 'POST'])
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        gmail = request.form['gmail'].strip().lower()
        username = request.form['username'].strip()
        password = request.form['password']
        location = request.form['location']
        profile_icon = request.form['profile_icon']

        conn = get_db()
        c = conn.cursor()

        # Check if user already exists
        c.execute('SELECT id FROM users WHERE gmail=?', (gmail,))
        if c.fetchone():
            conn.close()
            return render_template('register.html', error='Gmail already registered.')

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_valid_until = int(time.time()) + 600  # 10 minutes

        # Hash password and insert user
        hashed_password = generate_password_hash(password)
        c.execute('''
            INSERT INTO users (gmail, username, password, location, profile_icon, otp, otp_valid_until)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (gmail, username, hashed_password, location, profile_icon, otp, otp_valid_until))

        # Send OTP email
        if send_otp_email(gmail, otp):
            conn.commit()
            session['pending_gmail'] = gmail
            conn.close()
            return redirect(url_for('verify_otp'))
        else:
            conn.rollback()
            conn.close()
            return render_template('register.html', error='Failed to send OTP. Please try again.')
    return render_template('register.html')

# --- OTP VERIFICATION ROUTE ---
@app.route('/verify_otp', methods=['GET', 'POST'])
@app.route('/verify_otp.html', methods=['GET', 'POST'])
def verify_otp():
    gmail = session.get('pending_gmail')
    if not gmail:
        return redirect(url_for('register'))
    if request.method == 'POST':
        otp = request.form['otp']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT otp, otp_valid_until FROM users WHERE gmail=?', (gmail,))
        row = c.fetchone()
        current_time = int(time.time())
        if row and row['otp'] == otp and row['otp_valid_until'] and row['otp_valid_until'] > current_time:
            # OTP valid, clear OTP and log in
            c.execute('UPDATE users SET otp=NULL, otp_valid_until=NULL WHERE gmail=?', (gmail,))
            conn.commit()
            session['user'] = gmail
            session.pop('pending_gmail', None)
            return redirect(url_for('appliance_selection'))
        else:
            return render_template('verify_otp.html', error='Invalid or expired OTP.')
    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE gmail=?', (gmail,))
        user = c.fetchone()
        if user and check_password_hash(user['password'], password):
            # Robustly handle missing is_active for legacy users
            is_active = user['is_active'] if 'is_active' in user.keys() else 1
            if is_active == 0:
                return render_template('login.html', error='Account is deactivated.')
            session['user'] = gmail
            # Update last_login
            c.execute('UPDATE users SET last_login=datetime("now") WHERE gmail=?', (gmail,))
            # Log login history
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            c.execute('INSERT INTO login_history (gmail, ip, user_agent) VALUES (?, ?, ?)', (gmail, ip, user_agent))
            conn.commit()
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials.')
    return render_template('login.html')

# --- ADMIN LOGIN WITH OTP (Superadmin Only) ---
SUPERADMINS = ["hemanthleads@gmail.com", "23091a3243@rgmcet.edu.in"]

@app.route('/admin_login', methods=['GET', 'POST'])
@app.route('/admin_login.html', methods=['GET', 'POST'])
def admin_login():
    error = None
    step = request.args.get('step', 'email')
    if request.method == 'POST':
        if step == 'email':
            admin_gmail = request.form['admin_gmail'].strip().lower()
            if admin_gmail not in SUPERADMINS:
                error = 'Not a superadmin Gmail.'
                return render_template('admin_login.html', error=error, step='email')
            # Generate OTP and send
            otp = str(random.randint(100000, 999999))
            session['admin_otp'] = otp
            session['admin_gmail'] = admin_gmail
            send_otp_email(admin_gmail, otp)
            return render_template('admin_login.html', step='otp', admin_gmail=admin_gmail)
        elif step == 'otp':
            admin_gmail = session.get('admin_gmail')
            otp_input = request.form['otp']
            if not admin_gmail or 'admin_otp' not in session:
                error = 'Session expired. Please try again.'
                return render_template('admin_login.html', error=error, step='email')
            if otp_input == session['admin_otp']:
                session['admin'] = admin_gmail
                session.pop('admin_otp', None)
                return redirect(url_for('admin_dashboard'))
            else:
                error = 'Invalid OTP.'
                return render_template('admin_login.html', error=error, step='otp', admin_gmail=admin_gmail)
    # GET request
    return render_template('admin_login.html', step='email')

# --- ADMIN DASHBOARD ---
@app.route('/admin_dashboard')
@app.route('/admin_dashboard.html')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    # User count
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]
    # Appliance count
    c.execute('SELECT COUNT(*) FROM user_appliances')
    appliance_count = c.fetchone()[0]
    # Log count (stub, as system_logs.csv is empty)
    try:
        with open('data/system_logs.csv', 'r') as f:
            log_count = sum(1 for _ in f)
    except Exception:
        log_count = 0
    # Recent users
    c.execute('SELECT gmail, username, role FROM users ORDER BY id DESC LIMIT 10')
    recent_users = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', user_count=user_count, appliance_count=appliance_count, log_count=log_count, recent_users=recent_users)

# --- LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- FORGOT PASSWORD (OTP) ---
@app.route('/forgot_password', methods=['GET', 'POST'])
@app.route('/forgot_password.html', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        gmail = request.form['gmail']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE gmail=?', (gmail,))
        if not c.fetchone():
            return render_template('forgot_password.html', error='Gmail not found.')
        otp = str(random.randint(100000, 999999))
        send_otp_email(gmail, otp)
        c.execute('UPDATE users SET otp=?, otp_valid_until=strftime("%s","now") + 600 WHERE gmail=?', (otp, gmail))
        conn.commit()
        session['reset_gmail'] = gmail
        return redirect(url_for('reset_password_otp'))
    return render_template('forgot_password.html')

@app.route('/reset_password_otp', methods=['GET', 'POST'])
@app.route('/reset_password_otp.html', methods=['GET', 'POST'])
def reset_password_otp():
    gmail = session.get('reset_gmail')
    if not gmail:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        otp = request.form['otp']
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT otp FROM users WHERE gmail=?', (gmail,))
        row = c.fetchone()
        if row and row['otp'] == otp:
            return redirect(url_for('set_new_password'))
        else:
            return render_template('reset_password_otp.html', error='Invalid OTP.')
    return render_template('reset_password_otp.html')

@app.route('/set_new_password', methods=['GET', 'POST'])
@app.route('/set_new_password.html', methods=['GET', 'POST'])
def set_new_password():
    gmail = session.get('reset_gmail')
    if not gmail:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        hashed = generate_password_hash(password)
        c.execute('UPDATE users SET password=?, otp=NULL, otp_valid_until=NULL WHERE gmail=?', (hashed, gmail))
        conn.commit()
        session.pop('reset_gmail', None)
        return redirect(url_for('login'))
    return render_template('set_new_password.html')

# Sample data for demo. Replace with full dataset as needed.
location_data = {
    "Andhra Pradesh": {
        "Anantapur": ["Anantapur", "Hindupur", "Guntakal"],
        "Chittoor": ["Chittoor", "Tirupati", "Madanapalle"]
    },
    "Karnataka": {
        "Bangalore Urban": ["Bangalore"],
        "Mysuru": ["Mysore", "Nanjangud"]
    },
    "Maharashtra": {
        "Mumbai": ["Mumbai City", "Bandra"],
        "Pune": ["Pune", "Shivajinagar"]
    },
    "Tamil Nadu": {
        "Chennai": ["Chennai"],
        "Coimbatore": ["Coimbatore", "Pollachi"]
    },
    "Telangana": {
        "Hyderabad": ["Hyderabad", "Secunderabad"],
        "Warangal": ["Warangal", "Hanamkonda"]
    }
}

# Example state tariff slabs (customize as needed)
state_tariffs = {
    "Andhra Pradesh": [(100, 5), (100, 7), (float('inf'), 10)],
    "Karnataka": [(50, 4), (150, 6), (float('inf'), 8)],
    "Maharashtra": [(100, 6), (100, 8), (float('inf'), 12)],
    "Tamil Nadu": [(100, 4.5), (100, 6.5), (float('inf'), 9)],
    "Telangana": [(100, 5.5), (100, 7.5), (float('inf'), 11)],
}

def calculate_tariff_cost(units, state):
    slabs = state_tariffs.get(state, [(float('inf'), 8)])  # Default slab if state not found
    cost = 0
    remaining = units
    for limit, rate in slabs:
        use = min(remaining, limit)
        cost += use * rate
        remaining -= use
        if remaining <= 0:
            break
    return cost

@app.route('/get_states')
def get_states():
    return jsonify(sorted(list(location_data.keys())))

@app.route('/get_districts')
def get_districts():
    state = request.args.get('state')
    if not state or state not in location_data:
        return jsonify([])
    return jsonify(sorted(list(location_data[state].keys())))

@app.route('/get_cities')
def get_cities():
    state = request.args.get('state')
    district = request.args.get('district')
    if not state or not district or state not in location_data or district not in location_data[state]:
        return jsonify([])
    return jsonify(sorted(location_data[state][district]))


# Appliance list for the template
APPLIANCES = [
    {"id": 1, "name": "Refrigerator", "default_watts": 150},
    {"id": 2, "name": "Microwave Oven", "default_watts": 1200},
    {"id": 3, "name": "Dishwasher", "default_watts": 1000},
    {"id": 4, "name": "Toaster", "default_watts": 800},
    {"id": 5, "name": "Mixer Grinder", "default_watts": 500},
    {"id": 6, "name": "Air Conditioner", "default_watts": 1200},
    {"id": 7, "name": "Ceiling Fan", "default_watts": 75},
    {"id": 8, "name": "Room Heater", "default_watts": 1500},
    {"id": 9, "name": "Water Heater", "default_watts": 2000},
    {"id": 10, "name": "Television", "default_watts": 80},
    {"id": 11, "name": "Laptop", "default_watts": 65},
    {"id": 12, "name": "Desktop Computer", "default_watts": 150},
    {"id": 13, "name": "Water Pump/Motor", "default_watts": 750},
    {"id": 14, "name": "LED Bulb", "default_watts": 9},
    {"id": 15, "name": "Tube Light", "default_watts": 18},
    {"id": 16, "name": "Table Fan", "default_watts": 50},
    {"id": 17, "name": "Geyser", "default_watts": 2000},
    {"id": 18, "name": "Iron Box", "default_watts": 1000},
    {"id": 19, "name": "Water Purifier", "default_watts": 40},
    {"id": 20, "name": "Inverter", "default_watts": 350},
    {"id": 21, "name": "Chimney", "default_watts": 180},
]

@app.route('/appliance_selection', methods=['GET', 'POST'])
@app.route('/appliance_selection.html', methods=['GET', 'POST'])
def appliance_selection():
    if request.method == 'POST':
        selected = []
        # Only process appliances that are present in the form (for edit mode)
        for appliance in APPLIANCES:
            count = request.form.get(f"appliance_{appliance['id']}")
            watts = request.form.get(f"watts_{appliance['id']}")
            if count and int(count) > 0:
                selected.append({
                    "name": appliance["name"],
                    "count": int(count),
                    "watts": float(watts) if watts else appliance["default_watts"]
                })
        session['selected_appliances'] = selected
        return redirect(url_for('appliance_confirm'))
    # Always show the full appliance list, but prefill with previous selections if available
    selected_appliances = session.get('selected_appliances')
    prefill = {a["name"].lower(): {"count": "", "watts": ""} for a in APPLIANCES}
    if selected_appliances:
        for a in selected_appliances:
            prefill[a['name'].lower()] = {'count': str(a['count']), 'watts': str(a['watts'])}
    return render_template('appliance_selection.html', appliances=APPLIANCES, prefill=prefill)

@app.route('/appliance_confirm', methods=['GET', 'POST'])
@app.route('/appliance_confirm.html', methods=['GET', 'POST'])
def appliance_confirm():
    selected_appliances = session.get('selected_appliances', [])
    if request.method == 'POST':
        # Save appliances to user_appliances table for the logged-in user
        if 'user' in session:
            gmail = session['user']
            conn = get_db()
            c = conn.cursor()
            # Remove previous appliances for this user
            c.execute('DELETE FROM user_appliances WHERE gmail=?', (gmail,))
            # Insert new appliances
            for item in selected_appliances:
                c.execute('INSERT INTO user_appliances (gmail, name, count, watts, is_on) VALUES (?, ?, ?, ?, 0)',
                          (gmail, item['name'], item['count'], item['watts']))
            conn.commit()
            conn.close()
        return redirect(url_for('dashboard'))
    return render_template('appliance_confirm.html', selected_appliances=selected_appliances)



# --- DASHBOARD WITH WIDGETS ---

import random
@app.route('/dashboard')
@app.route('/dashboard.html')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    import datetime
    # Weather widget using OpenWeatherMap API
    try:
        from services.weather_service import get_weather
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT location FROM users WHERE gmail=?', (gmail,))
        row = c.fetchone()
        # Build a set of all known cities from location_data
        known_cities = set()
        for state in location_data.values():
            for district_cities in state.values():
                known_cities.update([c.lower() for c in district_cities])

        city = 'Nandyal'  # Default city
        if row and row['location']:
            parts = [p.strip() for p in row['location'].split(',') if p.strip()]
            for part in parts:
                if part.lower() in known_cities:
                    city = part
                    break
        weather = get_weather(city)
        conn.close()
    except Exception:
        weather = {
            'location': 'Bangalore',
            'temp_c': 28,
            'desc': 'Partly Cloudy',
            'icon': 'https://cdn-icons-png.flaticon.com/512/1163/1163661.png'
        }
    # Weather warning logic
    bad_weather_keywords = ['storm', 'rain', 'thunder', 'wind', 'hail', 'snow', 'cyclone']
    weather_warning = None
    is_bad_weather = False
    for word in bad_weather_keywords:
        if word in weather.get('desc', '').lower():
            is_bad_weather = True
            current_weather_desc = weather.get('desc')
            if session.get('weather_alert_sent_for') != current_weather_desc:
                weather_warning = 'Bad weather detected! Please turn off sensitive appliances. An alert has been sent to your email.'
                send_weather_alert_email(gmail, current_weather_desc)
                session['weather_alert_sent_for'] = current_weather_desc
            else:
                weather_warning = 'Bad weather detected! Please turn off sensitive appliances.'
            break
    if not is_bad_weather:
        session.pop('weather_alert_sent_for', None)

    # Usage data for charts
    today = datetime.date.today()
    week_dates = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    conn = get_db()
    c = conn.cursor()
    # Daily usage (for weekly chart)
    daily_usage = []
    for d in week_dates:
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=?', (gmail, d))
        total = c.fetchone()[0] or 0
        daily_usage.append(total)
    # Hourly usage for today (for daily chart)
    hourly_usage = [0]*24
    c.execute('SELECT strftime("%H", date_time) as hour, SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=? GROUP BY hour', (gmail, today.isoformat()))
    for row in c.fetchall():
        hour = int(row[0])
        hourly_usage[hour] = row[1] or 0
    # Yearly usage (monthly totals)
    year = today.year
    monthly_usage = []
    for m in range(1, 13):
        month_str = f"{year}-{m:02d}"
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date LIKE ?', (gmail, f"{month_str}%"))
        total = c.fetchone()[0] or 0
        monthly_usage.append(total)
    conn.close()
    # Growth/fall % for monthly chart
    monthly_growth = [0]
    for i in range(1, 12):
        prev = monthly_usage[i-1] or 1
        curr = monthly_usage[i]
        pct = ((curr - prev) / prev) * 100 if prev else 0
        monthly_growth.append(round(pct, 1))

    # ML Overuse Alert using real model if available
    import traceback # Import traceback for detailed error logging
    try:
        from ml_model.predict import predict_overuse
        features = daily_usage[-7:] if len(daily_usage) >= 7 else [0]* (7-len(daily_usage)) + daily_usage
        status, message, hint, usage, threshold = predict_overuse(features, return_hint=True)
        suspected_appliance = None
        if status in ("warning", "critical"):
            # Find the appliance with the highest usage for today
            conn2 = get_db()
            c2 = conn2.cursor()
            c2.execute('SELECT appliance_name, SUM(energy_kwh) as total_kwh FROM user_usage WHERE gmail=? AND date=? GROUP BY appliance_name ORDER BY total_kwh DESC LIMIT 1', (gmail, today.isoformat()))
            row = c2.fetchone()
            if row:
                suspected_appliance = row[0]
            conn2.close()
        # Format usage and threshold to 2 decimal places for display
        try:
            usage_fmt = format(float(usage), '.2f')
        except Exception:
            usage_fmt = usage
        try:
            threshold_fmt = format(float(threshold), '.2f')
        except Exception:
            threshold_fmt = threshold
        overuse_alert = {
            'status': status,
            'message': message,
            'hint': hint,
            'usage': usage_fmt,
            'threshold': threshold_fmt,
            'appliance': suspected_appliance
        }
        # Send mail alert if status is warning or critical, but only once per day
        import datetime
        alert_key = f"overuse_alert_sent_for_{datetime.date.today()}"
        if status in ("warning", "critical"):
            if session.get(alert_key) != status:
                send_overuse_email(gmail, status, usage_fmt, threshold_fmt, suspected_appliance)
                session[alert_key] = status
        else:
            # Reset alert for new day or normal status
            session.pop(alert_key, None)
    except Exception as e:
        print(f"Error predicting overuse: {e}")
        traceback.print_exc() # Print full traceback to console/logs
        overuse_alert = {
            'status': 'normal', # Default to normal if ML model fails
            'message': 'Welcome! Not enough data to predict overuse yet.',
            'hint': 'Start using your appliances to see smart alerts here.',
            'usage': format(0, '.2f'), # Default values, formatted
            'threshold': format(0, '.2f'), # Default values, formatted
            'appliance': None
        }
    # Tips logic: show based on top appliance usage
    energy_tips = [
        'Turn off appliances when not in use.',
        'Use LED bulbs to save energy.',
        'Unplug chargers when not needed.',
        'Run washing machines with full loads.',
        'Set AC to 24°C for efficiency.',
        'Clean your AC filters regularly for better efficiency.',
        'Use natural light during the day.',
        'Switch off fans and lights when leaving a room.',
        'Use a pressure cooker to save cooking energy.',
        'Defrost your fridge regularly to keep it efficient.',
        'Iron clothes in bulk to reduce repeated heating.',
        'Use smart power strips to avoid phantom loads.',
        'Dry clothes naturally instead of using a dryer.',
        'Keep doors and windows closed when AC is on.',
        'Use ceiling fans to circulate cool air.'
    ]
    env_tips = [
        'Plant a tree to offset carbon footprint.',
        'Recycle and reuse whenever possible.',
        'Reduce water wastage.',
        'Use public transport to reduce emissions.',
        'Carry a reusable bag when shopping.',
        'Avoid single-use plastics.',
        'Compost kitchen waste.',
        'Harvest rainwater for gardening.',
        'Support local and organic produce.',
        'Switch to eco-friendly cleaning products.',
        'Participate in community clean-up drives.',
        'Educate others about environmental conservation.',
        'Opt for digital receipts instead of paper.',
        'Use a bicycle for short trips.',
        'Turn off the tap while brushing your teeth.'
    ]

    # Analyze top appliance usage for today
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT appliance_name, SUM(energy_kwh) as total_kwh FROM user_usage WHERE gmail=? AND date=? GROUP BY appliance_name ORDER BY total_kwh DESC LIMIT 1', (gmail, today.isoformat()))
    row = c.fetchone()
    conn.close()
    tip_map = {
        'ac': [
            'Set AC to 24°C for efficiency.',
            'Clean your AC filters regularly for better efficiency.',
            'Keep doors and windows closed when AC is on.'
        ],
        'fridge': [
            'Defrost your fridge regularly to keep it efficient.'
        ],
        'refrigerator': [
            'Defrost your fridge regularly to keep it efficient.'
        ],
        'washing machine': [
            'Run washing machines with full loads.'
        ],
        'fan': [
            'Use ceiling fans to circulate cool air.',
            'Switch off fans and lights when leaving a room.'
        ],
        'iron': [
            'Iron clothes in bulk to reduce repeated heating.'
        ],
        'light': [
            'Use LED bulbs to save energy.',
            'Use natural light during the day.'
        ],
        'bulb': [
            'Use LED bulbs to save energy.'
        ],
        'computer': [
            'Use smart power strips to avoid phantom loads.'
        ],
        'tv': [
            'Unplug chargers when not needed.'
        ],
        'television': [
            'Unplug chargers when not needed.'
        ],
        'pump': [
            'Turn off appliances when not in use.'
        ],
        'geyser': [
            'Turn off appliances when not in use.'
        ],
        'inverter': [
            'Turn off appliances when not in use.'
        ],
        'microwave': [
            'Use a pressure cooker to save cooking energy.'
        ],
        'oven': [
            'Use a pressure cooker to save cooking energy.'
        ],
        'charger': [
            'Unplug chargers when not needed.'
        ],
        'dryer': [
            'Dry clothes naturally instead of using a dryer.'
        ]
    }
    if row and row[0]:
        appliance = row[0].lower()
        selected_tips = []
        for key, tips in tip_map.items():
            if key in appliance:
                selected_tips.extend(tips)
        if selected_tips:
            energy_tip = random.choice(selected_tips)
        else:
            energy_tip = random.choice(energy_tips)
    else:
        energy_tip = random.choice(energy_tips)
    env_tip = random.choice(env_tips)
    # Fetch user profile icon
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT profile_icon FROM users WHERE gmail=?', (gmail,))
    row = c.fetchone()
    profile_icon = row['profile_icon'] if row and row['profile_icon'] else 'icons/icon1.png'
    conn.close()
    return render_template(
        'dashboard.html',
        weather=weather,
        weather_warning=weather_warning,
        overuse_alert=overuse_alert,
        week_dates=week_dates,
        daily_usage=daily_usage,
        hourly_usage=hourly_usage,
        monthly_usage=monthly_usage,
        monthly_growth=monthly_growth,
        energy_tip=energy_tip,
        env_tip=env_tip,
        profile_icon=profile_icon
    )

# --- NAVIGATION PLACEHOLDER ROUTES ---
@app.route('/profile', methods=['GET', 'POST'])
@app.route('/profile.html', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        username = request.form.get('username')
        profile_icon = request.form.get('profile_icon')
        if username:
            c.execute('UPDATE users SET username=? WHERE gmail=?', (username, gmail))
        if profile_icon:
            c.execute('UPDATE users SET profile_icon=? WHERE gmail=?', (profile_icon, gmail))
        conn.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('profile'))
    c.execute('SELECT * FROM users WHERE gmail=?', (gmail,))
    user = c.fetchone()
    conn.close()
    # Pass profile_icon to base.html for navbar
    return render_template('profile.html', user=user, profile_icon=get_profile_icon())


@app.route('/toggle_inverter_mode', methods=['POST'])
def toggle_inverter_mode():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    session['inverter_mode'] = data.get('is_inverter_mode', False)
    return jsonify({'success': True, 'is_inverter_mode': session['inverter_mode']})

@app.route('/add_appliance', methods=['POST'])
def add_appliance():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    appliance_id = request.form.get('appliance_id')
    quantity = int(request.form.get('quantity', 1))

    appliance_to_add = next((a for a in APPLIANCES if a['id'] == int(appliance_id)), None)
    if not appliance_to_add:
        flash('Invalid appliance selected.', 'danger')
        return redirect(url_for('appliances'))

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, count FROM user_appliances WHERE gmail=? AND name=?', (gmail, appliance_to_add['name']))
    row = c.fetchone()
    if row:
        new_count = row['count'] + quantity
        c.execute('UPDATE user_appliances SET count=? WHERE id=?', (new_count, row['id']))
    else:
        c.execute('INSERT INTO user_appliances (gmail, name, count, watts, is_on) VALUES (?, ?, ?, ?, 0)',
                  (gmail, appliance_to_add['name'], quantity, appliance_to_add['default_watts']))
    conn.commit()
    conn.close()
    flash(f'{appliance_to_add["name"]} has been added to your appliances.', 'success')
    return redirect(url_for('appliances'))

@app.route('/add_custom_appliance', methods=['POST'])
def add_custom_appliance():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    name = request.form.get('name', '').strip()
    wattage = float(request.form.get('wattage', 0))

    if not name or wattage <= 0:
        flash('Invalid custom appliance details.', 'danger')
        return redirect(url_for('appliances'))

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM user_appliances WHERE gmail=? AND name=?', (gmail, name))
    if c.fetchone():
        flash('An appliance with this name already exists.', 'warning')
    else:
        c.execute('INSERT INTO user_appliances (gmail, name, count, watts, is_on) VALUES (?, ?, 1, ?, 0)',
                  (gmail, name, wattage))
        conn.commit()
        flash(f'Custom appliance "{name}" has been added.', 'success')
    conn.close()
    return redirect(url_for('appliances'))

@app.route('/appliances', methods=['GET', 'POST'])
@app.route('/appliances.html', methods=['GET', 'POST'])
def appliances():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    conn = get_db()
    c = conn.cursor()
    # Add inverter_mode column to session if not present
    if 'inverter_mode' not in session:
        session['inverter_mode'] = False
    # Handle inverter mode toggle
    if request.method == 'POST' and 'toggle_inverter' in request.form:
        session['inverter_mode'] = not session.get('inverter_mode', False)
    # Add appliance
    if request.method == 'POST' and 'add_appliance' in request.form:
        selected_name = request.form['name']
        custom_name = request.form.get('custom_name', '').strip()
        count = int(request.form['count'])
        watts = float(request.form['watts'])
        global_names = [a['name'].lower() for a in APPLIANCES]
        # Determine final appliance name
        if selected_name == '__custom__' and custom_name:
            name = custom_name
            is_custom = True
        else:
            name = selected_name
            is_custom = name.lower() not in global_names
        # Check if appliance already exists for user
        c.execute('SELECT id, count FROM user_appliances WHERE gmail=? AND name=?', (gmail, name))
        row = c.fetchone()
        if row:
            # Already present: increase count
            new_count = row['count'] + count
            c.execute('UPDATE user_appliances SET count=? WHERE id=?', (new_count, row['id']))
        else:
            # Not present: add new
            c.execute('INSERT INTO user_appliances (gmail, name, count, watts, is_on) VALUES (?, ?, ?, ?, 0)', (gmail, name, count, watts))
            # If custom, log for admin review
            if is_custom:
                c.execute('''CREATE TABLE IF NOT EXISTS custom_appliance_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gmail TEXT,
                    appliance_name TEXT,
                    watts REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')
                c.execute('INSERT INTO custom_appliance_requests (gmail, appliance_name, watts) VALUES (?, ?, ?)', (gmail, name, watts))
        conn.commit()
    # Remove appliance
    if request.method == 'POST' and 'remove_id' in request.form:
        c.execute('DELETE FROM user_appliances WHERE id=? AND gmail=?', (request.form['remove_id'], gmail))
        conn.commit()
    # Toggle appliance
    if request.method == 'POST' and 'toggle_id' in request.form:
        import datetime
        appliance_id = request.form['toggle_id']
        c.execute('SELECT is_on, last_on_time, accumulated_on_seconds, name, count, watts FROM user_appliances WHERE id=? AND gmail=?', (appliance_id, gmail))
        row = c.fetchone()
        if row:
            is_on = row['is_on']
            last_on_time = row['last_on_time']
            accumulated = row['accumulated_on_seconds'] or 0
            name = row['name']
            count = row['count']
            watts = row['watts']
            now = datetime.datetime.now()
            # Add a column to store how many units are ON (if not exists)
            try:
                c.execute('ALTER TABLE user_appliances ADD COLUMN units_on INTEGER DEFAULT 0')
            except Exception:
                pass
            if not is_on:
                # Turning ON: get units_on from form, record start time and units_on
                try:
                    units_on = int(request.form.get('units_on', count))
                except Exception:
                    units_on = count
                if units_on < 1 or units_on > count:
                    units_on = count
                c.execute('UPDATE user_appliances SET is_on=1, last_on_time=?, units_on=? WHERE id=? AND gmail=?', (now.isoformat(), units_on, appliance_id, gmail))
            else:
                # Turning OFF: calculate ON duration since last reset (last_on_time/accumulated_on_seconds)
                c.execute('SELECT units_on FROM user_appliances WHERE id=? AND gmail=?', (appliance_id, gmail))
                units_on_row = c.fetchone()
                units_on = units_on_row['units_on'] if units_on_row and units_on_row['units_on'] else count
                if last_on_time:
                    last_on = datetime.datetime.fromisoformat(last_on_time)
                    # Only use the time since last_on_time (accumulated should be 0 if periodic logger resets it)
                    duration = (now - last_on).total_seconds() + (accumulated or 0)
                    hours_on = duration / 3600
                    if hours_on > 24:
                        hours_on = 24
                    if hours_on > 0.0001:  # Only log if non-trivial
                        energy_kwh = (watts * units_on * hours_on) / 1000
                        # Insert usage record, with inverter_mode
                        c2 = get_db()
                        c2c = c2.cursor()
                        try:
                            c2c.execute('ALTER TABLE user_usage ADD COLUMN inverter_mode INTEGER DEFAULT 0')
                        except Exception:
                            pass
                        inverter_mode = 1 if session.get('inverter_mode', False) else 0
                        c2c.execute('''INSERT INTO user_usage (gmail, appliance_name, date, hours_on, energy_kwh, date_time, inverter_mode) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (gmail, name, now.date().isoformat(), hours_on, energy_kwh, now.strftime('%Y-%m-%d %H:%M:%S'), inverter_mode))
                        c2.commit()
                        c2.close()
                # Always reset ON time, accumulated, and units_on
                c.execute('UPDATE user_appliances SET is_on=0, last_on_time=NULL, accumulated_on_seconds=0, units_on=0 WHERE id=? AND gmail=?', (appliance_id, gmail))
            conn.commit()
    # Search
    search = request.args.get('search', '').strip()
    if search:
        c.execute('SELECT * FROM user_appliances WHERE gmail=? AND name LIKE ?', (gmail, f'%{search}%'))
    else:
        c.execute('SELECT * FROM user_appliances WHERE gmail=?', (gmail,))
    appliances = c.fetchall()
    # Pass global appliances for dropdown
    global_appliances = APPLIANCES
    conn.close()
    return render_template('appliances.html', appliances=appliances, search=search, global_appliances=global_appliances, inverter_mode=session.get('inverter_mode', False), profile_icon=get_profile_icon())




import datetime
@app.route('/weekly_analysis')
@app.route('/weekly_analysis.html')
def weekly_analysis():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']

    # Get the reference date from URL, default to today
    date_str = request.args.get('date', datetime.date.today().isoformat())
    try:
        ref_date = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        ref_date = datetime.date.today()

    # Calculate dates for the selected week
    start_of_week = ref_date - datetime.timedelta(days=ref_date.weekday())
    week_dates = [(start_of_week + datetime.timedelta(days=i)).isoformat() for i in range(7)]

    # Calculate dates for previous and next week buttons
    prev_week_date = (start_of_week - datetime.timedelta(days=7)).isoformat()
    next_week_start = start_of_week + datetime.timedelta(days=7)
    next_week_date = next_week_start.isoformat()

    # Check if the next week is in the future
    is_next_week_in_future = next_week_start > datetime.date.today()

    # Determine the month label for display
    month_label = start_of_week.strftime("%B %Y")
    end_of_week = start_of_week + datetime.timedelta(days=6)
    if start_of_week.month != end_of_week.month:
        month_label = f"{start_of_week.strftime('%b')} - {end_of_week.strftime('%b %Y')}"


    conn = get_db()
    c = conn.cursor()
    # Aggregate daily total kWh for the week
    daily_usage = []
    for d in week_dates:
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date=?', (gmail, d))
        total = c.fetchone()[0] or 0
        daily_usage.append(total)

    # For details of a selected day, default to the first day of the displayed week
    selected_day = request.args.get('day', week_dates[0])
    if selected_day not in week_dates:
        selected_day = week_dates[0]

    c.execute('''
        SELECT appliance_name, MIN(SUM(hours_on), 24) as hours_on, SUM(energy_kwh) as energy_kwh
        FROM user_usage
        WHERE gmail=? AND date=?
        GROUP BY appliance_name
    ''', (gmail, selected_day))
    details = c.fetchall()
    conn.close()

    return render_template(
        'weekly_analysis.html',
        week_dates=week_dates,
        daily_usage=daily_usage,
        selected_day=selected_day,
        details=details,
        prev_week_date=prev_week_date,
        next_week_date=next_week_date,
        month_label=month_label,
        is_next_week_in_future=is_next_week_in_future,
        profile_icon=get_profile_icon()
    )

import calendar
import csv
import calendar
import csv
@app.route('/my_consumption', methods=['GET', 'POST'])
@app.route('/my_consumption.html', methods=['GET', 'POST'])
def my_consumption():
    if 'user' not in session:
        return redirect(url_for('login'))

    gmail = session['user']
    today = datetime.date.today()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    conn = get_db()
    c = conn.cursor()

    # Get total kWh for the current month
    c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date BETWEEN ? AND ?',
              (gmail, first_day_of_month.isoformat(), last_day_of_month.isoformat()))
    total_kwh = c.fetchone()[0] or 0

    # Get user's state from profile
    c.execute('SELECT location FROM users WHERE gmail=?', (gmail,))
    user_row = c.fetchone()
    user_state = None
    known_states = ['andhra pradesh', 'telangana', 'karnataka', 'tamil nadu', 'kerala', 'maharashtra', 'gujarat', 'rajasthan', 'uttar pradesh', 'madhya pradesh', 'punjab', 'haryana', 'delhi', 'west bengal', 'odisha', 'bihar', 'jharkhand', 'chhattisgarh', 'assam', 'goa', 'tripura', 'manipur', 'mizoram', 'nagaland', 'meghalaya', 'arunachal pradesh', 'sikkim', 'uttarakhand', 'himachal pradesh', 'jammu and kashmir', 'ladakh']
    if user_row and user_row['location']:
        parts = [p.strip().lower() for p in user_row['location'].split(',') if p.strip()]
        for part in parts:
            if part in known_states:
                user_state = part.title()
                break
    if not user_state:
        user_state = ''

    # Hardcoded slab definitions
    ap_slab_defs = [
        {'start': 0, 'end': 30, 'rate': 1.9}, {'start': 31, 'end': 75, 'rate': 3.0},
        {'start': 76, 'end': 100, 'rate': 4.8}, {'start': 101, 'end': 200, 'rate': 5.6},
        {'start': 201, 'end': 300, 'rate': 7.1}, {'start': 301, 'end': 400, 'rate': 8.1},
        {'start': 401, 'end': None, 'rate': 9.75}
    ]
    tg_slab_defs = [
        {'start': 0, 'end': 100, 'rate': 2.5}, {'start': 101, 'end': 300, 'rate': 5.5},
        {'start': 301, 'end': None, 'rate': 8.0}
    ]

    simulated_cost = None
    sim_slabs = None

    if request.method == 'POST' and any(k.startswith('sim_slab_rate_') for k in request.form.keys()):
        sim_slabs = []
        idx = 0
        # Determine which slab definition to use for the loop
        base_slabs = ap_slab_defs if user_state.lower() == 'andhra pradesh' else tg_slab_defs
        
        while True:
            rate_key = f'sim_slab_rate_{idx}'
            if rate_key not in request.form:
                break
            
            try:
                rate = float(request.form[rate_key])
            except (ValueError, TypeError):
                rate = 0.0
            
            # Reconstruct the slab definition with the new rate
            sim_slabs.append({'start': base_slabs[idx]['start'], 'end': base_slabs[idx]['end'], 'rate': rate})
            idx += 1

        # Calculate simulated cost
        remaining = total_kwh
        cost = 0
        for slab in sim_slabs:
            rate = slab['rate']
            start = slab['start']
            end = slab['end']
            
            if end is None:
                use = remaining
            else:
                # This logic needs to be robust for start=0 and start=31 etc.
                slab_range = end - start + (1 if start > 0 else 0)
                use = min(remaining, slab_range)

            cost += use * rate
            remaining -= use
            if remaining <= 0:
                break
        simulated_cost = cost

    # Determine which slabs to use for display (either default or simulated)
    state_lc = user_state.strip().lower() if user_state else ''
    if state_lc == 'andhra pradesh':
        user_slabs = ap_slab_defs
    elif state_lc == 'telangana':
        user_slabs = tg_slab_defs
    else:
        # Fallback for other states (or if state is unknown)
        user_slabs = [{'start': 0.0, 'end': None, 'rate': 5.4}]

    # Calculate current slab index and estimated cost
    current_slab_idx = 1
    cost = 0
    remaining = total_kwh
    slab_breakdown = []
    for i, slab in enumerate(user_slabs):
        if remaining > 0:
            current_slab_idx = i + 1
        
        rate = slab['rate']
        start = slab['start']
        end = slab['end']

        if end is None:
            use = remaining
        else:
            slab_range = end - start + (1 if start > 0 else 0)
            use = min(remaining, slab_range)
        
        if use > 0:
            slab_breakdown.append(f"{use:.2f} kWh @ ₹{rate}/kWh")
        
        cost += use * rate
        remaining -= use
        if remaining <= 0:
            break
    estimated_cost = round(cost, 2)

    # Previous months usage and cost
    previous_months = []
    for i in range(1, 4):
        month = (today.replace(day=1) - datetime.timedelta(days=30 * i))
        year = month.year
        mon = month.month
        first = datetime.date(year, mon, 1)
        last = datetime.date(year, mon, calendar.monthrange(year, mon)[1])
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date BETWEEN ? AND ?',
                  (gmail, first.isoformat(), last.isoformat()))
        kwh = c.fetchone()[0] or 0
        
        # Simplified cost calculation for previous months for brevity
        prev_cost = kwh * (user_slabs[0]['rate'] if user_slabs else 5.4)

        previous_months.append({
            'month': first.strftime('%B %Y'),
            'usage': kwh,
            'cost': round(prev_cost, 2)
        })

    conn.close()

    return render_template(
        'my_consumption.html',
        total_kwh=total_kwh,
        estimated_cost=estimated_cost,
        user_state=user_state,
        user_slabs=user_slabs,
        slab_breakdown=slab_breakdown,
        previous_months=previous_months,
        ap_slab_defs=ap_slab_defs,
        tg_slab_defs=tg_slab_defs,
        current_slab_idx=current_slab_idx,
        simulated_cost=simulated_cost,
        sim_slabs=sim_slabs,  # Pass the simulated slabs back to the template
        profile_icon=get_profile_icon()
    )

import threading
import time
@app.route('/alarm', methods=['GET', 'POST'])
@app.route('/alarm.html', methods=['GET', 'POST'])
def alarm():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    conn = get_db()
    c = conn.cursor()
    # Add new alarm
    if request.method == 'POST' and 'appliance_name' in request.form:
        appliance_name = request.form['appliance_name']
        minutes = int(request.form['minutes'])
        end_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).isoformat()
        c.execute('INSERT INTO user_alarms (gmail, appliance_name, end_time) VALUES (?, ?, ?)', (gmail, appliance_name, end_time))
        conn.commit()
    # Remove alarm
    if request.method == 'POST' and 'remove_id' in request.form:
        c.execute('DELETE FROM user_alarms WHERE id=? AND gmail=?', (request.form['remove_id'], gmail))
        conn.commit()
    # List alarms
    c.execute('SELECT * FROM user_alarms WHERE gmail=? ORDER BY end_time', (gmail,))
    alarms = c.fetchall()
    # List appliances for dropdown
    c.execute('SELECT DISTINCT name FROM user_appliances WHERE gmail=?', (gmail,))
    appliances = [row['name'] for row in c.fetchall()]
    conn.close()
    return render_template('alarm.html', alarms=alarms, appliances=appliances, profile_icon=get_profile_icon())

# --- BACKGROUND ALARM CHECKER ---
def alarm_checker():
    while True:
        conn = get_db()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute('SELECT * FROM user_alarms WHERE notified=0 AND end_time<=?', (now,))
        for alarm in c.fetchall():
            send_alarm_email(alarm['gmail'], alarm['appliance_name'])
            c.execute('UPDATE user_alarms SET notified=1 WHERE id=?', (alarm['id'],))
        conn.commit()
        conn.close()
        time.sleep(60)

threading.Thread(target=alarm_checker, daemon=True).start()

@app.route('/power_goals', methods=['GET', 'POST'])
@app.route('/power_goals.html', methods=['GET', 'POST'])
def power_goals():
    if 'user' not in session:
        return redirect(url_for('login'))
    gmail = session['user']
    today = datetime.date.today()
    month_str = today.strftime('%Y-%m')
    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        goal_kwh = float(request.form['goal_kwh'])
        c.execute('SELECT id FROM user_goals WHERE gmail=? AND month=?', (gmail, month_str))
        if c.fetchone():
            c.execute('UPDATE user_goals SET goal_kwh=?, notified=0 WHERE gmail=? AND month=?', (goal_kwh, gmail, month_str))
            flash(f'Your monthly power goal has been updated to {goal_kwh} kWh.', 'success')
        else:
            c.execute('INSERT INTO user_goals (gmail, month, goal_kwh) VALUES (?, ?, ?)', (gmail, month_str, goal_kwh))
            flash(f'Your new monthly power goal is set to {goal_kwh} kWh.', 'success')
        conn.commit()
        return redirect(url_for('power_goals'))

    # GET request
    c.execute('SELECT goal_kwh, notified FROM user_goals WHERE gmail=? AND month=?', (gmail, month_str))
    row = c.fetchone()
    goal_kwh = row['goal_kwh'] if row else 0
    notified = row['notified'] if row else 0

    first_day = today.replace(day=1)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    last_day = today.replace(day=days_in_month)
    days_left = (last_day - today).days

    c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE gmail=? AND date BETWEEN ? AND ?', (gmail, first_day.isoformat(), last_day.isoformat()))
    total_kwh = c.fetchone()[0] or 0

    if goal_kwh and total_kwh >= goal_kwh and not notified:
        if today == last_day:
            print(f"[DEBUG] Power goal reached for {gmail}: {total_kwh} >= {goal_kwh} on last day of month, sending congratulatory email...")
            send_power_goal_email(gmail, goal_kwh)
        else:
            print(f"[DEBUG] Power goal reached for {gmail}: {total_kwh} >= {goal_kwh} before last day, sending warning email...")
            send_power_goal_warning_email(gmail, goal_kwh)
        c.execute('UPDATE user_goals SET notified=1 WHERE gmail=? AND month=?', (gmail, month_str))
        conn.commit()

    conn.close()
    percent = min(100, int((total_kwh / goal_kwh) * 100)) if goal_kwh > 0 else 0
    
    return render_template(
        'power_goals.html',
        goal_kwh=goal_kwh,
        total_kwh=total_kwh,
        percent=percent,
        days_left=days_left,
        profile_icon=get_profile_icon()
    )
@app.route('/about')
@app.route('/about.html')
def about():
    return render_template('about.html', profile_icon=get_profile_icon())


# --- LANDING PAGE ROUTE ---
@app.route('/')
def landing():
    return render_template('role_select.html')


# --- ADMIN ANALYTICS ---
@app.route('/admin/analytics')
def admin_analytics():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    # Total energy usage per day (last 7 days)
    import datetime
    today = datetime.date.today()
    week_dates = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    daily_totals = []
    for d in week_dates:
        c.execute('SELECT SUM(energy_kwh) FROM user_usage WHERE date=?', (d,))
        total = c.fetchone()[0] or 0
        daily_totals.append(total)
    # Top 5 appliances by total kWh
    c.execute('SELECT appliance_name, SUM(energy_kwh) as total_kwh FROM user_usage GROUP BY appliance_name ORDER BY total_kwh DESC LIMIT 5')
    top_appliances = c.fetchall()
    # Fetch custom appliance requests for admin review
    c.execute('''CREATE TABLE IF NOT EXISTS custom_appliance_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT,
        appliance_name TEXT,
        watts REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('SELECT id, gmail, appliance_name, watts, created_at FROM custom_appliance_requests ORDER BY created_at DESC')
    custom_requests = c.fetchall()
    conn.close()
    return render_template('admin_analytics.html', week_dates=week_dates, daily_totals=daily_totals, top_appliances=top_appliances, custom_requests=custom_requests, profile_icon=get_profile_icon())

# --- ADMIN LOG VIEW ---
@app.route('/admin/logs')
def admin_logs():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    # Get all admins
    c.execute("SELECT gmail FROM users WHERE role='admin'")
    admins = [row['gmail'] for row in c.fetchall()]
    logs = []
    if admins:
        placeholders = ','.join(['?'] * len(admins))
        query = f"SELECT gmail, ip, user_agent, login_time FROM login_history WHERE gmail IN ({placeholders}) ORDER BY login_time DESC"
        c.execute(query, admins)
        logs = c.fetchall()
    conn.close()
    return render_template('admin_logs.html', logs=logs, profile_icon=get_profile_icon())

# --- ADMIN USER MANAGEMENT ---

# --- ADMIN APPLIANCE MANAGEMENT ---
@app.route('/admin/appliances')
def admin_appliances():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    q = request.args.get('q', '').strip()
    conn = get_db()
    c = conn.cursor()
    query = '''SELECT a.id, a.gmail, u.username, a.name, a.count, a.watts, a.is_on
               FROM user_appliances a
               JOIN users u ON a.gmail = u.gmail
               WHERE 1=1'''
    params = []
    if q:
        query += ' AND (a.gmail LIKE ? OR u.username LIKE ? OR a.name LIKE ?)' 
        params += [f'%{q}%', f'%{q}%', f'%{q}%']
    query += ' ORDER BY a.id DESC'
    c.execute(query, params)
    appliances = c.fetchall()
    # For global appliance list management
    global_appliances = APPLIANCES
    conn.close()
    return render_template('admin_appliances.html', appliances=appliances, global_appliances=global_appliances, q=q)

# Remove appliance from a user
@app.route('/admin/remove_user_appliance/<int:appliance_id>', methods=['POST'])
def admin_remove_user_appliance(appliance_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM user_appliances WHERE id=?', (appliance_id,))
    conn.commit()
    conn.close()
    flash('User appliance removed.')
    return redirect(url_for('admin_appliances'))

# Add/remove appliances from global list (in-memory for now)
@app.route('/admin/add_global_appliance', methods=['POST'])
def admin_add_global_appliance():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    name = request.form.get('name')
    watts = request.form.get('watts')
    if name and watts:
        new_id = max([a['id'] for a in APPLIANCES]) + 1 if APPLIANCES else 1
        APPLIANCES.append({"id": new_id, "name": name, "default_watts": float(watts)})
        flash('Global appliance added.')
    return redirect(url_for('admin_appliances'))

@app.route('/admin/remove_global_appliance/<int:appliance_id>', methods=['POST'])
def admin_remove_global_appliance(appliance_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    global APPLIANCES
    APPLIANCES = [a for a in APPLIANCES if a['id'] != appliance_id]
    flash('Global appliance removed.')
    return redirect(url_for('admin_appliances'))

# --- ADMIN USER MANAGEMENT WITH FILTERS, EDIT, DEACTIVATE, LOGIN HISTORY ---
@app.route('/admin/users')
def admin_users():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    # Filters
    q = request.args.get('q', '').strip()
    role = request.args.get('role', '')
    active = request.args.get('active', '')
    conn = get_db()
    c = conn.cursor()
    # Robustly select only columns that exist
    c.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in c.fetchall()]
    select_cols = [col for col in ['id','gmail','username','role','join_date','last_login','is_active'] if col in columns]
    query = f"SELECT {', '.join(select_cols)} FROM users WHERE 1=1"
    params = []
    if q:
        query += ' AND (gmail LIKE ? OR username LIKE ?)'
        params += [f'%{q}%', f'%{q}%']
    if role:
        query += ' AND role=?'
        params.append(role)
    if active and 'is_active' in columns:
        query += ' AND is_active=?'
        params.append(1 if active == '1' else 0)
    query += ' ORDER BY id DESC'
    c.execute(query, params)
    users = c.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users, q=q, role=role, active=active, profile_icon=get_profile_icon())

# Edit user profile (username, profile icon, password reset)
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    # Prevent editing superadmin details
    c.execute('SELECT gmail FROM users WHERE id=?', (user_id,))
    user_row = c.fetchone()
    if user_row and user_row['gmail'] in SUPERADMINS:
        conn.close()
        flash('Superadmin details cannot be changed.')
        return redirect(url_for('admin_users'))
    if request.method == 'POST':
        username = request.form.get('username')
        profile_icon = request.form.get('profile_icon')
        password = request.form.get('password')
        if username:
            c.execute('UPDATE users SET username=? WHERE id=?', (username, user_id))
        if profile_icon:
            c.execute('UPDATE users SET profile_icon=? WHERE id=?', (profile_icon, user_id))
        if password:
            hashed = generate_password_hash(password)
            c.execute('UPDATE users SET password=? WHERE id=?', (hashed, user_id))
        conn.commit()
        conn.close()
        flash('User updated.')
        return redirect(url_for('admin_users'))
    c.execute('SELECT * FROM users WHERE id=?', (user_id,))
    user = c.fetchone()
    conn.close()
    return render_template('admin_edit_user.html', user=user, profile_icon=get_profile_icon())

# Deactivate/reactivate user
@app.route('/admin/deactivate_user/<int:user_id>', methods=['POST'])
def admin_deactivate_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT gmail FROM users WHERE id=?', (user_id,))
    user_row = c.fetchone()
    if user_row and user_row['gmail'] in SUPERADMINS:
        conn.close()
        flash('Superadmin cannot be deactivated.')
        return redirect(url_for('admin_users'))
    c.execute('UPDATE users SET is_active=0 WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('User deactivated.')
    return redirect(url_for('admin_users'))

@app.route('/admin/reactivate_user/<int:user_id>', methods=['POST'])
def admin_reactivate_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT gmail FROM users WHERE id=?', (user_id,))
    user_row = c.fetchone()
    if user_row and user_row['gmail'] in SUPERADMINS:
        conn.close()
        flash('Superadmin cannot be reactivated/deactivated.')
        return redirect(url_for('admin_users'))
    c.execute('UPDATE users SET is_active=1 WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('User reactivated.')
    return redirect(url_for('admin_users'))

# View login history for a user
@app.route('/admin/login_history/<int:user_id>')
def admin_login_history(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT gmail FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return 'User not found', 404
    gmail = row['gmail']
    c.execute('SELECT ip, user_agent, login_time FROM login_history WHERE gmail=? ORDER BY login_time DESC LIMIT 50', (gmail,))
    history = c.fetchall()
    conn.close()
    return render_template('admin_login_history.html', gmail=gmail, history=history)

@app.route('/debug_usage')
def debug_usage():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    gmail = session['user']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM user_usage WHERE gmail=?', (gmail,))
    usage_data = c.fetchall()
    conn.close()
    return jsonify([dict(row) for row in usage_data])

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted.')
    return redirect(url_for('admin_users'))

@app.route('/admin/toggle_role/<int:user_id>', methods=['POST'])
def admin_toggle_role(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT gmail, role FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    if row and row['gmail'] in SUPERADMINS:
        conn.close()
        flash('Superadmin role cannot be changed.')
        return redirect(url_for('admin_users'))
    if row:
        new_role = 'admin' if row['role'] == 'user' else 'user'
        c.execute('UPDATE users SET role=? WHERE id=?', (new_role, user_id))
        conn.commit()
    conn.close()
    flash('User role updated.')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':

    app.run(debug=True)
