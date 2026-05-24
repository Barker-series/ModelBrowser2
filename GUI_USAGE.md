# Model Browser GUI - Usage Guide

Your Model Browser now has a beautiful graphical interface! No more terminal issues with COSMIC.

## What Changed

✅ **NEW**: Python GUI with Start/Stop buttons
✅ **NEW**: Live server log viewer
✅ **NEW**: One-click browser opening
✅ **FIXED**: Works perfectly on COSMIC Desktop (no terminal needed!)

## How to Use

### Option 1: Run the AppImage (Recommended)

Simply double-click:
```
ModelBrowser-x86_64.AppImage
```

Or from terminal:
```bash
./ModelBrowser-x86_64.AppImage
```

### Option 2: Run the GUI Directly

If you're in the development directory:
```bash
python3 model_browser_gui.py
```

## GUI Features

### Main Window
- **Status Indicator**: Shows if server is running (● Running / ● Stopped)
- **Start Server Button**: Starts the model browser server
- **Stop Server Button**: Cleanly stops the server
- **Open Browser Button**: Opens http://localhost:8001 in your default browser
- **Server Log**: Real-time log viewer showing all server activity

### First Run
On first launch, the GUI will:
1. Create a virtual environment (if needed)
2. Install Pillow (if needed)
3. Enable the Start button when ready

This takes ~30 seconds on first run, then it's instant afterwards.

### Using the Server
1. Click **"▶ Start Server"**
2. Wait for "Server started" message
3. Browser will auto-open to http://localhost:8001
4. Browse your AI models!
5. When done, click **"■ Stop Server"**

### Closing the GUI
- If server is running, you'll be asked to confirm
- Click "Yes" to stop the server and quit
- Click "No" to keep it running and return to the GUI

## Benefits of the GUI

### ✅ Works on COSMIC Desktop
- No terminal emulator issues
- Native GUI experience
- Follows COSMIC design patterns

### ✅ Better User Experience
- Visual feedback of server status
- Easy start/stop with buttons
- Live log viewing
- One-click browser access

### ✅ Reliable
- Clean server shutdown
- Automatic cleanup on exit
- Error messages shown in GUI

## Troubleshooting

### GUI doesn't launch
Make sure Python 3 and tkinter are installed:
```bash
sudo apt install python3 python3-tk
```

### "Pillow not found" error
The GUI will automatically install Pillow on first run.
If it fails, install manually:
```bash
pip3 install Pillow
```

### Port 8001 already in use
If the server was previously running, stop it:
```bash
pkill -f model_server.py
# or
lsof -ti:8001 | xargs kill
```

## Files

- `ModelBrowser-x86_64.AppImage` - Portable AppImage (recommended)
- `model_browser_gui.py` - GUI launcher script
- `model_server.py` - The actual server
- `index.html` - Web interface
- `config.json` - Server configuration

## Configuration

The server configuration is in `config.json`:
```json
{
  "modelRoot": "/path/to/your/models",
  "folderWhitelist": ["Stable-diffusion", "Lora"]
}
```

You can also change these settings through the web interface once the server is running.

## Command Line Options

The original terminal-based launcher is still available:
```bash
./start_server.sh
```

This is useful for:
- SSH sessions
- Automation scripts
- Debugging

---

**Enjoy your new GUI! 🎨**
