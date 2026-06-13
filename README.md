# Arctis Battery Monitor

A minimal Windows system tray app that displays the battery level of **SteelSeries Arctis wireless headsets** — no SteelSeries GG required.

The tray icon shows the current charge percentage and changes color based on level (green → orange → red). A tooltip and right-click menu show the exact percentage and charging status. Battery is polled every 60 seconds by default (configurable via command line), with a manual Refresh option.

## Supported Devices

The app works with **all SteelSeries Arctis wireless headsets** that use a USB dongle, including:

- **Arctis 1 Wireless**
- **Arctis 7** (2019, Gen 2, 7+, 7P, 7X and variants)
- **Arctis 9 Wireless**
- **Arctis Pro Wireless**
- **Arctis Nova 3** (3P, 3X)
- **Arctis Nova 5** (5X)
- **Arctis Nova 7** (all variants and special editions)
- **Arctis Nova Pro** (Wireless, Pro X)

If your headset uses a SteelSeries USB dongle and reports battery over HID, it should work automatically.

## Requirements

- Windows 10/11
- SteelSeries Arctis USB dongle plugged in
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

You can customize the refresh interval (in seconds) with the `--refresh-interval` or `-r` flag:

```powershell
# Refresh every 30 seconds
uv run python main.py --refresh-interval 30

# Or using the short form
uv run python main.py -r 120
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
| USB Product ID | Varies by model (automatically detected) |
| HID command | Write `0xB0` → read response byte 3 (battery %) and byte 4 (charging flag) |

## Troubleshooting

If the tray icon shows "not connected" while the dongle is plugged in, run this snippet to inspect the HID interfaces your dongle exposes:

```python
import hid
for d in hid.enumerate(0x1038):
    print(d)
```

This will list all SteelSeries devices. The app automatically tests each device with the battery command. If you have multiple SteelSeries devices, you can identify your headset dongle from this list.
