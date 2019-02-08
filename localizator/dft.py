from typing import Tuple
import numpy as np


class DFT:
    """Class for handling discrete fourier transform, for efficiency it stores the predefined size of the transform,
       The Hanning window and sampling rate. Exception is thrown when the provided signal is not of the expected size"""

    def __init__(self, size: int, sampling_rate: int = 44100) -> None:
        self._size = size
        self._window = np.hanning(self.size)
        self._dtfSize = self.size // 2 + 1
        self._samplingRate = sampling_rate
        self._frequencies = np.linspace(0, self._samplingRate, self._size)

    def transform(self, signal: np.ndarray) -> np.ndarray:
        if len(signal) < self._size:
            signal = np.pad(signal, mode="constant", pad_width=(self._size - len(signal), 0))

        return np.fft.rfft(signal * self._window)

    def get_spectrum(self, fft_transform: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if len(fft_transform) != self._dtfSize:
            raise self.InvalidSignalLength("Invalid dft length: {}, should be: {}"
                                           .format(len(fft_transform), self._dtfSize))

        amp_spectrum = abs(fft_transform) * 4 / self._size
        return self._frequencies[0:self._dtfSize], amp_spectrum

    def amplitude_spectrum(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        dft = self.transform(signal)
        return self.get_spectrum(dft)

    def inverse_transform(self, fft_transform: np.ndarray, padding_factor: int = 1) -> np.ndarray:
        if len(fft_transform) != self._dtfSize:
            raise self.InvalidSignalLength("Invalid dft length: {}, should be: {}"
                                           .format(len(fft_transform), self._dtfSize))

        result = np.fft.irfft(fft_transform, n=padding_factor * self._size)
        # result[0] = 0  # Bit Questionable is it ?
        return result

    @property
    def size(self):
        return self._size

    @property
    def dft_size(self):
        return self._dtfSize

    @property
    def sampling_rate(self):
        return self._samplingRate

    @size.setter
    def size(self, new_size):
        self._size = new_size
        self._window = np.hamming(new_size)

    @sampling_rate.setter
    def sampling_rate(self, fs):
        self._samplingRate = fs

    class InvalidSignalLength(Exception):
        pass


def test():
    import matplotlib.pyplot as plt
    freq = 500
    fs = 44100
    n_fft = 1024

    dft = DFT(n_fft, sampling_rate=fs)

    data = [3 * np.sin(2 * np.pi * freq * t) + np.sin(2 * np.pi * 1200 * t) for t in np.arange(n_fft) / fs]
    spectrum = dft.amplitude_spectrum(np.array(data))

    plt.plot(spectrum[0], spectrum[1], 'b.-', label='Hann filtered')
    plt.xlim(-0.01, 5000)

    plt.xlabel('frequency')
    plt.ylabel('amplitude')
    plt.grid()
    plt.legend(loc=0)
    plt.show()

