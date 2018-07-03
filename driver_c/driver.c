#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <stdint.h>
#include "registers.h"
#include "driver.h"
#include "spi.h"

#define LED_GPIO 23
#define DATA_READY 13
#define CONV_RUN 19
#define SAMPLE_LIMIT 40000
#define CS_PIN 6

uint32_t sampleCount = 0;
uint16_t samples[SAMPLE_LIMIT];

int main(int argc, char *argv[]){
	char c = ' ';
	uint16_t reg = 0;

	hardware_init();
	spi_init(CS_PIN, DATA_READY, CONV_RUN);
	
	reg = MAX11043_reg_read(CONFIGURATION);
	printf("Reg :%X\r\n", reg);
	
	while(c != 'q'){
		c = getchar();
	}

	spi_close();
	hardware_disable();

	return 0;
}

void MAX11043_reg_write(uint8_t reg, uint16_t data){
	char dataBuff[2] = {data >> 8, data & 0xFF};
	char regAddr = reg | MAX11043_WRITE;

	printf("%X, %X\r\n", dataBuff[0], dataBuff[1]);	
	spi_cs_low();
	spi_write((char*) &regAddr, 1);
	spi_write((char*) &dataBuff, 2);
	spi_cs_high();
}

uint16_t MAX11043_reg_read(uint8_t reg){
	char dataBuff[2] = {0,0};
	char regAddr = reg | MAX11043_READ;
	uint16_t result = 0;

	spi_cs_low();
	spi_write((char*) &regAddr, 1);
	spi_read((char*) &dataBuff, 2);
	spi_cs_high();
	result = dataBuff[0] << 8 | dataBuff[1];
	return result;
}

void MAX11043_flash_write(uint8_t page, uint8_t address, uint16_t data){

}

uint16_t MAX11043_flash_read(uint8_t page, uint8_t address){

}

