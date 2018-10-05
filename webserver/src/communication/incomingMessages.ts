import { SoundSource, SamplingRates, Receiver } from '../common/simulation'

export enum IncomingMessageTypes {
    Connect = "Connect",
    Simulate = "Simulate",
    Settings = "Settings",
    Result = "Result",
    Error = "Error"
}

export enum ClientTypes {
    Worker = "Worker",
    GUI = "GUI",
    NotDefined = "NotDefined"
}

export abstract class IncomingMessage {
    type: IncomingMessageTypes
    html?: String;
}

export class ConnectMessage extends IncomingMessage {
    type: IncomingMessageTypes = IncomingMessageTypes.Connect;
    clientType: ClientTypes;

    constructor(clientType: ClientTypes) {
        super();
        this.clientType = clientType;
    }
}

export class SimulateMessage extends IncomingMessage {
    type: IncomingMessageTypes = IncomingMessageTypes.Simulate;
    simSource: SoundSource;

    constructor(soundSrc: SoundSource) {
        super();
        this.simSource = soundSrc;
    }
}

export class SettingsMessage extends IncomingMessage {
    type: IncomingMessageTypes = IncomingMessageTypes.Settings;
    receivers: Array<Receiver>;
    samplingRate?: SamplingRates;

    constructor(recs: Array<Receiver>, samplingRate?: SamplingRates) {
        super();
        this.receivers = recs;
        if (samplingRate) {
            this.samplingRate = samplingRate;
        }
    }
}

export class ResultMessage extends IncomingMessage {
    type: IncomingMessageTypes = IncomingMessageTypes.Result;
    roots: Array<SoundSource>;
    chosenRootId: number;
}

export class ErrorMessage extends IncomingMessage {
    type: IncomingMessageTypes = IncomingMessageTypes.Error;
    msg: string;
}