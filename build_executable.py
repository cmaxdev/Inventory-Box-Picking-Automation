#!/usr/bin/env python3
"""
Build script to create executable files for the Inventory Box Picking Automation system.
"""

import os
import subprocess
import sys
from pathlib import Path

def build_executable():
    """Build the executable files."""
    print("Building Inventory Box Picking Automation Executable...")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path.cwd()
    
    # Define the main script (desktop UI)
    main_script = "simple_desktop_ui.py"
    
    # Check if main script exists
    if not os.path.exists(main_script):
        print(f"ERROR: {main_script} not found!")
        return False
    
    # PyInstaller command for desktop UI (windowed application)
    desktop_cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # No console window for GUI
        "--name=InventoryBoxPicker",    # Name of the executable
        "--icon=NONE",                  # No icon for now
        "--add-data=sample.xlsx;.",     # Include sample inventory file
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        main_script
    ]
    
    # PyInstaller command for command-line version
    cli_cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--console",                    # Keep console window for CLI
        "--name=InventoryBoxPicker_CLI", # Name of the CLI executable
        "--icon=NONE",                  # No icon for now
        "--add-data=sample.xlsx;.",     # Include sample inventory file
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=tkinter",
        "quick_order.py"
    ]
    
    try:
        print("Building Desktop UI Executable...")
        result1 = subprocess.run(desktop_cmd, capture_output=True, text=True)
        
        if result1.returncode == 0:
            print("Desktop UI executable built successfully!")
        else:
            print("Error building desktop UI executable:")
            print(result1.stderr)
            return False
        
        print("\nBuilding Command-Line Executable...")
        result2 = subprocess.run(cli_cmd, capture_output=True, text=True)
        
        if result2.returncode == 0:
            print("Command-line executable built successfully!")
        else:
            print("Error building command-line executable:")
            print(result2.stderr)
            return False
        
        print("\nBuild completed successfully!")
        print("=" * 60)
        print("Executable files created in 'dist' folder:")
        print("   - InventoryBoxPicker.exe (Desktop UI)")
        print("   - InventoryBoxPicker_CLI.exe (Command Line)")
        print("\nUsage:")
        print("   Desktop UI: Double-click InventoryBoxPicker.exe")
        print("   Command Line: InventoryBoxPicker_CLI.exe \"Client Name\" 100 \"100% Woman, 50% DRESS, 50% TROUSERS\"")
        
        return True
        
    except Exception as e:
        print(f"Error during build: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    if success:
        print("\nBuild process completed successfully!")
    else:
        print("\nBuild process failed!")
        sys.exit(1)
