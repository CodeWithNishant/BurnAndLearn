import time
from burn_and_learn_gym import RocketEnv

env = RocketEnv()
obs = env.reset()
done = False

while not done:
    action = env.action_space.sample()  # random action
    obs, reward, done, info = env.step(action)
    env.render(mode="human")

    # Handle window events so pygame actually shows the frame
    import pygame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    time.sleep(0.02)  # slow down so you can see it

env.close()