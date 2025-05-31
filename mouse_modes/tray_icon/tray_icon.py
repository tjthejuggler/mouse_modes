#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import fcntl
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QColorDialog, QTabWidget,
                             QWidget, QListWidget, QListWidgetItem, QComboBox, QMessageBox,
                             QFileDialog, QGridLayout, QGroupBox)
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal

# Singleton instance lock (prevents multiple tray icons)
LOCK_FILE = '/tmp/mouse_modes_tray.lock'
lock_fp = None
try:
    lock_fp = open(LOCK_FILE, 'w')
    fcntl.lockf(lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("Mouse Modes tray icon is already running. Exiting.")
    sys.exit(0)

# Configuration
CONFIG_DIR = os.path.expanduser("~/.config/mouse_modes")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
ICON_DIR = os.path.join(CONFIG_DIR, "icons")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODE_FILE = "/tmp/mouse_mode_current"

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(ICON_DIR, exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "modes": {
        "default": {
            "color": "#3498db",  # Blue
            "buttons": {
                "upper_left": os.path.join(PROJECT_DIR, "mouse_modes/default/upper_left.sh"),
                "lower_left": os.path.join(PROJECT_DIR, "mouse_modes/default/lower_left.sh"),
                "upper_right": os.path.join(PROJECT_DIR, "mouse_modes/default/upper_right.sh"),
                "lower_right": os.path.join(PROJECT_DIR, "mouse_modes/default/lower_right.sh")
            }
        },
        "alternate": {
            "color": "#e74c3c",  # Red
            "buttons": {
                "upper_left": os.path.join(PROJECT_DIR, "mouse_modes/alternate/upper_left.sh"),
                "lower_left": os.path.join(PROJECT_DIR, "mouse_modes/alternate/lower_left.sh"),
                "upper_right": os.path.join(PROJECT_DIR, "mouse_modes/alternate/upper_right.sh"),
                "lower_right": os.path.join(PROJECT_DIR, "mouse_modes/alternate/lower_right.sh")
            }
        },
        "custom_mode": {
            "color": "#2ecc71",  # Green
            "buttons": {
                "upper_left": os.path.join(PROJECT_DIR, "mouse_modes/custom_mode/upper_left.sh"),
                "lower_left": os.path.join(PROJECT_DIR, "mouse_modes/custom_mode/lower_left.sh"),
                "upper_right": os.path.join(PROJECT_DIR, "mouse_modes/custom_mode/upper_right.sh"),
                "lower_right": os.path.join(PROJECT_DIR, "mouse_modes/custom_mode/lower_right.sh")
            }
        }
    }
}
def load_config():
    """Load configuration from file or create default if it doesn't exist"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def get_current_mode_index():
    """Get current mode index from mode file"""
    try:
        if os.path.exists(MODE_FILE):
            with open(MODE_FILE, 'r') as f:
                return int(f.read().strip())
        return 0
    except Exception as e:
        print(f"Error reading mode file: {e}")
        return 0

def get_current_mode_name(config):
    """Get current mode name based on index"""
    index = get_current_mode_index()
    modes = list(config["modes"].keys())
    if 0 <= index < len(modes):
        return modes[index]
    return "default"

def switch_to_next_mode():
    """Switch to the next mode by calling the volume up script"""
    script_path = os.path.join(PROJECT_DIR, "button_volume_up.sh")
    subprocess.run([script_path])

def create_mouse_icon(color_hex):
    """Create a mouse icon with the specified color"""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Set the color for all circles
    color = QColor(color_hex)
    painter.setBrush(QBrush(color))
    painter.setPen(Qt.NoPen)
    
    # Draw the face (larger circle) - positioned lower in the icon and slightly smaller
    face_size = int(size * 0.63)  # Reduced from 0.65 to 0.63
    face_x = int((size - face_size) / 2)
    face_y = int((size - face_size) / 2) + int(size * 0.05)  # Moved down by 5% of icon size
    painter.drawEllipse(face_x, face_y, face_size, face_size)
    
    # Draw the ears (slightly smaller than before, but still bigger than original)
    ear_size = int(size * 0.32)  # Reduced from 0.35 to 0.32
    ear_offset = int(size * 0.05)  # Small offset to disconnect from face
    
    # Left ear - adjusted position to account for face position
    painter.drawEllipse(
        int(face_x - ear_size/2 - ear_offset),
        int(face_y - ear_size/2),
        ear_size,
        ear_size
    )
    
    # Right ear - adjusted position to account for face position
    painter.drawEllipse(
        int(face_x + face_size - ear_size/2 + ear_offset),
        int(face_y - ear_size/2),
        ear_size,
        ear_size
    )
    
    painter.end()
    
    # Save the icon for future use
    icon_path = os.path.join(ICON_DIR, f"mouse_icon_{color_hex.replace('#', '')}.png")
    pixmap.save(icon_path)
    
    return pixmap

class MouseIconPreview(QWidget):
    """Widget to preview the mouse icon with a selected color"""
    def __init__(self, color_hex="#3498db", parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setMinimumSize(100, 100)
        
    def set_color(self, color_hex):
        """Update the preview with a new color"""
        self.color_hex = color_hex
        self.update()
        
    def paintEvent(self, event):
        """Paint the mouse icon preview"""
        size = min(self.width(), self.height())
        pixmap = create_mouse_icon(self.color_hex)
        
        # Scale the pixmap to fit the widget
        scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Center the pixmap in the widget
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        
        # Draw the pixmap
        painter = QPainter(self)
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

class EnhancedColorDialog(QDialog):
    """Enhanced color dialog with mouse icon preview"""
    colorSelected = pyqtSignal(QColor)
    
    def __init__(self, initial_color="#3498db", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Mode Color")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Preview section
        preview_group = QGroupBox("Icon Preview")
        preview_layout = QVBoxLayout()
        self.preview = MouseIconPreview(initial_color)
        self.preview.setMinimumHeight(100)
        preview_layout.addWidget(self.preview)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Color selection section
        color_group = QGroupBox("Color Selection")
        color_layout = QVBoxLayout()
        
        # Basic colors
        basic_colors_layout = QGridLayout()
        basic_colors = [
            "#3498db",  # Blue
            "#e74c3c",  # Red
            "#2ecc71",  # Green
            "#f39c12",  # Orange
            "#9b59b6",  # Purple
            "#1abc9c",  # Turquoise
            "#34495e",  # Dark Blue
            "#f1c40f",  # Yellow
            "#e67e22",  # Dark Orange
            "#95a5a6",  # Gray
            "#16a085",  # Dark Turquoise
            "#d35400",  # Dark Orange
            "#c0392b",  # Dark Red
            "#8e44ad",  # Dark Purple
            "#27ae60",  # Dark Green
            "#7f8c8d"   # Dark Gray
        ]
        
        row, col = 0, 0
        for color_hex in basic_colors:
            color_button = QPushButton()
            color_button.setFixedSize(40, 40)
            color_button.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #888;")
            color_button.clicked.connect(lambda checked, c=color_hex: self.select_basic_color(c))
            basic_colors_layout.addWidget(color_button, row, col)
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
        
        color_layout.addLayout(basic_colors_layout)
        
        # Custom color button
        custom_color_layout = QHBoxLayout()
        custom_color_button = QPushButton("Choose Custom Color...")
        custom_color_button.clicked.connect(self.open_color_dialog)
        custom_color_layout.addWidget(custom_color_button)
        color_layout.addLayout(custom_color_layout)
        
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.selected_color = QColor(initial_color)
    
    def select_basic_color(self, color_hex):
        """Select a basic color"""
        color = QColor(color_hex)
        self.selected_color = color
        self.preview.set_color(color_hex)
    
    def open_color_dialog(self):
        """Open the standard color dialog for custom colors"""
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.preview.set_color(color.name())
    
    def get_selected_color(self):
        """Get the selected color"""
        return self.selected_color
class AddModeDialog(QDialog):
    """Dialog for adding a new mode"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Mode")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Mode name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Mode Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Color picker
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Mode Color:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(30, 30)
        self.color = "#3498db"  # Default color
        self.update_color_button()
        self.color_button.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        add_button = QPushButton("Add Mode")
        add_button.clicked.connect(self.accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(add_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_color_button(self):
        """Update the color button appearance"""
        self.color_button.setStyleSheet(f"background-color: {self.color};")
    
    def pick_color(self):
        """Open enhanced color picker dialog"""
        dialog = EnhancedColorDialog(self.color, self)
        if dialog.exec_():
            color = dialog.get_selected_color()
            if color.isValid():
                self.color = color.name()
                self.update_color_button()
    
    def get_mode_info(self):
        """Get the mode information entered by the user"""
        return {
            "name": self.name_edit.text(),
            "color": self.color
        }

class EditScriptsDialog(QDialog):
    """Dialog for editing button scripts"""
    def __init__(self, mode_name, config, parent=None):
        super().__init__(parent)
        self.mode_name = mode_name
        self.config = config
        self.setWindowTitle(f"Edit Scripts for {mode_name} Mode")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Create a grid layout for the buttons
        grid_layout = QGridLayout()
        
        # Upper Left Button
        grid_layout.addWidget(QLabel("Upper Left Button:"), 0, 0)
        self.upper_left_edit = QLineEdit(config["modes"][mode_name]["buttons"]["upper_left"])
        self.upper_left_browse = QPushButton("Browse")
        self.upper_left_browse.clicked.connect(lambda: self.browse_script("upper_left"))
        grid_layout.addWidget(self.upper_left_edit, 0, 1)
        grid_layout.addWidget(self.upper_left_browse, 0, 2)
        
        # Lower Left Button
        grid_layout.addWidget(QLabel("Lower Left Button:"), 1, 0)
        self.lower_left_edit = QLineEdit(config["modes"][mode_name]["buttons"]["lower_left"])
        self.lower_left_browse = QPushButton("Browse")
        self.lower_left_browse.clicked.connect(lambda: self.browse_script("lower_left"))
        grid_layout.addWidget(self.lower_left_edit, 1, 1)
        grid_layout.addWidget(self.lower_left_browse, 1, 2)
        
        # Upper Right Button
        grid_layout.addWidget(QLabel("Upper Right Button:"), 2, 0)
        self.upper_right_edit = QLineEdit(config["modes"][mode_name]["buttons"]["upper_right"])
        self.upper_right_browse = QPushButton("Browse")
        self.upper_right_browse.clicked.connect(lambda: self.browse_script("upper_right"))
        grid_layout.addWidget(self.upper_right_edit, 2, 1)
        grid_layout.addWidget(self.upper_right_browse, 2, 2)
        
        # Lower Right Button
        grid_layout.addWidget(QLabel("Lower Right Button:"), 3, 0)
        self.lower_right_edit = QLineEdit(config["modes"][mode_name]["buttons"]["lower_right"])
        self.lower_right_browse = QPushButton("Browse")
        self.lower_right_browse.clicked.connect(lambda: self.browse_script("lower_right"))
        grid_layout.addWidget(self.lower_right_edit, 3, 1)
        grid_layout.addWidget(self.lower_right_browse, 3, 2)
        
        layout.addLayout(grid_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_script(self, button_name):
        """Open file dialog to browse for a script"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select Script for {button_name}", 
            os.path.join(PROJECT_DIR, "mouse_modes"), 
            "Shell Scripts (*.sh);;All Files (*)"
        )
        if file_path:
            if button_name == "upper_left":
                self.upper_left_edit.setText(file_path)
            elif button_name == "lower_left":
                self.lower_left_edit.setText(file_path)
            elif button_name == "upper_right":
                self.upper_right_edit.setText(file_path)
            elif button_name == "lower_right":
                self.lower_right_edit.setText(file_path)
    
    def get_scripts(self):
        """Get the scripts entered by the user"""
        return {
            "upper_left": self.upper_left_edit.text(),
            "lower_left": self.lower_left_edit.text(),
            "upper_right": self.upper_right_edit.text(),
            "lower_right": self.lower_right_edit.text()
        }
class ConfigDialog(QDialog):
    """Main configuration dialog"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Mouse Modes Configuration")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Modes tab
        self.modes_tab = QWidget()
        self.setup_modes_tab()
        self.tabs.addTab(self.modes_tab, "Modes")
        
        # Settings tab
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "Settings")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def setup_modes_tab(self):
        """Setup the modes tab"""
        layout = QVBoxLayout()
        
        # Mode list
        self.mode_list = QListWidget()
        self.update_mode_list()
        layout.addWidget(self.mode_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Mode")
        add_button.clicked.connect(self.add_mode)
        button_layout.addWidget(add_button)
        
        edit_button = QPushButton("Edit Scripts")
        edit_button.clicked.connect(self.edit_scripts)
        button_layout.addWidget(edit_button)
        
        edit_color_button = QPushButton("Change Color")
        edit_color_button.clicked.connect(self.change_color)
        button_layout.addWidget(edit_color_button)
        
        remove_button = QPushButton("Remove Mode")
        remove_button.clicked.connect(self.remove_mode)
        button_layout.addWidget(remove_button)
        
        layout.addLayout(button_layout)
        
        self.modes_tab.setLayout(layout)
    
    def setup_settings_tab(self):
        """Setup the settings tab"""
        layout = QVBoxLayout()
        
        # Update mode_manager.sh
        update_group = QGroupBox("Mode Manager")
        update_layout = QVBoxLayout()
        
        update_button = QPushButton("Update mode_manager.sh with current modes")
        update_button.clicked.connect(self.update_mode_manager)
        update_layout.addWidget(update_button)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        # Rename button files
        rename_group = QGroupBox("Rename Button Files")
        rename_layout = QVBoxLayout()
        
        rename_button = QPushButton("Rename 'lower_middle' to 'lower_right' in all files")
        rename_button.clicked.connect(self.rename_button_files)
        rename_layout.addWidget(rename_button)
        
        rename_group.setLayout(rename_layout)
        layout.addWidget(rename_group)
        
        layout.addStretch()
        
        self.settings_tab.setLayout(layout)
    
    def update_mode_list(self):
        """Update the mode list widget"""
        self.mode_list.clear()
        for mode_name, mode_data in self.config["modes"].items():
            color = mode_data.get("color", "#3498db")
            
            # Create a widget for the list item
            item_widget = QWidget()
            item_layout = QHBoxLayout()
            item_layout.setContentsMargins(4, 2, 4, 2)
            
            # Mode name label
            name_label = QLabel(mode_name)
            item_layout.addWidget(name_label)
            
            # Spacer
            item_layout.addStretch()
            
            # Color square
            color_square = QLabel()
            color_square.setFixedSize(20, 20)
            color_square.setStyleSheet(f"background-color: {color}; border: 1px solid #888;")
            item_layout.addWidget(color_square)
            
            item_widget.setLayout(item_layout)
            
            # Create list item and set the widget
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            
            # Add to list
            self.mode_list.addItem(list_item)
            self.mode_list.setItemWidget(list_item, item_widget)
    
    def add_mode(self):
        """Add a new mode"""
        dialog = AddModeDialog(self)
        if dialog.exec_():
            mode_info = dialog.get_mode_info()
            mode_name = mode_info["name"]
            
            if not mode_name:
                QMessageBox.warning(self, "Error", "Mode name cannot be empty")
                return
            
            if mode_name in self.config["modes"]:
                QMessageBox.warning(self, "Error", f"Mode '{mode_name}' already exists")
                return
            
            # Create mode directory
            mode_dir = os.path.join(PROJECT_DIR, "mouse_modes", mode_name)
            os.makedirs(mode_dir, exist_ok=True)
            
            # Create button scripts
            buttons = ["upper_left", "lower_left", "upper_right", "lower_right"]
            for button in buttons:
                script_path = os.path.join(mode_dir, f"{button}.sh")
                if not os.path.exists(script_path):
                    with open(script_path, 'w') as f:
                        f.write(f"""#!/bin/bash

# {mode_name} mode script for {button} mouse button
# This script shows a notification

notify-send "Mouse Button" "{button.replace('_', ' ').title()} Button Pressed in {mode_name} mode" -t 2000
""")
                    os.chmod(script_path, 0o755)  # Make executable
            
            # Add to config
            self.config["modes"][mode_name] = {
                "color": mode_info["color"],
                "buttons": {
                    "upper_left": os.path.join(mode_dir, "upper_left.sh"),
                    "lower_left": os.path.join(mode_dir, "lower_left.sh"),
                    "upper_right": os.path.join(mode_dir, "upper_right.sh"),
                    "lower_right": os.path.join(mode_dir, "lower_right.sh")
                }
            }
            
            save_config(self.config)
            self.update_mode_list()
    
    def edit_scripts(self):
        """Edit scripts for the selected mode"""
        selected_items = self.mode_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a mode")
            return
        
        # Get the selected item's widget
        selected_item = selected_items[0]
        item_widget = self.mode_list.itemWidget(selected_item)
        
        # Get the mode name from the first label in the widget
        mode_name = item_widget.layout().itemAt(0).widget().text()
        
        dialog = EditScriptsDialog(mode_name, self.config, self)
        if dialog.exec_():
            scripts = dialog.get_scripts()
            self.config["modes"][mode_name]["buttons"] = scripts
            save_config(self.config)
    
    def change_color(self):
        """Change color for the selected mode"""
        selected_items = self.mode_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a mode")
            return
        
        mode_name = selected_items[0].text().split(" (")[0]
        current_color = self.config["modes"][mode_name].get("color", "#3498db")
        
        dialog = EnhancedColorDialog(current_color, self)
        if dialog.exec_():
            color = dialog.get_selected_color()
            if color.isValid():
                self.config["modes"][mode_name]["color"] = color.name()
                save_config(self.config)
                self.update_mode_list()
    
    def remove_mode(self):
        """Remove the selected mode"""
        selected_items = self.mode_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a mode")
            return
        
        # Get the selected item's widget
        selected_item = selected_items[0]
        item_widget = self.mode_list.itemWidget(selected_item)
        
        # Get the mode name from the first label in the widget
        mode_name = item_widget.layout().itemAt(0).widget().text()
        
        # Don't allow removing default mode
        if mode_name == "default":
            QMessageBox.warning(self, "Error", "Cannot remove the default mode")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Removal", 
            f"Are you sure you want to remove the mode '{mode_name}'?\nThis will not delete the mode directory or scripts.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.config["modes"][mode_name]
            save_config(self.config)
            self.update_mode_list()
    
    def update_mode_manager(self):
        """Update the mode_manager.sh script with current modes"""
        mode_names = list(self.config["modes"].keys())
        
        try:
            # Read the current mode_manager.sh
            mode_manager_path = os.path.join(PROJECT_DIR, "mouse_modes", "mode_manager.sh")
            with open(mode_manager_path, 'r') as f:
                content = f.readlines()
            
            # Find the MODES line and replace it
            for i, line in enumerate(content):
                if line.strip().startswith("MODES=("):
                    modes_str = '"' + '" "'.join(mode_names) + '"'
                    content[i] = f"MODES=({modes_str})\n"
                    break
            
            # Write the updated content
            with open(mode_manager_path, 'w') as f:
                f.writelines(content)
            
            QMessageBox.information(self, "Success", "mode_manager.sh has been updated with current modes")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update mode_manager.sh: {e}")
    
    def rename_button_files(self):
        """Rename 'lower_middle' to 'lower_right' in all files"""
        try:
            # Rename button script
            old_button_script = os.path.join(PROJECT_DIR, "button_lower_middle.sh")
            new_button_script = os.path.join(PROJECT_DIR, "button_lower_right.sh")
            
            if os.path.exists(old_button_script):
                # Read the content
                with open(old_button_script, 'r') as f:
                    content = f.read()
                
                # Replace occurrences of "lower_middle" with "lower_right"
                content = content.replace("lower_middle", "lower_right")
                content = content.replace("Lower Middle", "Lower Right")
                
                # Write to the new file
                with open(new_button_script, 'w') as f:
                    f.write(content)
                
                # Make the new file executable
                os.chmod(new_button_script, 0o755)
                
                # Remove the old file
                os.remove(old_button_script)
            
            # Rename mode script files
            for mode_name in self.config["modes"]:
                mode_dir = os.path.join(PROJECT_DIR, "mouse_modes", mode_name)
                old_script = os.path.join(mode_dir, "lower_middle.sh")
                new_script = os.path.join(mode_dir, "lower_right.sh")
                
                if os.path.exists(old_script):
                    # Read the content
                    with open(old_script, 'r') as f:
                        content = f.read()
                    
                    # Replace occurrences of "lower_middle" with "lower_right"
                    content = content.replace("lower_middle", "lower_right")
                    content = content.replace("Lower Middle", "Lower Right")
                    
                    # Write to the new file
                    with open(new_script, 'w') as f:
                        f.write(content)
                    
                    # Make the new file executable
                    os.chmod(new_script, 0o755)
                    
                    # Remove the old file
                    os.remove(old_script)
            
            # Update README.md
            readme_path = os.path.join(PROJECT_DIR, "mouse_modes", "README.md")
            if os.path.exists(readme_path):
                with open(readme_path, 'r') as f:
                    content = f.read()
                
                content = content.replace("lower_middle.sh", "lower_right.sh")
                content = content.replace("Lower Middle", "Lower Right")
                content = content.replace("lower_middle", "lower_right")
                
                with open(readme_path, 'w') as f:
                    f.write(content)
            
            # Update config
            for mode_name, mode_data in self.config["modes"].items():
                if "buttons" in mode_data and "lower_middle" in mode_data["buttons"]:
                    mode_data["buttons"]["lower_right"] = mode_data["buttons"].pop("lower_middle")
            
            save_config(self.config)
            
            QMessageBox.information(self, "Success", "Successfully renamed 'lower_middle' to 'lower_right' in all files")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename button files: {e}")
class MouseModesTray:
    """System tray application for Mouse Modes"""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Load configuration
        self.config = load_config()
        
        # Create the tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setToolTip("Mouse Modes")
        
        # Create the menu
        self.menu = QMenu()
        
        # Add mode switching actions
        self.mode_actions = {}
        for mode_name in self.config["modes"]:
            action = QAction(f"Switch to {mode_name} mode", self.menu)
            action.triggered.connect(lambda checked, m=mode_name: self.switch_to_mode(m))
            self.menu.addAction(action)
            self.mode_actions[mode_name] = action
        
        self.menu.addSeparator()
        
        # Change color action for current mode
        change_color_action = QAction("Change Current Mode Color...", self.menu)
        change_color_action.triggered.connect(self.change_current_mode_color)
        self.menu.addAction(change_color_action)
        
        # Configure action
        configure_action = QAction("Configure...", self.menu)
        configure_action.triggered.connect(self.open_config_dialog)
        self.menu.addAction(configure_action)
        
        # Quit action
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.app.quit)
        self.menu.addAction(quit_action)
        
        # Set the menu
        self.tray_icon.setContextMenu(self.menu)
        
        # Update the icon based on current mode
        self.update_icon()
        
        # Set up a timer to periodically check the current mode
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_icon)
        self.timer.start(1000)  # Check every second
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Connect the activated signal
        self.tray_icon.activated.connect(self.tray_activated)
    
    def update_icon(self):
        """Update the tray icon based on the current mode"""
        current_mode = get_current_mode_name(self.config)
        color = self.config["modes"][current_mode].get("color", "#3498db")
        
        # Create the icon
        pixmap = create_mouse_icon(color)
        icon = QIcon(pixmap)
        
        # Set the icon
        self.tray_icon.setIcon(icon)
        
        # Update tooltip
        tooltip = f"Mouse Modes - Current: {current_mode}\n\n"
        tooltip += "Button Assignments:\n"
        
        for button, script in self.config["modes"][current_mode]["buttons"].items():
            script_name = os.path.basename(script)
            tooltip += f"{button.replace('_', ' ').title()}: {script_name}\n"
        
        self.tray_icon.setToolTip(tooltip)
        
        # Update menu
        for mode_name, action in self.mode_actions.items():
            action.setChecked(mode_name == current_mode)
    
    def tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:  # Left click
            switch_to_next_mode()
    
    def switch_to_mode(self, mode_name):
        """Switch to the specified mode"""
        # Get the index of the mode
        modes = list(self.config["modes"].keys())
        if mode_name in modes:
            index = modes.index(mode_name)
            
            # Write the index to the mode file
            try:
                with open(MODE_FILE, 'w') as f:
                    f.write(str(index))
                
                # Show notification
                subprocess.run(["notify-send", "Mouse Mode Switched", f"Now using: {mode_name} mode", "-t", "2000"])
                
                # Update the icon
                self.update_icon()
            except Exception as e:
                print(f"Error switching mode: {e}")
    
    def change_current_mode_color(self):
        """Open a color dialog to change the current mode's color"""
        current_mode = get_current_mode_name(self.config)
        current_color = self.config["modes"][current_mode].get("color", "#3498db")
        
        dialog = EnhancedColorDialog(current_color, None)
        if dialog.exec_():
            color = dialog.get_selected_color()
            if color.isValid():
                # Update the color in the configuration
                self.config["modes"][current_mode]["color"] = color.name()
                save_config(self.config)
                
                # Show notification
                subprocess.run(["notify-send", "Mode Color Changed",
                               f"Color for {current_mode} mode updated to {color.name()}",
                               "-t", "2000"])
                
                # Update the icon
                self.update_icon()
    
    def open_config_dialog(self):
        """Open the configuration dialog"""
        dialog = ConfigDialog(self.config, None)
        if dialog.exec_():
            # Reload configuration
            self.config = load_config()
            
            # Recreate mode actions
            self.menu.clear()
            self.mode_actions = {}
            
            for mode_name in self.config["modes"]:
                action = QAction(f"Switch to {mode_name} mode", self.menu)
                action.triggered.connect(lambda checked, m=mode_name: self.switch_to_mode(m))
                self.menu.addAction(action)
                self.mode_actions[mode_name] = action
            
            self.menu.addSeparator()
            
            # Change color action for current mode
            change_color_action = QAction("Change Current Mode Color...", self.menu)
            change_color_action.triggered.connect(self.change_current_mode_color)
            self.menu.addAction(change_color_action)
            
            # Configure action
            configure_action = QAction("Configure...", self.menu)
            configure_action.triggered.connect(self.open_config_dialog)
            self.menu.addAction(configure_action)
            
            # Quit action
            quit_action = QAction("Quit", self.menu)
            quit_action.triggered.connect(self.app.quit)
            self.menu.addAction(quit_action)
            
            # Update the icon
            self.update_icon()
    
    def run(self):
        """Run the application"""
        return self.app.exec_()

if __name__ == "__main__":
    # Fix for QSocketNotifier issue
    import os
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    
    tray = MouseModesTray()
    sys.exit(tray.run())