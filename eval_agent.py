# eval_agent.py
import time
import argparse
from stable_baselines3 import PPO
from burn_and_learn_gym import RocketEnv
import pygame

def run(model_path, episodes=5, render=True, sleep=0.02):
    model = PPO.load(model_path)
    env = RocketEnv()
    for ep in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, rew, done, truncated, info = env.step(int(action))
            done = done or truncated
            if render:
                env.render()
                # process events so window remains responsive
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        done = True
                        break
                time.sleep(sleep)
        print(f"Episode {ep+1} done. reward={rew}")
    env.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="path to model zip file")
    parser.add_argument("--episodes", type=int, default=3)
    args = parser.parse_args()
    run(args.model, episodes=args.episodes)