from Agent import Agent
from GeneralCoup import *
import itertools 
import enum

#TODO: all instances of starting_action_type need to be generalized for games greater than 2 players (multiple challenge inactions on movestack)

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
single_card_hands = [card for card in InfluenceType]
single_card_hands.remove(InfluenceType.inaction)
single_card_hands = [tuple([card]) for card in single_card_hands]
possible_hands.extend(single_card_hands)
set_of_hands = [i for i in set(possible_hands)]
exchange_possibilities = list(set(possible_hands) - set([(InfluenceType.duke, InfluenceType.duke), (InfluenceType.assassin, InfluenceType.assassin), (InfluenceType.captain, InfluenceType.captain), (InfluenceType.ambassador, InfluenceType.ambassador), (InfluenceType.contessa, InfluenceType.contessa)]))

def pub_priv_heuristic(pub, priv):
    #don't need to consider terminal states

    #return some value based on the number of coins you have/ cards you have 
    #  include some negative value based on relative wealth of opponents
    curr_value = 0
    #eval own cards and ascribe some value to them
    own_cards_num = pub.cards[pub.curr_player].count(-1)
    if own_cards_num == 0:
        return -100
    elif own_cards_num == 2:
        curr_value += 50
    #eval own coins and ascribe some value to them
    own_coins = pub.coins[pub.curr_player]
    curr_value += own_coins*3 #arbitrary

    #bonuses for reaching coin benchmarks enabling further action
    if own_coins >= 3:
        curr_value += 5
    if own_coins >= 7:
        curr_value += 5

    #eval number of opponent cards and coins in play
    total_opp_cards = 0
    total_opp_coins = 0
    for i in range(pub.players):
        if i != pub.curr_player:
            total_opp_cards += pub.cards[i].count(-1)
            total_opp_coins += pub.coins[i]
    average_cards_per_opp = total_opp_cards/(pub.players - 1)
    curr_value += (own_cards_num - average_cards_per_opp) * 50 

    #eval collective wealth of opponents
    average_coins_per_opp = total_opp_coins/ (pub.players - 1)
    curr_value += (own_coins - average_cards_per_opp) * 10
    return curr_value


