import { ClientTypes, IncomingMessage, IncomingMessageTypes, ConnectMessage, ResultMessage, SettingsMessage, ErrorMessage } from '../../communication/incomingMessages';
import { Log, LogMessage } from './log';

export class WebSocketClient {
    public ws: WebSocket;
    public log: Log;
    public onResult: (msg: ResultMessage) => void;
    public onSettings: (msg: SettingsMessage) => void;

    constructor(serverAddress: string) {
        this.ws = new WebSocket(serverAddress);
        this.log = new Log();
        this.initSocket();
    }

    private initSocket() {
        let that = this;

        this.ws.onopen = (event: Event) => {
            let msg = new ConnectMessage(ClientTypes.GUI);
            that.ws.send(JSON.stringify(msg));
            that.log.addMessage(new LogMessage("Connect", "Logging into ws server as GUI client"));
        }

        this.ws.onmessage = (event) => {
            let msg: IncomingMessage = JSON.parse(event.data);

            switch (msg.type) {
                case IncomingMessageTypes.Result:
                    let resMsg: ResultMessage = <ResultMessage>msg;
                    that.log.addMessage(new LogMessage("Result",
                        `Obtained results: ${JSON.stringify(resMsg.roots[0].pos)}, ${JSON.stringify(resMsg.roots[1].pos)} \r\n
                         Chosen root idx: ${resMsg.chosenRootId}`));
                    if (that.onResult !== undefined)
                        that.onResult(resMsg);
                    break;
                case IncomingMessageTypes.Settings:
                    let setMsg: SettingsMessage = <SettingsMessage>msg;
                    that.log.addMessage(new LogMessage(
                        "Received Current Settings",
                        `Settings present in Python script, receivers: ${JSON.stringify(setMsg.receivers)}, Sampling Rate: ${setMsg.samplingRate}`
                    ));
                    if (that.onSettings !== undefined)
                        that.onSettings(setMsg);
                    break;
                case IncomingMessageTypes.Error:
                    let errMsg: ErrorMessage = <ErrorMessage>msg;
                    that.log.addMessage(new LogMessage(
                        'Error occured !',
                        `Message: ${errMsg.msg}`
                    ));
                    break;
                default:
                    that.log.addMessage(new LogMessage(
                        'Error, not recognized message type',
                        `Message: ${JSON.stringify(msg)}`
                    ));
            }

        }

        this.ws.onclose = (event) => {
            that.log.addMessage(new LogMessage("Connection Closed", "Ws connection between client and server has been closed"));

        }

        this.ws.onerror = (event: Event) => {
            that.log.addMessage(new LogMessage("Error Occured", JSON.stringify(event)));
        }

    }

}

