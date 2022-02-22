import random 
import enum

class StateQuality(enum.Enum):
    ACTION = 0
    CHALLENGEACTION = 1
    COUNTER = 2
    CHALLENGECOUNTER = 3
    LOSINGCARD = 4

class InfluenceType(enum.Enum):
    duke = 0
    assassin = 1
    captain = 2
    ambassador = 3
    contessa = 4

class MoveType(enum.Enum):
    income = 0
    foreign_aid = 1
    coup = 2
    tax = 3
    assassinate = 4
    steal = 5
    exchange = 6

class CounterMoveType(enum.Enum):
    foreign_aid = 0
    assassinate = 1
    steal = 2

counter_index = {MoveType.foreign_aid:CounterMoveType.foreign_aid, 
                 MoveType.assassinate:CounterMoveType.assassinate,
                 MoveType.steal:CounterMoveType.steal}

unchallengeable_moves = [MoveType.income, MoveType.foreign_aid, MoveType.coup]

restricted_moves = {
    InfluenceType.duke:MoveType.income,
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

class MultiPlayerCoup():

    def valid_moves(self, public_state):
        if
    

    class BaseMove:
        def __init__(self, game):
            pass 
        
        #returns the new state of the game after execuing the action
        #updates self.history and reevaluates bins on each move
        def execute(self, curr_state):
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
            movestack = list of history"""
        #self.bins = bins
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

    def next_quality(self):
        #TODO: redo
        """return 0, 1, 2, 3 to represent whether the next game state is 
            either before any main actions (0), open to challenge immediately after (1),
            before an applicable counteraction (2), open to challenge after a counteraction (3)"""
        return (self.state_class + 1) % 4

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
