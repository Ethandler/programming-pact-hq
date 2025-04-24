import time
import math
import os
import krpc
import torch
import logging
import signal
from typing import Optional
from collections import deque
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# --- Configuration ---
LOG_FILE = "oberon_log.txt"
HIVE_SIZE = 10
TARGET_ORBIT_ALT = 75000
MUN_ORBIT_ALT = 20000
AI_UPDATE_INTERVAL = 0.1
MAX_NEW_TOKENS = 100
LANDING_THRESHOLD = 5
MAX_Q = 55000
STAGE_COOLDOWN = 1.0

shutdown_requested = False

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("UKF_MissionControl")

class MissionRecorder:
    def __init__(self):
        self.history = deque(maxlen=100)

    def log_captain(self, msg):
        entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        with open(LOG_FILE, 'a') as f:
            f.write(entry + "\n")
        logger.info(msg)
        self.history.append(entry)

mission_recorder = MissionRecorder()

# --- Load AI Hive ---
tokenizer = GPT2Tokenizer.from_pretrained('gpt2', pad_token='<|endoftext|>')
aihive = [GPT2LMHeadModel.from_pretrained('gpt2').eval() for _ in range(HIVE_SIZE)]

if torch.cuda.is_available():
    for model in aihive:
        model.half().cuda()

device = 'cuda' if torch.cuda.is_available() else 'cpu'

class AIMind:
    def __init__(self):
        self.context = deque(maxlen=5)

    def get_action(self, prompt: str) -> str:
        full_prompt = f"Pilot AI Dialog:\n{chr(10).join(self.context)}\nEnvironment:\n{prompt}\nDirective:"
        votes = {}
        inputs = tokenizer(full_prompt, return_tensors='pt').to(device)

        for model in aihive:
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=True, top_p=0.9)
            action = tokenizer.decode(outputs[0], skip_special_tokens=True).split('\n')[-1].strip()
            votes[action] = votes.get(action, 0) + 1

        best_action = max(votes, key=votes.get)
        self.context.append(f"Decision: {best_action}")
        return best_action

aimind = AIMind()

# --- Stage Logic ---
class StageController:
    def __init__(self, vessel):
        self.vessel = vessel
        self.last_stage_time = 0
        self.decouplers = [p for p in vessel.parts.decouplers if not p.decoupled]

    def analyze_stage(self):
        if time.time() - self.last_stage_time < STAGE_COOLDOWN:
            return False
        stage = self.vessel.control.current_stage
        if stage == 0:
            return False
        active = [e for e in self.vessel.parts.engines if e.part.stage == stage - 1 and e.active and e.has_fuel and e.thrust > 0.1 * e.max_thrust]
        decouplers = [d for d in self.decouplers if d.part.stage == stage - 1]
        return not active and decouplers

    def execute_stage(self):
        if self.analyze_stage():
            self.vessel.control.activate_next_stage()
            self.last_stage_time = time.time()
            mission_recorder.log_captain(f"Stage {self.vessel.control.current_stage} executed")
            return True
        return False

# --- Mission Phases ---
class MissionController:
    def __init__(self, conn):
        self.conn = conn
        self.sc = conn.space_center
        self.vessel = self.sc.active_vessel
        self.flight = self.vessel.flight()
        self.orbit = self.vessel.orbit
        self.body = self.orbit.body
        self.stage_controller = StageController(self.vessel)
        self._init_streams()

    def _init_streams(self):
        streams = self.conn.add_stream
        self.altitude = streams(getattr, self.flight, 'surface_altitude')
        self.vertical_speed = streams(getattr, self.flight, 'vertical_speed')
        self.horizontal_speed = streams(getattr, self.flight, 'horizontal_speed')
        self.apoapsis = streams(getattr, self.orbit, 'apoapsis_altitude')
        self.periapsis = streams(getattr, self.orbit, 'periapsis_altitude')
        self.dynamic_pressure = streams(getattr, self.flight, 'dynamic_pressure')
        self.fuel = streams(self.vessel.resources.amount, 'LiquidFuel')

    def execute_phase(self):
        raise NotImplementedError

class LaunchController(MissionController):
    def execute_phase(self):
        mission_recorder.log_captain("Launch phase initiated")
        self.vessel.control.throttle = 1.0
        self.vessel.control.activate_next_stage()
        self.vessel.auto_pilot.engage()
        self.vessel.auto_pilot.target_pitch_and_heading(90, 90)

        while self.apoapsis() < TARGET_ORBIT_ALT * 0.9 and not shutdown_requested:
            if self.dynamic_pressure() > MAX_Q * 0.8:
                self.vessel.control.throttle *= 0.95
            self.stage_controller.execute_stage()
            time.sleep(0.1)

        return OrbitCircularizationController(self.conn)

class OrbitCircularizationController(MissionController):
    def execute_phase(self):
        mission_recorder.log_captain("Circularizing orbit")
        mu = self.body.gravitational_parameter
        r = self.orbit.apoapsis
        delta_v = math.sqrt(mu/r) * (math.sqrt(2*r/(r + self.orbit.periapsis)) - 1)
        burn_time = delta_v / self.vessel.available_thrust * self.vessel.mass
        self.vessel.control.throttle = 1.0
        start_ut = self.sc.ut
        while self.sc.ut - start_ut < burn_time:
            time.sleep(0.1)
        self.vessel.control.throttle = 0.0
        return None

# --- Mission Manager ---
class MissionManager:
    def __init__(self):
        self.conn = None
        self.current_phase = None

    def connect(self):
        try:
            self.conn = krpc.connect(name="UKF_Command")
            mission_recorder.log_captain("Connected to KRPC")
            return True
        except Exception as e:
            mission_recorder.log_captain(f"Connection failed: {e}")
            return False

    def run(self):
        global shutdown_requested
        self.current_phase = LaunchController(self.conn)
        try:
            while self.current_phase and not shutdown_requested:
                next_phase = self.current_phase.execute_phase()
                self.current_phase = next_phase
        finally:
            if self.conn:
                self.conn.close()
                mission_recorder.log_captain("KRPC Disconnected")

# --- Signal Handling ---
def signal_handler(signum, frame):
    global shutdown_requested
    mission_recorder.log_captain(f"Shutdown signal ({signum}) received")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    mission_recorder.log_captain("UKF Autonomous Mission AI Online")
    manager = MissionManager()
    if manager.connect():
        manager.run()
    mission_recorder.log_captain("Mission complete. Standing down.")