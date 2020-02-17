const int ger_count = 4;
const int ger_pins[ger_count] = {3,9,6,11};
int save_ger_no = -1;

void setup() {
  Serial.begin(9600);
}

void loop() {
   for (int ger_no = 0 ; ger_no < ger_count; ++ger_no)  {
     if (digitalRead(ger_pins[ger_no])) {
        if (save_ger_no != ger_no) {
          Serial.print("switch"); 
          Serial.println(ger_no); 
          save_ger_no = ger_no;
        }
     };
   }
   delay(100); 
}
