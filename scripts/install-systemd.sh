#!/bin/bash
# Boon-Tube-Daemon - systemd Service Installation Script
# This script installs Boon-Tube-Daemon as a systemd service

set -e
set -u  # Exit on undefined variables

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Trap errors and provide cleanup
trap 'echo -e "${RED}Error occurred at line $LINENO. Exiting...${NC}"; exit 1' ERR

# Parse command-line arguments
DRY_RUN=false
UNINSTALL=false
FORCE=false

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
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Show what would be done without making changes"
            echo "  --uninstall   Remove installed service and related files"
            echo "  --force       Skip confirmation prompts"
            echo "  -h, --help    Show this help message"
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

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project directory is parent of scripts directory
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Get actual user (not root if using sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

# Function to run commands with sudo only when needed
run_with_sudo() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}[DRY-RUN]${NC} Would run: sudo $*"
        return 0
    fi
    
    if [ "$EUID" -eq 0 ]; then
        # Already root
        "$@"
    else
        # Need sudo
        sudo "$@"
    fi
}

# Function to check if service exists
service_exists() {
    systemctl list-unit-files | grep -q "^boon-tube-daemon.service"
}

echo -e "${GREEN}Boon-Tube-Daemon - systemd Service Installer${NC}"
echo "=========================================="
echo ""
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}[DRY-RUN MODE] - No changes will be made${NC}"
    echo ""
fi
echo "Project Directory: $PROJECT_DIR"
echo "Running as user: $ACTUAL_USER"
echo ""

# Handle uninstall
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}Uninstalling Boon-Tube-Daemon service...${NC}"
    echo ""
    
    if ! service_exists; then
        echo -e "${YELLOW}Service is not installed${NC}"
        exit 0
    fi
    
    if [ "$FORCE" = false ]; then
        read -p "Are you sure you want to uninstall? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Uninstall cancelled"
            exit 0
        fi
    fi
    
    # Stop and disable service
    if systemctl is-active --quiet boon-tube-daemon.service 2>/dev/null; then
        echo "Stopping service..."
        run_with_sudo systemctl stop boon-tube-daemon.service
        echo -e "${GREEN}✓${NC} Service stopped"
    fi
    
    if systemctl is-enabled --quiet boon-tube-daemon.service 2>/dev/null; then
        echo "Disabling service..."
        run_with_sudo systemctl disable boon-tube-daemon.service
        echo -e "${GREEN}✓${NC} Service disabled"
    fi
    
    # Remove service file
    SERVICE_FILE="/etc/systemd/system/boon-tube-daemon.service"
    if [ -f "$SERVICE_FILE" ]; then
        echo "Removing service file..."
        run_with_sudo rm -f "$SERVICE_FILE"
        echo -e "${GREEN}✓${NC} Service file removed"
    fi
    
    # Reload systemd
    echo "Reloading systemd..."
    run_with_sudo systemctl daemon-reload
    echo -e "${GREEN}✓${NC} systemd reloaded"
    
    # Clean up Docker containers if they exist
    if command -v docker &> /dev/null; then
        if docker ps -a --format "{{.Names}}" | grep -q "^boon-tube-daemon$"; then
            echo "Removing Docker container..."
            if [ "$DRY_RUN" = false ]; then
                docker stop boon-tube-daemon 2>/dev/null || true
                docker rm -f boon-tube-daemon 2>/dev/null || true
            else
                echo -e "${BLUE}[DRY-RUN]${NC} Would remove Docker container"
            fi
            echo -e "${GREEN}✓${NC} Docker container removed"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Uninstall complete!${NC}"
    echo ""
    echo "Note: Configuration files (.env, messages.txt) were preserved"
    echo "To remove them manually: rm $PROJECT_DIR/.env"
    exit 0
fi

