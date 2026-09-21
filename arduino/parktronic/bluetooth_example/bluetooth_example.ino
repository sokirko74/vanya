#include <SoftwareSerial.h>

// Создаем программный последовательный порт
// RX Arduino = 10 (сюда идет TX модуля)
// TX Arduino = 11 (отсюда идет на RX модуля)
SoftwareSerial BTSerial(10, 11); 

void setup() {
  Serial.begin(9600);   // Связь Arduino с компьютером
  BTSerial.begin(9600); // Связь Arduino с Bluetooth (9600 - стандартная скорость)
  
  Serial.println("Bluetooth готов к работе!");
}

void loop() {
  // Если пришли данные от Bluetooth -> отправляем в компьютер
  if (BTSerial.available()) {
    Serial.write(BTSerial.read());
  }
  
  // Если мы пишем что-то в компьютере -> отправляем по Bluetooth
  if (Serial.available()) {
    BTSerial.write(Serial.read());
  }
}
