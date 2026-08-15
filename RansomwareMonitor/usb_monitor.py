# usb_monitor.py

import ctypes
import json
import os
import subprocess
import time
import threading
import control
from monitor import start_monitor

# CREATE_NO_WINDOW flag on Windows to prevent console popup flashes
CREATE_NO_WINDOW = 0x08000000


def get_physical_usb_devices():
    """
    Returns a dictionary of physical USB devices with their hardware names and assigned drive letters:
    e.g. {
        "Disk_1": {
            "name": "Generic External",
            "drives": ["D:\\", "E:\\"],
            "unsafe": False
        }
    }
    """
    devices = {}
    try:
        ps_cmd = 'Get-Disk | Where-Object BusType -eq USB | Select-Object Number, FriendlyName | ConvertTo-Json'
        out = subprocess.check_output(
            ['powershell', '-NoProfile', '-Command', ps_cmd],
            creationflags=CREATE_NO_WINDOW
        ).decode().strip()

        if out:
            disks = json.loads(out)
            if isinstance(disks, dict):
                disks = [disks]

            for d in disks:
                disk_num = d.get('Number')
                name = d.get('FriendlyName', 'External USB Drive')

                # Query partitions for this physical disk
                part_cmd = f'Get-Partition -DiskNumber {disk_num} | Select-Object DriveLetter | ConvertTo-Json'
                part_out = subprocess.check_output(
                    ['powershell', '-NoProfile', '-Command', part_cmd],
                    creationflags=CREATE_NO_WINDOW
                ).decode().strip()

                letters = []
                if part_out:
                    parts = json.loads(part_out)
                    if isinstance(parts, dict):
                        parts = [parts]
                    for p in parts:
                        letter = p.get('DriveLetter')
                        if letter and str(letter).strip():
                            letters.append(f"{letter.upper()}:\\")

                devices[f"Disk_{disk_num}"] = {
                    "name": name,
                    "drives": letters,
                    "unsafe": False
                }
    except Exception:
        pass

    # Fallback to drive letter scanning if PowerShell WMI is restricted
    if not devices:
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        fallback_drives = []
        for i in range(26):
            if bitmask & (1 << i):
                drive_letter = f"{chr(65 + i)}:\\"
                if drive_letter.upper().startswith("C:"):
                    continue
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive_letter))
                if drive_type in (2, 3, 4, 5):
                    fallback_drives.append(drive_letter)

        if fallback_drives:
            devices["External_Drives"] = {
                "name": "External USB Storage",
                "drives": fallback_drives,
                "unsafe": False
            }

    return devices


def detect_usb(gui_callback):
    monitored_drive_letters = set()
    known_device_keys = set()

    while control.RUNNING:
        time.sleep(1.5)
        if not control.RUNNING:
            break

        current_devices = get_physical_usb_devices()

        for dev_key, dev_info in current_devices.items():
            name = dev_info["name"]
            drives = dev_info["drives"]

            if dev_key not in known_device_keys:
                known_device_keys.add(dev_key)
                drives_str = ", ".join(drives) if drives else "No drive letter"
                gui_callback(f"[+] USB Hard Drive Detected: {name} ({drives_str})")

                control.usb_status[dev_key] = {
                    "name": name,
                    "drives": drives,
                    "unsafe": False
                }

            # Ensure background monitor thread runs for each drive letter of the USB device
            for drive in drives:
                if drive not in monitored_drive_letters:
                    monitored_drive_letters.add(drive)
                    threading.Thread(
                        target=start_monitor,
                        args=(drive, gui_callback, dev_key),
                        daemon=True
                    ).start()


def generate_usb_report():
    if not control.usb_status:
        return "USB : No external USB device detected"

    report = ["EXTERNAL USB HARD DRIVE REPORT:"]
    for dev_key, info in control.usb_status.items():
        status = "UNSAFE 🚨" if info["unsafe"] else "SAFE ✅"
        drives_str = ", ".join(info["drives"]) if info["drives"] else "N/A"
        report.append(f" - {info['name']} ({drives_str}) : {status}")

    return "\n".join(report)
