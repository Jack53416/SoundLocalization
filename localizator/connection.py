from enum import Enum
from typing import Tuple, List, Callable

from twisted.internet.protocol import ReconnectingClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol, WebSocketClientFactory
from twisted.internet import reactor
import json
import threading
from localizator.receiver import Receiver
from localizator.MLE import MLE


class Messages:

    @staticmethod
    def connect():
        msg = {
            "type": "Connect",
            "clientType": "Worker"
        }
        return json.dumps(msg).encode('utf-8')

    @staticmethod
    def settings(receivers: List[Receiver]) -> str:
        msg = {
            "type": "Settings",
            "receivers": [rec.json for rec in receivers]
        }
        return json.dumps(msg).encode('utf-8')

    @staticmethod
    def result(root1: Tuple[float, float, float], root2: Tuple[float, float, float], root_idx: int):
        msg = {
            "type": "Result",
            "roots":[
                {"pos": {"x": root1[0], "y": root1[1], "z": root1[2]}},
                {"pos": {"x": root2[0], "y": root2[1], "z": root2[2]}}
            ],
            "chosenRootId": root_idx
        }
        return json.dumps(msg).encode('utf-8')

    @staticmethod
    def error(err_msg: str):
        msg = {
            "type": "Error",
            "msg": err_msg
        }
        return json.dumps(msg).encode("utf-8")


server = "10.128.99.64"  # Server IP Address or domain eg: tabvn.com
port = 8081  # Server Port


class App:

    onSettings: Callable[[List[Tuple[float, float, float]], int], None] = None
    onSimulate: Callable[[Tuple[float, float, float]], List[Tuple[float, float, float]]] = None
    on_settings_req: Callable[[], None] = None
    on_result_ready: Callable[[], None] = None


class AppProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Connected to the server")
        self.factory.resetDelay()

    def onOpen(self):
        print("Connection is open")
        self.sendMessage(Messages.connect(), isBinary=False)

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Got Binary message {0} bytes".format(len(payload)))
        else:
            msg = payload.decode('utf8')
            print("Got Text message from the server {0}".format(msg))
            try:
                self.decode_message(payload.decode('utf8'))
            except KeyError as ex:
                print("Message: {0}\nis invalid!".format(msg))
                self.sendMessage(Messages.error("Invalid Message !"))
            except MLE.InvalidInput as ex:
                print(str(ex))
                self.sendMessage(Messages.error(str(ex)))


    def onClose(self, wasClean, code, reason):
        print("Connect closed {0}".format(reason))

    def decode_message(self, msg: str):
        obj = json.loads(msg)
        if obj["type"] == "Simulate":
            src = obj["simSource"]
            pos = (src["pos"]["x"], src["pos"]["y"], src["pos"]["z"])
            print(pos)
            if App.onSimulate:
                res = App.onSimulate(pos)
                self.sendMessage(Messages.result(res[0], res[1], 0))

        elif obj["type"] == "Settings":
            rec_settings = obj["receivers"]
            positions = []
            ref_idx = 0
            for [idx, rec] in enumerate(rec_settings):
                positions.append((rec["pos"]["x"], rec["pos"]["y"], rec["pos"]["z"]))
                if rec["isReference"]:
                    ref_idx = idx

            if App.onSettings:
                App.onSettings(positions, ref_idx)


class AppFactory(WebSocketClientFactory, ReconnectingClientFactory):
    protocol = AppProtocol

    def clientConnectionFailed(self, connector, reason):
        self.retry(connector)

    def clientConnectionLost(self, connector, unused_reason):
        self.retry(connector)


class Connection():
    def __init__(self):
        super(Connection, self).__init__()
        self.factory = AppFactory(u"ws://{0}".format(server).format(":").format(port))

    def run(self):
        reactor.connectTCP(server, port, self.factory)
        reactor.run()

    def send(self, msg):
        self.factory.protocol.sendMessage(msg, isBinary=False)


def __test():
    import sys
    from twisted.python import log
    log.startLogging(sys.stdout)
    connection = Connection()
    #  connection.daemon = True
    connection.run()

# __test()
