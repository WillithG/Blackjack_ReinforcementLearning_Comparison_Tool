import Blackjack as BJ
from Simple_AI import Simple_AI
from CC_AI import CC_AI
from Rand_AI import Rand_AI
import os,sys
sys.path.append(os.path.realpath("./NN_AI"))
sys.path.append(os.path.realpath("./NN_AI/nn_data"))
sys.path.append(os.path.realpath("./DB"))
sys.path.append(os.path.realpath("./Structs"))

from Circular_Queue import Circular_Queue as cQ
from NN import NN
from Moves import Moves
from CT_Wrapper import CT_Wrapper
import matplotlib.pyplot as plt
import numpy as np
from Card_Counter import Card_Counter

"""
    - class which carries out all the functionality of the comparison tool
    - TODO - MOVE SOME OF THE GRAPHING PARTS TO THE GUI, THIS CLASS IS FAR TOO MEATY
"""

class Comparison_Tool:
    ID_NN = "nn"
    ID_SIMPLE = "simple"
    ID_CC_AI = "cc_ai"
    ID_RAND_AI = "rand"
    param_types = ["default", "passive", "aggressive"]  # maybe convert this to an aggressive scale?

    def __init__(self):
        self.blackjack_val = 21
        # Dictionary holding all the hands of the agents
        self.db_wrapper = CT_Wrapper("DB/blackjack.sqlite") # change this to the normal one
        self.agent_params = {}
        self.agents = {}
        self.agents_hands = {}


    # instanciates the agents, sets their parameters and hands
    def init_agents(self):
        # The instances of all the agents
        self.agents = {
            Comparison_Tool.ID_NN: NN(Training=False),
            Comparison_Tool.ID_SIMPLE: Simple_AI(),
            Comparison_Tool.ID_CC_AI: CC_AI(),
            Comparison_Tool.ID_RAND_AI: Rand_AI()
        }

        # set the params of the agents
        self.set_params()
        for agent_id in self.agents.keys():
            # rand does not have parameters - pass
            self.agents[agent_id].set_parameters(self.agent_params[agent_id])

        self.agents_hands = dict()
        self.agents_hands["dealer"] = BJ.Dealer_Hand()
        for agent_key in self.agents.keys():
            self.agents_hands[agent_key] = BJ.Hand(agent_key)

        # sets the hands in the agent class to the same ones in the agent hands dictionary
        for agent_id, agent in self.agents.items():
            agent.hand = self.agents_hands[agent_id]

    # sets the parametrs, takes in a dictionary as an argument to set the parameters
    def set_params(self):
        self.agent_params = {}
        for ID in [Comparison_Tool.ID_NN, Comparison_Tool.ID_SIMPLE, Comparison_Tool.ID_CC_AI, Comparison_Tool.ID_RAND_AI]:
            if ID not in self.agent_params:
                self.agent_params[ID] = "default"
        return self.agent_params

    # run X games of blackjack, either returns the winrates of each agent or the game_id of the games played
    # create and manage a mainloop game of blackjack
    # pass the id's of the agents who are playing - DEALER IS NOT AUTOMATICALLY INCLUDED
    # todo make this function not so large - abstract away all the database queue stuff
    # todo abstract away all the aggression and win rates stuff too
    def get_data(self, *args, no_games=1000, data_get="win"):
        # if a list of the players has been passed in
        if isinstance(args[0], list):
            args = args[0]

        # Initialise the agent hands and the agents playing
        self.agents = {}
        self.agents_hands = {}
        self.init_agents()

        agent_hands_playing = {}
        agents_playing = {}
        if data_get == "win":
            win_rates = {}
        elif data_get == "ids":
            game_ids = []
        for id_agent in args:
            if id_agent in self.agents_hands:
                agent_hands_playing[id_agent] = self.agents_hands[id_agent]
                agents_playing[id_agent] = self.agents[id_agent]
                if data_get == "win":
                    win_rates[id_agent] = 0

        cc = Card_Counter()
        blackjack = BJ.Blackjack(agent_hands_playing) # local instance of blackjack
        move_q = cQ(5000)
        cc_q = cQ(5000)
        game_q = cQ(2500)
        game_id = self.db_wrapper.get_next_game_id()
        # play the games and get the win rates
        for game_num in range(no_games):
            if game_num % 250 == 0:
                print("game_num:", game_num)
            while blackjack.continue_game:
                turn_num = blackjack.turnNumber
                ID_current_player = blackjack.get_current_player()
                all_hands = blackjack.get_all_hands()
                agent_current = self.agents[ID_current_player]

                hand_val_before = agent_current.hand.get_value()
                next_best_hand = self.get_next_best_hand(ID_current_player, all_hands)
                next_move = agent_current.get_move(all_hands) # pass in all player's hands

                if next_move == Moves.HIT:
                    blackjack.hit()
                elif next_move == Moves.STAND:
                    blackjack.stand()

                # calculate the required information to the databases and push to the query queues
                hand_val_after = agent_current.hand.get_value()
                move_info = (ID_current_player, game_id, turn_num, next_move,
                             next_best_hand, hand_val_before, hand_val_after)
                move_q.push(move_info)

                chances = cc.calcChances(handValue=hand_val_before, winning_value=next_best_hand)
                cc_info = (game_id, turn_num, chances["bust"], chances["blackjack"], chances["exceedWinningPlayer"],
                           chances["alreadyExceedingWinningPlayer"], next_move)
                cc_q.push(cc_info)

                if move_q.isFull():
                    self.empty_queue_push(move_q, "move")
                if cc_q.isFull():
                    self.empty_queue_push(cc_q, "cc")

            # PROCESS END OF GAME
            # get the winners, increment their wins, update the agents
            blackjack.end_game()
            # push winners to db
            winners = blackjack.winners
            winning_hands = []
            for winner_id in winners:
                winning_hands.append(agent_hands_playing[winner_id])
                if data_get == "win":
                    if winner_id == "dealer":
                        continue
                    win_rates[winner_id] += 1
            game_info = (game_id, winners, winning_hands, blackjack.turnNumber, agents_playing)
            game_q.push(game_info)

            if game_q.isFull():
               self.empty_queue_push(game_q, "game")

            #update agents and card counter then reset and increment game_id
            self.update_agents(agents_playing, blackjack)
            cc.decrement_cards(blackjack.new_cards)
            blackjack.reset()

            if data_get == "ids":
                game_ids.append(game_id)
            game_id += 1

        # stop session when agent action no longer needed
        if Comparison_Tool.ID_NN in self.agents:
            self.agents[Comparison_Tool.ID_NN].stop_session()
        # convert win records to % and return the win rates
        self.empty_queue_push(move_q, "move")
        self.empty_queue_push(game_q, "game")
        self.empty_queue_push(cc_q, "cc")

        # normalise win_rates
        if data_get == "win":
            for key in win_rates.keys():
                win_rates[key] /= no_games

        if data_get == "win":
            return win_rates
        elif data_get == "ids":
            return game_ids

    # NOT COMPLETED
    # returns a dictionary mapping a parameter (string) to an aggression rating (int)
    def map_params_aggression_simple(self):
        ids = {}
        param_agg = {} # map between parameter type and aggression
        for param in Comparison_Tool.param_types:
            self.agent_params[Comparison_Tool.ID_SIMPLE] = param
            ids[param] = self.get_data(Comparison_Tool.ID_SIMPLE, no_games=100, data_get="ids")
        for key in ids.keys():
            game_ids = ids[key]
            total = 0
            no_games = len(game_ids)
            for game_id in game_ids:
                aggr_rating = self.get_aggressive_rating_game(game_id, player_ids=Comparison_Tool.ID_SIMPLE)[Comparison_Tool.ID_SIMPLE]
                total += aggr_rating
            param_agg[key] = (total/no_games)
        return param_agg

    # method for emptying a db queue and pushing all the queries
    # pass in the queue and a string showing the type of queue "move" or "game"
    def empty_queue_push(self, queue, q_type):
        print("Emptying q: " + q_type)
        if q_type == "move":
            # push all moves to db
            while not queue.isEmpty():
                move_info = queue.pop()
                self.db_wrapper.push_move(agent_id=move_info[0], game_id=move_info[1], turn_num=move_info[2],
                                          move=move_info[3], next_best_val=move_info[4],
                                          hand_val_before=move_info[5], hand_val_after=move_info[6])
        elif q_type == "game":
            while not queue.isEmpty():
                game_info = queue.pop()
                self.db_wrapper.push_game(game_id=game_info[0], winners=game_info[1], winning_hands=game_info[2],
                                          num_of_turns=game_info[3], agents=game_info[4])
        elif q_type == "cc":
            while not queue.isEmpty():
                cc_info = queue.pop()
                self.db_wrapper.push_cc(game_id=cc_info[0], turn_num=cc_info[1], bust=cc_info[2],
                                        blackjack=cc_info[3], exceedWinningPlayer=cc_info[4],
                                        alreadyExceedingWinningPlayer=cc_info[5], move=cc_info[6])

    # pass in agent id
    # returns the hand value of the next best agent
    # will return 0 if all other agents are bust
    def get_next_best_hand(self, agent_id, all_hands):
        best_value = 0
        for hand in all_hands:
            if hand.id == agent_id:
                continue
            hand_val = hand.get_value()
            if hand_val > best_value:
                best_value = hand_val
        return best_value

    # pass in the hands of all the agents playing, returns dictionary mapping strings to agent instances
    def get_agents_playing(self, agent_hand_playing):
        toReturn = {}
        for key in agent_hand_playing.keys():
            if key == "dealer":
                continue
            toReturn[key] = self.agents[key]
        return toReturn

    def update_agents(self, agents_playing, blackjack_instance):
        new_cards = blackjack_instance.new_cards
        deck_iteration = blackjack_instance.deckIteration
        # pass new cards to card counters
        for player_id, player in agents_playing.items():
            player.update_end_game(new_cards)

    # pass in agent id, returns values on agent analysis
    def get_general_agent_analysis(self, agent_id):
        agent_data = self.db_wrapper.get_agent_moves(agent_id)
        analysis = self.process_move_data(agent_data)
        analysis["total_winrate"] = self.db_wrapper.get_agent_win_rate(agent_id)
        return analysis

    # pass in the data from X games and then process the game to show different stats
    # data should follow this format: turn_num, next_best_val, hand_val_before, move, hand_val_after
    # overall winner, winrates of each player,
    # extend this to compare winrates of each player, based on each parameter setting
    # 18 march 2018 -> currrently only analyses agents in isolation, not much relational analysis
    def process_move_data(self, data):
        # NOTE THIS IS NOT RELATED TO AGGRESSION RATING
        aggresive_threshold = 17 # TODO make this more sophisticated -> maybe make it so that it takes into account win margin?

        analysis = {
            "aggressive_hits" : 0, # hits when winning and larger than 17
            "total_stand_value" : 0, # used to calculate average stand value later on
            "no_times_stood" : 0,
            "no_times_hit" : 0,
            "sample_size" : len(data),
            "no_times_bust" : 0,
            "no_times_bust_after_aggressive_hit" : 0,
            "average_stand_value" : 0,
        }
        print(data[0])
        # iterate over data and count different cases
        for move in data:
            next_best = move[1]
            val_before = move[2]
            action = move[3]
            val_after = move[4]
            went_bust = False

            # aggressive check
            # TODO add a win margin!!!
            if action == Moves.STAND:
                analysis["total_stand_value"] += val_before
                analysis["no_times_stood"] += 1
            if val_after > self.blackjack_val: # and move = Moves.HIT ??
                analysis["no_times_bust"] += 1
                went_bust = True
            if action == Moves.HIT:
                analysis["no_times_hit"] += 1
            if val_before > next_best and val_before >= aggresive_threshold and action == Moves.HIT:
                analysis["aggressive_hits"] += 1
                if went_bust:
                    analysis["no_times_bust_after_aggressive_hit"] += 1
        analysis["average_stand_value"] = analysis["total_stand_value"] / analysis["no_times_stood"]
        analysis["%_hit"] = analysis["no_times_hit"] / analysis["sample_size"]
        analysis["%_stood"] = analysis["no_times_stood"] / analysis["sample_size"]
        return analysis

    # outputs graph of player winrate over games played
    # pass in player id
    # todo change this to getting data, plot in the gui class??
    def output_player_wr(self, id):
        is_agent = self.db_wrapper.agent_exists(id)
        is_user = self.db_wrapper.user_exists(id)
        if not is_agent and not is_user:
            print("not found, please pass valid id")
            return False

        agent_id_as_text = self.db_wrapper.convert_agents_to_text([id])
        # gets all the game record numbers which the user has played in
        games_query = """
                     SELECT game_id
                     FROM Game_Record
                     WHERE winner_ids LIKE '%{0}%'
                     ORDER BY game_id ASC;
                     """.format(id)  # add validation by selecting from users table

        # get the data from the database
        games = self.db_wrapper.execute_queries(games_query, get_result=True)
        if games == []:
            print("User has no games on record")
            return False

        d_win_rate = []
        games_won = 0
        win_rate = 0
        batch_count = 0

        # increases the batch size with number of games, to optimize speed (more queries slow it down a lot)
        no_games = len(games)
        if no_games >= 50000:
            batch_size = 1000
        elif no_games >= 10000:
            batch_size = 100
        elif no_games >= 1000:
            batch_size = 10
        elif no_games >= 100:
            batch_size = 3
        else:
            batch_size = 1

        for record in games:
            batch_count += 1
            game_id = record[0]
            games_won += 1
            if batch_count % batch_size == 0: # batches of x so that it is not too jagged
                # count how many games the player has played in up until this game_id
                games_played_q = """
                                 SELECT COUNT(*)
                                 FROM Game_Record
                                 WHERE game_id <= {0} AND players LIKE '%{1}%'
                                 """.format(game_id, agent_id_as_text)
                games_played = self.db_wrapper.execute_queries(games_played_q, get_result=True)[0][0]
                win_rate = games_won / games_played
                next_game = [game_id, win_rate]
                d_win_rate.append(next_game)
                batch_count = 0

        x_vals = [d[0] for d in d_win_rate]
        y_vals = [d[1] for d in d_win_rate]

        avg_wr = self.db_wrapper.get_avg_wr()
        avg_x = list(x_vals)
        avg_y = [avg_wr for d in range(len(avg_x))]
        self.plot_2d(x_vals, y_vals, x2=avg_x, y2=avg_y, label=id+" Winrate", label2="Avg. Winrate",
                     title="Average winrate over time", x_lbl="no games", y_lbl="Win rate")
        plt.show()

    # returns two zipped objects:
    # stand_value => win rate
    # hit_value => bust rate
    def get_zipped_aggression_data(self):
        stand_vals, win_rates = self.get_stand_vs_wr_data()
        wr_for_sv = zip(stand_vals, win_rates)
        hit_vals, bust_rates = self.get_hit_vs_br_data()
        br_for_hv = zip(hit_vals, bust_rates)
        zipped_rates = [wr_for_sv, br_for_hv]
        return zipped_rates

    # get an average of the chance to go bust if hit and the chance to win if stood at a particular value
    # this average will be the aggression rating: ie if there is 1 chance to win if stood and a 1 chance to go bust
    # if hit, then the aggression will be 1 -> stupidly aggressive
    # hits are always aggressive -> but can have an aggression of 0 ie. hitting with no chance to go bust AND standing would never result in win
    def map_hit_val_to_aggression(self):
        zipped_rates = self.get_zipped_aggression_data()
        # init aggr map
        aggr_mapping = {}
        for i in range(0, 22):
            aggr_mapping[str(i)] = 0

        # add all the decimal rates to the aggression map
        for z in zipped_rates:
            for pair in z:
                key = str(pair[0])
                val = pair[1]
                aggr_mapping[key] += val

        # normalise the rates
        aggr_mapping = self.normalise_dict(aggr_mapping)
        return aggr_mapping

    # maps_stand values to aggression rating
    def map_stand_val_to_aggression(self):
        zipped_rates = self.get_zipped_aggression_data()
        # init aggr map
        aggr_mapping = {}
        for i in range(0, 22):
            aggr_mapping[str(i)] = 0
        for z in zipped_rates:
            for pair in z:
                key = str(pair[0])
                val = pair[1]
                # 100 is really abritary, find a better way of picking this value
                aggr_mapping[key] += val

        for key in aggr_mapping.keys():
            aggr_mapping[key] /= -2

        aggr_mapping = self.normalise_dict(aggr_mapping)
        for key in aggr_mapping.keys():
            aggr_mapping[key] *= -1
        return aggr_mapping

    # pass in a dictionary and normalise all the values within it
    def normalise_dict(self, d):
        d_vals = d.values()
        max_val = max(d_vals)
        min_val = min(d_vals)
        norm_range = (max_val - min_val)
        for key in d.keys():
            d[key] = (d[key] - min_val) / (max_val - min_val)
        return d

    # pass in player id, get back aggresion rating
    # TODO extend this to include context (such as was losing at time of aggressive hit) and maybe avg / std devs of stand vals
    # Returns aggression on scale of -1 to 1 where -1 is extremely passive and 1 is extremely aggressive
    # eg of 1 => hitting when hit has prob of 1 to go bust and prob of 1 to win if stood
    # eg of -1 => standing when hitting would have 0 chance of going bust and standing has 0 chance of winning
    # overall aggression rating
    # RELATIVE SCALE -> not as absolute as shown above, ie there will be a move which is rated 1 and another -1
    def get_aggression_rating(self, id):
        exists_as_agent = self.db_wrapper.agent_exists(id)
        exists_as_user = self.db_wrapper.user_exists(id)
        exists = exists_as_agent or exists_as_user
        if not exists:
            print("id does not exist")
            return None
        has_games = self.db_wrapper.has_games(id)
        if not has_games:
            print("user does not have games")
            return None

        aggr_map_hit = self.map_hit_val_to_aggression()
        aggr_map_stand = self.map_stand_val_to_aggression()
        get_all_moves_q = """
                          SELECT turn_num, next_best_val, hand_val_before, move, hand_val_after
                          FROM Moves
                          WHERE player_id='{0}'
                          """.format(id)
        all_moves = self.db_wrapper.execute_queries(get_all_moves_q, get_result=True)
        no_moves = len(all_moves)
        total_aggr = 0
        for move in all_moves:
            move_rating = self.get_aggression_rating_move(move, hit_map=aggr_map_hit, stand_map=aggr_map_stand)
            total_aggr += move_rating
        total_aggr /= no_moves
        return total_aggr

    # returns aggression rating for a move
    # pass in data -> [turn_num, next_best_val, hand_val_before, move, hand_val_after]
    # for a move to be aggressive it must be above a critical threshold
    # the player must be winning,
    # depending on the win margin -> hitting even with "high" win margin => aggressive
    # does not work as stated in the comment -> just checks the mapping
    def get_aggression_rating_move(self, move, hit_map, stand_map):
        turn_num = move[0]
        next_best_val = move[1]
        hand_val_before = move[2]
        action = Moves.convert_to_move(move[3])
        hand_val_after = move[4]

        aggr_rating = None
        if action == Moves.HIT:
            aggr_rating = hit_map[str(hand_val_before)]
        elif action == Moves.STAND:
            aggr_rating = stand_map[str(hand_val_before)]
        return aggr_rating

    # pass in a query which gets single values
    # returns array of each value, and array of coressponding decimal frequency
    def get_values_frequency(self, query):
        all_instances = self.db_wrapper.execute_queries(query, get_result=True)
        frequencies = self.get_freq(all_instances)
        distinct_values = [int(key) for key in frequencies.keys()]
        distinct_values.sort()
        no_instances = len(all_instances)

        y_vals = [(frequencies[str(distinct_values[i])] / no_instances) for i in range(len(distinct_values))]
        return distinct_values, y_vals

    # outputs the frequencies of wins from standing at a particular win margin
    # also outputs the win margin stand frequency - NORMAL DISTRIBUTION
    def output_win_margin_at_stand_vs_winrate(self):
        get_win_margins_which_win = """
                                    SELECT (Moves.hand_val_before - Moves.next_best_val)
                                    FROM Moves, Game_Record
                                    WHERE Moves.move=0 AND Game_Record.winner_ids LIKE '%'||Moves.player_id||'%'
                                    AND Game_Record.game_id=Moves.game_id
                                    """
        x_vals, y_vals = self.get_values_frequency(get_win_margins_which_win)

        get_win_margins = """
                          SELECT (hand_val_before - next_best_val)
                          From Moves
                          WHERE move=0
                          """
        x2, y2 = self.get_values_frequency(get_win_margins)
        self.plot_2d(x_vals, y_vals, x2=x2, y2=y2, label="Win Frequency", label2="Frequency",
                     title="Win Margin Win Dist", x_lbl="Win Margin", y_lbl="% Frequency / % Win Frequency")
        plt.show()

    # pass in a game_id and player ids
    # aggression rating for game is measured with an average of the aggression of moves from each game
    # returns the aggression rating for that game
    def get_aggressive_rating_game(self, game_id, player_ids):
        if isinstance(player_ids, str):
            player_ids = [player_ids]
        hit_map = self.map_hit_val_to_aggression()
        stand_map = self.map_stand_val_to_aggression()
        ratings_for_game = {}
        for player in player_ids:
            get_moves_q = """
                          SELECT turn_num, next_best_val, hand_val_before, move, hand_val_after
                          FROM Moves
                          WHERE game_id={0} AND player_id='{1}';
                          """.format(game_id, player)
            all_moves = self.db_wrapper.execute_queries(get_moves_q, get_result=True)
            no_moves = len(all_moves)
            total_aggr = 0
            for move in all_moves:
                move_rating = self.get_aggression_rating_move(move, hit_map=hit_map, stand_map=stand_map)
                total_aggr += move_rating
            total_aggr /= no_moves
            ratings_for_game[player] = total_aggr
        return ratings_for_game

    # pass in agent id
    # outputs graph of average stand value against games played
    def output_avg_stand_value(self, id):
        query = """
                SELECT hand_val_before
                FROM Moves
                WHERE player_id='{0}' AND move=0
                ORDER BY game_id ASC;
                """.format(id)
        games = self.db_wrapper.execute_queries(query, get_result=True)
        x_vals = []
        y_vals = []
        total_stand_value = 0
        batch_count = 0
        for i in range(len(games)):
            game = games[i]
            stand_value = game[0]
            total_stand_value += stand_value
            avg_stand_value = total_stand_value / (i+1)

            if batch_count % 10 == 0:
                x_vals.append(i)
                y_vals.append(avg_stand_value)
                batch_count = 0

        self.plot_2d(x_vals, y_vals, title=id+"'s Avg Stand Val Over Time", x_lbl="no games", y_lbl="avg stand value")
        plt.show()

    # outputs the win rate against aggresion values
    # plots a point for each user / agent
    def output_aggression_win_relation(self):
        get_all_agents_q = """
                          SELECT agent_id, games_won, games_played
                          FROM agents
                          WHERE games_played != 0;
                          """
        get_all_users_q = """
                          SELECT username, games_won, games_played
                          FROM users
                          WHERE games_played != 0;
                          """
        all_agents = self.db_wrapper.execute_queries(get_all_agents_q, get_result=True)
        all_users = self.db_wrapper.execute_queries(get_all_users_q, get_result=True)
        all_players_data = all_agents + all_users

        # data => [player_id, games_won, games_played]
        aggression_ratings = [self.get_aggression_rating(data[0]) for data in all_players_data]
        win_rates = [(data[1] / data[2]) for data in all_players_data]

        # sorting the aggression ratings, but keeping the association
        agg_wr_dict = {}
        for i in range(len(aggression_ratings)):
            rating = aggression_ratings[i]
            agg_wr_dict[str(rating)] = win_rates[i]

        sorted_ratings = []
        corresp_wr = []
        print(aggression_ratings)
        for rating in sorted(aggression_ratings):
            as_key = str(rating)
            sorted_ratings.append(rating)
            corresp_wr.append(agg_wr_dict[as_key])

        self.plot_2d(sorted_ratings, corresp_wr, title="Aggression ratings vs Winrates",
                     x_lbl="Aggr. Rating", y_lbl="Win Rate")
        plt.show()

    # outputs a graph displaying hand values when players have stood, and their % frequency
    def output_stand_dist(self):
        get_all_stands_query = """
                               SELECT hand_val_before
                               FROM Moves
                               WHERE move=0;
                               """
        x_vals, y_vals = self.get_values_frequency(get_all_stands_query)

        self.plot_2d(x_vals, y_vals, title="Stand Distribution", x_lbl="Stand Value", y_lbl="% Frequency")
        plt.show()

    # outputs a graph displaying hand values when players have hit, and their % frequency
    def output_hit_dist(self):
        get_all_hits_query = """
                             SELECT hand_val_before
                             FROM Moves
                             WHERE move=1;
                             """
        x_vals, y_vals = self.get_values_frequency(get_all_hits_query)
        self.plot_2d(x_vals, y_vals, title="Hit Distribution", x_lbl="Hit Value", y_lbl="% Frequency")
        plt.show()

    # pass in a 2d list of values
    # returns a dictionary where key is a value the corresponding value is the frequency of that value from the dataset
    def get_freq(self, all_events):
        frequencies = {}
        for event in all_events:
            val = event[0]
            val_as_key = str(val)
            if val_as_key not in frequencies:
                frequencies[val_as_key] = 0
            frequencies[val_as_key] += 1
        return frequencies

    # pass in x and y values and optional labels
    # outputs new figure and plots
    # make the arguments for legends and multiple lines better - really messy atm
    def plot_2d(self, x, y, **kwargs):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        if "title" in kwargs:
            fig.suptitle(kwargs["title"])
        if "x_lbl" in kwargs:
            plt.xlabel(kwargs["x_lbl"])
        if "y_lbl" in kwargs:
            plt.ylabel(kwargs["y_lbl"])

        if "label" in kwargs:
            ax.plot(x, y, label=kwargs["label"])
        else:
            ax.plot(x,y)

        if "x2" in kwargs and "y2" in kwargs:
            if "label2" in kwargs:
                ax.plot(kwargs["x2"], kwargs["y2"], label=kwargs["label2"])
            else:
                ax.plot(kwargs["x2"], kwargs["y2"])

        if "label" in kwargs or "label2" in kwargs:
            ax.legend()
        ax.legend()

    # pass in move.hit or move.stand and get back all the distinct values of each hit/stand
    def get_distinct_vals(self, move):
        if isinstance(move, Moves):
            move = Moves.convert_to_bit(move)
        elif not (isinstance(move, int) and (move == 0 or move == 1)):
            return False
        get_distinct_vals = """
                            SELECT DISTINCT hand_val_before
                            FROM Moves
                            WHERE move={0};
                            """.format(move)
        distinct_vals_res = self.db_wrapper.execute_queries(get_distinct_vals, get_result=True)
        values = [i[0] for i in distinct_vals_res]  # all distinct hand values
        values.sort()
        return values

    # get series of stand values
    # get games won when standing on said value
    # get number of games when stood of value
    # returns the distinct stand values, returns the stand values and the corresponding winrates
    def get_stand_vs_wr_data(self):
        stand_values = self.get_distinct_vals(Moves.STAND)
        total_games_stood = [] # total number of games stood with value coressponding to stand_values
        games_won = [] # games won with value coressponding to stand_values

        for value in stand_values:
            total_games_query = """
                                SELECT COUNT(*)
                                FROM Moves
                                WHERE move=0 AND hand_val_before={0};
                                """.format(value)
            # cross param sql
            no_games_won_query = """
                                 SELECT COUNT(*)
                                 FROM Moves, Game_Record
                                 WHERE Moves.move=0 AND Game_Record.winner_ids LIKE '%'||Moves.player_id||'%'
                                 AND Game_Record.game_id=Moves.game_id AND hand_val_before={0};
                                 """.format(value)

            total_games = self.db_wrapper.execute_queries(total_games_query, get_result=True)[0][0]
            no_games = self.db_wrapper.execute_queries(no_games_won_query, get_result=True)[0][0]

            total_games_stood.append(total_games)
            games_won.append(no_games)

        win_rates = [games_won[i]/total_games_stood[i] for i in range(len(stand_values))]
        return stand_values, win_rates

    # outputs graph of winrates against stand values
    def output_stand_vs_wr(self):
        stand_values, y_vals = self.get_stand_vs_wr_data()
        self.plot_2d(stand_values, y_vals, title="Chance to Win Based on Stand Value",
                       x_lbl="Stand Value", y_lbl="Win Rate")

        plt.show()

    # returns different values that have been hit on, and the decimal rate of going bust when hit on that value
    def get_hit_vs_br_data(self):
        hit_values = self.get_distinct_vals(Moves.HIT)
        total_times_hit = []  # total number of games stood with value coressponding to stand_values
        games_bust = []  # games won with value coressponding to stand_values
        for value in hit_values:
            total_times_query = """
                                SELECT COUNT(*)
                                FROM Moves
                                WHERE move=1 AND hand_val_before={0};
                                """.format(value)
            # cross param sql
            no_games_bust_query = """
                                  SELECT COUNT(*)
                                  FROM Moves
                                  WHERE move=1 AND hand_val_before={0} AND hand_val_after > 21;
                                  """.format(value)

            total_games = self.db_wrapper.execute_queries(total_times_query, get_result=True)[0][0]
            no_games = self.db_wrapper.execute_queries(no_games_bust_query, get_result=True)[0][0]

            total_times_hit.append(total_games)
            games_bust.append(no_games)
        bust_rates = [games_bust[i] / total_times_hit[i] for i in range(len(hit_values))]
        return hit_values, bust_rates

    # outputs graph of bust rate against hit value
    def output_hit_vs_br(self):
        hit_values, y_vals = self.get_hit_vs_br_data()
        self.plot_2d(hit_values, y_vals, title="Chance to Go Bust Based on Hit Value",
                     x_lbl="Hit Value", y_lbl="Bust Rate")

        plt.show()

    # updates the neural network with new data from games it has played
    # ADD TO NN WU
    def update_nn(self):
        nn = NN()
        games_to_train = nn.update_training()
        if games_to_train >= 50:
            nn.stop_session()
        return games_to_train

    # outputs the aggression scaled for different moves
    def output_aggression_scale(self):
        hit_map = self.map_hit_val_to_aggression()
        stand_map = self.map_stand_val_to_aggression()

        hit_map_keys = hit_map.keys()
        x1 = sorted([int(key) for key in hit_map_keys])
        y1 = []
        for x in x1:
            y1.append(hit_map[str(x)])

        stand_map_keys = stand_map.keys()
        x2 = sorted([int(key) for key in stand_map_keys])
        y2 = []
        for x in x2:
            y2.append(stand_map[str(x)])

        self.plot_2d(x1, y1, x2=x2, y2=y2, label="Hit", label2="Stand",
                     title="Hit and stand aggression values", x_lbl="Hand Value", y_lbl="Aggression Rating")
        plt.show()

    # pass in a user id and get a graph of their aggression rating over time
    # really slow
    def output_aggression_over_time(self, id):
        agent_id_as_text = self.db_wrapper.convert_agents_to_text([id])
        # gets all the game record numbers which the user has played in
        games_query = """
                      SELECT game_id
                      FROM Game_Record
                      WHERE players LIKE '%{0}%'
                      ORDER BY game_id ASC;
                      """.format(id)  # add validation by selecting from users table

        # get the data from the database
        games = self.db_wrapper.execute_queries(games_query, get_result=True)
        batch_count = 0
        # increases the batch size with number of games, to make the querying faster
        no_games = len(games)
        if no_games >= 50000:
            batch_size = 1000
        elif no_games >= 10000:
            batch_size = 100
        elif no_games >= 1000:
            batch_size = 10
        elif no_games >= 100:
            batch_size = 3
        else:
            batch_size = 1

        d_aggr = []
        games_num = 0
        total_aggr = 0
        for record in games:
            batch_count += 1
            game_id = record[0]
            games_num += 1
            if games_num % 100:
                print("(aggression over time) on game num: " + str(games_num))

            if batch_count % batch_size == 0:  # batches of x so that it is not too jagged
                # count how many games the player has played in up until this game_id
                game_aggr = self.get_aggressive_rating_game(game_id, id)[id]
                total_aggr += game_aggr
                d_aggr.append([games_num, total_aggr / games_num])
                batch_count = 0

        x_vals = [d[0] for d in d_aggr]
        y_vals = [d[1] for d in d_aggr]

        self.plot_2d(x_vals, y_vals, label=id + " Aggression",
                     title="Average Aggression over time", x_lbl="no games", y_lbl="Aggr. Rating")
        plt.show()



