from Structs.Stack import Stack
from enum import Enum
from random import shuffle

"""
    - defines functionality for the stack-backed deck
    - defines the card class
"""

# defines enums for suits and royals
# improves readability of code
class Suits(Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"

class Royals(Enum):
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

# Card made up of a suit and a value
# and some simple behaviours
class Card:
    def __init__(self, suit, value):
        self.__suit = suit
        self.__value = value

    @property
    def value(self):
        return self.__value

    @property
    def suit(self):
        return self.__suit

    def isRoyal(self):
        return isinstance(self.__value, Royals) and not self.isAce()

    def isAce(self):
        return self.__value == Royals.ACE

    def __str__(self):
        return "{} {}".format(self.__suit, self.__value)

    def __eq__(self, other_card):
        if isinstance(self, other_card.__class__):
            return (self.__dict__ == other_card.__dict__)
        return False

# stack-backed deck, auto shuffle, when there is nothign in the deck
class Deck(Stack):
    def __init__(self):
        self.__DECK_SIZE = 52
        self.__deckIteration = 1
        self.__autoShuffleWhenEmpty = True
        self.__suits = [suit for suit in Suits]
        self.__values = [num for num in range(2, 11)] + [royal for royal in Royals]
        super().__init__(self.__DECK_SIZE)
        self.init_deck()

    @property
    def deckIteration(self):
        return self.__deckIteration

    def autoShuffleOff(self):
        self.__autoShuffleWhenEmpty = False

    def autoShuffleOn(self):
        self.__autoShuffleWhenEmpty = True

    # populates the deck randomly
    def init_deck(self):
        temp_deck = []
        for suit in self.__suits:
            for value in self.__values:
                temp_deck.append(Card(suit, value))
        shuffle(temp_deck)
        for card in temp_deck:
            self.push(card)

    # Removes top object from stack - autoshuffles deck when it is empty
    def pop(self):
        popped = super().pop()
        if self.isEmpty() and self.__autoShuffleWhenEmpty:
            self.init_deck()
            self.__deckIteration += 1
        return popped

    # test method showing contents of deck
    def display_and_empty(deck):
        while not deck.isEmpty:
            print(deck.pop)

if __name__ == "__main__":
    d = Deck()
    print(isinstance(Card(Suits.SPADES, Royals.QUEEN).value, Royals))
