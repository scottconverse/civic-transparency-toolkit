#!/bin/bash
# ============================================================
# Build script for Civic Transparency Toolkit (macOS / Linux)
# Creates a standalone executable using PyInstaller
#
#  >>> CHANGE THIS VERSION NUMBER FOR EACH BUILD <<<
# ============================================================
VERSION="v1.0"
# ============================================================

echo ""
echo "  Civic Transparency Toolkit — Build $VERSION"
echo "  ============================================"
echo ""

# --- Find Python ---
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found!"
    echo ""
    echo "  Install Python 3.9+ from python.org or your package manager:"
    echo "    macOS:  brew install python3"
    echo "    Ubuntu: sudo apt install python3 python3-pip"
    echo ""
    exit 1
fi

echo "Found Python: $PYTHON"
"$PYTHON" --version
echo ""

# --- Check for duplicate version ---
if [ -d "dist/CivicTransparencyToolkit-$VERSION" ]; then
    echo ""
    echo "  WARNING: dist/CivicTransparencyToolkit-$VERSION already exists!"
    echo "  If you continue, it will be REPLACED."
    echo ""
    read -p "  Type Y to overwrite, or anything else to cancel: " CONFIRM
    if [ "$CONFIRM" != "Y" ] && [ "$CONFIRM" != "y" ]; then
        echo "Build cancelled. Change the VERSION at the top of build.sh and try again."
        exit 0
    fi
    rm -rf "dist/CivicTransparencyToolkit-$VERSION"
fi

echo "Step 1 of 6: Installing dependencies..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r requirements.txt
"$PYTHON" -m pip install pyinstaller
echo ""

echo "Step 2 of 6: Clearing cached bytecode..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
rm -rf build
echo "  Cleared all Python and PyInstaller caches."
echo ""

# --- Determine platform-specific separator and icon ---
SEPARATOR=":"
ICON_FLAG=""
if [ -f "assets/icon.icns" ]; then
    ICON_FLAG="--icon assets/icon.icns"
elif [ -f "assets/icon.png" ]; then
    ICON_FLAG="--icon assets/icon.png"
fi

echo "Step 3 of 6: Building executable..."
"$PYTHON" -m PyInstaller \
    --name "CivicTransparencyToolkit" \
    --onedir \
    --windowed \
    $ICON_FLAG \
    --add-data "prompts${SEPARATOR}prompts" \
    --add-data "templates${SEPARATOR}templates" \
    --hidden-import "yt_dlp" \
    --hidden-import "youtube_transcript_api" \
    --hidden-import "docx" \
    --hidden-import "docx.shared" \
    --hidden-import "docx.enum" \
    --hidden-import "docx.enum.text" \
    --hidden-import "docx.oxml" \
    --hidden-import "docx.oxml.ns" \
    --noconfirm \
    --clean \
    main.py
echo ""

# --- Check if build succeeded ---
APP_DIR="dist/CivicTransparencyToolkit"
if [ -d "$APP_DIR" ] || [ -f "$APP_DIR/CivicTransparencyToolkit" ]; then

    echo "Step 4 of 6: Copying extras and source code..."
    cp "README.txt" "$APP_DIR/" 2>/dev/null
    cp "LICENSE" "$APP_DIR/" 2>/dev/null
    cp "Real World Example Sources List.csv" "$APP_DIR/" 2>/dev/null
    if [ -f "Civic Transparency Toolkit - User Guide.docx" ]; then
        cp "Civic Transparency Toolkit - User Guide.docx" "$APP_DIR/"
        echo "  Bundled user guide."
    fi

    # Bundle full source code so recipients can read, modify, and rebuild
    rm -rf "$APP_DIR/source"
    mkdir -p "$APP_DIR/source"
    cp *.py "$APP_DIR/source/" 2>/dev/null
    cp *.sh "$APP_DIR/source/" 2>/dev/null
    cp *.bat "$APP_DIR/source/" 2>/dev/null
    cp *.spec "$APP_DIR/source/" 2>/dev/null
    cp *.txt "$APP_DIR/source/" 2>/dev/null
    cp *.csv "$APP_DIR/source/" 2>/dev/null
    cp LICENSE "$APP_DIR/source/" 2>/dev/null
    cp -r prompts "$APP_DIR/source/" 2>/dev/null
    cp -r templates "$APP_DIR/source/" 2>/dev/null
    cp -r assets "$APP_DIR/source/" 2>/dev/null
    echo ""

    echo "Step 5 of 6: Renaming to versioned folder..."
    rm -rf "dist/CivicTransparencyToolkit-$VERSION"
    mv "$APP_DIR" "dist/CivicTransparencyToolkit-$VERSION"
    echo "  Created: dist/CivicTransparencyToolkit-$VERSION/"
    echo ""

    echo "Step 6 of 6: Creating zip for distribution..."
    ZIP_PATH="dist/CivicTransparencyToolkit-$VERSION.zip"
    rm -f "$ZIP_PATH"
    cd dist && zip -r "CivicTransparencyToolkit-$VERSION.zip" "CivicTransparencyToolkit-$VERSION" > /dev/null && cd ..
    if [ -f "$ZIP_PATH" ]; then
        echo "  Created: $ZIP_PATH"
    else
        echo "  WARNING: Zip creation failed. You can zip the folder manually."
    fi
    echo ""
    echo "============================================================"
    echo " BUILD SUCCESSFUL — $VERSION"
    echo "============================================================"
    echo ""
    echo "  Folder:  dist/CivicTransparencyToolkit-$VERSION/"
    echo "  Zip:     dist/CivicTransparencyToolkit-$VERSION.zip"
    echo ""
    echo "  Previous builds in dist/ are preserved."
    echo "  To distribute: share the .zip or copy the folder."
    echo ""
    echo "  All versions in dist/:"
    for d in dist/CivicTransparencyToolkit-v*/; do
        [ -d "$d" ] && echo "    $(basename "$d")"
    done
    echo ""
else
    echo "============================================================"
    echo " BUILD FAILED"
    echo "============================================================"
    echo ""
    echo "Check the error messages above. Common fixes:"
    echo "  - Make sure Python 3.9+ is installed"
    echo "  - Try running: $PYTHON -m pip install pyinstaller"
    echo "  - Then:        $PYTHON -m PyInstaller --onedir --windowed main.py"
fi
