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

    def public_state_update(self, state, turn_actions):
        pass

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
        print(self.private_state)

    def make_move(self, valid_moves, state):
        #TODO: implement CLI interface to the game
        print(state)
        print("Valid Moves: ")
        #note: all moves are given as [movetype, target]
        move_dict = {}
        for move in valid_moves:
            if move[0] not in move_dict.keys():
                move_dict[move[0]] = []
            move_dict[move[0]].append(move)
        move_type_list = move_dict.keys()

        if state.state_class == StateQuality.ACTION:

            print("Select move type: ")
            for i in range(len(move_type_list)):
                print(str(i) + ": " + move_type_strings[move_type_list[i]])
            selection = int(input("Select move number:" ))
            selected_move_type = move_type_list[selection]

            print("Possible targets: ")
            targets = [move_dict[selected_move_type][i][1] for i in range(len(move_dict[selected_move_type]))]
            target_str = ""
            for i in range(targets):
                target_str += "Player " + str() + ", "
            target_str = target_str[:len(target_str)-2] 
            print(target_str)
            selected_target = int(input("Select player:"))

            if selected_target not in targets:
                selected_target = targets[0]
                print("Invalid player. Default to player 0")
            
            return [selected_move_type, selected_target]

        elif state.state_class == StateQuality.CHALLENGEACTION:
            print("Select move type: ")
            for i in range(len(move_type_list)):
                print(str(i) + ": " + move_type_strings[move_type_list[i]])
            selection = int(input("Select move number:" ))
            selected_move_type = move_type_list[selection]

            return move_dict[selected_move_type][0]

        elif state.state_class == StateQuality.COUNTER:
            print("Select move type: ")
            for i in range(len(move_type_list)):
                print(str(i) + ": " + move_type_strings[move_type_list[i]])
            selection = int(input("Select move number:" ))
            selected_move_type = move_type_list[selection]

            return move_dict[selected_move_type][0]

        elif state.state_class == StateQuality.CHALLENGECOUNTER:
            print("Select move type: ")
            for i in range(len(move_type_list)):
                print(str(i) + ": " + move_type_strings[move_type_list[i]])
            selection = int(input("Select move number:" ))
            selected_move_type = move_type_list[selection]

            return move_dict[selected_move_type][0]

    def public_state_update(self, state, turn_actions):
        print("Current state at the end of the turn: ")
        print(state)
        for action in turn_actions:
            print(action[1])
