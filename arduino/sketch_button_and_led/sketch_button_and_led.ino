int button = 2;
int led = 8;

void setup() {
  pinMode(led, OUTPUT);
  pinMode(button, INPUT);
  Serial.begin(9600);
}

void loop() {
  if (digitalRead(button) == HIGH) {
    Serial.println("switch is on");
    digitalWrite(led, HIGH);
  }
  else {
    Serial.println("switch is off");
    digitalWrite(led, LOW);
  }
}
