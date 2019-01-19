import { WebSocketClient } from './ws_client';
import { ClientTypes, IncomingMessage, IncomingMessageTypes, ConnectMessage, ResultMessage, SettingsMessage, SimulateMessage } from '../../communication/incomingMessages';
import { SoundSource, Receiver } from '../../common/simulation';
import { LogMessage } from './log';
import { Game, GameStatus, PlayerSelect } from './game';
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

function updateTableSettings() {
    let tableWidth = parseFloat((<HTMLInputElement>document.getElementById('table_width')).value);
    let tableHeigth = parseFloat((<HTMLInputElement>document.getElementById('table_heigth')).value);
    let tableLength = parseFloat((<HTMLInputElement>document.getElementById('table_length')).value);

    if (isNaN(tableWidth) || isNaN(tableHeigth) || isNaN(tableLength))
        throw new DOMException("One of the table dimenstions is not a number", "InvalidCharacterError");

    Graphics.settings.table.realSize.heigth = tableHeigth;
    Graphics.settings.table.realSize.width = tableWidth;
    Graphics.settings.table.realSize.length = tableLength;
    Graphics.settings.calcScale();
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

    let tbl_width_form = <HTMLInputElement>document.getElementById('table_width');
    let tbl_heigth_form = <HTMLInputElement>document.getElementById('table_heigth');
    let tbl_length_form = <HTMLInputElement>document.getElementById('table_length');

    tbl_heigth_form.value = Graphics.settings.table.realSize.heigth.toString();
    tbl_width_form.value = Graphics.settings.table.realSize.width.toString();
    tbl_length_form.value = Graphics.settings.table.realSize.length.toString();
}

function hookDebugVariables() {
    (<any>window).game = game;
    (<any>window).PlayerSelect = PlayerSelect;
}

let wsClient = new WebSocketClient(serverAddress);
let settingsButton = document.querySelector("button#settings_button");
let simulateButton = document.querySelector("button#sim_button");
let settingsToggleButton = document.querySelector("button#settingsToggle");
let gameToggleButton = document.querySelector("button#gameToggle");
let gameStartButton = document.querySelector("button#gameStart");
let gameStopButton = document.querySelector("button#gameStop");

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

let game = new Game(10,
    document.getElementById("score_p1"),
    document.getElementById("score_p2"),
    document.getElementById("gameStatus"));

gameStartButton.addEventListener("click", (event) => {
    let maxScore = parseInt((<HTMLInputElement>document.getElementById("score_max")).value);
    if (!isNaN(maxScore))
        game.maxScore = maxScore;
    game.start();
});

gameStopButton.addEventListener("click", (event) => {
    game.reset();
});

gameToggleButton.addEventListener("click", (event) => {
    let maxScore = <HTMLInputElement>document.getElementById("score_max");
    maxScore.value = game.maxScore.toString();
});

settingsButton.addEventListener("click", (event) => {
    updateMicrophoneSettings();
    updateTableSettings();
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
hookDebugVariables();