===

https://wiki.iarduino.ru/page/trema-modul-bluetooth-hc-05/
Trema-модуль v 2.0 
Bluetooth  HC-05
TX -> Arduino RX наоборот
RX  ->  Arduino TX наоборот
GND
VCC
KEY
Питаетс от 3 до 5 (но кажется, Сама Piranha uno работает от 5 v)

===
Сама Piranha uno работает на 5 v R3
Разъем ICSP Для программирования

==
Нужна батарейка на 5 в и научиться подключать 
==
Пробую урок 2
http://edurobots.ru/2014/03/arduino-knopka/
Скачала arduino ide 
У меня Arduino на com5
черный резистор - на 10 кОм

В данном случае, когда кнопка отключена, пин будет подключен к земле через резистор, 
сопротивление которого заведомо меньше внутреннего сопротивления пина.


===
Bluetooth
это разные оппозиции
master - slave  (кажется у нас Android - это slave)
===
1. Забрать кода с github (включая код ардуино)
2.  добиться, что все работает на python
3. найти код для андроид
==
Соединить все репозитории в один, удалить старые.


===
1. Пробую испоьзовать библиотеку iarduino_Bluetooth_HC05.h
https://iarduino.ru/file/301.html
2. по инструкции
https://wiki.iarduino.ru/page/Installing_libraries/
3. Все библиотеки подключаются через меню Arduino IDE!!
iarduino_Bluetooth_HC05.h - падает при  конструкторо
iarduino_Bluetooth_HC05 hc05(4);


подключаю вывод Key от HC-05 к 4 порту
==
У меня rxpin и txpin Отличается от тех, что обычно дают в примерах (2,3), у меня аппаратные 0 и 1
const int rxpin = 0;
const int txpin = 1;


==
Upload иногда падает просто так
