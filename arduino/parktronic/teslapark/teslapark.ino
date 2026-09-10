#define HC_ECHO1 2
#define HC_TRIG1 3
#define BUZZER 4
#define HC_ECHO2 5
#define HC_TRIG2 6
#define G3 1480
#define C4 1975
#define FAR_DISTANCE 1000

// сделаем функцию для удобства
float getDist(uint8_t trig, uint8_t echo) {
  // импульс 10 мкс
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  // измеряем время ответного импульса
  uint32_t us = pulseIn(echo, HIGH);
  if (us == 0) {
    return FAR_DISTANCE;
  }
  // считаем расстояние и возвращаем
  return us / 58.2;
}

void setup() {
  Serial.begin(115200);     // для связи
  pinMode(HC_TRIG1, OUTPUT); // trig выход
  pinMode(HC_ECHO1, INPUT);  // echo вход
  pinMode(HC_TRIG2, OUTPUT); // trig выход
  pinMode(HC_ECHO2, INPUT);  // echo вход
  pinMode(BUZZER, OUTPUT);
}

void loop() {
  float dist1 = getDist(HC_TRIG1, HC_ECHO1);
  float dist2 = getDist(HC_TRIG2, HC_ECHO2);
  float dist = min(dist1, dist2);
  float long_buze = 5;
  if (dist < 50 && dist > long_buze) { // Если препятствие ближе 50 см
    Serial.println("close");
    tone(BUZZER, G3);        // Издаем писк
    delay(50);                 // Короткий звук
    noTone(BUZZER);
    
    // Динамическая пауза: чем меньше расстояние, тем меньше задержка
    int pause = dist * 10;     
    delay(pause);
  } else if (dist <= long_buze) {// Слишком близко!
    Serial.println("too_close1");
    tone(BUZZER, C4);        // Непрерывный сигнал
  } else {
    Serial.println("no_buze");
    noTone(BUZZER);            // Тишина, если далеко
  }

  Serial.print("  dist 1 = ");
  Serial.print(dist1);
  Serial.print("  dist 2  = ");
  Serial.println(dist2);                     // выводим
  delay(50);
}
