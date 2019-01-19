#include "driver.h"
#include "registers.h"
#include "hardware.h"
#include <SPI.h>

IntervalTimer statusTimer;

int counter = 0;

void setup() {
  MAX11043_STATUS adcStatus = STATUS_OK;
  SPI.begin();
  Serial.begin(2000000);
  spi_init(2,3,4);
  adcStatus = MAX11043_init(CHANNEL_A | CHANNEL_B | CHANNEL_C | CHANNEL_D, 2048, CLK_DIV_1_TO_6);
  if(adcStatus != STATUS_OK){
    pinMode(13, OUTPUT);
    signalizeError(adcStatus);
  }
  statusTimer.begin(serialStatus, 500000);
}

void loop() {
  #define SAMPLE_SIZE 4 * sizeof(int16_t)
  
  byte buff[SAMPLE_SIZE];
  bool dataReady = false;
  int16_t channelData = -1;
  
  if(digitalRead(3) == LOW && !dataReady){
      spi_cs_low();
      spi_read_back((char*)buff, SAMPLE_SIZE);
      spi_cs_high();
      dataReady = true;
  }

  if(Serial.dtr() && dataReady){
      channelData = buff[0] << 8 | buff[1];
      Serial.write(buff, SAMPLE_SIZE);
      dataReady = false;
    }
}

void timeThis(void (*f)(void), const char* test_name, unsigned int times) {
   unsigned long duration;
   float total;

   total = 0;
   duration = 0;
   for (unsigned int i = 0; i < times; i++) {
       duration = micros();
       f();
       duration = micros() - duration;
       total += duration;
   }
   
   if (times > 1) {
       total /= (float)times;
   }
   
   Serial.println("");
   Serial.print(test_name);
   Serial.print('(');
   Serial.print(times);
   Serial.print("): ");
   Serial.print(total);
   Serial.println("us");
}

void signalizeError(MAX11043_STATUS errorCode){
  while(true){
    Serial.print("ERROR: ");
    Serial.print(errorCode);
    Serial.print("\r\n");
    blinkDiode();
    delay(2000);
  }  
}

void blinkDiode(){
  static bool diodeState = false;
  if(diodeState)
    digitalWrite(13, LOW);
  else
    digitalWrite(13, HIGH);
  diodeState = !diodeState;
}

void serialStatus(){
  static bool isConverting = false;
  bool serialStatus = !Serial.rts() && Serial.dtr();
  
  if(serialStatus && !isConverting){
      MAX11043_read_samples_cont();
      isConverting = true;
  }
  else if(!serialStatus && isConverting){
      MAX11043_stop_reading_samples();
      isConverting = false;
  }  
 }

