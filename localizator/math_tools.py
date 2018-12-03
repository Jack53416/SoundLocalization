from typing import Tuple
from scipy.signal import butter, sosfilt, sosfreqz

import numpy as np
from localizator.dft import DFT
import matplotlib.pyplot as plt


def gcc_phat(input_signal: np.ndarray, ref_signal: np.ndarray, dft: DFT, phat: bool = False,
             delay_in_seconds: bool = True, interpolation_factor: int = 1,
             buffered_dft: bool = False, force_delay: bool = False) -> Tuple[float, np.ndarray]:
    """Performs General cross correlation in frequency domain with optional Phase Transform filtering(PHAT).
       Returns a Tuple of delay(in sec or samples) and resulting histogram"""

    fft_signal = dft.transform(input_signal)
    if buffered_dft:
        fft_ref_signal = ref_signal
    else:
        fft_ref_signal = np.conj(dft.transform(ref_signal))

    corr = fft_signal * fft_ref_signal

    if phat:
        denom = np.ones(corr.shape, corr.dtype)
        tmp = np.abs(corr)
        denom[tmp != 0] = tmp[tmp != 0]
        corr = corr / denom

    histogram = dft.inverse_transform(corr, interpolation_factor)
    if force_delay:
        histogram[0] = 0
    histogram = np.fft.fftshift(histogram)

    delay = (np.argmax(histogram) - dft.size // 2 * interpolation_factor) / interpolation_factor

    if delay_in_seconds:
        delay = delay / dft.sampling_rate

    return delay, histogram


def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


def _test_gcc_phat():
    freq = 500
    fs = 44100
    n_fft = 1024
    dt = 1 / fs
    t_delay = -50 * dt  # delay in samples
    int_factor = 8
    dft = DFT(n_fft, fs)

    test_signal = [3 * np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * 1200 * t) for t in np.arange(n_fft) / fs]
    delayed_test_signal = [3 * np.sin(2 * np.pi * freq * (t - t_delay)) + np.sin(2 * np.pi * 1200 * (t - t_delay))
                           for t in np.arange(n_fft) / fs]

    noise1 = np.random.normal(0, 1, 1024)
    noise2 = np.random.normal(0, 1, 1024)

    signal = test_signal + noise1
    delayed_signal = delayed_test_signal + noise2

    delay, hist = gcc_phat(signal, delayed_signal, dft, phat=False, delay_in_seconds=False,
                           interpolation_factor=int_factor)

    print(delay)

    plt.subplot(211)
    plt.plot(range(-n_fft // 2 * int_factor, n_fft // 2 * int_factor), hist)

    plt.subplot(212)
    plt.plot(signal, label="signal")
    plt.plot(delayed_signal, label="delayed")

    plt.legend(loc=0)
    plt.show()


def recognize_test():
    import matplotlib.pyplot as plt
    from bisect import bisect_left
    import wave
    import struct
    n_fft = 4096
    settings = {
        "lowSpectrum": 10000,
        "highSpectrum": 15000,
        "minPart": 0.05,#0.18
        "maxPart": 0.99,#0.5
        "noiseFloor": 5000 #170000
    }
    interpolation_f = 4

    filename = 'samples/micThreePingsDesk.wav'

    with wave.open(filename, "rb") as wav:
        fs = wav.getframerate()
        channels = wav.getnchannels()
        dft = DFT(n_fft, sampling_rate=fs)
        length = wav.getnframes() // n_fft

        for i in range(0, length):
            print(i)
            raw = wav.readframes(n_fft)
            data = struct.unpack("<{}h".format(n_fft * channels), raw)

            ch_data = unpack_channels(data, channels)

            spectrum = dft.amplitude_spectrum(np.array(ch_data[0]))
            pos_l = bisect_left(spectrum[0], settings["lowSpectrum"])
            pos_h = bisect_left(spectrum[0], settings["highSpectrum"])

            freq_s = sum(spectrum[1])
            high_fs = sum(spectrum[1][pos_l:pos_h:])
            high_f = high_fs / freq_s

            print("high:{} ,high ratio:{} sigLvl: {}".format(high_fs, high_f, freq_s))

            if settings["minPart"] <= high_f <= settings["maxPart"] and high_fs > settings["noiseFloor"]:
                print("Match")
                #ch_data[0] = butter_bandpass_filter(ch_data[0], 10000, 15000, fs = 44166)
                #ch_data[1] = butter_bandpass_filter(ch_data[1], 10000, 15000, fs = 44166)
                if channels > 1:
                    delay, hist = gcc_phat(ch_data[1], ch_data[0], dft, phat=True, delay_in_seconds=False, force_delay=False,
                                           interpolation_factor=interpolation_f)
                    print("Delay: {}".format(delay))
                    plt.subplot(311)
                    plt.plot(range(-n_fft // 2 * interpolation_f, n_fft // 2 * interpolation_f), hist)

                    plt.subplot(312)
                    plt.plot(ch_data[1], label="signal")
                    plt.plot(ch_data[0], label="delayed")

                    plt.legend(loc=0)

                    plt.subplot(313)
                    plt.plot(spectrum[0][pos_l:pos_h:], spectrum[1][pos_l:pos_h:], 'b.-', label='Hann filtered')

                    plt.show()


def unpack_channels(frames, channel_nr):
    result = []
    for ch_id in range(0, channel_nr):
        result.append(frames[ch_id::channel_nr])
    return result

def butter_bandpass(lowcut, highcut, fs=44166, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], analog=False, btype='band', output='sos')
    return sos


def butter_bandpass_filter(data, lowcut, highcut, fs=44166, order=5):
    sos = butter_bandpass(lowcut, highcut, fs, order=order)
    y = sosfilt(sos, data)
    return y


def xcorr(a: np.ndarray, b: np.ndarray) -> float:
    a = (a - np.mean(a)) / (np.std(a) * len(a))
    b = (b - np.mean(b)) / np.std(b)
    return np.max(np.correlate(a, b))

#_test_gcc_phat()


#recognize_test()

