import time
import numpy as np
import mss
import cv2
import pyautogui
import torch
from collections import deque

import gymnasium as gym
from gymnasium import spaces
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback

from transformers import GPT2LMHeadModel, GPT2TokenizerFast

# --- Custom Gym Environment ---
class BlackOpsZombiesEnv(gym.Env):
    def __init__(self):
        super().__init__()
        # Observation: grayscale 84×84
        self.observation_space = spaces.Box(0, 255, (84, 84, 1), dtype=np.uint8)
        # Actions: W, A, S, D, shoot, aim
        self.action_space = spaces.Discrete(6)
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        # Simple state for GPT-2 prompts
        self.state = {"round": 1, "ammo": 30}

    def reset(self, **kwargs):
        time.sleep(1)  # allow game to reset if needed
        frame = self._grab_frame()
        return frame, {}

    def step(self, action):
        self._inject_action(action)
        frame = self._grab_frame()
        # Dummy reward: +1 per frame survived
        reward = 1.0
        # Increment round every 500 steps
        if np.random.rand() < 0.002:
            self.state["round"] += 1
        done = False  # detect game over via image match in real use
        return frame, reward, done, False, {}

    def _grab_frame(self):
        img = np.array(self.sct.grab(self.monitor))
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        resized = cv2.resize(gray, (84, 84))
        return resized.reshape(84, 84, 1)

    def _inject_action(self, action):
        # Map 0–5 to keys/mouse
        mapping = {
            0: ("key", "w"), 1: ("key", "a"), 2: ("key", "s"),
            3: ("key", "d"), 4: ("mouse", "left"), 5: ("mouse", "right")
        }
        kind, code = mapping[action]
        if kind == "key":
            pyautogui.keyDown(code)
            time.sleep(0.05)
            pyautogui.keyUp(code)
        else:
            pyautogui.mouseDown(button=code)
            time.sleep(0.05)
            pyautogui.mouseUp(button=code)

# --- GPT-2 Callback for High-Level Planning ---
class GPT2Callback(BaseCallback):
    def __init__(self, env, tokenizer, model, verbose=0):
        super().__init__(verbose)
        self.env = env
        self.tokenizer = tokenizer
        self.gpt2 = model
        self.memory = deque(maxlen=10)
        self.interval = 1000  # steps between plans

    def _on_step(self) -> bool:
        # Every `interval` steps, get a plan
        if self.num_timesteps % self.interval == 0:
            st = self.env.state
            prompt = f"Round {st['round']}, ammo {st['ammo']}. Strategy?"
            inputs = self.tokenizer(prompt, return_tensors="pt", local_files_only=True)
            out = self.gpt2.generate(**inputs, max_new_tokens=20, do_sample=False)
            plan = self.tokenizer.decode(out[0], skip_special_tokens=True)
            self.memory.append((self.num_timesteps, plan))
        return True

# --- Main entrypoint ---
def main():
    # 1. Wait before starting controls
    print("Position on game window. Starting in 10 seconds...")
    time.sleep(10)

    # 2. Prepare GPT-2 offline
    tokenizer = GPT2TokenizerFast.from_pretrained("./models/gpt2", local_files_only=True)
    gpt2 = GPT2LMHeadModel.from_pretrained("./models/gpt2", local_files_only=True).eval()

    # 3. Create env and agent
    env = BlackOpsZombiesEnv()
    callback = GPT2Callback(env, tokenizer, gpt2)

    model = DQN(
        "CnnPolicy", env,
        learning_rate=1e-4,
        buffer_size=100_000,
        learning_starts=1_000,
        batch_size=32,
        target_update_interval=1_000,
        verbose=1
    )

    # 4. Start real-time learning
    model.learn(total_timesteps=int(1e6), callback=callback)

    # 5. Save trained agent & GPT-2 memory
    model.save("frank_castle_dqn")
    with open("gpt2_memory.txt", "w") as f:
        for ts, plan in callback.memory:
            f.write(f"{ts}: {plan}\n")

if __name__ == "__main__":
    main()



