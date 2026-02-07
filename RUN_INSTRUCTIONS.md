# How to Run "Green Pulse" Project

This project requires Python, Redis, and Celery running simultaneously.

## Prerequisites
- **Python**: Installed and `venv` set up.
- **Redis**: Required for background tasks. A portable version is downloaded in `d:\project gpt\redis`.

## Running the Project
You need to run 4 separate processes (in separate terminals):

1. **Redis Server**
   ```powershell
   .\redis\redis-server.exe
   ```

2. **Celery Worker** (Handles background tasks like email/usage logging)
   ```powershell
   .\venv\Scripts\celery -A tasks.celery_app worker --loglevel=info --pool=solo
   ```
   *Note: On Windows, `--pool=solo` is required.*

3. **Celery Beat** (Schedules periodic tasks)
   ```powershell
   .\venv\Scripts\celery -A tasks.celery_app beat --loglevel=info
   ```

4. **Flask Application** (The web server)
   ```powershell
   .\venv\Scripts\python app.py
   ```

## Troubleshooting
- If Celery complains about permissions or events, ensure you use `--pool=solo`.
- If Redis is missing, download it from [Redis for Windows](https://github.com/tporadowski/redis/releases).
