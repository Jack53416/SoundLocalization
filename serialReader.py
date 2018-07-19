import serial
import struct
import wave

with serial.Serial('/dev/ttyACM0', 2000000, timeout=1) as ser, wave.open("adc.wav", "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(41666)
    while True:
        try:
            inputBytes = ser.read(4096 * 2)
            bytelen = len(inputBytes)
            #print("len:{}, bytes:{}".format(bytelen, inputBytes))
            #frames = struct.unpack("{}H".format(bytelen // 2), inputBytes)
            wav.writeframes(inputBytes)
        except KeyboardInterrupt:
            break;

