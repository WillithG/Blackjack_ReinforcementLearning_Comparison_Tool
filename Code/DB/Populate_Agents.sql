/* agent_id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    games_won INTEGER NOT NULL,
    games_played INTEGER NOT NULL */

INSERT INTO "Agents" ("agent_name", "description") VALUES("nn", "neural network based agent. Takes in CC chances and hand values of itself and the best player as features");
INSERT INTO "Agents" ("agent_name", "description") VALUES("cc_ai", 'Standard Card counting ai, where behaviour depends on chance thresholds.');
INSERT INTO "Agents" ("agent_name", "description") VALUES("simple", "Simple AI, behaviour based on if possible to go bust and residual between agent and best player");
