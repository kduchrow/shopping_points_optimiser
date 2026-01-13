#!/bin/bash
# Clean Python environment and restart Docker container

set -e

# Remove all __pycache__ folders
find . -type d -name "__pycache__" -exec rm -rf {} +

echo "✅ Removed all __pycache__ folders."

# Remove .pyc files (if any outside __pycache__)
find . -type f -name "*.pyc" -delete

echo "✅ Removed all .pyc files."

# Restart Docker containers (assuming your main container is named 'app')
docker compose down
sleep 2
docker compose up -d

echo "✅ Docker containers restarted."

echo "Environment cleanup complete."
