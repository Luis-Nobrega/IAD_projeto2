import sys
import cv2
import serial
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QSlider, QHBoxLayout, QGridLayout, QGroupBox, QSizePolicy, QScrollArea
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
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.toggle_button = QPushButton("Iniciar Rastreamento")
        self.toggle_button_calib = QPushButton("Iniciar Calibração")
        self.fire_button = QPushButton("Disparar")
        self.motor_calib_button = QPushButton("Calibrar Motores")

        self.toggle_button.clicked.connect(self.toggle_tracking)
        self.toggle_button_calib.clicked.connect(self.toggle_calib)
        self.fire_button.clicked.connect(self.trigger_fire)
        self.motor_calib_button.clicked.connect(self.calibrate_motors)

        self.servo_x_slider = QSlider(Qt.Horizontal)
        self.servo_x_slider.setRange(0, 180)
        self.servo_x_slider.setValue(90)
        self.servo_x_slider.sliderReleased.connect(self.update_servo_x)

        self.servo_y_slider = QSlider(Qt.Horizontal)
        self.servo_y_slider.setRange(0, 180)
        self.servo_y_slider.setValue(90)
        self.servo_y_slider.sliderReleased.connect(self.update_servo_y)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)

        control_layout = QVBoxLayout()
        control_layout.addWidget(self.toggle_button)
        control_layout.addWidget(self.toggle_button_calib)
        control_layout.addWidget(self.fire_button)
        control_layout.addWidget(self.motor_calib_button)
        control_layout.addWidget(QLabel("Servo X"))
        control_layout.addWidget(self.servo_x_slider)
        control_layout.addWidget(QLabel("Servo Y"))
        control_layout.addWidget(self.servo_y_slider)

        controls = QWidget()
        controls.setLayout(control_layout)

        h_layout = QHBoxLayout()
        h_layout.addLayout(layout, 3)
        h_layout.addWidget(controls, 1)

        self.setLayout(h_layout)

        self.setWindowTitle("Rastreamento de Movimento")
        self.resize(1000, 700)

        self.tracking_enabled = False
        self.calib_enabled = False
        self.previous_frame = None
        self.tolerancia = 1
        self.pos_x = 0
        self.pos_y = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.read_serial_timer = QTimer()
        self.read_serial_timer.timeout.connect(self.read_serial_feedback)
        self.read_serial_timer.start(100)

    def update_servo_x(self):
        value = self.servo_x_slider.value()
        if ser:
            ser.write(f"SERVOX:{value}\n".encode())

    def update_servo_y(self):
        value = self.servo_y_slider.value()
        if ser:
            ser.write(f"SERVOY:{value}\n".encode())

    def calibrate_motors(self):
        if ser:
            ser.write(b"CALIBRAR\n")

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
            self.calib_timer = QTimer()
            self.calib_timer.timeout.connect(self.calib_step)
            self.calib_timer.start(200)
        else:
            self.calib_timer.stop()

    def calib_step(self):
        if self.fim:
            self.calib_timer.stop()
            self.toggle_button_calib.setText("Iniciar Calibração")
            print("Calibração concluída")
            return

        frame = self.picam2.capture_array()
        altura, comprimento, _ = frame.shape
        center_frame_x = comprimento // 2
        center_frame_y = altura // 2

        self.pos_x, self.pos_y = self.detect_red_dot(frame)

        if self.pos_x is None or self.pos_y is None:
            print("Erro: Laser não encontrado!")
            return

        Kx = 0.1
        Ky = 0.1

        current_servo_x = self.servo_x_slider.value()
        current_servo_y = self.servo_y_slider.value()

        error_x = center_frame_x - self.pos_x
        error_y = center_frame_y - self.pos_y

        target_servo_x = current_servo_x + int(Kx * error_x)
        target_servo_y = current_servo_y + int(Ky * error_y)

        target_servo_x = max(0, min(180, target_servo_x))
        target_servo_y = max(0, min(180, target_servo_y))

        self.send_commands(f"SERVOX:{target_servo_x}")
        self.send_commands(f"SERVOY:{target_servo_y}")

        if abs(error_x) < self.tolerancia and abs(error_y) < self.tolerancia:
            self.fim = 1

    def send_commands(self, command):
        if ser:
            ser.write(f"{command}\n".encode())

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

    def update_frame(self, fire=False):
        frame = self.picam2.capture_array()
        if frame is None:
            return

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.tracking_enabled and self.previous_frame is not None:
            diff = cv2.absdiff(self.previous_frame, gray_frame)
            _, motion_mask = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                self.follow_object(largest, frame, fire)

        self.previous_frame = gray_frame.copy()
        q_image = self.convert_cv_qt(frame)
        self.video_label.setPixmap(q_image)

    def follow_object(self, large, frame, fire=False):
        altura, comprimento, _ = frame.shape
        center_frame_x = comprimento // 2
        center_frame_y = altura // 2

        if self.pos_x == 0 and self.pos_y == 0:
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
        elif abs(self.pos_x - center_x) <= self.tolerancia and abs(self.pos_y - center_y) <= self.tolerancia and fire:
            self.send_commands("[0,0,1]")

    def trigger_fire(self):
        self.update_frame(fire=True)

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
