#!/bin/bash
#
# JARVIS Phase 1 Installation Script
# For Kubuntu 24.04
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/models"

echo "=========================================="
echo "  JARVIS Phase 1 - Installation Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running on Kubuntu/Ubuntu
if ! command -v apt &> /dev/null; then
    print_error "This script is designed for Debian/Ubuntu-based systems"
    exit 1
fi

# 1. Install system dependencies
echo ""
echo "1. Installing system dependencies..."
echo "-----------------------------------"

sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    ffmpeg \
    libsndfile1

print_status "System dependencies installed"

# 2. Create virtual environment
echo ""
echo "2. Setting up Python virtual environment..."
echo "--------------------------------------------"

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

source "$SCRIPT_DIR/venv/bin/activate"

# 3. Install Python dependencies
echo ""
echo "3. Installing Python packages..."
echo "--------------------------------"

pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

print_status "Python packages installed"

# 4. Download Vosk model (Spanish)
echo ""
echo "4. Downloading Vosk STT model..."
echo "--------------------------------"

mkdir -p "$MODELS_DIR"
VOSK_MODEL="vosk-model-small-es-0.42"
VOSK_MODEL_PATH="$MODELS_DIR/$VOSK_MODEL"

if [ ! -d "$VOSK_MODEL_PATH" ]; then
    echo "Downloading $VOSK_MODEL..."
    wget -q --show-progress -P "$MODELS_DIR" \
        "https://alphacephei.com/vosk/models/$VOSK_MODEL.zip"

    echo "Extracting..."
    unzip -q "$MODELS_DIR/$VOSK_MODEL.zip" -d "$MODELS_DIR"
    rm "$MODELS_DIR/$VOSK_MODEL.zip"

    print_status "Vosk model downloaded: $VOSK_MODEL"
else
    print_warning "Vosk model already exists"
fi

# 5. Download Piper TTS model (Spanish)
echo ""
echo "5. Downloading Piper TTS model..."
echo "---------------------------------"

PIPER_MODEL="es_ES-davefx-medium"
PIPER_MODEL_FILE="$MODELS_DIR/$PIPER_MODEL.onnx"

if [ ! -f "$PIPER_MODEL_FILE" ]; then
    echo "Downloading $PIPER_MODEL..."

    # Piper models from HuggingFace
    BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium"

    wget -q --show-progress -O "$MODELS_DIR/$PIPER_MODEL.onnx" \
        "$BASE_URL/$PIPER_MODEL.onnx"
    wget -q --show-progress -O "$MODELS_DIR/$PIPER_MODEL.onnx.json" \
        "$BASE_URL/$PIPER_MODEL.onnx.json"

    print_status "Piper model downloaded: $PIPER_MODEL"
else
    print_warning "Piper model already exists"
fi

# 6. Download OpenWakeWord models
echo ""
echo "6. Setting up OpenWakeWord..."
echo "-----------------------------"

# OpenWakeWord downloads models automatically on first use
# We'll trigger this by importing the module
python3 -c "
from openwakeword.model import Model
print('Downloading OpenWakeWord models...')
model = Model(wakeword_models=['alexa'], inference_framework='onnx')
print('OpenWakeWord models ready')
" 2>/dev/null || print_warning "OpenWakeWord model download will happen on first run"

print_status "OpenWakeWord configured"

# 7. Verify Claude CLI
echo ""
echo "7. Checking Claude CLI..."
echo "-------------------------"

if command -v claude &> /dev/null; then
    print_status "Claude CLI found: $(which claude)"
else
    print_warning "Claude CLI not found in PATH"
    echo "    Install Claude CLI before running JARVIS:"
    echo "    npm install -g @anthropic-ai/claude-cli"
    echo "    (or follow official installation instructions)"
fi

# 8. Test audio
echo ""
echo "8. Testing audio setup..."
echo "-------------------------"

python3 -c "
import sounddevice as sd
print('Available audio devices:')
print(sd.query_devices())
" || print_warning "Audio device query failed"

# 9. Create run script
echo ""
echo "9. Creating run script..."
echo "-------------------------"

cat > "$SCRIPT_DIR/run_jarvis.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/jarvis.py" "$@"
EOF

chmod +x "$SCRIPT_DIR/run_jarvis.sh"
print_status "Run script created: run_jarvis.sh"

# Done
echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "To run JARVIS:"
echo "  cd $SCRIPT_DIR"
echo "  ./run_jarvis.sh"
echo ""
echo "Or with verbose logging:"
echo "  ./run_jarvis.sh -v"
echo ""
echo "Note: Say 'Alexa' to activate (custom 'Jarvis' wake word"
echo "      will be added in a future update)"
echo ""
print_warning "Make sure your microphone is working before running!"
echo ""
