#include <Servo.h>

Servo servo1;
Servo servo2;
Servo servo_fire_ts;
int wait = 10;
float pos1 = 90;
float pos2 = 90;
float pos = 90;
float passo = 2.0;

void setup() {
  Serial.begin(9600);
  servo1.attach(2);
  servo2.attach(3);
  servo_fire_ts.attach(5);
  delay(500);
}

void movement1(int signal) {
  if (signal == 1) {
    pos1 = constrain(pos1 - passo, 30, 150);
    servo1.write(pos1);
  } else if (signal == 2) {
    pos1 = constrain(pos1 + passo, 30, 150);
    servo1.write(pos1);
  } else {
    servo1.write(pos1);
  }
}

void movement2(int signal) {
  if (signal == 1) {
    pos2 = constrain(pos2 + passo, 0, 180);
    servo2.write(pos2);
  } else if (signal == 2) {
    pos2 = constrain(pos2 - passo, 0, 180);
    servo2.write(pos2);
  } else {
    servo2.write(pos2);
  }
}

void missile(int signal) {
  if (signal == 1) {
    servo_fire_ts.write(180);
    delay(5 * wait);
    servo_fire_ts.write(0);
    delay(5 * wait);
    servo_fire_ts.write(90);
  }
}

void loop() {

    //servo_fire_ts.write(0);
    //delay(2000);
  
    //     servo_fire_ts.writeMicroseconds(1300);
    //delay(1000);
    //servo_fire_ts.writeMicroseconds(1700);
    //Serial.print("rfghn");
  
    //servo_fire_ts.write(180);
    //delay(2000);
  
    // servo1.write(90);
    //delay(1000);
  
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("SERVOX:")) {
      int value = input.substring(7).toInt();
      pos1 = constrain(value, 0, 180);
      servo1.write(pos1);
    } else if (input.startsWith("SERVOY:")) {
      int value = input.substring(7).toInt();
      pos2 = constrain(value, 0, 180);
      servo2.write(pos2);
    } else if (input == "CALIBRAR") {
      pos1 = 100;
      pos2 = 90;
      servo1.write(pos1);
      servo2.write(pos2);
    } else if (input.length() >= 7 && input[0] == '[' && input[6] == ']') {
      int signal1 = input[1] - '0';
      int signal2 = input[3] - '0';
      int signal3 = input[5] - '0';

      movement1(signal1);
      delay(wait);
      movement2(signal2);
      delay(wait);
      missile(signal3);
    }

    // Send back position feedback
    Serial.print("POS:");
    Serial.print((int)pos1);
    Serial.print(":");
    Serial.println((int)pos2);
  

  }

  delay(wait);
}
