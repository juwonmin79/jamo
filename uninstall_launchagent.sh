#!/usr/bin/env bash
set -euo pipefail

APP_PATH="/Applications/Jaso-Mon.app"
PLIST_ID="com.jaso.mon"
PLIST_PATH="${HOME}/Library/LaunchAgents/${PLIST_ID}.plist"

if [[ -f "$PLIST_PATH" ]]; then
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH"
    echo "Removed: $PLIST_PATH"
else
    echo "No LaunchAgent at $PLIST_PATH"
fi

if pgrep -x "Jaso-Mon" > /dev/null 2>&1; then
    echo "Quitting running Jaso-Mon..."
    osascript -e 'tell application "Jaso-Mon" to quit' 2>/dev/null || pkill -x "Jaso-Mon" 2>/dev/null || true
    sleep 1
fi

if [[ -d "$APP_PATH" ]]; then
    rm -rf "$APP_PATH"
    echo "Removed: $APP_PATH"
else
    echo "No app at $APP_PATH"
fi

echo "Uninstalled Jaso-Mon."