class BeliefState:
    def __init__(self, game, player_index, num_players, public_state, private_state, prob_distribution = None, special_state=None):
        self.index = player_index
        self.num_players = num_players
        #full public state obj; if passed as input to a model, it will be encoded
        self.public_state = public_state
        #extended state notion for custom evaluation
        if special_state != None:
            self.public_state.state_class = special_state
        #own private state
        self.private_state = private_state
        #probabilities player i has hand type j (index in set_of_hands) given by self.s_d[i][j]
        self.prob_distribution = {i:{j:0.0 for j in set_of_hands} for i in range(num_players)}
        if prob_distribution==None:
            #generate initial probabilities of opponents having each hand 
            starting_deck_copy = starting_deck.copy()
            for card in private_state.cards:
                starting_deck_copy.remove(card)
            in_play = len(starting_deck_copy)
            for i in range(num_players):
                if i == self.index:
                    curr_hand = tuple(self.private_state.cards)
                    self.prob_distribution[i][curr_hand] = 1.0
                else:
                    for j in set_of_hands:
                        if len(j) == 2:
                            first_card = j[0]
                            prob_first = starting_deck_copy.count(first_card) / in_play
                            starting_deck_copy.remove(first_card)
                            second_card = j[1] 
                            prob_second = starting_deck_copy.count(second_card) / (in_play - 1)
                            starting_deck_copy.append(first_card)
                            prob_hand = prob_first*prob_second 
                            self.prob_distribution[i][j] = prob_hand 
                        else: 
                            first_card = j[0]
                            prob_first = starting_deck_copy.count(first_card) / in_play
                            prob_hand = prob_first
                            self.prob_distribution[i][j] = prob_hand 
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
        for initiator in self.public_state.challenge_counts:
            for target in self.public_state.challenge_counts[initiator]:
                for card in self.public_state.challenge_counts[initiator][target]:
                    index = initiator*(self.num_players*5) + target*5 + (card.value-11)
                    encoded_challenges[index] = min(4, self.public_state.challenge_counts[initiator][target][card])
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

    def copy(self):
        return BeliefState(self.game, self.index, self.num_players, self.public_state.copy(), self.private_state.copy(), self.prob_distribution)

    def encode(self):
        #this can update
        prob_state = []
        for player in self.prob_distribution:
            prob_state.extend(self.prob_distribution[player])
        
        return tuple(self.player_state + self.opponent_state + prob_state)

    def encode_without_beliefs(self):
        return tuple(self.player_state + self.opponent_state)

    def is_terminal(self):
        return self.public_state.is_terminal()

    def _next_player(self, public_state, starting_ind = None):
        def alive(state, target):
            if state.cards[target][0] == -1 or state.cards[target][1] == -1:
                return True 
            return False
        
        if starting_ind == None:
            starting_ind = public_state.curr_player

        next_player_ind = (starting_ind + 1) % public_state.players
        while not alive(public_state, next_player_ind):
            next_player_ind = (next_player_ind + 1) % public_state.players
        
        return next_player_ind

    def eval_action_abstract(self, action_type, action_obj):
        #return list of new private/public state pairs resulting from action
        #NOTE for all states where this player loses card, change state class to appropriate LOSE_CARD state
        #NOTE for all eval starting action points, either direct state change or setting to EXCHANGE is done
        #NOTE for all iterating over players for next state, check for aliveness
        #TODO: also implement history editing/probability checking
        new_states = []
        new_public_base = self.public_state.copy()
        new_private_base = self.private_state.copy()

        #TODO: add actions to movestack for future eval
        if self.public_state.state_class == StateQuality.ACTION:
            if action_type == MoveType.coup:
                if action_obj.target != self.index:
                    #generate all possible result public states w/ statequality = action, curr_player incremented
                    res_states = self._opp_flip_states(new_public_base, new_private_base, action_obj.target, StateQuality.ACTION ,self._next_player(new_public_base))
                    for res in res_states:
                        pub = res[0]
                        priv = res[1]
                        pub.movestack.append([action_type, action_obj])
                    new_states.extend(res_states)
                else:
                    #if target is self, go to LOSE_CARD
                    new_public_base.state_class = ExtendedStateQuality.LOSE_CARD_ACTION
                    new_public_base.action_player = new_public_base.curr_player
                    new_public_base.movestack.append([action_type, action_obj])
                    new_states.append([new_public_base, new_private_base])
                    

            elif action_type == MoveType.income:
                #generate new state, iterate curr_player
                new_public_base.coins[new_public_base.curr_player] += 1
                new_public_base.state_class = StateQuality.ACTION
                new_public_base.action_player = new_public_base.curr_player 
                new_public_base.curr_player = self._next_player(new_public_base)
                new_public_base.movestack.append([action_type, action_obj])
                
                new_states.append([new_public_base, new_private_base])
            else: 
                new_public_base.state_class = StateQuality.CHALLENGEACTION
                new_public_base.action_player = new_public_base.curr_player
                new_public_base.curr_player = self._next_player(new_public_base)
                new_public_base.recent_history[self.public_state.curr_player].pop(0)
                new_public_base.recent_history[self.public_state.curr_player].append(action_type)
                new_public_base.movestack.append([action_type, action_obj])

                new_states.append([new_public_base, new_private_base])

        elif self.public_state.state_class == StateQuality.CHALLENGEACTION:
            if action_type == ChallengeMoveType.inaction:
                new_public_base.curr_player = self._next_player(new_public_base)
                if new_public_base.curr_player == new_public_base.action_player:
                    if new_public_base.movestack[-1][0] in counter_index:
                        new_public_base.curr_player = new_public_base.movestack[-1][1].target 
                        new_public_base.state_class = StateQuality.COUNTER
                    else:
                        new_public_base.curr_player = self._next_player(new_public_base)
                        new_public_base.state_class = StateQuality.ACTION
                ################Challenge history updating
                starting_action_type = new_public_base.movestack[-1][0]
                new_public_base.movestack.append([action_type, action_obj])
                new_public_base.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                ################
                new_states.append([new_public_base, new_private_base])

            else:
                target_self = True if action_obj.target == self.index else False 
                initiator_self = True if action_obj.player == self.index else False

                #generate target_win states, initiator loses card, action goes through
                if initiator_self:
                    new_public = new_public_base.copy()
                    new_public.state_class=ExtendedStateQuality.LOSE_CARD_CHALLENGE_ACTION
                    new_public.curr_player = action_obj.player 
                    #########
                    starting_action_type = new_public_base.movestack[-1][0]
                    new_public.movestack.append([action_type, action_obj])
                    new_public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    ##########
                    new_private = new_private_base.copy()
                    new_states.append([new_public, new_private])
                else:
                    res_states = self._opp_flip_states(new_public_base, new_private_base, action_obj.player, StateQuality.COUNTER, new_public_base.movestack[-1][1].target)
                    for res in res_states:
                        public = res[0]
                        private = res[1]
                        #check to see if COUNTER is suppsoed to be the next state, if not, go back to ACTION
                        if public.movestack[-1][0] not in counter_index or (-1 not in public.cards[action_obj.player] and action_obj.player == new_public_base.movestack[-1][1].target):
                            #change quality to action, next player 
                            public.state_class = StateQuality.ACTION 
                            public.curr_player = self._next_player(public, public.action_player)

                        #add to challenge history
                        starting_action_type = public.movestack[-1][0]
                        public.movestack.append([action_type, action_obj])
                        print(starting_action_type)
                        public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    new_states.extend(res_states)

                #generate initiator_win states
                if target_self:
                    new_public = new_public_base.copy()
                    new_public.state_class=ExtendedStateQuality.LOSE_CARD_CHALLENGE_ACTION
                    new_public.curr_player = action_obj.player 
                    #########
                    starting_action_type = new_public_base.movestack[-1][0]
                    new_public.movestack.append([action_type, action_obj])
                    new_public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    ##########
                    new_private = new_private_base.copy()
                    new_states.append([new_public, new_private])
                else:
                    res_states = self._opp_flip_states(new_public_base, new_private_base, action_obj.player, StateQuality.COUNTER, new_public_base.movestack[-1][1].target)
                    for res in res_states:
                        public = res[0]
                        private = res[1]
                        #check to see if COUNTER is the next state, if not, go back to ACTION
                        if public.movestack[-1][0] not in counter_index or (-1 not in public.cards[action_obj.target]):
                            #change quality to action, next player 
                            public.state_class = StateQuality.ACTION 
                            public.curr_player = self._next_player(public, public.action_player)
                        #add to challenge history
                        starting_action_type = new_public_base.movestack[-1][0]
                        public.movestack.append([action_type, action_obj])
                        public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    new_states.extend(res_states)


        elif self.public_state.state_class == StateQuality.COUNTER:
            if action_type == CounterMoveType.inaction:
                results = self._eval_starting_action(new_public_base, new_private_base) #TODO
                for res in results:
                    res[0].movestack.append([action_type, action_obj])
                new_states.append([res_pub, res_priv])
            else:
                new_public_base.state_class = StateQuality.CHALLENGECOUNTER
                ############
                new_public_base.recent_history[new_public_base.curr_player].pop(0)
                new_public_base.recent_history[new_public_base.curr_player].append(restricted_countermoves[action_type])
                new_public_base.curr_player = self._next_player(new_public_base)
                new_public_base.movestack.append([action_type, action_obj])
                ###########
                new_states.append([new_public_base, new_private_base])
                
        elif self.public_state.state_class == StateQuality.CHALLENGECOUNTER:
            if action_type == ChallengeMoveType.inaction:
                new_public_base.curr_player = self._next(new_public_base)
                if new_public_base.curr_player == self.public_state.movestack[-1][1].player: 
                    new_public_base.state_class = StateQuality.ACTION
                    new_public_base.curr_player = self._next(new_public_base, new_public_base.action_player)
            else:
                target_self = True if action_obj.target == self.index else False 
                initiator_self = True if action_obj.player == self.index else False

                #generate target_win states, initiator loses card, action doesn't go through
                if initiator_self:
                    new_public = new_public_base.copy()
                    new_public.state_class=ExtendedStateQuality.LOSE_CARD_CHALLENGE_COUNTER
                    new_public.curr_player = action_obj.player 
                    #########
                    starting_action_type = new_public_base.movestack[-1][0]
                    new_public.movestack.append([action_type, action_obj])
                    new_public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    ##########
                    new_private = new_private_base.copy()
                    new_states.append([new_public, new_private])
                else:
                    res_states = self._opp_flip_states(new_public_base, new_private_base, action_obj.player, StateQuality.ACTION, new_public_base.movestack[-1][1].target)
                    for res in res_states:
                        public = res[0]
                        private = res[1]
                        public.state_class = StateQuality.ACTION 
                        public.curr_player = self._next_player(public, public.action_player)

                        #add to challenge history
                        starting_action_type = new_public_base.movestack[-1][0]
                        public.movestack.append([action_type, action_obj])
                        public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    new_states.extend(res_states)

                #generate initiator_win states; action goes through
                if target_self:
                    new_public = new_public_base.copy()
                    new_public.state_class=ExtendedStateQuality.LOSE_CARD_CHALLENGE_COUNTER
                    new_public.curr_player = action_obj.player 
                    #########
                    starting_action_type = new_public_base.movestack[-1][0]
                    new_public.movestack.append([action_type, action_obj])
                    new_public.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                    ##########
                    new_private = new_private_base.copy()
                    new_states.append([new_public, new_private])
                else:
                    res_states = self._opp_flip_states(new_public_base, new_private_base, action_obj.player, StateQuality.COUNTER, new_public_base.movestack[-1][1].target)
                    for res in res_states:
                        public = res[0]
                        private = res[1]
                        results = self._eval_starting_action(public, private) #TODO
                        for res in results:
                            new_pub = res[0]
                            new_priv = res[1]
                            new_pub.movestack.append([action_type, action_obj])
                            new_pub.state_class = StateQuality.ACTION 
                            new_pub.curr_player = self._next_player(public, public.action_player)
                            #add to challenge history
                            starting_action_type = new_public_base.movestack[-1][0]
                            new_pub.movestack.append([action_type, action_obj])
                            new_pub.challenge_counts[action_obj.player][action_obj.target][restricted_moves[starting_action_type]] += 1
                        new_states.extend(results)



        #if statequality is any lose_card:
            #update state quality based on which move_card
            #remove card from private state into public state
        elif isinstance(self.public_state.state_class, ExtendedStateQuality):
            card_to_lose = lose_influence_action_to_type[action_type]
            if self.public_state.state_class == ExtendedStateQuality.LOSE_CARD_ACTION:
                #could only be from coup; lose selected card
                new_private_base.cards.remove(card_to_lose)
                if new_public_base.cards[action_obj.player][0] == -1:
                    new_public_base.cards[action_obj.player][0] = card_to_lose 
                else:
                    new_public_base.cards[action_obj.player][1] = card_to_lose 
                new_states.append([new_public_base, new_private_base])

            elif self.public_state.state_class == ExtendedStateQuality.LOSE_CARD_CHALLENGE_ACTION:
                new_private_base.cards.remove(card_to_lose)
                if new_public_base.cards[action_obj.player][0] == -1:
                    new_public_base.cards[action_obj.player][0] = card_to_lose 
                else:
                    new_public_base.cards[action_obj.player][1] = card_to_lose 
                starting_target = new_public_base.movestack[-2][1].target 
                new_public_base.curr_player = starting_target 
                new_public_base.state_class = StateQuality.COUNTER 
                new_states.append([new_public_base, new_private_base])

            elif self.public_state.state_class == ExtendedStateQuality.LOSE_CARD_CHALLENGE_COUNTER:
                new_private_base.cards.remove(card_to_lose)
                if new_public_base.cards[action_obj.player][0] == -1:
                    new_public_base.cards[action_obj.player][0] = card_to_lose 
                else:
                    new_public_base.cards[action_obj.player][1] = card_to_lose 

                counter_initiator = new_public_base.movestack[-2][1].player 
                if self.index == counter_initiator:
                    results = self._eval_starting_action(new_public_base, new_private_base) #TODO
                    new_states.extend(results)
                else:
                    new_public_base.curr_player = self._next_player(new_public_base, new_public_base.action_player)
                    new_public_base.state_class = StateQuality.ACTION
                    new_states.append([new_public_base, new_private_base])
                    
            else:
                #just LOSE_CARD:
                    #from completion of delayed starting action
                #iterate player from action_player
                new_private_base.cards.remove(card_to_lose)
                if new_public_base.cards[action_obj.player][0] == -1:
                    new_public_base.cards[action_obj.player][0] = card_to_lose 
                else:
                    new_public_base.cards[action_obj.player][1] = card_to_lose 
                new_public_base.curr_player = self._next_player(new_public_base, new_public_base.action_player)
                new_public_base.state_class = StateQuality.ACTION
                new_states.append([new_public_base, new_private_base])

        #if statequality is exchange:
            #exchange with deck
            #update state quality to action
        elif self.public_state.state_class == StateQuality.EXCHANGE:
            new_private_base.remove(action_obj.to_deck)
            new_private_base.append(action_obj.from_deck)
            self.non_agent_deck.remove(action_obj.from_deck)
            self.non_agent_deck.append(action_obj.to_deck)
            new_public_base.state_class = StateQuality.ACTION
            new_states.append([new_public_base, new_private_base])

        return new_states

    #only used in self-play and training
    def eval_action_discrete(self, index, action_type, action_obj, private_states):
        #copy abstract implementation but replace challenge/assasinate/coup/exchange with discrete results
        pass

    #returns the next state (public, private pair) and iterates curr_player and state_quality. 
    def _eval_starting_action(self, public, private):
        #find starting action by iterating backwards on movestack
        curr_ind = -1 
        while not isinstance(public.movestack[curr_ind][0], MoveType):
            curr_ind -= 1
        starting_action_type = public.movestack[curr_ind][0]
        starting_obj = public.movestack[curr_ind][1]
        new_public_base = public.copy()
        new_private_base = private.copy()
        eval_states = []

        if starting_action_type == MoveType.assassinate:
            if starting_obj.target == self.index:
                new_public_base.coins[starting_obj.player] -= 7
                new_public_base.state_class = ExtendedStateQuality.LOSE_CARD 
                new_public_base.curr_player = self.index 
                return [[new_public_base,new_private_base]]
            else:
                #generate all flip outcomes
                new_public_base.coins[starting_obj.player] -= 7
                results = self._opp_flip_states(new_public_base, new_private_base, starting_obj.target, StateQuality.ACTION, starting_obj.player)
                for res in results:
                    pub = res[0]
                    pub.curr_player = self._next_player(pub)
                return results

        new_public_base.curr_player = self._next_player(new_public_base, starting_obj.player)
        new_public_base.state_class = StateQuality.ACTION
        if starting_action_type == MoveType.foreign_aid:
            new_public_base.coins[starting_obj.player] += 2
        elif starting_action_type == MoveType.tax:
            new_public_base.coins[starting_obj.player] += 3
        elif starting_action_type == MoveType.steal:
            coins_stolen = min(new_public_base.coins[starting_obj.target], 2)
            new_public_base.coins[starting_obj.player] += coins_stolen 
            new_public_base.coins[starting_obj.target] -= coins_stolen
        elif starting_action_type == MoveType.exchange:
            if starting_obj.player == self.index:
                new_public_base = StateQuality.EXCHANGE 
                new_public_base.curr_player = self.index

        return [[new_public_base,new_private_base]]
        

    def _opp_flip_states(self, new_public_base, new_private_base, index, next_quality, next_player):
        new_states = []
        card_types = [card for card in InfluenceType]
        card_types.remove(InfluenceType.inaction)
        for card in card_types:
            if card in self.non_agent_deck:
                possible_state = new_public_base.copy()
                constant_private = new_private_base.copy()
                #possible outcome; add new public state with that card flipped for the target
                if possible_state.cards[index][0] == -1:
                    possible_state.cards[index][0] = card 
                elif possible_state.cards[index][1] == -1:
                    possible_state.cards[index][1] = card 
                possible_state.curr_player = next_player 
                possible_state.state_class = next_quality
                new_states.append([possible_state, constant_private])
        return new_states

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

    def _pbs_adjustment(self, unadj_pbs, new_index = None, private_cards = None):
        if self.original_index == None or new_index == None or new_index == self.original_index:
            return unadj_pbs 
        else:
            pbs = unadj_pbs.copy() #TODO: implement copy
            pbs.private_state.cards = list(private_cards)
            #to index into existing data fields by new index, swap old and original index info
            #  to maintain equality of game
            old_coins = pbs.public_state.coins[original_index] 
            old_cards = pbs.public_state.cards[original_index] 
            pbs.public_state.coins[original_index] = pbs.public_state.coins[new_index]
            pbs.public_state.cards[original_index] = pbs.public_state.cards[new_index]
            pbs.public_state.coins[new_index] = old_coins 
            pbs.public_state.cards[new_index] = old_cards

            old_history = pbs.public_state.recent_history[original_index]
            pbs.public_state.recent_history[original_index] = pbs.public_state.recent_history[new_index]
            pbs.public_state.recent_history[new_index] = old_history

            new_challenge_dict = pbs.public_state.challenge_counts.copy()
            for initiator in new_challenge_dict:
                new_challenge_dict[initiator][original_index] = pbs.public_state.challenge_counts[initiator][new_index]
                new_challenge_dict[initiator][new_index] = pbs.public_state.challenge_counts[initiator][original_index]

            new_challenge_dict[original_index] = pbs.public_state.challenge_counts[new_index]
            new_challenge_dict[new_index] = pbs.public_state.challenge_counts[original_index]
            pbs.public_state.challenge_counts = new_challenge_dict

    
    def get_strategy(self, unadj_pbs, new_index=None, new_hand=None):
        pbs = self._pbs_adjustment(unadj_pbs, new_index, new_hand)
        actions = self.game.add_targets(self.game.valid_moves(self.index, pbs.public_state), self.index, pbs.public_state.action_player, pbs.public_state)
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

    def get_average_opp_strategy(self, pub):
        #ignoring beliefs and which private hand, what is the average strategy?
        #TODO
        pass
        

    def _cfr(self, pbs, weights, h=None):
        if h==None:
            h=pub_priv_heuristic
        #first check if last state in history is a terminal state for the player
        pub = pbs.public_state 
        priv = pbs.private_state
        terminal_status = pub.is_terminal()
        if terminal_status == pub.curr_player:
            return 100
        elif terminal_status != -1:
            return -100 

        #check if we've reached the depth of the playthrough for CFR; if so, use heuristic
        if len(pbs.next) == 0:
            return h(pub,priv)
        else:
            all_actions = self.game.add_targets(self.game.valid_moves(pub.curr_player, pub), pub.curr_player, pub.action_player, pub)
            v = 0.0
            values = {tuple(a): 0.0 for a in all_actions}
            if pub.curr_player == self.index:
                strat = self.get_strategy(pbs)
            else:                
                strat = self.get_average_opp_strategy(pub)
            for a in all_actions:
                for res_act_state in pbs.next[a]:
                    new_weights = weights.copy() 
                    new_weights[pub.curr_player] = strat[a] * weights[pub.curr_player]
                    values[a] = -1.0 * self._cfr(res_act_state, new_weights, h)
                    v += strat[a] * values[a]
                    self._regret[pbs.encode()][a] += new_weights[(pub.curr_player+1)%pub.players] * (values[a] - v)
                    self._prob_sum[pbs.encode()][a] += new_weights[pub.curr_player] * strat[a]
            return v/len(pbs.next[a])

            

    #state_samples should be a subgame of PBSs, h=function for estimating leaf values
    def update(self, subgame, h=None):
        weights = [1.0] * subgame.root.public_state.players
        self._cfr(subgame.root, weights, h)
        

    def copy(self, new_index):
        new_policy = Policy(self.game, new_index, self.index)
        new_policy._regret = self._regret.copy()
        new_policy._prob_sum = self._prob_sum.copy()
        return new_policy


