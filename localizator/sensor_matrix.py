import numpy as np
import serial
import struct
from bisect import bisect_left
from collections import deque
from typing import Tuple, List
from localizator.receiver import Receiver
from localizator.dft import DFT
from localizator.MLE import MLE
from localizator.math_tools import gcc_phat
from localizator.sound_detector import SoundDetector

import matplotlib.pyplot as plt
import librosa
import librosa.display

import scipy.io.wavfile
import scipy.signal


class SensorMatrix(object):

    class InvalidInput(Exception):
        pass

    def __init__(self,
                 receiver_coords: List[Tuple[float, float, float]],
                 reference_rec_id: int = 0,
                 rec_buff_size: int = 2,
                 sampling_freq: int = 41666,
                 data_chunk: int = 4096,
                 debug: bool = False):

        receivers: List[Receiver] = [Receiver(rec[0], rec[1], rec[2], buffer_size=rec_buff_size)
                                     for rec in receiver_coords]
        self._sound_detector = SoundDetector(0.9993)
        self._mle_calc = MLE(receivers, reference_rec_id=reference_rec_id)
        self._data_chunk = 4096
        self._dft = DFT(256, sampling_freq)
        self._rec_dft_buff = np.array([])
        self._serial_settings = {
            "channelNr": 4,
            "port": '/dev/ttyACM0',
            "baud": 2000000,
            "timeout": 1,
            "resultSize_bytes": 2
        }
        self._recognition_settings = {
            "lowSpectrum": 7000,
            "highSpectrum": 12000,
            "minPart": 0.05,
            "noiseFloor": 5000
        }
        self.debug = debug

        self._memory_buff = []
        self._mem_buff_limit = sampling_freq * 30
        self._evt_chunk_idxs = []
        fs, self._reference = scipy.io.wavfile.read("samples/referenceBounce.wav")

        self._hit_ctr = 0

    def start_cont_localization(self, input_src: str ="serial", filename="input.wav"):
        byte_count = self._serial_settings["channelNr"] * self._data_chunk * self._serial_settings["resultSize_bytes"]
        Receiver.isSimulation = False

        if input_src == "wav":
            import wave

            with wave.open(filename, "rb") as wav:
                self._dft.sampling_rate = wav.getframerate()
                self._serial_settings["channelNr"] = wav.getnchannels()
                length = wav.getnframes() // self._data_chunk

                for idx in range(0, length):
                    input_bytes = wav.readframes(self._data_chunk)
                    if self.localize(input_bytes) and self.debug:
                        self._evt_chunk_idxs.append(idx)

                if len(self._evt_chunk_idxs) >= 0:
                    #plt.subplot(311)
                    plt.plot(self._memory_buff, 'b.-')
                    for idx in self._evt_chunk_idxs:
                        plt.axvspan(idx * self._data_chunk, (idx + 1) * self._data_chunk - 1,
                                    facecolor='#2ca02c', alpha=0.5)
                    plt.plot(self._sound_detector.env_history, 'r')
                    plt.tight_layout()
                    plt.show()
        else:
            with serial.Serial(self._serial_settings["port"],
                               self._serial_settings["baud"],
                               timeout=self._serial_settings["timeout"]) as ser:
                while ser.is_open:
                    input_bytes = ser.read(byte_count)
                    self.localize(input_bytes)

    def localize(self, raw_data: bytes) -> bool:
        """Performs the whole localization process: check for searched signal, and if it is found calculate the
        src position, returns true if it was detected and false otherwise(for statistics)"""
        byte_len = len(raw_data)
        frames: List[int] = struct.unpack("{}h".format(byte_len // self._serial_settings["resultSize_bytes"]),
                                          raw_data)
        recs = self._mle_calc.receivers
        energy = []
        # Split data into separate channels
        for ch_id in range(0, self._serial_settings["channelNr"]):
            ch_data = np.array(frames[ch_id::self._serial_settings["channelNr"]], dtype=np.float32)
            energy.append(sum(map(lambda x: x * x, ch_data)))
            recs[ch_id].data_buffer.append(ch_data)

        # claculate energy of all channels na choose the strongest
        strongest_idx: int = np.argmax(energy)

        is_event, s_idx, e_idx = self.is_event_detected(recs[strongest_idx].data_buffer, strongest_idx)

        if is_event:
            # find TdoA
            self.calculate_tdoa(s_idx, e_idx)
            # calculate src
            res = self.estimate_src_position()
            print("calculation result:{}".format(res))
            # send to server
            return True
        return False

    def update_receiver_pos(self, positions: List[Tuple[float, float, float]], ref_id: int = 0):
        """Updates the spatial positions of all microphones connected to the array. If less than 4 new positions are
           provided, then only first few will be updated. If more than 4 values are provided it raises InvalidInput
           Exception"""

        if len(positions) > len(self._mle_calc.receivers):
            raise SensorMatrix.InvalidInput("Too large position array to update only 4 receiver location!")

        for [idx, pos] in enumerate(positions):
            self._mle_calc.receivers[idx].position = pos

        self._mle_calc.ref_rec = ref_id

    def get_raw_data(self):
        pass

    def is_event_detected(self, signal_buffer: deque, mic_id: int) -> Tuple[bool, int, int]:
        """Detects if the ping pong ball hit was registered. This is done in a simple fashion by taking into account
           only frequencies from certain range specified in recognition settings. Then the spectrum is calculated and
           smoothed by moving average and compared via normalized cross-correlation to the saved sound pattern"""
        last_idx = len(signal_buffer) - 1
        current_signal = signal_buffer[last_idx]

        if self.debug and len(self._memory_buff) < self._mem_buff_limit:
            self._memory_buff += current_signal.tolist()

        self._sound_detector.detect_sound(current_signal, 15000, 12000)

        while len(self._sound_detector.events) > 0:
            l_idx, h_idx, s_mic = self._sound_detector.events.pop()

            if l_idx >= h_idx:
                if s_mic != mic_id:
                    signal_buffer = self._mle_calc.receivers[s_mic].data_buffer
                    current_signal = signal_buffer[last_idx]
                prev_signal_chunk = signal_buffer[0]
                sound_signal = np.concatenate([prev_signal_chunk[l_idx::], current_signal[:h_idx]])
            else:
                sound_signal = current_signal[l_idx: h_idx]

            D = librosa.stft(sound_signal, n_fft=64)
            spectrogram = np.abs(D)
            spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max)
            frequencies = np.linspace(0, 41666, 33)
            pos_l = bisect_left(frequencies, self._recognition_settings["lowSpectrum"])
            pos_h = bisect_left(frequencies, self._recognition_settings["highSpectrum"])

            spec_slice = np.mean(spectrogram_db[pos_l:pos_h, :], axis=0)
            bounce_idx = [idx for idx, el in enumerate(spec_slice) if el >= -32.0]

            if len(bounce_idx) >= 3:
                return True, l_idx, h_idx

        return False, -1, -1

    def calculate_tdoa(self, s_idx: int, e_idx: int):
        """Calculates TDoA between all receivers and reference one in the sensor matrix. Results are stored within
           receiver object"""

        # extract bounce sound and its surronding from rec buffers

        l_bound = s_idx - self._dft.size//2 + 1
        u_bound = (s_idx + self._dft.size//2) % (self._data_chunk - 1)
        last_idx = len(self._mle_calc.ref_rec.data_buffer) - 1

        if s_idx >= e_idx:
            last_idx -= 1

        if l_bound < 0:
            l_bound = (self._data_chunk - 1) + l_bound

        if l_bound >= u_bound:
            bounce_data = [np.concatenate([rec.data_buffer[0][l_bound:], rec.data_buffer[1][:u_bound]])
                           for rec in self._mle_calc.receivers]
        else:
            bounce_data = [rec.data_buffer[last_idx][l_bound: u_bound+1] for rec in self._mle_calc.receivers]

        for rec_idx in range(1, self._serial_settings["channelNr"]):

            delay, hist = gcc_phat(bounce_data[rec_idx], bounce_data[0], self._dft, phat=True,
                                   delay_in_seconds=True, buffered_dft=False)
            self._mle_calc.receivers[rec_idx].tDoA = delay
        if self.debug:
            print(delay)
            plt.subplot(311)
            plt.plot(bounce_data[0], label="signal")
            plt.plot(bounce_data[1], label="delayed")
            plt.subplot(312)
            plt.plot(bounce_data[0], label="signal")
            plt.plot(bounce_data[2], label="delayed")
            plt.subplot(313)
            plt.plot(bounce_data[0], label="signal")
            plt.plot(bounce_data[3], label="delayed")
            plt.show()

    def estimate_src_position(self) -> List[np.ndarray]:
        r1 = self._mle_calc.calculate()
        r2 = self._mle_calc.get_other_solution()
        r1 = np.squeeze(np.asarray(r1))
        r2 = np.squeeze(np.asarray(r2))
        return [r1, r2]

    def simulate_wave_propagation(self, src_pos: Tuple[float, float, float]) -> List[np.ndarray]:
        """Simulates the propagation of the sound from given src points and based on time differences, recalculates
           the position of the sound"source. Returns both roots found during the process, with first one being chosen
            by the algorithm as the correct one"""

        Receiver.set_source_position(src_pos)
        Receiver.isSimulation = True
        for rec in self._mle_calc.receivers:
            rec.receive()
        return self.estimate_src_position()