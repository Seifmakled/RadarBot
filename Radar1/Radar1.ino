#include <Servo.h>

// ── Ultrasonic sensor ──────────────────────────────────────
const int trigPin = 8;
const int echoPin = 9;

// ── Servo ──────────────────────────────────────────────────
const int servoPin = 10;
Servo myServo;

// ── Buzzer ─────────────────────────────────────────────────
const int buzzerPin = 7;

// ── Joystick ───────────────────────────────────────────────
const int joyX  = A0;
const int joySW = 4;

// ── State ──────────────────────────────────────────────────
int  angle      = 90;
int  dir        = 1;
bool manualMode = false;
bool lastSW     = HIGH;

long duration;
int  distance;

unsigned long lastManualSend  = 0;
const unsigned long MANUAL_INTERVAL = 20; // ms


// ── Distance measurement ───────────────────────────────────
int calculateDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH, 25000);
  if (duration == 0) return -1;
  return duration * 0.034 / 2;
}


// ── Setup ──────────────────────────────────────────────────
void setup() {
  pinMode(trigPin,  OUTPUT);
  pinMode(echoPin,  INPUT);
  pinMode(joySW,    INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);

  myServo.attach(servoPin);
  myServo.write(angle);

  Serial.begin(9600); // → Processing (for later)
}


// ── Main loop ──────────────────────────────────────────────
void loop() {

  // ---- Mode toggle via joystick button --------------------
  bool sw = digitalRead(joySW);
  if (lastSW == HIGH && sw == LOW) {
    manualMode = !manualMode;
    delay(200); // debounce
  }
  lastSW = sw;

  // ---- Angle control --------------------------------------
  if (manualMode) {
    int x = analogRead(joyX);
    angle  = map(x, 0, 1023, 15, 165);
  } else {
    angle += dir;
    if (angle >= 165 || angle <= 15) dir = -dir;
  }

  // ---- Sensor read ----------------------------------------
  distance = calculateDistance();

  // ---- Servo move -----------------------------------------
  myServo.write(angle);

  // ---- Buzzer ---------------------------------------------
  if (distance > 0 && distance < 30) {
    tone(buzzerPin, 2000);
  } else {
    noTone(buzzerPin);
  }

  // ---- Send to Processing (angle,distance.) ---------------
  Serial.print(angle);
  Serial.print(",");
  Serial.print(distance);
  Serial.println(".");

  // ---- Send to Python logger (angle,distance,mode,buzzer) -
  bool buzzerActive = (distance > 0 && distance < 30);
  Serial.print(angle);
  Serial.print(",");
  Serial.print(distance);
  Serial.print(",");
  Serial.print(manualMode ? 1 : 0);
  Serial.print(",");
  Serial.println(buzzerActive ? 1 : 0);

  // ---- Timing ---------------------------------------------
  if (manualMode) {
    // rate-limit in manual to avoid servo jitter
    unsigned long now = millis();
    if (now - lastManualSend < MANUAL_INTERVAL) {
      delay(MANUAL_INTERVAL - (now - lastManualSend));
    }
    lastManualSend = millis();
  } else {
    delay(30);
  }
}
