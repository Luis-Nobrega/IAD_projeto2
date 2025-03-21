#include <Servo.h> // Include servo library

Servo servo1; // Servos for movement 
Servo servo2;
Servo servo3; // Servo to release missile 
int wait = 20; // Delay in ms

void setup() {
    Serial.begin(9600); // Start serial communication
    servo1.attach(2);  // Attach servos to their pins
    servo2.attach(3);
    servo3.attach(4); 
}

void movement1(int signal){
    // 180 front; 90 stop; 0 backwards
    if (signal == 1) { 
        servo1.write(180); // Move forward
    } else if (signal == -1) { 
        servo1.write(0); // Move backward
    } else {
        servo1.write(90); // Stop
    }
}

void movement2(int signal){
    // 180 front; 90 stop; 0 backwards
    if (signal == 1) { 
        servo2.write(180); // Move forward
    } else if (signal == -1) { 
        servo2.write(0); // Move backward
    } else {
        servo2.write(90); // Stop
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
        
        if (input.length() >= 7 && input[0] == '[' && input[6] == ']') { // Validate format [x,y,z]
            int signal1 = input[1] - '0'; // Extract first value
            int signal2 = input[3] - '0'; // Extract second value
            int signal3 = input[5] - '0'; // Extract third value
            
            movement1(signal1);
            movement2(signal2);
            missile(signal3);
        }
    }
    delay(wait); // Small delay to allow stable communication
}