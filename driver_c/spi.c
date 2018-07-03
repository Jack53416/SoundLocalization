#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <pigpio.h>

#include "spi.h"

int spiHandle = -1;
uint8_t csPin = 0;
uint8_t dataReadyPin = 0;
uint8_t convRunPin = 0;

int hardware_init(){
	gpioCfgClock(1, 1, 0);
	return gpioInitialise();		
}

int spi_init(uint8_t cs, uint8_t dataReady, uint8_t convRun){
	csPin = cs;
	dataReadyPin = dataReady;
	convRunPin = convRun;
	gpioSetMode(dataReadyPin, PI_INPUT);
	gpioSetMode(convRunPin, PI_OUTPUT);
	gpioSetMode(csPin, PI_OUTPUT);
	
	spiHandle = spiOpen(0, 6000000, 0);
	return spiHandle;
}

void spi_close(){
	spiClose(spiHandle);
}

void hardware_disable(){
	gpioTerminate();
}

void spi_write(char *data, size_t byteCount){
	spiWrite(spiHandle, data, byteCount);
}

void spi_read(char *buffer, size_t byteCount){
	spiRead(spiHandle, buffer, byteCount);
}

void spi_xfer(char *txData, char *rxData, size_t byteCount){
	spiXfer(spiHandle, txData, rxData, byteCount);
}

void spi_cs_low(){
	gpioWrite(csPin, 0);
}

void spi_cs_high(){
	gpioWrite(csPin, 1);
}

