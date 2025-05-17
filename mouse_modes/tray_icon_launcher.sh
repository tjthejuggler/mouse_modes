#!/bin/bash

# Launcher script for the Mouse Modes tray icon application

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set the QT_QPA_PLATFORM environment variable to fix QSocketNotifier issue
export QT_QPA_PLATFORM=xcb

# Launch the tray icon application
"$SCRIPT_DIR/tray_icon/tray_icon.py" &

# Exit with success
exit 0