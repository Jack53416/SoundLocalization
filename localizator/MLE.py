from typing import List, Callable
from enum import Enum

from matplotlib import gridspec
from scipy.optimize import fsolve

from localizator.receiver import Receiver

import numpy as np
import matplotlib.pyplot as plt
# noinspection PyUnresolvedReferences
from mpl_toolkits.mplot3d import Axes3D
from uncertainties import unumpy as unp
from uncertainties import umath


class MLE(object):
    class Mode(Enum):
        MLE_MINUS = 0
        MLE_PLUS = 1
        MLE_HLS = 2

    class CalcMode(Enum):
        MLE_SOLVER = 0,
        MLE_COMPUTATION = 1

    class InvalidInput(Exception):
        pass

    def __init__(self, receivers: List[Receiver], src_conditions:Callable[[np.ndarray], bool] = None,
                 reference_rec_id: int = 0, mode: Mode = Mode.MLE_HLS):

        if receivers is None:
            receivers = []

        if len(receivers) != 4:
            raise MLE.InvalidInput("4 receivers required for a computation")

        if len(receivers) - 1 < reference_rec_id < 0:
            raise MLE.InvalidInput("Reference receiver id of {} is invalid!".format(reference_rec_id))

        if not isinstance(mode, Enum):
            raise MLE.InvalidInput("Mode is not instance of MLE.Mode enum class")

        self.condition_fun = src_conditions
        self._receivers = receivers
        self._refRec = receivers[reference_rec_id]
        self._refRec.is_reference = True

        self._posMatrix = None  # -inv(C) matrix
        self._refRec_k = None
        self._estimatedPositions = []
        self._chosenRootIdx = None
        self._mode = mode

        self._k_dist_matrix: np.matrix = None
        self._dist_matrix: np.matrix = None
        self._d_ref = None

        self.__setup_constants()

    @property
    def receivers(self) -> List[Receiver]:
        return self._receivers

    @property
    def root_idx(self):
        return self._chosenRootIdx

    @property
    def ref_rec(self):
        return self._refRec

    @ref_rec.setter
    def ref_rec(self, ref_idx: int):
        if len(self._receivers) - 1 < ref_idx < 0:
            raise MLE.InvalidInput("Reference receiver id of {} is invalid!".format(ref_idx))
        self.ref_rec.is_reference = False
        self._refRec = self._receivers[ref_idx]
        self._refRec.is_reference = True
        self.__setup_constants()

    def __setup_constants(self) -> None:

        """Initializes constants:
           position Matrix - C = [x2 - x1, y2 - y1, z2 - z1
                                  x3 - x1, y3 - y1, z3 - z1
                                  x4 - x1, y4 - y1, z4 - z1]
           K = xi^2 + yi^2 + zi^2"""

        self._posMatrix = np.array([rec.position - self._refRec.position
                                    for rec in self._receivers if rec != self._refRec], object)

        self._posMatrix = unp.umatrix(unp.nominal_values(self._posMatrix), unp.std_devs(self._posMatrix))
        try:
            self._posMatrix = -self._posMatrix.I

        except np.linalg.LinAlgError:
            raise MLE.InvalidInput("The receiver positions create singular matrix, which cannot be inversed")

        self._refRec_k = self._refRec.calc_k()

    def __apply_hls_of(self) -> np.ndarray:
        """Evaluates OF function for src positions returned by MLE equation, solution with
           lowest OF value is returned"""

        src_positions_err = [self.__calc_src(D).flatten() for D in self._d_ref]
        src_positions = np.around(unp.nominal_values(src_positions_err), 2)
        of_solutions = np.array([0.0, 0.0], np.float64)
        d = [np.linalg.norm(unp.nominal_values(rec.position) - src_pos) for rec in self._receivers for src_pos in src_positions]
        d = [d[0::2], d[1::2]]

        if Receiver.isSimulation:
            for i in range(1, len(self.receivers)):
                self.receivers[i].tDoA = np.around(self.receivers[i]._received_time - self.receivers[0]._received_time,
                                                   Receiver.decimal_num)

        for i in range(1, len(self._receivers)):
            of_solutions[0] += (d[0][i] - d[0][0] - unp.nominal_values(self.receivers[i].tDoA) * Receiver.c) ** 2
            of_solutions[1] += (d[1][i] - d[1][0] - unp.nominal_values(self.receivers[i].tDoA) * Receiver.c) ** 2

        self._estimatedPositions = src_positions
        self._chosenRootIdx = np.argmin(of_solutions)

        if self.condition_fun is not None:
            user_cond_met = [self.condition_fun(res.flatten()) for res in self._estimatedPositions]
            if user_cond_met[0] and not user_cond_met[1]:
                self._chosenRootIdx = np.argwhere(user_cond_met)

        result = src_positions_err[int(self._chosenRootIdx)]
        result = unp.uarray(np.around(unp.nominal_values(result), 2), np.around(unp.std_devs(result), 2))
        return result

    def __calc_src(self, d: np.float64) -> np.ndarray:
        """Applies the matrix equation for source coordinates, assuming known d - distance between the reference
           receiver(usually 1) and the source"""

        return self._posMatrix * (self._dist_matrix * d + self._k_dist_matrix)

    def __mle_distance_equation(self, d: np.float64) -> np.float64:
        """Realizes 4-th equation for d - distance between the reference receiver and the source,
           utilized in the equation solver to provide next steps for further iterations"""

        src = self.__calc_src(d)
        x_s, y_s, z_s = src[0], src[1], src[2]
        ref_pos = self._refRec.position

        return -d ** 2 + x_s ** 2 + y_s ** 2 + z_s ** 2 - 2 * x_s * ref_pos[0] - 2 * y_s * ref_pos[1] \
               - 2 * z_s * ref_pos[2] + self._refRec_k

    def calculate(self, calc_mode: CalcMode = CalcMode.MLE_COMPUTATION) -> np.ndarray:
        """Performs all the calculations for the source position, returns best guess of the source location (x,y,z)"""

        # R matrix
        self._k_dist_matrix = 0.5 * np.matrix([[rec.dist(self._refRec) ** 2 - rec.calc_k() + self._refRec_k]
                                                for rec in self._receivers if rec != self._refRec], object)

        # V matrix
        self._dist_matrix = np.array([[rec.dist(self._refRec)] for rec in self._receivers if rec != self._refRec],
                                     object)

        self._k_dist_matrix = unp.umatrix(unp.nominal_values(self._k_dist_matrix), unp.std_devs(self._k_dist_matrix))

        self._dist_matrix = unp.umatrix(unp.nominal_values(self._dist_matrix), unp.std_devs(self._dist_matrix))

        if calc_mode == MLE.CalcMode.MLE_SOLVER:
            self._d_ref = fsolve(lambda d: self.__mle_distance_equation(d), np.array([-40, 40]))
        else:
            n_mat = self._posMatrix * self._dist_matrix
            r_mat = self._posMatrix * self._k_dist_matrix
            a = n_mat.transpose() * n_mat - 1

            b = 2 * (n_mat.transpose() * r_mat - n_mat.transpose() * self.ref_rec.position.transpose())
            c = -2 * self.ref_rec.position * r_mat + r_mat.transpose() * r_mat + self._refRec_k

            delta_sqr = umath.sqrt(abs((b ** 2 - 4 * a * c)[0,0]))
            self._d_ref = [(-b - delta_sqr) / (2 * a), (-b + delta_sqr) / (2 * a)]

        if self._mode == self.Mode.MLE_HLS:
            return self.__apply_hls_of()

        elif self._mode == self.Mode.MLE_PLUS:
            return self.__calc_src(np.float64(max(self._d_ref))).flatten()

        return self.__calc_src(np.float64(min(self._d_ref))).flatten()

    def get_other_solution(self) -> np.ndarray:
        """Returns remaining solution of MLE equation"""

        if self._chosenRootIdx == 0:
            return self._estimatedPositions[1]
        return self._estimatedPositions[0]


