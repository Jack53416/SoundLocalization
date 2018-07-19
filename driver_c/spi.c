#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include "spi.h"

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

	return spiHandle;
}

void spi_close(){
}

void hardware_disable(){
}

void spi_write(char *data, size_t byteCount){

}

void spi_read(char *buffer, size_t byteCount){
}

void spi_xfer(char *txData, char *rxData, size_t byteCount){
}

void spi_cs_low(){
}

void spi_cs_high(){
}

void conv_run_high(){
}

void conv_run_low(){
}

void register_callback(void (*cb)(int, int, uint32_t)){
}

void remove_callback(){
}
