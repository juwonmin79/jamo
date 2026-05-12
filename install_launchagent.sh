#!/usr/bin/env bash
set -euo pipefail

APP_PATH="/Applications/Jaso-Mon.app"
APP_EXEC="${APP_PATH}/Contents/MacOS/Jaso-Mon"
PLIST_ID="com.jaso.mon"
PLIST_PATH="${HOME}/Library/LaunchAgents/${PLIST_ID}.plist"

if [[ ! -x "$APP_EXEC" ]]; then
    echo "Error: $APP_EXEC not found or not executable."
    echo "Build and install the app first:"
    echo "  python3 setup.py py2app && cp -r dist/Jaso-Mon.app /Applications/"
    exit 1
fi

mkdir -p "${HOME}/Library/LaunchAgents"

if launchctl list 2>/dev/null | grep -q "$PLIST_ID"; then
    echo "Existing LaunchAgent found, unloading..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTD/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_ID}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${APP_EXEC}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"

echo "Installed: $PLIST_PATH"
echo "Jaso-Mon will launch automatically on login."
