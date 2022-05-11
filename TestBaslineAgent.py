from GeneralCoup import MultiPlayerCoup
from Agent import *

#Testing against baseline agent

bl_agent = BaselineAgent()
human_agent = HumanAgent(0)
agent_list = [human_agent, bl_agent]
game = MultiPlayerCoup(agent_list)

result = game.play_game(print_phases=True)
print("Winner of this game: Player " + str(result))
