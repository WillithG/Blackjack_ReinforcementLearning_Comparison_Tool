import os,sys
sys.path.append(os.path.realpath(".."))
from DB_Wrapper import DB_Wrapper
from Moves import Moves
from os import remove
from math import sqrt

"""
    - wrapper and interface for the database for comparison tool
"""

class CT_Wrapper(DB_Wrapper):
    def __init__(self, db_path="blackjack.sqlite"):
        super().__init__(db_path)
        self.__tables_id = ["Agents", "Moves", "Game_Record"]
        self.init_tables()
        self.init_default_agents()

    # Creates the required tables - harcoded in -> TODO Change this from hardcoded?
    def init_tables(self):
        global db_dir_path
        sql_files = ["Create_Games_Record.sql", "Create_Agents_Table.sql", "Create_Users_Table.sql",
                     "Create_Card_Counter_Record.sql"]
        for sql_f in sql_files:
            self.execute_queries_from_file(db_dir_path + sql_f)

    # pushes the agents into the table, if they do not exist
    def init_default_agents(self):
        agents = [
            ["nn", "Neural Network based AI, card counter"],
            ["cc_ai", "Card Counting, threshold based AI"],
            ["simple", "Simple AI based on game state thresholds"],
            ["rand", "Control agent which takes a random move every turn"]
        ]
        self.populate_agents_table(agents[0], agents[1], agents[2], agents[3])

    # pass in all the parameters required to push a move to the move table
    # this method will push the move to the move table
    # TODO INSERT SOME ERROR HANDLING AND DEFENSIVE PROGRAMMING
    def push_move(self, agent_id, game_id, turn_num, move, next_best_val, hand_val_before, hand_val_after):
        move = Moves.convert_to_bit(move)
        query = """INSERT INTO "Moves"
                   (player_id, game_id, turn_num, next_best_val, hand_val_before, move, hand_val_after) \
                   VALUES ("{0}", {1}, {2}, {3}, {4}, {5}, {6});""".format(agent_id, game_id, turn_num,
                                                                           next_best_val, hand_val_before, move,
                                                                           hand_val_after)
        self.execute_queries(query)

    # push the a game to the game record table
    # agents => array of Agents Instances
    # winning_hands => Array of Hand Instances
    # convert winners to text
    def push_game(self, game_id, winners, winning_hands, num_of_turns, agents, table="Agents"):
        wnr_hands = ""
        wnr_vals = ""
        for hand in winning_hands:
            hand_as_text = self.convert_hand_to_text(hand)
            wnr_hands += hand_as_text + ";"

            winning_val = hand.get_value()
            wnr_vals += str(winning_val) + ";"
        agents_as_text = self.convert_agents_to_text(agents)
        wnr_ids = ";".join(winners) + ";"
        query = """
                  INSERT INTO Game_Record
                  (game_id, winner_ids, winning_hands, winning_values, num_of_turns, players)
                  VALUES ({0}, '{1}', '{2}', '{3}', {4}, '{5}');
                  """.format(game_id, wnr_ids, wnr_hands, wnr_vals, num_of_turns, agents_as_text)
        self.execute_queries(query)

        # increment the winners and the games played in the database
        for agent_id in winners:
            if agent_id == "dealer":
                continue
            self.inc_agent_win(agent_id, table=table)
        for agent_id in agents:
            if agent_id == "dealer":
                continue
            self.inc_games_played(agent_id, table=table)

    # pushes the state of the cc at a particular move
    def push_cc(self, game_id, turn_num, bust, blackjack, exceedWinningPlayer, alreadyExceedingWinningPlayer, move):
        move = Moves.convert_to_bit(move)
        alreadyExceedingWinningPlayer = int(alreadyExceedingWinningPlayer)
        query = """
                INSERT INTO Card_Counter_Record
                (game_id, turn_num, bust, blackjack, exceedWinningPlayer, alreadyExceedingWinningPlayer, move)
                VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6})
                """.format(game_id, turn_num, bust, blackjack, exceedWinningPlayer, alreadyExceedingWinningPlayer, move)
        self.execute_queries(query)

    # pass in a hand of cards
    # returns the hand as a string in the format:
    # "({value} of {suit}), ({value} of {suit})" .. -> etc
    def convert_hand_to_text(self, hand):
        hand_as_text = ""
        for card in hand.hand:
            if hand_as_text == "":
                hand_as_text += "({0} of {1})".format(card.value, card.suit)
            else:
                hand_as_text += ", ({0} of {1})".format(card.value, card.suit)
        return hand_as_text

    # pass in agent name, and a game_id
    # returns the turn_num, next_best_val, hand_val_before, move, hand_val_after
    # pass in a game move if moves from a particular game wanted
    # or else it will return all the moves the agent has made
    # returns tuple of move records
    def get_agent_moves(self, agent, game_id=None):
        # selects all moves
        if game_id is None:
            query = """SELECT turn_num, next_best_val, hand_val_before, move, hand_val_after
                       FROM Moves WHERE player_id='{0}'""".format(agent)
        else:
            query = """SELECT turn_num, next_best_val, hand_val_before, move, hand_val_after
                       FROM Moves WHERE player_id='{0}' AND game_id={1}""".format(agent, game_id)
        results = self.execute_queries(query, get_result=True)

        # convert moves from bit to move
        toReturn = []
        for result in results:
            record = list(result)
            move_as_move = Moves.convert_to_move(record[3])
            record[3] = move_as_move
            toReturn.append(record)
        return tuple(toReturn)

    # abstract method for incrementing a field in the agents table
    def inc_agent(self, field, agent_id, table="Agents"):
        name_field = ""
        if table == "Agents":
            name_field = "agent_id"
        elif table == "users":
            name_field = "username"
        get_curr_query = "SELECT {0} FROM {1} WHERE {2}='{3}'".format(field, table, name_field, agent_id)
        game_data = self.execute_queries(get_curr_query, get_result=True)
        game_data = game_data[0][0]

        inc_win_query = """
                        UPDATE {0}
                        SET {1}={2}
                        WHERE {3}='{4}';
                        """.format(table, field, game_data+1, name_field, agent_id)
        self.execute_queries(inc_win_query)

    # increments the win field of the passed agent
    def inc_agent_win(self, agent_id, table="Agents"):
        self.inc_agent("games_won", agent_id, table)

    # increments the games played for each of the agents passed
    def inc_games_played(self, *args, table="Agents"):
        for agent_id in args:
            self.inc_agent("games_played", agent_id, table)

    # returns the next available game id
    # game id has to exist in both the moves table and the game record table
    def get_next_game_id(self):
        q_moves = """
                 SELECT MAX(game_id)
                 FROM Moves
                 """
        q_gr = """
               SELECT MAX(game_id)
               FROM Game_Record
               """
        max_moves = self.execute_queries(q_moves, get_result=True)[0][0]
        max_gr = self.execute_queries(q_gr, get_result=True)[0][0]

        # returns the larger game id of the two
        # if max_moves is none and max_gr is none then there is nothing in the database
        if max_moves is None:
            if max_gr is None:
                game_id_test = 1
            else:
                game_id_test = max_gr + 1
        else:
            if max_gr is None:
                game_id_test = max_moves + 1
            else:
                game_id_test = max(max_moves, max_gr) + 1
        return game_id_test

    # pass in array of agent instances
    # returns string which is formatted for database suitability
    def convert_agents_to_text(self, agents):
        agent_text = ""
        for agent in agents:
            if isinstance(agent, str):
                agent_name = agent
            else: # TODO CHANGE THIS IN A WAY SO THAT ITS NOT SHIT
                agent_name = agent.id
            agent_text += agent_name + ";"
        return agent_text

    # pass in arrays [agents ids, desc], method will populate them in the database
    def populate_agents_table(self, *args):
        queries = []
        for arg in args:
            agent_name = arg[0]
            agent_desc = arg[1]

            if self.agent_exists(agent_name):
                continue

            queries.append("""
                INSERT INTO Agents (agent_id, description, games_won, games_played)
                VALUES ('{0}', '{1}', 0, 0);
            """.format(agent_name, agent_desc))
        self.execute_queries(queries)

    # pass in agent id, returns true or false depending on whether the agent
    # already exists in the databse or not
    def agent_exists(self, id):
        query = """
                SELECT *
                FROM Agents
                WHERE agent_id='{0}'
                """.format(id)
        result = self.execute_queries(query, get_result=True)
        if result == []:
            return False
        return True

    # returns true if the id exists in the user table
    def user_exists(self, id):
        query = """
                SELECT *
                FROM users
                WHERE username='{0}'
                """.format(id)
        result = self.execute_queries(query, get_result=True)
        if result == []:
            return False
        return True

    # pass in an agent id and get the winrate as a decimal
    def get_agent_win_rate(self, agent_id):
        # get the number of wins
        query = """
                SELECT games_won, games_played
                FROM Agents
                WHERE agent_id='{0}'
                """.format(agent_id)
        result = self.execute_queries(query, get_result=True)[0]
        winrate = result[0] / result[1]
        return winrate

    # todo contextualise this value -> look at opponents hand values before stand also
    # queries database, returns average stand value players stand on
    def get_stand_val_avg(self):
        query = """
                SELECT AVG(hand_val_before)
                FROM Moves
                WHERE move=0;
                """
        result = self.execute_queries(query, get_result=True)
        return result[0][0]

    # gets the standard deviation to the mean of the average value which the players stand on
    # todo test test test
    def get_stand_val_std_dev(self):
        avg_val = self.get_stand_val_avg()

        query = """
                SELECT hand_val_before
                FROM Moves
                WHERE move=0;
                """
        results = self.execute_queries(query, get_result=True)

        s = 0 # sum of (x - xbar)^2
        n = len(results)
        for result in results:
            s += (result[0] - avg_val) ** 2

        std_dev = sqrt(s / (n-1))
        return std_dev

    # returns true if id passed is a valid user ID
    def check_valid_id(self, id):
        query_agents = """
                       SELECT *
                       FROM Agents
                       WHERE agent_id='{0}';
                       """.format(id)

        query_users = """
                      SELECT *
                      FROM Users
                      WHERE username='{0}';
                      """.format(id)

        combined_q = """
                     SELECT COUNT(Agents.*) + COUNT(Users.*)
                     FROM Agents, Users
                     WHERE Agents.agent_id='{0}' OR Users.username='{0}'
                     """.format(id)

        agents_result = self.execute_queries(query_agents, get_result=True)
        users_result = self.execute_queries(query_users, get_result=True)

        return agents_result != [] or users_result != []

    # gets average winrate for the agents, returns as a decimal
    def get_avg_wr(self):
        q_agents = """
                   SELECT games_won, games_played, agent_id
                   FROM Agents
                   """
        res = self.execute_queries(q_agents, get_result=True)
        win_rates = [i[0] / i[1] for i in res]
        avg_winrate = sum(win_rates) / len(win_rates)
        return avg_winrate

    def has_games(self, id):
        q = """
            SELECT COUNT(*)
            FROM Game_Record
            WHERE players LIKE '%{0}%'
            """.format(id)
        res = self.execute_queries(q, get_result=True)[0][0]
        return res > 0


