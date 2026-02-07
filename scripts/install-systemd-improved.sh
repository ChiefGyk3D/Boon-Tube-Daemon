#!/bin/bash
# Boon-Tube-Daemon - systemd Service Installation Script
# This script installs Boon-Tube-Daemon as a systemd service
# Improved version: Only requires sudo for systemctl operations

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script mode flags
DRY_RUN=false
UNINSTALL=false
FORCE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "Boon-Tube-Daemon systemd installer"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Show what would be done without making changes"
            echo "  --uninstall   Remove the systemd service"
            echo "  --force       Force reinstall even if service exists"
            echo "  --help, -h    Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper function to check if running as root
is_root() {
    [ "$EUID" -eq 0 ]
}

# Helper function to run commands with sudo only when needed
run_sudo() {
    if is_root; then
        "$@"
    else
        sudo "$@"
    fi
}

# Helper function for dry-run mode
execute() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would execute: $*"
    else
        "$@"
    fi
}

# Get script and project directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Detect actual user (not root if using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo "~$ACTUAL_USER")

echo -e "${GREEN}Boon-Tube-Daemon - systemd Service Installer${NC}"
echo "=========================================="
echo ""
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN MODE - No changes will be made]${NC}"
    echo ""
fi
echo "Project Directory: $PROJECT_DIR"
echo "Running as user: $ACTUAL_USER"
echo ""

# Handle uninstall mode
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}Uninstall Mode${NC}"
    echo ""
    
    SERVICE_FILE="/etc/systemd/system/boon-tube-daemon.service"
    
    if [ ! -f "$SERVICE_FILE" ]; then
        echo -e "${YELLOW}Service is not installed (${SERVICE_FILE} not found)${NC}"
        exit 0
    fi
    
    echo "This will:"
    echo "  • Stop the service (if running)"
    echo "  • Disable the service"
    echo "  • Remove ${SERVICE_FILE}"
    echo ""
    read -p "Continue with uninstall? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstall cancelled"
        exit 0
    fi
    
    echo ""
    echo "Stopping service..."
    execute run_sudo systemctl stop boon-tube-daemon.service 2>/dev/null || true
    
    echo "Disabling service..."
    execute run_sudo systemctl disable boon-tube-daemon.service 2>/dev/null || true
    
    echo "Removing service file..."
    execute run_sudo rm -f "$SERVICE_FILE"
    
    echo "Reloading systemd..."
    execute run_sudo systemctl daemon-reload
    
    echo ""
    echo -e "${GREEN}✓ Service uninstalled successfully!${NC}"
    exit 0
fi

# ============================================================================
# PRE-FLIGHT CHECKS (no root required)
# ============================================================================

echo -e "${BLUE}Running pre-flight checks...${NC}"
echo ""

# Check if service already exists
SERVICE_FILE="/etc/systemd/system/boon-tube-daemon.service"
if [ -f "$SERVICE_FILE" ] && [ "$FORCE" = false ]; then
    echo -e "${YELLOW}WARNING: Service already installed at ${SERVICE_FILE}${NC}"
    echo ""
    echo "Options:"
    echo "  1) Upgrade/reinstall (stop, update, restart)"
    echo "  2) Uninstall (remove service)"
    echo "  3) Cancel"
    echo ""
    read -p "Select option [1-3]: " -n 1 -r EXISTING_ACTION
    echo ""
    echo ""
    
    case $EXISTING_ACTION in
        1)
            echo "Proceeding with upgrade/reinstall..."
            ;;
        2)
            echo "Stopping and removing service..."
            execute run_sudo systemctl stop boon-tube-daemon.service 2>/dev/null || true
            execute run_sudo systemctl disable boon-tube-daemon.service 2>/dev/null || true
            execute run_sudo rm -f "$SERVICE_FILE"
            execute run_sudo systemctl daemon-reload
            echo -e "${GREEN}✓ Service removed${NC}"
            exit 0
            ;;
        *)
            echo "Installation cancelled"
            exit 0
            ;;
    esac
fi

