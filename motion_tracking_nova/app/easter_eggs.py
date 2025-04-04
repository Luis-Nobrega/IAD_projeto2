# app/easter_eggs.py

from .control import perform_motion_sequence

def play_motion(axis: str, base_val: int, fast: bool = False):
    delay = 100 if fast else 300
    repetitions = 3
    amplitude = 20
    perform_motion_sequence(axis, base_val, delay, repetitions, amplitude)
