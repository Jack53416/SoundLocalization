#ifndef SPI
#define SPI

int hardware_init();
int spi_init(uint8_t cs, uint8_t dataReady, uint8_t convRun);
void spi_close();
void hardware_disable();

void spi_write(char *data, size_t byteCount);
void spi_read(char *buffer, size_t byteCount);
void spi_xfer(char *txData, char *rxData, size_t byteCount);
void spi_cs_low();
void spi_cs_high();


#endif