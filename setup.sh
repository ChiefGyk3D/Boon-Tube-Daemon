#!/bin/bash
# Boon-Tube-Daemon Setup Script

set -e  # Exit on error

echo "=================================="
echo "Boon-Tube-Daemon Setup"
echo "=================================="
echo ""

# Installation type selection
echo "Choose installation method:"
echo "  1) Docker (recommended) - Uses containers, easy updates"
echo "  2) Local - Direct Python installation on your system"
echo ""
read -p "Enter choice [1/2]: " INSTALL_TYPE
INSTALL_TYPE=${INSTALL_TYPE:-1}

# Create .env file if it doesn't exist (needed for both methods)
create_env_file() {
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
}

# ============================================
# DOCKER INSTALLATION
# ============================================
docker_install() {
    echo ""
    echo "🐳 Docker Installation"
    echo "======================"
    echo ""
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed."
        echo ""
        echo "Install Docker first:"
        echo "  curl -fsSL https://get.docker.com | sh"
        echo "  sudo usermod -aG docker \$USER"
        echo "  # Log out and back in for group changes to take effect"
        exit 1
    fi
    echo "✓ Docker found: $(docker --version)"
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo "✓ Docker Compose found: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo "✓ Docker Compose found: $(docker compose version)"
    else
        echo "❌ Docker Compose is not installed."
        echo "   Please install Docker Compose or use Docker Desktop."
        exit 1
    fi
    
    # Check for existing installation and offer cleanup
    EXISTING_CONTAINER=$(docker ps -a --filter "name=boon-tube-daemon" --format "{{.Names}}" 2>/dev/null || true)
    EXISTING_IMAGE=$(docker images "ghcr.io/chiefgyk3d/boon-tube-daemon" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | head -1 || true)
    
    if [[ -n "$EXISTING_CONTAINER" ]] || [[ -n "$EXISTING_IMAGE" ]]; then
        echo ""
        echo "⚠️  Existing Boon-Tube-Daemon installation detected:"
        [[ -n "$EXISTING_CONTAINER" ]] && echo "   Container: $EXISTING_CONTAINER"
        [[ -n "$EXISTING_IMAGE" ]] && echo "   Image: $EXISTING_IMAGE"
        echo ""
        read -p "🧹 Remove old container and image before installing? [Y/n]: " CLEANUP_OLD
        CLEANUP_OLD=${CLEANUP_OLD:-Y}
        
        if [[ $CLEANUP_OLD =~ ^[Yy]$ ]]; then
            echo "Stopping and removing old container..."
            $COMPOSE_CMD down 2>/dev/null || docker stop boon-tube-daemon 2>/dev/null || true
            docker rm boon-tube-daemon 2>/dev/null || true
            echo "✓ Old container removed"
            
            echo "Removing old image..."
            docker rmi ghcr.io/chiefgyk3d/boon-tube-daemon:latest 2>/dev/null || true
            docker rmi $(docker images "ghcr.io/chiefgyk3d/boon-tube-daemon" -q) 2>/dev/null || true
            echo "✓ Old image removed"
            
            # Optional: prune dangling images
            read -p "🗑️  Also prune unused Docker images to free space? [y/N]: " PRUNE_IMAGES
            PRUNE_IMAGES=${PRUNE_IMAGES:-N}
            if [[ $PRUNE_IMAGES =~ ^[Yy]$ ]]; then
                docker image prune -f
                echo "✓ Unused images pruned"
            fi
        fi
    fi
    
    # Create .env file
    create_env_file
    
    # Create config directory
    mkdir -p config
    echo "✓ Config directory created"
    
    # Choose image source
    echo ""
    echo "Choose Docker image source:"
    echo "  1) Pull from GitHub Container Registry (fastest)"
    echo "  2) Build locally from source code"
    echo ""
    read -p "Enter choice [1/2]: " DOCKER_SOURCE
    DOCKER_SOURCE=${DOCKER_SOURCE:-1}
    
    if [[ $DOCKER_SOURCE == "2" ]]; then
        echo ""
        echo "📦 Building Docker image locally..."
        $COMPOSE_CMD build --no-cache
        echo "✓ Docker image built"
    else
        echo ""
        echo "📥 Pulling Docker image from GitHub Container Registry..."
        $COMPOSE_CMD pull
        echo "✓ Docker image pulled"
    fi
    
    # Start container
    echo ""
    read -p "🚀 Start the container now? [Y/n]: " START_NOW
    START_NOW=${START_NOW:-Y}
    
    if [[ $START_NOW =~ ^[Yy]$ ]]; then
        echo "Starting Boon-Tube-Daemon..."
        $COMPOSE_CMD up -d
        echo "✓ Container started"
        echo ""
        echo "View logs with:"
        echo "  $COMPOSE_CMD logs -f"
    fi
    
    # Ensure Docker starts on boot
    echo ""
    if ! systemctl is-enabled docker &>/dev/null; then
        read -p "🔄 Enable Docker to start on boot? [Y/n]: " ENABLE_DOCKER
        ENABLE_DOCKER=${ENABLE_DOCKER:-Y}
        
        if [[ $ENABLE_DOCKER =~ ^[Yy]$ ]]; then
            echo "Enabling Docker service..."
            sudo systemctl enable docker
            echo "✓ Docker will start on boot"
            echo "✓ Container will auto-restart with Docker (restart: unless-stopped)"
        fi
    else
        echo "✓ Docker is already enabled to start on boot"
        echo "✓ Container will auto-restart with Docker (restart: unless-stopped)"
    fi
    
    # Summary
    echo ""
    echo "=================================="
    echo "✅ Docker Setup Complete!"
    echo "=================================="
    echo ""
    echo "Useful commands:"
    echo "  $COMPOSE_CMD up -d        # Start container"
    echo "  $COMPOSE_CMD down         # Stop container"
    echo "  $COMPOSE_CMD logs -f      # View logs"
    echo "  $COMPOSE_CMD pull         # Update to latest image"
    echo "  $COMPOSE_CMD up -d --build # Rebuild and restart"
    echo ""
    echo "The container will automatically restart on boot."
    echo "Don't forget to edit .env with your API keys!"
    echo ""
}

# ============================================
# LOCAL INSTALLATION
# ============================================
local_install() {
    echo ""
    echo "🐍 Local Python Installation"
    echo "============================="
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

    # Create .env file
    create_env_file

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
    echo "✅ Local Setup Complete!"
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
}

# ============================================
# MAIN EXECUTION
# ============================================
case $INSTALL_TYPE in
    1)
        docker_install
        ;;
    2)
        local_install
        ;;
    *)
        echo "❌ Invalid choice. Please enter 1 or 2."
        exit 1
        ;;
esac
