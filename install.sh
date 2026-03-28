#!/bin/bash
set -e

echo "=== SpeechToText Installer ==="
echo ""

# System dependencies
echo "[1/5] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    gir1.2-gst-1.0 \
    gir1.2-ayatanaappindicator3-0.1 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-pulseaudio \
    xdotool \
    python3-pip \
    python3-venv

# Install Python package
echo "[2/5] Installing SpeechToText..."
cd "$(dirname "$0")"
pip3 install --user --break-system-packages . 2>/dev/null || pip3 install --user .

# Install icon
echo "[3/5] Installing icon..."
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
cp assets/icon.svg "$ICON_DIR/speechtotext.svg"

# Install desktop file
echo "[4/5] Installing desktop entry..."
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
EXEC_PATH="$(python3 -c 'import site; print(site.getusersitepackages().replace("lib/python3", "bin").rsplit("/lib", 1)[0])')/bin/speechtotext"
# Fallback: check if it's on PATH
if [ ! -f "$EXEC_PATH" ]; then
    EXEC_PATH="$(which speechtotext 2>/dev/null || echo "$HOME/.local/bin/speechtotext")"
fi
sed "s|Exec=speechtotext|Exec=$EXEC_PATH|g; s|Icon=speechtotext|Icon=$ICON_DIR/speechtotext.svg|g" \
    speechtotext.desktop > "$DESKTOP_DIR/speechtotext.desktop"

# Autostart entry (system tray on login)
echo "[5/5] Setting up autostart..."
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cp "$DESKTOP_DIR/speechtotext.desktop" "$AUTOSTART_DIR/speechtotext.desktop"

# Update desktop database
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "=== Installation complete! ==="
echo "You can find SpeechToText in your application menu."
echo "It will also autostart with your session (system tray icon)."
echo ""
echo "Make sure your API key is configured in ~/.config/speechtotext/config.json"
