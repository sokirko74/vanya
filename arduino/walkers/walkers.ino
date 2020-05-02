const int reed_switch_count = 2;
const int reed_switches[reed_switch_count] = {2, 8};
int save_reed_switch = -1;

void setup() {
  Serial.begin(9600);
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
