from flask import Flask, session, jsonify
from services.weather_service import get_weather

def create_app():
    app = Flask(__name__)

    @app.route('/api/weather')
    def api_weather():
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        gmail = session['user']
        from app import get_db
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT location FROM users WHERE gmail=?', (gmail,))
        row = c.fetchone()
        city = 'Nandyal'
        if row and row['location']:
            parts = [p.strip() for p in row['location'].split(',') if p.strip()]
            known_cities = set()
            from app import location_data
            for state in location_data.values():
                for district_cities in state.values():
                    known_cities.update([c.lower() for c in district_cities])
            for part in parts:
                if part.lower() in known_cities:
                    city = part
                    break
        weather = get_weather(city)
        conn.close()
        return jsonify(weather)

    return app
