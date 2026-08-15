# control.py

RUNNING = False

system_status = {
    "unsafe": False
}

# Dict: drive -> {name, unsafe}
usb_status = {}

# List of threat dicts: [{"file_path": ..., "source": ..., "time": ..., "ext": ...}]
detected_threats = []
