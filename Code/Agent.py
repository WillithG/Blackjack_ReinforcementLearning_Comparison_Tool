"""
    - Abstract class implementing and initialise needed properties and methods
    - every agent should inheret from this and overrdide the behaviours implemented in this class
"""
import os, sys
sys.path.append(os.path.realpath("./DB"))
from DB_Wrapper import DB_Wrapper
from abc import ABC, abstractmethod

class Agent(ABC):
    # type is an array of strings signifying the type agent
    # eg NN, Card Counter
    def __init__(self, ID="", type=None):
        self.ID = ID
        self.type = type
        self.db_wrapper = DB_Wrapper("DB/Blackjack.sqlite")
        super().__init__()


    # this method will be called at the end of every game, the agent is playing in
    # an example use is for CC agents to decrement their card counter trees
    @abstractmethod
    def update_end_game(self):
        pass

    # Virtual method which will be called in every game that an agent plays in
    # this method returns Moves.HIT or Moves.STAND based on what the angent wants to do
    @abstractmethod
    def get_move(self):
        pass

    # Virtual method which sets the agents parameters, on a discrete scale of
    # "passive", "default", and "aggressive", however will also have a number
    # scale for more customisability
    def set_parameters(self, setting="default"):
        pass

    # mehod which allows the agent to find the next best player in the game
    # all agents do this in the same way, so it is implemented here
    # not necessarily going to be anyone but the current agent
    # pass in list of hands, returns the best hand value, not including tehe agent
    def get_best_hand(self, hands):
        best_hand_value = 0
        best_hand_hand = None
        # find the next best player
        for player in hands:
            if player.id == self.ID or player.bust:
                continue
            player_value = player.get_value()
            if player_value > best_hand_value:
                best_hand_value = player_value
                best_hand_hand = player
        # should never go to this section, because the dealer always plays last and cannot be bust
        if best_hand_hand == None:
            print("NO BEST PLAYER")
            for player in hands:
                if player.id == "dealer":
                    for card in player.hand:
                        print(card)
                    print(player.get_value())
            best_hand_hand = self.get_agent_hand(hands)
        return best_hand_hand

    # pass in list of hands, returns the hand which the agent corresponds to
    def get_agent_hand(self, hands):
        for player in hands:
            if player.id == self.ID:
                return player
