import numpy as np
import serial
import struct
from bisect import bisect_left
from typing import Tuple, List
from localizator.receiver import Receiver
from localizator.dft import DFT
from localizator.MLE import MLE
from localizator.math_tools import gcc_phat, running_mean


class SensorMatrix(object):

    class InvalidInput(Exception):
        pass

    def __init__(self,
                 receiver_coords: List[Tuple[float, float, float]],
                 reference_rec_id: int = 0,
                 rec_buff_size: int = 4096,
                 sampling_freq: int = 41666,
                 data_chunk: int = 4096,
                 debug: bool = False):

        receivers: List[Receiver] = [Receiver(rec[0], rec[1], rec[2], buffer_size=rec_buff_size)
                                     for rec in receiver_coords]

        self._mle_calc = MLE(receivers, reference_rec_id=reference_rec_id)
        self._dft = DFT(data_chunk, sampling_freq)
        self._rec_dft_buff = np.array([])
        self._serial_settings = {
            "channelNr": 4,
            "port": '/dev/ttyACM0',
            "baud": 2000000,
            "timeout": 1,
            "resultSize_bytes": 2
        }
        self._recognition_settings = {
            "lowSpectrum": 10000,
            "highSpectrum": 15000,
            "minPart": 0.05,
            "noiseFloor": 5000
        }
        self.debug = debug
        self._memory_buff = []
        self._mem_buff_limit = 100000
        self._evt_chunk_idxs = []

    def start_cont_localization(self, input_src: str ="serial", filename="input.wav"):
        byte_count = self._serial_settings["channelNr"] * self._dft.dft_size * self._serial_settings["resultSize_bytes"]
        Receiver.isSimulation = False

        if input_src == "wav":
            import wave

            with wave.open(filename, "rb") as wav:
                self._dft.sampling_rate = wav.getframerate()
                self._serial_settings["channelNr"] = wav.getnchannels()
                length = wav.getnframes() // self._dft.size

                for [idx, i] in enumerate(range(0, length)):
                    input_bytes = wav.readframes(self._dft.size)
                    if self.localize(input_bytes) and self.debug:
                        self._evt_chunk_idxs.append(idx)
                if self.debug:
                    import matplotlib.pyplot as plt
                    plt.plot(self.remove_noise(self._memory_buff), 'b.-')
                    for idx in self._evt_chunk_idxs:
                        plt.axvspan(idx * self._dft.size, (idx + 1) * self._dft.size - 1,
                                    facecolor='#2ca02c', alpha=0.5)
                    plt.show()

        else:
            with serial.Serial(self._serial_settings["port"],
                               self._serial_settings["baud"],
                               timeout=self._serial_settings["timeout"]) as ser:
                while ser.is_open:
                    input_bytes = ser.read(byte_count)
                    self.localize(input_bytes)

    def remove_noise(self, signal: np.ndarray, treshold = 2500):
        result = np.array(signal)
        tmp = np.abs(signal)
        tmp = running_mean(tmp, 15)
        for [idx, val] in enumerate(tmp):
            if val <= treshold:
                result[idx] = 0
        return result

    def localize(self, raw_data: bytes) -> bool:
        """Performs the whole localization process: check for searched signal, and if it is found calculate the
        src position, returns true if it was detected and false otherwise(for statistics)"""
        byte_len = len(raw_data)
        frames: List[int] = struct.unpack("{}h".format(byte_len // self._serial_settings["resultSize_bytes"]),
                                          raw_data)
        recs = self._mle_calc.receivers

        # Split data into separate channels
        for ch_id in range(0, self._serial_settings["channelNr"]):
            recs[ch_id].data_buffer = frames[ch_id::self._serial_settings["channelNr"]]

        self._rec_dft_buff = self._dft.transform(self._mle_calc.ref_rec.data_buffer)

        if self.debug and len(self._memory_buff) < self._mem_buff_limit:
            self._memory_buff += self._mle_calc.ref_rec.data_buffer

        is_event = self.is_event_detected(self._rec_dft_buff)

        if is_event:
            print("Event!")
            # find TdoA
            self.calculate_tdoa(self._rec_dft_buff)
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

    def is_event_detected(self, dft_signal: np.ndarray) -> bool:
        """Detects if the ping pong ball hit was registered. This is done in a simple fashion by taking into account
           only frequencies from certain range specified in recognition settings and checking if the the total magnitude
           from this range exceeds the threshold in regards of the whole signal. Furthermore noise floor is considered
           and signals with lower total magnitude across all frequencies are ignored"""

        spectrum = self._dft.get_spectrum(dft_signal)
        pos_l = bisect_left(spectrum[0], self._recognition_settings["lowSpectrum"])
        pos_h = bisect_left(spectrum[0], self._recognition_settings["highSpectrum"])

        freq_s = sum(spectrum[1])
        high_f = sum(spectrum[1][pos_l:pos_h:]) # / freq_s
        if high_f >= self._recognition_settings["noiseFloor"]:
            if self.debug:
                import matplotlib.pyplot as plt
                print("Match")
                print("high ratio:{} sigLvl: {}".format(high_f, freq_s))
                plt.plot(spectrum[0], spectrum[1], 'b.-', label='Hann filtered')
                plt.axvspan(1.25, 1.55, facecolor='#2ca02c', alpha=0.5)
                plt.show()
            return True

        return False

    def calculate_tdoa(self, dft_sig_reference: np.ndarray):
        """Calculates TDoA between all receivers and reference one in the sensor matrix. Results are stored within
           receiver object"""

        #self._mle_calc.ref_rec.data_buffer = self.remove_noise(self._mle_calc.ref_rec.data_buffer, 20000)
        recs = self._mle_calc.receivers

        for rec_idx in range(0, self._serial_settings["channelNr"]):
            if recs[rec_idx].is_reference:
                continue
          #  recs[rec_idx].data_buffer = self.remove_noise(recs[rec_idx].data_buffer, 20000)
            delay, hist = gcc_phat(recs[rec_idx].data_buffer, dft_sig_reference, self._dft, phat=True,
                                   delay_in_seconds=True, buffered_dft=True)
            if self.debug:
                print(delay * self._dft.sampling_rate)

            recs[rec_idx].tDoA = delay
        import matplotlib.pyplot as plt
        plt.subplot(311)
        plt.plot(recs[0].data_buffer, label="signal")
        plt.plot(recs[1].data_buffer, label="delayed")
        plt.subplot(312)
        plt.plot(recs[0].data_buffer, label="signal")
        plt.plot(recs[2].data_buffer, label="delayed")
        plt.subplot(313)
        plt.plot(recs[0].data_buffer, label="signal")
        plt.plot(recs[3].data_buffer, label="delayed")
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