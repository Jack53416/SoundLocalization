#ifndef DRIVER
#define DRIVER

enum {
	CHANNEL_A = 0x1,
	CHANNEL_B = 0x1 << 1,
	CHANNEL_C = 0x1 << 2,
	CHANNEL_D = 0x1 << 3
}Channels;

typedef enum {
	BITS_16 = 16,
	BITS_24 = 24
}BitMode;

typedef enum {
	STATUS_OK,
	ERROR_NO_ACTIVE_CHANNEL,
	ERROR_UNSUCCESSFULL_REGWRITE
}MAX11043_STATUS;

MAX11043_STATUS MAX11043_init(uint8_t activeChannels, BitMode bitNumber, size_t sampleNr, uint16_t clkDivision);

void MAX11043_reg_write(uint8_t reg, uint16_t data);
uint16_t MAX11043_reg_read(uint8_t reg);
void MAX11043_flash_write(uint8_t page, uint8_t address, uint16_t data);
uint16_t MAX11043_flash_read(uint8_t page, uint8_t address);
uint16_t MAX11043_scan_read();
bool MAX11043_isFlashBusy();

void MAX11043_on_sample(int GPIO, int level, uint32_t timestamp);

/**
 * Debug functions, not meant to use outside library
 * */
//static void *dumpToFile(void *arg);

#endif
