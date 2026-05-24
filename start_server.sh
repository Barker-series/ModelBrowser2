#!/bin/bash

# Model Gallery Server Startup Script
# This script starts the Python server for the model gallery browser

# Check if we're running in a terminal
if [ ! -t 0 ] && [ -z "$LAUNCHED_IN_TERMINAL" ]; then
    # Not in a terminal, try to launch in one
    export LAUNCHED_IN_TERMINAL=1

    # Try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- "$0" "$@"
        exit 0
    elif command -v konsole &> /dev/null; then
        konsole -e "$0" "$@"
        exit 0
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal -e "$0 $*"
        exit 0
    elif command -v cosmic-term &> /dev/null; then
        cosmic-term -e "$0" "$@"
        exit 0
    elif command -v xterm &> /dev/null; then
        xterm -e "$0" "$@"
        exit 0
    else
        # No terminal found, show error
        if command -v zenity &> /dev/null; then
            zenity --info --text="Please run ModelBrowser from a terminal:\n./start_server.sh"
        elif command -v notify-send &> /dev/null; then
            notify-send "Model Browser" "Please run from a terminal"
        fi
        exit 1
    fi
fi

echo "🎨 Model Gallery Server"
echo "======================="
echo ""

# Detect the directory where this script is located
# This works both for regular execution and AppImage packaging
DETECTED_SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

if [ -n "$APPIMAGE" ] && [ -f "$APPDIR/model_server.py" ]; then
    # Running inside a real AppImage - use AppImage directory
    SCRIPT_DIR="$APPDIR"
    # For AppImage, store venv in user's home directory
    VENV_DIR="$HOME/.local/share/ModelBrowser/venv"
    APPIMAGE_MODE=true
    echo "🔧 Running in AppImage mode"
else
    # Regular execution or AppImage env var from another app
    SCRIPT_DIR="$DETECTED_SCRIPT_DIR"
    VENV_DIR="$SCRIPT_DIR/venv"
    APPIMAGE_MODE=false
fi

echo "📁 Script directory: $SCRIPT_DIR"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment not found. Creating it..."
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: Python 3 is not installed or not in PATH"
        echo "Please install Python 3 and try again."
        exit 1
    fi

    # Create parent directory if in AppImage mode
    if [ "$APPIMAGE_MODE" = true ]; then
        mkdir -p "$(dirname "$VENV_DIR")"
    fi

    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "✅ Python 3 found: $(python3 --version)"
echo "✅ Using virtual environment at: $VIRTUAL_ENV"

# Check if Pillow is installed in the virtual environment
echo "🔍 Checking Python dependencies..."
if ! python3 -c "from PIL import Image" &> /dev/null; then
    echo "⚠️  Pillow not found, installing..."
    pip install Pillow
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install Pillow"
        exit 1
    fi
    echo "✅ Pillow installed successfully"
else
    echo "✅ Pillow is available"
fi

echo ""

# Check if the model server script exists
if [ ! -f "model_server.py" ]; then
    echo "❌ Error: model_server.py not found in current directory"
    echo "Make sure you're running this script from the ModelBrowser directory."
    exit 1
fi

# Check if the HTML file exists
if [ ! -f "index.html" ]; then
    echo "❌ Warning: 'index.html' not found"
    echo "Make sure the HTML file is in the same directory."
fi

echo "🚀 Starting Model Gallery Server..."
echo ""
echo "📝 Configuration:"
echo "   • Model Root: /media/simon/4TBDrive/Chris/AI_Master/stable-diffusion-webui-forge/models"
echo "   • Whitelisted Folders: Stable-diffusion, Lora"
echo "   • Server Port: 8001"
echo ""
echo "🌐 Once started, open your browser to:"
echo "   http://localhost:8001/"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo ""
echo "==============================================="
echo ""

# Function to cleanup any existing server process
cleanup_server() {
    echo "🧹 Cleaning up any existing server processes..."
    
    # Kill any process using port 8001
    if lsof -ti:8001 >/dev/null 2>&1; then
        echo "⚠️  Port 8001 is in use. Stopping existing process..."
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # Kill any model_server.py processes
    if pgrep -f "model_server.py" >/dev/null 2>&1; then
        echo "⚠️  Found existing model_server.py process. Stopping it..."
        pkill -f "model_server.py" 2>/dev/null || true
        sleep 1
    fi
}

# Function to open browser
open_browser() {
    sleep 2  # Wait for server to start
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8001/
    elif command -v open &> /dev/null; then
        open http://localhost:8001/
    elif command -v start &> /dev/null; then
        start http://localhost:8001/
    else
        echo "⚠️  Could not auto-open browser. Please manually open: http://localhost:8001/"
    fi
}

# Cleanup any existing server processes
cleanup_server

# Start the Python server and open browser
open_browser &
python3 model_server.py

# Keep terminal open on exit
echo ""
echo "🛑 Server stopped."
echo "Press any key to close this window..."
read -n 1 -s