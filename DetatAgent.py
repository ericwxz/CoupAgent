from Agent import Agent
from GeneralCoup import *
import itertools 

import keras
from keras.models import Sequential 
from keras.layers import Dense, Dropout
from keras.optimizers import SGD

####subgame depth in terms of complete turns (set of ACTION-CHALLENGE-COUNTER-CHALLENGE phases)
SUBGAME_DEPTH = 2
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
    def __init__(self, player_index, num_players, public_state, private_state, prob_distribution = None):
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
        #will be directly edited for subgame traversal purposes
        self.prev = None 
        self.next = None

    def is_terminal(self):
        return self.public_state.is_terminal()

    def eval_action_abstract(self, action_type, action_obj):
        #return list of new private/public state pairs resulting from action
        #NOTE for all states where this player loses card, change state class to appropriate LOSE_CARD state
        #NOTE for all eval starting action points, either direct state change or setting to EXCHANGE is done
        #if statequality is action:
            #if action is coup:
            #   all possible card flips
            #
            #if action is income:
            #   change public state 
            #
            #if action is foreign aid, tax, steal, assassinate, exchange:
            #   change state quality, defer action completion
            #
            #set starting_action 

        #if statequality is challengeaction:
            #if action is inaction:
            #   change statequality to counter

            #if action is challenge:
            #    generate successful/unsuccessful result states (with all possible flips)
            #    for each result, if initiator and target are alive, change statequality to counter
            #       else if initiator is alive but target is dead from successful challenge:
            #           do not proceed to counter, restart to action
            #
            #       else if initiator is dead from unsuccessful challenge:
            #           do not proceed to counter, restart to action and iterate curr player


        #if statequality is counter:
            #if action is inaction: 
            #   complete action, statequality=action 
            #
            #if action is a counter:
            #   statequality = challengecounter

        #if statequality is challengecounter:
            #if action is inaction:
            #   statequality = action
            #if action is a challenge:
            #   generate successful/unsuccessful result states w statequality=action
            #   for each result:
            #       if initiator and target are alive:
            #           evaluate starting action if successful
            #       elif initiaor is alive but target is dead:
            #           #challenge succeeded
            #           eval starting action
            #       elif initiator is dead but target is alive:
            #           don't eval starting action

        #if statequality is any lose_card:
            #update state quality
            #remove card from private state into public state
        
        #if statequality is exchange:
            #exchange with deck
            #update state quality
        pass

    def eval_action_discrete(self, action_type, action_obj, private_states):
        #copy abstract implementation but replace challenge/assasinate/coup/exchange with discrete results
        pass

    def _eval_starting_action(self):
        pass

#Policy that updates according to CFR
class Policy:
    def __init__(self):
        self._regret = {}
        self._prob_sum = {}
    
    def get_strategy(self, pbs):
        #actions = valid_actions
        #if pbs not in self._regret:
        #   initialize _regret[pbs] and _prob_sum[pbs]
        #sum_regret = 0
        #for a in actions:
        #   sum_regret += max(0.0, self.regret[pbs][a])
        #strat = {}
        #for a in actions:
        #    if sum_regret > 0.0:
        #        strat[a] = max(0.0, self._regret[pbs][a]) / sum_regret
        #    else:
        #        strat[a] = 1.0 / num_actions
        pass

    def update(self, distinct_states_to_add):
        #TODO
        pass 

    def copy(self):
        new_policy = Policy()
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
        pass

class CoupSubgame:
    #leaves 
    def __init__(self, init_pbs, leaf_pbs_list = None):
        self.root = init_pbs
        if leaf_pbs_list != None:
            self.leaf_pbs_list = leaf_pbs_list 
        else:
            #take public state, calculate all possible public and private states up to 
            #next, generate initial probabilities without considering policy
            #TODO:

    def generate_leaf_values(self, policy1, policy2):
        #for each pbs in the leaf list, update the distribution based on policies
        #TODO: figure out how this is done
        pass

    #TODO: are we updating values or pbs leafs?
    def update_leaves(self, policy1, policy2):
        pass

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
            print("no model loaded or built")
            return 
        self._model.save(filename) 

    def load(self,filename):
        self._model = keras.models.load_model(filename)

    def self_play(self, PBS):
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


    def construct_subtree(self, pbs):
        #TODO: generate 
        pass

    def update(self, policy, sample):
        #TODO:
        #runs CFR given sample discrete states to compute payoff/regret
        pass 

    def network_pbs_estimation(self, subgame):
        #TODO
        pass

    def train(self, training_episodes):     
        #TODO           
        pass



