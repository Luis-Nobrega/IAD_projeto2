import sys
import cv2
import serial
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QSlider, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from picamera2 import Picamera2

try:
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
except serial.SerialException:
    print("Erro: não foi possível abrir a porta serial")
    ser = None

class MotionTrackingApp(QWidget):
    def __init__(self):
        super().__init__()

        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_still_configuration({"size": (640, 480)}))
        self.picam2.start()

        self.video_label = QLabel(self)
        self.toggle_button = QPushButton("Iniciar Rastreamento", self)
        self.toggle_button_calib = QPushButton("Iniciar Calibração", self)
        self.toggle_button.clicked.connect(self.toggle_tracking)
        self.toggle_button_calib.clicked.connect(self.toggle_calib)

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

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.toggle_button_calib)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.threshold_label)
        slider_layout.addWidget(self.threshold_slider)
        layout.addLayout(slider_layout)

        slider_layout2 = QHBoxLayout()
        slider_layout2.addWidget(self.distinction_label)
        slider_layout2.addWidget(self.distinction_slider)
        layout.addLayout(slider_layout2)

        self.fire_button = QPushButton("Disparar")
        self.fire_button.clicked.connect(self.trigger_fire)
        layout.addWidget(self.fire_button)

        self.motor_calib_button = QPushButton("Calibrar Motores", self)
        self.motor_calib_button.clicked.connect(self.calibrate_motors)
        layout.addWidget(self.motor_calib_button)

        self.yes_button = QPushButton("Diz que sim")
        self.no_button = QPushButton("Diz que não")
        self.mega_yes_button = QPushButton("Mega sim")
        self.mega_no_button = QPushButton("Mega não")

        self.yes_button.clicked.connect(lambda: self.perform_motion(axis='y', fast=False))
        self.no_button.clicked.connect(lambda: self.perform_motion(axis='x', fast=False))
        self.mega_yes_button.clicked.connect(lambda: self.perform_motion(axis='y', fast=True))
        self.mega_no_button.clicked.connect(lambda: self.perform_motion(axis='x', fast=True))

        layout.addWidget(self.yes_button)
        layout.addWidget(self.no_button)
        layout.addWidget(self.mega_yes_button)
        layout.addWidget(self.mega_no_button)

        manual_layout = QGridLayout()
        manual_label = QLabel("Controlo Manual dos Servos:")
        layout.addWidget(manual_label)

        self.up_button = QPushButton("⬆️")
        self.down_button = QPushButton("⬇️")
        self.left_button = QPushButton("⬅️")
        self.right_button = QPushButton("➡️")

        self.up_button.clicked.connect(lambda: self.send_commands("[0,1,0]"))
        self.down_button.clicked.connect(lambda: self.send_commands("[0,2,0]"))
        self.left_button.clicked.connect(lambda: self.send_commands("[2,0,0]"))
        self.right_button.clicked.connect(lambda: self.send_commands("[1,0,0]"))

        manual_layout.addWidget(self.up_button, 0, 1)
        manual_layout.addWidget(self.left_button, 1, 0)
        manual_layout.addWidget(self.right_button, 1, 2)
        manual_layout.addWidget(self.down_button, 2, 1)
        layout.addLayout(manual_layout)

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

        layout.addWidget(QLabel("Servo X (0-180):"))
        layout.addWidget(self.servo_x_slider)
        layout.addWidget(QLabel("Servo Y (0-180):"))
        layout.addWidget(self.servo_y_slider)

        self.setLayout(layout)

        self.tracking_enabled = False
        self.calib_enabled = False
        self.previous_frame = None
        self.threshold = 5
        self.distinction_threshold = 6000
        self.tracked_objects = {}
        self.object_persistence = {}
        self.max_lost_frames = 10
        self.tolerancia = 1

        self.pos_x = 0
        self.pos_y = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.read_serial_timer = QTimer()
        self.read_serial_timer.timeout.connect(self.read_serial_feedback)
        self.read_serial_timer.start(100)

        self.setWindowTitle("Rastreamento de Movimento")
        self.resize(640, 480)

    def perform_motion(self, axis='y', fast=False):
        delay = 100 if fast else 300
        repetitions = 3
        amplitude = 20
        base_val = self.servo_y_slider.value() if axis == 'y' else self.servo_x_slider.value()
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

    def update_servo_x(self):
        value = self.servo_x_slider.value()
        if ser:
            ser.write(f"SERVOX:{value}\n".encode())

    def update_servo_y(self):
        value = self.servo_y_slider.value()
        if ser:
            ser.write(f"SERVOY:{value}\n".encode())

    def read_serial_feedback(self):
        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8').strip()
                if line.startswith("POS:"):
                    _, x, y = line.split(":")
                    self.servo_x_slider.setValue(int(x))
                    self.servo_y_slider.setValue(int(y))
            except Exception as e:
                print(f"Erro ao ler da serial: {e}")

    def toggle_tracking(self):
        self.tracking_enabled = not self.tracking_enabled
        self.toggle_button.setText("Parar Rastreamento" if self.tracking_enabled else "Iniciar Rastreamento")

    def toggle_calib(self):
        self.calib_enabled = not self.calib_enabled
        self.toggle_button_calib.setText("Parar Calibração" if self.calib_enabled else "Iniciar Calibração")
        if self.calib_enabled:
            self.fim = 0
            self.x_ok = 0
            self.y_ok = 0
            self.calib_timer = QTimer()
            self.calib_timer.timeout.connect(self.calib_step)
            self.calib_timer.start(200)
        else:
            self.calib_timer.stop()

    def calibrate_motors(self):
        if ser:
            ser.write(b"CALIBRAR\n")

    def trigger_fire(self):
        self.update_frame(fire=True)

    def send_commands(self, lista):
        if ser:
            ser.write(f"{str(lista)}\n".encode())

    def update_threshold(self, value):
        self.threshold = value
        self.threshold_label.setText(f"Threshold: {value}")

    def update_distinction(self, value):
        self.distinction_threshold = value
        self.distinction_label.setText(f"Distinction: {value}")

    def detect_red_dot(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        lower_red1 = np.array([0,120,70])
        upper_red1 = np.array([10,255,255])
        lower_red2 = np.array([170,120,70])
        upper_red2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        center_x = x + w // 2
        center_y = y + h // 2
        return center_x, center_y

    def detect_motion_objects(self, previous_frame, current_frame):
        diff = cv2.absdiff(previous_frame, current_frame)
        _, motion_mask = cv2.threshold(diff, self.threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        new_objects = []
        for contour in contours:
            if cv2.contourArea(contour) > self.distinction_threshold:
                x, y, w, h = cv2.boundingRect(contour)
                center_x, center_y = x + w // 2, y + h // 2
                new_objects.append(((center_x, center_y), (x, y, w, h)))
        largest_contour = max(contours, key=cv2.contourArea) if contours else None
        return new_objects, motion_mask, largest_contour

    def update_frame(self, fire=False):
        frame = self.picam2.capture_array()
        if frame is None:
            return
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.tracking_enabled and self.previous_frame is not None:
            detected_objects, motion_mask, large = self.detect_motion_objects(self.previous_frame, gray_frame)
            if large is not None:
                self.follow_object(large, frame, fire)
        self.previous_frame = gray_frame.copy()
        q_image = self.convert_cv_qt(frame)
        self.video_label.setPixmap(q_image)

    def follow_object(self, large, frame, fire=False):
        altura, comprimento, _ = frame.shape
        center_frame_x = comprimento // 2
        center_frame_y = altura // 2
        if not self.pos_x and not self.pos_y:
            self.pos_x = center_frame_x
            self.pos_y = center_frame_y
        x, y, w, h = cv2.boundingRect(large)
        center_x, center_y = x + w // 2, y + h // 2
        if self.pos_x < center_x - self.tolerancia:
            self.send_commands("[1,0,0]")
        elif self.pos_x > center_x + self.tolerancia:
            self.send_commands("[2,0,0]")
        if self.pos_y < center_y - self.tolerancia:
            self.send_commands("[0,1,0]")
        elif self.pos_y > center_y + self.tolerancia:
            self.send_commands("[0,2,0]")
        elif self.pos_x == center_x and self.pos_y == center_y and fire:
            self.send_commands("[0,0,1]")

    def convert_cv_qt(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qt_image)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotionTrackingApp()
    window.show()
    sys.exit(app.exec())
