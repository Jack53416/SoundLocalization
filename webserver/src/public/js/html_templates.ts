export module HtmlTemplates {
    export function logMessage(title: string, date: string, content: string): string
    {
        return (
            `<li class="left clearfix" >
            <div class="log-body clearfix" >
                <div class="header" >
                    <strong class="primary-font">${title} </strong>
                        <small class="pull-right text-muted"><i class="fas fa-clock"></i>&nbsp${date}</small>
                </div>
                <p>${content}</p>
            </div>
            </li>`);
    }

}