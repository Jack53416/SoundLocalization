from enum import IntEnum, IntFlag, unique
from abc import ABC
from functools import reduce


# noinspection SpellCheckingInspection
@unique
class RegAddr(IntEnum):
    # REG                                 SIZE(BITS)
    ADC_A_RES = 0x00,                    # 16/24
    ADC_B_RES = 0x04,                    # 16/24
    ADC_C_RES = 0x08,                    # 16/24
    ADC_D_RES = 0x0C,                    # 16/24
    ADC_A_AND_B_RES = 0x10,              # 32/48
    ADC_C_AND_D_RES = 0x14,              # 32/48
    ADC_ABCD_RES = 0x1B,                 # 64/96

    STATUS = 0X1C,                       # 8
    CONFIG = 0x20,                       # 16

    FINE_DAC_VALUE = 0x24,               # 16
    DAS_STEP_SIZE = 0x28,                # 16
    COARSE_DAC_H_L = 0x2C,               # 8 + 8

    ADC_A_CONFIG = 0x30,                 # 16
    ADC_B_CONFIG = 0x34,                 # 16
    ADC_C_CONFIG = 0x38,                 # 16
    ADC_D_CONFIG = 0x3C,                 # 16

    REF_AND_BUF_CONFIG = 0x40,           # 16
    GAIN_A = 0x44,                       # 16
    GAIN_B = 0x48,                       # 16
    GAIN_C = 0x4C,                       # 16
    GAIN_D = 0x50,                       # 16

    FILTER_COEFFICIENTS_ADDRESS = 0x54,  # 8
    CRAM_DATA_OUT = 0x58,                # 32
    FILTER_COEFFICIENT_IN = 0x5C,        # 32

    FLASH_MODE_SELECT = 0x60,            # 8
    FLASH_ADDRESS = 0x64,                # 16
    FLASH_DATA_IN = 0x68,                # 16
    FLASH_DATA_OUT = 0x6C                # 16


class Register(ABC):

    def __init__(self, address: int, mask: int, size: int = 8, reset_value: int = 0x0):
        self._address = address
        self._value = reset_value
        self._size = size
        self._reset_value = reset_value
        if mask is not None:
            self._mask = mask
        else:
            self._mask = 2 ** size - 1
        pass

    @property
    def value(self):
        return self._value & self.mask

    @property
    def mask(self):
        return self._mask

    @property
    def size(self):
        return self._size

    @value.setter
    def value(self, value):
        self._value = value

    def set_flags(self, *flags):
        self._value = reduce(lambda a, b: a | b, list(flags))


class StatusRegister(Register):
    def __init__(self):
        super(StatusRegister, self).__init__(RegAddr.STATUS, mask=0xFF, size=8, reset_value=0x00)

    @unique
    class Flags(IntFlag):
        FLASH_BUSY = 0x20
        BOOT = 0x10
        OVERFLOW_A = 0x08
        OVERFLOW_B = 0x04
        OVERFLOW_C = 0x02
        OVERFLOW_D = 0x01


class ConfigRegister(Register):
    def __init__(self):
        super(ConfigRegister, self).__init__(RegAddr.CONFIG, mask=0xFFFF, size=16, reset_value=0x6000)

    class Flags(IntFlag):
        EXT_CLK_RESONATOR = 0x0,
        EXT_CLK_CLOCK = 0x1 << 15,

        CLK_DIV_1_TO_2 = 0x0 << 13,
        CLK_DIV_1_TO_3 = 0x1 << 13,
        CLK_DIV_1_TO_4 = 0x2 << 13,
        CLK_DIV_1_TO_6 = 0x3 << 13,

        POWER_MODE_LOW = 0x1 << 12
        POWER_MODE_NORMAL = 0x0 << 12,

        CHANNEL_A_POWER_DOWN = 0x1 << 11,  # 0 means channel is powered
        CHANNEL_B_POWER_DOWN = 0x1 << 10,
        CHANNEL_C_POWER_DOWN = 0x1 << 9,
        CHANNEL_D_POWER_DOWN = 0x1 << 8,

        DAC_POWER_DOWN = 0x1 << 7,  # 0 means DAC is powered
        OSC_POWER_DOWN = 0x1 << 6,  # 0 means OSC is powered
        ADC_24_BITS = 0x1 << 5,     # 0 means ADC is in 16 bit mode

        SCAN_A_CHANNEL = 0x1 << 4,  # 0 SCAN mode is inactive
        SCAN_B_CHANNEL = 0x1 << 3
        SCAN_C_CHANNEL = 0x1 << 2
        SCAN_D_CHANNEL = 0x1 << 1

        DECIMATE_FILTER_12 = 0x1
        DECIMATE_FILTER_24 = 0x0


class ChannelConfigRegister(Register):
    class Flags(IntFlag):
        BIAS_VOLTAGE_33_AVDD = 0x0,
        BIAS_VOLTAGE_35_AVDD = 0x1,
        BIAS_VOLTAGE_38_AVDD = 0x2,
        BIAS_VOLTAGE_40_AVDD = 0x3
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


