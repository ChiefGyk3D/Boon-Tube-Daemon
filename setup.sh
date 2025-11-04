#!/bin/bash
# Boon-Tube-Daemon Setup Script

set -e  # Exit on error

echo "=================================="
echo "Boon-Tube-Daemon Setup"
echo "=================================="
echo ""

# Check Python version
echo "🔍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Found Python $PYTHON_VERSION"

# Check if Python version is 3.8+
if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    echo "❌ Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment (optional but recommended)
read -p "📦 Create virtual environment? (recommended) [Y/n]: " CREATE_VENV
CREATE_VENV=${CREATE_VENV:-Y}

if [[ $CREATE_VENV =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Python dependencies installed"

# Install Playwright browsers for TikTok
read -p "🎭 Install Playwright browsers for TikTok? (~150MB) [Y/n]: " INSTALL_PLAYWRIGHT
INSTALL_PLAYWRIGHT=${INSTALL_PLAYWRIGHT:-Y}

if [[ $INSTALL_PLAYWRIGHT =~ ^[Yy]$ ]]; then
    echo "Installing Playwright browsers..."
    playwright install chromium
    echo "✓ Playwright browsers installed"
fi

# Create config file if it doesn't exist
echo ""
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✓ Config file created: .env"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your API keys and settings!"
    echo "   nano .env"
else
    echo "ℹ️  .env already exists, skipping..."
fi

# Create systemd service file (optional)
echo ""
read -p "🔧 Create systemd service file? [y/N]: " CREATE_SERVICE
CREATE_SERVICE=${CREATE_SERVICE:-N}

if [[ $CREATE_SERVICE =~ ^[Yy]$ ]]; then
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    PYTHON_PATH=$(which python3)
    
    cat > boon-tube.service << EOF
[Unit]
Description=Boon-Tube-Daemon - TikTok/YouTube Monitor
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$PYTHON_PATH $CURRENT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "✓ Service file created: boon-tube.service"
    echo ""
    echo "To install the service, run:"
    echo "  sudo cp boon-tube.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable boon-tube"
    echo "  sudo systemctl start boon-tube"
fi

# Summary
echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env with your API keys:"
echo "   nano .env"
echo ""
echo "2. Run the daemon:"
if [[ $CREATE_VENV =~ ^[Yy]$ ]]; then
    echo "   source venv/bin/activate  # If not already activated"
fi
echo "   python main.py"
echo ""
echo "3. Or run in background:"
echo "   nohup python main.py > boon-tube.log 2>&1 &"
echo ""
echo "For more info, see README.md"
echo ""
