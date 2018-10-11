from Blackjack import Blackjack
from Blackjack import Hand
from Agent import Agent
from Moves import Moves

"""
    - threshold based agent, which makes it's own calculations
    - behaviour is defined by thresholds
"""

class Simple_AI(Agent):
    def __init__(self, hand=None, parameters=None):
        super().__init__(ID="simple", type=["Simple"])
        self.blackjack_value = 21
        self.maxCard = 11
        self.bust_value = self.blackjack_value + 1
        self.hand = hand

        if parameters is None:
            self.set_parameters(setting="default")
        if hand is None:
            self.hand = Hand(self.ID)

    def set_parameters(self, setting="default"):
        if setting == "default":
            self.win_margin_threshold = 1
            self.bust_threshold = 3
            self.min_hand_threshold = 15
        elif setting == "aggressive":
            self.win_margin_threshold = 3
            self.bust_threshold = 7
            self.min_hand_threshold = 18
        elif setting == "passive":
            self.win_margin_threshold = 0
            self.bust_threshold = 1
            self.min_hand_threshold = 13


    # returns decision to hit or not -> true => hit, false => stand
    # stands if blackjacked or winning by a sufficient amount
    # otherwise hits if cannot go bust, or under the bust margin threshold
    def get_move(self, all_players):
        next_best_hand = self.get_best_hand(all_players)
        best_player_value = next_best_hand.get_value()
        best_player_stood = next_best_hand.has_stood

        hand_value = self.hand.get_value()
        win_margin = hand_value - best_player_value

        # if blackjack'd or winning by a sufficient amount
        if hand_value == self.blackjack_value or \
           (win_margin > self.win_margin_threshold and hand_value > self.min_hand_threshold):
            return Moves.STAND
        # If cannot go bust, or edge case satisfied then hit
        elif (hand_value < (self.bust_value - self.maxCard)
              or self.edge_move_calc(hand_value, best_player_value)):
            return Moves.HIT
        return Moves.STAND

    # HAVE A LOOK AT THIS
    def edge_move_calc(self, hand_value, best_value):
        bustDiff = abs(hand_value - self.bust_value) # how far off being bust SAI is
        LTBestPlayer = hand_value < best_value and best_value <= 21
        if LTBestPlayer or bustDiff <= self.bust_threshold:
            return True
        return False

    def update_end_game(self, new_cards):
        pass
