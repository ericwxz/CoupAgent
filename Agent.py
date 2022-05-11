import random
from GeneralCoup import *

#######################################
# extra definitions not used in game implementation 
# that may be useful for agents

class ExtendedStateQuality(enum.Enum):
    LOSE_CARD = 5
    LOSE_CARD_ACTION = 6
    LOSE_CARD_CHALLENGE_ACTION = 7
    LOSE_CARD_CHALLENGE_COUNTER = 8

class LoseInfluenceMoveType(enum.Enum):
    LOSE_DUKE = 12
    LOSE_CAPTAIN = 13
    LOSE_ASSASSIN = 14
    LOSE_CONTESSA = 15
    LOSE_AMBASSADOR = 16

class LoseDukeMove(BaseMove):
    #for consistency, target is included as an init field but should =player
    def __init__(self, player, target):
        self.card_type = InfluenceType.duke
        BaseMove.__init__(player, target)
    
class LoseCaptainMove(BaseMove):
    def __init__(self, player, target):
        self.card_type = InfluenceType.captain
        BaseMove.__init__(player, target)

class LoseAssassinMove(BaseMove):
    def __init__(self, player, target):
        self.card_type = InfluenceType.assassin
        BaseMove.__init__(player, target)

class LoseContessaMove(BaseMove):
    def __init__(self, player, target):
        self.card_type = InfluenceType.contessa
        BaseMove.__init__(player, target)

class LoseAmbassadorMove(BaseMove):
    def __init__(self, player, target):
        self.card_type = InfluenceType.ambassador
        BaseMove.__init__(player, target)

lose_influence_type = {InfluenceType.duke:LoseInfluenceMoveType.LOSE_DUKE,
                        InfluenceType.captain:LoseInfluenceMoveType.LOSE_CAPTAIN,
                        InfluenceType.assassin:LoseInfluenceMoveType.LOSE_ASSASSIN,
                        InfluenceType.contessa:LoseInfluenceMoveType.LOSE_CONTESSA,
                        InfluenceType.ambassador:LoseInfluenceMoveType.LOSE_AMBASSADOR}

lose_influence_action_to_type = {LoseInfluenceMoveType.LOSE_DUKE:InfluenceType.duke,
                        LoseInfluenceMoveType.LOSE_CAPTAIN:InfluenceType.captain,
                        LoseInfluenceMoveType.LOSE_ASSASSIN:InfluenceType.assassin,
                        LoseInfluenceMoveType.LOSE_CONTESSA:InfluenceType.contessa,
                        LoseInfluenceMoveType.LOSE_AMBASSADOR:InfluenceType.ambassador}

lose_card_move_objs = {LoseInfluenceMoveType.LOSE_DUKE:LoseDukeMove,
                        LoseInfluenceMoveType.LOSE_CAPTAIN:LoseCaptainMove,
                        LoseInfluenceMoveType.LOSE_ASSASSIN:LoseAssassinMove,
                        LoseInfluenceMoveType.LOSE_CONTESSA:LoseContessaMove,
                        LoseInfluenceMoveType.LOSE_AMBASSADOR:LoseAmbassadorMove}