# Check if service already exists
if service_exists; then
    echo -e "${YELLOW}WARNING: boon-tube-daemon.service is already installed${NC}"
    echo ""
    echo "Options:"
    echo "  1) Reinstall/upgrade (recommended)"
    echo "  2) Uninstall and exit"
    echo "  3) Cancel"
    echo ""
    read -p "Select option [1-3]: " -n 1 -r EXISTING_ACTION
    echo ""
    
    case $EXISTING_ACTION in
        1)
            echo "Proceeding with reinstall..."
            # Stop service if running
            if systemctl is-active --quiet boon-tube-daemon.service; then
                echo "Stopping existing service..."
                run_with_sudo systemctl stop boon-tube-daemon.service
            fi
            ;;
        2)
            echo "Run with --uninstall flag to remove service"
            exit 0
            ;;
        *)
            echo "Installation cancelled"
            exit 0
            ;;
    esac
    echo ""
fi

# ============================================================================
# PRE-FLIGHT CHECKS (No root required)
# ============================================================================
echo -e "${GREEN}Running pre-flight checks...${NC}"
echo ""

# Check if main.py exists
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo -e "${RED}✗ main.py not found in $PROJECT_DIR${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} main.py found"

# Check if .env exists and validate
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}✗ .env file not found!${NC}"
    echo ""
    echo "You need to create a .env file with your configuration."
    echo "Copy .env.example as a starting point:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓${NC} .env file found"

# Validate .env has required settings
echo "Validating .env configuration..."
ENV_WARNINGS=0

# Check for required YouTube settings if YouTube is enabled
if grep -q "^YOUTUBE_ENABLE=true" "$PROJECT_DIR/.env"; then
    if ! grep -q "^YOUTUBE_API_KEY=" "$PROJECT_DIR/.env" || grep -q "^YOUTUBE_API_KEY=$" "$PROJECT_DIR/.env"; then
        echo -e "${YELLOW}  ⚠ YouTube enabled but YOUTUBE_API_KEY not set${NC}"
        ENV_WARNINGS=$((ENV_WARNINGS + 1))
    fi
    if ! grep -q "^YOUTUBE_CHANNEL_ID=" "$PROJECT_DIR/.env" || grep -q "^YOUTUBE_CHANNEL_ID=$" "$PROJECT_DIR/.env"; then
        echo -e "${YELLOW}  ⚠ YouTube enabled but YOUTUBE_CHANNEL_ID not set${NC}"
        ENV_WARNINGS=$((ENV_WARNINGS + 1))
    fi
fi

# Check for at least one social platform enabled
SOCIAL_ENABLED=false
for platform in DISCORD MATRIX BLUESKY MASTODON; do
    if grep -q "^${platform}_ENABLE_POSTING=true" "$PROJECT_DIR/.env"; then
        SOCIAL_ENABLED=true
        break
    fi
done

if [ "$SOCIAL_ENABLED" = false ]; then
    echo -e "${YELLOW}  ⚠ No social platforms enabled (Discord, Matrix, Bluesky, Mastodon)${NC}"
    ENV_WARNINGS=$((ENV_WARNINGS + 1))
fi

if [ $ENV_WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}  $ENV_WARNINGS warnings found in .env${NC}"
    if [ "$FORCE" = false ]; then
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${GREEN}✓${NC} .env validation passed"
fi

# Ask user which deployment mode they want
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

