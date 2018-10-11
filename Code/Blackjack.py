from Deck import Deck
from Deck import Royals
from random import shuffle
from Structs.Circular_Queue import Circular_Queue

"""
    Class which implemetents a blackjack environment
    - usage call hit() or stand() based on what action you want to take
    - winners stored in _winners
    - call check_game_over() to check if game is over
    - then call end_game() to determine the winners
    - then reset() to reset the env
"""

class Blackjack:
    # playersDict is a dictionary <String => Hand> where the key is the name
    # of the player and the mapped value is their hand
    def __init__(self, playersDict=None):
        self.deck = Deck()
        self._blackjack = 21 # The winning value
        self._winners = [] # List of ids of the winners of the previous game
        self._beat_dealer = []
        self.turnNumber = 1
        self.auto_reset = False

        # defensive programming - if nothing is passed, default playersDict
        if playersDict is None:
            playersDict = {
                "dealer": Dealer_Hand("dealer")
            }

        # if dealer has not been added, add the dealer to playersDict
        if bool(playersDict) is False or "dealer" not in playersDict.keys():
            playersDict["dealer"] = Dealer_Hand("dealer")

        self.players = playersDict

        # queue which holds the player hands, keeps track of whose turn it is
        # pop to get the next player, and push if they are still in the game
        # game over when nobody left in the queue
        self.players_queue = self.create_player_queue()

        self.continue_game = True
        self.deckIteration = self.deck.deckIteration # tracks deck resets
        self.new_cards = [] # each time a new card is added to the game this it is appended to here

        # Deals to each player
        self.init_deal()

    @property
    def winners(self):
        return self._winners

    def blackjack(self):
        return self._blackjack

    # returns circular queue storing player hands, determining the order of play
    # random order each time
    def create_player_queue(self):
        playerList = [self.players[key] for key in self.players.keys() if self.players[key].id != "dealer"]
        shuffle(playerList)
        cQ = Circular_Queue(len(playerList))
        for player in playerList:
            cQ.push(player)
        return cQ

    # returns the player id whose turn it is
    def get_current_player(self):
        return self.players_queue.peek().id

    # Reset the hands and the tracking variables
    def reset(self):
        for key in self.players.keys():
            self.players[key].reset()
        self.continue_game = True
        self.init_deal()
        self.players_queue = self.create_player_queue()
        self.new_cards = []
        self.turnNumber = 1

    # deals two cards to every player, called at the start of the game
    def init_deal(self):
        for key in self.players.keys():
            for x in range(2):
                self.deal(self.players[key])

    # compares the hands of the passed players
    # returns the winners of teh game
    def compare_hands(self):
        best_hand = [] # array of player ids
        best_value = 0
        for key in self.players.keys():
            current_player = self.players[key]
            current_player_name = current_player.id
            current_player_value = current_player.get_value()
            if current_player.bust:
                continue
            elif best_hand is []:
                best_value = current_player_value
                best_hand.append(current_player_name)
            elif current_player_value >= best_value:
                # if equal to, going to append anyways, so do not need to do anything if equal to.
                if current_player_value == best_value:
                    pass
                elif current_player_value > best_value:
                    best_hand[:] = []
                    best_value = current_player_value
                best_hand.append(current_player_name)
        return best_hand

    # Deals a card to players passed
    def deal(self, *args):
        for player in args:
            next_card = self.deck.pop()
            player.hit(next_card)
        # updates the deck iteration, if the deck has reset
        if self.deckIteration != self.deck.deckIteration:
            self.deckIteration = self.deck.deckIteration

    # pops the next player and then hits their hand
    # if they go bust do not push them back onto the queue
    def hit(self):
        current_player = self.players_queue.pop()
        self.deal(current_player)
        self.turnNumber += 1
        if current_player.bust:
            self.check_game_over()
        else:
            self.players_queue.push(current_player)


    # pop the next player and stand
    # do not push them back onto the queue
    def stand(self):
        current_player = self.players_queue.pop()
        current_player.stand()
        self.turnNumber += 1
        self.check_game_over()

    # Outputs the current state of the game to console
    # - each hand contents followed by their current value.
    def display_game(self):
        for key in self.players.keys():
            currentPlayer = self.players[key]
            print(currentPlayer.id, end = " ")
            for card in currentPlayer.hand:
                print(card, end = " ")
            p_total = currentPlayer.get_value()
            print(str(p_total))

    # Calls all the methods associated with ending the game, and return winner
    def end_game(self):
        # dealer deals to itself until it reaches above its threshold hand value
        self.players["dealer"].dealer_end(self.deck)
        self._winners = self.compare_hands()
        self.update_new_cards()
        if self.auto_reset:
            self.reset()
        return self._winners

    # appends all cards dealt that game to the new_cards array
    # alternative: append each card as it is being dealt
    def update_new_cards(self):
        for player_id, player_hand in self.players.items():
            for card in player_hand.hand:
                self.new_cards.append(card)

    # check if everyone has bust or stood
    # game is over if the players_queue is empty
    def check_game_over(self):
        if self.players_queue.isEmpty():
            self.continue_game = False
            #self.end_game() # end game manually
            return True
        return False

    # converts player queue to array and returns the Hands of all players currently in play
    def get_all_hands_playing(self):
        players = []
        while not self.players_queue.isEmpty():
            #print("gapp", self.players_queue.peek())
            current_player = self.players_queue.pop()
            players.append(current_player)
        for player in players:
            self.players_queue.push(player)
        return players

    # returns array of ints
    # each element is the hand value of a player
    def get_all_hand_values(self):
        hand_values = []
        for key in self.players.keys():
            hand_val = self.players[key].get_value()
            hand_values.append(hand_val)
        return hand_values

    # returns all hands in self.players dictionary as an array, in no particular order
    def get_all_hands(self):
        toReturn = []
        for key, hand in self.players.items():
            toReturn.append(hand)
        return toReturn

