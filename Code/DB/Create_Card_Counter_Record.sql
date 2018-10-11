CREATE TABLE IF NOT EXISTS Card_Counter_Record (
    game_id INTEGER NOT NULL,
    turn_num INTEGER NOT NULL,
    bust FLOAT NOT NULL,
    blackjack FLOAT NOT NULL,
    exceedWinningPlayer FLOAT NOT NULL,
    alreadyExceedingWinningPlayer BIT NOT NULL,
    move BIT NOT NULL,
    trained BIT DEFAULT 0, -- update this maybe, its a bit messy, only the nn needs this, makes this un-normalised, make it null if other ai's don't need it?

    FOREIGN KEY (game_id) REFERENCES Game_Record(game_id),
    FOREIGN KEY (turn_num) REFERENCES Moves(turn_num),
    PRIMARY KEY(game_id, turn_num)
);