# alert.py

from tkinter import messagebox


def show_alert(file_path, confidence=95.0):
    """
    Displays a modal warning dialog alerting the user about detected ransomware.
    Should be called on the main GUI thread.
    """
    message = (
        f"🚨 RANSOMWARE ALERT DETECTED 🚨\n\n"
        f"Affected File:\n{file_path}\n\n"
        f"Confidence: {confidence:.1f}%\n\n"
        f"Recommended Actions:\n"
        f"• Disconnect system/network immediately\n"
        f"• Isolate affected files\n"
        f"• Run full antivirus scan\n"
        f"• Restore clean files from backup"
    )
    messagebox.showerror("Ransomware Alert", message)