if __name__ == "__main__":
    db_dir_path = ""

    ct_w = CT_Wrapper()
    ct_w.execute_queries_from_file("Create_Games_Record.sql")
    ct_w.execute_queries("INSERT INTO 'Moves' (player_id, game_id, turn_num, next_best_val, hand_val_before, move, hand_val_after) VALUES ('asdf', 1, 3, 5, 0, 0, 10);")
    ct_w.execute_queries("INSERT INTO 'Moves' (player_id, game_id, turn_num, next_best_val, hand_val_before, move, hand_val_after) VALUES ('asdf', 2, 3, 5, 0, 0, 10);")

    ct_w.execute_queries("INSERT INTO 'Game_Record' (game_id, winner_id, winning_hand, winning_hand_value, num_of_turns, players) VALUES (1, 'asdf', 'agfdsg', 3, 5, 'asdf');")
    ct_w.execute_queries("INSERT INTO 'Game_Record' (game_id, winner_id, winning_hand, winning_hand_value, num_of_turns, players) VALUES (2, 'asdf', 'agfdsg', 3, 5, 'asdfsad');")
    print(ct_w.get_next_game_id())
    connection, cursor = ct_w.execute_queries("SELECT * FROM Moves", keep_open=True)
    for i in cursor:
        print(i)
    connection.close()

    ct_w.execute_queries_from_file("Create_Agents_Table")
    ct_w.execute_queries("INSERT INTO Agents (agent_id, description, games_won, games_played) VALUES ('asdf', 'adsfdf', 0, 0);")
    for x in range(2):
        ct_w.inc_agent_win("asdf")
    connection, cursor = ct_w.execute_queries("SELECT * FROM Agents", keep_open=True)
    for i in cursor:
        print(i)
    connection.close()
else:
    db_dir_path = "DB/"
