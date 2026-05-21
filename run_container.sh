#!/bin/bash
# run_container.sh
# Usage: ./run_container.sh
# For macOS UTM with X11 forwarding (requires XQuartz installed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Allow X11 connections from Docker
xhost + 2>/dev/null || true

# Build if image doesn't exist
if ! docker image inspect scout_mini_nav2:humble-arm64 >/dev/null 2>&1; then
    echo "Building Docker image (first time)..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" build
fi

# Run container
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up -d

echo "Container 'scout_mini_nav2' is running."
echo "Attach with: docker exec -it scout_mini_nav2 bash"
echo "Inside container, run:"
echo "  cd ~/scout_ws"
echo "  colcon build --symlink-install"
echo "  source install/setup.bash"
