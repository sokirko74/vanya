#include <SoftwareSerial.h>

const int HC_ECHO1 = 2; // parktronic1
const int HC_TRIG1 = 3;

const int HC_ECHO2 = 4; // parktronic2
const int HC_TRIG2 = 5;

const int TXD_PIN = 12; // bluetooth tx
const int RXD_PIN = 13; // bluetooth rx

const int JOYSTICK_PIN_X = A0; // ось X джойстика
const int JOYSTICK_PIN_Y = A1; // ось Y джойстика

SoftwareSerial BTSerial(TXD_PIN, RXD_PIN);

void printfSerial(const char *fmt, ...) {
  char buf[128];
  va_list args;
  va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);
  Serial.print(buf);
}

float getDist(uint8_t trig, uint8_t echo) {
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  int us = pulseIn(echo, HIGH, 15000);
  if (us == 0) {
    return -1;
  }
  return (int)(us / 58.2);
}

void setup() {
  Serial.begin(9600);
  pinMode(HC_TRIG1, OUTPUT);
  pinMode(HC_ECHO1, INPUT);
  pinMode(HC_TRIG2, OUTPUT);
  pinMode(HC_ECHO2, INPUT);
  BTSerial.begin(38400);
  printfSerial("start setup\n");
}

int readRawAvg(int pin) {
  int r1 = analogRead(pin);
  int r2 = analogRead(pin);
  int r3 = analogRead(pin);
  return (r1 + r2 + r3) / 3;
}

void loop() {
  int distance1 = getDist(HC_TRIG1, HC_ECHO1);
  int distance2 = getDist(HC_TRIG2, HC_ECHO2);

  int rawX = readRawAvg(JOYSTICK_PIN_X);
  int rawY = readRawAvg(JOYSTICK_PIN_Y);

  char mess[256];
  sprintf(
          mess,
          "{\"dist1\": %d, \"dist2\": %d, \"raw_x\": %d, \"raw_y\": %d}",
          distance1, distance2,
          rawX, rawY
  );

  BTSerial.println(mess);
  Serial.println(mess);
  delay(500);
}