extended_move_objs = move_objs | lose_card_move_objs

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
            #num_players (scaled coins)
            #num_players * (5 * 2 bits to represent flipped influence cards (all 0 for no flipped, otherwise one-hot))
            #history with simplifications:
                #(challenges)
                #num_players * (num_players * 1 (scaled) * 5 bits to represent number of times (up to 4) a player has challenged another player on a certain card)
                #(recent history)
                #(num_players * 5(last actions stored) * (12(moves/counters, including null)))
            #number of distinct states used in evaluation, one-hot (6)

        #private state space:
        #size = 5 + 5 possible cards
        num_players = state.players
        #list out starting indexes for each portion of information
        coins_start = 0
        influence_start = num_players 
        challenges_start = influence_start + 10*num_players 
        history_start = challenges_start + 5*num_players
        #simplification: remove inaction encoding (12->11 possible action types to keep in recent memory)
        private_start = history_start + (num_players * 5 * 11)
        quality_start = private_start + 5
        state_size = quality_start + 6

        encoded_state = []

        encoded_state.extend(self._encode_coins(state))
        encoded_state.extend(self._encode_influence(state))
        encoded_state.extend(self._encode_challenges(state))
        encoded_state.extend(self._encode_history(state))
        encoded_state.extend(self._encode_private(self.private_state))
        encoded_state.extend(self._encode_state_class(state))

        return encoded_state
    
    def _encode_coins(self, state):
        encoded_coins = [0 for _ in range(state.players)]
        for i in range(state.players):
            #at 10 coins or more, one must spend coins and coup
            #at 9 coins, the most coins you can accumulate in a single turn is 3 more
            #the most number of coins possibly held at once is 12
            encoded_coins[i] = state.coins[i] / 12.0
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
        #challenge encoding as n groups of (n * 1 * 5) bits
            #each player i has a batch of (n*1*5) bits, representing how many times they
            #  challenged another player (in fourths) on one of 5 cards
        #indexing to player i's batch: i*(n*5)
            #indexing to the number of times player i challenged player j on card type k (from 0 to 4):
                #[ i*(n*5) + j*(5) + (k)) ]
        encoded_challenges = [0 for i in range(state.players * state.players * 5)]
        for key in state.challenge_counts.keys():
            num_challenges = min(4, state.challenge_counts[key])
            #uses enum values for influence cards
            start_index = key[0]*(state.players * 5) + key[1]*(5) + ((key[2].value - 11))
            encoded_challenges[start_index] = num_challenges/4.0
        
        return encoded_challenges

    def _encode_history(self, state):
        #simplification: remove inaction encoding
        encoded_history = [0 for i in range(state.players * 5 * 11)]
        for i in range(state.players):
            for j in range(5):
                recent_move = state.recent_history[i][j]
                if recent_move != -1:
                    encoded_history[i*5*11 + j*11 + (recent_move)] = 1
                
        return encoded_history

    def _encode_private(self, private_state):
        private_encoded = [0 for i in range(5)]
        if len(private_state.cards) >= 1:
            private_encoded[private_state.cards[0].value - 11] += 0.5
        if len(private_state.cards) == 2:
            private_encoded[private_state.cards[1].value - 11] += 0.5

        return private_encoded

    def _encode_state_class(self, state):
        encoded_state_class = [0, 0, 0, 0, 0, 0]
        encoded_state_class[state.state_class.value] = 1
        return encoded_state_class

        


class RandomAgent(Agent):
    def make_move(self, valid_moves, state):
        return random.choice(valid_moves)

class BaselineAgent(Agent):
    def make_move(self, valid_moves, state):
        if len(valid_moves) == 1: 
            return valid_moves[0]
        #split moves into challenge-winnables and unwinnables
        epsilon = 0.2
        safe = 0.2
        if state.state_class == StateQuality.ACTION: 
            unchallengeables = []
            winnables = []
            unwinnables = []
            for move in valid_moves:
                if move[0] in unchallengeable_moves:
                    unchallengeables.append(move)
                elif restricted_moves[move[0]] in self.private_state.cards:
                    winnables.append(move)
                else:
                    unwinnables.append(move)
            pool = random.random()
            if pool < epsilon and len(unwinnables) > 0:
                return random.choice(unwinnables)
            elif pool > (1.0-safe) and len(unchallengeables) > 0:
                return random.choice(unchallengeables)
            elif len(winnables) > 0:
                return random.choice(winnables)
            else:
                return random.choice(valid_moves)
            
        elif state.state_class == StateQuality.CHALLENGEACTION:
            pool = random.random()
            print("DEBUG: valid moves in challengeaction: ")
            print(valid_moves)
            if pool > epsilon:
                return valid_moves[1]
            else:
                return valid_moves[0]
        elif state.state_class == StateQuality.COUNTER:
            if len(valid_moves) == 1: 
                return valid_moves[0]
            winnables = []
            unwinnables = []
            for move in valid_moves:
                if move[0] == -1:
                    winnables.append(move)
                elif restricted_moves[move[0]] in self.private_state.cards:
                    winnables.append(move)
                else:
                    unwinnables.append(move)
            pool = random.random()
            if len(unwinnables) > 0 and pool < epsilon:
                return random.choice(unwinnables) 
            else: 
                return random.choice(winnables)
                
        elif state.state_class == StateQuality.CHALLENGECOUNTER:
            pool = random.random()
            if pool > epsilon:
                return valid_moves[1]
            else:
                return valid_moves[0]
        else:
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

