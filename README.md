# 🐬 Flipper Zero — BadUSB Keylogger + C2 Forensics Kit

> ⚠️ **Ethical Disclaimer:** This project is strictly educational.
> All testing was performed on my own hardware and machines only.
> Do not deploy this on any device you do not own. Unauthorized use is illegal.

## Overview
A dual red-team / blue-team cybersecurity project demonstrating how a BadUSB keylogger
attack works end-to-end — from deployment via Flipper Zero, to C2 communication,
to real-time detection, forensic analysis, and incident reporting.

## Project Structure
- `red-team/flipper-payloads/` — BadUSB script that deploys the implant
- `red-team/keylogger/`        — The keylogger implant itself
- `red-team/c2-server/`        — Flask C2 server with web dashboard
- `blue-team/detector/`        — Real-time threat detection engine
- `blue-team/forensics/`       — Post-infection log analyzer
- `blue-team/dashboard/`       — Incident report UI
- `docs/`                      — Threat model and attack walkthrough

## Setup
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Status
🔨 In progress
