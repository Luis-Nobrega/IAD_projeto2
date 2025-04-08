#include <Servo.h>

// Servo objects
Servo servo_x;  // Horizontal servo
Servo servo_y;  // Vertical servo
Servo servo_fire;

// Configuration
const int WAIT_DELAY = 10;  // ms
const float STEP_SIZE = 1.5; // degrees per step
const int SERVO_X_MIN = 30;
const int SERVO_X_MAX = 150;
const int SERVO_Y_MIN = 30;
const int SERVO_Y_MAX = 150;

// Current positions
float pos_x = 90;
float pos_y = 90;

void setup() {
  Serial.begin(115200);  // Increased baud rate
  
  servo_x.attach(2);
  servo_y.attach(3);
  servo_fire.attach(5);
  
  // Initialize servos to center position
  servo_x.write(pos_x);
  servo_y.write(pos_y);
  servo_fire.write(90);
  
  delay(1000);  // Allow servos to reach position
}

void move_servo_x(int direction, int steps) {
  float movement = STEP_SIZE * steps;
  
  if (direction == 1) {  // Move right
    pos_x = constrain(pos_x - movement, SERVO_X_MIN, SERVO_X_MAX);
  } 
  else if (direction == 2) {  // Move left
    pos_x = constrain(pos_x + movement, SERVO_X_MIN, SERVO_X_MAX);
  }
  
  servo_x.write(pos_x);
  delay(WAIT_DELAY);
}

void move_servo_y(int direction, int steps) {
  float movement = STEP_SIZE * steps;
  
  if (direction == 1) {  // Move up (corrected direction)
    pos_y = constrain(pos_y - movement, SERVO_Y_MIN, SERVO_Y_MAX);
  } 
  else if (direction == 2) {  // Move down (corrected direction)
    pos_y = constrain(pos_y + movement, SERVO_Y_MIN, SERVO_Y_MAX);
  }
  
  servo_y.write(pos_y);
  delay(WAIT_DELAY);
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

void process_command(String input) {
  input.trim();
  
  // Direct servo position commands
  if (input.startsWith("SERVOX:")) {
    int value = input.substring(7).toInt();
    pos_x = constrain(value, SERVO_X_MIN, SERVO_X_MAX);
    servo_x.write(pos_x);
  } 
  else if (input.startsWith("SERVOY:")) {
    int value = input.substring(7).toInt();
    pos_y = constrain(value, SERVO_Y_MIN, SERVO_Y_MAX);
    servo_y.write(pos_y);
  } 
  // Calibration command
  else if (input == "CALIBRAR") {
    pos_x = 90;
    pos_y = 90;
    servo_x.write(pos_x);
    servo_y.write(pos_y);
    delay(1000);
  } 
  // Movement command [x_dir,x_steps,y_dir,y_steps,fire]
  else if (input.length() >= 7 && input[0] == '[' && input[input.length()-1] == ']') {
    int x_dir = input[1] - '0';
    int x_steps = input.substring(3, input.indexOf(',', 3)).toInt();
    int y_dir = input[input.indexOf(',', 3)+1] - '0';
    int y_steps = input.substring(input.indexOf(',', input.indexOf(',', 3)+1)+1, input.length()-1).toInt();
    
    if (x_dir >= 0 && x_dir <= 2 && x_steps > 0) {
      move_servo_x(x_dir, x_steps);
    }
    if (y_dir >= 0 && y_dir <= 2 && y_steps > 0) {
      move_servo_y(y_dir, y_steps);
    }
    if (input.indexOf('1', input.indexOf(',', input.indexOf(',', 3)+1)+1) != -1) {
      fire_missile();
    }
  }
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    process_command(input);
  }
  
  // Send position feedback every 100ms
  static unsigned long last_feedback = 0;
  if (millis() - last_feedback >= 100) {
    Serial.print("POS:");
    Serial.print((int)pos_x);
    Serial.print(":");
    Serial.println((int)pos_y);
    last_feedback = millis();
  }
  
  delay(WAIT_DELAY);
}