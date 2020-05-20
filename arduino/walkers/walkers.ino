#include <SoftwareSerial.h>

//const int rxpin = 2;.
//const int txpin = 3;
const int rxpin = 0;
const int txpin = 1;

SoftwareSerial          softSerial(rxpin,txpin);                                        // Создаём объект softSerial указывая выводы RX, TX (можно указывать любые выводы Arduino UNO). Вывод 2 Arduino подключается к выводу TX модуля, вывод 3 Arduino подключается к выводу RX модуля

#include <iarduino_Bluetooth_HC05.h>                                            // Подключаем библиотеку iarduino_Bluetooth_HC05 для работы с Trema Bluetooth модулем HC-05

iarduino_Bluetooth_HC05 hc05(4);                            // Создаём объект hc05 указывая любой вывод Arduino, который подключается к выводу K модуля


const int reed_switch_count = 2;
const int reed_switches[reed_switch_count] = {2, 8};
int save_reed_switch = -1;

                                              

void setup() {
  Serial.begin(9600);
  
  if( hc05.begin(softSerial) ) {
      Serial.println("Ok"); 
  }             
  else {
      Serial.println("Error"); 
  }          

  Serial.print  ("create slave: ");  
  if( hc05.createSlave("MyName","4567") ) {
    Serial.println("Ok");
  } else {
    Serial.println("Error");
  }
}

int get_switch() {
  for (int i = 0; i < reed_switch_count; ++i)  {
     if (digitalRead(reed_switches[i]) == HIGH) {
        return  i;
     }
  }
  return -1;
}

void loop() {
  int found_reed_switch = get_switch();
  if (found_reed_switch != save_reed_switch){
    Serial.print("switch"); 
    Serial.println(found_reed_switch); 
    save_reed_switch = found_reed_switch;
  }
  delay(100); 
}
