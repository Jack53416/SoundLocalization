export enum SamplingRates {
    KHz_41 = 41166,
    KHz_62 = 62499,
    KHz_83 = 83332,
    KHz_124 = 124998
}

export interface Position {
    x: number;
    y: number;
    z: number;
}

export class Settings {
    receivers: Array<Receiver>;
}

export abstract class SimObject {
    pos: Position;

    constructor(position: Position = { x: 0, y: 0, z: 0 }) {
        this.pos = position;
    }
}

export class SoundSource extends SimObject {

}

export class Receiver extends SimObject {
    isReference: boolean;
    constructor(position?: Position, isRef: boolean = false) {
        super(position);
        this.isReference = isRef;
    }
}