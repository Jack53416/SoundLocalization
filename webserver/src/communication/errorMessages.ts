export enum ErrorTypes {
    InvalidMessage = "InvalidMessage",
    ScriptNotResponding = "Script not responding"
}

export class ErrorMessage {
    public readonly errorType: ErrorTypes;
    public readonly msg: string;
    constructor(errorType: ErrorTypes, msg?: string) {
        this.errorType = errorType;
        this.msg = msg !== undefined ? msg : '';
    }
}