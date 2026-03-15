# Ibyco — Docker Deployment Guide

## 📁 Files
| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build for the Flask app |
| `docker-compose.yml` | Orchestrates Flask app + Redis |
| `.env.example` | Template for your secrets |

---

## ⚠️ Required Code Fix Before Building

The Redis host in `service/redis_worker.py` is hardcoded to `localhost`.
Inside Docker, it must point to the Redis **service name** instead.

Open `service/redis_worker.py` and change **line 6** from:
```python
r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
```
to:
```python
import os
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
r = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
```

---

## 🚀 Deployment Steps

### 1. Place the Docker files
Copy `Dockerfile`, `docker-compose.yml`, and `.env.example` into the **root of your project** (same folder as `app.py`).

### 2. Create your `.env` file
```bash
cp .env.example .env
# Then edit .env and fill in your real keys
```

### 3. Apply the Redis fix (see above)

### 4. Add gunicorn to requirements.txt
```bash
echo "gunicorn" >> requirements.txt
```

### 5. Build and start
```bash
docker compose up --build -d
```

### 6. Initialize the database (first run only)
```bash
docker compose exec app python -c "from app import app, db; app.app_context().__enter__(); db.create_all()"
```

### 7. Check logs
```bash
docker compose logs -f app
docker compose logs -f redis
```

---

## 🔗 Access
- Dashboard: `http://localhost:5000`
- WhatsApp Webhook: `http://your-server-ip:5000/webhook`

---

## 🛑 Stop
```bash
docker compose down          # stop containers (data is preserved)
docker compose down -v       # stop + delete volumes (wipes DB & Redis)
```

---

## 🏗️ Architecture

```
           ┌──────────────────────────────────────┐
           │         docker-compose network        │
           │                                       │
  :5000 ───►   ibyco_app (Flask + Gunicorn)        │
           │        │ Redis client                 │
           │        ▼                              │
           │   ibyco_redis  (Redis 7)              │
           │                                       │
           │  Volumes:                             │
           │   sqlite_data  →  /app/instance/      │
           │   redis_data   →  Redis persistence   │
           └──────────────────────────────────────┘
```

## 📝 Notes
- SQLite data is persisted in the `sqlite_data` Docker volume — it survives restarts.
- Redis keyspace notifications are enabled automatically (`KEx` flag) for the buffer expiry worker.
- For production, consider replacing SQLite with PostgreSQL (the `psycopg2-binary` dependency is already in requirements.txt).