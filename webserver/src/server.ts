import * as express from 'express';
import * as WebSocket from 'ws';
import * as http from 'http';
import * as path from 'path';
import { ClientTypes, IncomingMessage, IncomingMessageTypes, ConnectMessage, ResultMessage, SettingsMessage } from './communication/incomingMessages';
import { ErrorMessage, ErrorTypes } from './communication/errorMessages';

class ExtWebSocket extends WebSocket {
    public clientType: ClientTypes = ClientTypes.NotDefined;
    public isAlive: boolean;
}

class ExtWebSocketServer extends WebSocket.Server {
    public sendTo(clientType: ClientTypes, message: string) {
        this.clients.forEach((client: ExtWebSocket) => {
            if (client.clientType === clientType)
                client.send(message);
        });
    }
}

const port = 8081;
const app = express();

app.set('port', process.env.PORT || port);
app.set('views', path.join(__dirname, '../views'));
app.set('view engine', 'pug');
app.use(express.static(path.join(__dirname, "public"), { maxAge: 31557600000 }));
app.get('/', (req, res, next) => {
    console.log("GET request!\r\n");
    console.log(req.connection.localAddress);
    res.render('index', { title: 'Home', serverIp: req.connection.localAddress, portNr: req.connection.localPort });
});
app.get('/test', (req, res, next) => {
    res.send("test");
});
app.get('*', (req, res, next) => {
    res.status(404).send("Not found");
});
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
    res.status(500).send(`Error: \r\n${err}`);
});

const server = http.createServer(app);
const wsServer: ExtWebSocketServer = new ExtWebSocketServer({ server });
//server.on('upgrade', wsServer.handleUpgrade);

wsServer.on('connection', (ws: ExtWebSocket) => {
    console.log("Registered new connection");
    ws.isAlive = true;
    ws.on('pong', () => {
        ws.isAlive = true;
    });

    ws.on('open', (ws: ExtWebSocket) => {

    });

    ws.on('message', (message: string) => {
        console.log(`received: %s`, message);
        let incTask: IncomingMessage
        try {
            incTask = JSON.parse(message);
        }
        catch (err) {
            console.log("Error Parsing message");
            let errMsg = new ErrorMessage(ErrorTypes.InvalidMessage, "Invalid JSON");
            return;
        }

        switch (incTask.type) {
            case IncomingMessageTypes.Connect:
                let connectMessage = <ConnectMessage> incTask;
                ws.clientType = connectMessage.clientType;
                break;
            case IncomingMessageTypes.Result:
                wsServer.sendTo(ClientTypes.GUI, message);
                break;
            case IncomingMessageTypes.Settings:
                wsServer.sendTo(ClientTypes.Worker, message);
                break;
            case IncomingMessageTypes.Simulate:
                wsServer.sendTo(ClientTypes.Worker, message);
                break;
            case IncomingMessageTypes.Error:
                if (ws.clientType == ClientTypes.Worker) {
                    wsServer.sendTo(ClientTypes.GUI, message);
                }
            default:
                console.log("Invalid Message !")
        }
    });
});
const interval = setInterval(() => {
    wsServer.clients.forEach((ws: ExtWebSocket) => {
        if (ws.isAlive == false)
            return ws.terminate();
        ws.isAlive = false;
        ws.ping();
    });
}, 10000);
server.listen(port, '0.0.0.0', () => {
    console.log("Server started on port:%d", app.get('port'));
});
//# sourceMappingURL=server.js.map