import sys
from twisted.python import log
from localizator.sensor_matrix import SensorMatrix
from localizator.connection import Connection, App

sensorMat = SensorMatrix([
    (0.0, 0.0, 0.72),
    (0.0, 1.11, 1.0),
    (1.15, 1.11, 0.72),
    (1.14, 0.0, 0.72)
], debug=True)


def __main__():
    log.startLogging(sys.stdout)
    App.onSimulate = sensorMat.simulate_wave_propagation
    App.onSettings = sensorMat.update_receiver_pos
    connection = Connection()
    connection.run()


def test():
    sensorMat.start_cont_localization(input_src="wav", filename="samples/finalTest06amp.wav")

#__main__()

test()