class CoupSubgame:
    def __init__(self, game, index, init_pbs, leaf_state_pbs = None, leaf_pbs_weight_base = None, leaf_pbs_weight = None):
        self.game = game
        self.index = index
        self.root = init_pbs
        #map of encoded public+private info to pbs
        if leaf_state_pbs != None:
            self.leaf_state_pbs = leaf_state_pbs
        else:
            self.leaf_state_pbs = {}
        #base leaf heuristic values
        if leaf_pbs_weight_base !=None: 
            self.leaf_pbs_weight_base = leaf_pbs_weight_base
        else:
            self.leaf_pbs_weight_base = {}

        #leaf values adjusted by probabilistic weights
        if leaf_pbs_weight != None:
            self.leaf_pbs_weight = leaf_pbs_weight
        else:
            #take public state, calculate all possible public and private states up to 
            #next, generate initial probabilities without considering policy
            self.init_subgame(self.root, SUBGAME_DEPTH, pub_priv_heuristic)
            self.leaf_pbs_weight = self.leaf_pbs_weight_base.copy()

    def init_subgame(self, pbs, depth, h):
        #initialization doesn't set leaf pbs distributions; those are dependent on policies
        #recursive call to generate all pbs nodes in subgame and set leaf values as heuristic
        #
        #if depth = 0, return self
        if depth == 0:
            #NOTE: possible efficiency improvement can be done
            if pbs.encode() not in self.leaf_pbs_weight_base:
                self.leaf_pbs_weight_base[pbs.encode()] = 0
            self.leaf_pbs_weight_base[pbs.encode()] += h(pbs.public_state, pbs.private_state)
            self.leaf_state_pbs[pbs.encode_without_beliefs()] = pbs
            return pbs

        #generate all possible resulting public/private pairs from this pbs
        #for each distinct state, add init_subgame(pbs, depth-1) to list of pbs.next
        new_depth = depth 

        #iterate over all possible actions
        all_actions = self.game.add_targets(self.game.valid_moves(pbs.public_state.curr_player, pbs.public_state), pbs.public_state.curr_player, pbs.public_state.action_player, pbs.public_state)
        all_actions_elaborated = [[a[0], move_objs[a[0]](pbs.public_state.curr_player, a[1])] for a in all_actions ]
        result_states = []
        for a in all_actions_elaborated:
            result_states.append(pbs.eval_action_abstract(a[0], a[1]))
        
        for i in range(len(all_actions)):
            branch_states = result_states[i]
            pbs.next[tuple(all_actions[i])] = []
            for sub in branch_states:
                public = sub[0]
                private = sub[1]
                terminal_status = public.is_terminal()
                if terminal_status != -1:
                    #generate pbs, encode, check/add to list
                    terminal_pbs = BeliefState(self.game, pbs.index, pbs.num_players, public, private)
                    terminal_pbs_encoded = terminal_pbs.encode()
                    #if terminal_pbs_encoded not in self.leaf_pbs_weight_base:
                    #    self.leaf_pbs_weight_base[terminal_pbs_encoded] = 0
                    #self.leaf_pbs_weight_base[terminal_pbs_encoded] = 100 if terminal_status == self.index else -100
                    self.leaf_state_pbs[terminal_pbs.encode_without_beliefs()] = terminal_pbs
                    pbs.next[tuple(all_actions[i])].append(terminal_pbs)
                else:
                    new_pbs = BeliefState(self.game, pbs.index, pbs.num_players, public, private)
                    #only increment depth for the completion of a whole "turn"
                    if new_pbs.public_state.state_class == StateQuality.ACTION and new_pbs.public_state.curr_player == self.index:
                        new_depth = depth-1
                    self.init_subgame(new_pbs, new_depth, h)
                    pbs.next[tuple(all_actions[i])].append(new_pbs)

    #PROBABLY NOT EVER USED; assume it does not work probably
    #policy 1 is "self-policy", policy2 is the policy for all opponents
    #note: policy2 should have indexing updated before passing to update_leaves
    def update_weights(self, policies):
        self._update_by_weight(self.root, 1.0, policies, opp_policies)
        
    #opp_policies should be a dict of index->policy object
    def _update_by_weight(self, pbs, weight, policies):
        pbs_encoded = pbs.encode()
        if pbs_encoded in self.leaf_pbs_weight:
            self.leaf_pbs_weight[pbs_encoded] = self.leaf_pbs_weight_base[pbs_encoded] * weight 
        strat = policies[pbs.public_state.curr_player].get_strategy(pbs, pbs.public_state.curr_player)

        for action in strat:
            new_weight = weight * strat[action]
            new_pbs = pbs.next[action]
            self._update_by_weight(new_pbs, new_weight, policy1, policies)

    def update_all_pbs(self, policies):
        self._update_subgame_pbs_distributions(self.root, policies)

    def _update_subgame_pbs_distributions(self, pbs, policies):
        #don't update subsequent PBSs if leaf
        if len(pbs.next) != 0:
            all_actions = self.game.add_targets(self.game.valid_moves(pbs.public_state.curr_player, pbs.public_state), pbs.public_state.curr_player, pbs.public_state.action_player, pbs.public_state)
            
            beliefs_about_target = pbs.prob_distribution[pbs.public_state.curr_player]
            
            #check for impossible hands; set probability in pbs to 0 for those hands for this player
            possible_cards = set(pbs.non_agent_deck)
            card_counts_in_play = {i:pbs.non_agent_deck.count(i) for i in possible_cards}
            for hand in set_of_hands:
                for card in hand:
                    if hand.count(card) > card_counts_in_play[i]:
                        pbs.prob_distribution[pbs.public_state.curr_player][hand] = 0.0 
            strats_by_hand = {}
            action_overall_probability = {}
            #initialize possible strategies by hand
            for hand in set_of_hands:
                strat = policies[pbs.public_state.curr_player].get_strategy(pbs, pbs.public_state.curr_player, hand)
                strats_by_hand[hand] = strat
            #initialize overall probabilities per action
            for action in all_actions:
                overall_probability = 0.0
                for hand in set_of_hands:
                    overall_probability += strats_by_hand[hand][action] * pbs.prob_distribution[pbs.public_state.curr_player][hand]
                action_overall_probability[hand]

            #check the strat for the probability of playing action for each hand
            for hand in set_of_hands:
                if pbs.prob_distribution[pbs.public_state.curr_player][hand] != 0.0:
                    strat = strats_by_hand[hand]
                    for action in all_actions:
                        for res_act_state in pbs.next[action]:
                            prob_action_given_hand = strat[action]
                            prob_hand = pbs.prob_distribution[pbs.public_state.curr_player][hand]
                            prob_action = action_overall_probability[action]

                            prob_hand_given_action = prob_action_given_hand * prob_hand / prob_action
                            res_act_state.prob_distribution[pbs.public_state.curr_player][hand] = prob_hand_given_action
    

        if len(pbs.next) != 0:
            for action in pbs.next:
                for res_act_state in pbs.next[action]:
                    self._update_subgame_pbs_distributions(res_act_state, policies)
        
    #only need for full self-play/network/Rebel agent
    def sample_playthrough(self, policy1, policy2):
        #return a list of distinct (public, private) pairs from playthrough as well as last PBS leaf
        #   the cards from the opponent(s) are randomized based on available cards
        pass
            

#########################################################################################################
#########################################################################################################
#Unimplemented framework for self-play/ReBel agent


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



#takes a policy for sampling purposes in self-play
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
