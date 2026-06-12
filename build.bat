@echo off
uv sync --group dev
uv run pyinstaller --onefile --windowed --name ArctisBattery main.py
echo.
echo Build complete. Executable is at dist\ArctisBattery.exe
pause
