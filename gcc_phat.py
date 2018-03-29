"""Implementation of genral cross corelation phase transform method 
- GCC-PHAT for finding siganls delay"""

import numpy as np
import profile

def gcc_phat(signal, refSignal, fs = 1, fftSize = None, intFactor = 1):
    """Calculates the delay in seconds between signal and refSignal
       Additionaly it performs interpolation in time domain by padding 0s intFactor times
       in the frequency domain"""

    if not fftSize:
        fftSize = getFftSize(len(signal) + len(refSignal))
    
    fft_signal = np.fft.rfft(signal, n = fftSize)
    fft_refSignal = np.fft.rfft(refSignal, n = fftSize)
    
    fft_refSignal = np.conj(fft_refSignal)
    
    corr = fft_signal * fft_refSignal
    
    ratio = corr / abs(corr)
    
    result = np.fft.irfft(ratio, n = intFactor * fftSize)
    result[0] = 0
    delay = np.argmax(result) / (intFactor * fs)
    
    if delay > fftSize / 2:
        delay = -(fftSize - delay) 
    return delay, result

def getFftSize(sampleNr):
    """Finds the closes power of 2 to the provided sample number"""
    return 1 << (sampleNr - 1).bit_length()


def test():
    import matplotlib.pyplot as plt
    
    s1 = [1,2,3,4,5,0,0,0,0]
    s2 = [0,0,1,2,3,4,5,0,0]

    #gcc_phat(s1, s2, intFactor = 16)
    Fs = 20000
    f1 = 100
    dt = 1 / Fs
    tdelay = 500 *  dt
    x = np.linspace(0, 1, 20000)
    s1 = np.sin(2 * np.pi * f1 * x) + np.sin(2 * np.pi * 234 * x)
    s2 = np.sin(2 * np.pi * f1 * (x - tdelay)) + np.sin(2 * np.pi * 234 * (x - tdelay))
    t, res = gcc_phat(s2, s1)
    print(t)
    plt.plot(abs(res[0:20]))
    plt.show()

test()
#profile.run("test()")
