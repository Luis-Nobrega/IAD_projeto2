#include <Servo.h> // Include servo library

Servo servo1; // Servos for movement 
Servo servo2;
Servo servo3; // Servo to release missile 
int wait = 20; // Delay in ms
float pos1 = 90;
float pos2 = 90;
float passo = 0.5;
const int servo_X_min = 60;
const int servo_X_max = 120;
const int servo_Y_min = 60;
const int servo_Y_max = 120;

void setup() {
    Serial.begin(9600); // Start serial communication
    servo1.attach(2);  // Attach servos to their pins
    servo2.attach(3);
    servo3.attach(4); 

    delay(500);
}

void movement1(int signal){
    // 180 front; 90 stop; 0 backwards
    if (signal == 1) { 
        pos1 = constrain(pos1 - passo, servo_X_min, servo_X_max);
        servo1.write(pos1 - passo); // Move forward
    } else if (signal == 2) { 
        pos1 = constrain(pos1 + passo, servo_X_min, servo_X_max);
        servo1.write(pos1 + passo); // Move backward verificar
    } else {
        servo1.write(pos1); // Stop
    }
}

void movement2(int signal){
    // 180 front; 90 stop; 0 backwards
    if (signal == 1) { 
        pos2 = constrain(pos2 + passo, servo_Y_min, servo_Y_max);
        servo2.write(pos2 + passo); // Move forward
    } else if (signal == 2) { 
        pos2 = constrain(pos2 - passo, servo_Y_min, servo_Y_max);
        servo2.write(pos2 - passo); // Move backward
    } else {
        servo2.write(pos2); // Stop
    }
}

void missile(int signal){
    if (signal == 1) { 
        servo3.write(0); // Move forward
        delay(19 * wait); // manually tested for full rotation
        servo3.write(180);
        delay(38 * wait);
        servo3.write(0);
        delay(19 * wait);
        servo3.write(90);
    }
    else if (signal == 2) { 
        servo3.write(0); // Move backward
        delay(5 * wait); 
        servo3.write(90);
    } else if (signal == 3){
        servo3.write(180); // Move backward
        delay(5 * wait); 
        servo3.write(90);
    }
}

void loop() {
    if (Serial.available() > 0) { // Wait for incoming data
        String input = Serial.readStringUntil('\n'); // Read the incoming string
        if (input.length() >= 7 && input[0] == '[' && input[6] == ']') { // Validate format [x,y,z]
            int signal1 = input[1] - '0'; // Extract first value
            int signal2 = input[3] - '0'; // Extract second value
            int signal3 = input[5] - '0'; // Extract third value
            
            movement1(signal1);
            delay(wait);
            movement2(signal2);
            delay(wait);
            missile(signal3);
        }
        else if (input == "CALIBRAR") {
        pos1 = 100;
        pos2 = 90;
        servo1.write(100);  // Or whatever is the center
        servo2.write(90);
        }
        else if (input.startsWith("SERVOX:")) {
            int value = input.substring(7).toInt();
            pos1 = constrain(value, servo_X_min, servo_X_max);
            servo1.write(pos1);
          } 
        else if (input.startsWith("SERVOY:")) {
        int value = input.substring(7).toInt();
        pos2 = constrain(value, servo_Y_min, servo_Y_max);
        servo2.write(pos2);
        } 
    }
    static unsigned long last_feedback = 0;
    if (millis() - last_feedback >= 100) {
    Serial.print("POS:");
    Serial.print((int)pos1);
    Serial.print(":");
    Serial.println((int)pos2);
    last_feedback = millis();
  }
  

    delay(wait); // Small delay to allow stable communication
}
