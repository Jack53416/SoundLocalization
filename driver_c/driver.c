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

static const int16_t transferCoefficient = 1 << 13; //2^13

static bool verifyRegister(const uint8_t reg, const uint16_t regValue);
static uint8_t getActiveChannelNum(uint8_t channelFlag);
static uint8_t getRegisterSize(const uint8_t reg);\
//helpers for filter coefficients
static int16_t encodeDecimal(float value);
static float decodeDecimal(int16_t value);

MAX11043_STATUS MAX11043_init(uint8_t activeChannels, size_t sampleNr, uint16_t clkDivision){
    uint16_t configurationReg = 0x0;
    uint16_t channelReg = 0x0;
    bool correctlyWritten = true;
    uint8_t resultSize = getActiveChannelNum(activeChannels) * sizeof(uint16_t);

    configurationReg |= (activeChannels & CHANNEL_A) ? SCAN_A_CHANNEL : CHANNEL_A_POWER_DOWN;
    configurationReg |= (activeChannels & CHANNEL_B) ? SCAN_B_CHANNEL : CHANNEL_B_POWER_DOWN;
    configurationReg |= (activeChannels & CHANNEL_C) ? SCAN_C_CHANNEL : CHANNEL_C_POWER_DOWN;
    configurationReg |= (activeChannels & CHANNEL_D) ? SCAN_D_CHANNEL : CHANNEL_D_POWER_DOWN;

	configurationReg |= clkDivision | DAC_POWER_DOWN;

	channelReg  = BIAS_VOLTAGE_33_AVDD |
				  PGA_POWERED_DOWN |
				  DIFF_NORMAL |
				  USE_LP_FILTER |
				  EQ_DISABLED;

    MAX11043_reg_write(ADC_A_CONFIG, channelReg, true);
    MAX11043_reg_write(ADC_B_CONFIG, channelReg, true);
    MAX11043_reg_write(ADC_C_CONFIG, channelReg, true);
    MAX11043_reg_write(ADC_D_CONFIG, channelReg, true);
  
    correctlyWritten = (verifyRegister(ADC_A_CONFIG, channelReg) &&
                        verifyRegister(ADC_B_CONFIG, channelReg) &&
                        verifyRegister(ADC_C_CONFIG, channelReg) &&
                        verifyRegister(ADC_D_CONFIG, channelReg));
    
    MAX11043_reg_write(CONFIGURATION, configurationReg, true); // Turning on Scan mode, results in invalid register reads
    
    if(!correctlyWritten)
      return ERROR_UNSUCCESSFULL_REGWRITE;
    return STATUS_OK;
}

void MAX11043_on_sample(){
  /*uint16_t sample = MAX11043_scan_read();
  roundBuff_put(&samples, &sample);
*/
  /*spi_cs_low();
  spi_read_back((char*) samples.buffer + samples.head * samples.elementSize, samples.elementSize);
  spi_cs_high();
  roudBuff_incrHead(&samples);
  counter++;*/
}

void MAX11043_reg_write(const uint8_t reg, const uint32_t data, bool toggleCS){
  uint8_t regSize = getRegisterSize(reg);
  unsigned char regAddr[5] = {reg | MAX11043_WRITE, 0, 0, 0, 0};
  for(int i = 1, shift = (regSize - 1) * 8; i <= regSize; i++, shift -= 8){
    regAddr[i] = (data >> shift) & 0xFF;
  }
    
	spi_cs_low();
	spi_write((char*) &regAddr, regSize + 1);
	spi_cs_high();
}

uint32_t MAX11043_reg_read(const uint8_t reg, bool toggleCS){
	char dataBuff[5] = {reg | MAX11043_READ,0,0,0,0};
  uint8_t regSize = getRegisterSize(reg);
	uint32_t result = 0;

  if(toggleCS)
	  spi_cs_low();
	spi_xfer((char*) &dataBuff, (char*) &dataBuff, regSize + 1);
	if(toggleCS)
	  spi_cs_high();
  for(int i = 1, shift = (regSize - 1) * 8; i <= regSize; i++, shift -= 8){
      result |= (dataBuff[i] << shift);
  }
	return result;
}

inline uint16_t MAX11043_scan_read(){
	char dataBuff[2] = {0, 0};
	uint16_t result;
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
	 MAX11043_reg_write(FLASH_ADDRESS, (page << 8) | address, false);
	///execute read content of FLASH at address (flash_address) to (data_out) register
   MAX11043_reg_write(FLASH_MODE_SELECT, 0xA0, false); //read data from flash to data_out register
	///Wait for flash until ready
	while(MAX11043_isFlashBusy());
	/// read data from (data_out) register
  result = MAX11043_reg_read(FLASH_DATA_OUT, false);

	spi_cs_high();
	return result;
}

bool MAX11043_isFlashBusy(){
  int16_t statusRegister = MAX11043_reg_read(STATUS, true);
  statusRegister = statusRegister >> 5;
  return (statusRegister & 0x01) == 0x01;
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

static bool verifyRegister(const uint8_t reg, const uint16_t regValue){
	uint16_t readReg = MAX11043_reg_read(reg, true);
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

static uint8_t getRegisterSize(const uint8_t reg){
    const uint8_t defaultRegSize = sizeof(uint16_t); // bytes
    switch(reg){
        case ADC_A_RESULT:
        case ADC_B_RESULT:
        case ADC_C_RESULT:
        case ADC_D_RESULT:
            return defaultRegSize; // special case if ever to be used with 24 bits

        case ADC_A_AND_B_RESULT:
        case ADC_C_AND_D_RESULT:
            return defaultRegSize * 2; //special case if ever to be used with 24 bits

        case ADC_ABCD_RESULT:
            return defaultRegSize * 4; //special case if ever to be used with 24 bits

        case STATUS:
        case FILTER_COEFFICIENTS_ADDRESS:
        case FLASH_MODE_SELECT:
            return sizeof(uint8_t);

        case CRAM_DATA_OUT:
        case FILTER_COEFFICIENT_IN:
            return sizeof(uint32_t);

        default:
            return defaultRegSize;

    }
}

static int16_t encodeDecimal(float value){
  return (int16_t) (value * transferCoefficient);
}

static float decodeDecimal(int16_t decimalValue){
  return decimalValue / (float)transferCoefficient;
}
