# Real-Time Network Threat Detection and Traffic Analysis System

## Overview

This project is a **real-time network monitoring and threat detection system** that captures and analyzes network packets using packet sniffing techniques.

The system is designed to monitor network traffic, identify suspicious activity, and record network events for security analysis.

## Features

- Real-time network packet sniffing
- Network traffic analysis
- Detection of suspicious network activity
- Web-based monitoring interface
- Network activity logging
- Simple and easy-to-use interface

## Technologies Used

- **Python**
- **Flask**
- **HTML**
- **CSS**
- **JavaScript**
- **Packet Sniffing / Network Analysis**

## Project Structure

```text
NetworkThreatDetector/
│
├── __pycache__/
│   └── packet_sniffer.cpython-*.pyc
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── app.py
├── network_logs.txt
└── test.txt
```

### File Description

| File/Folder | Purpose |
|---|---|
| `app.py` | Main Python application |
| `static/` | Contains the CSS and JavaScript files |
| `static/style.css` | Controls the appearance of the web interface |
| `static/script.js` | Handles client-side JavaScript functionality |
| `templates/` | Contains the HTML templates |
| `templates/index.html` | Main web interface |
| `network_logs.txt` | Stores network monitoring/log information |
| `test.txt` | Test data/file used during development |
| `__pycache__/` | Python-generated cache files |

## How It Works

The system follows a simple process:

1. The application starts through `app.py`.
2. Network packets are captured using packet sniffing techniques.
3. Network traffic is analyzed for relevant information.
4. Suspicious or unusual activity can be identified.
5. Network information is recorded in the log file.
6. Results can be viewed through the web interface.

## Installation

Make sure Python is installed on your computer.

Install the required dependencies used by the project. If you have a `requirements.txt` file, run:

```bash
pip install -r requirements.txt
```

Otherwise, install the packages required by `app.py` according to the libraries used in your implementation.

## Running the Project

Open a terminal inside the `NetworkThreatDetector` folder and run:

```bash
python app.py
```

Then open the local web address displayed by Flask in your browser.

> Depending on your operating system and packet-sniffing configuration, administrator/root privileges may be required.

## Example Use

The system can be used in an authorized test environment to:

- Monitor network traffic.
- Observe packet activity.
- Analyze network communications.
- Identify potentially suspicious behavior.
- Keep a record of network activity.

## Security and Ethical Use

This project is intended for **educational, research, and authorized cybersecurity purposes**.

Only monitor networks and devices that you own or have explicit permission to monitor. Do not use the system to intercept or analyze network traffic without authorization.

## Future Improvements

Possible improvements include:

- Advanced threat detection rules
- Machine-learning-based anomaly detection
- Real-time security alerts
- Interactive traffic dashboards
- Database storage for logs
- IP address reputation checking
- More detailed protocol analysis
- Email or notification alerts

## Author

**Prince Abatan**

---

⭐ If you find this project useful, feel free to star the repository on GitHub.
