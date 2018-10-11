from Blackjack import Blackjack
from Blackjack import Hand
import os,sys
sys.path.append(os.path.realpath("./DB"))
sys.path.append(os.path.realpath("./Structs"))
from CT_Wrapper import CT_Wrapper
from Card_Counter import Card_Counter
from Circular_Queue import Circular_Queue as cQ
from Moves import Moves
from CC_AI import CC_AI
from NN import NN
from Simple_AI import Simple_AI

class Console_Env():
    def __init__(self, users):
        self.db_wrapper = CT_Wrapper("DB/Blackjack.sqlite")
        self.usernames = users
        self.hands = self.construct_hands()

    # builds the hands for each user
    def construct_hands(self):
        hands = {}
        for name in self.usernames:
            hands[name] = Hand(name)
        return hands

    # executes the environemnt
    def play_game(self):
        cc = Card_Counter()
        self.blackjack = Blackjack(self.hands)  # local instance of blackjack
        game_ids = []
        move_q = cQ(100)
        cc_q = cQ(100)
        game_q = cQ(100)
        game_id = self.db_wrapper.get_next_game_id()
        continue_playing = True
        while continue_playing:
            while self.blackjack.continue_game:
                turn_num = self.blackjack.turnNumber
                ID_current_player = self.blackjack.get_current_player()
                all_hands = self.blackjack.get_all_hands()
                current_hand = self.hands[ID_current_player]
                hand_val_before = current_hand.get_value()
                next_best_hand = self.get_next_best_hand(ID_current_player, all_hands)

                next_move = self.get_move(ID_current_player)  # pass in all player's hands

                if next_move == Moves.HIT:
                    self.blackjack.hit()
                elif next_move == Moves.STAND:
                    self.blackjack.stand()

                # calculate the required information to the databases and push to the query queues
                hand_val_after = current_hand.get_value()
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
            self.blackjack.end_game()
            # push winners to db
            winners = self.blackjack.winners
            winning_hands = []
            for winner_id in winners:
                winning_hands.append(self.hands[winner_id])
            self.display_winners(winning_hands)
            game_info = (game_id, winners, winning_hands, self.blackjack.turnNumber, self.hands)
            game_q.push(game_info)

            if game_q.isFull():
                self.empty_queue_push(game_q, "game")

            # update agents and card counter then reset and increment game_id
            cc.decrement_cards(self.blackjack.new_cards)
            self.blackjack.reset()
            game_ids.append(game_id)
            game_id += 1
            continue_playing = self.get_continue_playing()

        self.empty_queue_push(move_q, "move")
        self.empty_queue_push(game_q, "game")
        self.empty_queue_push(cc_q, "cc")
        return game_ids

    # gets input from the console to get user's current move
    def get_move(self, currPlayerID):
        self.blackjack.display_game()
        inp = ""
        move = None
        while inp != "h" and inp != "s":
            inp = input("\n" + currPlayerID + ": would you like to hit (h) or (s) ")
            if inp != "h" and inp != "s":
                print("please input h or s")
        print()
        if inp == "h":
            move = Moves.HIT
        elif inp == "s":
            move = Moves.STAND
        return move

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
                                          num_of_turns=game_info[3], agents=game_info[4], table="users")
        elif q_type == "cc":
            while not queue.isEmpty():
                cc_info = queue.pop()
                self.db_wrapper.push_cc(game_id=cc_info[0], turn_num=cc_info[1], bust=cc_info[2],
                                        blackjack=cc_info[3], exceedWinningPlayer=cc_info[4],
                                        alreadyExceedingWinningPlayer=cc_info[5], move=cc_info[6])

    # returns true if the user enters that they want to continue playing
    def get_continue_playing(self):
        inp = ""
        res = None
        while inp != "y" and inp != "n":
            inp = input("Would you like play another? (y or n) ")
            if inp != "y" and inp != "n":
                print("please enter y or n")
        if inp == "y":
            res = True
        elif inp == "n":
            res = False
        return res

    # outputs the winners
    def display_winners(self, winning_hands):
        winning_val = winning_hands[0].get_value()
        print("Winners!!", winning_val)
        for hand in winning_hands:
            print(hand.id)
        print()

    # dynamic agent selection
    def pick_agent(self, avgWr, agent_win_streak):
        agents = ["nn", "cc_ai", "simple"]
        if avgWr > 0.3:
            agent = "nn"
        elif avgWr > 0.2:
            agent = "cc_ai"
        else:
            agent = "simple"
        # push it down to a lower difficulty if agent is on a high win streak
        if agent_win_streak > 5 and agent != "simple":
            new_agent_ind = agents.index(agent)
            agent = agents[new_agent_ind + 1]
        return agent

if __name__ == "__main__":
    players = ["mr_aqa"]
    ce = Console_Env(players)
    ce.play_game()
    #ce.db_wrapper.execute_queries("DELETE FROM users WHERE username='Mrs_qaaq'")
    #ce.db_wrapper.display_all_records("users")
