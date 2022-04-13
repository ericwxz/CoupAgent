from Agent import Agent 
from GeneralCoup import *

################################################
###Additional Info useful for BRS implementation
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

extended_move_objs = dict(move_objs, **lose_card_move_objs)


################################################
###BRS Agent Implementation
class BestReplySearchAgent(Agent):
    def __init__(self, index):
        Agent.__init__(self)
        #for CLI printing purposes
        self.index = index
    
    class BRSState:
        #wrapper around game state that formats for BRS
        #  allows stochastic points at a particular point in the game tree
        def __init__(self, num_game_states, game_states, private_states, weights=None):
            self.num_game_states = num_game_states 
            self.weights = [1/num_game_states for _ in range(num_game_states)] if weights==None else weights
            self.public_states = public_states
            self.private_states = private_states
        

    def make_move(self, valid_moves, game_state):
        #potentially implement Best Reply Search? essentially paranoid but can implement longer planning
            #assume coalition collectively agrees to make best move, everyone else passes   
                #passing can be treated as income
                #relaxes pessimism of Paranoid Search, since coalitions aren't possible in 
                #  computer temrinal play but do sometimes happen in live play
            #faulty assumptions = hopefully somewhat poor performance as a baseline
        pass

    def set_game_info(self, game):
        self.game = game

    #turn is a true/false value 
    def _BRS(self, alpha, beta, depth, agent_turn, node_state)
        #BRS algo:
        #####the main drawback here is reducing certain subtrees to stochastic nodes 
        #####  without any notion of a belief state, treating outcomes with limited weighting

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
        #       agent_turn = false
        #   else 
        #       moves = all_moves_from_all_opponents
        #       agent_turn = true
        #
        #   for all moves:
        #       temp_state = do_move(move, game_state) -----note, resulting BRSNode may be stochastic
        #       ------TODO: need custom do_move that presumes all other opponents income and 
        #       ------      is flexible to multi-game-state stochastic nodes 
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
                cum_val += node_state.weight[i] * self._BRS(-1 * beta, -1 * alpha, depth-1, not agent_turn, BRSState(1, [public_state], [private_state]))
            if cum_val >= beta:
                return cum_val
            alpha = max(alpha, cum_val)
            return alpha 
        
        else:
            #TODO: modify agent_turn swapping, since no guarantee one action leads to opponent turn
            if depth <= 0:
                return self._h(node_state.public_states[0])

            if agent_turn:
                move_types = self._extended_valid_moves(self.index, node_state.public_states[0])
                moves = []
                for move_type in move_types:
                    move_options = self.game.add_targets(move_types, self.index, node_state.public_states[0].action_player)
                    for move_option in move_options:
                    moves += [[move_type],[move_objs[move_type](self.index, move_option[1])]]
                agent_turn = False 
            else:
                #TODO: add only target as agent
                moves = self._generate_all_opponent_movesets(node_state.public_states[0])
                agent_turn = True

        for move in moves:



        pass 

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
                starting_deck.remove(card)

        return starting_deck

    #meant to handle cases that weren't handled in main game loop implementation
        #1) handles extended state quality "LOSE_CARD" that is implemented differently
        #   in the main game loop due to required access to private state
        #     -note: requires private state in order to accomplish lose_card functionality

    def _extended_valid_moves(self, single_public_state, private_state):
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

        else:
            self.game.valid_moves(self.index, single_public_state)

    #returns a list of [action_type, action_object, player] 
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

        for i in range(len(game_state.players)):
            if i != self.index:
                possible_move_types = self.game.valid_moves(i, game_state)
                for move_type in possible_move_types:
                    complete_move_info = self.game.add_targets(possible_move_types, i, game_state.action_player)
                    for move_info in complete_move_info:
                        #generate a "moveset" in order from the player after the agent
                        #   with agent i making this move and all others passing
                        move_type_set = [pass_action for j in range(len(game_state.players) - 1)]
                        move_type_set[i-self.index] = move_type 
                        move_object_set = [move_objs[j](i,i) for j in move_type_set]
                        move_object_set[i-self.index] = move_objs[move_type](i, move_info[1])
                        movesets.append([move_type_set, move_object_set])

        return movesets

    def _h(self, node_state):
        #simple heurisic for the state
        curr_terminal_status = state.is_terminal()
        if curr_terminal_status == self.index:
            return 100
        elif curr_terminal_status != -1:
            return -100

        #return some value based on the number of coins you have/ cards you have 
        #TODO:

    #TODO: ensure state.curr_player is updated
    def _eval_move_set(node_state, action_type_list, action_obj_list):
        """Returns new BRSstate object with all actions applied in order"""
        #note: the node_state only contains a single public/private state pair
        
        ##### the possible "opponent" move sets:
        #####       - [action, income, income...] in order from the player after curr, looping around
        #####       - [challenge/inaction, inaction, inaction...] in order
        #####       - [counter]

        for i in range(len(action_obj_list)):
            result_node = self._eval_action(node_state, action_type_list[i], action_obj_list[i])
            #this is enough; same agent acting in a row isn't a concer
                #if opponents lose a challenge, resulting node is just a stochastic state
                #if agent loses a challenge, agent has another choice, but there are no other actions in the moveset


        return new_state

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
    def _eval_action(node_state, action_type, action_obj, turn):
        """Modifies the state given, with the action applied and added to the movestack, to return a new BRS node"""
        #note: needs to apply the action on all game states within the node_state
        #note: acts on a copy of what is given

        #TODO: fix to apply to all public_states and such
        game_states = [state.copy() for state in node_state.public_states]
        private_states = [state.copy() for state in node_state.private_states]
        weights = []

        actor = action_obj.player
        target = action_obj.target

        possible_flips = self._possible_card_flips()

        for i in range(len(public_states)):
            public_state = game_states[i]
            private_state = private_states[i]
            #for each MoveType, add to movestack
            if isinstance(action_type, MoveType):
                if action_type == MoveType.income:
                    public_state.coins[actor] += 1
                    game_states.append(public_state)
                    private_states.append(private_state)
                elif action_type == MoveType.foreign_aid:
                    public_state.coins[actor] += 2
                    game_states.append(public_state)
                    private_states.append(private_state)
                elif action_type == MoveType.tax:
                    public_state.coins[actor] += 3
                    game_states.append(public_state)
                    private_states.append(private_state)
                elif action_type == MoveType.steal:
                    if self.game.check_target_aliveness(public_state, target):
                        target_coins = public_state.coins[target]
                        stolen_coins = (target_coins if target_coins <= 2 else 2)
                        action_obj.set_steal_amount(stolen_coins)
                        public_state.coins[target] -= stolen_coins
                        public_state.coins[state.curr_player] += stolen_coins

                        game_states.append(public_state)
                        private_states.append(private_state)
                elif action_type == MoveType.coup:
                    public_state.coins[actor] -= 7
                    #TODO: populate stochastic game_states

                elif action_type == MoveType.assassin:
                    public_state.coins[actor] -= 3
                    #TODO: populate stochastic game_states

                #separate these two evaluations because of the difference in state quality change
                if action_type != MoveType.exchange:
                    public_state.state_class = StateQuality.CHALLENGEACTION
                    public_state.curr_player = (public_state.curr_player+1)%public_state.num_players
                else: 
                    #action_type == MoveType.exchange
                    public_state.state_class = StateQuality.EXCHANGE
                    game_states.append(public_state)
                    private_states.append(private_state)
                    
                public_state.action_player = actor

                
            elif isinstance(action_type, ChallengeMoveType):
                if action_obj[1].target == self.index:
                    self._eval_challenge_against_agent(public_state, private_state)
                else:
                    self._agent_challenge_possibilities(public_state, private_state, action_obj[1].target)

            elif isinstance(action_type, CounterMoveType):
                
                #iterate backwards thru movestack until we get to an instance of MoveType, then reverse that move
                target_counter_type = MoveType.income
                #TODO: loop back
                if target_counter_type == MoveType.foreign_aid:
                    
                elif target_counter_type == MoveType.steal:
                    
                elif target_counter_type == MoveType.assassin:
                    
            elif isinstance(action_type, LoseInfluenceMoveType):
                #TODO:
                    

        return ret_state


    def _eval_challenge_against_agent(self, public_state, private_state):
        """checks movestack to find the challenged card and evaluates outcome"""
        last_action_type = public_state.movestack[-2][0]
        challenge_initiator = public_state.movestack[-1][1].player
        if isinstance(last_action_type, MoveType):
            last_restricted_card = restricted_moves[last_action_type]
        else:
            last_restricted_card = restricted_countermoves[last_action_type]
        
        if last_restricted_card == InfluenceType.ambassador:
            #TODO: add info on the cards exchanged to the move object to undo exchange first

        if last_restricted_card in private_state.cards:
            #5 possible outcomes-- stochastic node
            #   2 stochastic elements: the card you get after reshuffling and the card that gets flipped
            #TODO: implement all possible new private states as well as all possible public flips, return
            #   node with all those possible states

        if last_restricted_card == InfluenceType.ambassador:
            #TODO: re-exchange after shuffle

        else:
            #TODO: agent just loses the card-- single outcome, generate a new state for agent 
            #   to choose card to lose


    def _agent_challenge_possibilities(public_state, private_state, target):
        """returns a stochastic BRS state for the result of challenging a target"""
        
        pass 