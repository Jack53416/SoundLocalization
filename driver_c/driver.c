#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>

#include "registers.h"
#include "driver.h"
#include "hardware.h"
#include "roundBuffer.h"

#define LED_GPIO 23
#define DATA_READY 13
#define CONV_RUN 19
#define CS_PIN 6

static bool verifyRegister(uint8_t reg, uint16_t regValue);
static uint8_t getActiveChannelNum(uint8_t channelFlag);

volatile roundBuff samples;
volatile uint64_t counter = 0;

MAX11043_STATUS MAX11043_init(uint8_t activeChannels, BitMode bitNumber, size_t sampleNr, uint16_t clkDivision){
	uint16_t configurationReg = 0x0;
	uint16_t channelReg = 0x0;
	uint8_t resultSize = getActiveChannelNum(activeChannels) * sizeof(uint16_t);

  configurationReg |= (activeChannels & CHANNEL_A) ? SCAN_A_CHANNEL : CHANNEL_A_POWER_DOWN;
  configurationReg |= (activeChannels & CHANNEL_B) ? SCAN_B_CHANNEL : CHANNEL_B_POWER_DOWN;
  configurationReg |= (activeChannels & CHANNEL_C) ? SCAN_C_CHANNEL : CHANNEL_C_POWER_DOWN;
  configurationReg |= (activeChannels & CHANNEL_D) ? SCAN_D_CHANNEL : CHANNEL_D_POWER_DOWN;
  
	configurationReg |= clkDivision |
		               DAC_POWER_DOWN;

	channelReg  = BIAS_VOLTAGE_33_AVDD |
				  PGA_POWERED_DOWN |
				  DIFF_NORMAL |
				  USE_LP_FILTER |
				  EQ_DISABLED; //|
				  //ENABLE_NEGATIVE_BIAS;// |
				  //ENABLE_POSITIVE_BIAS;

	MAX11043_reg_write(ADC_A_CONFIG, channelReg);

	/*if(!verifyRegister(ADC_A_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;*/

	MAX11043_reg_write(ADC_B_CONFIG, channelReg);

	/*if(!verifyRegister(ADC_B_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;*/

	MAX11043_reg_write(ADC_C_CONFIG, channelReg);

	/*if(!verifyRegister(ADC_C_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;*/

	MAX11043_reg_write(ADC_D_CONFIG, channelReg);

	/*if(!verifyRegister(ADC_D_CONFIG, channelReg))
		return ERROR_UNSUCCESSFULL_REGWRITE;*/
  
  MAX11043_reg_write(CONFIGURATION, configurationReg);
  
	if(roundBuff_init(&samples, sampleNr, resultSize) != BUFFER_OK)
    return ERROR_INVALID_BUFFER_STATE;
    
  register_callback(MAX11043_on_sample);

	return STATUS_OK;
}

inline void MAX11043_on_sample(){
  /*uint16_t sample = MAX11043_scan_read();
  roundBuff_put(&samples, &sample);
*/spi_cs_low();
  spi_read_back((char*) samples.buffer + samples.head * samples.elementSize, samples.elementSize);
  spi_cs_high();
  roudBuff_incrHead(&samples);
  counter++;
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
	result = dataBuff[1] << 8 | dataBuff[2];
	return result;
}

inline uint16_t MAX11043_scan_read(){
	char dataBuff[2] = {0, 0};
	uint16_t result;
	spi_cs_low();
	spi_read((char*) &dataBuff, 2);
	spi_cs_high();
  result = dataBuff[0] << 8 | dataBuff[1];
  /*
	result.ch1 = dataBuff[0] << 8 | dataBuff[1]; 
	result.ch2 = dataBuff[2] << 8 | dataBuff[3];
  result.ch3 = dataBuff[4] << 8 | dataBuff[5];*/
  //result.ch4 = dataBuff[6] << 8 | dataBuff[7];
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

void MAX11043_read_samples(size_t sampleNr){
  conv_run_high();
  while(counter < sampleNr);
  conv_run_low();
  counter = 0;
}

void MAX11043_read_samples_cont(){
  conv_run_high();  
}

void MAX11043_stop_reading_samples(){
  conv_run_low();  
}

void MAX11043_stop_interrupt(){
  remove_callback();
}

void MAX11043_attach_interrupt(){
  register_callback(MAX11043_on_sample);
}

static bool verifyRegister(uint8_t reg, uint16_t regValue){
	uint16_t readReg = MAX11043_reg_read(reg);
	return readReg == regValue;
}

static uint8_t getActiveChannelNum(uint8_t channelFlag){
    uint8_t count = 0;
    while(channelFlag > 0){
        count += 1;
        channelFlag = channelFlag & (channelFlag-1);
    }
    return count;
}