if [ "$DEPLOYMENT_MODE" = "1" ]; then
    # ============================================================================
    # PYTHON DEPLOYMENT MODE (No root required for setup)
    # ============================================================================
    echo -e "${GREEN}Setting up Python deployment...${NC}"
    echo ""
    
    # Detect Python command
    PYTHON_CMD=""
    if command -v python3.13 &> /dev/null; then
        PYTHON_CMD="python3.13"
    elif command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_CMD="python3.10"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo -e "${RED}✗ Python 3 not found!${NC}"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version)
    echo -e "${GREEN}✓${NC} Found Python: $PYTHON_VERSION ($PYTHON_CMD)"

    # Check if virtual environment exists, create if not
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo ""
        echo "Creating Python virtual environment..."
        if [ "$DRY_RUN" = false ]; then
            $PYTHON_CMD -m venv "$PROJECT_DIR/venv"
            echo -e "${GREEN}✓${NC} Virtual environment created"
        else
            echo -e "${BLUE}[DRY-RUN]${NC} Would create venv at $PROJECT_DIR/venv"
        fi
    else
        echo -e "${GREEN}✓${NC} Virtual environment already exists"
    fi

    # Install/upgrade dependencies
    echo ""
    echo "Installing Python dependencies..."
    if [ "$DRY_RUN" = false ]; then
        "$PROJECT_DIR/venv/bin/pip" install --upgrade pip > /dev/null 2>&1
        "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" > /dev/null 2>&1
        echo -e "${GREEN}✓${NC} Dependencies installed"
    else
        echo -e "${BLUE}[DRY-RUN]${NC} Would install dependencies from requirements.txt"
    fi

    # ============================================================================
    # CREATE SYSTEMD SERVICE (Requires root)
    # ============================================================================
    SERVICE_FILE="/etc/systemd/system/boon-tube-daemon.service"
    echo ""
    echo "Creating systemd service file..."
    echo -e "${YELLOW}(This step requires sudo/root)${NC}"
    echo ""

    if [ "$DRY_RUN" = false ]; then
        # Create temp file first, then copy with sudo
        TEMP_SERVICE=$(mktemp)
        cat > "$TEMP_SERVICE" << EOF
[Unit]
Description=Boon-Tube-Daemon - Multi-platform Live Stream Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
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
WantedBy=multi-user.target
EOF
        
        # Copy to system location with sudo
        run_with_sudo cp "$TEMP_SERVICE" "$SERVICE_FILE"
        run_with_sudo chmod 644 "$SERVICE_FILE"
        rm -f "$TEMP_SERVICE"
        echo -e "${GREEN}✓${NC} Service file created: $SERVICE_FILE"
    else
        echo -e "${BLUE}[DRY-RUN]${NC} Would create service file at $SERVICE_FILE"
    fi

