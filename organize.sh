#!/bin/bash
# Cleanup and reorganization script for Boon-Tube-Daemon

set -e

echo "🧹 Starting project cleanup and reorganization..."

# Move test files to tests directory
echo "📦 Moving test files to tests/..."
mkdir -p tests
[ -f "get_ms_token.py" ] && mv get_ms_token.py tests/ || true
[ -f "matrix_join_room.py" ] && mv matrix_join_room.py tests/ || true

# Move detailed setup documentation to docs
echo "📚 Organizing documentation..."
mkdir -p docs/setup
[ -f "DISCORD_EXAMPLES.md" ] && mv DISCORD_EXAMPLES.md docs/setup/ || true
[ -f "SOCIAL_PLATFORMS_SETUP.md" ] && mv SOCIAL_PLATFORMS_SETUP.md docs/setup/ || true
[ -f "TIKTOK_API_SETUP.md" ] && mv TIKTOK_API_SETUP.md docs/setup/ || true

# Remove duplicate QUICKSTART.md (keep the one in docs/)
if [ -f "QUICKSTART.md" ] && [ -f "docs/QUICKSTART.md" ]; then
    echo "🗑️  Removing duplicate QUICKSTART.md from root..."
    rm QUICKSTART.md
fi

# Move legal docs to docs/legal
echo "⚖️  Organizing legal documents..."
mkdir -p docs/legal
[ -f "PRIVACY_POLICY.md" ] && mv PRIVACY_POLICY.md docs/legal/ || true
[ -f "TERMS_OF_SERVICE.md" ] && mv TERMS_OF_SERVICE.md docs/legal/ || true

echo "✅ Cleanup complete!"
echo ""
echo "Project structure:"
echo "  tests/          - All test scripts"
echo "  docs/setup/     - Platform setup guides"
echo "  docs/legal/     - Legal documents"
echo "  docs/           - General documentation"
