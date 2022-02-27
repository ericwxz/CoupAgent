import random 
import enum

INFLUENCE_TO_SELECTION_OFFSET = 11

class StateQuality(enum.Enum):
    ACTION = 0
    CHALLENGEACTION = 1
    COUNTER = 2
    CHALLENGECOUNTER = 3
    #include additional quality after calling exchange as a unique stochastic moment
    EXCHANGE = 4

class InfluenceType(enum.Enum):
    #include inaction index for use in the exchange function, when a card must be chosen
    inaction = -1
    duke = 11
    assassin = 12
    captain = 13
    ambassador = 14
    contessa = 15

class MoveType(enum.Enum):
    income = 0
    foreign_aid = 1
    coup = 2
    tax = 3
    assassinate = 4
    steal = 5
    exchange = 6

class CounterMoveType(enum.Enum):
    inaction = -1
    foreign_aid = 7
    assassinate = 8
    steal = 9

class ChallengeMoveType(enum.Enum):
    inaction = -1 
    challenge = 10 

move_objs = {MoveType.income:IncomeMove, MoveType.foreign_aid:ForeignAidMove, MoveType.coup:CoupMove,
            MoveType.tax:TaxMove, MoveType.assassinate:AssassinateMove, MoveType.steal:StealMove, 
            MoveType.exchange:ExchangeMove, CounterMoveType.inaction:BaseMove, CounterMoveType.foreign_aid:CounterForeignAidMove,
            CounterMoveType.assassinate:CounterAssassinMove, CounterMoveType.steal:CounterStealMove, 
            ChallengeMoveType.inaction:BaseMove, ChallengeMoveType.challenge:ChallengeMove}

counter_index = {MoveType.foreign_aid:CounterMoveType.foreign_aid, 
                 MoveType.assassinate:CounterMoveType.assassinate,
                 MoveType.steal:CounterMoveType.steal}

unchallengeable_moves = [MoveType.income, MoveType.foreign_aid, MoveType.coup]

restricted_moves = {
    InfluenceType.duke:MoveType.tax,
    InfluenceType.assassin:MoveType.assassinate,
    InfluenceType.captain:MoveType.steal,
    InfluenceType.ambassador:MoveType.exchange
}
restricted_countermoves = {
    InfluenceType.duke:CounterMoveType.foreign_aid,
    InfluenceType.contessa:CounterMoveType.assassinate,
    InfluenceType.captain:CounterMoveType.steal,
    InfluenceType.ambassador:CounterMoveType.steal
}


class PrivateState:
    #contains private cards and known sightings from the public deck
    def __init__(self, cards, sightings):
        """PrivateState(cards, sightings)
            cards = list of private influence cards still in play"""
        self.cards = cards
        self.sightings = sightings
    
    def lost_influence(self):
        #TODO: maybe not? depends on state change mechanism

class PublicState:
    #contains info about history, each player's coin count, and dead influence

    def __init__(self, players, cards, coins, turn_counter, state_class, curr_player, action_player, movestack):
        """PublicState(cards, coins, turn_counter, state_class, curr_player, movestack)
            players = number of players
            cards = list where the ith entry is the dead influence cards of player i
            coins = list where the ith entry is the number of coins belonging to player i
            turn_counter = number of turns that have passed
            state_class = a StateQuality value
            curr_player = int to denote the player who initiated this state
            action_player = int to denote the player who chose the starting action (whose turn it is)
            movestack = list of history entries: [player, move] for all actions, counter-actions, challenges"""
        self.players = players
        self.cards = cards
        self.coins = coins 
        self.turn_counter = turn_counter
        self.state_class = state_class
        self.curr_player = curr_player
        self.action_player = action_player
        self.movestack = movestack

    def is_terminal(self):
        """returns -1 if not terminal, 0 if p1 wins, 1 if p2 wins"""
        alive_count = 0
        for player in cards:
            if len(player) < 2:
                alive_count+=1
        if alive_count > 1: 
            return False
        return True

    def encode_action(self,  action):
        #TODO: leave for player implementations
        """One-hot encoding of an action"""
        return (0 if i != action-1 else 1 for i in range(12))

    def encode(self):
        """returns all relevant information in the public state, encoded in a list of length 24"""
        """encoded = list(self.bins[0]) #4 
        encoded.extend(list(self.bins[1])) #4
        if len(self.movestack) == 0:
            last_move = (0,self.curr_player)
        elif len(self.movestack) < 3:
            last_move = self.movestack[0] 
        else:
            last_move = self.movestack[len(self.movestack)-1]
        encoded.extend([self.p1cards,self.p1coins,self.p2cards,self.p2coins,self.state_class]) #5
        encoded.extend(list(self.encode_action(last_move[0]))) #13
        encoded.append(last_move[1]) #1
        return encoded"""