elif [ "$DEPLOYMENT_MODE" = "2" ]; then
    # ============================================================================
    # DOCKER DEPLOYMENT MODE
    # ============================================================================
    echo -e "${GREEN}Setting up Docker deployment...${NC}"
    echo ""
    
    # Check if Docker is installed and get path
    DOCKER_PATH=$(command -v docker)
    if [ -z "$DOCKER_PATH" ]; then
        echo -e "${RED}✗ Docker is not installed!${NC}"
        echo "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Docker is installed: $(docker --version)"
    echo -e "${GREEN}✓${NC} Docker path: $DOCKER_PATH"
    
    # Check if docker-compose is installed
    COMPOSE_CMD=""
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo -e "${GREEN}✓${NC} Found docker-compose: $(docker-compose --version)"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo -e "${GREEN}✓${NC} Found docker compose plugin: $(docker compose version)"
    else
        echo -e "${RED}ERROR: docker-compose is not installed!${NC}"
        echo "Please install docker-compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check if user is in docker group
    USER_IN_DOCKER_GROUP=false
    if groups $ACTUAL_USER | grep -q '\bdocker\b'; then
        USER_IN_DOCKER_GROUP=true
        echo -e "${GREEN}✓${NC} User $ACTUAL_USER is in docker group"
    else
        echo -e "${YELLOW}⚠ User $ACTUAL_USER is not in the docker group${NC}"
        echo ""
        read -p "Add $ACTUAL_USER to docker group? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Adding user to docker group..."
            run_with_sudo usermod -aG docker $ACTUAL_USER
            echo -e "${GREEN}✓${NC} User added to docker group"
            echo -e "${YELLOW}NOTE: You'll need to log out and back in for group changes to take effect${NC}"
            echo ""
        fi
    fi
    
    # Check if Docker image exists or needs to be built
    IMAGE_NAME="boon-tube-daemon"
    IMAGE_EXISTS=false
    
    # Check for existing image (improved detection)
    if docker images --format "{{.Repository}}" | grep -q "^${IMAGE_NAME}$"; then
        IMAGE_TAG=$(docker images --format "{{.Tag}}" "$IMAGE_NAME" | head -n 1)
        IMAGE_ID=$(docker images --format "{{.ID}}" "$IMAGE_NAME" | head -n 1)
        IMAGE_SIZE=$(docker images --format "{{.Size}}" "$IMAGE_NAME" | head -n 1)
        echo -e "${GREEN}✓${NC} Docker image found: ${IMAGE_NAME}:${IMAGE_TAG} (${IMAGE_SIZE}, ID: ${IMAGE_ID:0:12})"
        IMAGE_EXISTS=true
        
        # Ask if they want to rebuild or pull
        echo ""
        read -p "Use existing image? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            # Use existing image, skip to service creation
            IMAGE_EXISTS=true
        else
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
        echo ""
        
        if [ "$IMAGE_SOURCE" = "2" ]; then
            # Pull from GitHub Container Registry
            echo "Pulling Docker image from GitHub Container Registry..."
            echo ""
            GHCR_IMAGE="ghcr.io/chiefgyk3d/boon-tube-daemon:latest"
            
            if [ "$DRY_RUN" = false ]; then
                if docker pull "$GHCR_IMAGE"; then
                    echo ""
                    echo -e "${GREEN}✓${NC} Image pulled successfully!"
                    
                    # Tag it as boon-tube-daemon:latest for local use
                    docker tag "$GHCR_IMAGE" "$IMAGE_NAME:latest"
                    echo -e "${GREEN}✓${NC} Tagged as ${IMAGE_NAME}:latest"
                    
                    # Show image info
                    NEW_IMAGE_SIZE=$(docker images --format "{{.Size}}" "$IMAGE_NAME" | head -n 1)
                    NEW_IMAGE_ID=$(docker images --format "{{.ID}}" "$IMAGE_NAME" | head -n 1)
                    echo -e "${GREEN}✓${NC} Image: ${IMAGE_NAME}:latest (${NEW_IMAGE_SIZE}, ID: ${NEW_IMAGE_ID:0:12})"
                else
                    echo ""
                    echo -e "${RED}✗${NC} Failed to pull Docker image from GitHub Container Registry"
                    echo ""
                    echo -e "${YELLOW}Possible issues:${NC}"
                    echo "  • Image may not be published yet"
                    echo "  • Network connectivity issues"
                    echo "  • GitHub Container Registry may be unavailable"
                    echo ""
                    read -p "Would you like to build locally instead? (y/N) " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        exit 1
                    fi
                    IMAGE_SOURCE="1"
                fi
            else
                echo -e "${BLUE}[DRY-RUN]${NC} Would pull $GHCR_IMAGE"
            fi
        fi
        
        if [ "$IMAGE_SOURCE" = "1" ]; then
            # Build locally
            echo "Building Docker image..."
            echo ""
            
            # Check if Dockerfile exists
            if [ ! -f "$PROJECT_DIR/docker/Dockerfile" ]; then
                echo -e "${RED}✗ docker/Dockerfile not found!${NC}"
                echo -e "${YELLOW}Expected location: $PROJECT_DIR/docker/Dockerfile${NC}"
                exit 1
            fi
            
            # Check if requirements.txt exists
            if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
                echo -e "${YELLOW}⚠ requirements.txt not found${NC}"
            fi
            
            # Build the image
            echo "Building from: $PROJECT_DIR/docker/Dockerfile"
            echo "Build context: $PROJECT_DIR"
            echo ""
            cd "$PROJECT_DIR"
            
            if [ "$DRY_RUN" = false ]; then
                BUILD_OUTPUT=$(mktemp)
                if docker build -t $IMAGE_NAME -f docker/Dockerfile . 2>&1 | tee "$BUILD_OUTPUT"; then
                    echo ""
                    echo -e "${GREEN}✓${NC} Docker image built successfully!"
                    
                    # Show image info
                    NEW_IMAGE_SIZE=$(docker images --format "{{.Size}}" "$IMAGE_NAME" | head -n 1)
                    NEW_IMAGE_ID=$(docker images --format "{{.ID}}" "$IMAGE_NAME" | head -n 1)
                    echo -e "${GREEN}✓${NC} Image: ${IMAGE_NAME}:latest (${NEW_IMAGE_SIZE}, ID: ${NEW_IMAGE_ID:0:12})"
                else
                    echo ""
                    echo -e "${RED}✗${NC} Failed to build Docker image"
                    echo ""
                    echo -e "${YELLOW}Common issues and solutions:${NC}"
                    
                    # Analyze build output for common errors
                    if grep -q "no space left on device" "$BUILD_OUTPUT"; then
                        echo -e "${RED}  • No space left on device${NC}"
                        echo "    Solution: Free up disk space or clean Docker cache"
                        echo "    Run: docker system prune -a"
                    fi
                    
                    if grep -q "Cannot connect to the Docker daemon" "$BUILD_OUTPUT"; then
                        echo -e "${RED}  • Cannot connect to Docker daemon${NC}"
                        echo "    Solution: Make sure Docker is running"
                        echo "    Run: sudo systemctl start docker"
                    fi
                    
                    if grep -q "denied" "$BUILD_OUTPUT" || grep -q "permission denied" "$BUILD_OUTPUT"; then
                        echo -e "${RED}  • Permission denied${NC}"
                        echo "    Solution: Add user to docker group"
                        echo "    Run: sudo usermod -aG docker $ACTUAL_USER"
                        echo "    Then log out and back in"
                    fi
                    
                    if grep -q "Dockerfile" "$BUILD_OUTPUT" && grep -q "not found" "$BUILD_OUTPUT"; then
                        echo -e "${RED}  • Dockerfile not found or invalid${NC}"
                        echo "    Solution: Verify docker/Dockerfile exists and is readable"
                        echo "    Path: $PROJECT_DIR/docker/Dockerfile"
                    fi
                    
                    if grep -q "requirements.txt" "$BUILD_OUTPUT"; then
                        echo -e "${RED}  • Missing Python dependencies${NC}"
                        echo "    Solution: Verify requirements.txt exists"
                        echo "    Path: $PROJECT_DIR/requirements.txt"
                    fi
                    
                    echo ""
                    echo -e "${YELLOW}Troubleshooting steps:${NC}"
                    echo "  1. Check Docker is running: docker ps"
                    echo "  2. Clean Docker cache: docker system prune -a"
                    echo "  3. Verify files exist: ls -la docker/Dockerfile requirements.txt"
                    echo "  4. Check build logs above for specific errors"
                    echo "  5. Try manual build: cd $PROJECT_DIR && docker build -t boon-tube-daemon -f docker/Dockerfile ."
                    echo ""
                    
                    rm -f "$BUILD_OUTPUT"
                    exit 1
                fi
                
                rm -f "$BUILD_OUTPUT"
            else
                echo -e "${BLUE}[DRY-RUN]${NC} Would build Docker image from $PROJECT_DIR/docker/Dockerfile"
            fi
        fi
    fi
    
    # ============================================================================
    # CREATE SYSTEMD SERVICE FOR DOCKER (Requires root)
    # ============================================================================
    SERVICE_FILE="/etc/systemd/system/boon-tube-daemon.service"
    echo ""
    echo "Creating systemd service file for Docker..."
    echo -e "${YELLOW}(This step requires sudo/root)${NC}"
    echo ""

    if [ "$DRY_RUN" = false ]; then
        # Create temp file first, then copy with sudo
        TEMP_SERVICE=$(mktemp)
        cat > "$TEMP_SERVICE" << EOF