# Check if main.py or main module exists
if [ ! -f "$PROJECT_DIR/main.py" ] && [ ! -d "$PROJECT_DIR/boon_tube_daemon" ]; then
    echo -e "${RED}ERROR: Neither main.py nor boon_tube_daemon module found in $PROJECT_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Project files found"

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Expected location: $PROJECT_DIR/.env"
    echo ""
    echo "Please create .env file first. You can:"
    echo "  1. Copy from .env.example: cp .env.example .env"
    echo "  2. Use the create-secrets.sh script: ./scripts/create-secrets.sh"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓${NC} Found .env file"

# Validate .env has required keys
REQUIRED_ENV_VARS=("YOUTUBE_API_KEY" "YOUTUBE_CHANNEL_ID")
MISSING_VARS=()
for var in "${REQUIRED_ENV_VARS[@]}"; do
    if ! grep -q "^${var}=" "$PROJECT_DIR/.env"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${YELLOW}WARNING: Missing required environment variables in .env:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  • $var"
    done
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Required environment variables present"
fi

# ============================================================================
# DEPLOYMENT MODE SELECTION
# ============================================================================

echo ""
echo "Choose deployment mode:"
echo "  1) Python (uses Python virtual environment)"
echo "  2) Docker (uses Docker containers)"
echo ""
read -p "Select option [1-2]: " -n 1 -r DEPLOYMENT_MODE
echo ""
echo ""

if [[ ! $DEPLOYMENT_MODE =~ ^[1-2]$ ]]; then
    echo -e "${RED}ERROR: Invalid option selected${NC}"
    exit 1
fi

# ============================================================================
# PYTHON DEPLOYMENT MODE
# ============================================================================

if [ "$DEPLOYMENT_MODE" = "1" ]; then
    echo -e "${GREEN}Setting up Python deployment...${NC}"
    echo ""
    
    # Detect Python command
    PYTHON_CMD=""
    for py_cmd in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$py_cmd" &> /dev/null; then
            PYTHON_CMD="$py_cmd"
            break
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        echo -e "${RED}ERROR: Python 3 not found!${NC}"
        echo "Please install Python 3.10 or later"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo -e "${GREEN}✓${NC} Found Python: $PYTHON_VERSION ($PYTHON_CMD)"
    
    # Check Python version (require 3.10+)
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        echo -e "${RED}ERROR: Python 3.10 or later required (found ${PYTHON_MAJOR}.${PYTHON_MINOR})${NC}"
        exit 1
    fi
    
    # Check if venv module available
    if ! $PYTHON_CMD -m venv --help > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Python venv module not available${NC}"
        echo "Please install: sudo apt-get install python3-venv"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo ""
        echo "Creating Python virtual environment..."
        execute $PYTHON_CMD -m venv "$PROJECT_DIR/venv"
        echo -e "${GREEN}✓${NC} Virtual environment created"
    else
        echo -e "${GREEN}✓${NC} Virtual environment exists"
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        echo -e "${YELLOW}WARNING: requirements.txt not found${NC}"
    else
        echo -e "${GREEN}✓${NC} Found requirements.txt"
    fi
    
    # Install/upgrade dependencies
    if [ "$DRY_RUN" = false ]; then
        echo ""
        echo "Installing Python dependencies..."
        "$PROJECT_DIR/venv/bin/pip" install --upgrade pip -q
        "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q
        echo -e "${GREEN}✓${NC} Dependencies installed"
    fi
    
    # Determine the correct ExecStart command
    if [ -f "$PROJECT_DIR/main.py" ]; then
        EXEC_START="$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py"
    else
        EXEC_START="$PROJECT_DIR/venv/bin/python -m boon_tube_daemon"
    fi
    
    # Create systemd service file
    echo ""
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would create systemd service file at: $SERVICE_FILE"
    else
        echo "Creating systemd service file..."
    fi
    
    SERVICE_CONTENT="[Unit]
