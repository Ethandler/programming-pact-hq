import time
import math
import os
import krpc
import torch
import logging
import signal
from typing import Optional, List
from collections import deque
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# --- Configuration ---
LOG_FILE = "oberon_log.txt"
HIVE_SIZE = 10
TARGET_ORBIT_ALT = 75000
AI_UPDATE_INTERVAL = 0.1
MAX_NEW_TOKENS = 100
MAX_Q = 55000
STAGE_COOLDOWN = 0.5
LAUNCH_STABILITY_DELAY = 1.0
LANDING_ALTITUDE_THRESHOLD = 5
MUN_TRANSFER_ALTITUDE = 120000

shutdown_requested = False

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("UKF_MissionControl")

class MissionRecorder:
    def __init__(self):
        self.history = deque(maxlen=100)
        self.staging_log = []

    def log_captain(self, msg):
        entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        with open(LOG_FILE, 'a') as f:
            f.write(entry + "\n")
        logger.info(msg)
        self.history.append(entry)
        self.staging_log.append(entry)

mission_recorder = MissionRecorder()

# --- AI ---
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
        full_prompt = f"Pilot AI Directive:\n{'\n'.join(self.context)}\nEnvironment:\n{prompt}\nDirective:"
        votes = {}
        inputs = tokenizer(full_prompt, return_tensors='pt').to(device)
        for model in aihive:
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=True, temperature=0.7, top_p=0.9)
            action = tokenizer.decode(outputs[0], skip_special_tokens=True).split('Action:')[-1].strip()
            votes[action] = votes.get(action, 0) + 1
        best_action = max(votes, key=votes.get)
        self.context.append(f"Action: {best_action}")
        return best_action

aimind = AIMind()

# --- Stage Controller ---
class StageController:
    def __init__(self, vessel):
        self.vessel = vessel
        self.last_stage_time = 0
        self.stage_history = []

    def analyze_stage(self) -> bool:
        if time.time() - self.last_stage_time < STAGE_COOLDOWN:
            return False

        stage = self.vessel.control.current_stage
        mission_recorder.log_captain(f"Analyzing stage {stage}")

        all_parts = self.vessel.parts.all
        current_stage_parts = [p for p in all_parts if p.stage == stage and not p.decoupled]

        engines = [e for e in self.vessel.parts.engines if e.part.stage == stage]
        has_engine = any(e.has_fuel and e.thrust > 0 for e in engines)
        should_stage = not has_engine and any(current_stage_parts)

        if should_stage:
            mission_recorder.log_captain(f"Stage {stage} ready: {len(current_stage_parts)} parts remaining")
        return should_stage

    def execute_stage(self):
        if self.analyze_stage():
            stage = self.vessel.control.current_stage
            self.vessel.control.activate_next_stage()
            self.last_stage_time = time.time()
            mission_recorder.log_captain(f"Staging: {stage} -> {self.vessel.control.current_stage}")
            self.stage_history.append((time.time(), stage))
            return True
        return False

# --- Mission Controllers ---
class MissionController:
    def __init__(self, conn):
        self.conn = conn
        self.vessel = conn.space_center.active_vessel
        self.body = self.vessel.orbit.body
        self.sc = conn.space_center
        self.stage_controller = StageController(self.vessel)

    def altitude(self): return self.vessel.flight().mean_altitude
    def apoapsis(self): return self.vessel.orbit.apoapsis_altitude
    def periapsis(self): return self.vessel.orbit.periapsis_altitude
    def dynamic_pressure(self): return self.vessel.flight().dynamic_pressure

