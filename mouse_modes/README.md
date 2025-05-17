# Mouse Mode Switching System

This system allows switching between different sets of mouse button configurations by pressing the volume up button when no volume button has been pressed in the last 5 seconds. When switching modes, the volume is not increased. The system also provides a system tray icon that changes color based on the active mode.

## Directory Structure

```
mouse_modes/
├── default/           # Default mode scripts
│   ├── upper_left.sh
│   ├── lower_left.sh
│   ├── upper_right.sh
│   └── lower_right.sh
├── alternate/         # Alternate mode scripts (placeholders)
│   ├── upper_left.sh
│   ├── lower_left.sh
│   ├── upper_right.sh
│   └── lower_right.sh
├── custom_mode/       # Custom mode scripts (example)
│   ├── upper_left.sh
│   ├── lower_left.sh
│   ├── upper_right.sh
│   └── lower_right.sh
├── tray_icon/         # System tray icon application
│   └── tray_icon.py   # Python script for the system tray icon
├── tray_icon_launcher.sh # Launcher script for the tray icon
└── mode_manager.sh    # Main script that manages modes
```

## Button Scripts

The following scripts should be mapped to your mouse buttons in KDE shortcuts:

- `button_upper_left.sh` - Upper left mouse button
- `button_lower_left.sh` - Lower left mouse button
- `button_upper_right.sh` - Upper right mouse button
- `button_lower_right.sh` - Lower right mouse button
- `button_volume_up.sh` - Volume up mouse button
- `button_volume_down.sh` - Volume down mouse button

## How It Works

1. When a mouse button is pressed, the corresponding button script calls the mode manager with the button name.
2. The mode manager checks the current mode and executes the appropriate script from the mode directory.
3. For volume buttons, the mode manager also tracks when they were last pressed.
4. If the volume up button is pressed and no volume button has been pressed in the last 5 seconds, the mode is switched to the next one.
5. A notification is displayed when the mode is switched.
6. The system tray icon changes color based on the active mode.

## System Tray Icon

The system tray icon provides the following features:

- Icon design consists of three circles (face and two ears) that all change color based on the active mode
- The face circle is slightly smaller and positioned lower, with the ears slightly disconnected for better visibility
- Left-clicking switches to the next mode (same as pressing the volume up button)
- Right-clicking opens a menu with options to:
  - Switch to a specific mode
  - Change the current mode's color directly with a color picker
  - Configure modes (add, edit, remove)
  - Update the mode_manager.sh script with current modes
  - Rename button files
  - Quit the application
- Hovering over the icon shows a tooltip with the current mode and button assignments

To start the system tray icon application:

```bash
./mouse_modes/tray_icon_launcher.sh
```

The tray icon application is also configured to start automatically when you log in, thanks to the desktop entry file in `~/.config/autostart/mouse_modes_tray.desktop`.

## Adding New Modes

You can add new modes in two ways:

### Using the System Tray Icon

1. Right-click on the system tray icon
2. Select "Configure..."
3. In the configuration dialog, click "Add Mode"
4. Enter a name and select a color for the new mode
5. Click "Add Mode"
6. The new mode will be created with default scripts
7. You can edit the scripts by selecting the mode and clicking "Edit Scripts"
8. After adding or modifying modes, click "Update mode_manager.sh with current modes" in the Settings tab

### Manually

1. Create a new directory under `mouse_modes/` with the mode name.
2. Add scripts for each button in the new directory.
3. Update the `MODES` array in `mode_manager.sh` to include the new mode.

## Current Button Mappings

### Default Mode
- Upper Left: Launches or focuses Obsidian
- Lower Left: Launches or focuses VS Code
- Upper Right: Launches or focuses Firefox
- Lower Right: Launches or focuses Konsole
- Volume Up: Increases volume by 10%
- Volume Down: Decreases volume by 10%

### Alternate Mode
- All buttons show a notification indicating which button was pressed in alternate mode
- Volume buttons still control volume but also show the alternate mode notification

### Custom Mode
- Example mode showing how to add additional modes
- All buttons show a notification indicating which button was pressed in custom mode
- You can replace these scripts with your own functionality