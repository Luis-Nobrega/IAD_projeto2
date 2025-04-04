# app/control.py

import serial
from PyQt5.QtCore import QTimer

try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
except serial.SerialException:
    print("Erro: não foi possível abrir a porta serial")
    ser = None

# ========== BASIC SERIAL COMMANDS ==========

def send_commands(data):
    if ser:
        ser.write(f"{str(data)}\n".encode())

def update_servo(axis, value):
    if ser:
        ser.write(f"SERVO{axis.upper()}:{value}\n".encode())

def calibrate_motors():
    if ser:
        ser.write(b"CALIBRAR\n")

def trigger_fire_command():
    send_commands("[0,0,1]")

# ========== SERIAL FEEDBACK (POSITION FROM ARDUINO) ==========

def read_serial_feedback(callback_x, callback_y):
    if ser and ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("POS:"):
                _, x, y = line.split(":")
                callback_x(int(x))
                callback_y(int(y))
        except Exception as e:
            print(f"Erro ao ler da serial: {e}")

# ========== EASTER EGG MOVEMENT (YES/NO) ==========

def perform_motion_sequence(axis, base_val, delay, repetitions, amplitude):
    plus = min(180, base_val + amplitude)
    minus = max(0, base_val - amplitude)

    def sequence(i):
        if i >= repetitions:
            return
        if ser:
            if axis == 'y':
                ser.write(f"SERVOY:{plus}\n".encode())
                QTimer.singleShot(delay, lambda: ser.write(f"SERVOY:{minus}\n".encode()))
                QTimer.singleShot(2 * delay, lambda: ser.write(f"SERVOY:{base_val}\n".encode()))
            else:
                ser.write(f"SERVOX:{plus}\n".encode())
                QTimer.singleShot(delay, lambda: ser.write(f"SERVOX:{minus}\n".encode()))
                QTimer.singleShot(2 * delay, lambda: ser.write(f"SERVOX:{base_val}\n".encode()))
        QTimer.singleShot(3 * delay, lambda: sequence(i + 1))

    sequence(0)

# ========== GRADUAL SERVO MOVEMENT ==========

def move_servo_gradually(axis, current_val, target_val, step=2, delay=30):
    steps = []
    if target_val > current_val:
        steps = list(range(current_val, target_val + 1, step))
    else:
        steps = list(range(current_val, target_val - 1, -step))

    for i, val in enumerate(steps):
        QTimer.singleShot(i * delay, lambda v=val: update_servo(axis, v))

# ========== CALIBRATION LOOP STEP ==========

def start_calibration_step(camera, get_slider_vals, set_slider_vals, finish_callback, tolerancia=1, Kx=0.1, Ky=0.1):
    frame = camera.get_frame()
    if frame is None:
        return None, None, None

    altura, comprimento, _ = frame.shape
    center_x = comprimento // 2
    center_y = altura // 2

    from .detection import detect_red_dot
    pos_x, pos_y = detect_red_dot(frame)

    if pos_x is None or pos_y is None:
        print("Erro: laser não encontrado")
        return frame, pos_x, pos_y

    current_x, current_y = get_slider_vals()

    error_x = pos_x - center_x
    error_y = pos_y - center_y

    target_x = max(0, min(180, current_x + int(Kx * error_x)))
    target_y = max(0, min(180, current_y + int(Ky * error_y)))

    move_servo_gradually('x', current_x, target_x)
    move_servo_gradually('y', current_y, target_y)

    set_slider_vals(target_x, target_y)

    if abs(error_x) < tolerancia and abs(error_y) < tolerancia:
        finish_callback()

    return frame, pos_x, pos_y