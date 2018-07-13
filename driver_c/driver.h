#ifndef DRIVER
#define DRIVER

void callback(int gpio, int level, uint32_t tick);
void finnish();
uint16_t readMes();

void MAX11043_reg_write(uint8_t reg, uint16_t data);
uint16_t MAX11043_reg_read(uint8_t reg);
void MAX11043_flash_write(uint8_t page, uint8_t address, uint16_t data);
uint16_t MAX11043_flash_read(uint8_t page, uint8_t address);
uint16_t MAX11043_scan_read();

void MAX11043_on_sample(int GPIO, int level, uint32_t timestamp);
void *dumpToFile(void *arg);

#endif
