#!/usr/bin/env python3
"""
kerbal_bot.py - Kerbal Space Program autonomous lunar mission script
using kRPC and offline GPT-2 for mission logging and active learning.
"""
import sys
import time
import math
import krpc
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# --- Initialization ---
print("Connecting to kRPC server...", file=sys.stderr)
conn = krpc.connect(name='KerbalBot Lunar Transfer')
print("Connected to kRPC server.", file=sys.stderr)
sc = conn.space_center
vessel = sc.active_vessel
print(f"Active vessel: {vessel.name}", file=sys.stderr)

# Load GPT-2 for logs and learning
print("Loading GPT-2 model...", file=sys.stderr)
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2')
model.eval()
print("GPT-2 model loaded.", file=sys.stderr)

# Setup SAS/RCS
vessel.control.sas = True
vessel.control.rcs = True
try:
    vessel.control.sas_mode = sc.SASMode.stability_assist
    print("SAS Mode: Stability Assist", file=sys.stderr)
except Exception as e:
    print(f"Warning: SAS mode set failed: {e}", file=sys.stderr)

# Celestial bodies
kerbin = sc.bodies['Kerbin']
mun = sc.bodies['Mun']

# --- Helper Functions ---
def ask_gpt2(prompt, max_length=50):
    inputs = tokenizer.encode(prompt, return_tensors='pt')
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=max_length,
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def log_status(msg):
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {msg}" , file=sys.stderr)


def get_fuel_percentage():
    props = vessel.resources
    total = props.max('LiquidFuel') + props.max('Oxidizer')
    current = props.amount('LiquidFuel') + props.amount('Oxidizer')
    return (current / total * 100) if total > 0 else 0


def adaptive_log(prompt_prefix):
    state = f"Altitude: {vessel.flight().mean_altitude:.0f}m, Apoapsis: {vessel.orbit.apoapsis_altitude:.0f}m, Fuel: {get_fuel_percentage():.1f}%"
    log = ask_gpt2(f"{prompt_prefix} {state}")
    print("AI Insight:", log)


def perform_gravity_turn():
    target_alt = 100000
    turn_start = 100
    turn_end = 45000
    log_status("Starting gravity turn...")
    while True:
        alt = vessel.flight().mean_altitude
        apo = vessel.orbit.apoapsis_altitude
        log_status(f"Alt={alt:.0f}m, Apo={apo:.0f}m")
        if turn_start < alt < turn_end:
            frac = (alt - turn_start) / (turn_end - turn_start)
            pitch = max(0, 90 - frac * 45)
            vessel.auto_pilot.target_pitch_and_heading(pitch, 90)
            vessel.auto_pilot.engage()
            log_status(f"Pitch set to {pitch:.1f}")
        if apo >= target_alt * 0.9:
            vessel.control.throttle = 0.2
            log_status("Throttle reduced for cutoff.")
        if apo >= target_alt:
            vessel.control.throttle = 0
            log_status("Reached target apoapsis.")
            break
        time.sleep(1)
        adaptive_log("Gravity Turn:")


def circularize_at_apoapsis():
    log_status("Warping to apoapsis for circularization...")
    sc.warp_to(sc.ut + vessel.orbit.time_to_apoapsis - 5)
    vessel.control.sas_mode = sc.SASMode.prograde
    vessel.control.throttle = 1.0
    time.sleep(8)
    vessel.control.throttle = 0
    log_status("Circularization complete.")
    adaptive_log("Post-Circularization:")


def aim_for_munar_transfer():
    log_status("Aiming for Mun transfer... ")
    vessel.control.sas_mode = sc.SASMode.maneuver
    dir_vec = mun.position(vessel.orbit.reference_frame)
    mag = math.sqrt(sum(c*c for c in dir_vec))
    unit = [c/mag for c in dir_vec]
    vessel.auto_pilot.target_direction = unit
    vessel.auto_pilot.engage()
    adaptive_log("Mun Transfer Aim:")


def execute_trans_mun_injection():
    log_status("Executing trans-Munar injection burn...")
    vessel.control.sas_mode = sc.SASMode.prograde
    vessel.control.throttle = 1.0
    time.sleep(12)
    vessel.control.throttle = 0.5
    for _ in range(25):
        aim_for_munar_transfer()
        time.sleep(2)
    vessel.control.throttle = 0
    log_status("Trans-Munar injection complete.")
    adaptive_log("Injection Burn:")


def monitor_transfer_and_correct():
    log_status("Monitoring transfer trajectory and correcting course...")
    while vessel.orbit.body.name != 'Mun':
        aim_for_munar_transfer()
        fuel = get_fuel_percentage()
        if fuel < 5:
            log_status("Fuel low, holding trajectory...")
            break
        vessel.control.throttle = 0.25
        time.sleep(3)
        vessel.control.throttle = 0
        log_status(f"Course correction performed. Fuel={fuel:.1f}%")
        adaptive_log("Transfer Correction:")
        time.sleep(10)
    log_status("Entered Mun's sphere of influence.")


def circularize_at_mun():
    log_status("Circularizing around Mun...")
    vessel.control.sas_mode = sc.SASMode.prograde
    vessel.control.throttle = 1.0
    time.sleep(10)
    vessel.control.throttle = 0.2
    time.sleep(18)
    vessel.control.throttle = 0
    log_status("Munar orbit established.")
    adaptive_log("Munar Orbit:")

# --- Main Flow ---
vessel.control.throttle = 1.0
vessel.control.activate_next_stage()
perform_gravity_turn()
vessel.control.activate_next_stage()
circularize_at_apoapsis()

execute_trans_mun_injection()
monitor_transfer_and_correct()
circularize_at_mun()

log_text = ask_gpt2("KerbalBot completed lunar mission. Summary:")
print("AI Log:", log_text)