#include <Servo.h>

Servo servo1; // X-axis
Servo servo2; // Y-axis
Servo servo3; // Missile trigger

float pos1 = 90; // current X
float pos2 = 90; // current Y
int wait = 20;   // ms delay between actions
float passo = 0.5; // small increment step

unsigned long lastFeedbackTime = 0;
const unsigned long feedbackInterval = 100; // ms

void setup() {
  Serial.begin(9600);
  servo1.attach(2);
  servo2.attach(3);
  servo3.attach(4);
  delay(500);

  servo1.write(pos1);
  servo2.write(pos2);
  servo3.write(90); // Neutral position
}

void movement1(int signal) {
  if (signal == 1) {
    pos1 = constrain(pos1 - passo, 0, 180);
  } else if (signal == 2) {
    pos1 = constrain(pos1 + passo, 0, 180);
  }
  servo1.write(pos1);
}

void movement2(int signal) {
  if (signal == 1) {
    pos2 = constrain(pos2 + passo, 0, 180);
  } else if (signal == 2) {
    pos2 = constrain(pos2 - passo, 0, 180);
  }
  servo2.write(pos2);
}

void missile(int signal) {
  if (signal == 1) {
    servo3.write(180);
    delay(5 * wait);
    servo3.write(0);
    delay(5 * wait);
    servo3.write(90);
  }
}

void sendPositionFeedback() {
  unsigned long now = millis();
  if (now - lastFeedbackTime > feedbackInterval) {
    Serial.print("POS:");
    Serial.print((int)pos1);
    Serial.print(":");
    Serial.println((int)pos2);
    lastFeedbackTime = now;
  }
}

void loop() {
  // Process all available commands in buffer
  while (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // removes trailing newline, etc.

    if (input.startsWith("SERVOX:")) {
      int angle = input.substring(7).toInt();
      pos1 = constrain(angle, 0, 180);
      servo1.write(pos1);
    }
    else if (input.startsWith("SERVOY:")) {
      int angle = input.substring(7).toInt();
      pos2 = constrain(angle, 0, 180);
      servo2.write(pos2);
    }
    else if (input == "CALIBRAR") {
      pos1 = 100;
      pos2 = 90;
      servo1.write(pos1);
      servo2.write(pos2);
    }
    else if (input.length() >= 7 && input.charAt(0) == '[' && input.charAt(6) == ']') {
      int signal1 = input.charAt(1) - '0'; // X movement
      int signal2 = input.charAt(3) - '0'; // Y movement
      int signal3 = input.charAt(5) - '0'; // Missile
      movement1(signal1);
      delay(wait);
      movement2(signal2);
      delay(wait);
      missile(signal3);
    }

    // Optional: print for debugging
    // Serial.println("Received: " + input);
  }

  sendPositionFeedback(); // Periodically update GUI with position
  delay(wait); // Stability delay
}
