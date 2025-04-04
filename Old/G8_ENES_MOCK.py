import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QSlider, QHBoxLayout, QGridLayout, QGroupBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

ser = None  # Serial is mocked

class MotionTrackingApp(QWidget):
    def __init__(self):
        super().__init__()

        self.video_label = QLabel("Preview do vídeo (simulado)")
        self.video_label.setStyleSheet("background-color: black; color: white; padding: 10px;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Control Buttons
        self.toggle_button = QPushButton("Iniciar Rastreamento")
        self.toggle_button_calib = QPushButton("Iniciar Calibração")
        self.fire_button = QPushButton("Disparar")
        self.motor_calib_button = QPushButton("Calibrar Motores")

        self.toggle_button.clicked.connect(self.toggle_tracking)
        self.toggle_button_calib.clicked.connect(self.toggle_calib)
        self.fire_button.clicked.connect(self.trigger_fire)
        self.motor_calib_button.clicked.connect(self.calibrate_motors)

        # Tracking Threshold Sliders
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(1)
        self.threshold_slider.setMaximum(200)
        self.threshold_slider.setValue(5)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.valueChanged.connect(self.update_threshold)

        self.distinction_slider = QSlider(Qt.Orientation.Horizontal)
        self.distinction_slider.setMinimum(10)
        self.distinction_slider.setMaximum(10000)
        self.distinction_slider.setValue(6000)
        self.distinction_slider.setTickInterval(10)
        self.distinction_slider.valueChanged.connect(self.update_distinction)

        self.threshold_label = QLabel(f"Threshold: {self.threshold_slider.value()}")
        self.distinction_label = QLabel(f"Distinction: {self.distinction_slider.value()}")

        # Manual Controls
        self.up_button = QPushButton("⬆️")
        self.down_button = QPushButton("⬇️")
        self.left_button = QPushButton("⬅️")
        self.right_button = QPushButton("➡️")

        self.up_button.clicked.connect(lambda: self.send_commands("[0,1,0]"))
        self.down_button.clicked.connect(lambda: self.send_commands("[0,2,0]"))
        self.left_button.clicked.connect(lambda: self.send_commands("[2,0,0]"))
        self.right_button.clicked.connect(lambda: self.send_commands("[1,0,0]"))

        self.servo_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.servo_x_slider.setMinimum(0)
        self.servo_x_slider.setMaximum(180)
        self.servo_x_slider.setValue(90)
        self.servo_x_slider.setTickInterval(10)
        self.servo_x_slider.sliderReleased.connect(self.update_servo_x)

        self.servo_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.servo_y_slider.setMinimum(0)
        self.servo_y_slider.setMaximum(180)
        self.servo_y_slider.setValue(90)
        self.servo_y_slider.setTickInterval(10)
        self.servo_y_slider.sliderReleased.connect(self.update_servo_y)

        # Easter Egg Buttons
        self.yes_button = QPushButton("Diz que sim")
        self.no_button = QPushButton("Diz que não")
        self.mega_yes_button = QPushButton("Mega sim")
        self.mega_no_button = QPushButton("Mega não")

        self.yes_button.clicked.connect(lambda: self.perform_motion(axis='y', fast=False))
        self.no_button.clicked.connect(lambda: self.perform_motion(axis='x', fast=False))
        self.mega_yes_button.clicked.connect(lambda: self.perform_motion(axis='y', fast=True))
        self.mega_no_button.clicked.connect(lambda: self.perform_motion(axis='x', fast=True))

        # Layout Assembly
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)

        ctrl_group = QGroupBox("Controlo Principal")
        ctrl_layout = QVBoxLayout()
        ctrl_layout.addWidget(self.toggle_button)
        ctrl_layout.addWidget(self.toggle_button_calib)
        ctrl_layout.addWidget(self.fire_button)
        ctrl_layout.addWidget(self.motor_calib_button)
        ctrl_group.setLayout(ctrl_layout)

        threshold_group = QGroupBox("Parâmetros de Rastreamento")
        threshold_layout = QVBoxLayout()
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.distinction_label)
        threshold_layout.addWidget(self.distinction_slider)
        threshold_group.setLayout(threshold_layout)

        manual_group = QGroupBox("Controlo Manual dos Servos")
        manual_layout = QGridLayout()
        manual_layout.addWidget(self.up_button, 0, 1)
        manual_layout.addWidget(self.left_button, 1, 0)
        manual_layout.addWidget(self.right_button, 1, 2)
        manual_layout.addWidget(self.down_button, 2, 1)
        manual_group.setLayout(manual_layout)

        servo_layout = QVBoxLayout()
        servo_layout.addWidget(QLabel("Servo X (0-180):"))
        servo_layout.addWidget(self.servo_x_slider)
        servo_layout.addWidget(QLabel("Servo Y (0-180):"))
        servo_layout.addWidget(self.servo_y_slider)

        easter_group = QGroupBox("Easter Eggs")
        easter_layout = QVBoxLayout()
        easter_layout.addWidget(self.yes_button)
        easter_layout.addWidget(self.no_button)
        easter_layout.addWidget(self.mega_yes_button)
        easter_layout.addWidget(self.mega_no_button)
        easter_group.setLayout(easter_layout)

        layout.addWidget(ctrl_group)
        layout.addWidget(threshold_group)
        layout.addWidget(manual_group)
        layout.addLayout(servo_layout)
        layout.addWidget(easter_group)

        self.setLayout(layout)
        self.setWindowTitle("Simulação da Interface de Rastreamento")
        self.resize(700, 700)

    def perform_motion(self, axis='y', fast=False):
        print(f"Simulando movimento '{'sim' if axis == 'y' else 'não'}' com velocidade {'alta' if fast else 'normal'}")

    def calibrate_motors(self):
        print("Simulando calibração dos motores")

    def update_servo_x(self):
        value = self.servo_x_slider.value()
        print(f"Simulando envio de SERVOX:{value}")

    def update_servo_y(self):
        value = self.servo_y_slider.value()
        print(f"Simulando envio de SERVOY:{value}")

    def update_threshold(self, value):
        self.threshold_label.setText(f"Threshold: {value}")

    def update_distinction(self, value):
        self.distinction_label.setText(f"Distinction: {value}")

    def toggle_tracking(self):
        print("Simulando início/fim do rastreamento")

    def toggle_calib(self):
        print("Simulando início/fim da calibração")

    def trigger_fire(self):
        print("Simulando disparo")

    def send_commands(self, lista):
        print(f"Simulando comando: {lista}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotionTrackingApp()
    window.show()
    sys.exit(app.exec())
