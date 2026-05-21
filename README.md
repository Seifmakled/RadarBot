# RadarBot — Ultrasonic Radar System

**Team:** Seif Mohamed Fouad Makled & Antoni Ashraf Mikhael  
**Course:** Selected Topics in CS — Embedded Systems  
**Year:** Third Year, CS-AI

---

## What It Does

A real-time radar system built on a single Arduino. The servo rotates an ultrasonic sensor across a 150° arc, measures distances, drives a buzzer alarm when objects get too close, and streams data to a Processing visualization and a Python/SQLite logger.

---

## Hardware Required

- Arduino (Uno or Mega)
- HC-SR04 Ultrasonic Sensor
- SG90 Micro Servo Motor
- Joystick Module
- Passive Buzzer
- Breadboard + jumper cables

## Wiring

| Component | Pin |
|-----------|-----|
| HC-SR04 Trig | Pin 8 |
| HC-SR04 Echo | Pin 9 |
| Servo Signal | Pin 10 |
| Buzzer (+) | Pin 7 |
| Joystick HORZ | A0 |
| Joystick SEL | Pin 4 |
| HC-SR04 VCC, Servo VCC, Joystick VCC | Breadboard 5V rail → Arduino 5V |
| All GNDs | Breadboard GND rail → Arduino GND |

---

## Software Setup

### 1. Arduino
- Open `Radar1/Radar1.ino` in Arduino IDE
- Select your board and COM port
- Upload

### 2. Processing (Radar UI)
- Open `Processing Code/Radar_pde.pde` in Processing
- Find this line and change the port to match yours:
  ```java
  myPort = new Serial(this, "COM5", 9600);
  ```
- Click Play ▶

### 3. Python Logger (Database)
Install dependency:
```bash
pip install pyserial
```
Run the logger (or double-click `run_logger.bat`):
```bash
python logger.py
```
Data is saved to `radar_logs.db` — open with DB Browser for SQLite.

> **Note:** Processing and the Python logger cannot run at the same time. They share the same COM port. Close one before opening the other.

---

## Operation Modes

| Mode | How to activate | Behaviour |
|------|----------------|-----------|
| **Auto** | Default on startup | Servo sweeps 15°→165° continuously |
| **Manual** | Press joystick button | Joystick controls servo angle directly |

Buzzer activates automatically when distance < 30 cm in either mode.

---

## Database Schema

Table: `radar_logs`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| timestamp | TEXT | ISO 8601 timestamp |
| angle | INTEGER | Servo angle (15–165°) |
| distance | INTEGER | Distance in cm (−1 = out of range) |
| mode | INTEGER | 0 = Auto, 1 = Manual |
| buzzer_active | INTEGER | 0 = OFF, 1 = ON |

---

## Troubleshooting

**COM port not found** — Check Device Manager → Ports and update the port number in `Radar_pde.pde` and `logger.py`.

**Servo not moving** — Re-upload `Radar1.ino`. If it still twitches or resets the board, power the servo from a separate 5V source sharing the same GND.

**No readings in logger** — Make sure Processing is closed first, then run the logger.

**Buzzer not beeping** — Confirm long leg of buzzer is on Pin 7 and short leg is on GND.
