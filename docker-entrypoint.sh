#!/bin/bash
set -e

echo "🔧 Setting up directories..."

# Ensure instance and logs directories exist with correct permissions
mkdir -p /app/instance /app/logs
chmod -R 777 /app/instance /app/logs

echo "✅ Directories created"
ls -la /app/instance
ls -la /app/logs

touch /app/instance/test.txt && rm /app/instance/test.txt && echo "✅ /app/instance is writable" || echo "❌ /app/instance is NOT writable"

echo "⏳ Waiting for database..."
python - <<'PY'
import os
import sys
import time
from sqlalchemy import create_engine, text

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print('DATABASE_URL is not set; skipping DB wait and migrations', flush=True)
    sys.exit(0)

engine = create_engine(database_url)
retries = 10
for attempt in range(retries):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('✅ Database is reachable', flush=True)
        break
    except Exception as exc:  # pragma: no cover
        wait = 2 * (attempt + 1)
        print(f"Database not ready (attempt {attempt + 1}/{retries}): {exc}. Retrying in {wait}s", flush=True)
        time.sleep(wait)
else:
    print('❌ Database is not reachable after retries', flush=True)
    sys.exit(1)
PY

echo "📦 Running migrations..."
cd /app && python -m alembic upgrade head

echo "🚀 Starting gunicorn..."
# Use a single worker to avoid concurrent DB init races during startup.
exec gunicorn --bind 0.0.0.0:5000 --workers 1 --worker-class sync --timeout 60 app:app
