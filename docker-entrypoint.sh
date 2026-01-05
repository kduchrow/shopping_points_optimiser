#!/bin/bash
set -e

echo "🔧 Setting up directories..."

# Ensure instance and logs directories exist with correct permissions
mkdir -p /app/instance /app/logs
chmod -R 777 /app/instance /app/logs

echo "✅ Directories ready"

# Start gunicorn
echo "🚀 Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class sync --timeout 60 app:app
