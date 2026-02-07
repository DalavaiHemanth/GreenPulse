import requests

API_KEY = '9bf46d04e890b1c1f39d7100cf2cbdf3'  # Replace with your real API key

def get_weather(city):
	"""
	Fetch current weather for a city using OpenWeatherMap API.
	Returns a dict with keys: temp_c, desc, icon, location
	"""
	url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'
	try:
		resp = requests.get(url, timeout=5)
		data = resp.json()
		weather = {
			'location': data['name'],
			'temp_c': int(data['main']['temp']),
			'desc': data['weather'][0]['description'].title(),
			'icon': f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
		}
		return weather
	except Exception as e:
		return {
			'location': city,
			'temp_c': '--',
			'desc': 'Unavailable',
			'icon': 'https://cdn-icons-png.flaticon.com/512/1163/1163661.png'
		}