Description=Boon-Tube-Daemon - Multi-platform Video Notification Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment=\"PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin\"
ExecStart=$EXEC_START
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=boon-tube-daemon

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target"
    
    if [ "$DRY_RUN" = false ]; then
        echo "$SERVICE_CONTENT" | run_sudo tee "$SERVICE_FILE" > /dev/null
        echo -e "${GREEN}✓${NC} Service file created"
    fi

# ============================================================================
# DOCKER DEPLOYMENT MODE
# ============================================================================

elif [ "$DEPLOYMENT_MODE" = "2" ]; then
    echo -e "${GREEN}Setting up Docker deployment...${NC}"
    echo ""
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker is not installed!${NC}"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    DOCKER_CMD=$(command -v docker)
    echo -e "${GREEN}✓${NC} Docker is installed: $(docker --version)"
    
    # Check if docker-compose is available
    COMPOSE_CMD=""
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo -e "${GREEN}✓${NC} Found docker-compose: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo -e "${GREEN}✓${NC} Found docker compose plugin"
    fi
    
    # Check if user can run Docker commands
    if ! docker ps > /dev/null 2>&1; then
        echo -e "${YELLOW}WARNING: Cannot run Docker commands as current user${NC}"
        
        if ! groups "$ACTUAL_USER" | grep -q docker; then
            echo "User $ACTUAL_USER is not in the docker group"
            echo ""
            read -p "Add user to docker group? (Y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                execute run_sudo usermod -aG docker "$ACTUAL_USER"
                echo -e "${GREEN}✓${NC} User added to docker group"
                echo -e "${YELLOW}NOTE: You'll need to log out and back in for group changes to take effect${NC}"
            fi
        fi
    else
        echo -e "${GREEN}✓${NC} Docker access confirmed"
    fi
    
    # Check for Docker image
    IMAGE_NAME="boon-tube-daemon"
    IMAGE_EXISTS=false
    
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${IMAGE_NAME}:latest$"; then
        IMAGE_SIZE=$(docker images --format "{{.Size}}" "$IMAGE_NAME:latest")
        echo -e "${GREEN}✓${NC} Docker image found: ${IMAGE_NAME}:latest (${IMAGE_SIZE})"
        IMAGE_EXISTS=true
        
        read -p "Use existing image? (Y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            IMAGE_EXISTS=false
        fi
    else
        echo -e "${YELLOW}Docker image '$IMAGE_NAME' not found${NC}"
    fi
    
    # Get or build the image
    if [ "$IMAGE_EXISTS" = false ]; then
        echo ""
        echo "How would you like to get the Docker image?"
        echo "  1) Build locally from source (recommended for development)"
        echo "  2) Pull from GitHub Container Registry (faster, production-ready)"
        echo ""
        read -p "Select option [1-2]: " -n 1 -r IMAGE_SOURCE
        echo ""
        
        if [ "$IMAGE_SOURCE" = "2" ]; then
            # Pull from GitHub Container Registry
            GHCR_IMAGE="ghcr.io/chiefgyk3d/boon-tube-daemon:latest"
            echo "Pulling Docker image from GitHub Container Registry..."
            echo ""
            
            if execute docker pull "$GHCR_IMAGE"; then
                execute docker tag "$GHCR_IMAGE" "$IMAGE_NAME:latest"
                echo -e "${GREEN}✓${NC} Image pulled and tagged"
            else
                echo -e "${RED}✗${NC} Failed to pull image"
                read -p "Build locally instead? (y/N) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
                IMAGE_SOURCE="1"
            fi
        fi
        
        if [ "$IMAGE_SOURCE" = "1" ]; then
            # Build locally
            if [ ! -f "$PROJECT_DIR/docker/Dockerfile" ]; then
                echo -e "${RED}ERROR: docker/Dockerfile not found!${NC}"
                exit 1
            fi
            
            echo "Building Docker image..."
            echo "This may take several minutes..."
            echo ""
            
            cd "$PROJECT_DIR"
            if execute docker build -t "$IMAGE_NAME:latest" -f docker/Dockerfile .; then
                IMAGE_SIZE=$(docker images --format "{{.Size}}" "$IMAGE_NAME:latest")
                echo ""
                echo -e "${GREEN}✓${NC} Docker image built: ${IMAGE_NAME}:latest (${IMAGE_SIZE})"
            else
                echo ""
                echo -e "${RED}✗${NC} Failed to build Docker image"
                echo ""
                echo "Troubleshooting:"
                echo "  • Check Docker is running: docker ps"
                echo "  • Free up space: docker system prune"
                echo "  • Check logs above for specific errors"
                exit 1
            fi
        fi
    fi
    
    # Create systemd service file for Docker
    echo ""
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would create systemd service file at: $SERVICE_FILE"
    else
        echo "Creating systemd service file for Docker..."
    fi
    
    SERVICE_CONTENT="[Unit]
