#!/usr/bin/env python3
"""
Build script to create a macOS .app bundle for Screenshot Tool
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).parent
APP_NAME = "Screenshot Tool"
APP_BUNDLE = PROJECT_DIR / f"{APP_NAME}.app"
CONTENTS = APP_BUNDLE / "Contents"
MACOS = CONTENTS / "MacOS"
RESOURCES = CONTENTS / "Resources"

def create_app_structure():
    """Create the .app bundle directory structure."""
    print("Creating app structure...")

    # Remove old bundle if exists
    if APP_BUNDLE.exists():
        shutil.rmtree(APP_BUNDLE)

    # Create directories
    MACOS.mkdir(parents=True)
    RESOURCES.mkdir(parents=True)

    # Copy source files
    src_dest = RESOURCES / "src"
    shutil.copytree(PROJECT_DIR / "src", src_dest)

    # Copy main.py
    shutil.copy(PROJECT_DIR / "main.py", RESOURCES / "main.py")

def create_launcher():
    """Create the launcher script."""
    print("Creating launcher...")

    launcher_path = MACOS / "Screenshot Tool"

    # Get the path to the venv Python
    venv_python = PROJECT_DIR / "venv" / "bin" / "python"

    launcher_content = f'''#!/bin/bash
# Screenshot Tool Launcher

# Get the directory where the app is located
APP_DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"

# Use the venv Python from the original project location
VENV_PYTHON="{venv_python}"

# Fallback to system Python if venv not found
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON=$(which python3)
fi

# Set environment
export PYTHONPATH="$APP_DIR"

# Run the app
cd "$APP_DIR"
exec "$VENV_PYTHON" "$APP_DIR/main.py"
'''

    launcher_path.write_text(launcher_content)
    os.chmod(launcher_path, 0o755)

def create_info_plist():
    """Create Info.plist file."""
    print("Creating Info.plist...")

    plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Screenshot Tool</string>
    <key>CFBundleDisplayName</key>
    <string>Screenshot Tool</string>
    <key>CFBundleIdentifier</key>
    <string>com.screenshottool.app</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>Screenshot Tool</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>Video File</string>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>public.movie</string>
                <string>public.video</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
'''

    (CONTENTS / "Info.plist").write_text(plist_content)

def create_icon():
    """Create a simple app icon."""
    print("Creating app icon...")

    # Create a simple icon using Python (requires Pillow)
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create icon at multiple sizes
        sizes = [16, 32, 64, 128, 256, 512, 1024]

        iconset_path = RESOURCES / "AppIcon.iconset"
        iconset_path.mkdir(exist_ok=True)

        for size in sizes:
            img = Image.new('RGBA', (size, size), (45, 45, 48, 255))
            draw = ImageDraw.Draw(img)

            # Draw a camera/frame icon shape
            margin = size // 8
            rect_bounds = [margin, margin, size - margin, size - margin]

            # Outer rectangle (frame)
            draw.rounded_rectangle(rect_bounds, radius=size//10,
                                   outline=(76, 175, 80, 255), width=max(1, size//20))

            # Inner play/capture symbol
            center = size // 2
            triangle_size = size // 4
            points = [
                (center - triangle_size//2, center - triangle_size//2),
                (center - triangle_size//2, center + triangle_size//2),
                (center + triangle_size//2, center)
            ]
            draw.polygon(points, fill=(76, 175, 80, 255))

            # Save different sizes
            img.save(iconset_path / f"icon_{size}x{size}.png")
            if size <= 512:
                img_2x = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
                img_2x.save(iconset_path / f"icon_{size}x{size}@2x.png")

        # Convert iconset to icns using iconutil
        icns_path = RESOURCES / "AppIcon.icns"
        subprocess.run(['iconutil', '-c', 'icns', str(iconset_path), '-o', str(icns_path)],
                      check=True, capture_output=True)

        # Clean up iconset
        shutil.rmtree(iconset_path)

        print("  Icon created successfully")

    except ImportError:
        print("  Pillow not available, skipping icon creation")
    except subprocess.CalledProcessError:
        print("  iconutil failed, skipping icon creation")
    except Exception as e:
        print(f"  Icon creation failed: {e}")

def build():
    """Build the app bundle."""
    print(f"\nBuilding {APP_NAME}.app...\n")

    create_app_structure()
    create_launcher()
    create_info_plist()
    create_icon()

    print(f"\n{'='*50}")
    print(f"App created successfully!")
    print(f"Location: {APP_BUNDLE}")
    print(f"\nYou can now:")
    print(f"  1. Double-click '{APP_NAME}.app' to run")
    print(f"  2. Drag it to /Applications folder")
    print(f"  3. Add it to your Dock")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    build()
