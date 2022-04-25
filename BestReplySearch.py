from Agent import Agent 
from GeneralCoup import *
import itertools

################################################
###Additional Info useful for BRS implementation
DEPTH = 6

class ExtendedStateQuality(enum.Enum):
    LOSE_CARD = 5

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

lose_card_move_objs = {LoseInfluenceMoveType.LOSE_DUKE:LoseDukeMove,
                        LoseInfluenceMoveType.LOSE_CAPTAIN:LoseCaptainMove,
                        LoseInfluenceMoveType.LOSE_ASSASSIN:LoseAssassinMove,
                        LoseInfluenceMoveType.LOSE_CONTESSA:LoseContessaMove,
                        LoseInfluenceMoveType.LOSE_AMBASSADOR:LoseAmbassadorMove}

extended_move_objs = move_objs | lose_card_move_objs

class BRSState:
    #wrapper around game state that formats for BRS
    #  allows stochastic points at a particular point in the game tree
    def __init__(self, num_game_states, game_states, private_states, weights=None, moves=None):
        self.num_game_states = num_game_states 
        self.weights = [1/num_game_states for _ in range(num_game_states)] if weights==None else weights
        self.public_states = game_states
        self.private_states = private_states
        #list of [[move, move, move], [move, move, move]] with each list corresponding to a state, in case 
        #  we have restricted moves per state due to custom evaluation in BRS
        #NOTE: for state without restrictions, empty list denotes normal valid moves behavior
        self.moves = [[] for _ in range(num_game_states)] if moves==None else moves
    
    #used to detail a stochastic branching where states don't differ in public state but rather possible movesets
    def set_stochastic_moves(self, restricted_moveset):
        self.moves = restricted_moveset

    def copy(self):
        return BRSState(self.num_game_states, self.public_states, self.private_states, self.weights, self.moves)

    def __add__(self, other):
        new_game_states = self.num_game_states + other.num_game_states
        new_public_states = self.public_states + other.public_states 
        new_private_states = self.private_states + other.private_states 
        #new_brs_states = None 
        #if self.brs_states != None and other.brs_states != None:
        #    new_brs_states = self.brs_states + other.brs_states 
        #elif self.brs_states != None:
        #    new_brs_states = self.brs_states 
        #elif other.brs_states != None: 
        #    new_brs_states = otehr.brs_states
        new_weights = None 
        if self.weights != None and other.weights != None:
            new_weights = [i / new_game_states for i in range(self.weights)] + [i / new_game_states for i in range(other.weights)]
        elif self.weights != None:
            new_weights = [i / new_game_states for i in range(self.weights)] + [1/other.num_game_states/new_game_states for _ in range(other.num_game_states)]
        elif other.weights != None:
            new_weights = [1/self.num_game_states/new_game_states for _ in range(self.num_game_states)] + [i / new_game_states for i in range(other.weights)]
        #arbitrary: new set of possible moves is union of both
        new_moves = None
        if self.moves != None and other.moves != None:
            new_moves = self.moves + other.moves 
        elif self.moves != None: 
            new_moves = self.moves 
        elif other.moves != None:
            new_moves = other.moves
        return BRSState(new_game_states, new_public_states, new_private_states, new_weights, new_moves)


