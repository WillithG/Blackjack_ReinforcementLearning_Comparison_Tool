import sys, os
sys.path.append(os.path.realpath("./DB"))
sys.path.append(os.path.realpath("./NN"))
from DB_Wrapper import DB_Wrapper
from Deck import Deck
from Card_Counter import Card_Counter
from Comparison_Tool import Comparison_Tool
from NN import NN
import tensorflow as tf
import numpy as np

class T:
    def __init__(self):
        self.db_wrapper = DB_Wrapper("DB/Blackjack.sqlite")

    def test_1ai(self):
        # proving the function of the card counter
        d = Deck()
        cc = Card_Counter()

        HAND_VALUE = 15
        WNR_VALUE = 17

        cc.displayCardRecord()
        print(cc.calcChances(HAND_VALUE, WNR_VALUE))
        for _ in range(5):
            print()
            card = d.pop()
            print(card)
            cc.decrement_card(card)
            cc.displayCardRecord()
            print(cc.calcChances(HAND_VALUE, WNR_VALUE))
        print(end="\n\n\n")

        # getting the moves from a game of the neural network and showing it's internal state
        r = []
        game_id = 999
        while len(r) < 3:
            r = []
            game_id += 1
            query = """
                    SELECT Moves.*, Card_Counter_Record.*
                    FROM Moves, Card_Counter_Record
                    WHERE Moves.game_id={0} AND Card_Counter_Record.game_id={0}
                          AND Moves.player_id="nn" AND Moves.turn_num=Card_Counter_Record.turn_num
                    """.format(game_id)

            result = self.db_wrapper.execute_queries(query, get_result=True)

            for move in result:
                r.append(move)
        for move in r:
            print(move)

    def test_1aii(self):
        results = []
        for game_id in range(1000,2000):
            move_query = """
                    SELECT * 
                    FROM Moves
                    WHERE game_id = {0} AND hand_val_before=17 AND player_id="nn"
                    """.format(game_id)


            move = self.db_wrapper.execute_queries(move_query, get_result=True)
            if move == []:
                continue
            turn_num = move[0][2]
            cc_rec_query = """
                           SELECT *
                           FROM Card_Counter_Record
                           WHERE game_id={0} AND turn_num={1}
                           """.format(game_id, turn_num)

            cc_rec = self.db_wrapper.execute_queries(cc_rec_query, get_result=True)
            results.append(move + cc_rec)

        for result in results:
            print(result)
            print()

    def test_1aiii(self):
        lower_bound = 3105
        uppper_bound = 3150

        for agent in ["nn"]: #"cc_ai", "simple"]:
            q_21 = """
                    SELECT *       
                    FROM Moves
                    WHERE game_id < {1} AND game_id > {0} AND hand_val_before=21 AND player_id="{2}"
                   """.format(lower_bound, uppper_bound, agent)

            q_lt_12 = """
                      SELECT * 
                      FROM Moves
                      WHERE game_id < {1} AND game_id > {0} AND hand_val_before<=11 AND player_id="{2}"
                      """.format(lower_bound, uppper_bound, agent)

            res_21 = self.db_wrapper.execute_queries(q_21, get_result=True)
            res_lt_12 = self.db_wrapper.execute_queries(q_lt_12, get_result=True)

            for move in res_21:
                print(move)
            print(end="\n")
            for move in res_lt_12:
                print(move)
            print(end="\n\n")

    def test_1bi(self):
        ct = Comparison_Tool()
        ids = ["admin"]
        for id in ids:
            print(id)
            ct.output_player_wr(id)

    def test_1bii(self):
        ct = Comparison_Tool()
        ids = ["admin"]
        for id in ids:
            print(id)
            print(ct.get_aggression_rating(id))

    def test_2ai(self):
        ct = Comparison_Tool()
        user = "slakdjlafd"
        aggr = ct.get_aggression_rating(user)
        if aggr == None:
            print("pass")

    def test_2av(self):
        ct = Comparison_Tool()
        query = """
                SELECT turn_num, next_best_val, hand_val_before, move, hand_val_after 
                FROM Moves
                WHERE move=1 AND hand_val_before=21
                """
        rec = self.db_wrapper.execute_queries(query, get_result=True)[0]
        hit_map = ct.map_hit_val_to_aggression()
        stand_map = ct.map_stand_val_to_aggression()
        print(rec)

        print(ct.get_aggression_rating_move(rec, hit_map, stand_map))

    def test_2avii(self):
        ct = Comparison_Tool()
        testing_values = [(1, 11), (1, 4), (0, 21)]
        results = []
        for t_v in testing_values:
            move = t_v[0]
            hand_val = t_v[1]
            query = """
                    SELECT turn_num, next_best_val, hand_val_before, move, hand_val_after 
                    FROM Moves
                    WHERE move={0} AND hand_val_before={1}
                    """.format(move, hand_val)
            rec = self.db_wrapper.execute_queries(query, get_result=True)[0]
            results.append(rec)
        hit_map = ct.map_hit_val_to_aggression()
        stand_map = ct.map_stand_val_to_aggression()

        for rec in results:
            print(rec)
            print(ct.get_aggression_rating_move(rec, hit_map, stand_map))
            print()

    def test_2bi(self):
        ct = Comparison_Tool()
        print(ct.map_params_aggression_simple())

    def test_2ci(self):
        res = {}
        for agent_id in ["nn", "cc_ai", "simple"]:
            q = """
                SELECT games_won, games_played
                FROM Agents
                WHERE agent_id="{0}"
                """.format(agent_id)
            rec = self.db_wrapper.execute_queries(q, get_result=True)[0]
            res[agent_id] = rec[0]/rec[1]

        for key in res.keys():
            print(key, res[key])

    def test_3a(self):
        nn = NN()
        # getting the moves from a game of the neural network and showing it's internal state
        r = []
        game_id = 999
        while len(r) < 3:
            r = []
            game_id += 1
            query = """
                           SELECT Moves.*, Card_Counter_Record.*
                           FROM Moves, Card_Counter_Record
                           WHERE Moves.game_id={0} AND Card_Counter_Record.game_id={0}
                                 AND Moves.player_id="nn" AND Moves.turn_num=Card_Counter_Record.turn_num
                           """.format(game_id)

            result = self.db_wrapper.execute_queries(query, get_result=True)

            for move in result:
                r.append(move)
        for move in r:
            print(move)

    def test_3b(self):
        q = """
            SELECT game_id, turn_num
            FROM Card_Counter_Record
            WHERE trained=0;
            """
        toTrain = self.db_wrapper.execute_queries(q, get_result=True)
        for rec in toTrain:
            print(rec)

        nn = NN()
        t_vals_before = [i[1] for i in nn.get_trainable_vars()]
        nn.update_training()

        t_vals_after = [i[1] for i in nn.get_trainable_vars()]
        print(np.array_equal(t_vals_before, t_vals_after))


    def test_3b2(self):
        nn = NN()
        print(nn.update_training())

    def test_4f(self):
        q = """
        SELECT password
        FROM users
        """
        res = self.db_wrapper.execute_queries(q, get_result=True)
        for pw in res:
            print(pw)

    def test_6ei(self):
        output = []
        for x in range(3594, 3645):
            q = """
                SELECT winner_ids
                FROM Game_Record
                WHERE game_id={0}
                """.format(str(x))
            res = self.db_wrapper.execute_queries(q, get_result=True)[0]
            output.append(res)
        for r in output:
            print(r)

if __name__ == "__main__":
    t = T()
    t.test_1bii()