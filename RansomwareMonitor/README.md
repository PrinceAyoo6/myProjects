# 🛡️ Ransomware & USB Security Monitor

A real-time offline desktop security tool built with Python and Tkinter that monitors your system folders and USB drives for ransomware file signatures.

## Features

- 🔍 **Real-time file monitoring** — watches Desktop, Documents, and Downloads for suspicious file extensions
- 💾 **USB drive protection** — automatically scans any USB drive plugged in
- 🚨 **50+ ransomware signatures** — detects WannaCry, LockBit, REvil, STOP/DJVU, Dharma, Cerber, Ryuk and more
- 🧪 **Test mode** — simulate a ransomware threat to verify the monitor is working
- 🗑️ **Multi-select quarantine** — select and delete multiple threats at once from the inspector
- 📋 **Incident reports** — auto-generates JSON logs for every detected threat
- 🖥️ **Modern dark UI** — security-grade dashboard with real-time event console

## Tech Stack

- Python 3
- Tkinter (GUI)
- Threading (real-time monitoring)
- Winreg (resolves OneDrive-redirected Windows paths)

## How to Run

```bash
pip install pyinstaller   # only needed if building the .exe
python gui.py
```

## Project Structure

```
├── gui.py          # Main UI and application entry point
├── monitor.py      # File system watcher (startup scan + real-time loop)
├── detector.py     # Ransomware extension signature matching
├── usb_monitor.py  # USB drive detection and monitoring
├── alert.py        # Popup alert system
├── reporter.py     # JSON incident report generator
├── control.py      # Shared state (RUNNING flag, threat list, USB status)
└── logs/           # Auto-generated incident reports (gitignored)
```

---

> Built for educational and personal cybersecurity awareness purposes.
