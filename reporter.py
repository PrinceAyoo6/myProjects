# reporter.py

from datetime import datetime
import json
import os

LOG_DIR = "logs"


def generate_report(file_path, confidence=95.0):
    """
    Generates a structured JSON incident report in the logs/ directory.
    Returns (report_text, filename).
    """
    if os.path.exists(LOG_DIR) and not os.path.isdir(LOG_DIR):
        os.remove(LOG_DIR)

    os.makedirs(LOG_DIR, exist_ok=True)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]

    report_data = {
        "time": now_str,
        "affected_file": file_path,
        "confidence": f"{confidence:.1f}%",
        "recommended_actions": [
            "Disconnect system from the internet",
            "Backup unaffected files immediately",
            "Run a full antivirus scan",
            "Restore files from a clean backup",
            "Do NOT pay the ransom"
        ]
    }

    filename = os.path.join(LOG_DIR, f"incident_{timestamp_file}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4)

    report_text = (
        "🚨 RANSOMWARE INCIDENT REPORT 🚨\n"
        f"Time: {now_str}\n"
        f"Affected File: {file_path}\n"
        f"Confidence: {confidence:.1f}%\n"
        f"Log Saved To: {filename}"
    )

    return report_text, filename
