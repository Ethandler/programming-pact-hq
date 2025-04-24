# ZombieAgent: Reinforcement Learning with GPT2 for Black Ops Zombies

## Overview

ZombieAgent is a hybrid AI system that trains a reinforcement learning (RL) agent to play Call of Duty: Black Ops Zombies using a custom OpenAI Gym environment. It incorporates GPT-2 for high-level strategy suggestions.

## Features

- Custom `gymnasium` environment simulating BOZ inputs
- Screen capture using `mss` and `cv2`
- Real-time keyboard/mouse control with `pyautogui`
- GPT-2 integration for strategy guidance every 1000 frames
- Trains a DQN agent using `stable-baselines3`

## Requirements

```plaintext
numpy
mss
opencv-python
pyautogui
torch>=1.10.0
transformers>=4.0.0
gymnasium
stable-baselines3
```bash

## Folder Structure

```

./models/gpt2/       # Local GPT-2 model files
./frank_castle_dqn.zip  # Saved trained RL model

## How to Run

```bash
python zombie_agent.py
```

- Position your mouse over the game window before the 10-second countdown ends.
- Agent will train for 1 million frames with GPT-2 injected planning.

## Output

- Saves RL model as `frank_castle_dqn.zip`
- Writes GPT-2 generated strategic memory to `gpt2_memory.txt`

## Notes

- GPT-2 is used offline (no internet callout)
- This is an experimental project and not suitable for online matches

## License

Creative Commons Attribution-NonCommercial 4.0 International
