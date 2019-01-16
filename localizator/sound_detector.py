from typing import Tuple, List
from collections import deque
import numpy as np


class SoundDetector:
    def __init__(self, release_factor: float, buffer_size: int):
        self.envelope = 0.0
        self.release_factor = release_factor
        self.is_above_threshold = False
        self.start_idx = -1
        self.end_idx = -1
        self.events: List[Tuple[int, int, int]] = []
        self.star_mic_id = 0
        self.env_history = deque(maxlen=buffer_size)

    def detect_sound(self, signal: np.ndarray, upper_treshold: float, lower_treshold:float,
                     data_offset = 0, mic_id = 0):

        for idx in range(data_offset, len(signal)):
            self.envelope *= self.release_factor
            self.envelope = max(abs(signal[idx]), self.envelope)
            self.env_history.append(self.envelope)

            if self.envelope > upper_treshold and not self.is_above_threshold:
                self.is_above_threshold = True
                self.start_idx = idx
                self.star_mic_id = mic_id

            elif self.envelope <= lower_treshold and self.is_above_threshold:
                self.is_above_threshold = False
                self.end_idx = idx
                self.events.append((self.start_idx, self.end_idx, self.star_mic_id))
                self.reset_indexes()

        if self.start_idx > 0:
            self.start_idx -= data_offset

    def reset_indexes(self):
        self.start_idx = -1
        self.end_idx = -1
