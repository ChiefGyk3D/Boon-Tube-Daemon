#!/bin/bash
# Boon-Tube-Daemon Update Script
# Pulls the latest image from GHCR and restarts the container.
#
# Usage:
#   ./update.sh          # Pull latest + restart
#   ./update.sh --build  # Build locally + restart

set -e

cd "$(dirname "$0")"

# Detect compose command
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose is not installed."
    exit 1
fi

echo "=================================="
echo "Boon-Tube-Daemon Update"
echo "=================================="
echo ""

# Pull latest git changes
if [ -d .git ]; then
    echo "📥 Pulling latest code from git..."
    git pull --ff-only 2>&1 || {
        echo "⚠️  Git pull failed (local changes?). Continuing with current code..."
    }
    echo ""
fi

if [[ "${1:-}" == "--build" ]]; then
    echo "📦 Building Docker image locally..."
    $COMPOSE_CMD build --no-cache --pull
    echo "✓ Image built"
else
    # Clear stale GHCR credentials to prevent "denied" errors.
    # Docker sends stored credentials even for public repos — if the token is
    # expired or revoked, the pull fails instead of falling back to anonymous access.
    if grep -q '"ghcr.io"' ~/.docker/config.json 2>/dev/null; then
        echo "⚠️  Clearing stored GHCR credentials (stale tokens cause pull failures)..."
        docker logout ghcr.io 2>/dev/null || true
        echo ""
    fi

    echo "📥 Pulling latest image from GHCR..."
    $COMPOSE_CMD pull
    echo "✓ Image pulled"
fi

echo ""
echo "🔄 Restarting container..."
$COMPOSE_CMD down --remove-orphans 2>/dev/null || true
$COMPOSE_CMD up -d
echo "✓ Container started"

echo ""
echo "📋 Container status:"
docker ps --filter "name=boon-tube-daemon" --format "  Image:  {{.Image}}\n  Status: {{.Status}}"

echo ""
echo "View logs with: $COMPOSE_CMD logs -f"
echo ""
