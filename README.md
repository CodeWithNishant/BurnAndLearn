# BurnAndLearn 🚀

A reinforcement learning environment for training rockets to land like SpaceX

## Overview
Welcome to the project Burn And Learn - Have a Safe Landing!!
This project is a custom 2D rocket reusable rocket landing simulator built in python using pygame and wrapped around Gymnasium API.
### The goal: launch a rocket to space, re-enter, and land safely on Earth.

Inspired by SpaceX’s Falcon 9 landings, this environment allows you to train RL agents (PPO, DQN, etc.) or manually play with physics-based controls.

## Features
	•	 Realistic physics: gravity, thrust, RCS thrusters, fuel consumption
	•	 Environmental effects: air resistance, wind
	•	 Manual play mode with keyboard controls
	•	 Reinforcement Learning environment (Gym-compatible)
	•	 Works with Stable-Baselines3 (PPO, DQN, SAC, etc.)

 ## Project Structure
 BurnAndLearn/  
│  
├── physics/                # Rocket physics (forces, gravity, controls)  
├── rendering/              # Pygame-based rendering  
├── utils/                  # Camera, helper classes  
├── burn_and_learn_gym.py   # Gym environment wrapper  
├── rocket_game.py          # Playable rocket game  
├── test_env.py             # Test script for the Gym environment  
├── requirements.txt        # Project dependencies  
└── README.md               # This file  
|__ main.py                 # Main file  
|__ config.py               # Project configurations  

## How to Play in Manual Mode
run - 'python3 main.py' in the project root

## Controls:
	•	⬆️ UP: Fire main engine
	•	⬅️ LEFT: Fire left RCS thruster (rotate right)
	•	➡️ RIGHT: Fire right RCS thruster (rotate left)
	•	🚀 Goal: Reach space (altitude > 100 km) and land safely with low speed (<5.0m/s) + upright angle(<0.2 radians/ ~11.5 degrees ).

## Install dependencies
pip3 install -r requirements.txt

## Run the test environemnt
run - 'python3 test_env.py' in project root
Note : This will make rocket to randomly choose different rocket actions.

## Requirements
	•	Python 3.10+
	•	pygame
	•	gymnasium
	•	numpy
	•	stable-baselines3

 ## 🛠 Roadmap
	•	Add landing pad target
	•	Add variable wind conditions
	•	Multi-agent support (racing rockets 🚀🚀)
	•	More advanced reward shaping

 ## 📜 License
 MIT License – free to use, modify, and share.

## 🙌 Acknowledgements
	•	OpenAI Gym for the environment standard
	•	Stable-Baselines3 for RL algorithms
	•	SpaceX for inspiring the idea 💡
