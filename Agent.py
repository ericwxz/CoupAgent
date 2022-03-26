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
        self.private_state.cards.remove(card)

    def public_state_update(self, state, turn_actions):
        pass

    def encode_state(self, state):
        #public state space as one-hot encoding of most features 
        #size = 
            #num_players * (4 bits to represent max coins)
            #num_players * (5 * 2 bits to represent flipped influence cards (all 0 for no flipped, otherwise one-hot))
            #history with simplifications:
                #(challenges)
                #num_players * (num_players * 2 * 5 bits to represent number of times (up to 4) a player has challenged another player on a certain card)
                #(recent history)
                #(num_players * 5(last actions/counters) * (11(moves/counters)*num_players)(permutations of possible actions))
        #private state space:
        #size = 5 + 5 possible cards
        num_players = state.players
        #list out starting indexes for each portion of information
        coins_start = 0
        influence_start = 4*num_players 
        challenges_start = influence_start + 10*num_players 
        history_start = challenges_start + 10*num_players
        private_start = history_start + (num_players * 5 * (11 * num_players))
        state_size = private_start + 10

        encoded_state = [0 for i in range(state_size)]

        #TODO


        return encoded_state

    def _encode_coins(self, state):
        encoded_coins = []
        for i in range(state.players):
            #format into binary string and split into list
            single_coin_arr = list('{0:04b}'.format(state.coins[i]))
            for j in range(4):
                #convert into int values
                single_coin_arr[j] = int(single_coin_arr[j])
            encoded_coins.extend(single_coin_arr)
        return encoded_coins

    def _encode_influence(self, state):
        encoded_influence = []
        for i in range(state.players):
            flipped_influences = state.cards[i]
            flipped_influence_encoding = [0 for i in range(10)]
            if flipped_influences[0] != -1:
                #use indexing from influences enum defined in GeneralCoup.py
                flipped_influence_encoding[flipped_influences[0].value - 11] = 1
            if flipped_influences[1] != -1:
                flipped_influence_encoding[flipped_influences[1].value - 6] = 1
            encoded_influence.extend(flipped_influence_encoding)
        return encoded_influence

    def _encode_challenges(self, state):
        #challenge encoding as n groups of (n * 2 * 5) bits
            #each player i has a batch of (n*2*5) bits, representing how many times they
            #  challenged another player (2 bits) on one of 5 cards
        #indexing to player i's batch: i*(n*2*5)
            #indexing to the number of times player i challenged player j on card type k (from 0 to 4):
                #the two binary digits starting at [ i*(n*2*5) + j*(2*5) + (2*k)) ]
        encoded_challenges = [0 for i in range(state.players * state.players * 2 * 5)]
        for key in state.challenge_counts.keys:
            num_challenges = min(4, state.challenge_counts[key])
            #uses enum values for influence cards
            start_index = key[0]*(state.players * 2 * 5) + key[1]*(2*5) + (2*(key[2].value - 11))
            num_challenges_binlist = list('{0:02b}'.format(num_challenges))
            encoded_challenges[start_index] = num_challenges_binlist[0]
            encoded_challenges[start_index + 1] = num_challenges_binlist[1]
        
        return encoded_challenges

    def _encode_history(self, state):
        #TODO: do updating of recent history and maintenance in main state/gameplay loop
        
        pass

    def _encode_private(self, private_state):
        private_encoded = [0 for i in range(10)]
        if len(private_state.cards) >= 1:
            private_encoded[private_state.cards[0].value - 11] = 1
        if len(private_state.cards) == 2:
            private_encoded[private_state.cards[1].value - 6] = 1

        return private_encoded

        


class RandomAgent(Agent):
    def make_move(self, valid_moves, state):
        return random.choice(valid_moves)

class HumanAgent(Agent):
    def __init__(self, index):
        Agent.__init__(self)
        #for CLI printing purposes
        self.index = index

    def set_private_state(self, private_state):
        self.private_state = private_state 
        print(self.private_state)
        print()

    def make_move(self, valid_moves, state):
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
                print()
                print("Player " + str(self.index) +  " needs to make a choice...")
                #note: all moves are given as [movetype, target]
                move_dict = {}
                for move in valid_moves:
                    if move[0] not in move_dict.keys():
                        move_dict[move[0]] = []
                    move_dict[move[0]].append(move)
                move_type_list = list(move_dict.keys())

                if state.state_class == StateQuality.ACTION:
                    
                    print("Select basic action type: ")
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
                    print("Select whether or not to challenge the last action: ")
                    for i in range(len(move_type_list)):
                        print(str(i) + ": " + move_type_strings[move_type_list[i]])
                    selection = int(input("Select move number:" ))
                    selected_move_type = move_type_list[selection]

                    return move_dict[selected_move_type][0]

                elif state.state_class == StateQuality.COUNTER:
                    print("Select counter option: ")
                    for i in range(len(move_type_list)):
                        print(str(i) + ": " + move_type_strings[move_type_list[i]])
                    selection = int(input("Select move number:" ))
                    selected_move_type = move_type_list[selection]

                    return move_dict[selected_move_type][0]

                elif state.state_class == StateQuality.CHALLENGECOUNTER:
                    print("Select whether or not to challenge the counter: ")
                    for i in range(len(move_type_list)):
                        print(str(i) + ": " + move_type_strings[move_type_list[i]])
                    selection = int(input("Select move number:" ))
                    selected_move_type = move_type_list[selection]

                    return move_dict[selected_move_type][0]

    def public_state_update(self, state, turn_actions):
        print("\nCurrent state at the end of the turn: ")
        print(state)
        print("Actions made over the course of the past turn:")
        for i in range(len(turn_actions)):
            print("  " + str(i+1) + ". " + str(turn_actions[i][1]))
        print()
        print(str(self.private_state))
        print("--------------------------------------------")


#TODO: for imperfect info agent, state simplification mostly in history->set of times a player has asserted a card, but need temporal element of exchange encoded somehow 
#TODO: for challenge simplification, straightforward-- this plalyer has challenged this other player on having x card n times
#TODO: perhaps including recent move history in state encoding-- temporal element of "recent history" part of state cycling out an exchange action might be enough information for black box?