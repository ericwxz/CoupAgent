import random

def Agent():
    def __init__():
        self.private_state = None

    def make_move(self, valid_moves, state):
        pass

    def set_private_state(self, private_state)
        self.private_state = private_state

    #used to update private state after an exchange
    def update_observations(self, deck_cards, state):
        self.private_state.sightings.extend(deck_cards)
        
    def lose_card(self, card):
        self.private_state.cards.remove(card)

def RandomAgent(Agent):
    def make_move(self, valid_moves, state):
        return random.choice(valid_moves)

def HumanAgent(Agent):
    def __init__(self, index):
        self.private_state = None 
        #for CLI printing purposes
        self.index = index

    def set_private_state(self, private_state):
        self.private_state = private_state 
        #TODO: add print for CLI    

    def make_move(self, valid_moves, state):
        #TODO: implement CLI interface to the game
        pass 

    
