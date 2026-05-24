#!/bin/bash
# Start Model Browser on Bazzite using Distrobox
# Uses the same container as ComfyUI (comfyui)

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODEL_BROWSER_DIR="$SCRIPT_DIR"

# Check if the comfyui distrobox exists
if ! distrobox list | grep -q "comfyui"; then
    echo "Error: 'comfyui' Distrobox container not found."
    echo "Please create it first with:"
    echo "  distrobox create --name comfyui --image ubuntu:22.04 --nvidia"
    read -p "Press Enter to close..."
    exit 1
fi

# Check if Model Browser is already running on port 8001
if lsof -i :8001 > /dev/null 2>&1; then
    echo "Model Browser appears to be already running on port 8001."
    echo "Stop it first or use a different port."
    read -p "Press Enter to close..."
    exit 1
fi

echo "🎨 Model Gallery Server"
echo "======================="
echo ""
echo "Starting Model Browser in Distrobox..."
echo "Model Browser will be available at: http://localhost:8001"
echo ""
echo "📝 Configuration:"
echo "   • Model Root: /media/simon/4TBDrive/Chris/AI_Master/stable-diffusion-webui-forge/models"
echo "   • Whitelisted Folders: Stable-diffusion, Lora"
echo "   • Server Port: 8001"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""
echo "==============================================="
echo ""

# Function to open browser after a delay
open_browser() {
    sleep 3
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8001/ &
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Model Browser..."
    # Kill model_server.py INSIDE the container using podman exec (fast + direct,
    # unlike distrobox enter which spins up a full session and can hang during shutdown)
    podman exec comfyui pkill -f "model_server.py" 2>/dev/null || true
    # Kill the host-side distrobox/podman process
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill "$SERVER_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$SERVER_PID" 2>/dev/null || true
    fi
    # Final fallback: kill anything left on port 8001
    lsof -ti:8001 2>/dev/null | xargs kill -9 2>/dev/null || true
    echo "✓ Server stopped."
}

# Set trap to cleanup on script exit, Ctrl+C, terminal close, or termination
trap cleanup EXIT INT TERM HUP

# Open browser in background
open_browser &

# Run Model Browser server within the Distrobox.
# 'exec' replaces the intermediate bash shell so signals reach python directly.
distrobox enter comfyui -- bash -c "cd '$MODEL_BROWSER_DIR' && exec python3 model_server.py" &
SERVER_PID=$!
wait $SERVER_PID 2>/dev/null

# Keep terminal open after server exits
echo ""
echo "----------------------------------------"
echo "Model Browser has stopped."
read -p "Press Enter to close this window..."
