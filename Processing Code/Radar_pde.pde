import processing.serial.*;
import java.awt.event.KeyEvent;
import java.io.IOException;

Serial myPort;

String distance = "";
String data = "";
String noObject;
String angle = "";

float pixsDistance;
int iAngle, iDistance;
int index1 = 0;

float radarRadius;   // max radius for 100 cm

void setup() {

  size(1280, 720);
  smooth();

  radarRadius = width * 0.44;

  myPort = new Serial(this, "COM7", 9600);
  myPort.bufferUntil('.');
}

void draw() {

  noStroke();
  fill(0, 4);
  rect(0, 0, width, height - height * 0.065);

  fill(98, 245, 31);
  drawRadar();
  drawLine();
  drawObject();
  drawText();
}

void serialEvent(Serial myPort) {

  data = myPort.readStringUntil('.');
  if (data == null) return;

  data = data.substring(0, data.length() - 1);   // drop trailing '.'

  // The Arduino also prints a 4-field logger line (angle,distance,mode,buzzer)
  // that has no '.', so it gets buffered in front of the next reading.
  // Keep only the text after the last newline -> the clean "angle,distance".
  int nl = data.lastIndexOf('\n');
  if (nl != -1) data = data.substring(nl + 1);
  data = data.trim();

  index1 = data.indexOf(',');
  if (index1 == -1) return;

  angle = data.substring(0, index1);
  distance = data.substring(index1 + 1);

  iAngle = int(angle);
  iDistance = min(int(distance), 100);
}

void drawRadar() {

  pushMatrix();
  translate(width / 2, height - height * 0.074);
  noFill();
  strokeWeight(2);
  stroke(98, 245, 31);

  for (int i = 1; i <= 5; i++) {
    float r = radarRadius * i / 5.0;
    arc(0, 0, r * 2, r * 2, PI, TWO_PI);
  }

  for (int a = 0; a <= 180; a += 30) {
    line(0, 0,
         radarRadius * cos(radians(a)),
        -radarRadius * sin(radians(a)));
  }

  popMatrix();
}

void drawObject() {

  pushMatrix();
  translate(width / 2, height - height * 0.074);
  strokeWeight(9);

  // ---------- COLOR LOGIC ----------
  if (iDistance == -1) {
    stroke(255, 165, 0); // ORANGE → no echo
  } else {
    stroke(255, 10, 10); // RED → valid object
  }

  pixsDistance = map(constrain(iDistance, 0, 100), 0, 100, 0, radarRadius);

  if (iDistance < 100 && iDistance != -1) {
    line(
      pixsDistance * cos(radians(iAngle)),
     -pixsDistance * sin(radians(iAngle)),
      radarRadius * cos(radians(iAngle)),
     -radarRadius * sin(radians(iAngle))
    );
  }

  popMatrix();
}

void drawLine() {

  pushMatrix();
  translate(width / 2, height - height * 0.074);
  strokeWeight(9);
  stroke(30, 250, 60);

  line(0, 0,
       radarRadius * cos(radians(iAngle)),
      -radarRadius * sin(radians(iAngle)));

  popMatrix();
}

void drawText() {

  pushMatrix();

  noObject = (iDistance == -1 || iDistance >= 100) ? "Out of Range" : "In Range";

  fill(0);
  noStroke();
  rect(0, height - height * 0.0648, width, height);

  fill(98, 245, 31);
  textSize(25);

  for (int i = 1; i <= 5; i++) {
    text(i * 20 + "cm",
         width / 2 + radarRadius * i / 5.0 - 35,
         height - height * 0.0833);
  }

  textSize(40);
  text("Seif & Antoni", width * 0.05, height - height * 0.0277);
  text("Angle: " + iAngle + "°", width * 0.45, height - height * 0.0277);

  if (iDistance != -1) {
    text("Distance: " + iDistance + " cm", width * 0.65, height - height * 0.0277);
  } else {
    text("Distance: --", width * 0.65, height - height * 0.0277);
  }

  popMatrix();
}
