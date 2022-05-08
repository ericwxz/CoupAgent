from Agent import Agent
from GeneralCoup import *
import itertools 

import keras
from keras.models import Sequential 
from keras.layers import Dense, Dropout
from keras.optimizers import SGD

####subgame depth in terms of complete turns (set of ACTION-CHALLENGE-COUNTER-CHALLENGE phases)
SUBGAME_DEPTH = 2
CFR_DEPTH = 8
DISTINCT_SAMPLES = 5

starting_deck = [InfluenceType.duke, InfluenceType.duke, InfluenceType.duke,
                InfluenceType.assassin, InfluenceType.assassin, InfluenceType.assassin,
                InfluenceType.captain, InfluenceType.captain, InfluenceType.captain, 
                InfluenceType.ambassador, InfluenceType.ambassador, InfluenceType.ambassador, 
                InfluenceType.contessa, InfluenceType.contessa, InfluenceType.contessa]
possible_hands = list(itertools.combinations(starting_deck,2))
set_of_hands = [i for i in set(possible_hands)]
exchange_possibilities = list(set(possible_hands) - set([(InfluenceType.duke, InfluenceType.duke), (InfluenceType.assassin, InfluenceType.assassin), (InfluenceType.captain, InfluenceType.captain), (InfluenceType.ambassador, InfluenceType.ambassador), (InfluenceType.contessa, InfluenceType.contessa)]))


