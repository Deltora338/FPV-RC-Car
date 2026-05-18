#include <Servo.h>

Servo myServo;

const int powerPin = 5;
const int inputPin = 9;

void setup() {
  myServo.attach(9);  
}

void loop() {
  // Sweep from 0 to 180 degrees
  for (int pos = 0; pos <= 180; pos += 1) { 
    myServo.write(pos);  
    delay(15);  
  }
  
  // Sweep back from 180 to 0 degrees
  for (int pos = 180; pos >= 0; pos -= 1) { 
    myServo.write(pos);  
    delay(15);  
  }
}