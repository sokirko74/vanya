#include <SoftwareSerial.h>


const int HC_ECHO1 = 2; // parktronic1
const int HC_TRIG1 = 3;

const int HC_ECHO2 = 4; // parktronic2
const int HC_TRIG2 = 5;

const int TXD_PIN = 12; // bluetooth tx
const int RXD_PIN = 13; // bluetooth rx

const int JOYSTICK_PIN_X = A0; // ось X джойстика
const int JOYSTICK_PIN_Y = A1; //ось Y джойстика



SoftwareSerial BTSerial(TXD_PIN, RXD_PIN); 


void printfSerial(const char *fmt, ...) {
  char buf[128]; // Размер буфера под вашу строку
  va_list args;
  va_start(args, fmt);
  vsnprintf(buf, sizeof(buf), fmt, args);
  va_end(args);
  Serial.print(buf);
}

// сделаем функцию для удобства
float getDist(uint8_t trig, uint8_t echo) {
  // импульс 10 мкс
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
 

  // измеряем время ответного импульса
  int us = pulseIn(echo, HIGH, 15000);
  if (us == 0) {
    return -1;
  }
  // считаем расстояние и возвращаем
  return (int)(us / 58.2);
}

void setup() {
  printfSerial("start setup");
  Serial.begin(9600);     // для связи
  pinMode(HC_TRIG1, OUTPUT); // trig выход
  pinMode(HC_ECHO1, INPUT);  // echo вход
  pinMode(HC_TRIG2, OUTPUT); // trig выход
  pinMode(HC_ECHO2, INPUT);  // echo вход
  BTSerial.begin(38400); // Связь с Bluetooth-модулем
}

int readAnalogWithThreshold(int pin) {
    int r = analogRead(pin);
    if (r < 200) {
      return 0;
    }
    return r;
}

int getAxisSpeed(int pin) {
  int r1 = readAnalogWithThreshold(pin);
  int r2 = readAnalogWithThreshold(pin);
  int r3 = readAnalogWithThreshold(pin);
  int val = (r1 + r2 + r3) / 3;
  //printfSerial("pin=%i r1=%i r2=%i r3=%i\n", pin, r1, r2, r3);
  if (val == 0) {
    return -1;
  }
  // 2. Находим отклонение от центра (нейтраль ~ 512)
  // dev = 0 (покой), dev = 512 (максимальный газ)
  int dev = abs(val - 512); 
  
  // Игнорируем небольшую «мертвую зону» около центра
  if (dev < 30) {
    dev = 0;
  }
  return dev;
}


void loop() {
  int distance1 = getDist(HC_TRIG1, HC_ECHO1);
  int distance2 = getDist(HC_TRIG2, HC_ECHO2);
  int speed1  = getAxisSpeed(JOYSTICK_PIN_X);
  int speed2 = getAxisSpeed(JOYSTICK_PIN_Y);
  //speed1 = -1;
  
  char mess[1024];
  sprintf(mess, "{\"dist1\": %i, \"dist2\": %i, \"speed1\": %i, \"speed2\": %i}",
   distance1, distance2, speed1, speed2);
  BTSerial.println(mess);
  Serial.println(mess);
  delay(500);
}
