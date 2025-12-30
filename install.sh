#!/bin/bash
#
# JARVIS Installation Script
# Voice Assistant for Kubuntu/Linux
#
# Usage: ./install.sh [--systemd] [--dev]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$JARVIS_DIR/venv"
MODELS_DIR="$JARVIS_DIR/models"
MEMORY_DIR="$JARVIS_DIR/memory"
LOGS_DIR="$JARVIS_DIR/logs"

# Parse arguments
INSTALL_SYSTEMD=false
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --systemd)
            INSTALL_SYSTEMD=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║     JARVIS Installation Script             ║"
echo "║     Voice Assistant for Kubuntu            ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Check for required system packages
echo -e "${YELLOW}Checking system dependencies...${NC}"

REQUIRED_PACKAGES=(
    "python3"
    "python3-venv"
    "python3-pip"
    "portaudio19-dev"
    "libsndfile1"
    "ffmpeg"
    "espeak-ng"
)

OPTIONAL_PACKAGES=(
    "xdotool"
    "spectacle"
)

MISSING_PACKAGES=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" &> /dev/null; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Installing missing packages: ${MISSING_PACKAGES[*]}${NC}"
    sudo apt-get update
    sudo apt-get install -y "${MISSING_PACKAGES[@]}"
fi

# Install optional packages
echo -e "${YELLOW}Installing optional packages...${NC}"
for pkg in "${OPTIONAL_PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" &> /dev/null; then
        sudo apt-get install -y "$pkg" || echo -e "${YELLOW}Optional package $pkg not available${NC}"
    fi
done

# Create directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$MODELS_DIR"
mkdir -p "$MEMORY_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p "$JARVIS_DIR/sounds"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r "$JARVIS_DIR/requirements.txt"

if [ "$DEV_MODE" = true ]; then
    echo -e "${YELLOW}Installing development dependencies...${NC}"
    pip install pytest pytest-mock pytest-asyncio ruff
fi

# Download models if not present
echo -e "${YELLOW}Checking models...${NC}"

# Vosk Spanish model
VOSK_MODEL="vosk-model-small-es-0.42"
if [ ! -d "$MODELS_DIR/$VOSK_MODEL" ]; then
    echo -e "${YELLOW}Downloading Vosk Spanish model...${NC}"
    cd "$MODELS_DIR"
    wget -q "https://alphacephei.com/vosk/models/$VOSK_MODEL.zip" -O "$VOSK_MODEL.zip"
    unzip -q "$VOSK_MODEL.zip"
    rm "$VOSK_MODEL.zip"
    cd "$JARVIS_DIR"
fi

# Piper TTS model
PIPER_MODEL="es_ES-davefx-medium.onnx"
if [ ! -f "$MODELS_DIR/$PIPER_MODEL" ]; then
    echo -e "${YELLOW}Downloading Piper TTS model...${NC}"
    cd "$MODELS_DIR"
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/$PIPER_MODEL"
    wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/$PIPER_MODEL.json"
    cd "$JARVIS_DIR"
fi

# Create default config if not exists
if [ ! -f "$JARVIS_DIR/config.yaml" ]; then
    echo -e "${YELLOW}Creating default configuration...${NC}"
    cp "$JARVIS_DIR/config.yaml.example" "$JARVIS_DIR/config.yaml" 2>/dev/null || true
fi

# Install systemd service
if [ "$INSTALL_SYSTEMD" = true ]; then
    echo -e "${YELLOW}Installing systemd service...${NC}"

    SERVICE_FILE="/etc/systemd/system/jarvis.service"

    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=JARVIS Voice Assistant
After=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$JARVIS_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
Environment="DISPLAY=:0"
Environment="XDG_RUNTIME_DIR=/run/user/$(id -u)"
ExecStart=$VENV_DIR/bin/python $JARVIS_DIR/jarvis.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable jarvis.service

    echo -e "${GREEN}Systemd service installed. Use:${NC}"
    echo "  sudo systemctl start jarvis    # Start JARVIS"
    echo "  sudo systemctl stop jarvis     # Stop JARVIS"
    echo "  sudo systemctl status jarvis   # Check status"
    echo "  journalctl -u jarvis -f        # View logs"
fi

# Run tests if in dev mode
if [ "$DEV_MODE" = true ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    python -m pytest tests/ -q || true
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     JARVIS Installation Complete!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "To start JARVIS:"
echo -e "  ${BLUE}cd $JARVIS_DIR${NC}"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo -e "  ${BLUE}python jarvis.py${NC}"
echo ""
echo -e "Or with verbose logging:"
echo -e "  ${BLUE}python jarvis.py -v${NC}"
echo ""

if [ "$INSTALL_SYSTEMD" = true ]; then
    echo -e "Or as a service:"
    echo -e "  ${BLUE}sudo systemctl start jarvis${NC}"
fi

echo -e "${GREEN}Enjoy your AI assistant!${NC}"
