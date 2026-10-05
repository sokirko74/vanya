#include <SoftwareSerial.h>

const int HC_ECHO1 = 2; // parktronic1
const int HC_TRIG1 = 3;

const int HC_ECHO2 = 4; // parktronic2
const int HC_TRIG2 = 5;

const int TXD_PIN = 12; // bluetooth tx
const int RXD_PIN = 13; // bluetooth rx

const int JOYSTICK_PIN_X = A0; // ось X джойстика
const int JOYSTICK_PIN_Y = A1; // ось Y джойстика

struct SpeedStruct {
    int r1;
    int r2;
    int r3;
    int dev;
};

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

int readAnalogWithThreshold(int pin) {
  int r = analogRead(pin);
  if (r < 200) {
    return 0;
  }
  return r;
}

void getAxisSpeed(int pin, SpeedStruct &s) {
  s.r1 = readAnalogWithThreshold(pin);
  s.r2 = readAnalogWithThreshold(pin);
  s.r3 = readAnalogWithThreshold(pin);
  int val = (s.r1 + s.r2 + s.r3) / 3;

  if (val == 0) {
    s.dev = -1;
    return;
  }

  s.dev = abs(val - 512);

  if (s.dev < 30) {
    s.dev = 0;
  }
}

void loop() {
  int distance1 = getDist(HC_TRIG1, HC_ECHO1);
  int distance2 = getDist(HC_TRIG2, HC_ECHO2);

  SpeedStruct s1;
  getAxisSpeed(JOYSTICK_PIN_X, s1);

  SpeedStruct s2;
  getAxisSpeed(JOYSTICK_PIN_Y, s2);

  char mess[256];
  sprintf(
          mess,
          "{\"dist1\": %d, \"dist2\": %d, \"speed1\": %d, \"speed2\": %d, \"debug_speed\": \"%d %d %d; %d %d %d\"}",
          distance1, distance2,
          s1.dev, s2.dev,
          s1.r1, s1.r2, s1.r3,
          s2.r1, s2.r2, s2.r3
  );

  BTSerial.println(mess);
  Serial.println(mess);
  delay(500);
}
