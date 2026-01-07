#!/bin/bash
# Test and Rebuild Script for Shopping Points Optimiser
# This script rebuilds the Docker image, restarts the container, and shows logs

set -e

SKIP_BUILD=false
CLEAN_START=false
LOG_LINES=40

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --clean)
            CLEAN_START=true
            shift
            ;;
        --log-lines)
            LOG_LINES="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-build] [--clean] [--log-lines N]"
            exit 1
            ;;
    esac
done

echo "🔨 Shopping Points Optimiser - Test & Rebuild"
echo "============================================="
echo ""

if [ "$CLEAN_START" = true ]; then
    echo "🧹 Clean start: Removing all containers and volumes..."
    docker-compose down -v
    echo ""
fi

if [ "$SKIP_BUILD" = false ]; then
    echo "🔨 Building Docker image..."
    docker-compose build --no-cache shopping-points
    echo "✅ Build complete"
    echo ""
fi

echo "🚀 Starting containers..."
if [ "$CLEAN_START" = true ]; then
    docker-compose up -d
else
    docker-compose restart shopping-points
fi

echo "✅ Containers started"
echo ""

echo "⏳ Waiting for initialization (15 seconds)..."
sleep 15

echo ""
echo "📋 Container logs (last $LOG_LINES lines):"
echo "========================================"
docker-compose logs shopping-points --tail="$LOG_LINES"

echo ""
echo "✅ Ready for testing!"
echo ""
echo "Useful commands:"
echo "  - Open app:          http://localhost:5000"
echo "  - Run tests:         docker-compose exec -T shopping-points python -m pytest -q"
echo "  - View logs:         docker-compose logs shopping-points -f"
echo "  - Check status:      docker-compose ps"
echo "  - Stop containers:   docker-compose down"
echo ""
