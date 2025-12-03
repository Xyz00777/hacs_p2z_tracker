#!/usr/bin/env bash
# NixOS build script for Person Zone Time Tracker integration
# Creates a ZIP file ready for upload to Home Assistant
# Uses nix-shell for dependencies

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Person Zone Time Tracker - NixOS Build Script${NC}"
echo ""

# Check if we're running in nix-shell
if [ -z "$IN_NIX_SHELL" ]; then
    echo "Setting up Nix environment with required dependencies..."
    # Re-run this script inside nix-shell with required dependencies
    exec nix-shell -p bash coreutils findutils gnugrep zip --run "$0 $*"
fi

echo "Running in nix-shell environment"
echo ""

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Get version from manifest.json
VERSION=$(grep -oP '(?<="version": ")[^"]*' "$PROJECT_ROOT/custom_components/p2z_tracker/manifest.json")
echo "Building version: $VERSION"

# Create build directory
BUILD_DIR="$PROJECT_ROOT/build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create temporary directory for the integration
TEMP_DIR="$BUILD_DIR/temp"
mkdir -p "$TEMP_DIR/p2z_tracker"

# Copy integration files
echo "Copying integration files..."
cp -r "$PROJECT_ROOT/custom_components/p2z_tracker/"* "$TEMP_DIR/p2z_tracker/"

# Create ZIP file
ZIP_NAME="p2z_tracker-${VERSION}.zip"
echo ""
echo "Creating ZIP archive: $ZIP_NAME"

cd "$TEMP_DIR"
zip -r "$BUILD_DIR/$ZIP_NAME" p2z_tracker/ -x "*.pyc" "*__pycache__*" "*.git*"

# Clean up temp directory
cd "$PROJECT_ROOT"
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo "Output: $BUILD_DIR/$ZIP_NAME"
echo "Size: $(du -h "$BUILD_DIR/$ZIP_NAME" | cut -f1)"
echo ""
echo "To install in Home Assistant:"
echo "1. Go to Settings → Add-ons → File editor (or use SAMBA/SSH)"
echo "2. Upload $ZIP_NAME to /config/"
echo "3. Unzip: unzip /config/$ZIP_NAME -d /config/custom_components/"
echo "4. Restart Home Assistant"
echo ""
echo -e "${YELLOW}NixOS Note:${NC} You can also use the build/ directory directly"
echo "in your NixOS configuration if managing HA declaratively."
