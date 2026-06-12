# Arctis Battery Monitor

A minimal Windows system tray app that displays the battery level of a **SteelSeries Arctis Nova 5 Wireless** headset — no SteelSeries GG required.

The tray icon shows the current charge percentage and changes color based on level (green → orange → red). A tooltip and right-click menu show the exact percentage and charging status. Battery is polled every 60 seconds, with a manual Refresh option.

## Requirements

- Windows 10/11
- SteelSeries Arctis Nova 5 USB dongle plugged in
- [uv](https://docs.astral.sh/uv/) (Python package manager)

Install uv if you don't have it:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Run from source

```powershell
uv sync
uv run python main.py
```

## Build a standalone .exe

```powershell
build.bat
```

The executable is placed at `dist\ArctisBattery.exe`. It has no runtime dependencies — copy it anywhere and run it.

## How it works

The app communicates with the headset dongle directly over USB HID without any SteelSeries software:

| Detail | Value |
|---|---|
| USB Vendor ID | `0x1038` (SteelSeries) |
| USB Product ID | `0x2232` (Nova 5 wireless dongle) |
| HID command | Write `0xB0` → read response byte 1 (battery %) and byte 2 (charging flag) |

## Troubleshooting

If the tray icon shows "not connected" while the dongle is plugged in, run this snippet to inspect the HID interfaces your dongle exposes:

```python
import hid
for d in hid.enumerate(0x1038, 0x2232):
    print(d)
```

Look at the `usage_page` values and update `_SS_USAGE_PAGE` in `main.py` if your firmware version uses a different interface.
