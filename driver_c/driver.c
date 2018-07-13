#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <stdint.h>
#include "registers.h"
#include "driver.h"
#include "spi.h"
#include "wavWriter.h"
#include <pigpio.h>

#define LED_GPIO 23
#define DATA_READY 13
#define CONV_RUN 19
#define SAMPLE_LIMIT 1000000
#define CS_PIN 6

uint32_t sampleCount = 0;
uint16_t samples[SAMPLE_LIMIT];

int main(int argc, char *argv[]){
	char c = ' ';
	uint16_t reg = 0;

	hardware_init();
	spi_init(CS_PIN, DATA_READY, CONV_RUN);
	
	MAX11043_reg_write(CONFIGURATION,
			   CLK_DIV_1_TO_6 |
		 	   DAC_POWER_DOWN |
			   CHANNEL_B_POWER_DOWN |
			   CHANNEL_C_POWER_DOWN |
			   CHANNEL_D_POWER_DOWN);

	MAX11043_reg_write(ADC_A_CONFIG,
			   BIAS_VOLTAGE_50_AVDD |
			   PGA_POWERED_DOWN |
			   DIFF_NORMAL |
			   ENABLE_POSITIVE_BIAS |
			   USE_LP_FILTER |
			   EQ_DISABLED);
	
	reg = MAX11043_reg_read(CONFIGURATION);
	printf("Reg :%X\r\n", reg);
	reg = MAX11043_reg_read(ADC_A_CONFIG);
	printf("Reg :%X\r\n", reg);

	register_callback(MAX11043_on_sample);
	conv_run_high();
	while(c != 'q'){
		c = getchar();
	}

	spi_close();
	hardware_disable();

	return 0;
}

void *dumpToFile(void *arg){
	write_wav("out.wav", SAMPLE_LIMIT, (short int*)samples, 41666);
	FILE *pfile;
	pfile = fopen("out.txt", "w");
	if(!pfile){
		printf("File Error!");
		return NULL;
	}

	for(int i = 0; i < SAMPLE_LIMIT; i++){
		fprintf(pfile, "%u\r\n", samples[i]);
	}

	fclose(pfile);
	printf("Finished file write\r\n");
}

void MAX11043_on_sample(int GPIO, int level, uint32_t timestamp){
	char sampleBuff[2];
	uint16_t sample = 0;
	if(level == 1){
		return;
	}

	sample = MAX11043_reg_read(ADC_A_RESULT);//MAX11043_reg_read(ADC_B_RESULT);
	samples[sampleCount] = sample;
	sampleCount++;
	if(sampleCount > SAMPLE_LIMIT){
		remove_callback();
		conv_run_low();
		printf("DOOONE BABY\r\n");
		gpioStartThread(dumpToFile, (void*) samples);
	}
}

void MAX11043_reg_write(uint8_t reg, uint16_t data){
	char regAddr[3] = {reg | MAX11043_WRITE, data >> 8, data & 0xFF};
	spi_cs_low();
	spi_write((char*) &regAddr, 3);
	spi_cs_high();
}

uint16_t MAX11043_reg_read(uint8_t reg){
	char dataBuff[3] = {reg | MAX11043_READ,0,0};
	uint16_t result = 0;

	spi_cs_low();
	spi_xfer((char*) &dataBuff, (char*) &dataBuff, 3);
	spi_cs_high();
	//printf("Read: %X, %X %X\r\n ", dataBuff[0], dataBuff[1], dataBuff[2]);
	result = dataBuff[1] << 8 | dataBuff[2];
	return result;
}

uint16_t MAX11043_scan_read(){
	char dataBuff[2] = {0, 0};
	uint16_t result = 0;
	spi_cs_low();
	spi_read((char*) &dataBuff, 2);
	spi_cs_high();
	result = dataBuff[0] << 8 | dataBuff[1];
	return result;
}

void MAX11043_flash_write(uint8_t page, uint8_t address, uint16_t data){

}

uint16_t MAX11043_flash_read(uint8_t page, uint8_t address){

}

