import random 
import enum

INFLUENCE_TO_SELECTION_OFFSET = 11


#influence type / move type indexes can be changed up here if there are any specific encoding concerns that arise later
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

influence_type_strings = {InfluenceType.duke:"Duke",InfluenceType.assassin:"Assassin", InfluenceType.captain:"Captain",
                          InfluenceType.ambassador:"Ambassador", InfluenceType.contessa:"Contessa", -1:"N/A"}

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
    steal_s = 9
    steal_a = 10

class ChallengeMoveType(enum.Enum):
    inaction = -1 
    challenge = 11

move_type_strings = {MoveType.income:"Income",MoveType.foreign_aid:"Foreign Aid", MoveType.coup:"Coup", 
                     MoveType.tax:"Tax (Duke)",MoveType.assassinate:"Assassinate (Assassin)",MoveType.steal:"Steal (Captain)",
                     MoveType.exchange:"Exchange (Ambassador)", CounterMoveType.inaction:"Allow", 
                     CounterMoveType.foreign_aid:"Block Foreign Aid (Duke)", CounterMoveType.assassinate:"Block Assassination (Contessa)",
                     CounterMoveType.steal_s:"Block Steal (Captain)", CounterMoveType.steal_a:"Block Steal (Ambassador)",
                     ChallengeMoveType.inaction:"Allow", ChallengeMoveType.challenge:"Challenge"}

#possible TODO: change to be general move info object and streamline information encoding above

#move-specific class definitions are artifacts of an older "simplified 2-player coup" implementation
class BaseMove:
    def __init__(self, player, target):
        self.player = player 
        self.target = target
    
    def execute(self, curr_state):
        """"""
        pass

class TaxMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " taxed (Duke)"
        
class AssassinateMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " assassinated Player " + str(self.target) + " (Assassin)" 

class StealMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " stole from Player " + str(self.target) + " (Captain)"

class ExchangeMove(BaseMove):
    def __repr__(self): 
        return "Player " + str(self.player) + " exchanged with the deck"

class IncomeMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " took income"

class ForeignAidMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " took foreign aid"
    
class CoupMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " couped Player " + str(self.target)
    
class CounterForeignAidMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " countered Player " + str(self.target) + "'s attempt at foreign aid"
    
class CounterStealCaptainMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " countered Player " + str(self.target) + "'s attempt at stealing (Captain)"

class CounterStealAmbassadorMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " countered Player " + str(self.target) + "'s attempt at stealing (Ambassador)"
    
class CounterAssassinMove(BaseMove):
    def __repr__(self):
        return "Player " + str(self.player) + " countered Player " + str(self.target) + "'s attempt at assassination (Contessa)"

class ChallengeMove(BaseMove):
    def __init__(self, player, target, success=None):
        self.success = success
        self.success_str = ""
        BaseMove.__init__(self, player, target)
    
    def update_success(self, success):
        self.success = success
        self.success_str = "successfully" if success else "unsuccessfully"

    def __repr__(self):
        return "Player " + str(self.player) + " challenged Player " + str(self.target) + "'s last action " + self.success_str

move_objs = {MoveType.income:IncomeMove, MoveType.foreign_aid:ForeignAidMove, MoveType.coup:CoupMove,
            MoveType.tax:TaxMove, MoveType.assassinate:AssassinateMove, MoveType.steal:StealMove, 
            MoveType.exchange:ExchangeMove, CounterMoveType.inaction:BaseMove, CounterMoveType.foreign_aid:CounterForeignAidMove,
            CounterMoveType.assassinate:CounterAssassinMove, CounterMoveType.steal_s:CounterStealCaptainMove, 
            CounterMoveType.steal_a:CounterStealAmbassadorMove, ChallengeMoveType.inaction:BaseMove, 
            ChallengeMoveType.challenge:ChallengeMove}

counter_index = {MoveType.foreign_aid:CounterMoveType.foreign_aid, 
                 MoveType.assassinate:CounterMoveType.assassinate,
                 MoveType.steal:[CounterMoveType.steal_s, CounterMoveType.steal_a]}

unchallengeable_moves = [MoveType.income, MoveType.foreign_aid, MoveType.coup]

uncounterable_moves = [MoveType.income, MoveType.coup]

