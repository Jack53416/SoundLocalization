from typing import Tuple

import numpy as np
from dft import DFT
import matplotlib.pyplot as plt


def gcc_phat(input_signal: np.ndarray, ref_signal: np.ndarray, dft: DFT, phat: bool = False,
             delay_in_seconds: bool = True, interpolation_factor: int = 1) -> Tuple[float, np.ndarray]:
    """Performs General cross correlation in frequency domain with optional Phase Transform filtering(PHAT).
       Returns a Tuple of delay(in sec or samples) and resulting histogram"""

    fft_signal = dft.transform(input_signal)
    fft_ref_signal = np.conj(dft.transform(ref_signal))

    corr = fft_signal * fft_ref_signal

    if phat:
        denom = np.ones(corr.shape, corr.dtype)
        tmp = np.abs(corr)
        denom[tmp != 0] = tmp[tmp != 0]
        corr = corr / denom

    histogram = dft.inverse_transform(corr, interpolation_factor)

    histogram = np.fft.fftshift(histogram)

    delay = np.argmax(histogram) - dft.size // 2

    if delay_in_seconds:
        delay = delay / (interpolation_factor * dft.sampling_rate)

    return delay, histogram


def _test_gcc_phat():
    freq = 500
    fs = 44100
    n_fft = 1024
    dt = 1 / fs
    t_delay = -50 * dt  # delay in samples

    dft = DFT(n_fft, fs)

    test_signal = [3 * np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * 1200 * t) for t in np.arange(n_fft) / fs]
    delayed_test_signal = [3 * np.sin(2 * np.pi * freq * (t - t_delay)) + np.sin(2 * np.pi * 1200 * (t - t_delay))
                           for t in np.arange(n_fft) / fs]

    noise1 = np.random.normal(0, 1, 1024)
    noise2 = np.random.normal(0, 1, 1024)

    signal = test_signal + noise1
    delayed_signal = delayed_test_signal + noise2

    delay, hist = gcc_phat(signal, delayed_signal, dft, phat=False)

    print(delay)

    plt.subplot(211)
    plt.plot(range(-n_fft // 2, n_fft // 2), hist)

    plt.subplot(212)
    plt.plot(signal, label="signal")
    plt.plot(delayed_signal, label="delayed")

    plt.legend(loc=0)
    plt.show()

# _test_gcc_phat()
