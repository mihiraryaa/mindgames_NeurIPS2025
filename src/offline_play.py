
from src.agents.revac import RevacAgent
from src.agents.revac2_1 import Revac2Agent

import textarena as ta 


# initialize the agents
agents = {
    0: RevacAgent("gpt-5-mini", "openai"),
    1: RevacAgent("gpt-5-mini", "openai"),
    2: RevacAgent("gpt-5-mini", "openai"),
    3: RevacAgent("gpt-5-mini", "openai"),
    4: Revac2Agent("gpt-5-mini", "openai"),
    5: Revac2Agent("gpt-5-mini", "openai"),
}


    
num=str(len(agents))

# initialize the environment
env = ta.make(env_id="SecretMafia-v0")
env.reset(num_players=len(agents))

# main game loop
final_obs=""
done = False 
while not done:
  player_id, observation = env.get_observation()
  #print('-'*30, "Player-",player_id)
  action = agents[player_id](observation)

  done, step_info = env.step(action=action)
  final_obs=observation+'\n\n'+action


rewards, game_info = env.close()

print(final_obs)
print(f"Rewards: {rewards}")
print(f"Game Info: {game_info}")

