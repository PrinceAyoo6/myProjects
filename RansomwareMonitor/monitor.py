# monitor.py

import os
import time
import control
from detector import analyze_file
from reporter import generate_report

# Use the actual script's directory (not CWD) to correctly exclude app files
# regardless of how the script is launched (double-click, shell, etc.)
APP_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__))).lower()

# The test_monitor sandbox folder is INSIDE app dir but must be monitored
TEST_MONITOR_DIR = os.path.normpath(os.path.join(APP_DIR, "test_monitor")).lower()


def start_monitor(path, gui_callback, source_name="SYSTEM"):
    """
    Monitors a folder or drive for suspicious ransomware file extensions.
    Scans pre-existing files on startup and continuously watches for new/renamed files.
    """
    if not os.path.exists(path):
        return

    norm_monitored_path = os.path.normpath(path).lower()
    seen_files = set()

    gui_callback(f"[+] Started monitoring path: {path}")

    # ---------------- INITIAL STARTUP SCAN ---------------- #
    try:
        for root, dirs, files in os.walk(path):
            if not control.RUNNING:
                return

            # Exclude app directory (logs, code, cache) but ALLOW test_monitor sandbox
            norm_root = os.path.normpath(root).lower()
            if (norm_root == APP_DIR or norm_root.startswith(APP_DIR + os.sep)) \
                    and not (norm_root == TEST_MONITOR_DIR or norm_root.startswith(TEST_MONITOR_DIR + os.sep)):
                continue

            for file in files:
                full_path = os.path.join(root, file)
                norm_full = os.path.normpath(full_path).lower()
                seen_files.add(norm_full)

                is_suspicious, ext = analyze_file(full_path)
                if is_suspicious:
                    if source_name == "SYSTEM":
                        control.system_status["unsafe"] = True
                    elif source_name in control.usb_status:
                        control.usb_status[source_name]["unsafe"] = True

                    report_text, log_file = generate_report(full_path, confidence=95.0)

                    device_label = f"USB Drive ({source_name})" if source_name != "SYSTEM" else f"Local System ({os.path.basename(path)})"
                    threat_info = {
                        "file_path": full_path,
                        "source": device_label,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "ext": ext,
                        "log_file": log_file
                    }
                    if threat_info not in control.detected_threats:
                        control.detected_threats.append(threat_info)

                    alert_msg = f"[ALERT] Suspicious file detected ({ext}): {full_path}"
                    gui_callback(alert_msg, alert_file=full_path)
                    gui_callback(f"[REPORT] Details saved to: {log_file}")
    except Exception as e:
        gui_callback(f"[!] Startup scan error: {e}")

    # ---------------- CONTINUOUS REAL-TIME MONITOR ---------------- #
    while control.RUNNING:
        time.sleep(0.5)

        try:
            for root, dirs, files in os.walk(path):
                if not control.RUNNING:
                    break

                norm_root = os.path.normpath(root).lower()
                if (norm_root == APP_DIR or norm_root.startswith(APP_DIR + os.sep)) \
                        and not (norm_root == TEST_MONITOR_DIR or norm_root.startswith(TEST_MONITOR_DIR + os.sep)):
                    continue

                for file in files:
                    full_path = os.path.join(root, file)
                    norm_full = os.path.normpath(full_path).lower()

                    if norm_full in seen_files:
                        continue

                    seen_files.add(norm_full)

                    is_suspicious, ext = analyze_file(full_path)
                    if is_suspicious:
                        if source_name == "SYSTEM":
                            control.system_status["unsafe"] = True
                        elif source_name in control.usb_status:
                            control.usb_status[source_name]["unsafe"] = True

                        report_text, log_file = generate_report(full_path, confidence=95.0)

                        device_label = f"USB Drive ({source_name})" if source_name != "SYSTEM" else f"Local System ({os.path.basename(path)})"
                        threat_info = {
                            "file_path": full_path,
                            "source": device_label,
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "ext": ext,
                            "log_file": log_file
                        }
                        if threat_info not in control.detected_threats:
                            control.detected_threats.append(threat_info)

                        alert_msg = f"[ALERT] Suspicious file detected ({ext}): {full_path}"
                        gui_callback(alert_msg, alert_file=full_path)
                        gui_callback(f"[REPORT] Details saved to: {log_file}")

        except Exception as e:
            time.sleep(0.5)
