# SafeTensors Model Browser

A standalone web-based gallery for managing and browsing Stable Diffusion models (checkpoints, LoRAs, etc.) with a familiar interface inspired by A1111's model viewer.

## Features

### Backend (Python)
- **HTTP Server**: Lightweight Python-based server that scans your models folder recursively
- **Model Support**: Works with `.ckpt`, `.safetensors`, `.pt`, `.pth`, and `.bin` files
- **Smart Thumbnail Caching**: Generates 512px thumbnails (longest side) with `aig_` prefix in `thumbs/` subfolders. Uses PIL's `thumbnail()` + `draft()` for low memory use and forces regen on each cache pass
- **Drag & Drop Upload**: Upload custom thumbnails for models via drag and drop
- **JSON Metadata**: Store and manage metadata for each model in companion JSON files
- **URL Extraction**: Pulls the first URL out of each model's description so the gallery can link straight to its source page
- **File Explorer Integration**: Open file location directly from the browser
- **Configuration Persistence**: Settings saved to `config.json`

### Frontend
- **Tree Navigation**: Hierarchical folder tree on the left sidebar
- **Gallery Grid View**: Card-based layout inspired by ComfyUI-Lora-Manager, with full-bleed previews and a frosted-glass footer showing the model name
- **Per-card quick actions**:
  - Globe icon — opens the model's source URL in a new tab
  - Folder-open icon — opens the model's location in your system file manager
- **Folder badge & date badge** floating over each thumbnail
- **Polished header**: command-palette-style centered search and a round settings button
- **Search Functionality**: Search models by name or description
- **Sorting Options**: Sort by name (A-Z) or modification date
- **Model Details Modal**: Popup with comprehensive model information including description, SD version, activation text, post prompt, preferred weight, negative text, notes, plus checkpoint-specific settings (checkpoint, VAE, steps, CFG scale, sampler, scheduler, width, height)

### Design
- Dark, OLED-friendly theme with purple accent
- Frosted-glass card footers, hover lift, and smooth transitions
- Responsive grid that adapts from ~180px cards on mobile up to ~280px on 4K displays

## Requirements

- Python 3.6 or higher
- PIL/Pillow (for thumbnail generation)
- Web browser (Chrome, Firefox, Edge, Safari)

## Installation

1. Clone or download this repository
2. Ensure Python 3 is installed on your system
3. Install dependencies (if not already installed):
   ```bash
   pip3 install Pillow
   ```

## Usage

### Linux (Primary Testing Platform)

This project is primarily tested on Linux. To start the server:

```bash
./start_server.sh
```

Make sure the script is executable:
```bash
chmod +x start_server.sh
```

The startup script will:
- Check for Python 3 installation
- Verify required modules
- Clean up any existing server processes on port 8001
- Start the server
- Automatically open your browser to `http://localhost:8001/`

### Windows

```cmd
start_server.bat
```

### Manual Start

```bash
python3 model_server.py
```

Then open your browser to: `http://localhost:8001/`

## Configuration

On first run, click the **Settings** button (⚙️) in the top right corner to configure:

1. **Model Root Directory**: Path to your models folder
   - Example: `/media/simon/4TBDrive/Chris/AI_Master/stable-diffusion-webui-forge/models`

2. **Folder Whitelist**: Comma-separated list of folders to scan
   - Example: `Stable-diffusion,Lora,checkpoints`

3. Click **Save Settings** to persist your configuration

4. Click **Load Files** to scan your models

Configuration is saved to `config.json` in the application directory.

### Default Configuration

```json
{
  "modelRoot": "/path/to/your/models",
  "folderWhitelist": [
    "Stable-diffusion",
    "Lora",
    "checkpoints"
  ]
}
```

## File Structure

```
ModelBrowser/
├── index.html          # Main web interface
├── model_server.py     # Python HTTP server
├── config.json         # Configuration file (created on first save)
├── start_server.sh     # Linux startup script
├── start_server.bat    # Windows startup script
└── README.md           # This file
```

## How It Works

1. **Scanning**: The server recursively scans the model root directory for compatible files
2. **Filtering**: Only folders in the whitelist are displayed
3. **Thumbnails**:
   - Looks for existing PNG files matching model names
   - Generates cached 512px versions (longest side) in `thumbs/` subfolders
   - Falls back to a "No preview" placeholder if no thumbnail exists
