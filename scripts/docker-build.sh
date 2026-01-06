#!/usr/bin/env bash
# Docker build script with automatic version tagging
# Usage: ./scripts/docker-build.sh [--push]

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Extract version from spo/version.py
APP_VERSION=$(python -c "exec(open('$PROJECT_ROOT/spo/version.py').read()); print(__version__)")

# Get git info
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Image name
IMAGE_NAME="shopping-points-optimiser"

echo "🏗️  Building Docker image..."
echo "   Version: $APP_VERSION"
echo "   Git Ref: $VCS_REF"
echo "   Build Date: $BUILD_DATE"
echo ""

# Build the image
docker build \
  --build-arg APP_VERSION="$APP_VERSION" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VCS_REF="$VCS_REF" \
  --build-arg FLASK_ENV="${FLASK_ENV:-production}" \
  -t "$IMAGE_NAME:$APP_VERSION" \
  -t "$IMAGE_NAME:latest" \
  "$PROJECT_ROOT"

echo ""
echo "✅ Build complete!"
echo "   Tagged as: $IMAGE_NAME:$APP_VERSION"
echo "   Tagged as: $IMAGE_NAME:latest"
echo ""

# Inspect labels
echo "📋 Image metadata:"
docker inspect "$IMAGE_NAME:$APP_VERSION" --format='{{json .Config.Labels}}' | jq

# Push if requested
if [[ "$1" == "--push" ]]; then
    echo ""
    echo "🚀 Pushing to registry..."
    docker push "$IMAGE_NAME:$APP_VERSION"
    docker push "$IMAGE_NAME:latest"
    echo "✅ Push complete!"
fi
