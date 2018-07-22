#include "driver.h"
#include "registers.h"
#include "hardware.h"
#include <SPI.h>
#include "roundBuffer.h"
//IntervalTimer blinkTimer;

uint8_t testBuff[2048 * 8];
uint32_t buffSize = 0;

extern volatile roundBuff samples;
extern volatile uint32_t counter;

void setup() {
  MAX11043_STATUS adcStatus = STATUS_OK;
  SPI.begin();
  Serial.begin(2000000);
  spi_init(2,3,4);  
  adcStatus = MAX11043_init(CHANNEL_A | CHANNEL_B | CHANNEL_D, BITS_16, 2048, CLK_DIV_1_TO_6);
  if(adcStatus != STATUS_OK){
    pinMode(13, OUTPUT);
    signalizeError(adcStatus);
  }
  MAX11043_read_samples_cont();
}

void loop() {
  uint32_t ctr = 0;
  sample3_ch sample;
  delay(20);
  
  MAX11043_stop_interrupt();
  ctr = counter;
  counter = 0;
  MAX11043_attach_interrupt();
  buffSize = roundBuff_getMany(&samples, testBuff, ctr);
  /*if(Serial.dtr()){
    sample = ((sample3_ch*)testBuff)[5];
    Serial.print(sample.ch1); Serial.print("|");
    Serial.print(sample.ch2); Serial.print("|");
    Serial.print(sample.ch3); Serial.print("\r\n");
    //Serial.print(sample.ch4); Serial.print("\r\n");
  }*/
  if(Serial.dtr()){
    Serial.write(testBuff,buffSize * samples.elementSize);
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
    delay(500);
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

