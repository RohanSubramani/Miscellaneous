import random

class Card():
    def __init__(self,suit=str,rank=int):
        self.suit = suit
        self.rank = rank
    def __repr__(self):
        return f"{self.rank}{self.suit}"

class Deck():
    def __init__(self):
        self.deck = []
        for suit in ["S","H","D","C"]:
            for rank in range(1,14):
                self.deck.append(Card(suit,rank))
        self.shuffle()
    
    def shuffle(self):
        for i in range(1000):
            self.swap()
    
    def swap(self):
        pos_a = random.randint(0,51)
        pos_b = random.randint(0,51)
        a = self.deck[pos_a]
        b = self.deck[pos_b]
        self.deck[pos_b] = a
        self.deck[pos_a] = b
    
    def deal(self, num):
        dealt_cards = self.deck[:num]
        self.deck = self.deck[num:]
        return dealt_cards

    def __repr__(self):
        a,b,c = tuple(self.deck[:3])
        return f"{a}, {b}, {c}, ..."