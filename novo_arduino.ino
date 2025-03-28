#include <Servo.h> // Include servo library

Servo servo1; // Servo for X-axis movement
Servo servo2; // Servo for Y-axis movement
Servo servo3; // Servo to release missile

int wait = 20; // Delay in ms
float pos1 = 90; // Current position for servo1
float pos2 = 90; // Current position for servo2
float passo = 0.5; // Increment step for incremental movement

void setup() {
  Serial.begin(9600); // Start serial communication
  servo1.attach(2);   // Attach servos to their pins
  servo2.attach(3);
  servo3.attach(4);
  delay(500);
}

void movement1(int signal) {
  // Incremental control for servo1
  if (signal == 1) { 
    pos1 = constrain(pos1 - passo, 0, 180);
  } else if (signal == 2) { 
    pos1 = constrain(pos1 + passo, 0, 180);
  }
  servo1.write(pos1);
}

void movement2(int signal) {
  // Incremental control for servo2
  if (signal == 1) { 
    pos2 = constrain(pos2 + passo, 0, 180);
  } else if (signal == 2) { 
    pos2 = constrain(pos2 - passo, 0, 180);
  }
  servo2.write(pos2);
}

void missile(int signal) {
  if (signal == 1) { 
    servo3.write(180); // Activate missile release
    delay(5 * wait); 
    servo3.write(0);
    delay(5 * wait);
    servo3.write(90);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // Remove any extra whitespace
    
    // Check for absolute positioning commands from the Python sliders
    if (input.startsWith("SERVOX:")) {
      String valueStr = input.substring(7); // Extract angle value after "SERVOX:"
      int angle = valueStr.toInt();
      pos1 = constrain(angle, 0, 180);
      servo1.write(pos1);
    }
    else if (input.startsWith("SERVOY:")) {
      String valueStr = input.substring(7); // Extract angle value after "SERVOY:"
      int angle = valueStr.toInt();
      pos2 = constrain(angle, 0, 180);
      servo2.write(pos2);
    }
    // Calibration command using absolute positioning
    else if (input == "CALIBRAR") {
      pos1 = 100; // Adjust these center values as needed
      pos2 = 90;
      servo1.write(pos1);
      servo2.write(pos2);
    }
    // Incremental movement command using the [x,y,z] format
    else if (input.length() >= 7 && input.charAt(0) == '[' && input.charAt(6) == ']') {
      int signal1 = input.charAt(1) - '0'; // Extract first value
      int signal2 = input.charAt(3) - '0'; // Extract second value
      int signal3 = input.charAt(5) - '0'; // Extract third value
      movement1(signal1);
      delay(wait);
      movement2(signal2);
      delay(wait);
      missile(signal3);
    }
  }
  delay(wait); // Small delay for stable communication
}
