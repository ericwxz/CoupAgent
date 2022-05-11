from GeneralCoup import MultiPlayerCoup
from Agent import *
from BestReplySearch import *

rand_agent = RandomAgent()
human_agent = HumanAgent(0)
agent_list = [human_agent, rand_agent]
game = MultiPlayerCoup(agent_list)

result = game.play_game(print_phases=True)
print("Winner of this game: Player " + str(result))


"""
init_state = game.init_state(2)
print("test initial state coin encoding:")
print(rand_agent._encode_coins(init_state))
print("test initial state flipped influence encoding:")
print(rand_agent._encode_influence(init_state))
print("test initial state challenge history encoding:")
print(rand_agent._encode_challenges(init_state))
print("test initial state move history encoding:")
print(rand_agent._encode_history(init_state))
print("test initial private state encoding:")
print(human_agent._encode_private(rand_agent.private_state))

print("test complete initial state encoding:")
print(rand_agent.encode_state(init_state))"""

#baseline_agent = BestReplySearchAgent(0)
#agent_list = [baseline_agent,rand_agent]
#game = MultiPlayerCoup(agent_list)
#baseline_agent.set_game_info(game)
#result = game.play_game(print_phases=True)
#print("Winner of this game: Player " + str(result))