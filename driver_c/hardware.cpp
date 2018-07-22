#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "hardware.h"

#include <SPI.h>

int spiHandle = -1;
uint8_t csPin = 0;
uint8_t dataReadyPin = 0;
uint8_t convRunPin = 0;

int hardware_init(){
	return 0;
}

int spi_init(uint8_t cs, uint8_t dataReady, uint8_t convRun){
	csPin = cs;
	dataReadyPin = dataReady;
	convRunPin = convRun;
	///TO DO SPI platform init and GPIO init
  pinMode(dataReady, INPUT);
  pinMode(convRunPin, OUTPUT);
  pinMode(csPin, OUTPUT);
  //SPI.setClockDivider(SPI_CLOCK_DIV2);
  SPI.beginTransaction(SPISettings(40000000, MSBFIRST, SPI_MODE0));
  spiHandle = 0;
	return spiHandle;
}

void spi_close(){
}

void hardware_disable(){
}

void spi_write(char *data, size_t byteCount){
  SPI.transfer(data, byteCount);
}

void spi_read(char *buffer, size_t byteCount){
  for(unsigned int i = 0; i < byteCount; i++){
      buffer[i] = SPI.transfer(0x00);
    }
}

void spi_read_back(char *buffer, size_t byteCount){
  for(int i = byteCount - 1; i >= 0; i--){
    buffer[i] = SPI.transfer(0x00); 
  }  
}

void spi_xfer(char *txData, char *rxData, size_t byteCount){
  for(unsigned int i = 0; i < byteCount; i++){
      rxData[i] = SPI.transfer(txData[i]);
    }
}

void spi_cs_low(){
  digitalWrite(csPin, LOW);
}

void spi_cs_high(){
  digitalWrite(csPin, HIGH);
}

void conv_run_high(){
  digitalWrite(convRunPin, HIGH);
}

void conv_run_low(){
  digitalWrite(convRunPin, LOW);
}

void register_callback(void (*cb)()){
  attachInterrupt(digitalPinToInterrupt(dataReadyPin), cb, FALLING);
}

void remove_callback(){
  detachInterrupt(digitalPinToInterrupt(dataReadyPin));
}

