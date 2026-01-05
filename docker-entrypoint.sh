#!/bin/bash
set -e

echo "🔧 Setting up directories..."

# Ensure instance and logs directories exist with correct permissions
mkdir -p /app/instance /app/logs
chmod -R 777 /app/instance /app/logs

# Test if directories are writable
echo "✅ Directories created"
ls -la /app/instance
ls -la /app/logs

# Test write permissions
touch /app/instance/test.txt && rm /app/instance/test.txt && echo "✅ /app/instance is writable" || echo "❌ /app/instance is NOT writable"

echo "🚀 Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class sync --timeout 60 app:app
