# Deploying to Render

Your project is now configured for deployment on Render.com with:
- **Web Service**: Flask application.
- **Worker Service**: Celery worker for background tasks.
- **Redis**: Required for communication between Flask and Celery.
- **Persistent Disk**: To save your SQLite database (`users.db`).

## Steps to Deploy

1. **Push to GitHub**
   - Create a new repository on GitHub.
   - Push your code:
     ```bash
     git init
     git add .
     git commit -m "Prepare for Render deployment"
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
     git push -u origin main
     ```

2. **Connect to Render**
   - Go to [dashboard.render.com](https://dashboard.render.com).
   - Click **New +** -> **Blueprint**.
   - Connect your GitHub repository.
   - Render will detect `render.yaml` and show you the resources to be created.

3. **Important Configuration Notes**
   - **Costs**: The configuration uses a **Persistent Disk** (required for SQLite) and a **Redis** instance. These may successfully deploy on the free tier initially, but persistently storing data usually requires a paid "Starter" plan for the services.
   - **Environment Variables**: The `render.yaml` automatically sets `DATABASE_PATH` and `REDIS_URL`. You don't need to add them manually.

## Database Note
Since we are using SQLite with a Persistent Disk, your database is saved in `/data/users.db`. 
- **Warning**: If you delete the disk or the service, the database is lost.
- **Backup**: You can SSH into the service on Render to download `users.db` if needed.
