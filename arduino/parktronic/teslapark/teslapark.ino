#define HC_ECHO1 2
#define HC_TRIG1 3
const int BUZZER_PIN = 4;
#define HC_ECHO2 5
#define HC_TRIG2 6
const int MOTOR_BUZZER_PIN = 7;

#define G3 1480
#define C4 1975
#define FAR_DISTANCE 1000
const int JOYSTICK_PIN_X = A0; // ось X джойстика
const int JOYSTICK_PIN_Y = A1; //ось Y джойстика
unsigned long lastParktronicTime = 0;
unsigned long lastStrokeTime = 0;



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
  pinMode(BUZZER_PIN, OUTPUT);
}



void parktronic() {
  unsigned long tim = millis();
  if (tim - lastParktronicTime < 50) {
    return;
  }
  lastParktronicTime = tim;
  
  float dist1 = getDist(HC_TRIG1, HC_ECHO1);
  float dist2 = getDist(HC_TRIG2, HC_ECHO2);
  float dist = min(dist1, dist2);
  float long_buze = 5;
  if (dist < 50 && dist > long_buze) { // Если препятствие ближе 50 см
    Serial.println("close");
    tone(BUZZER_PIN, G3, 50);        // Издаем писк
    //noTone(BUZZER);
    
    // Динамическая пауза: чем меньше расстояние, тем меньше задержка
    int pause = dist * 10;     
    delay(pause);
  } else if (dist <= long_buze) {// Слишком близко!
    Serial.println("too_close1");
    tone(BUZZER_PIN, C4);        // Непрерывный сигнал
  } else {
    Serial.println("no_buze");
    noTone(BUZZER_PIN);            // Тишина, если далеко
  }

  Serial.print("  dist 1 = ");
  Serial.print(dist1);
  Serial.print("  dist 2  = ");
  Serial.println(dist2);                     // выводим
}

int getAxisSpeed(int pin) {
  int val = analogRead(pin);
  // 2. Находим отклонение от центра (нейтраль ~ 512)
  // dev = 0 (покой), dev = 512 (максимальный газ)
  int dev = abs(val - 512); 
  
  // Игнорируем неболшую «мертвую зону» около центра
  if (dev < 30) {
    dev = 0;
  }
  return dev;
}

void playMotorSound() {
  // 1. Считываем значение с потенциометра (0..1023)
  int val1 = getAxisSpeed(JOYSTICK_PIN_X);
  int val2 = getAxisSpeed(JOYSTICK_PIN_Y);
  int dev = max(val1, val2);
  
  // 3. Рассчитываем параметры звука ДВС на основе "газа" (dev):
  // Пауза между «взрывами»: от 130 мс (медленный холостой ход) до 20 мс (высокие обороты)
  int strokeInterval = map(dev, 0, 512, 130, 20);
  
  // Высота тона «взрыва»: от 60 Гц (бас) до 160 Гц (рычание)
  int strokeTone = map(dev, 0, 512, 40, 120);
  
  // Длительность одного «взрыва»
  int strokeDuration = map(dev, 0, 512, 12, 6);

  // 4. Неблокирующая генерация тактов ДВС через millis()
  unsigned long currentTime = millis();
  if (currentTime - lastStrokeTime >= strokeInterval) {
    lastStrokeTime = currentTime;
    
    // Издаем один «взрыв»
    tone(MOTOR_BUZZER_PIN, strokeTone, strokeDuration);
  }
}



void loop() {
  playMotorSound();
  parktronic();
}
