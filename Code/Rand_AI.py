from Blackjack import Hand
from Agent import Agent
from Moves import Moves
from random import randint

"""
    - Agent which takes a random action every turn
    - Control Agent
"""

class Rand_AI(Agent):
    def __init__(self, hand=None):
        super().__init__(ID="rand", type=["Random"])
        self.hand = hand
        if hand is None:
            self.hand = Hand(self.ID)

    def get_move(self, *args):
        move_bit = randint(0, 1)
        return Moves.convert_to_move(move_bit)

    def update_end_game(self, new_cards):
        pass