[Unit]
Description=Boon-Tube-Daemon - Multi-platform Live Stream Monitor (Docker)
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
ExecStartPre=-$DOCKER_PATH stop boon-tube-daemon
ExecStartPre=-$DOCKER_PATH rm -f boon-tube-daemon

# Start the Docker container
ExecStart=$DOCKER_PATH run -d \\
    --name boon-tube-daemon \\
    --restart unless-stopped \\
    --env-file $PROJECT_DIR/.env \\
    -v $PROJECT_DIR/messages.txt:/app/messages.txt:ro \\
    -v $PROJECT_DIR/end_messages.txt:/app/end_messages.txt:ro \\
    $IMAGE_NAME

# Stop and remove the container
ExecStop=$DOCKER_PATH stop boon-tube-daemon
ExecStopPost=$DOCKER_PATH rm -f boon-tube-daemon

StandardOutput=journal
StandardError=journal
SyslogIdentifier=boon-tube-daemon

[Install]
WantedBy=multi-user.target
EOF
        
        # Copy to system location with sudo
        run_with_sudo cp "$TEMP_SERVICE" "$SERVICE_FILE"
        run_with_sudo chmod 644 "$SERVICE_FILE"
        rm -f "$TEMP_SERVICE"
        echo -e "${GREEN}✓${NC} Service file created: $SERVICE_FILE"
    else
        echo -e "${BLUE}[DRY-RUN]${NC} Would create service file at $SERVICE_FILE"
    fi
