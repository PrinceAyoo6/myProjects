import os
import threading
from collections import defaultdict, deque
from datetime import datetime
from flask import Flask, render_template, jsonify
from scapy.all import sniff, IP, TCP, UDP, Raw, conf

app = Flask(__name__)

# --- GLOBAL STATE ---
# Limit lists to prevent memory overflow
MAX_PACKETS = 500
MAX_ALERTS = 50

state = {
    "is_sniffing": True,
    "packet_counter": 0,
    "alert_counter": 0,
    "total_packets": 0,
    "protocols": {"TCP": 0, "UDP": 0, "OTHER": 0},
    "ip_count": defaultdict(int),
    "port_scan_tracker": defaultdict(set),
    "recent_packets": deque(maxlen=MAX_PACKETS),
    "alerts": deque(maxlen=MAX_ALERTS)
}

def add_alert(msg, level="warning"):
    state["alert_counter"] += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    state["alerts"].appendleft({"id": state["alert_counter"], "time": timestamp, "message": msg, "level": level})

def packet_callback(packet):
    state["total_packets"] += 1

    if IP in packet:
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        protocol = "OTHER"

        if TCP in packet:
            protocol = "TCP"
            state["protocols"]["TCP"] += 1
            dst_port = packet[TCP].dport
            
            # Port Scan Detection
            state["port_scan_tracker"][src_ip].add(dst_port)
            scanned_ports = len(state["port_scan_tracker"][src_ip])
            
            if scanned_ports > 10 and scanned_ports % 10 == 1: # Alert every 10 ports to avoid spam
                add_alert(f"🚨 PORT SCAN DETECTED from {src_ip} ({scanned_ports} ports)", "danger")

        elif UDP in packet:
            protocol = "UDP"
            state["protocols"]["UDP"] += 1
        else:
            state["protocols"]["OTHER"] += 1

        state["ip_count"][src_ip] += 1

        # Suspicious traffic (High Volume)
        if state["ip_count"][src_ip] == 20:
            add_alert(f"⚠️ HIGH TRAFFIC from {src_ip}", "warning")

        # Payload analysis
        payload_preview = ""
        is_website = False
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            try:
                payload_text = payload.decode(errors="ignore")
                if "Host:" in payload_text:
                    is_website = True
                    for line in payload_text.split("\r\n"):
                        if "Host:" in line:
                            payload_preview = line.strip()
                            break
                if not payload_preview:
                    payload_preview = payload_text[:50] + "..."
            except Exception:
                pass

        # Save to recent packets
        state["packet_counter"] += 1
        packet_info = {
            "id": state["packet_counter"],
            "time": datetime.now().strftime("%H:%M:%S"),
            "src": src_ip,
            "dst": dst_ip,
            "protocol": protocol,
            "info": "🌐 Website HTTP" if is_website else "Standard Traffic",
            "payload": payload_preview
        }
        state["recent_packets"].appendleft(packet_info)

def start_sniffer():
    import time
    while True:
        if state["is_sniffing"]:
            try:
                # Use stop_filter to break out of sniff() when is_sniffing becomes False
                sniff(prn=packet_callback, store=False, stop_filter=lambda x: not state["is_sniffing"])
            except PermissionError:
                print("[!] Permission Denied. Run as Administrator.")
                time.sleep(5)
            except RuntimeError as e:
                if "winpcap is not installed" in str(e).lower():
                    print("[*] Npcap not found. Attempting to fall back to native Windows L3 socket...")
                    conf.L2listen = conf.L3socket
                    try:
                        sniff(prn=packet_callback, store=False, stop_filter=lambda x: not state["is_sniffing"])
                    except OSError as e2:
                        print(f"[!] Sniffing failed: {e2}")
                        time.sleep(5)
                else:
                    print(f"[!] Sniffing error: {e}")
                    time.sleep(5)
            except OSError as e:
                print(f"[!] OS Error: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"[!] Unexpected error: {e}")
                time.sleep(5)
        else:
            # If not sniffing, sleep and check again later
            time.sleep(1)

# Start the background thread
sniffer_thread = threading.Thread(target=start_sniffer, daemon=True)
sniffer_thread.start()

# --- FLASK ROUTES ---

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/toggle", methods=["POST"])
def toggle_sniffing():
    state["is_sniffing"] = not state["is_sniffing"]
    if state["is_sniffing"]:
        add_alert("Sniffing Resumed", "info")
    else:
        add_alert("Sniffing Paused", "info")
    return jsonify({"is_sniffing": state["is_sniffing"]})

@app.route("/api/data")
def api_data():
    # Sort top IPs
    top_ips = sorted(state["ip_count"].items(), key=lambda x: x[1], reverse=True)[:50]
    
    return jsonify({
        "is_sniffing": state["is_sniffing"],
        "stats": {
            "total_packets": state["total_packets"],
            "protocols": state["protocols"],
            "top_ips": top_ips
        },
        "packets": list(state["recent_packets"])[:100], # Changed from 50 to 100
        "alerts": list(state["alerts"])
    })

if __name__ == "__main__":
    # Disable reloader so we don't start the sniffer thread twice
    app.run(debug=True, use_reloader=False)