"""
    - class to handle functionality of each hand
    - has player id associated with it
    - handles hit and stand functionality
    - automatically picks best ace value for the player
"""
class Hand:
    def __init__(self, id):
        self._id = id
        self._hand = []
        self.__has_stood = False
        self._bust = False
        self.blackjack = 21
        self.Royals = {  # Defines the values for the royals
            Royals.JACK: 10,
            Royals.QUEEN: 10,
            Royals.KING: 10,
            Royals.ACE: 11
        }

    @property
    def id(self):
        return self._id

    @property
    def hand(self):
        return self._hand

    @property
    def has_stood(self):
        return self.__has_stood

    @property
    def bust(self):
        return self._bust

    # Only blackjack parent class will have access to the deck, will pass it to cards
    def hit(self, card):
        self._hand.append(card)
        hand_value = self.get_value()
        if hand_value > self.blackjack:
            self._bust = True

    def stand(self):
        self.__has_stood = True

    # Calculate the best total value of the passed hand (where hand is an array of cards)
    def get_value(self):
        total = 0
        noAces = 0
        for card in self._hand:
            cValue = card.value
            if isinstance(cValue, Royals):
                cValue = self.Royals[cValue]
                if card.value == Royals.ACE:
                    noAces += 1
            total += cValue
        if noAces > 0:
            total = self.__choose_ace(total, noAces)
        return total

    # If bust, changes the ace from 11 to a 1.
    def __choose_ace(self, total, noAces):
        for _ in range(noAces):
            if total > self.blackjack:
                total -= 10
        return total

    # resets teh hand and tracking variables
    def reset(self):
        self._hand = []
        self.__has_stood = False
        self._bust = False

    # returns true if this hand is out of the game
    def bust_or_stood(self):
        return self.bust or self.__has_stood

    def get_hand_size(self):
        return len(self._hand)

    def __str__(self):
        return self.id

    # equality comparison to check if two hands are equal
    def __eq__(self, other):
        if not isinstance(other, Hand):
            return False
        return self.id == other.id


# child class which is to be used for the dealer only
# only new method is the dealer_end() method which
# takes in the deck and deals to self until it gets above 17
class Dealer_Hand(Hand):
    def __init__(self, id="dealer"):
        super().__init__(id)
        self.dealer_threshold = 17

    # should you not do this in the blackjack class?
    def dealer_end(self, deck):
        while self.get_value() < self.dealer_threshold and not self.bust:
            self.hit(deck.pop())

"""
    - test class which allows for manual testing of the blackjack environment
    - including possibility to play a game from the console
"""
class Blackjack_Tests:
    @staticmethod
    def setUp_Blackjack_Instance():
        player1 = Hand("mariusz")
        player2 = Hand("vince")
        dealer = Dealer_Hand("dealer")

        # testhand = Hand("mariusz")
        # print(testhand == player1)

        players = {
            "player1": player1,
            "player2": player2,
            "dealer": dealer
        }
        bj = Blackjack(players)
        return bj

    # allows client to play a game of blackjack via the console
    @staticmethod
    def manual_test():
        bj = Blackjack_Tests.setUp_Blackjack_Instance()
        for x in range(2):
            while bj.continue_game:
                bj.display_game()
                currPlayer = bj.whoseTurnIsIt()
                c = input("\n" + currPlayer + ": would you like to hit (h) or (s) ")
                if c is "h":
                    bj.hit()
                elif c is "s":
                    bj.stand()
                else:
                    print("please input h or s")
            bj.display_game()
            bj.end_game()
            print(bj.winners, "are the winners!")
            bj.reset()

    @staticmethod
    def get_players_playing_test():
        bj = Blackjack_Tests.setUp_Blackjack_Instance()
        for i in bj.get_all_players_playing():
            print(i)

if __name__ == "__main__":
    print(Royals)
    #Blackjack_Tests.manual_test()
