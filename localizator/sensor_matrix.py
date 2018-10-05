import numpy as np
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
                 data_chunk: int = 1024):
        receivers: List[Receiver] = [Receiver(rec[0], rec[1], rec[2], buffer_size=rec_buff_size)
                                     for rec in receiver_coords]

        self._mle_calc = MLE(receivers, reference_rec_id=reference_rec_id)
        self._gcc_dft = DFT(data_chunk, sampling_freq)

    def start_cont_localization(self):
        pass

    def update_receiver_pos(self, positions: List[Tuple[float, float, float]], ref_id: int = 0):
        if len(positions) > len(self._mle_calc.receivers):
            raise SensorMatrix.InvalidInput("Too large position array to update only 4 receiver location!")

        for [idx, pos] in enumerate(positions):
            self._mle_calc.receivers[idx].position = pos

        self._mle_calc.ref_rec = ref_id

    def get_raw_data(self):
        pass

    def is_event_detected(self) -> bool:
        pass

    def calculate_tdoa(self):
        pass

    def estimate_src_position(self) -> Tuple[float, float, float]:
        pass

    def simulate_wave_propagation(self, src_pos: Tuple[float, float, float]) -> List[np.ndarray]:
        Receiver.set_source_position(src_pos)
        Receiver.isSimulation = True
        for rec in self._mle_calc.receivers:
            rec.receive()
        r1 = self._mle_calc.calculate()
        r2 = self._mle_calc.get_other_solution()
        r1 = np.squeeze(np.asarray(r1))
        r2 = np.squeeze(np.asarray(r2))
        return [r1, r2]