if __name__ == "__main__":
    ct = Comparison_Tool()
    print(ct.map_params_aggression_simple())

    #ct.get_data(Comparison_Tool.ID_NN, Comparison_Tool.ID_CC_AI,Comparison_Tool.ID_SIMPLE, Comparison_Tool.ID_RAND_AI, no_games=2000)
    #ct.output_aggression_over_time("nn")

    #ct.output_aggression_scale()
    #ct.output_aggression_win_relation()
    #print(ct.get_aggression_rating("simple"))

    #ct.output_win_margin_at_stand_vs_winrate()
    #Comparison_Tool.ID_CC_AI, Comparison_Tool.ID_NN, Comparison_Tool.ID_SIMPLE
    #ct.get_data(Comparison_Tool.ID_NN, no_games=50)
    #print(ct.db_wrapper.execute_queries(query, get_result=True))


    #ct.output_avg_stand_value("cc_ai")
    #print(ct.db_wrapper.get_avg_wr())

    #q = """
     #   SELECT *
     #   FROM Game_Record
      #  WHERE game_id=2;
      #  """
    #print(ct.db_wrapper.execute_queries(q, get_result=True))

    #print(ct.get_data(Comparison_Tool.ID_SIMPLE, Comparison_Tool.ID_CC_AI, Comparison_Tool.ID_NN,
     #                 Comparison_Tool.ID_RAND_AI, no_games=50000))
    #connection, cursor = ct.db_wrapper.execute_queries(
    #    "SELECT * FROM Game_Record", keep_open=True)
    #print(cursor.fetchone())
    #connection.close()

    #connection, cursor = ct.db_wrapper.execute_queries(
    #    "SELECT * FROM Moves WHERE player_id='simple'", keep_open=True
    #)
    #print(cursor.fetchall())
    #connection.close()

    #agent_to_analyse = Comparison_Tool.ID_SIMPLE
    #print(agent_to_analyse, ct.get_agent_analysis(agent_to_analyse))

    #ct.output_player_wr(agent_to_analyse)
    #ct.output_avg_stand_value(agent_to_analyse)

    #print(ct.db_wrapper.get_stand_val_avg())
    #print(ct.db_wrapper.get_stand_val_std_dev())
    #ct.output_stand_dist()
    #ct.output_hit_dist()

    #ct.output_stand_vs_wr()
    #ct.output_hit_vs_br()

    #q = """
    #    SELECT *
    #    FROM Moves
    #    WHERE hand_val_before=21 AND player_id != 'rand' AND move=1;
    #    """

    #res = ct.db_wrapper.execute_queries(q, get_result=True)
    #total_games = ct.db_wrapper.execute_queries(q1, get_result=True)[0]
