import random
from GeneralCoup import *
class Agent():
    def __init__(self):
        self.private_state = None

    def make_move(self, valid_moves, state):
        pass

    def set_private_state(self, private_state):
        self.private_state = private_state

    #used to update private state after an exchange
    def update_observations(self, deck_cards, state):
        self.private_state.sightings.extend(deck_cards)
        
    def lose_card(self, card):
        print("DEBUG: losing card " + str(card))
        self.private_state.cards.remove(card)
        print("DEBUG: current cards after losing cards: " + str(self.private_state.cards))

    def public_state_update(self, state, turn_actions):
        pass

class RandomAgent(Agent):
    def make_move(self, valid_moves, state):
        print("DEBUG: Random agent choosing from possible moves: ")
        for i in valid_moves:
            print(i)
        return random.choice(valid_moves)

class HumanAgent(Agent):
    def __init__(self, index):
        Agent.__init__(self)
        #for CLI printing purposes
        self.index = index

    def set_private_state(self, private_state):
        self.private_state = private_state 
        print(self.private_state)

    def make_move(self, valid_moves, state):
        print("DEBUG: own cards: " + str(self.private_state.cards))
        #possible TODO: simplify flow here
        #test for standard "choose card to lose" format
        if not isinstance(valid_moves[0], list):
            #parse possible cards to lose 
            print("Player " + str(self.index) + " lost a challenge. Choose which card to lose: ")
            for i in range(len(valid_moves)):
                print(str(i) + ": " + influence_type_strings[valid_moves[i]])
            selected_card_ind = int(input("Select index of card: "))
            if selected_card_ind > len(valid_moves):
                print("Invalid card index. Defaulting to card 0")
                selected_card_ind = 0
            return valid_moves[selected_card_ind]
            
        else:
            #if in the exchange state, [-1 (do nothing)] is offered as first possible move
            if valid_moves[0] == [-1]:
                #TODO: add exchange mechanism
                print("Valid exchanges: ")
                print("0. " + "Keep existing cards")
                for i in range(1,len(valid_moves)):
                    print(str(i) + ". Exchange " + influence_type_strings[valid_moves[i][0]] + " for " + influence_type_strings[valid_moves[i][1]])
                selected_move = int(input("Select option:"))
                return valid_moves[selected_move]

            else:
                    
                #standard action selection
                print(state)
                print("Valid Moves: ")
                #note: all moves are given as [movetype, target]
                move_dict = {}
                #DEBUG
                print(valid_moves)
                for move in valid_moves:
                    #DEBUG
                    print(move)
                    if move[0] not in move_dict.keys():
                        move_dict[move[0]] = []
                    move_dict[move[0]].append(move)
                move_type_list = list(move_dict.keys())

                if state.state_class == StateQuality.ACTION:
                    

                    print("Select move type: ")
                    for i in range(len(move_type_list)):
                        print(str(i) + ": " + move_type_strings[move_type_list[i]])
                    selection = int(input("Select move number:" ))
                    selected_move_type = move_type_list[selection]

                    print("Possible targets: ")
                    targets = [move_dict[selected_move_type][i][1] for i in range(len(move_dict[selected_move_type]))]
                    target_str = ""
                    for i in range(len(targets)):
                        target_str += "Player " + str(targets[i]) + ", "
                    target_str = target_str[:len(target_str)-2] 
                    print(target_str)
                    selected_target = int(input("Select player:"))

                    if selected_target not in targets:
                        selected_target = self.index
                        print("Invalid player. Default to self")
                    
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
