"""SteelSeries Arctis Battery Monitor — system tray battery monitor for Arctis wireless headsets."""

import argparse
import threading
import hid
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem

VENDOR_ID      = 0x1038   # SteelSeries
DEFAULT_POLL_INTERVAL = 60  # Default seconds between polls
_SS_USAGE_PAGE = 0xFFC0   # SteelSeries proprietary HID command interface


# ---------------------------------------------------------------------------
# HID communication
# ---------------------------------------------------------------------------

def _find_device_path():
    """Find a SteelSeries Arctis headset by testing all SteelSeries devices with the battery command."""
    devices = hid.enumerate(VENDOR_ID)
    if not devices:
        return None
    
    # First pass: try devices with SteelSeries usage page
    for d in devices:
        if d.get('usage_page') != _SS_USAGE_PAGE:
            continue
        path = d.get('path')
        if not path:
            continue
        try:
            dev = hid.device()
            dev.open_path(path)
            dev.write(bytes([0x00, 0xB0] + [0x00] * 62))
            resp = dev.read(64, 3000)
            dev.close()
            if resp and len(resp) >= 5 and resp[0] == 0xB0:
                return path
        except Exception:
            pass
    
    # Second pass: try all SteelSeries devices (in case usage_page differs)
    for d in devices:
        path = d.get('path')
        if not path:
            continue
        try:
            dev = hid.device()
            dev.open_path(path)
            dev.write(bytes([0x00, 0xB0] + [0x00] * 62))
            resp = dev.read(64, 3000)
            dev.close()
            if resp and len(resp) >= 5 and resp[0] == 0xB0:
                return path
        except Exception:
            pass
    
    # Fallback: return first device path if we found any
    if devices:
        return devices[0].get('path')
    return None


def read_battery():
    """Return (battery_pct: int, charging: bool) or (None, None) when unavailable."""
    path = _find_device_path()
    if path is None:
        return None, None
    try:
        dev = hid.device()
        dev.open_path(path)
        try:
            # 64-byte output report: report-ID 0x00, command 0xB0, zero padding
            dev.write(bytes([0x00, 0xB0] + [0x00] * 62))
            resp = dev.read(64, 3000)
            if not resp:
                return None, None
            # Response layout: [0xB0, ?, ?, battery_pct, charging_status, ?, ...]
            # charging_status: 0x01 = charging, 0x03 = on battery
            if len(resp) >= 5 and resp[0] == 0xB0:
                return min(resp[3], 100), resp[4] != 0x03
        finally:
            dev.close()
    except Exception:
        pass
    return None, None


# ---------------------------------------------------------------------------
# Icon rendering
# ---------------------------------------------------------------------------

def _load_font(size):
    for path in ('C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _make_icon(battery, charging):
    W = H = 64
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)

    if battery is None:
        d.ellipse([2, 2, 62, 62], fill=(110, 110, 110, 210))
        font = _load_font(28)
        d.text((20, 16), '?', fill='white', font=font)
        return img

    if charging:
        fill = (30, 144, 255)      # blue
    elif battery > 50:
        fill = (50, 200, 60)       # green
    elif battery > 20:
        fill = (255, 165, 0)       # orange
    else:
        fill = (210, 35, 35)       # red

    d.ellipse([2, 2, 62, 62], fill=fill)

    label = str(battery)
    font  = _load_font(22 if battery < 100 else 18)
    bb    = d.textbbox((0, 0), label, font=font)
    x     = (W - (bb[2] - bb[0])) // 2 - bb[0]
    y     = (H - (bb[3] - bb[1])) // 2 - bb[1] - 2
    d.text((x, y), label, fill='white', font=font)
    return img


# ---------------------------------------------------------------------------
# Command line argument parsing
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description='SteelSeries Arctis Battery Monitor')
    parser.add_argument('--refresh-interval', '-r', type=int, default=DEFAULT_POLL_INTERVAL,
                        help=f'Seconds between battery level refreshes (default: {DEFAULT_POLL_INTERVAL})')
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Tray application
# ---------------------------------------------------------------------------

class ArctisTray:
    def __init__(self, poll_interval=DEFAULT_POLL_INTERVAL):
        self.battery  = None
        self.charging = False
        self._icon    = None
        self._stop    = threading.Event()
        self._poll_interval = poll_interval
        self._refresh()

    # --- state ---

    def _refresh(self):
        batt, chg     = read_battery()
        self.battery  = batt
        self.charging = bool(chg)

    def _tooltip(self):
        if self.battery is None:
            return 'Arctis: not connected'
        status = 'Charging' if self.charging else 'Discharging'
        return f'Arctis — {self.battery}%  ({status})'

    def _update(self):
        if self._icon:
            self._icon.icon  = _make_icon(self.battery, self.charging)
            self._icon.title = self._tooltip()
            self._icon.update_menu()

    # --- menu callbacks ---

    def _on_refresh(self, icon, item):
        self._refresh()
        self._update()

    def _on_exit(self, icon, item):
        self._stop.set()
        icon.stop()

    # --- dynamic menu text ---

    def _battery_text(self, _):
        if self.battery is None:
            return 'Headset not connected'
        return f'Battery: {self.battery}%'

    def _status_text(self, _):
        if self.battery is None:
            return 'Plug in the USB dongle'
        return 'Status: Charging ⚡' if self.charging else 'Status: Discharging'

    # --- run ---

    def run(self):
        menu = pystray.Menu(
            MenuItem(self._battery_text, None, enabled=False),
            MenuItem(self._status_text,  None, enabled=False),
            pystray.Menu.SEPARATOR,
            MenuItem('Refresh', self._on_refresh),
            MenuItem('Exit',    self._on_exit),
        )
        self._icon = pystray.Icon(
            'arctis_monitor',
            _make_icon(self.battery, self.charging),
            self._tooltip(),
            menu,
        )
        self._icon.run_detached()
        try:
            while not self._stop.wait(self._poll_interval):
                self._refresh()
                self._update()
        finally:
            self._icon.stop()


if __name__ == '__main__':
    args = parse_arguments()
    ArctisTray(poll_interval=args.refresh_interval).run()