class MultiPlayerCoup():
    #game object runs game loop and:
        #updates game state for every action made
        #fetches valid moves for every player
        #checks whether moves can be made and whether game phases need to be skipped
        #passes moves to player agents; waits on them for their choices
        #gives additional choices to agents if needed (ambassador exchange as a two-part decision)
    #game object also stores the deck that is neither private nor completely public

    #initialized by main program to 
    def __init__(self, agent_list):
        """initialize private states and restricted deck"""
        num_players = len(agent_list)
        if num_players > 6 or num_players < 2:
            raise ValueError("Invalid number of players")
        self.players = num_players
        self.agent_list = agent_list
        self.deck = [InfluenceType.duke, InfluenceType.duke, InfluenceType.duke,
                    InfluenceType.assassin, InfluenceType.assassin, InfluenceType.assassin,
                    InfluenceType.captain, InfluenceType.captain, InfluenceType.captain, 
                    InfluenceType.ambassador, InfluenceType.ambassador, InfluenceType.ambassador, 
                    InfluenceType.contessa, InfluenceType.contessa, InfluenceType.contessa]
        self.curr_state = self.init_state(num_players)

        random.shuffle(self.deck)
        private_states = []
        for i in range(num_players):
            private_states.append(PrivateState([self.deck.pop(), self.deck.pop()]))
        
        return private_states
        

    def init_state(self, num_players):
        cards = []
        for i in range(num_players):
            #unflipped cards-- no observations
            cards.append([-1,-1])
        coins = [2 for i in range(num_players)]
        turn_counter = 0
        state_class = StateQuality.ACTION
        curr_player = 0
        action_player = 0
        movestack = []
        return PublicState(num_players, cards, coins, turn_counter, state_class, curr_player, action_player, movestack)

    def add_targets(self, valid_actions, player, last_move_player):
        moves_with_targets = []
        for move in valid_actions:
            if move == MoveType.coup or move == moveType.assassinate or move == moveType.steal:
                for i in range(self.players):
                    if i != player:
                        moves_with_targets.append([move, i])
            elif isinstance(move, CounterMoveType):
                moves_with_targets.append([move, last_move_player])
            elif isinstance(move, ChallengeMoveType):
                moves_with_targets.append([move, last_move_player])
            else:
                moves_with_targets.append([move, player])
        return moves_with_targets

    def valid_moves(self, player, public_state):
        #called by game manager for each player to pass to each agent
        if public_state.state_class == StateQuality.ACTION and player == public_state.curr_player:
            curr_coins = public_state.coins[public_state.curr_player]
            moves = [MoveType.income, MoveType.foreign_aid]
            if curr_coins > 3:
                moves.append(MoveType.assassinate)
            if curr_coins > 7:
                moves.append(MoveType.coup)
            moves.append([MoveType.tax, MoveType.steal, MoveType.assassinate])

            #reset moves to only have coup if over coin limit
            if curr_coins >= 10:
                moves = [MoveType.coup]

            return moves 
        
        elif public_state.state_class == StateQuality.COUNTER:
            #movestack stores [move type, move object] with move object storing target
            last_action = public_state.movestack[-1]
            if public_state.action_player != player:
                if last_action[0] == MoveType.foreign_aid:
                    return [CounterMoveType.foreign_aid]
                #aside from foreign aid, other counters can only be initiated if a player is a target
                elif last_action[1].target == player and last_action[0] in counter_index:
                    return [counter_index[last_action[0]]]
                else:
                    return []
            else:
                return []
            
        elif public_state.state_class == StateQuality.CHALLENGEACTION or public_state.state_class == StateQuality.CHALLENGECOUNTER:
            return [ChallengeMoveType.inaction, ChallengeMoveType.challenge]

        elif public_state.state_class == StateQuality.EXCHANGE:
            #take public deck, shuffle, and draw first two
            moves = self.show_deck_top()
            moves.append(InfluenceType.inaction)
            return moves


    def is_terminal(self, public_state):
        """return -1 if not terminal, otherwise index of player"""
        alive_count = self.players
        alive_ind = -1
        for i in range(self.players):
            #if both cards are flipped (-1 means not public/in play)
            if public_state.cards[i][0] != -1 and public_state.cards[i][1] != -1:
                alive_count -= 1
            else:
                alive_ind = i
        if alive_count == 1:
            return alive_ind 
        else: 
            return -1
            
    def show_deck_top(self):
        random.shuffle(self.deck)
        return [self.deck[0], self.deck[1]]


    #updates public and private game states by evaluating the results of the entire turn: actions, counteractions, challenges
    #returns [state, finished] where continue is a bool indicating whether the turn is over
    def eval_turn(self, state, index):
        #index is an integer showing how much from the end of the list we need to go back to find the starting action
        starting_action = state.movestack[-1*index - 1]
        finished = False 
        while not finished:
            if index == 0:
                #no other actions were attempted aside from the starting action, direct eval
                #TODO: 

                #moves involving just change in coins (completely public state change)
                if starting_action[0] == MoveType.income:

                elif starting_action[0] == MoveType.foreign_aid:

                elif starting_action[0] == MoveType.tax:
                
                elif starting_action[0] == MoveType.steal:

                #moves involving further choice and private state adjustment
                elif starting_action[0] == MoveType.assasinate:

                elif starting_action[0] == MoveType.coup:

                elif starting_action[0] == MoveType.exchange:

                finished = True

            elif index == 1:
                #either a challenge or a counteraction was attempted 
                if starting_action[0] == ChallengeMoveType.challenge:
                    #if challenge succeeded, introduce choice to lose card and mark finished

                    #if challenged failed, action goes through; introduce choice to lose card go back to action

                #counter moves prevent change in state except in the case of assassination, where spent coins are not returned
                elif starting_action[0] == CounterMoveType.assassinate:

                    finished = True
            elif index == 2: 
                #either challenge + uncontested counter or counter + challengecounter

                #if last move on the stack is a challenge:
                    #evaluate challenge on the counteraction; if successful, introduce choice to lose card and go back to action

                    #if failed, counteraction succeeds and action fails; introduce choice to lose card and mark finished

                #elif last move on the stack is a counter:



    def play_game(self, agents, print=False):
        winner = -1
        while winner = self.is_terminal(self.curr_state) == -1:
            curr = self.curr_state
            additional_actions = 0

            challenge_initiated = -1
            counter_initiated = -1

            turn_over = False

            #action phase
            valid_moves = self.add_targets(self.valid_moves(curr.curr_player, curr), curr.action_player)
            chosen_move = agents[curr.curr_player].make_move(valid_moves, curr)
            curr.movestack.append([curr.curr_player, move_objs[chosen_move[0]](curr.curr_player, chosen_move[1])])
            
            #challenge phase, for action
            curr.state_class = StateQuality.CHALLENGEACTION
            challenge_initiated = -1
            for i in range(self.players):
                if i != curr.curr_player:
                    valid_moves = self.add_targets(self.valid_moves(currr.curr_player, curr), curr.action_player)
                    chosen_move = agents[curr.curr_player].make_move(valid_moves, curr)
                    if chosen_move[0] == ChallengeMoveType.challenge:
                        curr.movestack.append([curr.curr_player, move_objs[chosen_move[0]](i, chosen_move[1])])
                        additional_actions += 1
                        challenge_initiated = i
                        break 
            if challenge_initiated > -1:
                #skip other phases and immediately evaluate result of challenge/edit state
                result = self.eval_turn(curr, additional_actions)
                curr = result[0]
                turn_over = result[1]
                if turn_over:
                    #challenge successful
                    curr.state_class = StateQuality.ACTION
                else:
                    #challenge unsuccessful; still opportunity to counter
                    curr.state_class = StateQuality.COUNTER
            else:
                #challenge not initiated: move on to counter phase
                curr.state_class = StateQuality.COUNTER
                    
            
            #COUNTER PHASE
            if curr.state_class == StateQuality.COUNTER:
                counter_initiated = -1
                for i in range(self.players):
                    if i != curr.curr_player:
                        valid_moves = self.add_targets(self.valid_moves(currr.curr_player, curr), curr.movestack[-1][1].player)
                        #in the case of uncounterable moves (like exchange), no counters or further challenges
                        #counter_initiated will remain -1 and state will go to ACTION phase, completing starting action
                        if len(valid_moves) > 0:
                            chosen_move = agents[curr.curr_player].make_move(valid_moves, curr)
                            if chosen_move[0] != CounterMoveType.inaction:
                                counter_initiated = i
                                additional_actions += 1
                                curr.movestack.append([curr.curr_player, move_objs[chosen_move[0]](i, chosen_move[1])])
                                break
                if counter_initiated > -1:
                    curr.state_class = StateQuality.CHALLENGECOUNTER
                else:
                    #no counter initiated; skip challengecounter phase and move back to action
                    result = self.eval_turn(curr, additional_actions)
                    curr = result[0]
                    turn_over = result[1]
                    curr.state_class = StateQuality.ACTION


            #challenge phase, for counteraction
            if curr.state_class == StateQuality.CHALLENGECOUNTER:
                challenge_initiated = -1
                for i in range(self.players):
                    if i != curr.curr_player:
                        valid_moves = self.add_targets(self.valid_moves(currr.curr_player, curr), curr.movestack[-1][1].player)
                        chosen_move = agents[curr.curr_player].make_move(valid_moves, curr)
                        if chosen_move[0] == ChallengeMoveType.challenge:
                            curr.movestack.append([curr.curr_player, move_objs[chosen_move[0]](i, chosen_move[1])])
                            additional_actions += 1
                            challenge_initiated = i 
                            break
                if challenge_initiated > -1: 
                    result = self.eval_turn(curr, additional_actions)
                    curr = result[0]
                    turn_over = result[1]

            if not turn_over:
                result = self.eval_turn(curr, additional_actions)
            #advance to next turn
            curr.state_class = StateQuality.ACTION
            curr.curr_player = (curr.curr_player + 1) % curr.players
            

        return winner 
        
            
    

    #TODO: change initialization of each move
        #must include targeted players in init()
        #in execute, must implement direct player intervention point
            #exchange move particularly
            #abstract away move obj from game tree decision making "moves"

    class BaseMove:
        def __init__(self, player, target):
            self.player = player 
            self.target = target
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state):
            """"""
            pass

    class TaxMove:
        def __init__(self):
            self.index =4
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins+3,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,[(self.index, player)])
            else:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins+3,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,[(self.index,player)])

    class AssassinateMove:
        def __init__(self):
            self.index = 5 
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            #delay card loss after other stages; only calculate coin loss
            if player== 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins-3,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, curr_state.next_quality(), (player+1)%2,[(self.index,player)])
            else:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins-3,curr_state.turn_counter, curr_state.next_quality(), (player+1)%2,[(self.index, player)])   

    class StealMove:
        def __init__(self):
            self.index = 6 
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            stolen_amount = 2
            if player == 0:
                if curr_state.p2coins < 2:
                    stolen_amount = curr_state.p2coins
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins+stolen_amount,curr_state.p2cards,curr_state.p2coins-stolen_amount,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,[(self.index, player)])
            else:
                if curr_state.p1coins < 2:
                    stolen_amount = curr_state.p1coins
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins-stolen_amount,curr_state.p2cards,curr_state.p2coins+stolen_amount,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,[(self.index, player)]) 

    class IncomeMove:
        def __init__(self):
            self.index = 1
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins+1,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, StateQuality.ACTION,(player+1)%2,[(self.index, player)])
            else:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins+1,curr_state.turn_counter, StateQuality.ACTION,(player+1)%2,[(self.index, player)])

    class ForeignAidMove:
        def __init__(self):
            self.index = 2
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins+2,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, StateQuality.COUNTER,(player+1)%2,[(self.index, player)])
            else:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins+2,curr_state.turn_counter, StateQuality.COUNTER,(player+1)%2,[(self.index,player)]) 

    class CoupMove:
        def __init__(self):
            self.index = 3
        
        def assign_players(self,p1obj,p2obj):
            self.p1 = p1obj 
            self.p2 = p2obj

        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins-7,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, StateQuality.LOSINGCARD,(player+1)%2,[(self.index,player)])
            else:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins-7,curr_state.turn_counter, StateQuality.LOSINGCARD,(player+1)%2,[(self.index,player)]) 
    
    class CounterForeignAidMove:
        def __init__(self):
            self.index = 7
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            curr_state.movestack.append((self.index,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins-2,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,curr_state.movestack)
            else: 
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins-2,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,curr_state.movestack)  

    class CounterStealMove:
        def __init__(self):
            self.index = 8
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            curr_state.movestack.append((self.index,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins+2,curr_state.p2cards,curr_state.p2coins-2,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,curr_state.movestack)
            else: 
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins-2,curr_state.p2cards,curr_state.p2coins+2,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,curr_state.movestack)  
  

    class CounterAssassinMove:
        def __init__(self):
            self.index = 9
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state, bin_encoder, history):
            player = curr_state.curr_player
            history.append((self,player))
            curr_state.movestack.append((self.index,player))
            if player == 0:
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins ,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,curr_state.movestack)
            else: 
                return PublicState(bin_encoder(),curr_state.p1cards,curr_state.p1coins,curr_state.p2cards,curr_state.p2coins,curr_state.turn_counter, curr_state.next_quality(),(player+1)%2,curr_state.movestack)  
  

    class ChallengeMove:
        def __init__(self,associationtable):
            self.index = 10
            self.associations = associationtable
        def assign_players(self,p1obj,p2obj):
            self.p1 = p1obj 
            self.p2 = p2obj
        def execute(self,curr_state,bin_encoder,history):
            last_action = curr_state.movestack.pop()[0] 
            card_challenge = self.associations[last_action]
            curr_state.movestack.append((self.index,curr_state.curr_player))
            if curr_state.curr_player == 0:
                if card_challenge not in self.p2.cards:
                    #successful challenge
                    return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins, curr_state.turn_counter,StateQuality.LOSINGCARD, (curr_state.curr_player+1)%2,curr_state.movestack)
                else:
                    return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins, curr_state.turn_counter,StateQuality.LOSINGCARD, curr_state.curr_player,curr_state.movestack)
            else: 
                if card_challenge not in self.p1.cards:
                    #successful challenge
                    return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins, curr_state.turn_counter,StateQuality.LOSINGCARD, (curr_state.curr_player+1)%2,curr_state.movestack)
                else:
                    return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins, curr_state.turn_counter,StateQuality.LOSINGCARD, curr_state.curr_player,curr_state.movestack)

    class AllowMove:
        def __init__(self):
            self.index = 11 

        def execute(self,curr_state,bin_encoder,history):
            next_counter = curr_state.turn_counter
            next_player = curr_state.curr_player
            curr_state.movestack.append((self.index,curr_state.curr_player))
            if curr_state.next_quality() == StateQuality.ACTION:
                next_counter += 1
                next_player = (next_player + 1)%2

            #allowing at some point in the assasination route
            if curr_state.movestack[0].index == 5:
                last_move = curr_state.movestack[len(curr_state.movestack)-1]
                if last_move[0] == 9:
                    #last move was a contessa, and allowing contessa to block: no changes 
                    return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins,next_counter,curr_state.next_quality(),next_player,curr_state.movestack)
                elif last_move[0] == 11:
                    #last move was an opportunity to block with contessa but chose to let assassin go through: advance to LOSINGCARD
                    return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins,next_counter,StateQuality.LOSINGCARD,next_player,curr_state.movestack)
            
            return PublicState(curr_state.bins, curr_state.p1cards, curr_state.p1coins, curr_state.p2cards, curr_state.p2coins,next_counter,curr_state.next_quality(),next_player,curr_state.movestack)
    class LoseCardZero:
        def __init__(self, game):
            self.index = 12
            self.game = game 

        def execute(self, curr_state,bin_encoder,history):
            if curr_state.curr_player == 0:
                card_lost = self.game.p1cards.pop(0)
                self.game.p1deadcards.append(card_lost)
                self.game.history.append((-1, 0, card_lost))
                p1cards = curr_state.p1cards-1
                p2cards = curr_state.p2cards
                
            else:
                card_lost = self.game.p2cards.pop(0)
                self.game.p2deadcards.append(card_lost)
                self.game.history.append((-1,1,card_lost))
                p1cards = curr_state.p1cards
                p2cards = curr_state.p2cards-1
            
            curr_action = curr_state.movestack.pop(0)
            if curr_action[1] == 0:
                next_player = 1
            else:
                next_player = 0
                    
            return PublicState(bin_encoder(), p1cards, curr_state.p1coins, p2cards,curr_state.p2coins,curr_state.turn_counter+1,StateQuality.ACTION, next_player, [])

    class LoseCardOne:
        def __init__(self, game):
            self.index = 13
            self.game = game 

        def execute(self, curr_state,bin_encoder,history):
            if curr_state.curr_player == 0:
                card_lost = self.game.p1cards.pop(1)
                self.game.p1deadcards.append(card_lost)
                self.game.history.append((-1, 0, card_lost))
                p1cards = curr_state.p1cards-1
                p2cards = curr_state.p2cards
            else:
                card_lost = self.game.p2cards.pop(1)
                self.game.p2deadcards.append(card_lost)
                self.game.history.append((-1,1,card_lost))
                p1cards = curr_state.p1cards
                p2cards = curr_state.p2cards-1

            curr_action = curr_state.movestack.pop(0)
            if curr_action[1] == 0:
                next_player = 1
            else:
                next_player = 0
                    
            return PublicState(bin_encoder(), p1cards, curr_state.p1coins, p2cards,curr_state.p2coins,curr_state.turn_counter+1,StateQuality.ACTION, next_player, [])

