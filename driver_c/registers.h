#ifndef REGISTERS
#define REGISTERS

// *** REGISTERS  *** //
// ADR      SIZE
/* 0x00     16/24 */ #define   ADC_A_RESULT          0x00
/* 0x01     16/24 */ #define   ADC_B_RESULT          0x04
/* 0x02     16/24 */ #define   ADC_C_RESULT          0x08
/* 0x03     16/24 */ #define   ADC_D_RESULT          0x0C
/* 0x04     32/48 */ #define   ADC_A_AND_B_RESULT    0x10
/* 0x05     32/48 */ #define   ADC_C_AND_D_RESULT    0x14
/* 0x06     64/96 */ #define   ADC_ABCD_RESULT       0x18

/* 0x07     8     */ #define   STATUS                0x1C
/* 0x08     16    */ #define   CONFIGURATION         0x20

/* 0x09     16    */ #define   FINE_DAC_VALUE        0x24
/* 0x0A     16    */ #define   DAC_STEP_SIZE         0x28
/* 0x0B     8 + 8 */ #define   COARSE_DAC_H_L        0x2C

/* 0x0C     16    */ #define   ADC_A_CONFIG          0x30
/* 0x0D     16    */ #define   ADC_B_CONFIG          0x34
/* 0x0E     16    */ #define   ADC_C_CONFIG          0x38
/* 0x0F     16    */ #define   ADC_D_CONFIG          0x3C

/* 0x10     16    */ #define   REF_AND_BUF_CONFIG    0x40
/* 0x11     16    */ #define   GAIN_A                0x44
/* 0x12     16    */ #define   GAIN_B                0x48
/* 0x13     16    */ #define   GAIN_C                0x4C
/* 0x14     16    */ #define   GAIN_D                0x50

/* 0x15     8     */ #define   FILTER_COEFFICIENTS_ADDRESS   0x54
/* 0x16     32    */ #define   CRAM_DATA_OUT         0x58
/* 0x17     32    */ #define   FILTER_COEFFICIENT_IN 0x5C

/* 0x18     8     */ #define   FLASH_MODE_SELECT     0x60
/* 0x19     16    */ #define   FLASH_ADDRESS         0x64
/* 0x1A     16    */ #define   FLASH_DATA_IN         0x68
/* 0x1B     16    */ #define   FLASH_DATA_OUT        0x6C

#define MAX11043_WRITE    0x00
#define MAX11043_READ     0x02

// ADDRESSES for CRAM
// get the Address by calculating ADC_x + STAGE_x + COEFF_x or FILTER_GAIN
// get the start-Address for a Filter-stage by calculating ADC_x + STAGE_x

#define CRAM_STAGE_1   0x03
#define CRAM_STAGE_2   0x06
#define CRAM_STAGE_3   0x09
#define CRAM_STAGE_4   0x0C
#define CRAM_STAGE_5   0x0F
#define CRAM_STAGE_6   0x12
#define CRAM_STAGE_7   0x15

#define CRAM_ADC_A     0x00
#define CRAM_ADC_B     0x40
#define CRAM_ADC_C     0x80
#define CRAM_ADC_D     0xc0


//STATUS REG 0x07
enum __attribute__ ((__packed__)) {
	FLASH_BUSY = 0x20,
	BOOT = 0x10,
	OVERFLOW_A = 0x08,
	OVERFLOW_B = 0x04,
	OVERFLOW_C = 0x02,
	OVERFLOW_D = 0x01

}Status;


//CONFIG REG 0x08


enum {
        EXT_CLK_RESONATOR = 0x0 << 15,
        EXT_CLK_CLOCK = 0x1 << 15
}ClkSource;

enum {
        CLK_DIV_1_TO_2 = 0x0 << 13,
        CLK_DIV_1_TO_3 = 0x1 << 13,
        CLK_DIV_1_TO_4 = 0x2 << 13,
        CLK_DIV_1_TO_6 = 0x3 << 13
}ClkDivision;

enum {
        POWER_MODE_LOW = 0x1 << 12,
        POWER_MODE_NORMAL = 0x0 << 12,
	CHANNEL_A_POWER_DOWN = 0x1 << 11, 
        CHANNEL_B_POWER_DOWN = 0x1 << 10,
        CHANNEL_C_POWER_DOWN = 0x1 << 9,
        CHANNEL_D_POWER_DOWN = 0x1 << 8,
        DAC_POWER_DOWN = 0x1 << 7,
        OSC_POWER_DOWN = 0x1 << 6  
}PowerMode;

enum {
	ADC_16_BITS = 0x0,
	ADC_24_BITS = 0x1 << 5

}BitSize;

enum {
        SCAN_A_CHANNEL = 0x1 << 4, 
        SCAN_B_CHANNEL = 0x1 << 3,
        SCAN_C_CHANNEL = 0x1 << 2,
        SCAN_D_CHANNEL = 0x1 << 1

}ScanMode;

enum {
        DECIMATE_FILTER_12 = 0x1,
        DECIMATE_FILTER_24 = 0x0

}DecimateFilter;

//CHANNEL CONFIG REGISTERS

enum {
        BIAS_VOLTAGE_33_AVDD = 0x0,
        BIAS_VOLTAGE_35_AVDD = 0x1,
        BIAS_VOLTAGE_38_AVDD = 0x2,
        BIAS_VOLTAGE_40_AVDD = 0x3,
        BIAS_VOLTAGE_42_AVDD = 0x4,
        BIAS_VOLTAGE_44_AVDD = 0x5,
        BIAS_VOLTAGE_46_AVDD = 0x6,
        BIAS_VOLTAGE_48_AVDD = 0x7,
        BIAS_VOLTAGE_50_AVDD = 0x8,
        BIAS_VOLTAGE_52_AVDD = 0x9,
        BIAS_VOLTAGE_54_AVDD = 0xA,
        BIAS_VOLTAGE_56_AVDD = 0xB,
        BIAS_VOLTAGE_58_AVDD = 0xC,
        BIAS_VOLTAGE_60_AVDD = 0xD,
        BIAS_VOLTAGE_62_AVDD = 0xE,
        BIAS_VOLTAGE_65_AVDD = 0xF
}ChannelBias;

#endif
