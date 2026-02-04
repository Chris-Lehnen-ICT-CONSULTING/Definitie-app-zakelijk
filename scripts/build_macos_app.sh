#!/usr/bin/env bash
set -euo pipefail

# Build macOS .app bundle for DefinitieAgent
# Usage: bash scripts/build_macos_app.sh

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="DefinitieAgent"
APP_PATH="$PROJECT_DIR/$APP_NAME.app"
LAUNCHER="$PROJECT_DIR/scripts/deployment/launcher.sh"

echo "Building $APP_NAME.app..."

# Ensure launcher is executable
chmod +x "$LAUNCHER"

# Remove old .app if exists
if [[ -d "$APP_PATH" ]]; then
    rm -rf "$APP_PATH"
fi

# Create AppleScript source
APPLESCRIPT=$(cat <<EOF
on run
    try
        do shell script "/bin/bash '$LAUNCHER'"
    on error errMsg number errNum
        if errNum is not -128 then
            display dialog "DefinitieAgent kon niet starten:" & return & return & errMsg buttons {"OK"} default button "OK" with icon stop with title "DefinitieAgent"
        end if
    end try
end run
EOF
)

# Compile to .app
echo "$APPLESCRIPT" | osacompile -o "$APP_PATH"

echo "Done: $APP_PATH"
echo ""
echo "Je kunt de app nu starten door te dubbelklikken op $APP_NAME.app"
echo "Of sleep hem naar je Dock voor snelle toegang."
echo ""
echo "Tip: Bij eerste keer openen kan macOS vragen om toestemming."
echo "     Ga naar Systeeminstellingen > Privacy & Beveiliging > toch openen."
