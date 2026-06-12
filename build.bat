@echo off
uv sync --group dev
uv run pyinstaller ArctisBattery.spec --noconfirm
echo.
echo Build complete. Executable is at dist\ArctisBattery.exe
echo.
echo SHA-256 (publish this so users can verify the download):
powershell -NoProfile -Command "(Get-FileHash dist\ArctisBattery.exe -Algorithm SHA256).Hash"
pause