fi

# ============================================================================
# FINALIZE INSTALLATION (Requires root for systemctl commands)
# ============================================================================

# Reload systemd
echo ""
echo "Reloading systemd..."
echo -e "${YELLOW}(This step requires sudo/root)${NC}"
if [ "$DRY_RUN" = false ]; then
    run_with_sudo systemctl daemon-reload
    echo -e "${GREEN}✓${NC} systemd reloaded"
else
    echo -e "${BLUE}[DRY-RUN]${NC} Would reload systemd"
fi

# Enable service
echo ""
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    read -p "Enable Boon-Tube-Daemon to start on boot? (Y/n) " -n 1 -r
    echo
    ENABLE_SERVICE=$REPLY
else
    ENABLE_SERVICE="y"
fi

if [[ ! $ENABLE_SERVICE =~ ^[Nn]$ ]]; then
    if [ "$DRY_RUN" = false ]; then
        run_with_sudo systemctl enable boon-tube-daemon.service
        echo -e "${GREEN}✓${NC} Service enabled (will start on boot)"
    else
        echo -e "${BLUE}[DRY-RUN]${NC} Would enable service"
    fi
fi

# Start service
echo ""
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    read -p "Start Boon-Tube-Daemon now? (Y/n) " -n 1 -r
    echo
    START_SERVICE=$REPLY
else
    START_SERVICE="y"
fi

if [[ ! $START_SERVICE =~ ^[Nn]$ ]]; then
    if [ "$DRY_RUN" = false ]; then
        run_with_sudo systemctl start boon-tube-daemon.service
        sleep 2
        if systemctl is-active --quiet boon-tube-daemon.service; then
            echo -e "${GREEN}✓${NC} Service started successfully!"
        else
            echo -e "${RED}✗${NC} Service failed to start. Check status with: sudo systemctl status boon-tube-daemon"
        fi
    else
        echo -e "${BLUE}[DRY-RUN]${NC} Would start service"
    fi
fi

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Service management commands:"
echo "  Start:   sudo systemctl start boon-tube-daemon"
echo "  Stop:    sudo systemctl stop boon-tube-daemon"
echo "  Restart: sudo systemctl restart boon-tube-daemon"
echo "  Status:  sudo systemctl status boon-tube-daemon"
echo "  Logs:    sudo journalctl -u boon-tube-daemon -f"
echo "  Enable:  sudo systemctl enable boon-tube-daemon"
echo "  Disable: sudo systemctl disable boon-tube-daemon"
echo ""
