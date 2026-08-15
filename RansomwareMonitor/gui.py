# gui.py

import os
import queue
import subprocess
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import winreg

from alert import show_alert
import control
from monitor import start_monitor
from usb_monitor import detect_usb, generate_usb_report

# ---------------- PATHS & CONSTANTS ---------------- #

TEST_FOLDER = os.path.join(os.getcwd(), "test_monitor")


def get_system_paths():
    """
    Resolves the user's actual Windows Desktop, Documents, and Downloads folder paths.
    Automatically handles OneDrive redirection (e.g. C:\\Users\\user\\OneDrive\\Desktop).
    """
    home = os.path.expanduser("~")
    resolved_paths = set()

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        shell_keys = ["Desktop", "Personal", "{374DE290-123F-4565-9164-39C4925E467B}"]
        for k in shell_keys:
            try:
                val, _ = winreg.QueryValueEx(key, k)
                expanded = os.path.expandvars(val)
                if os.path.exists(expanded):
                    resolved_paths.add(expanded)
            except Exception:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass

    candidates = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "OneDrive", "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "OneDrive", "Documents"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "OneDrive", "Downloads"),
        TEST_FOLDER,
    ]
    for c in candidates:
        if os.path.exists(c):
            resolved_paths.add(c)

    return list(resolved_paths)


SYSTEM_PATHS = get_system_paths()

# Color Palette (Catppuccin / Modern Dark Security Aesthetic)
COLOR_BG = "#0f172a"          # Slate 900
COLOR_CARD = "#1e293b"        # Slate 800
COLOR_CARD_HOVER = "#334155"  # Slate 700
COLOR_CARD_BORDER = "#475569" # Slate 600
COLOR_TEXT_MAIN = "#f8fafc"   # Slate 50
COLOR_TEXT_MUTED = "#94a3b8"  # Slate 400
COLOR_ACCENT_GREEN = "#10b981"# Emerald 500
COLOR_ACCENT_RED = "#ef4444"  # Rose 500
COLOR_ACCENT_BLUE = "#3b82f6" # Sapphire 500
COLOR_ACCENT_AMBER = "#f59e0b"# Amber 500
COLOR_CONSOLE_BG = "#0b0f19"   # Dark Obsidian


# ---------------- HOVER BUTTON HELPER ---------------- #

def create_hover_button(parent, text, bg_color, hover_color, fg_color="#ffffff", command=None, width=16):
    btn = tk.Button(
        parent,
        text=text,
        bg=bg_color,
        fg=fg_color,
        activebackground=hover_color,
        activeforeground=fg_color,
        font=("Segoe UI", 10, "bold"),
        width=width,
        height=1,
        relief=tk.FLAT,
        bd=0,
        cursor="hand2",
        command=command
    )

    def on_enter(e):
        if btn["state"] != tk.DISABLED:
            btn["bg"] = hover_color

    def on_leave(e):
        if btn["state"] != tk.DISABLED:
            btn["bg"] = bg_color

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn


# ---------------- MAIN APPLICATION CLASS ---------------- #

class RansomwareMonitorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Offline Ransomware & USB Protection Monitor")
        self.root.geometry("880x640")
        self.root.minsize(820, 600)
        self.root.config(bg=COLOR_BG)

        self.log_queue = queue.Queue()
        self.threat_count = 0

        self._configure_ttk_styles()
        self._build_ui()
        self.root.after(100, self.process_log_queue)

    def _configure_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#0b0f19",
            foreground="#e2e8f0",
            fieldbackground="#0b0f19",
            rowheight=30,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading",
            background="#1e293b",
            foreground="#f8fafc",
            relief="flat",
            font=("Segoe UI", 9, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", "#3b82f6")],
            foreground=[("selected", "#ffffff")]
        )

    def _build_ui(self):
        # Top Header Frame
        header_frame = tk.Frame(self.root, bg=COLOR_BG, pady=12, padx=20)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame,
            text="🛡️ RANSOMWARE & USB SECURITY MONITOR",
            font=("Segoe UI", 15, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MAIN
        )
        title_label.pack(side=tk.LEFT)

        # Status Badge Pill
        self.badge_label = tk.Label(
            header_frame,
            text="● SYSTEM IDLE",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="#cbd5e1",
            padx=12,
            pady=4
        )
        self.badge_label.pack(side=tk.RIGHT)

        # ---------------- METRIC CARDS ---------------- #
        cards_frame = tk.Frame(self.root, bg=COLOR_BG, padx=20)
        cards_frame.pack(fill=tk.X, pady=5)

        num_paths = len(SYSTEM_PATHS)
        # Card 1: System Protection
        self.card_sys, self.val_sys = self._create_card(
            cards_frame,
            title="SYSTEM HEALTH 🔍",
            default_val="SAFE ✅",
            subtext=f"{num_paths} Folders Active",
            val_color=COLOR_ACCENT_GREEN,
            click_command=self.open_threat_inspector
        )
        self.card_sys.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Card 2: USB Monitor
        self.card_usb, self.val_usb = self._create_card(
            cards_frame,
            title="USB DRIVES 💾",
            default_val="0 Connected",
            subtext="Click to inspect drives",
            val_color=COLOR_ACCENT_BLUE,
            click_command=self.open_threat_inspector
        )
        self.card_usb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        # Card 3: Threat Counter (CLICKABLE)
        self.card_threat, self.val_threat = self._create_card(
            cards_frame,
            title="THREAT COUNTER 🚨",
            default_val="0 Threats",
            subtext="Click to inspect threats",
            val_color=COLOR_ACCENT_GREEN,
            click_command=self.open_threat_inspector
        )
        self.card_threat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # ---------------- ACTION TOOLBAR ---------------- #
        toolbar_frame = tk.Frame(self.root, bg=COLOR_CARD, padx=15, pady=10, bd=1, relief=tk.SOLID)
        toolbar_frame.pack(fill=tk.X, padx=20, pady=12)

        self.btn_start = create_hover_button(
            toolbar_frame,
            text="▶ Start Scan",
            bg_color="#10b981",
            hover_color="#059669",
            command=self.start_protection,
            width=15
        )
        self.btn_start.pack(side=tk.LEFT, padx=6)

        self.btn_stop = create_hover_button(
            toolbar_frame,
            text="⏹ Stop Scan",
            bg_color="#ef4444",
            hover_color="#dc2626",
            command=self.stop_protection,
            width=15
        )
        self.btn_stop.pack(side=tk.LEFT, padx=6)

        self.btn_test = create_hover_button(
            toolbar_frame,
            text="🧪 Create Test Threat",
            bg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.create_test_file,
            width=19
        )
        self.btn_test.pack(side=tk.LEFT, padx=6)

        self.btn_inspect = create_hover_button(
            toolbar_frame,
            text="🔍 Inspect Threats",
            bg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=self.open_threat_inspector,
            width=17
        )
        self.btn_inspect.pack(side=tk.LEFT, padx=6)

        self.btn_clear = create_hover_button(
            toolbar_frame,
            text="🧹 Clear Logs",
            bg_color="#475569",
            hover_color="#334155",
            command=self.clear_logs,
            width=12
        )
        self.btn_clear.pack(side=tk.RIGHT, padx=6)

        # ---------------- CONSOLE LOG ---------------- #
        console_container = tk.Frame(self.root, bg=COLOR_CARD, padx=2, pady=2, bd=1, relief=tk.SOLID)
        console_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        console_title_bar = tk.Frame(console_container, bg="#1e293b", height=24)
        console_title_bar.pack(fill=tk.X)

        tk.Label(
            console_title_bar,
            text="  💻 SECURITY EVENT CONSOLE LOG",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg=COLOR_TEXT_MUTED
        ).pack(side=tk.LEFT, pady=2)

        self.output = scrolledtext.ScrolledText(
            console_container,
            bg=COLOR_CONSOLE_BG,
            fg="#e2e8f0",
            insertbackground="white",
            font=("Cascadia Code", 9),
            relief=tk.FLAT,
            bd=5
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        # Console Color Formatting Tags
        self.output.tag_config("timestamp", foreground="#64748b")
        self.output.tag_config("alert", foreground="#ef4444", font=("Cascadia Code", 9, "bold"))
        self.output.tag_config("report", foreground="#38bdf8")
        self.output.tag_config("success", foreground="#10b981")
        self.output.tag_config("usb", foreground="#f59e0b")
        self.output.tag_config("test", foreground="#c084fc")

        # Footer Status Bar
        self.status_label = tk.Label(
            self.root,
            text="Protection Offline • Click 'Start Scan' to begin monitoring or click metric cards to view details.",
            font=("Segoe UI", 9),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MUTED,
            anchor="w",
            padx=20
        )
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=6)

    def _create_card(self, parent, title, default_val, subtext, val_color, click_command=None):
        card = tk.Frame(
            parent,
            bg=COLOR_CARD,
            padx=14,
            pady=12,
            bd=1,
            relief=tk.SOLID,
            cursor="hand2"
        )

        lbl_title = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 8, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT_MUTED,
            cursor="hand2"
        )
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(
            card,
            text=default_val,
            font=("Segoe UI", 13, "bold"),
            bg=COLOR_CARD,
            fg=val_color,
            cursor="hand2"
        )
        lbl_val.pack(anchor="w", pady=(2, 2))

        lbl_sub = tk.Label(
            card,
            text=subtext,
            font=("Segoe UI", 8),
            bg=COLOR_CARD,
            fg="#64748b",
            cursor="hand2"
        )
        lbl_sub.pack(anchor="w")

        def on_enter(e):
            card["bg"] = COLOR_CARD_HOVER
            lbl_title["bg"] = COLOR_CARD_HOVER
            lbl_val["bg"] = COLOR_CARD_HOVER
            lbl_sub["bg"] = COLOR_CARD_HOVER

        def on_leave(e):
            card["bg"] = COLOR_CARD
            lbl_title["bg"] = COLOR_CARD
            lbl_val["bg"] = COLOR_CARD
            lbl_sub["bg"] = COLOR_CARD

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        if click_command:
            for widget in (card, lbl_title, lbl_val, lbl_sub):
                widget.bind("<Button-1>", lambda e: click_command())

        return card, lbl_val

    # ---------------- REFRESH STATUS HELPER ---------------- #

    def refresh_threat_status(self):
        """
        Recalculates active threats and updates metric cards, status badges,
        and system health when a threat is deleted or quarantined.
        """
        remaining_threats = len(control.detected_threats)
        self.threat_count = remaining_threats

        has_system_threats = any(
            "SYSTEM" in t.get("source", "").upper() or "LOCAL" in t.get("source", "").upper()
            for t in control.detected_threats
        )
        control.system_status["unsafe"] = has_system_threats

        if remaining_threats == 0:
            self.val_threat.config(text="0 Threats", fg=COLOR_ACCENT_GREEN)
            self.val_sys.config(text="SAFE ✅", fg=COLOR_ACCENT_GREEN)
            if control.RUNNING:
                self.badge_label.config(text="● PROTECTION ACTIVE", bg="#064e3b", fg="#6ee7b7")
            else:
                self.badge_label.config(text="● SYSTEM IDLE", bg="#334155", fg="#cbd5e1")
        else:
            self.val_threat.config(text=f"{remaining_threats} Threats 🚨", fg=COLOR_ACCENT_RED)
            if has_system_threats:
                self.val_sys.config(text="UNSAFE 🚨", fg=COLOR_ACCENT_RED)

    # ---------------- THREAT INSPECTOR DIALOG ---------------- #

    def open_threat_inspector(self):
        inspector = tk.Toplevel(self.root)
        inspector.title("🛡️ Threat & Connected Device Inspector")
        inspector.geometry("840x480")
        inspector.config(bg=COLOR_BG)

        # Header
        top_frame = tk.Frame(inspector, bg=COLOR_BG, padx=15, pady=10)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame,
            text="🔍 Detected Threats & Connected Device Inspector",
            font=("Segoe UI", 13, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT_MAIN
        ).pack(side=tk.LEFT)

        lbl_count = tk.Label(
            top_frame,
            text=f"Total Threats: {len(control.detected_threats)}",
            font=("Segoe UI", 10, "bold"),
            bg="#334155",
            fg="#f8fafc",
            padx=10,
            pady=3
        )
        lbl_count.pack(side=tk.RIGHT)

        # Table container
        table_frame = tk.Frame(inspector, bg=COLOR_CARD, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        columns = ("time", "source", "ext", "file_path")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10, selectmode="extended")

        tree.heading("time", text="Timestamp")
        tree.heading("source", text="Device / Source")
        tree.heading("ext", text="Type")
        tree.heading("file_path", text="File Location")

        tree.column("time", width=140, anchor="center")
        tree.column("source", width=170, anchor="w")
        tree.column("ext", width=80, anchor="center")
        tree.column("file_path", width=390, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def populate_tree():
            for item in tree.get_children():
                tree.delete(item)
            if not control.detected_threats:
                tree.insert("", tk.END, values=("N/A", "System Clear", "None", "No active threats detected on system or USB drives."))
            else:
                for item in control.detected_threats:
                    tree.insert(
                        "",
                        tk.END,
                        values=(
                            item.get("time", "N/A"),
                            item.get("source", "System"),
                            item.get("ext", "Unknown"),
                            item.get("file_path", "")
                        )
                    )

        populate_tree()

        # Buttons Bar
        btn_bar = tk.Frame(inspector, bg=COLOR_BG, padx=15, pady=12)
        btn_bar.pack(fill=tk.X)

        def open_in_explorer():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Select Item", "Please select a threat from the list first.")
                return
            values = tree.item(selected[0], "values")
            filepath = values[3]
            if os.path.exists(filepath):
                subprocess.run(["explorer", "/select,", os.path.normpath(filepath)])
            else:
                messagebox.showwarning("File Missing", f"File no longer exists at:\n{filepath}")

        def copy_path():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Select Item", "Please select a threat from the list first.")
                return
            values = tree.item(selected[0], "values")
            filepath = values[3]
            inspector.clipboard_clear()
            inspector.clipboard_append(filepath)
            messagebox.showinfo("Copied", f"File path copied to clipboard:\n{filepath}")

        def quarantine_file():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("Select Item", "Please select one or more threats from the list first.")
                return

            deleted = []
            failed = []

            for item_id in selected:
                values = tree.item(item_id, "values")
                filepath = values[3]

                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        self.log(f"[+] Quarantined & deleted threat file: {filepath}")
                        deleted.append(filepath)
                    except Exception as ex:
                        failed.append(f"{filepath} ({ex})")
                        continue
                else:
                    self.log(f"[+] Threat file no longer on disk, removing record: {filepath}")
                    deleted.append(filepath)

                # Remove from control.detected_threats
                control.detected_threats = [
                    t for t in control.detected_threats if t.get("file_path") != filepath
                ]

                # Remove from treeview
                tree.delete(item_id)

            # Refresh main dashboard
            self.refresh_threat_status()
            lbl_count.config(text=f"Total Threats: {len(control.detected_threats)}")

            # Summary message
            summary = f"{len(deleted)} threat(s) removed."
            if failed:
                summary += f"\n\nFailed to delete {len(failed)} file(s):\n" + "\n".join(failed)
            messagebox.showinfo("Quarantine Complete", summary)

        btn_open = create_hover_button(
            btn_bar, text="📂 Open File Location", bg_color="#3b82f6", hover_color="#2563eb",
            command=open_in_explorer, width=20
        )
        btn_open.pack(side=tk.LEFT, padx=5)

        btn_copy = create_hover_button(
            btn_bar, text="📋 Copy Path", bg_color="#475569", hover_color="#334155",
            command=copy_path, width=14
        )
        btn_copy.pack(side=tk.LEFT, padx=5)

        btn_del = create_hover_button(
            btn_bar, text="🗑️ Delete Selected", bg_color="#ef4444", hover_color="#dc2626",
            command=quarantine_file, width=20
        )
        btn_del.pack(side=tk.LEFT, padx=5)

        btn_close = create_hover_button(
            btn_bar, text="✖ Close", bg_color="#334155", hover_color="#475569",
            command=inspector.destroy, width=10
        )
        btn_close.pack(side=tk.RIGHT, padx=5)

    # ---------------- LOGGING & QUEUE PROCESSING ---------------- #

    def log(self, message, alert_file=None):
        self.log_queue.put((message, alert_file))

    def process_log_queue(self):
        while not self.log_queue.empty():
            try:
                message, alert_file = self.log_queue.get_nowait()
                ts = datetime.now().strftime("[%H:%M:%S] ")

                self.output.insert(tk.END, ts, "timestamp")

                if "[ALERT]" in message:
                    self.output.insert(tk.END, message + "\n", "alert")
                    self.refresh_threat_status()
                elif "[REPORT]" in message:
                    self.output.insert(tk.END, message + "\n", "report")
                elif "[+]" in message or "SUCCESS" in message:
                    self.output.insert(tk.END, message + "\n", "success")
                elif "USB" in message:
                    self.output.insert(tk.END, message + "\n", "usb")
                elif "[TEST]" in message:
                    self.output.insert(tk.END, message + "\n", "test")
                else:
                    self.output.insert(tk.END, message + "\n")

                self.output.see(tk.END)

                if alert_file:
                    show_alert(alert_file, confidence=95.0)

            except queue.Empty:
                break

        self.root.after(100, self.process_log_queue)

    def clear_logs(self):
        self.output.delete("1.0", tk.END)

    # ---------------- SCAN CONTROLS ---------------- #

    def start_protection(self):
        if control.RUNNING:
            self.log("[!] Protection scan is already running.")
            return

        control.RUNNING = True
        control.system_status["unsafe"] = False
        control.usb_status.clear()
        control.detected_threats.clear()
        self.threat_count = 0

        os.makedirs(TEST_FOLDER, exist_ok=True)

        self.badge_label.config(text="● PROTECTION ACTIVE", bg="#064e3b", fg="#6ee7b7")
        self.val_sys.config(text="SAFE ✅", fg=COLOR_ACCENT_GREEN)
        self.val_threat.config(text="0 Threats", fg=COLOR_ACCENT_GREEN)
        self.status_label.config(text="Status: Active • Monitoring System folders & USB drives in real-time.")

        self.log("==========================================")
        self.log("[+] RANSOMWARE MONITOR ACTIVATED")
        active_paths = get_system_paths()
        self.log(f"[+] Active monitored paths ({len(active_paths)}):")
        for p in active_paths:
            self.log(f"    • {p}")

        for path in active_paths:
            if os.path.exists(path):
                threading.Thread(
                    target=start_monitor,
                    args=(path, self.log, "SYSTEM"),
                    daemon=True
                ).start()

        threading.Thread(target=detect_usb, args=(self.log,), daemon=True).start()
        threading.Thread(target=self.system_report_timer, daemon=True).start()
        threading.Thread(target=self.usb_report_timer, daemon=True).start()

        self.log("[+] Real-time monitoring engines online...")

    def stop_protection(self):
        if not control.RUNNING:
            self.log("[!] Protection is already stopped.")
            return

        control.RUNNING = False
        self.badge_label.config(text="● MONITORING STOPPED", bg="#334155", fg="#cbd5e1")
        self.status_label.config(text="Status: Stopped • Click 'Start Scan' to resume.")
        time.sleep(0.5)

        self.log("\n==========================================")
        self.log("📌 ===== SUMMARY INCIDENT REPORT =====")

        sys_res = "UNSAFE 🚨" if control.system_status["unsafe"] else "SAFE ✅"
        self.log(f"SYSTEM STATUS : {sys_res}")
        self.log(generate_usb_report())
        self.log("===== MONITORING INACTIVE =====\n")

    # ---------------- TIMERS ---------------- #

    def system_report_timer(self):
        while control.RUNNING:
            for _ in range(15):
                if not control.RUNNING:
                    return
                time.sleep(1)

            if control.system_status["unsafe"]:
                self.log("[PERIODIC REPORT] System Health: UNSAFE 🚨")
            else:
                self.log("[PERIODIC REPORT] System Health: SAFE ✅")

    def usb_report_timer(self):
        while control.RUNNING:
            for _ in range(15):
                if not control.RUNNING:
                    return
                time.sleep(1)

            num_drives = len(control.usb_status)
            if num_drives > 0:
                self.val_usb.config(text=f"{num_drives} Connected", fg=COLOR_ACCENT_AMBER)
            else:
                self.val_usb.config(text="0 Connected", fg=COLOR_ACCENT_BLUE)

            if not control.usb_status:
                self.log("[PERIODIC REPORT] USB Status: No USB detected")
                continue

            self.log("[PERIODIC REPORT] USB Drives Connected:")
            for drive, info in control.usb_status.items():
                status = "UNSAFE 🚨" if info["unsafe"] else "SAFE ✅"
                self.log(f" - {info['name']} ({drive}) : {status}")

    # ---------------- SIMULATION FILE TEST ---------------- #

    def create_test_file(self):
        os.makedirs(TEST_FOLDER, exist_ok=True)
        test_path = os.path.join(TEST_FOLDER, f"simulated_threat_{int(time.time())}.encrypted")
        try:
            with open(test_path, "w", encoding="utf-8") as f:
                f.write("Simulated ransomware payload test.")
            self.log(f"[TEST] Created ransomware simulation file: {test_path}")
            if not control.RUNNING:
                messagebox.showinfo(
                    "Test Threat Created",
                    f"Test file generated at:\n{test_path}\n\nClick 'Start Scan' to trigger detection!"
                )
        except Exception as e:
            self.log(f"[TEST ERROR] Could not create file: {e}")


# ---------------- MAIN ENTRY ---------------- #

if __name__ == "__main__":
    root = tk.Tk()
    app = RansomwareMonitorApp(root)
    root.mainloop()
