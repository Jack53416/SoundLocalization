#ifndef HARDWARE_H
#define HARDWARE_H

#ifdef __cplusplus
extern "C" {
#endif

int hardware_init();
int spi_init(uint8_t cs, uint8_t dataReady, uint8_t convRun);
void spi_close();
void hardware_disable();

void spi_read_back(char *buffer, size_t byteCount);

void spi_write(char *data, size_t byteCount);
void spi_read(char *buffer, size_t byteCount);
void spi_xfer(char *txData, char *rxData, size_t byteCount);
void spi_cs_low();
void spi_cs_high();

void conv_run_high();
void conv_run_low();
void register_callback(void (*cb)());
void remove_callback();
#ifdef __cplusplus
}
#endif

#endif

