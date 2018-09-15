from typing import Tuple, List
from receiver import Receiver
from dft import DFT


class SensorMatrix(object):

    def __init__(self,
                 receiver_coords: List[Tuple[float, float, float]],
                 reference_rec_id: int = 0,
                 rec_buff_size: int = 4096,
                 sampling_freq: int = 41666,
                 data_chunk: int = 1024):

        self._receivers: List[Receiver] = [Receiver(rec[0], rec[1], rec[2], buffer_size=rec_buff_size)
                                           for rec in receiver_coords]
        self._reference_rec_id = reference_rec_id
        self._gcc_dft = DFT(data_chunk, sampling_freq)

    def get_raw_data(self):
        pass

    def is_event_detected(self) -> bool:
        pass

    def calculate_tdoa(self):
        pass

    def estimate_src_position(self) -> Tuple[float, float, float]:
        pass