4. **Metadata**: Stores model information in JSON files alongside the models
5. **API**: Provides RESTful endpoints for the frontend to fetch data

## Features in Detail

### Thumbnail System
- Original thumbnails: `model_name.png` (stored alongside model)
- Cached thumbnails: `thumbs/aig_model_name.png` (auto-generated)
- Drag & drop to upload custom thumbnails
- "Cache Thumbnails" button to batch-generate cached versions

### Model Information
Each model can store:
- **Description**: General information about the model
- **SD Version**: Which Stable Diffusion version (1.5, 2.0, XL, etc.)
- **Activation Text**: Trigger words or prompts
- **Preferred Weight**: Recommended strength/weight setting
- **Negative Text**: Negative prompts to use
- **Notes**: Any additional information

### File Explorer Integration
Click "Open in Explorer" to:
- **Windows**: Opens Explorer with the file selected
- **macOS**: Opens Finder with the file revealed
- **Linux**: Opens file manager (xdg-open, nautilus, dolphin, or thunar)

## Development Notes

- Primarily developed and tested on **Linux**
- Server runs on port **8001** by default
- CORS enabled for local development
- Supports both local file paths and server-based deployment

## Troubleshooting

### Port Already in Use
If port 8001 is already in use, the `start_server.sh` script will automatically clean it up. Or manually:
```bash
lsof -ti:8001 | xargs kill -9
```

### Permission Denied
Make sure the startup script is executable:
```bash
chmod +x start_server.sh
```

### Thumbnails Not Showing
- Check that thumbnails are named the same as the model file (e.g., `model.safetensors` → `model.png`)
- Use the "Cache Thumbnails" button to generate thumbnails
- Check file permissions on the models directory

### Models Not Appearing
- Verify the Model Root path is correct
- Ensure folder names are in the Folder Whitelist
- Check that files have valid extensions (`.ckpt`, `.safetensors`, etc.)

## AppImage Distribution

A portable AppImage is available for easy distribution on Linux systems, including those with newer desktop environments like COSMIC.

### Using the AppImage

Simply run:
```bash
./ModelBrowser-x86_64.AppImage
```

Or double-click in your file manager. The AppImage includes:
- Python GUI launcher with Start/Stop buttons
- Live server log viewer
- One-click browser opening
- Automatic virtual environment and dependency management

See `GUI_USAGE.md` for full details.

### Building the AppImage

If you need to rebuild the AppImage, see `APPIMAGE_BUILD.md` for instructions.

## Development Lessons: AppImage + Modern Desktop Environments

**Reality Check for Future Developers:**

When building AppImages for interactive server applications on modern Linux desktops (especially COSMIC, which is still in early development):

### ❌ What NOT to Do:
- **Don't fight with terminal emulators**: Trying to force `cosmic-term -e`, `gnome-terminal --`, etc. is a dead end
- **Don't assume old solutions work**: Terminal-based approaches that worked on GNOME 2 may not work on Wayland/COSMIC
- **Don't declare things "impossible"**: If a major desktop environment exists, there's a proper way to do it

### ✅ What TO Do:
1. **Use Python + tkinter GUIs**: This is the modern standard for interactive AppImages
2. **Look for examples first**: Search for similar AppImages and see how they solve the problem
3. **Think about UX**: A GUI with buttons is actually *better* than forcing a terminal:
   - Visual status indicators
   - Start/Stop buttons instead of Ctrl+C
   - Scrollable log viewer
   - One-click features
4. **Research before building**: Look up "appimage interactive application" or "appimage server gui" before implementing

### The Journey:
This AppImage went through several iterations:
1. ❌ Tried using `Terminal=true` in desktop file (doesn't work reliably)
2. ❌ Tried auto-launching terminal emulators from bash script (COSMIC doesn't support `-e` flag)
3. ❌ Almost gave up, declaring it "impossible" on COSMIC
4. ✅ User pointed to example AppImage creator that uses Python GUIs
5. ✅ Built proper tkinter GUI - works everywhere, better UX

**Lesson**: Don't get tunnel vision on one approach. Step back, research how others solve the same problem, and prioritize user experience over technical constraints.

## License

This project is provided as-is for personal use.

## Credits

Inspired by the AUTOMATIC1111 Stable Diffusion WebUI's checkpoint and LoRA browser interface.