class LaunchController(MissionController):
    def execute_phase(self):
        mission_recorder.log_captain("Initiating smart launch sequence")
        self.vessel.control.throttle = 1.0
        self.vessel.auto_pilot.engage()
        self.vessel.auto_pilot.target_pitch_and_heading(90, 90)

        ignition = False
        while not ignition and not shutdown_requested:
            if self.stage_controller.execute_stage():
                mission_recorder.log_captain("Stage triggered pre-ignition")
            if any(e.active and e.thrust > 50 for e in self.vessel.parts.engines):
                ignition = True
                mission_recorder.log_captain("Engine ignition detected")
            time.sleep(0.1)

        while self.apoapsis() < TARGET_ORBIT_ALT * 0.95 and not shutdown_requested:
            q = self.dynamic_pressure()
            throttle = min(1.0, (MAX_Q * 1.1 - q) / (MAX_Q * 0.2))
            self.vessel.control.throttle = throttle
            self.stage_controller.execute_stage()
            alt = self.altitude()
            if alt > 1000:
                pitch = 90 * (1 - min(alt/45000, 1))
                self.vessel.auto_pilot.target_pitch_and_heading(pitch, 90)
            time.sleep(0.1)

        mission_recorder.log_captain("Max Q and target apoapsis reached")
        return OrbitCircularizationController(self.conn)

class OrbitCircularizationController(MissionController):
    def execute_phase(self):
        mission_recorder.log_captain("Precision orbital insertion")
        mu = self.body.gravitational_parameter
        r = self.apoapsis()
        v_target = math.sqrt(mu / r)
        v_current = math.sqrt(self.vessel.flight().horizontal_speed**2 + self.vessel.flight().vertical_speed**2)
        delta_v = v_target - v_current
        burn_time = (self.vessel.mass * delta_v) / self.vessel.available_thrust
        start_ut = self.sc.ut

        self.vessel.auto_pilot.target_direction = (0, 1, 0)
        self.vessel.auto_pilot.wait()
        self.vessel.control.throttle = 1.0

        while self.sc.ut < start_ut + burn_time * 0.95:
            remaining = (start_ut + burn_time) - self.sc.ut
            self.vessel.control.throttle = min(1.0, remaining / 2)
            time.sleep(0.1)

        self.vessel.control.throttle = 0.0
        mission_recorder.log_captain(f"Orbit achieved: {self.apoapsis()/1000:.1f}km x {self.periapsis()/1000:.1f}km")
        return MunTransferController(self.conn)

class MunTransferController(MissionController):
    def execute_phase(self):
        mission_recorder.log_captain("Calculating transfer to Mun")
        self.vessel.auto_pilot.set_reference_frame(self.body.non_rotating_reference_frame)
        self.vessel.auto_pilot.sas = True
        self.vessel.auto_pilot.sas_mode = self.sc.SASMode.prograde
        self.vessel.control.throttle = 1.0
        time.sleep(5)
        self.vessel.control.throttle = 0.0
        mission_recorder.log_captain("Trans-munar injection complete")
        return None

# --- Manager & Signals ---
class MissionManager:
    def connect(self):
        mission_recorder.log_captain("Connecting to KSP...")
        try:
            self.conn = krpc.connect(name="UKF Mission Control")
            mission_recorder.log_captain("Connection established")
            return True
        except Exception as e:
            mission_recorder.log_captain(f"Connection failed: {e}")
            return False

    def run(self):
        mission_recorder.log_captain("Starting mission sequence")
        controller = LaunchController(self.conn)
        next_phase = controller.execute_phase()
        while next_phase and not shutdown_requested:
            next_phase = next_phase.execute_phase()

signal.signal(signal.SIGINT, lambda s, f: [globals().update(shutdown_requested=True), mission_recorder.log_captain("Emergency shutdown!")])
signal.signal(signal.SIGTERM, lambda s, f: [globals().update(shutdown_requested=True), mission_recorder.log_captain("Termination signal received")])

if __name__ == "__main__":
    mission_recorder.log_captain("UKF Advanced Flight Systems Online")
    manager = MissionManager()
    if manager.connect():
        try:
            manager.run()
        except Exception as e:
            mission_recorder.log_captain(f"Critical failure: {str(e)}")
            raise
    mission_recorder.log_captain("Mission termination sequence complete")
