import numpy as np
import serial
import struct
from bisect import bisect_left
from collections import deque
from typing import Tuple, List, NamedTuple, Sized, Iterable
import itertools
from localizator.receiver import Receiver, SliceDeck
from localizator.dft import DFT
from localizator.MLE import MLE
from localizator.math_tools import gcc_phat
from localizator.sound_detector import SoundDetector

import matplotlib.pyplot as plt
import librosa
import librosa.display


class HistoryEvent(object):
    def __init__(self, start_idx: int, end_idx: int, result: List[np.ndarray]):
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.result = result

    def decrement_indexes(self, value) -> bool:
        self.start_idx -= value
        self.end_idx -= value
        return self.start_idx < 0


class DebugHistory(object):

    def __init__(self, data_chunk: int, buffer_size: int):
        self.data_buffer = SliceDeck(maxlen=buffer_size)
        self._data_chunk = data_chunk
        self._events: List[HistoryEvent] = []
        self._time_offset = 0

    def extend_data(self, data: Sized):
        if len(self.data_buffer) + len(data) > self.data_buffer.maxlen:
            self._time_offset += len(data)

        self.data_buffer.extend(data)

    def append_event(self, overall_idx: int, s_idx, e_idx: int, result: List[np.ndarray]):

        if e_idx > self._data_chunk:
            overall_idx -= 1
            s_idx -= self._data_chunk
            e_idx -= self._data_chunk

        l_bound = overall_idx * self._data_chunk + s_idx
        u_bound = overall_idx * self._data_chunk + e_idx

        self._events.append(HistoryEvent(l_bound, u_bound, result))

    def plot(self, env_history: np.ndarray = np.array([])):
            time_axis = range(self._time_offset, self._time_offset + len(self.data_buffer))
            plt.figure(figsize=(18, 10))
            plt.plot(time_axis, np.array(self.data_buffer), 'b.-')
            plt.axhline(y=12000)
            plt.axhline(y=7000)

            for event in self._events:
                if event.start_idx >= self._time_offset:
                    plt.axvspan(event.start_idx, event.end_idx, facecolor='#2ca02c', alpha=0.5)

            plt.plot(time_axis, np.array(env_history), 'r')
            plt.tight_layout(rect=[0.02, 0.03, 1, 0.95])
            plt.xlabel("Sample number", fontsize=20)
            plt.ylabel("ADC value", fontsize=20)
            plt.savefig("signal.png")
            plt.show()


class SensorMatrix(object):

    class InvalidInput(Exception):
        pass

    def __init__(self,
                 receiver_coords: List[Tuple[float, float, float]],
                 reference_rec_id: int = 0,
                 rec_buff_size: int = 4096 * 2,
                 sampling_freq: int = 41666,
                 data_chunk: int = 4096,
                 debug: bool = False):

        receivers: List[Receiver] = [Receiver(rec[0], rec[1], rec[2], buffer_size=rec_buff_size)
                                     for rec in receiver_coords]
        debug_buff_size = 120 * data_chunk
        self._sound_detector = SoundDetector(0.9993, debug_buff_size)
        self._mle_calc = MLE(receivers, src_conditions=lambda src: 0 <= src[2] < 2.0, reference_rec_id=reference_rec_id)
        self._data_chunk = 4096
        self._dft = DFT(512, sampling_freq)
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

        self.debug_history = DebugHistory(data_chunk, debug_buff_size)

    def start_cont_localization(self, input_src: str = "serial", filename="input.wav"):
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
                    self.localize(input_bytes, idx)

                if self.debug:
                    self.debug_history.plot(self._sound_detector.env_history)
        else:
            with serial.Serial(self._serial_settings["port"],
                               self._serial_settings["baud"],
                               timeout=self._serial_settings["timeout"]) as ser:
                while ser.is_open:
                    input_bytes = ser.read(byte_count)
                    self.localize(input_bytes)

    def localize(self, raw_data: bytes, idx: int = 0):
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
            recs[ch_id].data_buffer.extend(ch_data)

        # claculate energy of all channels na choose the strongest
        strongest_idx: int = np.argmax(energy)

        if self.debug:
            self.debug_history.extend_data(recs[strongest_idx].data_buffer[self._data_chunk::])

        signal_buffer = recs[strongest_idx].data_buffer

        self._sound_detector.detect_sound(signal_buffer, 12000, 7000, data_offset=self._data_chunk)

        while len(self._sound_detector.events) > 0:
            l_idx, h_idx, s_mic = self._sound_detector.events.pop()

            is_event = self.is_event_detected(signal_buffer[l_idx: h_idx])

            if is_event:
                # find TdoA
                self.calculate_tdoa(l_idx, h_idx)
                # calculate src
                res = self.estimate_src_position()
                print("calculation result:{}".format(res))
                self.debug_history.append_event(idx, l_idx, h_idx, res)
                # send to server

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

    def is_event_detected(self, sound_signal: Iterable) -> bool:
        """Detects if the ping pong ball hit was registered. This is done in a simple fashion by taking into account
           only frequencies from certain range specified in recognition settings. Then the spectrum is calculated and
           smoothed by moving average and compared via normalized cross-correlation to the saved sound pattern"""

        sound_signal = np.array(sound_signal, np.float32)

        D = librosa.stft(sound_signal, n_fft=64)
        spectrogram = np.abs(D)
        spectrogram_db = librosa.amplitude_to_db(spectrogram, ref=np.max)
        frequencies = np.linspace(0, 41666, 33)
        pos_l = bisect_left(frequencies, self._recognition_settings["lowSpectrum"])
        pos_h = bisect_left(frequencies, self._recognition_settings["highSpectrum"])

        spec_slice = np.mean(spectrogram_db[pos_l:pos_h, :], axis=0)
        bounce_idx = [idx for idx, el in enumerate(spec_slice) if el >= -32.0]

        if len(bounce_idx) >= 3:
            return True

        return False

    def calculate_tdoa(self, s_idx: int, e_idx: int):
        """Calculates TDoA between all receivers and reference one in the sensor matrix. Results are stored within
           receiver object"""

        # extract bounce sound and its surrounding from rec buffers
        l_bound = s_idx - self._dft.dft_size + 1
        u_bound = s_idx + self._dft.dft_size - 1

        if l_bound < 0:
            l_bound = 0

        if u_bound >= len(self._mle_calc.receivers[0].data_buffer):
            u_bound = len(self._mle_calc.receivers[0].data_buffer)

        bounce_data = [rec.data_buffer[l_bound: u_bound] for rec in self._mle_calc.receivers]

        for rec_idx in range(1, self._serial_settings["channelNr"]):

            delay, hist = gcc_phat(bounce_data[rec_idx], bounce_data[0], self._dft, phat=True,
                                   delay_in_seconds=True, buffered_dft=False)
            self._mle_calc.receivers[rec_idx].tDoA = delay
        if self.debug:
            print(delay)
            plt.figure(figsize=(18, 10))
            plt.subplot(311)
            plt.plot(bounce_data[0], label="mic_1")
            plt.plot(bounce_data[1], label="mic_2")
            plt.legend()
            plt.subplot(312)
            plt.plot(bounce_data[0], label="mic_1")
            plt.plot(bounce_data[2], label="mic_3")
            plt.legend()
            plt.subplot(313)
            plt.plot(bounce_data[0], label="mic_1")
            plt.plot(bounce_data[3], label="mic_4")
            plt.xlabel("Sample number")
            #plt.tight_layout(rect=[0.00, 0.03, 1, 0.95])
            plt.legend()
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