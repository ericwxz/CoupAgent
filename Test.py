from GeneralCoup import MultiPlayerCoup
from Agent import *
from BestReplySearch import *
from DetatAgent import *

#Testing functionality in DetatAgent
rand_agent = RandomAgent()
human_agent = HumanAgent(0)
agent_list = [human_agent, rand_agent]
game = MultiPlayerCoup(agent_list)
init_public = game.init_state(2)
init_private = human_agent.private_state
init_pbs = BeliefState(game, 0, 2, init_public, init_private)
init_subgame = CoupSubgame(game, 0, init_pbs)


#Testing BRS Agent
#baseline_agent = BestReplySearchAgent(0)
#agent_list = [baseline_agent,rand_agent]
#game = MultiPlayerCoup(agent_list)
#baseline_agent.set_game_info(game)
#result = game.play_game(print_phases=True)
#print("Winner of this game: Player " + str(result))