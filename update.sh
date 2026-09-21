#!/bin/bash
# Boon-Tube-Daemon Update Script
# Pulls the latest image from GHCR and restarts the container.
#
# Usage:
#   ./update.sh          # Pull latest + restart
#   ./update.sh --build  # Build locally + restart

set -e

cd "$(dirname "$0")"

# Verify the image signature before running it. Every published image is
# signed keyless by the release workflow in ChiefGyk3D/git-your-ship-together
# (see SECURITY.md). With cosign installed a bad or missing signature aborts;
# without it the check is skipped and says so.
verify_image() {
    local image="$1"
    if ! command -v cosign >/dev/null 2>&1; then
        echo "⚠️  cosign is not installed; the image signature was NOT verified."
        echo "   https://docs.sigstore.dev/cosign/system_config/installation/"
        return 0
    fi
    echo "🔏 Verifying the image signature with cosign..."
    cosign verify "$image" \
        --certificate-identity-regexp '^https://github.com/ChiefGyk3D/git-your-ship-together/' \
        --certificate-oidc-issuer https://token.actions.githubusercontent.com >/dev/null
    echo "✓ Signature verified"
}

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
    verify_image "ghcr.io/chiefgyk3d/boon-tube-daemon:latest"
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
