#!/bin/bash
# Start Celery Worker and Beat in the background
celery -A tasks.celery_app worker --loglevel=info --beat &

# Start Gunicorn (The Web Server) in the foreground
exec gunicorn app:app