class BeliefState:
    def __init__(self, game, player_index, num_players, public_state, private_state, prob_distribution = None):
        self.index = player_index
        self.num_players = num_players
        #full public state obj; if passed as input to a model, it will be encoded
        self.public_state = public_state
        #own private state
        self.private_state = private_state
        #probabilities player i has hand type j (index in set_of_hands) given by self.s_d[i][j]
        self.prob_distribution = [[0.0 for j in range(len(set_of_hands))] for i in range(num_players)]
        if prob_distribution==None:
            #generate initial probabilities of opponents having each hand 
            starting_deck_copy = starting_deck.copy()
            for card in private_state.cards:
                starting_deck_copy.remove(card)
            in_play = len(starting_deck_copy)
            for i in range(num_players):
                if i == self.index:
                    hand_index = set_of_hands.index(self.private_state.cards)
                    prob_distribution[i][hand_index] = 1.0
                else:
                    for j in range(len(set_of_hands)):
                        first_card = j[0]
                        prob_first = starting_deck_copy.count(first_card) / in_play
                        starting_deck_copy.remove(first_card)
                        second_card = j[1] 
                        prob_second = starting_deck_copy.count(second_card) / (in_play - 1)
                        starting_deck_copy.append(first_card)
                        prob_hand = prob_first*prob_second 
                        prob_distribution[i][j] = prob_hand 

        else:
            self.prob_distribution = state_distribution
        self.non_agent_deck = starting_deck.copy()
        for i in self.private_state.cards:
            self.non_agent_deck.remove(i)
        for flip_set in self.public_state.cards:
            for i in flip_set:
                if i != -1:
                    self.non_agent_deck.remove(i)
        #will be directly edited for subgame traversal purposes
        #self.prev = []
        self.next = {}
        
        #reorder state info as set of "player" and "opponent" public state components to use as keys in strategy dict
        player_formatted = self.private_state.cards.copy()
        if len(player_formatted) < 2:
            player_formatted.append(-1)
        player_formatted.append(self.public_state.coins[self.index])
        self.player_state = player_formatted
        opponents_formatted = []
        for i in range(self.num_players):
            if i != self.index:
                opponents_formatted.extend([j for j in self.public_state.cards[i]])
                opponents_formatted.append(self.public_state.coins[i])
        
        encoded_challenges = [0 for i in range(self.num_players * self.num_players * 5)]
        for key in self.public_state.challenge_counts.keys():
            num_challenges = min(4, self.public_state.challenge_counts[key])
            #uses enum values for influence cards
            start_index = key[0]*(self.num_players * 5) + key[1]*(5) + ((key[2].value - 11))
            encoded_challenges[start_index] = num_challenges/4.0
        opponents_formatted.extend(encoded_challenges)

        #possible TODO: encode more recent history, rather than just the last one
        def last_move(player):
            for move in self.public_state.recent_history[player]:
                if move != -1:
                    return move 
            return -1
        recent_history = [last_move(i) for i in range(self.num_players)]
        opponents_formatted.extend(recent_history)

        self.opponent_state = opponents_formatted

    def encode(self):
        #this can update
        prob_state = []
        for player in prob_state:
            prob_state.extend(player)
        
        return tuple(self.player_state + self.opponent_state + prob_state)

    def is_terminal(self):
        return self.public_state.is_terminal()

    def _next_player(self, public_state):
        def alive(state, target):
            if state.cards[target][0] == -1 or state.cards[target][1] == -1:
                return True 
            return False
        next_player_ind = (public_state.curr_player + 1) % public_state.players
        while not alive(public_state, next_player_ind):
            next_player_ind = (public_state.curr_player + 1) % public_state.players
        
        return next_player_ind

    def eval_action_abstract(self, action_type, action_obj):
        #return list of new private/public state pairs resulting from action
        #NOTE for all states where this player loses card, change state class to appropriate LOSE_CARD state
        #NOTE for all eval starting action points, either direct state change or setting to EXCHANGE is done
        #NOTE for all iterating over players for next state, check for aliveness
        #TODO: also implement history editing/probability checking
        new_publics = []
        new_privates = []
        new_public_base = self.public_state.copy()
        new_private_base = self.private_state.copy()

        if self.public_state.state_class == StateQuality.ACTION:
            if action_type == MoveType.coup:
                #generate all possible result public states w/ statequality = action, curr_player incremented
                #TODO: if target is self, go to LOSE_CARD, otherwise generate possibilities using self.non_agent_deck
            elif action_type == MoveType.income:
                #generate new state, iterate curr_player
                new_public_state.coins[new_public_state.curr_player] += 1
                new_public_base.state_class = StateQuality.ACTION
                new_public_base.action_player = new_public_state.curr_player 
                new_public_base.curr_player = self._next_player(new_public_base)
                new_publics.append(new_public_base)
                new_privates.append(new_private_base)
            else: 
                new_public_base.state_class = StateQuality.CHALLENGEACTION
                new_public_base.action_player = new_public_state.curr_player
                new_public_base.curr_player = self._next_player(new_public_base)
                new_publics.append(new_public_base)
                new_privates.append(new_private_base)

        #if statequality is challengeaction:
            #if action is inaction:
            #   iterate player
            #   change statequality to counter if player = action_player

            #if action is challenge:
            #    generate successful/unsuccessful result states (with all possible flips)
            #    for each result, if initiator and target are alive, change statequality to counter
            #       else if initiator is alive but target is dead from successful challenge:
            #           do not proceed to counter, restart to action
            #           iterate player from action_player
            #
            #       else if initiator is dead from unsuccessful challenge:
            #           do not proceed to counter, restart to action 
            #           iterate player from action_player

        elif self.public_state.state_class == StateQuality.CHALLENGEACTION:
            if action_type == ChallengeMoveType.inaction:

            else:


        #if statequality is counter:
            #if action is inaction: 
            #   complete action, statequality=action, iterate from action_player
            #
            #if action is a counter:
            #   statequality = challengecounter
            #   iterate curr_player

        elif self.public_state.state_class == StateQuality.COUNTER:
            if action_type == CounterMoveType.inaction:

            else:
                

        #if statequality is challengecounter:
            #if action is inaction:
            #   iterate curr_player
            #   if curr_player = initiator of counter, statequality = action, iterate player from action_player
            #if action is a challenge:
            #   generate successful/unsuccessful result states w statequality=action
            #   for each result:
            #       if initiator and target are alive:
            #           evaluate starting action if successful
            #       elif initiaor is alive but target is dead:
            #           #challenge succeeded
            #           eval starting action
            #           iterate player from action_player
            #       elif initiator is dead but target is alive:
            #           don't eval starting action
            #           iterate player from action_player
            #       elif loser is the player:
            #           update state quality to appropriate extended lose_card
        elif self.public_state.state_class == StateQuality.CHALLENGECOUNTER:
            if action_type == ChallengeMoveType.inaction:

            else:

        #if statequality is any lose_card:
            #update state quality based on which move_card
            #remove card from private state into public state
        elif isinstance(self.public_state.state_class, ExtendedStateQuality):

        #if statequality is exchange:
            #exchange with deck
            #update state quality to action
        elif self.public_state.state_class == StateQuality.EXCHANGE:

        
        return new_publics, new_privates

    def eval_action_discrete(self, index, action_type, action_obj, private_states):
        #copy abstract implementation but replace challenge/assasinate/coup/exchange with discrete results
        pass

    def _eval_starting_action(self):
        pass

