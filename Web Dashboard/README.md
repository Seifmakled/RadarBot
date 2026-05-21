# Radar Web Dashboard

A web-based replacement for `logger.py` / `run_logger.bat`. It reads the same
serial stream from the Arduino, writes the same rows to the shared
`radar_logs.db`, **and** serves a live, animated radar dashboard in your
browser.

![mode banner: LIVE / SIMULATION shown in the top-right of the UI]

## Run it

```bat
cd "Web Dashboard"
run_dashboard.bat
```

…or manually:

```bash
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**.

> ⚠️ Only one program can hold the serial port at a time. Close the Processing
> sketch and the old `logger.py` before starting the dashboard.

## Modes

The status pill (top-right) always shows what the backend is doing:

| Pill | Meaning |
|------|---------|
| **LIVE** | Connected to the Arduino; readings are streaming and being logged to `radar_logs.db`. |
| **SIMULATION** | Serial port couldn't be opened (no board / wrong port / pyserial missing). The dashboard runs on synthetic data so you can still see it work. *Simulated data is NOT written to the database.* |
| **PORT BUSY** | The port exists but another program holds it (Processing or the old logger). Close that program and restart. |
| **NO DATA** | The port opened but no valid packets arrived in 8 s (Arduino not running `Radar1.ino`, or wrong baud). |

## Configuration

All optional, via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `RADAR_PORT` | `COM7` | Serial port |
| `RADAR_BAUD` | `9600` | Baud rate (matches `Radar1.ino`) |
| `RADAR_DB` | `../radar_logs.db` | SQLite database path |
| `RADAR_SIM` | `0` | Set to `1` to force simulation mode |
| `RADAR_HOST` | `127.0.0.1` | Web host |
| `RADAR_WEBPORT` | `5000` | Web port |

PowerShell example (force the demo, different port):

```powershell
$env:RADAR_SIM = "1"; python app.py
```

## How it connects to the logger

`app.py` contains the exact serial-parsing + SQLite-insert logic from
`logger.py` (4-field `angle,distance,mode,buzzer` packets, one persisted row
per second). The browser receives every reading live via Server-Sent Events
(`/api/stream`) for the radar/metrics/trend, and polls `/api/history` to show
the rows actually persisted in `radar_logs.db`.

## Endpoints

- `GET /` — the dashboard
- `GET /api/stream` — SSE feed of the latest reading (~20 Hz)
- `GET /api/history?limit=N` — most recent persisted rows as JSON
