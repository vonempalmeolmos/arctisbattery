"""Arctis Nova 5 Wireless — system tray battery monitor."""

import threading
import time
import hid
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem

VENDOR_ID      = 0x1038   # SteelSeries
PRODUCT_ID     = 0x2232   # Arctis Nova 5 wireless dongle
POLL_INTERVAL  = 60        # seconds between polls
_SS_USAGE_PAGE = 0xFF43   # SteelSeries proprietary HID command interface


# ---------------------------------------------------------------------------
# HID communication
# ---------------------------------------------------------------------------

def _find_device_path():
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    if not devices:
        return None
    for d in devices:
        if d.get('usage_page') == _SS_USAGE_PAGE:
            return d['path']
    return devices[0]['path']


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
            dev.write([0x00, 0xB0] + [0x00] * 62)
            resp = dev.read(64, timeout_ms=3000)
            if not resp:
                return None, None
            # Response layout: [0xB0, battery_pct, charging_flag, ...]
            # hidapi may or may not prepend a report-ID byte; check both offsets.
            for offset in (0, 1):
                if len(resp) > offset + 2 and resp[offset] == 0xB0:
                    return min(resp[offset + 1], 100), bool(resp[offset + 2])
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
# Tray application
# ---------------------------------------------------------------------------

class ArctisTray:
    def __init__(self):
        self.battery  = None
        self.charging = False
        self._icon    = None
        self._stop    = threading.Event()
        self._refresh()

    # --- state ---

    def _refresh(self):
        batt, chg     = read_battery()
        self.battery  = batt
        self.charging = bool(chg)

    def _tooltip(self):
        if self.battery is None:
            return 'Arctis Nova 5: not connected'
        status = 'Charging' if self.charging else 'Discharging'
        return f'Arctis Nova 5 — {self.battery}%  ({status})'

    def _update(self):
        if self._icon:
            self._icon.icon  = _make_icon(self.battery, self.charging)
            self._icon.title = self._tooltip()
            self._icon.update_menu()

    # --- background poll ---

    def _poll(self):
        while not self._stop.wait(POLL_INTERVAL):
            self._refresh()
            self._update()

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
        threading.Thread(target=self._poll, daemon=True).start()
        self._icon.run()


if __name__ == '__main__':
    ArctisTray().run()