restricted_moves = {
    MoveType.tax:InfluenceType.duke,
    MoveType.assassinate:InfluenceType.assassin,
    MoveType.steal:InfluenceType.captain,
    MoveType.exchange:InfluenceType.ambassador
}
restricted_countermoves = {
    CounterMoveType.foreign_aid:InfluenceType.duke,
    CounterMoveType.assassinate:InfluenceType.contessa,
    CounterMoveType.steal_s:InfluenceType.captain,
    CounterMoveType.steal_a:InfluenceType.ambassador
}


class PrivateState:
    #contains private cards and known sightings from the public deck
    def __init__(self, cards, sightings):
        """PrivateState(cards, sightings)
            cards = list of private influence cards still in play"""
        self.cards = cards
        self.sightings = sightings
    
    #def lost_influence(self):
        #TODO: maybe not? depends on state change mechanism
    
    def __repr__(self):
        repr_str = "Private influence: " 
        for card in self.cards:
            repr_str += influence_type_strings[card]
        return repr_str

class PublicState:
    #contains info about history, each player's coin count, and dead influence

    def __init__(self, players, cards, coins, turn_counter, state_class, curr_player, action_player, movestack, challenge_counts, recent_history):
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
        self.challenge_counts = challenge_counts
        self.recent_history = recent_history

    def is_terminal(self):
        """returns -1 if not terminal, 0 if p1 wins, 1 if p2 wins"""
        alive_count = 0
        for player in self.cards:
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

    def __repr__(self):
        line1 = "       "
        line2 = "Coins: "
        line3 = "Cards: "
        line4 = "       "
        for i in range(self.players):
            line1 += "Player" + str(i) + "    " #ten characters per player
            coins_str = str(self.coins[i])
            line2 += coins_str 
            line2 += " " * (11 - len(coins_str))
            line3 += influence_type_strings[self.cards[i][0]]
            line3 += " " * (11 - len(influence_type_strings[self.cards[i][0]]))
            line4 += influence_type_strings[self.cards[i][1]]
            line4 += " " * (11 - len(influence_type_strings[self.cards[i][1]]))
        return line1 + "\n" + line2 + "\n" + line3 + "\n" + line4 

        

