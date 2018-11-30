import numpy as np
import serial
import struct
from bisect import bisect_left
from typing import Tuple, List
from localizator.receiver import Receiver
from localizator.dft import DFT
from localizator.MLE import MLE
from localizator.math_tools import gcc_phat


class SensorMatrix(object):

    class InvalidInput(Exception):
        pass

    def __init__(self,
                 receiver_coords: List[Tuple[float, float, float]],
                 reference_rec_id: int = 0,
                 rec_buff_size: int = 4096,
                 sampling_freq: int = 41666,
                 data_chunk: int = 2048,
                 debug: bool = False):

        receivers: List[Receiver] = [Receiver(rec[0], rec[1], rec[2], buffer_size=rec_buff_size)
                                     for rec in receiver_coords]

        self._mle_calc = MLE(receivers, reference_rec_id=reference_rec_id)
        self._dft = DFT(data_chunk, sampling_freq)
        self._rec_dft_buff = np.array()
        self._serial_settings = {
            "channelNr": 3,
            "port": '/dev/ttyACM0',
            "baud": 1000,
            "timeout": 1,
            "resultSize_bytes": 2
        }
        self._recognition_settings = {
            "lowSpectrum": 8000,
            "highSpectrum": 14000,
            "minPart": 0.25,
            "noiseFloor": 10000
        }
        self.debug = debug

    def start_cont_localization(self):
        byte_count = self._serial_settings["channelNr"] * self._dft.dft_size * self._serial_settings["resultSize_bytes"]
        Receiver.isSimulation = False

        with serial.Serial(self._serial_settings["port"],
                           self._serial_settings["baud"],
                           timeout=self._serial_settings["timeout"]) as ser:
            while ser.is_open:
                input_bytes = ser.read(byte_count)
                byte_len = len(input_bytes)
                frames: List[int] = struct.unpack("{}h".format(byte_len // self._serial_settings["resultSize_bytes"]),
                                                  input_bytes)
                recs = self._mle_calc.receivers
                for ch_id in range(0, self._serial_settings["channelNr"]):
                    recs[ch_id].data_buffer.append(frames[ch_id::self._serial_settings["channelNr"]])
                last_id = len(recs[0].data_buffer) - 1

                self._rec_dft_buff = self._dft.transform(recs[0].data_buffer.pop())

                is_event = self.is_event_detected(self._rec_dft_buff)

                if is_event:
                    print("Event!")
                    # find TdoA
                    self.calculate_tdoa(self._rec_dft_buff)
                    # calculate src
                    res = self.estimate_src_position()
                    print("calculation result:{}".format(res))
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

    def is_event_detected(self, dft_signal: np.ndarray) -> bool:
        """Detects if the ping pong ball hit was registered. This is done in a simple fashion by taking into account
           only frequencies from certain range specified in recognition settings and checking if the the total magnitude
           from this range exceeds the threshold in regards of the whole signal. Furthermore noise floor is considered
           and signals with lower total magnitude across all frequencies are ignored"""

        spectrum = self._dft.get_spectrum(dft_signal)
        pos_l = bisect_left(spectrum[0], self._recognition_settings["lowSpectrum"])
        pos_h = bisect_left(spectrum[0], self._recognition_settings["highSpectrum"])

        freq_s = sum(spectrum[1])
        high_f = sum(spectrum[1][pos_l:pos_h:]) / freq_s
        if high_f >= self._recognition_settings["minPart"] and freq_s > self._recognition_settings["noiseFloor"]:
            if self.debug:
                import matplotlib.pyplot as plt
                print("Match")
                print("high ratio:{} sigLvl: {}".format(high_f, freq_s))
                plt.plot(spectrum[0], spectrum[1], 'b.-', label='Hann filtered')
                plt.show()
            return True

        return False

    def calculate_tdoa(self, dft_sig_reference: np.ndarray):
        """Calculates TDoA between all receivers and reference one in the sensor matrix. Results are stored within
           receiver object"""

        recs = self._mle_calc.receivers

        for rec_idx in range(0, self._serial_settings["channelNr"]):
            if rec_idx == self._mle_calc.ref_rec:
                continue
            delay, hist = gcc_phat(recs[rec_idx].data_buffer.pop(), dft_sig_reference, phat=True,
                                   delay_in_seconds=True, buffered_dft=True)
            recs[rec_idx].tDoA = delay

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