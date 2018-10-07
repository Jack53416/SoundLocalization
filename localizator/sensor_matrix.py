import numpy as np
import serial
import struct
from bisect import bisect_left
from typing import Tuple, List
from localizator.receiver import Receiver
from localizator.dft import DFT
from localizator.MLE import MLE


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
        self._gcc_dft = DFT(2 * data_chunk, sampling_freq)
        self._rec_dft = DFT(data_chunk, sampling_freq)
        self._serial_settings = {
            "channelNr": 3,
            "port": '/dev/ttyACM0',
            "baud": 1000,
            "timeout": 1
        }
        self._recognition_settings = {
            "lowSpectrum": 8000,
            "highSpectrum": 14000,
            "minPart": 0.25,
            "noiseFloor": 10000
        }
        self.debug = debug

    def start_cont_localization(self):
        with serial.Serial(self._serial_settings["port"],
                           self._serial_settings["baud"],
                           timeout=self._serial_settings["timeout"]) as ser:
            input_bytes = ser.read(4096 * 3)
            while ser.is_open:
                byte_len = len(input_bytes)
                frames: List[int] = struct.unpack("{}h".format(byte_len // 2), input_bytes)
                recs = self._mle_calc.receivers
                for ch_id in range(0, self._serial_settings["channelNr"]):
                    recs[ch_id].data_buffer.append(frames[ch_id::4])
                last_id = len(recs[0].data_buffer) - 1

                is_event = self.is_event_detected(recs[0].data_buffer[last_id])

                if is_event:
                    # find TdoA
                    # calculate src
                    # send to server
                    print("Event!")

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

    def is_event_detected(self, signal: np.ndarray) -> bool:
        """Detects if the ping pong ball hit was registered. This is done in a simple fashion by taking into account
           only frequencies from certain range specified in recognition settings and checking if the the total magnitude
           from this range exceeds the threshold in regards of the whole signal. Furthermore noise floor is considered
           and signals with lower total magnitude across all frequencies are ignored"""

        spectrum = self._rec_dft.amplitude_spectrum(signal)
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

    def calculate_tdoa(self):
        pass

    def estimate_src_position(self) -> Tuple[float, float, float]:
        pass

    def simulate_wave_propagation(self, src_pos: Tuple[float, float, float]) -> List[np.ndarray]:
        """Simulates the propagation of the sound from given src points and based on time differences, recalculates
           the position of the sound"source. Returns both roots found during the process, with first one being chosen
            by the algorithm as the correct one"""

        Receiver.set_source_position(src_pos)
        Receiver.isSimulation = True
        for rec in self._mle_calc.receivers:
            rec.receive()
        r1 = self._mle_calc.calculate()
        r2 = self._mle_calc.get_other_solution()
        r1 = np.squeeze(np.asarray(r1))
        r2 = np.squeeze(np.asarray(r2))
        return [r1, r2]