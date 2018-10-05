import { WebSocketClient } from './ws_client';
import { ClientTypes, IncomingMessage, IncomingMessageTypes, ConnectMessage, ResultMessage, SettingsMessage, SimulateMessage } from '../../communication/incomingMessages';
import { SoundSource, Receiver } from '../../common/simulation';
import { LogMessage } from './log';
import * as Graphics from './graphics';

const serverAddress = getServerAddress();

function getServerAddress(): string {
    let ip = document.getElementById("ip").innerText;
    let port = document.getElementById("port").innerText;
    return `ws://${ip}:${port}`;
}


function updateMicrophoneSettings() {
    for (let [idx, mic] of microphones.entries()) {
        let x_coord: number = parseFloat((<HTMLInputElement>document.getElementById(`mic${idx + 1}_x`)).value);
        let y_coord: number = parseFloat((<HTMLInputElement>document.getElementById(`mic${idx + 1}_y`)).value);
        let z_coord: number = parseFloat((<HTMLInputElement>document.getElementById(`mic${idx + 1}_z`)).value);
        let isReference: boolean = (<HTMLInputElement>document.getElementById(`mic${idx + 1}_ref`)).checked;
        mic.pos.x = isNaN(x_coord) ? 0.0 : x_coord;
        mic.pos.y = isNaN(y_coord) ? 0.0 : y_coord;
        mic.pos.z = isNaN(z_coord) ? 0.0 : z_coord;
        mic.isReference = isReference; ///Fix me: Validate if only one reference microphone is chosen !
    }

}

function updateSettingsForms() {
    for (let [idx, mic] of microphones.entries()) {
        let x_form: HTMLInputElement = <HTMLInputElement>document.getElementById(`mic${idx + 1}_x`);
        let y_form: HTMLInputElement = <HTMLInputElement>document.getElementById(`mic${idx + 1 }_y`);
        let z_form: HTMLInputElement = <HTMLInputElement>document.getElementById(`mic${idx + 1}_z`);
        let isReferenceForm: HTMLInputElement = <HTMLInputElement>document.getElementById(`mic${idx + 1}_ref`);

        x_form.value = mic.pos.x.toString();
        y_form.value = mic.pos.y.toString();
        z_form.value = mic.pos.z.toString();
        isReferenceForm.checked = mic.isReference;
    }
}

let wsClient = new WebSocketClient(serverAddress);
let settingsButton = document.querySelector("button#settings_button");
let simulateButton = document.querySelector("button#sim_button");
let settingsToggleButton = document.querySelector("button#settingsToggle");

wsClient.onResult = (msg: ResultMessage) => {
    let solution = msg.roots[msg.chosenRootId]
    let pos = Graphics.mapRealToVirtualCoord(solution.pos)
    Graphics.markPoint(pos.x, pos.y, pos.z, 5, 0.5);
}

let microphones = [
    new Receiver({ x: 0.7625, y: 0.8, z: -1.37  }, true),
    new Receiver({x: 0.7625, y: 0.8, z: 1.37}),
    new Receiver({x: -0.7625, y: 0.8, z: 1.37}),
    new Receiver({ x: -0.7625, y: 0.8, z: -1.37 })
];

settingsButton.addEventListener("click", (event) => {
    updateMicrophoneSettings();
    Graphics.updateMicrohoneMeshes(microphones);
    let msg: SettingsMessage = new SettingsMessage(microphones);
    wsClient.ws.send(JSON.stringify(msg));
    wsClient.log.addMessage(new LogMessage(
        'Settings updated',
        `New settings are are follows:\n receivers ${JSON.stringify(microphones)}`
    ));
});

settingsToggleButton.addEventListener("click", (event) => {
    updateSettingsForms();
});

simulateButton.addEventListener("click", (event) => {
    let src_x: number = parseFloat((<HTMLInputElement>document.getElementById("src_x")).value);
    let src_y: number = parseFloat((<HTMLInputElement>document.getElementById("src_y")).value);
    let src_z: number = parseFloat((<HTMLInputElement>document.getElementById("src_z")).value);

    let src = new SoundSource();
    src.pos.x = isNaN(src_x) ? 0 : src_x;
    src.pos.y = isNaN(src_y) ? 0 : src_y;
    src.pos.z = isNaN(src_z) ? 0 : src_z;

    let msg: SimulateMessage = new SimulateMessage(src);
    wsClient.ws.send(JSON.stringify(msg));
    wsClient.log.addMessage(new LogMessage(
        'Simulation of sound propagation',
        `Simulation queued with sound src with position ${src.pos.x}, ${src.pos.y}, ${src.pos.z}`
    ));
});

Graphics.init(microphones);