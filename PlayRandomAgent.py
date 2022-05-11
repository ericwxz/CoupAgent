from GeneralCoup import MultiPlayerCoup
from Agent import *
#Testing against random agent

rand_agent = RandomAgent()
human_agent = HumanAgent(0)
agent_list = [human_agent, rand_agent]
game = MultiPlayerCoup(agent_list)

result = game.play_game(print_phases=True)
print("Winner of this game: Player " + str(result))
