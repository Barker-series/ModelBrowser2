# Building ModelBrowser as an AppImage

## How the Script Works

The `start_server.sh` script now automatically detects its environment:

- **Regular Mode**: Uses the script's actual directory and creates `venv/` locally
- **AppImage Mode**: Detects when running from an AppImage and:
  - Uses `$APPDIR` for the read-only app files
  - Stores the virtual environment in `~/.local/share/ModelBrowser/venv`
  - Automatically installs dependencies on first run

## AppImage Structure

When building your AppImage, you'll need to include:

```
ModelBrowser.AppDir/
├── AppRun                  # Your start_server.sh (renamed/symlinked)
├── model_browser.desktop   # Desktop entry file
├── model_browser.png       # App icon
├── model_server.py         # Python server
├── index.html              # Web interface
├── config.json             # Configuration (optional)
└── usr/
    └── bin/
        └── python3         # Bundled Python (or rely on system)
```

## Building the AppImage

### Option 1: Using appimagetool (Recommended)

```bash
# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Create AppDir structure
mkdir -p ModelBrowser.AppDir
cp start_server.sh ModelBrowser.AppDir/AppRun
cp model_server.py index.html ModelBrowser.AppDir/
cp config.json ModelBrowser.AppDir/  # if you have one

# Create desktop entry
cat > ModelBrowser.AppDir/model_browser.desktop << 'EOF'
[Desktop Entry]
Name=Model Browser
Exec=AppRun
Icon=model_browser
Type=Application
Categories=Graphics;Utility;
EOF

# Add an icon (you'll need to create or find one)
# cp your_icon.png ModelBrowser.AppDir/model_browser.png

# Build the AppImage
./appimagetool-x86_64.AppImage ModelBrowser.AppDir ModelBrowser-x86_64.AppImage
```

### Option 2: Using python-appimage

For bundling Python with your app:

```bash
pip install python-appimage

python-appimage build app \
    -l manylinux2014_x86_64 \
    -p 3.12 \
    ModelBrowser.AppDir
```

## Testing Your AppImage

```bash
chmod +x ModelBrowser-x86_64.AppImage
./ModelBrowser-x86_64.AppImage
```

On first run, it will:
1. Create `~/.local/share/ModelBrowser/venv`
2. Install Pillow automatically
3. Start the server on http://localhost:8001

## Notes

- The AppImage will be portable but needs Python 3 installed on the system
- To fully bundle Python, use python-appimage or include Python in the AppDir
- Configuration and virtual environment persist in user's home directory
- Models directory path is configured via `config.json`
