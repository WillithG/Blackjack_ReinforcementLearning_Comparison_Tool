from CC_Agent import CC_Agent
from Blackjack import Hand
from Moves import Moves

"""
    - Threshold based Card Counting AI
"""
class CC_AI(CC_Agent):
    def __init__(self, parameters=None, hand=None):
        super().__init__(ID="cc_ai")
        self.parameters = parameters
        self.Hand = hand
        if parameters is None:
            self.set_parameters(setting="default")
        if hand is None:
            self.Hand = Hand(self.ID)

    # entire agent bevahiour defined here
    # will hit if below best player or below bust threshold or below the minimum hand threshold
    # beyond that, it will hit, in risky situations defined by it's parameters which maps to an aggression rating
    def getNextAction(self, chances, game_state):
        # not exceeding the dealer, hit.
        playerHandValue = game_state[0].get_value()
        bestHandValue = game_state[1].get_value()

        winMargin =  playerHandValue - bestHandValue
        belowBestPlayer = (winMargin < 0) and bestHandValue <= 21
        belowBustThreshold = chances["bust"] <= self.parameters["bust_tol"]
        highBlackjackChance = chances["blackjack"] >= self.parameters["blackjack_thresh"]
        belowWinMarginThresh = winMargin < self.parameters["winMarginThresh"]
        belowMinHandThresh = playerHandValue < self.parameters["minHandThresh"]

        # BEHAVIOUR: Hit IF:
        # - losing or below the bust threshold or below the min hand threshold or below min hand threshold/win margin threshold
        # - or winning, above the bust threshold and below the risky bust threshold
        if (belowBestPlayer or belowBustThreshold or belowMinHandThresh):
            return Moves.HIT
        elif highBlackjackChance:
            belowRiskyBustThreshold = chances["bust"] <= self.parameters["bust_tol"] * self.parameters["riskTolerance"]
            if belowRiskyBustThreshold:
                return Moves.HIT
        elif belowWinMarginThresh:
            return Moves.HIT
        return Moves.STAND

    # Sets the  parameters of the CCAI
    def set_parameters(self, setting="default"):
        # Change these parameters to change the behaviour of the CCAI
        # Change these to personality parameters, then calculate these thresholds based on parameters
        if isinstance(setting, dict):
            self.parameters = setting #todo check to see if all the keys are in here

        if setting == "default":
            self.parameters = {
                "bust_tol" : 0.5,
                "blackjack_thresh" : 0.2,
                "riskTolerance" : 1.3,
                "winMarginThresh" : 5,
                "minHandThresh" : 15
            }
        elif setting == "aggressive":
            pass
        elif setting == "passive":
            pass
