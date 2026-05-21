"""
Radar Web Dashboard
===================
A drop-in upgrade of logger.py: it does everything the original logger did
(reads the Arduino on the serial port, parses "angle,distance,mode,buzzer"
packets, and persists them to the shared radar_logs.db) *and* serves a live
web UI that visualises the radar sweep in real time.

Run it INSTEAD of run_logger.bat / logger.py — only one program can hold the
serial port at a time.

If the serial port can't be opened (no Arduino, wrong port, or the port is
busy because Processing/the old logger is running) the app automatically
switches to SIMULATION mode so the dashboard is still fully demonstrable.
A banner in the UI always tells you which mode you're in.

Config via environment variables (all optional):
    RADAR_PORT   serial port      (default: COM7)
    RADAR_BAUD   baud rate        (default: 9600)
    RADAR_DB     sqlite db path   (default: ../radar_logs.db)
    RADAR_SIM    set to 1 to force simulation mode
    RADAR_HOST   web host         (default: 127.0.0.1)
    RADAR_WEBPORT  web port       (default: 5000)
"""

import os
import json
import math
import time
import random
import sqlite3
import threading
from datetime import datetime

from flask import Flask, Response, jsonify, render_template, request

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))

PORT = os.environ.get("RADAR_PORT", "COM7")
BAUD = int(os.environ.get("RADAR_BAUD", "9600"))
DB_PATH = os.environ.get("RADAR_DB", os.path.normpath(os.path.join(HERE, "..", "radar_logs.db")))
FORCE_SIM = os.environ.get("RADAR_SIM", "0") == "1"
LOG_INTERVAL = 1.0          # seconds between persisted DB rows (matches logger.py)
NO_DATA_TIMEOUT = 8.0       # flag NO_DATA if the port opens but stays silent this long

# ----------------------------------------------------------------------------
# Shared live state (guarded by `lock`)
# ----------------------------------------------------------------------------
# source values: STARTING | LIVE | SIM | PORT_BUSY | NO_DATA
state = {
    "angle": 90,
    "distance": -1,
    "mode": 0,
    "buzzer": 0,
    "source": "STARTING",
    "connected": False,
    "port": PORT,
    "baud": BAUD,
    "reason": "",
    "last_update": None,
    "total_readings": 0,
    "logged_rows": 0,
}
lock = threading.Lock()

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS radar_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            angle INTEGER,
            distance INTEGER,
            mode INTEGER,
            buzzer_active INTEGER
        )
        """
    )
    conn.commit()
    conn.close()


def set_state(**kwargs):
    with lock:
        state.update(kwargs)


def push_reading(angle, distance, mode, buzzer, source):
    with lock:
        state["angle"] = angle
        state["distance"] = distance
        state["mode"] = mode
        state["buzzer"] = buzzer
        state["source"] = source
        state["last_update"] = datetime.now().isoformat()
        state["total_readings"] += 1


# ----------------------------------------------------------------------------
# Simulation — synthesises a believable radar sweep with a few "objects"
# ----------------------------------------------------------------------------
# Virtual obstacles as (centre_angle, distance_cm, angular_width)
SIM_OBJECTS = [
    (40, 35, 10),
    (95, 18, 8),
    (140, 70, 14),
]


def _sim_distance(angle):
    best = -1
    for c_ang, dist, width in SIM_OBJECTS:
        if abs(angle - c_ang) <= width:
            jitter = random.randint(-2, 2)
            d = max(2, dist + jitter)
            if best == -1 or d < best:
                best = d
    # occasional dropout (no echo) like a real sensor
    if best == -1 and random.random() < 0.04:
        return -1
    return best


def run_simulator(source, reason=""):
    set_state(source=source, connected=False, reason=reason)
    angle = 15
    direction = 1
    while True:
        angle += direction * 2
        if angle >= 165:
            angle, direction = 165, -1
        elif angle <= 15:
            angle, direction = 15, 1
        distance = _sim_distance(angle)
        buzzer = 1 if (0 < distance < 30) else 0
        push_reading(angle, distance, 0, buzzer, source)
        time.sleep(0.04)


# ----------------------------------------------------------------------------
# Serial worker — real Arduino path, with graceful fallback to simulation
# ----------------------------------------------------------------------------
def run_serial():
    if FORCE_SIM:
        run_simulator("SIM", "forced via RADAR_SIM=1")
        return

    try:
        import serial  # pyserial
    except ImportError:
        run_simulator("SIM", "pyserial not installed")
        return

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except Exception as e:
        msg = str(e)
        src = "PORT_BUSY" if "denied" in msg.lower() or "access" in msg.lower() else "SIM"
        run_simulator(src, f"could not open {PORT}: {msg}")
        return

    set_state(connected=True, source="STARTING", reason=f"listening on {PORT} @ {BAUD}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    last_log = 0.0
    silent_until = time.time() + NO_DATA_TIMEOUT

    while True:
        try:
            line = ser.readline().decode(errors="ignore").strip()
        except Exception as e:
            set_state(connected=False, source="SIM", reason=f"serial error: {e}")
            run_simulator("SIM", f"serial error: {e}")
            return

        if not line:
            with lock:
                still_starting = state["source"] == "STARTING"
            if still_starting and time.time() > silent_until:
                set_state(source="NO_DATA", reason="port open but no packets received")
            continue

        parts = line.split(",")
        if len(parts) != 4:
            continue  # ignore the Processing-format line (angle,distance.)
        try:
            angle = int(parts[0])
            distance = int(parts[1])
            mode = int(parts[2])
            buzzer = int(parts[3])
        except ValueError:
            continue

        push_reading(angle, distance, mode, buzzer, "LIVE")

        now = time.time()
        if now - last_log >= LOG_INTERVAL:
            last_log = now
            cur.execute(
                "INSERT INTO radar_logs (timestamp, angle, distance, mode, buzzer_active) "
                "VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), angle, distance, mode, buzzer),
            )
            conn.commit()
            with lock:
                state["logged_rows"] += 1


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stream")
def stream():
    """Server-Sent Events: pushes the latest reading ~20x/second."""
    def gen():
        while True:
            with lock:
                payload = json.dumps(dict(state))
            yield f"data: {payload}\n\n"
            time.sleep(0.05)

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/history")
def history():
    """Recent persisted rows from the shared radar_logs.db."""
    try:
        limit = max(1, min(500, int(request.args.get("limit", "60"))))
    except ValueError:
        limit = 60
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT timestamp, angle, distance, mode, buzzer_active "
        "FROM radar_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


def main():
    init_db()
    worker = threading.Thread(target=run_serial, daemon=True)
    worker.start()

    host = os.environ.get("RADAR_HOST", "127.0.0.1")
    web_port = int(os.environ.get("RADAR_WEBPORT", "5000"))
    print("=" * 60)
    print("  RADAR WEB DASHBOARD")
    print(f"  Serial : {PORT} @ {BAUD}  (DB: {DB_PATH})")
    print(f"  Open   : http://{host}:{web_port}")
    print("  Stop   : Ctrl+C")
    print("=" * 60)
    # threaded=True so SSE streams don't block the history/static requests
    app.run(host=host, port=web_port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
