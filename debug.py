"""Run with: uv run python debug.py"""
import hid

VENDOR_ID = 0x1038

devices = hid.enumerate(VENDOR_ID)
if not devices:
    print("No SteelSeries Arctis headset found. Plug in the USB dongle and try again.")
else:
    print(f"Found {len(devices)} HID interface(s):\n")
    for i, d in enumerate(devices):
        print(f"  [{i}] usage_page=0x{d.get('usage_page', 0):04X}  "
              f"usage=0x{d.get('usage', 0):04X}  "
              f"interface={d.get('interface_number', '?')}  "
              f"path={d.get('path')}")

    print()
    for i, d in enumerate(devices):
        print(f"--- Interface {i} "
              f"(usage_page=0x{d.get('usage_page', 0):04X}) ---")
        try:
            dev = hid.device()
            dev.open_path(d['path'])
            dev.write(bytes([0x00, 0xB0] + [0x00] * 62))
            resp = dev.read(64, 3000)
            dev.close()
            if resp:
                print(f"  bytes : {list(resp)}")
                print(f"  hex   : {[hex(b) for b in resp]}")
            else:
                print("  (no response)")
        except Exception as e:
            print(f"  error : {e}")
        print()