#Policy that updates according to CFR and returns a strategy at a given PBS
class Policy:
    #TODO: manage index switching for player/opponent in copy()
    def __init__(self, game, index, original_index = None):
        #two dicts have keys: encoded pbs, values: inner dict of keys:action to value
        self._regret = {}
        self._prob_sum = {}
        self.game = game
        #index can change in training; custom pbs reordering done in update and get_strategy
        self.index = index
        self.original_index = original_index

    def _pbs_adjustment(self, pbs, new_index = None):
        if self.original_index == None or new_index == None or new_index == self.original_index:
            return pbs 
        else:
            #to index into existing data fields by new index, swap old and original index info
            #  to maintain equality of game
            pbs.public_state.coins[original_index] = old_coins 
            pbs.public_state.cards[original_index] = old_cards 
            pbs.public_state.coins[original_index] = pbs.public_state.coins[new_index]
            pbs.public_state.cards[original_index] = pbs.public_state.cards[new_index]
            pbs.public_state.coins[new_index] = old_coins 
            pbs.public_state.cards[new_index] = old_cards

            

    
    def get_strategy(self, unadj_pbs, new_index=None):
        pbs = self._pbs_adjustment(unadj_pbs, new_index)
        actions = self.game.add_targets(self.game.valid_actions(self.index, pbs.public_state), self.index, pbs.public_state.action_player, pbs.public_state)
        state_key = pbs.encode()
        if state_key not in self._regret:
            self._regret[state_key] = {a: 0.0 for a in actions}
            self._prob_sum[state_key] = {a: 0.0 for a in actions}
        sum_regret = 0
        for a in actions:
            sum_regret += max(0.0, self.regret[pbs][a])

        strat = {}
        for a in actions:
            if sum_regret > 0.0:
                strat[a] = max(0.0, self._regret[pbs][a])
            else:
                strat[a] = 1.0/num_actions
        
        return strat

    def _cfr(self, hist, weights, depth):
        self_realization_weight = 
        opp_realization_weight = 
        #first check if last state in history is a terminal state for the player
        pub = hist[-1][0]
        priv = hist[-1][1]
        terminal_status = pub.is_terminal()
        if terminal_status == self.index:
            return 100
        elif terminal_status != -1:
            return -100 

        #check if we've reached the depth of the playthrough for CFR; if so, use heuristic
        if depth == 0:
            return self.game.h( #TODO)

    #state_samples should be distinct public/private state pairs
    def update(self, state_samples):
        
        
        
        
        #generate value for each available action


        #update regret/prob_sum[pbs][a] for all a and all pbs
        for a in action_values:


    def copy(self, new_index):
        new_policy = Policy(self.game, new_index, self.index)
        new_policy._regret = self._regret.copy()
        new_policy._prob_sum = self._prob_sum.copy()
        return new_policy


#takes a policy for sampling purposes
class MetaPolicyAgent(Agent):
    def __init__(self, index, num_players, policy):
        self.policy = policy 
        self.num_players = num_players 
        Agent.__init__(index)

    def make_move(self, valid_moves, public_state):
        pbs = BeliefState(self.index, public_state.num_players, public_state, self.private_state)
        strat = self.policy.get_strategy(pbs)
        #TODO: figure out how to actually pull dict[action]->weight into usable form
        #generate PBS
        #feed to policy to get a strategy
        #select from strategy
        pass


############################
#make_move(valid_moves, state):
#  -generate PBS based on state history
#  -self-play based on that PBS, but without adding to training
#       - once terminal, return policy after iterative search
#  -based on policy (probabilities per action), return action


####### takes a pre-trained network and uses it to make decisions
class DetatAgent(Agent):
    def __init__(self, index, num_players):
        self.num_players = num_players
        Agent.__init__(index)
    
    def set_network(self, detat_network):
        self.network = detat_network

    def make_move(self, valid_moves, public_state):
        #generate PBS
        #policy = self-play(pbs)
        #strat = get_strategy(PBS)
        #return based on strategy
        pass

class CoupSubgame:
    #leaves 
    def __init__(self, game, index, init_pbs, leaf_pbs_dict_base = None, leaf_pbs_dict = None):
        self.game = game
        self.index = index
        self.root = init_pbs
        #base leaf heuristic values
        if leaf_pbs_dict_base !=None: 
            self.leaf_pbs_dict_base = leaf_pbs_dict_base
        else:
            self.leaf_pbs_dict_base = {}

        #leaf values adjusted by probabilistic weights
        if leaf_pbs_dict != None:
            self.leaf_pbs_dict = leaf_pbs_dict
        else:
            #take public state, calculate all possible public and private states up to 
            #next, generate initial probabilities without considering policy
            self.init_subgame(self.root, SUBGAME_DEPTH)
            self.leaf_pbs_dict = self.leaf_pbs_dict_base.copy()

    def init_subgame(self, pbs, depth, h):
        #recursive call to generate all pbs nodes in subgame and set leaf values as heuristic
        
        #if depth = 0, return self
        if depth == 0:
            #NOTE: possible efficiency improvement can be done
            if pbs.encode() not in self.leaf_pbs_dict_base:
                self.leaf_pbs_dict_base[pbs.encode()] = 0
            self.leaf_pbs_dict_base[pbs.encode()] += h(pbs.encode())
            return pbs

        #generate all possible resulting public/private pairs from this pbs
        #for each distinct state, add init_subgame(pbs, depth-1) to list of pbs.next
        new_depth = depth 

        #iterate over all possible actions
        all_actions = self.game.add_targets(self.game.valid_actions(self.index, pbs.public_state), self.index, pbs.public_state.action_player, pbs.public_state)
        result_states = []
        result_states.extend([pbs.eval_action_abstract(a) for a in all_actions])
        for i in range(len(all_actions)):
            public = result_states[i][0]
            private = result_states[i][1]
            terminal_status = public.is_terminal()
            if terminal_status != -1:
                #generate pbs, encode, check/add to list
                terminal_pbs = BeliefState(pbs.index, pbs.num_players, public, private)
                terminal_pbs_encoded = terminal_pbs.encode()
                if terminal_pbs_encoded not in self.leaf_pbs_dict_base:
                    self.leaf_pbs_dict_base[terminal_pbs_encoded] = 0
                self.leaf_pbs_dict_base[terminal_pbs_encoded] = 100 if terminal_status == self.index else -100
                pbs.next[all_actions[i]] = terminal_pbs
            else:
                new_pbs = BeliefState(pbs.index, pbs.num_players, public, private)
                #only increment depth for the completion of a whole "turn"
                if new_pbs.public_state.state_class == StateQuality.ACTION:
                    new_depth = depth-1
                result_layer = init_subgame(new_pbs, new_depth)
                pbs.next[all_actions[i]] = result_layer

    #policy 1 is "self-policy", policy2 is the policy for all opponents
    #note: policy2 should have indexing updated before passing to update_leaves
    def update_leaves(self, policy1, policy2):
        self._update_by_weight(self.root, 1.0, policy, policy2)
        

    def _update_by_weight(self, pbs, weight, policy1, policy2)
        pbs_encoded = pbs.encode()
        if pbs_encoded in self.leaf_pbs_dict:
            self.leaf_pbs_dict[pbs_encoded] = self.leaf_pbs_dict_base[pbs_encoded] * weight

        if pbs.public_state.curr_player == self.index:
            strat = policy1.get_strategy(pbs)
        else:
            strat = policy2.get_strategy(pbs, pbs.public_state.curr_player)

        for action in strat:
            new_weight = weight * strat[action]
            new_pbs = pbs.next[action]
            self._update_by_weight(new_pbs, new_weight, policy1, policy2)


    def sample_playthrough(self, policy1, policy2):
        #return a list of distinct (public, private) pairs from playthrough as well as last PBS leaf
        #   the cards from the opponent(s) are randomized based on available cards
        pass
            

####### Trains a network through self-play
class DetatNetwork:
    def __init__(self,game):
        self.game = game 
        self._model = None
        self.curr_policy = None
        self.training_data = {}

    def save(self, filename):
        if self._model == None:
            print("Not saving model: no model loaded or built")
            return 
        self._model.save(filename) 

    def load(self,filename):
        self._model = keras.models.load_model(filename)

    def self_play(self, PBS, training=True):
    #   while(PBS.not_terminal)
    #  -policy, iter_policy = init_policy(PBS) #set both
    #   TODO: construct subgame class and generate via __init__(PBS), containing leaf fields and leaf_value fields
    #  -subgame = construct_subtree(PBS) 
    #       ##generate all possible distinct states at SUBGAME_DEPTH
    #  -subgame.leaf_pbs = generate_leaf_values(PBS, policy, iter_policy) 
    #       ##generate PBSs for each leaf in the subgame, based on conditional probability
    #  -pbs_value = network_value(leaf_PBS_list)
    #       ##for each PBS leaf, take weighted average? update as value for root PBS
    #  -sample_iter = rand(range(loop_length))
    #  -for iter in loop_length:
    #       -TODO: figure out how to represent sample playthrough for CFR to act on
    #       -sample, pbs_leaf = sample_playthrough(PBS, policy, policy) 
    #           ## generate distinct states resulting from a policy playthrough, and also resulting PBS at end of subgame
    #       -if iter == sample_iter:
    #           -next_PBS = pbs_leaf
    #       -new_policy = CFR(policy, sample)
    #       -#NOTE: maybe exclude this: iter_policy = iter/(iter+1) * old_policy_vals + 1/(iter+1) new_policy_vals
    #       -subgame-leaf_values = genreate_leaf_values(PBS, iter_policy or policy, new_policy)
    #       -new_est_val = iter/(iter+1)*pbs_value + 1/(iter+1)*network_value(new subgame leaves)
    #  -if training: add (PBS, new_est_value) to training data
    #  -PBS = next_PBS 
        curr_pbs = PBS
        curr_policy = Policy()
        iter_policy = Policy()
        next_PBS = PBS
        while curr_PBS.is_terminal == -1:
            subgame = CoupSubgame(curr_PBS)
            #TODO: generate values for leaves (PBSs or actual values? need function or nah?)
            pbs_value = network_pbs_estimation(subgame)
            sample_index = random.choice(range(DISTINCT_SAMPLES))
            for i in range(DISTINCT_SAMPLES):
                sample, pbs_leaf = subgame.sample_playthrough(curr_policy, iter_policy)
                if i == sample_index:
                    next_PBS = pbs_leaf 
                iter_policy = iter_policy.update(sample)
                subgame.update_leaves(curr_policy, iter_policy)
                new_pbs_value = i/(i+1)*pbs_value + 1/(i+1)*network_pbs_estimation(subgame)
            self.training_data[PBS] = new_pbs_value 
            curr_PBS = next_PBS
            curr_policy = iter_policy.copy()

        return curr_policy

    def network_pbs_estimation(self, subgame):
        #TODO
        pass


    ####################################################
    ########functions used to actually build the network
    def init_network(self):
        pass

    def train(self, training_episodes):     
        #trains using the self_play algorithm to generate training data
        #TODO           
        pass



