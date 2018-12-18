from typing import Tuple
import numpy as np
import json
from collections import deque


class Receiver(object):
    """Class models the receiver in the microphone array and provides interface for the simulation"""

    srcX: np.float64 = -10.0
    srcY: np.float64 = -10.0
    srcZ: np.float64 = -10.0

    c: np.float64 = 340.0  # m/x

    isSimulation: bool = False

    def __init__(self, pos_x: np.float64, pos_y: np.float64, pos_z: np.float64, is_reference: bool = False,
                 buffer_size: int = 3, received_time: np.longfloat = 0):

        self._pos_x, self._pos_y, self._pos_z = pos_x, pos_y, pos_z
        self._isReference = is_reference
        self._received_time: np.float64 = np.float64(received_time)
        # public TDOA time variable between this microphone and reference one
        self.tDoA: float = 0.0

        self.receive()
        self.data_buffer = [] # deque(maxlen=buffer_size)

    @property
    def is_reference(self) -> bool:
        return self._isReference

    @is_reference.setter
    def is_reference(self, is_ref: bool):
        self._isReference = is_ref

    @property
    def position(self) -> np.ndarray:
        """Return the current position of the receiver (x,y,z)"""

        return np.array([self._pos_x, self._pos_y, self._pos_z])

    @position.setter
    def position(self, pos: Tuple[float, float, float]) -> None:
        """Sets the position of the receiver (x,y,z)"""

        self._pos_x, self._pos_y, self._pos_z = pos[0], pos[1], pos[2]

    def dist(self, other: 'Receiver') -> np.float:
        """Expresses the distance between two microphones in terms of TDoA between them"""
        if Receiver.isSimulation:
            return (self._received_time - other._received_time) * Receiver.c
        return self.tDoA * Receiver.c

    def calc_k(self) -> float:
        return self._pos_x ** 2 + self._pos_y ** 2 + self._pos_z ** 2

    def receive(self) -> None:
        """Simulates the the received time offset, based on src position class variables"""

        src = Receiver.get_source_position()
        self._received_time = np.round(np.linalg.norm(self.position - src) / Receiver.c, 6)  # seconds

    @property
    def json(self) -> str:
        obj = {
            "x": self._pos_x,
            "y": self._pos_y,
            "z": self._pos_z,
            "isReference": self._isReference
        }
        return json.dumps(obj)

    @classmethod
    def set_source_position(cls, src_position: Tuple[float, float, float] = (srcX, srcY, srcZ)):
        """Sets the source position coordinates for the simulation purposes"""

        cls.srcX, cls.srcY, cls.srcZ = src_position[0], src_position[1], src_position[2]

    @classmethod
    def get_source_position(cls) -> Tuple[float, float, float]:
        """Returns source position coordinates, simulation only !"""
        return cls.srcX, cls.srcY, cls.srcZ