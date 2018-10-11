CREATE TABLE IF NOT EXISTS Agents (
    agent_id varchar(255) PRIMARY KEY,
    description TEXT,
    games_won INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER NOT NULL DEFAULT 0
);