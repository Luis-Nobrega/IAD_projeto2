#include <Servo.h>  // Include servo library

Servo servo1;  // Servo for X-axis movement
Servo servo2;  // Servo for Y-axis movement
Servo servo3;  // Servo to release missile

int waitTime = 20; // Delay in milliseconds
float pos1 = 90;   // Current position for servo1 (X-axis)
float pos2 = 90;   // Current position for servo2 (Y-axis)
float passo = 0.5; // Step size (adjust as needed)

//-------------------------
// Movement functions
//-------------------------

// Adjust servo1 by a number of steps defined by magnitude.
void movement1(int direction, int magnitude) {
  // direction: 1 means decrease pos1, 2 means increase pos1.
  if (direction == 1) {
    pos1 = constrain(pos1 - (passo * magnitude), 0, 180);
  } else if (direction == 2) {
    pos1 = constrain(pos1 + (passo * magnitude), 0, 180);
  }
  servo1.write(pos1);
}

// Adjust servo2 by a number of steps defined by magnitude.
void movement2(int direction, int magnitude) {
  // direction: 1 means increase pos2, 2 means decrease pos2.
  if (direction == 1) {
    pos2 = constrain(pos2 + (passo * magnitude), 0, 180);
  } else if (direction == 2) {
    pos2 = constrain(pos2 - (passo * magnitude), 0, 180);
  }
  servo2.write(pos2);
}

// Missile or "fire" command.
void missile(int signal) {
  if (signal == 1) { 
    servo3.write(180);
    delay(5 * waitTime);
    servo3.write(0);
    delay(5 * waitTime);
    servo3.write(90);
  }
}

//-------------------------
// Setup and Loop
//-------------------------

void setup() {
  Serial.begin(9600); // Start serial communication
  servo1.attach(2);   // Attach servos to their pins
  servo2.attach(3);
  servo3.attach(4);
  delay(500);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n'); // Read incoming string
    input.trim();
    
    // Check if command is in the format [ ... ]
    if (input.startsWith("[") && input.endsWith("]")) {
      // Remove the surrounding brackets.
      String inner = input.substring(1, input.length() - 1);
      // Find positions of commas.
      int firstComma = inner.indexOf(',');
      int secondComma = inner.indexOf(',', firstComma + 1);
      
      if (firstComma != -1 && secondComma != -1) {
        String s1 = inner.substring(0, firstComma);
        String s2 = inner.substring(firstComma + 1, secondComma);
        String s3 = inner.substring(secondComma + 1);
        
        int value1 = s1.toInt();
        int value2 = s2.toInt();
        int value3 = s3.toInt();
        
        // Interpret command according to our new protocol:
        // If first value is nonzero, command is for servo1.
        if (value1 != 0) {
          // value1: direction for servo1; value2: magnitude.
          movement1(value1, value2);
        } 
        // If first value is zero and second is nonzero, command is for servo2.
        else if (value1 == 0 && value2 != 0) {
          // value2: direction for servo2; value3: magnitude.
          movement2(value2, value3);
        } 
        // If all are zero except the missile signal (e.g., [0,0,1]), then fire.
        else if (value1 == 0 && value2 == 0 && value3 == 1) {
          missile(value3);
        }
      }
    }
    // Also handle calibration command.
    else if (input == "CALIBRAR") {
      pos1 = 100; // Example calibration values
      pos2 = 90;
      servo1.write(pos1);
      servo2.write(pos2);
    }
  }
  delay(waitTime); // Small delay to allow stable communication
}
