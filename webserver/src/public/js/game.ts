
export enum GameStatus {
    In_Progress = "In Progress",
    Finished = "Finished",
    Not_Started = "Not_Stared"
}

export enum PlayerSelect {
    One,
    Two,
    None
}

export interface Score {
    player_one: number;
    player_two: number;
    winner: PlayerSelect;
}

export class Game {
    maxScore: number;
    readonly defaultMaxScore: number = 10;
    score: Score;
    private _status: GameStatus;
    private p1_scoreHandle: HTMLElement;
    private p2_scoreHandle: HTMLElement;
    private statusHandle: HTMLElement;

    constructor(m_score: number, p1_handle: HTMLElement, p2_handle: HTMLElement, statusHandle: HTMLElement) {
        this.maxScore = m_score;
        this._status = GameStatus.Not_Started;
        this.statusHandle = statusHandle;
        this.p1_scoreHandle = p1_handle;
        this.p2_scoreHandle = p2_handle;

        this.reset();

    }

    get status() {
        return this._status;
    }

    start() {
        this.reset();
        this._status = GameStatus.In_Progress;
        this.statusHandle.innerHTML = this._status;
    }

    reset() {
        this.p1_scoreHandle.innerHTML = "0";
        this.p2_scoreHandle.innerHTML = "0";
        this._status = GameStatus.Not_Started;
        this.statusHandle.innerHTML = this._status;
        this.score = {
            player_one: 0,
            player_two: 0,
            winner: PlayerSelect.None
        };
    }

    incrementScore(player: PlayerSelect) {
        if (this._status != GameStatus.In_Progress)
            return;
        if (player == PlayerSelect.One) {
            this.score.player_one++;
            this.p1_scoreHandle.innerHTML = this.score.player_one.toString();
        }
        else {
            this.score.player_two++;
            this.p2_scoreHandle.innerHTML = this.score.player_two.toString();
        }
        this.checkWinningCondition();
            
    }

    private checkWinningCondition() {
        let scoreDiff = Math.abs(this.score.player_one - this.score.player_two);
        if (scoreDiff > 2) {
            if (this.score.player_one >= this.maxScore) {
                this._status = GameStatus.Finished;
                this.score.winner = PlayerSelect.One;
                this.statusHandle.innerHTML = "Finished, winner: player 1";
            }
            else if (this.score.player_two >= this.maxScore) {
                this._status = GameStatus.Finished;
                this.score.winner = PlayerSelect.Two;
                this.statusHandle.innerHTML = "Finished, winner: player 2";
            }
        }
    }
}