#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

#include "registers.h"
#include "driver.h"
#include "spi.h"
#include "wavWriter.h"
#include "ciricularBuffer.h"

#define LED_GPIO 23
#define DATA_READY 13
#define CONV_RUN 19
#define CS_PIN 6

#define CHANNEL_NUMBER (uint8_t) 4

static bool verifyRegister(uint8_t reg, uint16_t regValue);

ciricularBuff16_t samples;

MAX11043_STATUS MAX11043_init(uint8_t activeChannels, BitMode bitNumber, size_t sampleNr, uint16_t clkDivision){
	uint16_t configurationReg = 0x0;
	uint16_t channelReg = 0x0;
	uint8_t resultSize = bitNumber * CHANNEL_NUMBER;

	if(!(activeChannels & CHANNEL_A)){ configurationReg |= CHANNEL_A_POWER_DOWN; resultSize -= bitNumber; }
	if(!(activeChannels & CHANNEL_B)){ configurationReg |= CHANNEL_B_POWER_DOWN; resultSize -= bitNumber; }
	if(!(activeChannels & CHANNEL_C)){ configurationReg |= CHANNEL_C_POWER_DOWN; resultSize -= bitNumber; }
	if(!(activeChannels & CHANNEL_D)){ configurationReg |= CHANNEL_D_POWER_DOWN; resultSize -= bitNumber; }

	if(resultSize <= 0)
		return ERROR_NO_ACTIVE_CHANNEL;

	configurationReg |= clkDivision |
		               DAC_POWER_DOWN;

	MAX11043_reg_write(CONFIGURATION, configurationReg);

	if(!verifyRegister(CONFIGURATION, configurationReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;

	channelReg  = BIAS_VOLTAGE_50_AVDD |
				  PGA_POWERED_DOWN |
				  DIFF_NORMAL |
				  USE_LP_FILTER |
				  EQ_DISABLED |
				  ENABLE_POSITIVE_BIAS;

	MAX11043_reg_write(ADC_A_CONFIG, channelReg);

	if(!verifyRegister(ADC_A_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;

	MAX11043_reg_write(ADC_B_CONFIG, channelReg);

	if(!verifyRegister(ADC_B_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;;

	MAX11043_reg_write(ADC_C_CONFIG, channelReg);

	if(!verifyRegister(ADC_C_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;

	MAX11043_reg_write(ADC_D_CONFIG, channelReg);

	if(!verifyRegister(ADC_D_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;

	ciricularBuffer16_init(&samples, sampleNr);

	return STATUS_OK;
}

void MAX11043_on_sample(int GPIO, int level, uint32_t timestamp){
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
	uint16_t result = 0x0;

	spi_cs_low();
	///Wait for flash until ready
	while(MAX11043_isFlashBusy());
	///Write page and adress to FLASH_ADDRESS register
	 MAX11043_reg_write(FLASH_ADDRESS, page << 8 | address);
	///execute read content of FLASH at address (flash_address) to (data_out) register

	///Wait for flash until ready
	while(MAX11043_isFlashBusy());

	/// read data from (data_out) register


	spi_cs_high();
	return result;
}

bool MAX11043_isFlashBusy(){
	char flashModeValue = 0x1;
	char flashModeReg = FLASH_MODE_SELECT | MAX11043_READ;
	spi_xfer(&flashModeReg, &flashModeValue, 2);
	return flashModeValue & 0x1;
}

static bool verifyRegister(uint8_t reg, uint16_t regValue){
	uint16_t readReg = MAX11043_reg_read(reg);
	return readReg == regValue;
}

/*static void *dumpToFile(void *arg){
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
}*/