class PerformanceTest(object):
    """Setups the performance test for localization algorithm. Sources are placed inside a cuboid of dimensions:
       x_range x y_range x z_range with a step of delta. Then the propagation is simulated and source positions are
       recalculated by algorithm.

       One can choose between MLE- or MLE+ solution or get one chosen by HLS function.
       If all_roots are set to true, the simulation takes into account both solutions.
       Additionally computation mode can be chosen: either using iterative solver, or by solving quadratic equation
       manually"""

    def __init__(self, x_range: float = 20, y_range: float = 20, z_range: float = 20, delta: float = 0.1,
                 all_roots: bool = False, mle_mode: MLE.Mode = MLE.Mode.MLE_HLS,
                 mle_calc_mode: MLE.CalcMode = MLE.CalcMode.MLE_COMPUTATION):

        self.delta = delta
        self.xRange, self.yRange, self.zRange = x_range, y_range, z_range

        receivers = [
            Receiver(np.float64(-1.5), np.float64(-1.5), np.float64(-1.5)),
            Receiver(np.float64(-1.5), np.float64(1.5), np.float64(1.5)),
            Receiver(np.float64(1.5), np.float64(1.5), np.float64(-1.5)),
            Receiver(np.float64(1.5), np.float64(-1.5), np.float64(-1.5))
        ]
        self.localizer = MLE(receivers, mode=mle_mode)
        self.mle_calc_mode = mle_calc_mode

        self.xStart, self.yStart, self.zStart = -x_range / 2, -y_range / 2, -z_range / 2

        self.gAccuracy = []  # err <= 0.05
        self.mAccuracy = []  # err <= 0.2
        self.pAccuracy = []  # err <= 1
        self.bAccuracy = []  # err > 1

        self.allRoots = all_roots
        self.captions = []
        self.percentage = 0.0

    def execute(self) -> None:
        """Performs the actual simulation in the cuboid"""

        for xPos in np.around(np.arange(self.xStart, self.xStart + self.xRange + self.delta, self.delta), 2):
            # change X pos
            print(xPos)
            for yPos in np.around(np.arange(self.yStart, self.yStart + self.yRange + self.delta, self.delta), 2):
                # change Y pos
                for zPos in np.around(np.arange(self.zStart, self.zStart + self.zRange + self.delta, self.delta),2):
                    # change Z pos
                    self.setup_source_position(xPos, yPos, zPos)
                    pos = self.localizer.calculate(self.mle_calc_mode)
                    # print(pos)
                    self.asses_accuracy(pos)

    def setup_source_position(self, x_pos: float, y_pos: float, z_pos: float) -> None:
        """Places source in new location, specified by arguments, and simulates the sound propagation"""

        Receiver.set_source_position((x_pos, y_pos, z_pos))
        for rec in self.localizer._receivers:
            rec.receive()

    def asses_accuracy(self, calc_src_position: np.ndarray) -> None:
        """Computes the accuracy of the position obtained with algorithm and qualifies it into several tiers:
           good, medium, poor, bad"""

        actual_pos = Receiver.get_source_position()
        err = np.linalg.norm(calc_src_position - actual_pos)

        if self.allRoots:
            err2 = np.linalg.norm(self.localizer.get_other_solution() - actual_pos)
            err = min(err, err2)

        if err <= 0.05:
            self.gAccuracy.append(tuple(actual_pos))
        elif err <= 0.2:
            self.mAccuracy.append(tuple(actual_pos))
        elif err <= 1.0:
            self.pAccuracy.append(tuple(actual_pos))
        else:
            self.bAccuracy.append(tuple(actual_pos))

    def plot(self) -> None:
        """Plots the obtained accuracy visually in 3d space in the cuboid, marking colors with respective accuracy
           tiers. File is saved on the hard drive - mle_performance.png"""

        plt.figure(figsize=(8, 6))
        gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        ax0 = plt.subplot(gs[0], projection='3d')
        g_accuracy = np.array(self.gAccuracy)
        m_accuracy = np.array(self.mAccuracy)
        p_accuracy = np.array(self.pAccuracy)
        b_accuracy = np.array(self.bAccuracy)

        if len(g_accuracy) > 0:
            ax0.scatter(g_accuracy[:, 0], g_accuracy[:, 1], g_accuracy[:, 2], c='g', marker='o')
        if len(m_accuracy) > 0:
            ax0.scatter(m_accuracy[:, 0], m_accuracy[:, 1], m_accuracy[:, 2], c='y', marker='o')
        if len(p_accuracy) > 0:
            ax0.scatter(p_accuracy[:, 0], p_accuracy[:, 1], p_accuracy[:, 2], c='orange', marker='o')
        if len(b_accuracy) > 0:
            ax0.scatter(b_accuracy[:, 0], b_accuracy[:, 1], b_accuracy[:, 2], c='r', marker='o')

        ax0.set_xlabel('X[m]')
        ax0.set_ylabel('Y[m]')
        ax0.set_zlabel('Z[m]')

        ax0.xaxis.labelpad = 20
        ax0.yaxis.labelpad = 20
        ax0.zaxis.labelpad = 20

        self.calc_stats()
        ax1 = plt.subplot(gs[1])
        explode = (0.1, 0, 0, 0)
        labels = ['{0} - {1:1.2f} %'.format(i, j) for i, j in zip(self.captions, self.percentage)]

        patches, text = ax1.pie(self.percentage, explode=explode, shadow=True, startangle=90,
                                colors=['g', 'y', 'orange', 'r'])

        patches, labels, dummy = zip(*sorted(zip(patches, labels, self.percentage),
                                             key=lambda x: x[2],
                                             reverse=True))

        ax1.legend(patches, labels, loc='lower center', bbox_to_anchor=(0.5, 0.1),
                   fontsize=8)

        ax1.axis('equal')

        plt.tight_layout()
        #plt.show()
        plt.savefig('mle_performance.png', transparent=True)

    def calc_stats(self) -> None:
        """Calculates exact percentages for each tier of accuracy"""

        self.captions = ["err <= 0.01m", "0.01m < err <= 0.2m", "0.2m < err <= 1.0 m", "err > 1.0m"]
        lengths = np.array([len(self.gAccuracy), len(self.mAccuracy), len(self.pAccuracy), len(self.bAccuracy)])
        total = sum(lengths)
        self.percentage = np.round(lengths / total * 100, 5)
        # print(dict(zip(captions, percentage)))


def __test_mle():
    rec1 = Receiver(np.float64(-1.18 / 2), np.float64(-1.11 / 2), np.float64(0.72))
    rec2 = Receiver(np.float64(-1.18 / 2), np.float64(1.11 / 2), np.float64(1.0))
    rec3 = Receiver(np.float64(1.15 - 1.18/2), np.float64(1.11 / 2), np.float64(0.72))
    rec4 = Receiver(np.float64(1.14 - 1.18/2), np.float64(-1.11 / 2), np.float64(0.72))

    m = MLE(receivers=[rec1, rec2, rec3, rec4])
    res = m.calculate()

    print(res)


def __full_performance_test():
    Receiver.isSimulation = True
    p = PerformanceTest(4, 4, 0, 0.1, all_roots=False, mle_mode=MLE.Mode.MLE_HLS,
                        mle_calc_mode=MLE.CalcMode.MLE_COMPUTATION)
    p.execute()
    p.plot()
