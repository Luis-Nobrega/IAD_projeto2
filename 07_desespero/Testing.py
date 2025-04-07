import sys
import cv2
import serial
import numpy as np
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, 
                            QVBoxLayout, QSlider, QHBoxLayout, QGridLayout, 
                            QGroupBox, QSizePolicy, QScrollArea)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from picamera2 import Picamera2

class SerialWrapper:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            print(f"Connected to {port}")
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
    
    def write(self, data):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(data)
                return True
            except serial.SerialException:
                return False
        return False
    
    def readline(self):
        if self.ser and self.ser.in_waiting:
            try:
                return self.ser.readline().decode('utf-8').strip()
            except:
                return None
        return None
    
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

ser = SerialWrapper()

class MotionTrackingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_camera()
        self.setup_variables()
        self.setup_timers()

    def setup_ui(self):
         # Main window setup
        self.setWindowTitle("Motion Tracking System")
        self.resize(1200, 800)
        
        # Video display
        self.video_label = QLabel(self)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        
        # Control buttons
        self.toggle_button = QPushButton("Start Tracking")
        self.toggle_button_calib = QPushButton("Calibrate")
        self.fire_button = QPushButton("FIRE")
        self.motor_calib_button = QPushButton("Motor Calibration")
        
        # Button styling
        button_style = """
            QPushButton {
                padding: 8px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton#fire_button {
                background-color: #ff4444;
                color: white;
            }
        """
        self.fire_button.setObjectName("fire_button")
        self.setStyleSheet(button_style)
        
        # Connect buttons
        self.toggle_button.clicked.connect(self.toggle_tracking)
        self.toggle_button_calib.clicked.connect(self.toggle_calibration)
        self.fire_button.clicked.connect(self.trigger_fire)
        #self.motor_calib_button.clicked.connect(self.calibrate_motors)
        
        # Threshold controls
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(1, 100)
        self.threshold_slider.setValue(20)
        self.threshold_label = QLabel(f"Motion Threshold: {self.threshold_slider.value()}")
        
        # Object size controls
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(100, 10000)
        self.size_slider.setValue(3000)
        self.size_label = QLabel(f"Min Object Size: {self.size_slider.value()} px")
        
        # Manual control buttons
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        
        # Button size policy
        for btn in [self.up_button, self.down_button, self.left_button, self.right_button]:
            btn.setFixedSize(50, 50)
        
        # Connect manual controls
        self.up_button.clicked.connect(lambda: self.send_commands("[0,1,5]"))
        self.down_button.clicked.connect(lambda: self.send_commands("[0,2,5]"))
        self.left_button.clicked.connect(lambda: self.send_commands("[2,0,5]"))
        self.right_button.clicked.connect(lambda: self.send_commands("[1,0,5]"))
        
        # Create control groups
        ctrl_group = QGroupBox("Main Controls")
        ctrl_layout = QVBoxLayout()
        ctrl_layout.addWidget(self.toggle_button)
        ctrl_layout.addWidget(self.toggle_button_calib)
        ctrl_layout.addWidget(self.fire_button)
        ctrl_layout.addWidget(self.motor_calib_button)
        ctrl_group.setLayout(ctrl_layout)
        
        threshold_group = QGroupBox("Tracking Parameters")
        threshold_layout = QVBoxLayout()
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.size_label)
        threshold_layout.addWidget(self.size_slider)
        threshold_group.setLayout(threshold_layout)
        
        manual_group = QGroupBox("Manual Control")
        manual_layout = QGridLayout()
        manual_layout.addWidget(self.up_button, 0, 1)
        manual_layout.addWidget(self.left_button, 1, 0)
        manual_layout.addWidget(self.right_button, 1, 2)
        manual_layout.addWidget(self.down_button, 2, 1)
        manual_group.setLayout(manual_layout)
        
        # Modified servo layout with center markers
        servo_layout = QVBoxLayout()
        servo_layout.addWidget(QLabel("Servo X (30-150°):"))
        self.servo_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.servo_x_slider.setRange(30, 150)
        self.servo_x_slider.setValue(90)
        servo_layout.addWidget(self.servo_x_slider)
        
        servo_layout.addWidget(QLabel("Servo Y (30-150°):"))
        self.servo_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.servo_y_slider.setRange(30, 150)
        self.servo_y_slider.setValue(90)
        servo_layout.addWidget(self.servo_y_slider)
        
        # Easter egg buttons
        self.easter_group = QGroupBox("Special Functions")
        easter_layout = QVBoxLayout()
        
        self.yes_button = QPushButton("Nod (Yes)")
        self.no_button = QPushButton("Shake (No)")
        self.mega_yes_button = QPushButton("Excited Yes!")
        self.mega_no_button = QPushButton("Angry No!")
        
        # Connect easter eggs
        self.yes_button.clicked.connect(lambda: self.perform_motion('y', False))
        self.no_button.clicked.connect(lambda: self.perform_motion('x', False))
        self.mega_yes_button.clicked.connect(lambda: self.perform_motion('y', True))
        self.mega_no_button.clicked.connect(lambda: self.perform_motion('x', True))
        
        easter_layout.addWidget(self.yes_button)
        easter_layout.addWidget(self.no_button)
        easter_layout.addWidget(self.mega_yes_button)
        easter_layout.addWidget(self.mega_no_button)
        self.easter_group.setLayout(easter_layout)
        
        # Right side panel layout
        right_layout = QVBoxLayout()
        right_layout.addWidget(ctrl_group)
        right_layout.addWidget(threshold_group)
        right_layout.addWidget(manual_group)
        right_layout.addLayout(servo_layout)  # This is where servo controls were added
        right_layout.addWidget(self.easter_group)
        right_layout.addStretch()
        
        # Scroll area for controls
        right_container = QWidget()
        right_container.setLayout(right_layout)
        
        scroll = QScrollArea()
        scroll.setWidget(right_container)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(350)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.video_label, 4)  # 80% space for video
        main_layout.addWidget(scroll, 1)            # 20% space for controls
        self.setLayout(main_layout)

    def setup_camera(self):
        self.picam2 = Picamera2()
        try:
            config = self.picam2.create_still_configuration(
                main={"size": (640, 480)},
                transform=Qt.Horizontal)
            self.picam2.configure(config)
            self.picam2.start()
        except Exception as e:
            print(f"Camera error: {e}")
            #self.show_error_message("Camera initialization failed")

    def setup_variables(self):
        self.tracking_enabled = False
        self.calib_enabled = False
        self.previous_frame = None
        self.threshold = 20  # Increased default threshold
        self.distinction_threshold = 6000
        self.tolerancia = 10  # Increased tolerance
        self.pos_x = 90
        self.pos_y = 90
        self.servo_limits = {
            'x': (30, 150),
            'y': (30, 150)
        }
        self.k_p = 0.5  # Proportional gain
        self.k_i = 0.01  # Integral gain
        self.k_d = 0.1  # Derivative gain
        self.prev_error_x = 0
        self.prev_error_y = 0
        self.integral_x = 0
        self.integral_y = 0

    def setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)  # Reduced frame rate for stability
        
        self.serial_timer = QTimer()
        self.serial_timer.timeout.connect(self.read_serial_feedback)
        self.serial_timer.start(100)

    def follow_object(self, large, frame, fire=False):
        try:
            x, y, w, h = cv2.boundingRect(large)
            obj_center_x = x + w // 2
            obj_center_y = y + h // 2
            
            frame_center_x = frame.shape[1] // 2
            frame_center_y = frame.shape[0] // 2
            
            # Calculate errors
            error_x = obj_center_x - frame_center_x
            error_y = obj_center_y - frame_center_y
            
            # PID control for X axis
            self.integral_x += error_x
            derivative_x = error_x - self.prev_error_x
            output_x = self.k_p * error_x + self.k_i * self.integral_x + self.k_d * derivative_x
            self.prev_error_x = error_x
            
            # PID control for Y axis (INVERTED because camera Y increases downward)
            self.integral_y += error_y
            derivative_y = error_y - self.prev_error_y
            output_y = -(self.k_p * error_y + self.k_i * self.integral_y + self.k_d * derivative_y)
            self.prev_error_y = error_y
            
            # Apply movement
            if abs(error_x) > self.tolerancia:
                direction_x = 1 if output_x > 0 else 2
                steps_x = min(int(abs(output_x)), 10)  # Limit max steps
                self.send_commands(f"[{direction_x},{steps_x},0]")
            
            if abs(error_y) > self.tolerancia:
                direction_y = 1 if output_y > 0 else 2  # Note: Corrected direction
                steps_y = min(int(abs(output_y)), 10)  # Limit max steps
                self.send_commands(f"[0,{direction_y},{steps_y}]")
            
            if fire and abs(error_x) <= self.tolerancia and abs(error_y) <= self.tolerancia:
                self.send_commands("[0,0,1]")
                
            # Draw debug info
            cv2.line(frame, (frame_center_x-20, frame_center_y), (frame_center_x+20, frame_center_y), (0,255,0), 1)
            cv2.line(frame, (frame_center_x, frame_center_y-20), (frame_center_x, frame_center_y+20), (0,255,0), 1)
            cv2.putText(frame, f"Xerr:{error_x:.1f}", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            cv2.putText(frame, f"Yerr:{error_y:.1f}", (10, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
            
        except Exception as e:
            print(f"Tracking error: {e}")

    def send_commands(self, command):
        if not ser.write(f"{command}\n".encode()):
            print("Failed to send command to Arduino")

    def toggle_tracking(self):
        try:
            self.tracking_enabled = not self.tracking_enabled
            self.toggle_button.setText("Stop Tracking" if self.tracking_enabled else "Start Tracking")
            if self.tracking_enabled:
                self.prev_frame = None
        except Exception as e:
            print(f"Error toggling tracking: {e}")
            self.tracking_enabled = False
            self.toggle_button.setText("Start Tracking")

    def toggle_calibration(self):
        try:
            self.calib_enabled = not self.calib_enabled
            self.toggle_button_calib.setText("Stop Calibration" if self.calib_enabled else "Start Calibration")
            
            if self.calib_enabled:
                self.calib_step = 0
                self.calib_timer = QTimer()
                self.calib_timer.timeout.connect(self.run_calibration)
                self.calib_timer.start(200)
            else:
                if hasattr(self, 'calib_timer'):
                    self.calib_timer.stop()
        except Exception as e:
            print(f"Calibration error: {e}")
            self.calib_enabled = False
            self.toggle_button_calib.setText("Start Calibration")

    def trigger_fire(self):
        try:
            if ser and ser.write(b"[0,0,1]\n"):
                self.fire_button.setStyleSheet("background-color: #aa0000;")
                QTimer.singleShot(500, lambda: self.fire_button.setStyleSheet("background-color: #ff4444;"))
        except Exception as e:
            print(f"Fire command failed: {e}")

    def send_commands(self, command):
        try:
            if ser and ser.write(f"{command}\n".encode()):
                return True
            return False
        except Exception as e:
            print(f"Command send failed: {e}")
            return False

    def perform_motion(self, axis, fast=False):
        try:
            delay = 100 if fast else 300
            repetitions = 3
            amplitude = 20
            
            base_val = self.servo_y_slider.value() if axis == 'y' else self.servo_x_slider.value()
            plus = min(180, base_val + amplitude)
            minus = max(0, base_val - amplitude)

            def sequence(i):
                if i >= repetitions:
                    return
                if axis == 'y':
                    self.send_commands(f"SERVOY:{plus}\n")
                    QTimer.singleShot(delay, lambda: self.send_commands(f"SERVOY:{minus}\n"))
                else:
                    self.send_commands(f"SERVOX:{plus}\n")
                    QTimer.singleShot(delay, lambda: self.send_commands(f"SERVOX:{minus}\n"))
                QTimer.singleShot(2*delay, lambda: self.send_commands(
                    f"SERVO{'Y' if axis == 'y' else 'X'}:{base_val}\n"))
                QTimer.singleShot(3*delay, lambda: sequence(i+1))

            sequence(0)
        except Exception as e:
            print(f"Motion sequence failed: {e}")

    def read_serial_feedback(self):
        try:
            if ser and ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("POS:"):
                    _, x, y = line.split(":")
                    self.servo_x_slider.setValue(int(x))
                    self.servo_y_slider.setValue(int(y))
                    self.pos_x = int(x)
                    self.pos_y = int(y)
        except Exception as e:
            print(f"Serial read error: {e}")
    
    def closeEvent(self, event):
        self.timer.stop()
        self.serial_timer.stop()
        if self.picam2:
            self.picam2.stop()
        ser.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        window = MotionTrackingApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error: {e}")
        ser.close()