web: gunicorn --bind 0.0.0.0:$PORT app:app
worker: celery -A tasks.celery_app worker --loglevel=info
beat: celery -A tasks.celery_app beat --loglevel=info --pidfile=/tmp/celerybeat.pid