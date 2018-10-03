import { HtmlTemplates } from './html_templates';

export class LogMessage {
    topic: string;
    date: Date;
    content: string;

    constructor(topic: string, content: string, date?: Date) {
        this.topic = topic;
        this.content = content;
        this.date = date ? date : new Date();
    }

    get formatedDate(): string {
        let dd: any = this.date.getDate();
        let mm: any = this.date.getMonth() + 1;
        let hh: any = this.date.getHours();
        let MM: any = this.date.getMinutes();
        let ss: any = this.date.getSeconds();

        dd = dd > 10 ? dd : '0' + dd;
        mm = mm > 10 ? mm : '0' + mm;
        hh = hh > 10 ? hh : '0' + hh;
        MM = MM > 10 ? MM : '0' + MM;
        ss = ss > 10 ? ss : '0' + ss;


        return `${dd}/${mm} ${hh}:${MM}:${ss}`;
    }

    public render(): string {
        return HtmlTemplates.logMessage(this.topic, this.formatedDate, this.content);
    }
}

export class Log {
    private readonly handle: any;
    private messages: Array<LogMessage> = [];

    constructor() {
        this.handle = document.querySelector("ul.log");
        if (!this.handle) {
            console.log("Error could not find log handle!");
        }
    }

    public addMessage(msg: LogMessage) {
        this.messages.push(msg);
        this.handle.innerHTML = this.handle.innerHTML + msg.render();
    }

}