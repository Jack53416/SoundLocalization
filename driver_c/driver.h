#ifndef DRIVER_H
#define DRIVER_H
#ifdef __cplusplus
extern "C" {
#endif

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
	ERROR_UNSUCCESSFULL_REGWRITE,
  ERROR_INVALID_BUFFER_STATE
}MAX11043_STATUS;

typedef struct {
  uint16_t ch1;
  uint16_t ch2;
}sample2_ch;

typedef struct {
  uint16_t ch1;
  uint16_t ch2;
  uint16_t ch3;
}sample3_ch;

typedef struct {
  uint16_t ch1;
  uint16_t ch2;
  uint16_t ch3;
  uint16_t ch4;
}sample4_ch;


MAX11043_STATUS MAX11043_init(uint8_t activeChannels, size_t sampleNr, uint16_t clkDivision);

void MAX11043_reg_write(const uint8_t reg, const uint32_t data, bool toggleCS);
uint32_t MAX11043_reg_read(const uint8_t reg, bool toggleCS);
void MAX11043_flash_write(uint8_t page, uint8_t address, uint16_t data);
uint16_t MAX11043_flash_read(uint8_t page, uint8_t address);
uint16_t MAX11043_scan_read();
bool MAX11043_isFlashBusy();

void MAX11043_read_samples_cont();
void MAX11043_stop_reading_samples();
void MAX11043_attach_interrupt();
void MAX11043_stop_interrupt();

void MAX11043_on_sample();

#ifdef __cplusplus
}
#endif
#endif