Description=Boon-Tube-Daemon - Multi-platform Video Notification Bot (Docker)
After=docker.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR

# Clean up any stale container from unclean shutdown
ExecStartPre=-${DOCKER_CMD} stop boon-tube-daemon
ExecStartPre=-${DOCKER_CMD} rm -f boon-tube-daemon

# Start the Docker container
ExecStart=${DOCKER_CMD} run -d \\
    --name boon-tube-daemon \\
    --restart unless-stopped \\
    --env-file $PROJECT_DIR/.env \\
    $IMAGE_NAME:latest

# Stop and remove the container
ExecStop=${DOCKER_CMD} stop boon-tube-daemon
ExecStopPost=${DOCKER_CMD} rm -f boon-tube-daemon

StandardOutput=journal
StandardError=journal
SyslogIdentifier=boon-tube-daemon

[Install]
WantedBy=multi-user.target"
    
    if [ "$DRY_RUN" = false ]; then
        echo "$SERVICE_CONTENT" | run_sudo tee "$SERVICE_FILE" > /dev/null
        echo -e "${GREEN}✓${NC} Service file created"
    fi
fi

# ============================================================================
# SYSTEMD CONFIGURATION (requires sudo)
# ============================================================================

if [ "$DRY_RUN" = false ]; then
    echo ""
    echo "Reloading systemd daemon..."
    run_sudo systemctl daemon-reload
    echo -e "${GREEN}✓${NC} systemd reloaded"
    
    # Enable service
    echo ""
    read -p "Enable service to start on boot? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_sudo systemctl enable boon-tube-daemon.service
        echo -e "${GREEN}✓${NC} Service enabled"
    fi
    
    # Start service
    echo ""
    read -p "Start service now? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_sudo systemctl start boon-tube-daemon.service
        sleep 2
        
        if systemctl is-active --quiet boon-tube-daemon.service; then
            echo -e "${GREEN}✓${NC} Service started successfully!"
            echo ""
            echo "Service status:"
            run_sudo systemctl status boon-tube-daemon.service --no-pager -l
        else
            echo -e "${RED}✗${NC} Service failed to start"
            echo ""
            echo "Check status with: sudo systemctl status boon-tube-daemon"
            echo "Check logs with: sudo journalctl -u boon-tube-daemon -n 50"
        fi
    fi
fi

# ============================================================================
# COMPLETION
# ============================================================================

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Useful commands:"
echo "  Status:  sudo systemctl status boon-tube-daemon"
echo "  Start:   sudo systemctl start boon-tube-daemon"
echo "  Stop:    sudo systemctl stop boon-tube-daemon"
echo "  Restart: sudo systemctl restart boon-tube-daemon"
echo "  Logs:    sudo journalctl -u boon-tube-daemon -f"
echo "  Enable:  sudo systemctl enable boon-tube-daemon"
echo "  Disable: sudo systemctl disable boon-tube-daemon"
echo ""
if [ "$DEPLOYMENT_MODE" = "2" ]; then
    echo "Docker commands:"
    echo "  Logs:    docker logs boon-tube-daemon -f"
    echo "  Shell:   docker exec -it boon-tube-daemon /bin/bash"
    echo "  Rebuild: docker build -t boon-tube-daemon:latest -f docker/Dockerfile ."
    echo ""
fi
echo "To uninstall: $0 --uninstall"
echo ""
