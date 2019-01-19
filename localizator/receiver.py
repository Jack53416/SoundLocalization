from typing import Tuple
import numpy as np
import json
from collections import deque
from uncertainties import unumpy as unp
from uncertainties import ufloat
import itertools


class SliceDeck(deque):
    def __getitem__(self, index):
        try:
            return deque.__getitem__(self, index)
        except TypeError:
            return type(self)(itertools.islice(self, index.start, index.stop))


class Receiver(object):
    """Class models the receiver in the microphone array and provides interface for the simulation"""

    srcX: np.float64 = -10.0
    srcY: np.float64 = -10.0
    srcZ: np.float64 = -10.0
    c: np.float64 = 343.0  # m/x

    decimal_num: int = 5
    x_pos_err = 0.005
    y_pos_err = 0.005
    z_pos_err = 0.005

    isSimulation: bool = False

    def __init__(self, pos_x: np.float64, pos_y: np.float64, pos_z: np.float64, is_reference: bool = False,
                 buffer_size: int = 2 * 4096, received_time: np.longfloat = 0):

        self._pos_x, self._pos_y, self._pos_z = ufloat(pos_x, Receiver.x_pos_err), ufloat(pos_y, Receiver.y_pos_err), \
                                                ufloat(pos_z, Receiver.z_pos_err)
        self._isReference = is_reference
        self._received_time: np.float64 = np.float64(received_time)
        # public TDOA time variable between this microphone and reference one
        self.tDoA: float = 0.0

        self.receive()
        self.data_buffer = SliceDeck(maxlen=buffer_size)

    @property
    def is_reference(self) -> bool:
        return self._isReference

    @is_reference.setter
    def is_reference(self, is_ref: bool):
        self._isReference = is_ref

    @property
    def position(self) -> np.ndarray:
        """Return the current position of the receiver (x,y,z)"""
        pos = [self._pos_x, self._pos_y, self._pos_z]
        return unp.umatrix(unp.nominal_values(pos), unp.std_devs(pos))

    @position.setter
    def position(self, pos: Tuple[float, float, float]) -> None:
        """Sets the position of the receiver (x,y,z)"""

        self._pos_x, self._pos_y, self._pos_z = pos[0], pos[1], pos[2]

    def dist(self, other: 'Receiver') -> np.float:
        """Expresses the distance between two microphones in terms of TDoA between them"""
        if Receiver.isSimulation:
            return np.around((self._received_time - other._received_time) * Receiver.c, Receiver.decimal_num)
        return self.tDoA * Receiver.c

    def calc_k(self) -> float:
        return self._pos_x ** 2 + self._pos_y ** 2 + self._pos_z ** 2

    def receive(self) -> None:
        """Simulates the the received time offset, based on src position class variables"""
        src = Receiver.get_source_position()
        self._received_time = np.linalg.norm(unp.nominal_values(self.position) - src) / Receiver.c

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