#include <SoftwareSerial.h>
const int TXD_PIN = 12;
const int RXD_PIN = 13;

SoftwareSerial BTSerial(TXD_PIN, RXD_PIN); 

void setup() {
  BTSerial.begin(38400); // Связь с Bluetooth-модулем
  Serial.begin(9600);
  
}

void loop() {
  BTSerial.println("sent via Bluetooth  from arduino");
  Serial.println("test message");
  delay(1000); // Задержка 1000 мс (1 секунда)
}
