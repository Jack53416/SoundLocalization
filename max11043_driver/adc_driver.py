"""
    Driver for MAX11043 simultaneous sampling analog to digital converter.
    Requires python 3.7+
    To install python 3.8
    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get dist-upgrade
    sudo apt-get install build-essential python-dev python-setuptools python-pip python-smbus
    sudo apt-get install build-essential libncursesw5-dev libgdbm-dev libc6-dev
    sudo apt-get install zlib1g-dev libsqlite3-dev tk-dev
    sudo apt-get install libssl-dev openssl
    sudo apt-get install libffi-dev

    then clone https://github.com/python/cpython
    and follow the instructions from repository
"""
import pigpio
import numpy as np
import scipy.io.wavfile
from typing import Callable, Tuple
from registers import *

pigScript = b'w 6 0 spiw p0 0x0 spir p0 2 w 6 1' 
class RegAccessMode(IntFlag):
        WRITE = 0x00,
        READ = 0x02

class Adc(object):
    class Channel(IntFlag):
        A = 0x1,
        B = 0x2,
        C = 0x4,
        D = 0x8

    def __init__(self, cs_pin: int = 6, data_ready_pin: int = 13, convrun_pin = 19):
        self._cs_pin: int = cs_pin
        self._data_ready_pin: int = data_ready_pin
        self._convrun_pin: int = convrun_pin

        self.__setup_hardware()

        self._statusReg = StatusRegister()
        self._configReg = ConfigRegister()
        self._channelConfigReg = ChannelConfigRegister()

        self._samples_read: int = 0
        self._channel_A_buffer = []
        self._conversion_finished = False

    """Functions requiring additional hardware library for spi communication"""

    def __spi_xfer(self, data) -> Tuple[int, bytes]:
        data = data.to_bytes(self.byte_length(data), byteorder='big')
        return self.pi.spi_xfer(self.spi_handle, data)

    def __spi_write(self, data: int):
        data = data.to_bytes(self.byte_length(data), byteorder='big')
        self.pi.spi_write(self.spi_handle, data)

    def __spi_read(self, byte_nr) -> Tuple[int, bytes]:
        return self.pi.spi_read(self.spi_handle, byte_nr)

    def __setup_hardware(self):
        self.pi = pigpio.pi()
        self.spi_handle = self.pi.spi_open(0, 20000000)
        self.pi.set_mode(self._cs_pin, pigpio.OUTPUT)
        self.pi.set_mode(self._convrun_pin, pigpio.OUTPUT)
        self.pi.set_mode(self._data_ready_pin, pigpio.INPUT)
        self._cb_handle = self.pi.callback(self._data_ready_pin, pigpio.FALLING_EDGE, self.__on_data_ready())

    def __cs_low(self):
        self.pi.write(self._cs_pin, 0)

    def __cs_high(self):
        self.pi.write(self._cs_pin, 1)

    def __convrun_high(self):
        self.pi.write(self._convrun_pin, 1)

    def __convrun_low(self):
        self.pi.write(self._convrun_pin, 0)

    def __on_data_ready(self):
        def data_redy_cb(gpio, level, tick):
            #print(gpio, level, tick)
            self._samples_read = self._samples_read + 1
            if self._samples_read >= 100000 and not self._conversion_finished:
                print("Data Collected !")
                self._conversion_finished = True
                self.__convrun_low()
                #print(tick)
                #print(self._channel_A_buffer)
                data = np.asarray(self._channel_A_buffer, dtype=np.int16)
                scipy.io.wavfile.write('out.wav', 2000, data)
                print("Done!\r\n")
            sample = self.register_read(RegAddr.ADC_A_RES, 2)
            #print(sample)
            self._channel_A_buffer.append(sample)

        return data_redy_cb
        
    """ADC software functionality implementation"""

    def register_write(self, register: RegAddr, data: int) -> None:
        self.__cs_low()
        self.__spi_write(register.value | RegAccessMode.WRITE)
        self.__spi_write(data)
        self.__cs_high()

    def register_read(self, register: RegAddr, size: int) -> int:
        self.__cs_low()
        self.__spi_write(register.value | RegAccessMode.READ)
        (count, data) = self.__spi_read(size)
        self.__cs_high()
        #print("Nr:{}, data: {}".format(count, data.hex()))
        return int.from_bytes(data, byteorder='big')

    def read_channel(self, channel: Channel, samples_nr: int) -> None:
        self.__convrun_high()

    def read_channel_continuous(self, channel: Channel, sample_chunk: int) -> None:
        pass

    @staticmethod
    def byte_length(data: int) -> int:
        return (data.bit_length() + 7) // 8

def test():
    a = Adc()
    a._configReg.value = a.register_read(RegAddr.CONFIG, 2)
    print(ConfigRegister.Flags(a._configReg.value))
    a._configReg.set_flags(ConfigRegister.Flags.CLK_DIV_1_TO_6,
                           ConfigRegister.Flags.CHANNEL_B_POWER_DOWN,
                           ConfigRegister.Flags.CHANNEL_C_POWER_DOWN,
                           ConfigRegister.Flags.CHANNEL_D_POWER_DOWN)
    print(a._configReg.value)
    print("hex:{}".format(hex(a._configReg.value)))
    a.register_write(RegAddr.CONFIG, a._configReg.value)
    read = a.register_read(RegAddr.CONFIG, 2)
    print(hex(read))
    a._channelConfigReg.set_flags(ChannelConfigRegister.Flags.BIAS_VOLTAGE_50_AVDD,
                                  ChannelConfigRegister.Flags.PGA_POWERED_DOWN,
                                  ChannelConfigRegister.Flags.DIFF_NORMAL,
                                  ChannelConfigRegister.Flags.ENABLE_POSITIVE_BIAS,
                                  ChannelConfigRegister.Flags.USE_LP_FILTER)
    print("hex:{}".format(hex(a._channelConfigReg.value)))
    a.register_write(RegAddr.ADC_A_CONFIG, a._channelConfigReg.value)
    read = a.register_read(RegAddr.ADC_A_CONFIG, 2)
    print(hex(read))
    a.read_channel(a.Channel.A, 128)
    print(a.pi.get_current_tick())
    input("Press Enter")
    a.__convrun_low();
    a.pi.spi_close(a.spi_handle)

test()