################################################
###BRS Agent Implementation
class BestReplySearchAgent(Agent):
    def __init__(self, index):
        Agent.__init__(self)
        #for CLI printing purposes
        self.index = index
                

    def make_move(self, valid_moves, game_state):
        #potentially implement Best Reply Search? essentially paranoid but can implement longer planning
            #assume coalition collectively agrees to make best move, everyone else passes   
                #passing can be treated as income
                #relaxes pessimism of Paranoid Search, since coalitions aren't possible in 
                #  computer temrinal play but do sometimes happen in live play
            #faulty assumptions = hopefully somewhat poor performance as a baseline

        #for every move, generate new state, call BFS on each node, choose highest value
        curr_highest_value = -200
        curr_best_action = valid_moves[0]
        for move in valid_moves:
            new_public_state = game_state.copy()
            new_private_state = self.private_state.copy()
            temp_state = BRSState(1, [new_public_state], [new_private_state])
            if len(move) == 1:
                #choosing a card to lose or inaction; generate move objects if needed
                if move[0] == InfluenceType.duke:
                    movetype = LoseInfluenceMoveType.LOSE_DUKE 
                    move_obj = LoseDukeMove(self.index, self.index)
                elif move[0] == InfluenceType.assassin:
                    movetype = LoseInfluenceMoveType.LOSE_ASSASSIN
                    move_obj = LoseAssassinMove(self.index, self.index)
                elif move[0] == InfluenceType.captain:
                    movetype = LoseInfluenceMoveType.LOSE_CAPTAIN
                    move_obj = LoseCaptainMove(self.index, self.index)
                elif move[0] == InfluenceType.contessa:
                    movetype = LoseInfluenceMoveType.LOSE_CONTESSA
                    move_obj = LoseContessaMove(self.index, self.index)
                elif move[0] == InfluenceType.ambassador:
                    movetype = LoseInfluenceMoveType.LOSE_AMBASSADOR
                    move_obj = LoseAmbassadorMove(self.index, self.index)
                temp_state = self._eval_action(temp_state, movetype, move_obj)
                
            elif isinstance(move[0], InfluenceType):
                #if the movetype is actually a card type and there are two indexes in the move, exchange!
                #format of the list is [old card, new card]
                movetype = MoveType.exchange 
                move_obj = ExchangeMove(self.index, self.index)
                move_obj.set_exchange_info(move[1],move[0])
                temp_state = self._eval_action(temp_state, movetype, move_obj)

            else:
                #any other move, create move object
                movetype = move[0]
                target = move[1]
                move_obj = extended_move_objs[movetype](self.index, target)
                temp_state = self._eval_action(temp_state, movetype, move_obj)

            val = self._BRS(float('-inf'), float('inf'), DEPTH, temp_state)
            if val > curr_highest_value:
                curr_best_action = move 
                curr_highest_value = val 
        return curr_best_action


    def set_game_info(self, game):
        self.game = game

    #turn is a true/false value 
    def _BRS(self, alpha, beta, depth, node_state):
        #BRS algo:
        #####the main drawback here is reducing certain subtrees to stochastic nodes 
        #####  without any notion of a belief state, treating outcomes with limited weighting
        #####the algorithm also doesn't handle opponents exchanging very well
        #####  -without any knowledge of opponents' private states and only knowledge of 
        #####     "cards in play," exchanging as an opponent doesn't change anything actionable

        #if stochastic branch:
        #   for all sub-node states:
        #       cum_val += BRS(-beta, -alpha, depth-1, !agent_turn, BRSState(1, [sub_state]))
        #   value = cum_val/num_states 
        #   if value >= beta:
        #       return value
        #   alpha = max(alpha, value)
        #   return alpha
        #
        #else (single game state):
        #   if depth <= 0:
        #       return heuristic
        #
        #   if current player's turn:
        #       moves = get_moves_from_state/game
        #   else 
        #       moves = all_moves_from_all_opponents
        #
        #   for all moves:
        #       temp_state = do_move(move, game_state) -----note, resulting BRSNode may be stochastic
        #       value = -1 * BRS(-beta, -alpha, depth-1, agent_turn, temp_state)
        #       if value >= beta:
        #           return value
        #       alpha = max(alpha, value)
        #
        #   return alpha

        if node_state.num_game_states > 1:
            #stochastic-- multiple probabilities 
            cum_val = 0
            for i in range(len(node_state.public_states)):
                public_state = node_state.public_states[i]
                private_state = node_state.private_states[i]
                sub_moves = node_state.moves[i]
                cum_val += node_state.weights[i] * self._BRS(-1 * beta, -1 * alpha, depth, BRSState(1, [public_state], [private_state], moves=sub_moves))
            if cum_val >= beta:
                return cum_val
            alpha = max(alpha, cum_val)
            return alpha 
        
        else:
            #modify agent_turn swapping, since no guarantee one action leads to opponent turn
            agent_turn = (node_state.public_states[0].curr_player == self.index)
            if depth <= 0:
                return self._h(node_state.public_states[0])

            if agent_turn:
                #check if state_class is EXCHANGE
                if node_state.public_states[0].state_class != StateQuality.EXCHANGE:
                    print("DEBUG moves resulting from normal evaluation for agent")
                    #normal evaluation
                    move_types = self._extended_valid_moves(self.index, node_state.public_states[0], node_state.moves)
                    moves = []
                    for move_type in move_types:
                        move_options = self.game.add_targets(move_types, self.index, node_state.public_states[0].action_player, node_state.public_states[0])
                        for move_option in move_options:
                            moves.append([[move_type],[move_objs[move_type](self.index, move_option[1])]])
                else:
                    print("DEBUG moves stored exchange possibilities")
                    #moves should be stored in state
                    moves = node_state.moves
            else:
                print("DEBUG moves resulting from opponent moveset generation")
                moves = self._generate_all_opponent_movesets(node_state)
                
        print("DEBUG moves: " + str(moves))

        #in exchange case, 'moves' stores the set of possible exchanges; need to generate actual moveset
        if len(moves) != 0 and moves[0] == [-1]:
            new_moves = []
            for exchange in moves:
                if exchange != [-1]:
                    exch_obj = ExchangeMove(self.index,self.index)
                    exch_obj.set_exchange_info(exchange[1], exchange[0])
                    new_moves.append([[MoveType.exchange],[exch_obj]])
            moves = new_moves

        for moveset in moves:
            result = self._eval_move_set(node_state, moveset[0], moveset[1])
            value = -1 * self._BRS(-1*beta, -1*alpha, depth-1, result)
            if value >= beta:
                return value 
            alpha = max(alpha, value)

        return alpha

    #########################################################
    #Private helper functions for BRS

    
    #because this agent doesn't have a notion of other private states and maintenance of the deck,
    #  it can only determine possible states after drawing a card from the deck or an opponent losing
    #  a challenge from what it knows from flipped cards and the agent's own private state
    def _possible_card_flips(self, public_state, private_state):
        """returns an array of cards that are still in play"""
        starting_deck = [InfluenceType.duke, InfluenceType.duke, InfluenceType.duke,
                        InfluenceType.assassin, InfluenceType.assassin, InfluenceType.assassin,
                        InfluenceType.captain, InfluenceType.captain, InfluenceType.captain, 
                        InfluenceType.ambassador, InfluenceType.ambassador, InfluenceType.ambassador, 
                        InfluenceType.contessa, InfluenceType.contessa, InfluenceType.contessa]
        for card in private_state.cards:
            starting_deck.remove(card)
        for flipped_cards in public_state.cards:
            for card in flipped_cards:
                if card != -1:
                    starting_deck.remove(card)

        return starting_deck

    #meant to handle cases that weren't handled in main game loop implementation
        #1) handles extended state quality "LOSE_CARD" that is implemented differently
        #   in the main game loop due to required access to private state
        #     -note: requires private state in order to accomplish lose_card functionality

    def _extended_valid_moves(self, player, single_public_state, private_state, moves=None):
        if single_public_state.state_class == ExtendedStateQuality.LOSE_CARD:
            move_types = []
            if private_state != None:
                #if agent, return just the possibilities from private state
                for card in private_state.cards:
                    move_types.append(lose_influence_type[card])
                
            else: 
                #if opponent, return possibilities based on what might be in the deck
                possible_flips = set(self._possible_card_flips(single_public_state, private_state))
                for card in possible_flips:
                    move_types.append(lose_influence_type[card])

            return move_types
        
        elif single_public_state.state_class == StateQuality.EXCHANGE:
            #return stored valid moves from state
            return moves

        else:
            return self.game.valid_moves(player, single_public_state)

    def _add_opponent_targets(self, valid_actions, player, last_move_player):
        moves_with_targets = []
        for move in valid_actions:
            if move == MoveType.coup or move == MoveType.assassinate or move == MoveType.steal:
                moves_with_targets.append([move, self.index])
            elif isinstance(move, CounterMoveType) and last_move_player == self.index:
                moves_with_targets.append([move, last_move_player])
            elif isinstance(move, ChallengeMoveType) and last_move_player == self.index:
                moves_with_targets.append([move, last_move_player])
            else:
                moves_with_targets.append([move, player])
        return moves_with_targets

    #returns a list of [action_type, action_object] sub-lists
    def _generate_all_opponent_movesets(self, single_node_state):
        movesets = []
        game_state = single_node_state.public_states[0]
        pass_action = None 
        if game_state.state_class == StateQuality.ACTION:
            #action
            pass_action = MoveType.income
        elif game_state.state_class == StateQuality.COUNTER:
            #counter
            pass_action = CounterMoveType.inaction
        else:
            #challenge
            pass_action = ChallengeMoveType.inaction

        for i in range(game_state.players):
            if i != self.index:
                possible_move_types = self._extended_valid_moves(i, game_state, None)
                for move_type in possible_move_types:
                    complete_move_info = self._add_opponent_targets(possible_move_types, i, game_state.action_player)
                    for move_info in complete_move_info:
                        #generate a "moveset" in order from the player after the agent
                        #   with agent i making this move and all others passing
                        move_type_set = [pass_action for j in range(game_state.players - 1)]
                        #try:
                        move_type_set[i-self.index-1] = move_type 
                        #except Exception as e:
                        #    print("index error for i-self.index = " + str(i-self.index) + " with i=" + str(i))
                        #    raise e
                        move_object_set = [move_objs[j](i,i) for j in move_type_set]
                        move_object_set[i-self.index-1] = move_objs[move_type](i, move_info[1])
                        movesets.append([move_type_set, move_object_set])

        return movesets

    def _h(self, public_state):
        #simple heurisic for the state, can be adjusted; current numerical measures are arbitrary
        curr_terminal_status = public_state.is_terminal()
        if curr_terminal_status == self.index:
            return 100
        elif curr_terminal_status != -1:
            return -100

        #return some value based on the number of coins you have/ cards you have 
        #  include some negative value based on relative wealth of opponents
        curr_value = 0
        #eval own cards and ascribe some value to them
        own_cards_num = public_state.cards[self.index].count(-1)
        if own_cards_num == 0:
            return -100
        elif own_cards_num == 2:
            curr_value += 50
        #eval own coins and ascribe some value to them
        own_coins = public_state.coins[self.index]
        curr_value += own_coins*3 #arbitrary

        #bonuses for reaching coin benchmarks enabling further action
        if own_coins >= 3:
            curr_value += 5
        if own_coins >= 7:
            curr_value += 5

        #eval number of opponent cards and coins in play
        total_opp_cards = 0
        total_opp_coins = 0
        for i in range(public_state.players):
            if i != self.index:
                total_opp_cards += public_state.cards[i].count(-1)
                total_opp_coins += public_state.coins[i]
        average_cards_per_opp = total_opp_cards/(public_state.players - 1)
        curr_value += (own_cards_num - average_cards_per_opp) * 50 

        #eval collective wealth of opponents
        average_coins_per_opp = total_opp_coins/ (public_state.players - 1)
        curr_value += (own_coins - average_cards_per_opp) * 10
        return curr_value

    def _eval_move_set(self, node_state, action_type_list, action_obj_list):
        """Returns new BRSstate object with all actions applied in order"""
        #note: the node_state only contains a single public/private state pair
        
        ##### the possible "opponent" move sets:
        #####       - [action, income, income...] in order from the player after curr, looping around
        #####       - [challenge/inaction, inaction, inaction...] in order
        #####       - [counter]

        print("DEBUG: evaluating player " + str(action_obj_list[0].player) + " moveset of " + str(action_type_list))

        curr_node = node_state.copy()
        #print(action_type_list)
        for i in range(len(action_obj_list)):
            curr_node = self._eval_action(curr_node, action_type_list[i], action_obj_list[i])
            #this is enough; same agent acting in a row isn't a concern
                #if opponents lose a challenge, resulting node is just a stochastic state
                #if agent loses a challenge, agent has another choice, but there are no other actions in the moveset
                #NOTE: there will never be a series where multiple branches occur over the course of a single moveset
                #similarly, opponent exchanging does nothing to public state or private state


        return curr_node

    ###############################################################################
    #### notes for action evaluation: 
    ####    -only challenge outcomes are truly stochastic; game knowledge (which card 
    ####       is chosen to be flipped) that might otherwise be part of public state 
    ####       isn't considered
    ####        -some exchange actions will still map as desirable actions, especially
    ####          when there is risk of being challenged
    ####
    ####    -changes in influence (assasination) don't map to concrete card flips
    ####        -only flipped/unflipped in public state
    ####        -allows for immediate evaluation of all actions on state instead of
    ####          waiting until the end of all phases wrapped inside a turn
    ####
    ####    -challenges against the agent CAN be mapped as a single outcome rather
    ####      than a stochastic branching, but challenges against opponents can't
    ####    
    #### eval logic:
    ####    -if starting action, immediately change the game state
    ####        -exchanging as stochastic result; return stochastic node of all possible combos
    ####        -can front-load assassination result since we aren't privy to information anyways,
    ####           is a stochastic outcome that is essentially speculation
    ####    -if counter, immediately reverse the mapped changes
    ####    -if challenge against the agent, evaluate to a single state
    ####        -NOTE: results in someone choosing a card to lose
    ####    -if challenge against an opponent, return a list of game states
    def _eval_action(self, node_state, action_type, action_obj):
        """Modifies the state given, with the action applied and added to the movestack, to return a new BRS node"""
        #note: needs to apply the action on all game states within the node_state
        #note: acts on a copy of what is given
        #print("DEBUG: evaluating action type " + str(action_type))
        game_states = [state.copy() for state in node_state.public_states]
        private_states = [state.copy() for state in node_state.private_states]

        #separate states to work on and possible expansion in number of states
        res_public_states = []
        res_private_states = []
        res_moves = []

        weights = None
        res_substates = None 

        actor = action_obj.player
        target = action_obj.target

        for i in range(len(game_states)):
            public_state = game_states[i]
            private_state = private_states[i]
            possible_flips = self._possible_card_flips(public_state,private_state)
            #for each MoveType, add to movestack
            public_state.movestack.append([action_type, action_obj])
            if public_state.state_class == StateQuality.EXCHANGE:
                #action_obj should be ExchangeMove with exchange info set
                #NOTE: only private state changes
                if actor == self.index:
                    #DEBUG:
                    print("card to remove from private state: " + str(action_obj.to_deck))
                    print("private state: " + str(private_state))

                    private_state.cards.remove(action_obj.to_deck)
                    private_state.cards.append(action_obj.from_deck)
                    public_state.state_class = StateQuality.CHALLENGEACTION
                
            else:
                if isinstance(action_type, MoveType):
                    public_state.action_player = actor
                    if action_type == MoveType.income:
                        public_state.coins[actor] += 1
                    elif action_type == MoveType.foreign_aid:
                        public_state.coins[actor] += 2
                    elif action_type == MoveType.tax:
                        public_state.coins[actor] += 3
                    elif action_type == MoveType.steal:
                        if self.game.check_target_aliveness(public_state, target):
                            target_coins = public_state.coins[target]
                            stolen_coins = (target_coins if target_coins <= 2 else 2)
                            action_obj.set_steal_amount(stolen_coins)
                            public_state.coins[target] -= stolen_coins
                            public_state.coins[public_state.curr_player] += stolen_coins
                    elif action_type == MoveType.coup:
                        public_state.coins[actor] -= 7
                        res_states = self._stochastic_influence_loss(public_state, private_state, possible_flips, action_obj.target)
                        for public_state in res_states.public_states:
                            public_state.state_class = StateQuality.CHALLENGEACTION
                            public_state.curr_player = (public_state.curr_player+1)%public_state.players
                            public_state.action_player = actor
                        return res_states
                    elif action_type == MoveType.assassinate:
                        public_state.coins[actor] -= 3
                        res_states = self._stochastic_influence_loss(public_state, private_state, possible_flips, action_obj.target)
                        for public_state in res_states.public_states:
                            public_state.state_class = StateQuality.CHALLENGEACTION
                            public_state.curr_player = (public_state.curr_player+1)%public_state.players
                            public_state.action_player = actor
                        return res_state
                    

                    #separate these two evaluations because of the difference in state quality change
                    if action_type != MoveType.exchange:
                        public_state.state_class = StateQuality.CHALLENGEACTION
                        public_state.curr_player = (public_state.curr_player+1)%public_state.players
                        res_public_states.append(public_state)
                        res_private_states.append(private_state)
                    else: 
                        #action_type == MoveType.exchange
                        public_state.state_class = StateQuality.EXCHANGE

                        #generate possible exchange movesets
                        possible_draws = list(itertools.combinations(self._possible_card_flips(public_state, private_state),2))
                        num_possible_draws = len(possible_draws)
                        distinct_draws = set(possible_draws)
                        if weights == None:
                            weights = []
                        for distinct_draw in distinct_draws:
                            weights.append(possible_draws.count(distinct_draw)/num_possible_draws)
                            possible_exchanges = [[-1]]
                            #generate possible exchanges in the form [held card to switch, new card from deck]
                            for j in distinct_draw:
                                for k in private_state.cards:
                                    possible_exchanges.append([k, j])
                            res_moves.append(possible_exchanges)
                            res_public_states.append(public_state.copy())
                            res_private_states.append(private_state.copy())
                    
                    #normalize weights if needed (multiple exchange states)
                    if weights != None and sum(weights) > 1:
                        num_weights = len(weights)
                        weights = [weight / num_weights for weight in weights]
                    return BRSState(len(res_public_states), res_public_states, res_private_states, weights, res_moves)
                        
                    
                elif isinstance(action_type, ChallengeMoveType):
                    if action_type != ChallengeMoveType.inaction:
                        if action_obj.target == self.index:
                            return self._eval_challenge_against_agent(public_state, private_state)
                        else:
                            return self._agent_challenge_possibilities(public_state, private_state, action_obj.target)
                    #elif (actor + 1) % public_state.players == target:
                    else:
                        if public_state.state_class == StateQuality.CHALLENGEACTION:
                            public_state.state_class = StateQuality.COUNTER 
                        else:
                            public_state.state_class = StateQuality.ACTION
                    

                elif isinstance(action_type, CounterMoveType):
                    #iterate backwards thru movestack until we get to an instance of MoveType, then reverse that move
                    target_counter_type = MoveType.income
                    i = -1
                    while (not isinstance(public_state.movestack[i][0], MoveType)):
                        i-=1
                    target_counter_type = public_state.movestack[i][0]
                    if target_counter_type == MoveType.foreign_aid:
                        public_state.coins[action_obj.target] = max(0, public_state.coins[action_obj.target]-2)
                    elif target_counter_type == MoveType.steal:
                        public_state.coins[action_obj.target] += action_obj.steal_amount 
                        public_state.coins[action_obj.player] -= action_obj.steal_amount
                    elif target_counter_type == MoveType.assassin:
                        #reverse last flip
                        if public_state.cards[action_obj.target][1] != -1:
                            public_state.cards[action_obj.target][1] = -1
                        else:
                            public_state.cards[action_obj.target][0] = -1
                        
                elif isinstance(action_type, LoseInfluenceMoveType):
                    if action_type == LoseInfluenceMoveType.LOSE_DUKE:
                        private_state.cards.remove(InfluenceType.duke)
                        self._brs_update_states_lose_card(public_state, self.index, InfluenceType.duke)
                    elif action_type == LoseInfluenceMoveType.LOSE_CAPTAIN:
                        private_state.cards.remove(InfluenceType.captain)
                        self._brs_update_states_lose_card(public_state, self.index, InfluenceType.captain)
                    elif action_type == LoseInfluenceMoveType.LOSE_ASSASSIN:
                        private_state.cards.remove(InfluenceType.assassin)
                        self._brs_update_states_lose_card(public_state, self.index, InfluenceType.assassin)
                    elif action_type == LoseInfluenceMoveType.LOSE_CONTESSA:
                        private_state.cards.remove(InfluenceType.contessa)
                        self._brs_update_states_lose_card(public_state, self.index, InfluenceType.contessa)
                    elif action_type == LoseInfluenceMoveType.LOSE_AMBASSADOR:
                        private_state.cards.remove(InfluenceType.ambassador)
                        self._brs_update_states_lose_card(public_state, self.index, InfluenceType.ambassador)
                
        return BRSState(len(game_states), game_states, private_states, weights)


    def _stochastic_influence_loss(self, public_state, private_state, possible_flips, target):
        """Returns a BRS node with multiple game states and weights"""
        num_dukes = possible_flips.count(InfluenceType.duke)
        num_captains = possible_flips.count(InfluenceType.captain)
        num_assassins = possible_flips.count(InfluenceType.assassin)
        num_contessas = possible_flips.count(InfluenceType.contessa)
        num_ambassadors = possible_flips.count(InfluenceType.ambassador)
        public_states = []
        num_flippable = len(possible_flips)
        if num_dukes > 0:
            duke_state = public_state.copy()
            self._brs_update_states_lose_card(duke_state, target, InfluenceType.duke)
            public_states.append(duke_state)
            weights.append(num_dukes/num_flippable)
        
        if num_captains > 0:
            captain_state = public_state.copy()
            self._brs_update_states_lose_card(captain_state, target, InfluenceType.captain)
            public_states.append(captain_state)
            weights.append(num_captains/num_flippable)

        if num_assassins > 0:
            assassin_state = public_state.copy()
            self._brs_update_states_lose_card(assassin_state, target, InfluenceType.assassin)
            public_states.append(assassin_state)
            weights.append(num_assassins/num_flippable)

        if num_contessas > 0:
            contessa_state = public_state.copy()
            self._brs_update_states_lose_card(contessa_state, target, InfluenceType.contessa)
            public_states.append(contessa_state)
            weights.append(num_contessas/num_flippable)

        if num_ambassadors > 0:
            ambassador_state = public_state.copy()
            self._brs_update_states_lose_card(ambassador_state, target, InfluenceType.ambassador)
            public_states.append(ambassador_state)
            weights.append(num_ambassadors/num_flippable)
        
        private_states = [private_state.copy() for _ in range(len(public_states))]

        return BRSState(len(public_states), public_states, private_states, weights)
        

    def _brs_update_states_lose_card(self, state, loser, chosen_discard):
        #update public state with the flipped card
        if state.cards[loser][0] != -1:
            state.cards[loser][1] = chosen_discard 
        else:
            state.cards[loser][0] = chosen_discard


    ##########################################################
    #NOTE: return a new BRSNode state for challenge evaluation helpers

    def _eval_challenge_against_agent(self, public_state, private_state):
        """checks movestack to find the challenged card and evaluates outcome"""
        print("DEBUG: evaluating challenge on this movestack: " )
        print(public_state.movestack)
        last_action_type = public_state.movestack[-1][0]
        curr_ind = -1
        while last_action_type == ChallengeMoveType.inaction:
            curr_ind -= 1
            last_action_type = public_state.movestack[curr_ind][0]
        challenge_initiator = public_state.movestack[-1][1].player

        possible_flips = self._possible_card_flips(public_state, private_state)
        
        if isinstance(last_action_type, MoveType):
            last_restricted_card = restricted_moves[last_action_type]
        else:
            last_restricted_card = restricted_countermoves[last_action_type]
        
        hand_to_check = private_state.cards

        next_state_class = StateQuality.ACTION
        next_player = (public_state.curr_player+1)%public_state.players
        if public_state.state_class == StateQuality.CHALLENGEACTION:
            next_state_class = StateQuality.COUNTER

        if last_restricted_card == InfluenceType.ambassador:
            next_state_class = StateQuality.EXCHANGE
            next_player = self.index
            action_obj = public_state.movestack[-2][1]
            if len(action_obj.to_deck) != 0:
                #cards were exchanged by agent; undo exchange in a temp setting to
                #  evaluate whether ambassador card was present 
                temp_hand = private_state.cards.copy()
                for card in action_obj.from_deck:
                    temp_hand.remove(card)
                    possible_flips.append(card)
                for card in action_obj.to_deck:
                    temp_hand.add(card)
                    possible_flips.remove(card)
                hand_to_check = temp_hand

        #if agent wins challenge, make relevant opponent lose a card
        if last_restricted_card in hand_to_check:
            #2 stochastic elements: the card you get after reshuffling and the card that gets flipped
            hand_to_check.remove(last_restricted_card)

            public_states = []
            private_states = []
            weights = []

            for i in set(possible_flips):
                num_i = possible_flips.count(i)
                weight_i = num_i / len(possible_flips)
                new_private = private_state.copy()
                new_private.cards = hand_to_check.append(i)
                
                #create new weights/probabilities for opponent losing cards
                temp_flips = possible_flips.copy().remove(i)
                for j in set(temp_flips):
                    num_j = temp_flips.remove(j)
                    weight_j = num_j / len(temp_flips)
                    new_public = public_state.copy()
                    new_public.state_class = next_state_class
                    new_public.curr_player = next_player

                    self._brs_update_states_lose_card(public_state, challenge_initiator, j)
                    public_states.append(new_public)
                    private_states.append(new_private.copy())
                    weights.append(weight_i * weight_j)
                    

            return BRSState(len(public_states), public_states, private_states, weights)

        else:
            #agent just loses the card-- single outcome, generate a new state for agent 
            #   to choose card to lose
            new_public = public_state.copy()
            new_private = private_state.copy()
            new_public.state_class = ExtendedStateQuality.LOSE_CARD 
            return BRSState(1, new_public, new_private)


    def _agent_challenge_possibilities(public_state, private_state, target):
        """returns a stochastic BRS state for the result of challenging a target"""
        last_action_type = public_state.movestack[-2][0]

        hand_size = public_state.cards[target].count(-1)

        possible_flips = self._possible_card_flips(public_state, private_state)
        total_unknown = len(possible_flips)
        
        if isinstance(last_action_type, MoveType):
            last_restricted_card = restricted_moves[last_action_type]
        else:
            last_restricted_card = restricted_countermoves[last_action_type]

        #evaluate probability that the challenged card may be held by this particular agent
        # simple evaluation that may become more sophisticated: 
        #    for 2-card hands, probability that either card is the target - probability of both 
        #    for 1-card hands, just probability of 1
        
        public_states = []
        private_states = []
        weights = []

        #evaluate challenge lose states-- probability the card is held
            #when opponent shuffles, we don't actually change anything except state class to LOSE_CARD
        num_challenged_card = possible_flips.count(last_restricted_card)
        if hand_size == 1:
            probability_lost = num_challenged_card/total_unknown
        else: 
            #hand_size == 2
            probability_lost = (num_challenged_card/total_unknown) + (0 if num_challenged_card <= 1 else 1/total_unknown) - (0 if num_challenged_card <=1 else num_challenged_card/(total_unknown^2))
        lose_public_state = public_state.copy()
        public_state.state_class = ExtendedStateQuality.LOSE_CARD 
        lose_private_state = private_state.copy()
        public_states.append(lose_public_state)
        private_states.append(lose_private_state)
        weights.append(probability_lost)

        #evaluate the diff states if opponent loses challenge
        for card in set(possible_flips):
            if card != last_restricted_card:
                num_card = possible_flips.count(card)
                if hand_size == 1:
                    weights.append(num_card/total_unknown)
                else:
                    weights.append((num_card/total_unknown) + (0 if num_card <= 1 else 1/total_unknown)
                        - (0 if num_card <=1 else num_card/(total_unknown^2)))
                #flip the card in question
                new_public = public_state.copy() 
                new_public.state_class = StateQuality.COUNTER if new_public.state_class == StateQuality.CHALLENGEACTION else StateQuality.ACTION
                new_private = private_state.copy()
                self._brs_update_states_lose_card(new_public, target, card)
                public_states.append(new_public)
                private_states.append(new_private)
        
        return BRSState(len(public_states), public_states, private_states, weights)



        
        

