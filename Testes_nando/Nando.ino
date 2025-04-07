#include <Servo.h> // Include servo library

Servo servo1; // Servos for movement 
Servo servo2;
Servo servo3; // Servo to release missile 
int wait = 20; // Delay in ms
int pos1 = 90;
int pos2 = 90;
int pos = 90;

// movement limitations
int max_x = 130;
int min_x = 50;
int max_y = 130;
int min_y = 50; 

void setup() {
    Serial.begin(9600); // Start serial communication
    servo1.attach(2);  // Attach servos to their pins
    servo2.attach(3);
    servo3.attach(4); 

    delay(500);

    // Move servos to initial position
    servo1.write(pos1);
    servo2.write(pos2);

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
        
        if (input.startsWith("[") && input.endsWith("]")) { // Validate format [x,y,z]
            // Remove the brackets
            input = input.substring(1, input.length() - 1);

            // Split the string by commas
            int comma1 = input.indexOf(',');
            int comma2 = input.indexOf(',', comma1 + 1);

            if (comma1 != -1 && comma2 != -1) {
                String str1 = input.substring(0, comma1);
                String str2 = input.substring(comma1 + 1, comma2);
                String str3 = input.substring(comma2 + 1);

                int signal1 = str1.toInt();
                int signal2 = str2.toInt();
                int signal3 = str3.toInt();

                // The number of commands received has to be controled in the ino file 

                if (signal1 > min_x || signal1 < max_x) { // set maximum movement as fov of camera (120º)
                    servo1.write(signal1);
                    
                }
                else { // bound movement to maximum
                    servo1.write(constrain(signal1, min_x, max_x));
                }
                if (signal2 > min_y || signal2 < max_y) {
                    servo2.write(signal2);
                }
                else {
                    servo1.write(constrain(signal2, min_y, max_y));
                }
                // Check if the third signal is for missile launch
                missile(signal3);
            }
        }
    }
    delay(wait); // Small delay to allow stable communication
}

