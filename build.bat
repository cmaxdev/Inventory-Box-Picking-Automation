@echo off
echo Building Inventory Box Picking Automation Executable...
echo ============================================================

REM Build Desktop UI Executable
echo Building Desktop UI Executable...
pyinstaller --onefile --windowed --name=InventoryBoxPicker --hidden-import=pandas --hidden-import=openpyxl --hidden-import=tkinter --hidden-import=tkinter.ttk --hidden-import=tkinter.messagebox --hidden-import=tkinter.filedialog simple_desktop_ui.py

if %ERRORLEVEL% EQU 0 (
    echo Desktop UI executable built successfully!
) else (
    echo Error building desktop UI executable!
    pause
    exit /b 1
)

REM Build Command-Line Executable
echo.
echo Building Command-Line Executable...
pyinstaller --onefile --console --name=InventoryBoxPicker_CLI --hidden-import=pandas --hidden-import=openpyxl quick_order.py

if %ERRORLEVEL% EQU 0 (
    echo Command-line executable built successfully!
) else (
    echo Error building command-line executable!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build completed successfully!
echo.
echo Executable files created in 'dist' folder:
echo   - InventoryBoxPicker.exe (Desktop UI)
echo   - InventoryBoxPicker_CLI.exe (Command Line)
echo.
echo Usage:
echo   Desktop UI: Double-click InventoryBoxPicker.exe
echo   Command Line: InventoryBoxPicker_CLI.exe "Client Name" 100 "100%% Woman, 50%% DRESS, 50%% TROUSERS"
echo.
pause
