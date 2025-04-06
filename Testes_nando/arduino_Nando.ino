#include <Servo.h> // Include servo library

Servo servo1; // Servos for movement 
Servo servo2;
Servo servo3; // Servo to release missile 
int wait = 20; // Delay in ms
float pos1 = 90;
float pos2 = 90;
float pos = 90;
float passo = 0.5;

void setup() {
    Serial.begin(9600); // Start serial communication
    servo1.attach(2);  // Attach servos to their pins
    servo2.attach(3);
    servo3.attach(4); 

    delay(500);
}

void movement1(int signal){
    // 180 front; 90 stop; 0 backwards

    if (signal == 0){
        servo1.write(pos1); // Stop
    } else {
        pos1 = constrain(pos1 - signal * passo, 0, 180);
        servo1.write(pos1 - signal * passo); 
    }
}

void movement2(int signal){
    // 180 front; 90 stop; 0 backwards   

    if (signal == 0){
        servo2.write(pos2); // Stop
    } else {
        pos2 = constrain(pos2 + signal * passo, 0, 180);
        servo2.write(pos2 + signal * passo); 
    }
}

void missile(int signal){
    if (signal == 1) { 
        servo3.write(180); // Move forward
        delay(5 * wait); 
        servo3.write(0);
        delay(5 * wait);
        servo3.write(90);
    }
}

void loop() {
    if (Serial.available() > 0) { // Wait for incoming data
      String input = Serial.readStringUntil('\n'); // Read the incoming string
  
      input.trim(); // Remove any whitespace or newline characters
  
      if (input.startsWith("[") && input.endsWith("]")) { // Validate brackets
        input = input.substring(1, input.length() - 1); // Remove the [ and ]
  
        // Split string by comma
        int values[3]; // To store the three integers
        int index = 0;
        int lastCommaIndex = -1;
  
        for (int i = 0; i < input.length(); i++) {
          if (input[i] == ',' || i == input.length() - 1) {
            int endIdx = (input[i] == ',') ? i : i + 1;
            String part = input.substring(lastCommaIndex + 1, endIdx);
            values[index++] = part.toInt(); // Convert substring to int
            lastCommaIndex = i;
            if (index >= 3) break; // Only expect 3 values
          }
        }
  
        if (index == 3) {
          movement1(values[0]);
          delay(wait);
          movement2(values[1]);
          delay(wait);
          missile(values[2]);
        }
      } else if (input == "CALIBRAR") {
        pos1 = 100;
        pos2 = 90;
        servo1.write(100);  // Or whatever is the center
        servo2.write(90);
      }
    }
  
    delay(wait); // Small delay to allow stable communication
  }
