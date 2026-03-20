#!/bin/bash
# Build the VibeSci CLI as a standalone macOS binary and package as .dmg
#
# Output:
#   dist/proposal          — standalone binary (~32 MB)
#   dist/VibeSci.dmg       — distributable disk image
#
# Usage:
#   ./build.sh
#
# Prerequisites on the target Mac:
#   - Claude Code CLI installed (claude command available)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="VibeSci"
BINARY_NAME="proposal"
DMG_NAME="${APP_NAME}.dmg"
VERSION="0.1.0"

echo "=== ${APP_NAME}: Building standalone binary ==="

# Ensure dependencies are installed
echo "→ Checking dependencies..."
pip3 install -e . --quiet 2>/dev/null
pip3 install pyinstaller --quiet 2>/dev/null

# Clean previous builds
echo "→ Cleaning previous builds..."
rm -rf build/ dist/

# Build binary
echo "→ Building with PyInstaller..."
python3 -m PyInstaller proposal.spec --noconfirm

if [ ! -f "dist/${BINARY_NAME}" ]; then
    echo "ERROR: Build failed — dist/${BINARY_NAME} not found"
    exit 1
fi

BINARY_SIZE=$(du -sh "dist/${BINARY_NAME}" | cut -f1)
echo "  Binary: dist/${BINARY_NAME} (${BINARY_SIZE})"

# Package as .dmg
echo "→ Packaging .dmg..."

DMG_DIR="dist/dmg_staging"
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy binary
cp "dist/${BINARY_NAME}" "$DMG_DIR/"

# Create installer script inside the DMG
cat > "$DMG_DIR/Install.command" << 'INSTALLER'
#!/bin/bash
# VibeSci Installer — double-click to install

set -e

BINARY="proposal"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/local/bin"

echo ""
cat << 'LOGO'
   _    ___ __        _____      _
  | |  / (_) /_  ___ / ___/_____(_)
  | | / / / __ \/ _ \\__ \/ ___/ /
  | |/ / / /_/ /  __/__/ / /__/ /
  |___/_/_.___/\___/____/\___/_/
LOGO
echo ""
echo "  Research Proposal Generator by www.opensci.io"
echo ""

# Check source binary exists
if [ ! -f "$SOURCE_DIR/$BINARY" ]; then
    echo "  ERROR: $BINARY not found in $SOURCE_DIR"
    echo "  Make sure you are running this from the VibeSci disk image."
    echo ""
    read -n 1 -s -r -p "  Press any key to close..."
    exit 1
fi

# Create /usr/local/bin if needed (requires sudo)
if [ ! -d "$INSTALL_DIR" ]; then
    echo "  Creating $INSTALL_DIR (requires admin password)..."
    sudo mkdir -p "$INSTALL_DIR"
fi

# Copy binary
echo "  Installing $BINARY to $INSTALL_DIR..."
sudo cp "$SOURCE_DIR/$BINARY" "$INSTALL_DIR/$BINARY"
sudo chmod +x "$INSTALL_DIR/$BINARY"

echo ""
echo "  ✓ Installed successfully!"
echo ""
echo "  Launching proposal..."
sleep 1

# Open a new Terminal window running proposal
osascript -e '
tell application "Terminal"
    activate
    do script "cd ~/Desktop && proposal"
end tell
'

# Close this installer window
osascript -e '
tell application "Terminal"
    close (every window whose name contains "Install.command")
end tell
' &
INSTALLER
chmod +x "$DMG_DIR/Install.command"

# Create the .dmg
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}" \
    2>/dev/null

rm -rf "$DMG_DIR"

if [ -f "dist/${DMG_NAME}" ]; then
    DMG_SIZE=$(du -sh "dist/${DMG_NAME}" | cut -f1)
    echo ""
    echo "=== Build complete! ==="
    echo "  Binary : dist/${BINARY_NAME} (${BINARY_SIZE})"
    echo "  DMG    : dist/${DMG_NAME} (${DMG_SIZE})"
    echo ""
    echo "Distribute dist/${DMG_NAME} — users open it and double-click Install.command"
else
    echo "ERROR: DMG creation failed"
    exit 1
fi