class MultiPlayerCoup():
    #game object runs game loop and:
        #updates game state for every action made
        #fetches valid moves for every player
        #checks whether moves can be made and whether game phases need to be skipped
        #passes moves to player agents; waits on them for their choices
        #gives additional choices to agents if needed (ambassador exchange as a two-part decision)
    #game object also stores the deck that is neither private nor completely public

    #initialized by main program to generate all relevant states
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
            new_hand = PrivateState([self.deck.pop(), self.deck.pop()], [])
            agent_list[i].set_private_state(new_hand)
            private_states.append(new_hand)
        
        return
        

    def init_state(self, num_players):
        cards = []
        for _ in range(num_players):
            #unflipped cards-- no observations
            cards.append([-1,-1])
        coins = [2 for _ in range(num_players)]
        turn_counter = 0
        state_class = StateQuality.ACTION
        curr_player = 0
        action_player = 0
        movestack = []
        challenge_counts = {}
        recent_history = {}
        for i in range(num_players):
            recent_history[i] = [-1, -1, -1, -1, -1]
        return PublicState(num_players, cards, coins, turn_counter, state_class, curr_player, action_player, movestack, recent_history)

    def add_targets(self, valid_actions, player, last_move_player):
        moves_with_targets = []
        for move in valid_actions:
            if move == MoveType.coup or move == MoveType.assassinate or move == MoveType.steal:
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

    #provides valid types of actions for the start of a turn
        #if further choices need to be made after evaluating the other phases (exchange choice), those choices are given in eval_turn
        #otherwise, target selection is made by the agent
    def valid_moves(self, player, public_state):
        #called by game manager for each player to pass to each agent
        if public_state.state_class == StateQuality.ACTION and player == public_state.curr_player:
            curr_coins = public_state.coins[public_state.curr_player]
            moves = [MoveType.income, MoveType.foreign_aid]
            if curr_coins >= 3:
                moves.append(MoveType.assassinate)
            if curr_coins >= 7:
                moves.append(MoveType.coup)
            moves.extend([MoveType.tax, MoveType.steal, MoveType.exchange])

            #reset moves to only have coup if over coin limit
            if curr_coins >= 10:
                moves = [MoveType.coup]

            return moves 
        
        elif public_state.state_class == StateQuality.COUNTER:
            #movestack stores [move type, move object] with move object storing target
            last_action = public_state.movestack[-1]
            if public_state.curr_player != player:
                if last_action[0] == MoveType.foreign_aid:
                    return [CounterMoveType.inaction, CounterMoveType.foreign_aid]
                #aside from foreign aid, other counters can only be initiated if a player is a target
                elif last_action[1].target == player and last_action[0] in counter_index:
                    possible_counters = counter_index[last_action[0]]
                    return possible_counters if isinstance(possible_counters, list) else [possible_counters]
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


    def update_states_lose_card(self, state, loser, chosen_discard):
        self.agent_list[loser].lose_card(chosen_discard)
        #update public state with the flipped card
        if state.cards[loser][0] != -1:
            state.cards[loser][1] = chosen_discard 
        else:
            state.cards[loser][0] = chosen_discard


    #called in game loop when a challenge is initiated to determine the next game phase
        #1) checks private states and presents the loser with a choice to lose a card
        #2) receives choice from agent and edits private and public states
        #returns [state, True or False] signifying whether the challenge was successful or not
    def eval_challenge(self, state, initiator, target):
        #index to the challenged action in question will always be the penultimate on the movestack
        initiator_cards = self.agent_list[initiator].private_state.cards
        target_cards = self.agent_list[target].private_state.cards

        challenged_move_type = state.movestack[-2][0]
        challenged_influence_type = restricted_moves[challenged_move_type] if state.state_class == StateQuality.CHALLENGEACTION else restricted_countermoves[challenged_move_type]
        
        challenge_success = False
        
        if challenged_influence_type not in target_cards: 
            #challenge succeeded-- target chooses a card to lose 
            chosen_discard = self.agent_list[target].make_move(target_cards, state)
            #change public and private states with new information
            self.update_states_lose_card(state, target, chosen_discard)
            challenge_success = True

        else:
            #challenge failed-- initiator chooses a card to lose
            chosen_discard = self.agent_list[initiator].make_move(initiator_cards, state)
            #change public and private states with new information
            self.update_states_lose_card(state, initiator, chosen_discard)

            #TODO: target has to switch out the card in question for a random one from the deck
            random.shuffle(self.deck)
            new_card = self.deck.pop()
            self.agent_list[target].private_state.cards.remove(challenged_influence_type)
            self.agent_list[target].private_state.cards.append(new_card)
            self.deck.append(challenged_influence_type)
        
        state.movestack[-1][1].update_success(challenge_success)
        return [state, challenge_success]

    #returns True/False-- True if player #target is still alive, False otherwise
    def check_target_aliveness(self, state, target):
        if state.cards[target][0] == -1 or state.cards[target][1] == -1:
            return True 
        return False

    #action = [action_index, action_object]
    def eval_starting_action(self, state, starting_action):
        #no other actions were attempted aside from the starting action, direct eval
        target = starting_action[1].target 

        #moves involving just change in coins (completely public state change)
        if starting_action[0] == MoveType.income:
            state.coins[state.curr_player] += 1
        elif starting_action[0] == MoveType.foreign_aid:
            state.coins[state.curr_player] += 2
        elif starting_action[0] == MoveType.tax:
            state.coins[state.curr_player] += 3
        elif starting_action[0] == MoveType.steal:
            if self.check_target_aliveness(state, target):
                target_coins = state.coins[target]
                state.coins[target] = 0 if target_coins <= 2 else target_coins - 2
                state.coins[state.curr_player] += target_coins if target_coins <= 2 else 2

        #moves involving further choice and private state adjustment
        elif starting_action[0] == MoveType.assassinate:
            if self.check_target_aliveness(state, target):
                state.coins[state.curr_player] -= 3
                target_cards = self.agent_list[target].private_state.cards
                #target chooses a card to lose 
                chosen_discard = self.agent_list[target].make_move(target_cards, state)
                #change public and private states with new information
                self.update_states_lose_card(state, target, chosen_discard)

        elif starting_action[0] == MoveType.coup:
            if self.check_target_aliveness(state, target):
                state.coins[state.curr_player] -= 7
                target_cards = self.agent_list[target].private_state.cards
                #target chooses a card to lose 
                chosen_discard = self.agent_list[target].make_move(target_cards, state)
                #change public and private states with new information
                self.update_states_lose_card(state, target, chosen_discard)

        #possible TODO: edit encoding of possible exchange moves
        elif starting_action[0] == MoveType.exchange:
            if self.check_target_aliveness(state, target):
                deck_top = self.show_deck_top() 
                possible_exchanges = [[-1]]
                #generate possible exchanges in the form [held card to switch, new card from deck]
                for i in deck_top:
                    for j in self.agent_list[state.curr_player].private_state.cards:
                        possible_exchanges.append([j, i])
                chosen_exchange = self.agent_list[state.curr_player].make_move(possible_exchanges, state)
                if chosen_exchange != [-1]:
                    #edit private state and deck
                    deck_index = 0 if deck_top[0] == chosen_exchange[1] else 1
                    hand_index = 0 if self.agent_list[state.curr_player].private_state.cards[0] == chosen_exchange[0] else 1
                    discarded_card = self.agent_list[state.curr_player].private_state.cards[hand_index]
                    self.agent_list[state.curr_player].private_state.cards[hand_index] = chosen_exchange[1]
                    self.deck[deck_index] = discarded_card 

    def eval_counter(self, state, counteraction_type):
        if counteraction_type == CounterMoveType.assassinate:
            state.coins[state.curr_player] -= 3
        
    
    #note: eval_turn is called at the end of the turn (absence of a counter, or with all challenges evaluated)
        #eval_turn directly changes the game state (both public and private) and passes back the result to the play_game loop
    #note: in evaluating the turn, all changes to states based on challenges will have been integrated into state

    #updates public and private states with the results of actions (and counteractions)
    def eval_turn(self, state, index):
        #index is an integer showing how much from the end of the list we need to go back to find the starting action
        starting_action = state.movestack[-1*index - 1]

        if index == 0:
            #no challenges or counters initiated, just evaluate action
            self.eval_starting_action(state, starting_action)
        elif index == 1:
            #check if last move is a challenge-- if so, no counteraction was taken and the challenge failed, so evaluate action
            last_action = state.movestack[-1][0]
            if last_action == ChallengeMoveType.challenge: 
                self.eval_starting_action(state, starting_action)
            #counter moves prevent change in state except in the case of assassination, where spent coins are not returned
            else: 
                self.eval_counter(state, last_action)
            
        elif index == 2: 
            #either challenge + uncontested counter or counter + challengecounter
            last_action = state.movestack[-1][0]

            #if last move on the stack is a challengecounter:
            if last_action == ChallengeMoveType.challenge:
                if state.movestack[-1][1].success:
                    self.eval_starting_action(state, starting_action)
                else: 
                    self.eval_counter(state, state.movestack[-2][0])

            #elif last move on the stack is a counter:
            else: 
                self.eval_counter(state, last_action)

        elif index == 3:
            #unsuccessful challenge + counter + challengecounter
            #we only evaluate if the final counter was successful
            if state.movestack[-1][1].success:
                self.eval_starting_action(state, starting_action)

        return self.is_terminal(state)


    def play_game(self, print_phases=False):
        #TODO: cleanup references to agent_list
        #TODO: add recent history management to loop
        agents = self.agent_list
        winner = -1
        while (winner := self.is_terminal(self.curr_state)) == -1:
            curr = self.curr_state
            while curr.cards[curr.curr_player][0] != -1 and curr.cards[curr.curr_player][1] != -1:
                #loop over dead players where both cards are flipped; continue until we get to a player with at least one unturned influence
                curr.curr_player = (curr.curr_player + 1) % curr.players
            additional_actions = 0

            challenge_initiated = -1
            counter_initiated = -1

            turn_over = False

            #action phase
            if print_phases:
                print("\nACTION PHASE")
            valid_moves = self.add_targets(self.valid_moves(curr.curr_player, curr), curr.curr_player, curr.curr_player)
            chosen_move = agents[curr.curr_player].make_move(valid_moves, curr)
            curr.movestack.append([chosen_move[0], move_objs[chosen_move[0]](curr.curr_player, chosen_move[1])])
            #if print_phases:
            #    print(curr.movestack[-1])
            if chosen_move[0] not in unchallengeable_moves:
                curr.state_class = StateQuality.CHALLENGEACTION
            elif chosen_move[0] not in uncounterable_moves:
                curr.state_class = StateQuality.COUNTER

            #challenge phase, for action
            starting_action_type = curr.movestack[-1][0]
            if curr.state_class == StateQuality.CHALLENGEACTION:
                if print_phases:
                    print("\nACTION CHALLENGE PHASE")
                    print("Last action: " + str(curr.movestack[-1][1]))
                challenge_initiated = -1
                for i in range(self.players):
                    if i != curr.curr_player:
                        valid_moves = self.add_targets(self.valid_moves(i, curr), i, curr.curr_player)
                        chosen_move = agents[i].make_move(valid_moves, curr)
                        if chosen_move[0] == ChallengeMoveType.challenge:
                            curr.movestack.append([ChallengeMoveType.challenge, move_objs[chosen_move[0]](i, chosen_move[1])])
                            additional_actions += 1
                            challenge_initiated = i
                            break 
                if challenge_initiated > -1:
                    #skip other phases and immediately evaluate result of challenge/edit state
                    if print_phases:
                        print("Challenge initiated by Player " + str(challenge_initiated) + "against Player " + str(curr.curr_player))

                    #update record of challenges in state
                    challenge_dict_key = (challenge_initiated, curr.curr_player, restricted_moves[starting_action_type])
                    if challenge_dict_key not in curr.challenge_counts:
                        curr.challenge_counts[challenge_dict_key] = 1
                    else:
                        curr.challenge_counts[challenge_dict_key] += 1

                    result = self.eval_challenge(curr, challenge_initiated, curr.curr_player)
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
                if print_phases:
                    print("\nCOUNTER PHASE")
                    print("Last action: " + str(curr.movestack[-1 if challenge_initiated == -1 else -2][1]))
                counter_initiated = -1
                for i in range(self.players):
                    if i != curr.curr_player:
                        valid_moves = self.add_targets(self.valid_moves(i, curr), i, curr.movestack[-1][1].player)
                        #in the case of uncounterable moves (like exchange), no counters or further challenges
                        #counter_initiated will remain -1 and state will go to ACTION phase, completing starting action
                        if len(valid_moves) > 0:
                            chosen_move = agents[i].make_move(valid_moves, curr)
                            if chosen_move[0] != CounterMoveType.inaction:
                                counter_initiated = i
                                additional_actions += 1
                                curr.movestack.append([chosen_move[0], move_objs[chosen_move[0]](i, chosen_move[1])])
                                break
                if counter_initiated > -1:
                    curr.state_class = StateQuality.CHALLENGECOUNTER
                else:
                    #no counter initiated; skip challengecounter phase and move back to action
                    curr.state_class = StateQuality.ACTION


            #challenge phase, for counteraction
            if curr.state_class == StateQuality.CHALLENGECOUNTER:
                if print_phases:
                    print("\nCOUNTER CHALLENGE PHASE")
                    print("Last counter: " + str(curr.movestack[-1][1]))
                challenge_initiated = -1
                for i in range(self.players):
                    if i != counter_initiated:
                        valid_moves = self.add_targets(self.valid_moves(i, curr), i, curr.movestack[-1][1].player)
                        chosen_move = agents[i].make_move(valid_moves, curr)
                        if chosen_move[0] == ChallengeMoveType.challenge:
                            curr.movestack.append([ChallengeMoveType.challenge, move_objs[chosen_move[0]](i, chosen_move[1])])
                            additional_actions += 1
                            challenge_initiated = i 
                            break
                if challenge_initiated > -1: 
                    print("Challenge initiated by player " + str(challenge_initiated))
                    result = self.eval_challenge(curr, challenge_initiated, counter_initiated)
                    curr = result[0]
                    challenge_success = result[1]
                    if challenge_success:
                        #counter fails; starting action goes through
                        turn_over = False 
                    else:
                        #counter succeeds; no starting action
                        turn_over = True

            if not turn_over:
                result = self.eval_turn(curr, additional_actions)
            
            for agent in self.agent_list:
                #does nothing for most agents except for human players, for whom itll print their state
                agent.public_state_update(curr, curr.movestack[len(curr.movestack)-(additional_actions + 1):])

            #advance to next turn
            curr.state_class = StateQuality.ACTION
            curr.curr_player = (curr.curr_player + 1) % curr.players
        
        return winner 
        
            
    

