#!/bin/bash
# Clean up script for Boon-Tube-Daemon
# Removes old files, cache, and build artifacts

echo "🧹 Cleaning Boon-Tube-Daemon..."

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type f -name "*.pyd" -delete 2>/dev/null

# Remove build artifacts
rm -rf build/ dist/ *.egg-info/ 2>/dev/null

# Remove old backup files
find . -name "*.old" -delete 2>/dev/null
find . -name "*.bak" -delete 2>/dev/null
find . -name "*.backup" -delete 2>/dev/null

# Remove logs
rm -f *.log 2>/dev/null

# Remove pytest cache
rm -rf .pytest_cache/ 2>/dev/null

# Remove coverage reports
rm -rf htmlcov/ .coverage 2>/dev/null

echo "✓ Cleanup complete!"
echo ""
echo "Kept:"
echo "  ✓ .env (your configuration)"
echo "  ✓ Source code"
echo "  ✓ Documentation"
