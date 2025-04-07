import sys
import cv2
import serial
import math
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QPushButton, QVBoxLayout, QSlider, QHBoxLayout, QGridLayout, QGroupBox, QSizePolicy, QScrollArea
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from picamera2 import Picamera2
from time import time

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
        #self.toggle_button_calib = QPushButton("Iniciar Calibração") ###############################
        self.fire_button = QPushButton("Disparar")
        self.motor_calib_button = QPushButton("Calibrar Motores")
        
        # --- Novo widget para definir a distância horizontal ---
        #self.distance_input = QLineEdit("100")
        #self.set_distance_button = QPushButton("Set Horizontal Distance")
        #self.set_distance_button.clicked.connect(self.set_horizontal_distance)
        # Variável para armazenar a distância horizontal definida (default = 100)
        #self.horizontal_distance = 100

        self.toggle_button.clicked.connect(self.toggle_tracking)
        #self.toggle_button_calib.clicked.connect(self.toggle_calib) ###############################
        self.vertical_pixel_offset = 0

        self.fire_button.clicked.connect(self.trigger_fire)
        self.motor_calib_button.clicked.connect(self.calibrate_motors)

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

        self.yes_button = QPushButton("Diz que sim")
        self.no_button = QPushButton("Diz que não")
        self.mega_yes_button = QPushButton("Mega sim")
        self.mega_no_button = QPushButton("Mega não")

        self.yes_button.clicked.connect(lambda: self.perform_motion(axis='y', fast=False))
        self.no_button.clicked.connect(lambda: self.perform_motion(axis='x', fast=False))
        self.mega_yes_button.clicked.connect(lambda: self.perform_motion(axis='y', fast=True))
        self.mega_no_button.clicked.connect(lambda: self.perform_motion(axis='x', fast=True))

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

        right_layout = QVBoxLayout()
        right_layout.addWidget(ctrl_group)
        right_layout.addWidget(threshold_group)
        right_layout.addWidget(manual_group)
        right_layout.addLayout(servo_layout)
        right_layout.addWidget(easter_group)

        right_container = QWidget()
        right_container.setLayout(right_layout)
        right_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(right_container)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.video_label, 3)
        main_layout.addWidget(scroll, 2)

        self.setLayout(main_layout)

        self.setWindowTitle("Rastreamento de Movimento")
        self.resize(1000, 700)

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

    """def set_horizontal_distance(self): #####################################################
        try:
            value = int(self.distance_input.text())
            self.horizontal_distance = value
            print(f"Distância horizontal em cm definida para: {self.horizontal_distance}")
        except ValueError:
            print("Valor inválido para a distância!")"""

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

    def calibrate_motors(self):
        if ser:
            ser.write(b"CALIBRAR\n")

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

    """def toggle_calib(self):
        self.calib_enabled = not self.calib_enabled
        self.toggle_button_calib.setText("Parar Calibração" if self.calib_enabled else "Iniciar Calibração")

        if self.calib_enabled:
            self.vertical_errors = []
            self.calib_start_time = time.time()
            self.calib_timer = QTimer()
            self.calib_timer.timeout.connect(self.calib_step)
            self.calib_timer.start(200)  # A cada 200ms → ~5 leituras por segundo
        else:
            self.calib_timer.stop()

    def calib_step(self):
        frame = self.picam2.capture_array()
        if frame is None:
            print("Erro: Frame não capturado!")
            return

        altura, comprimento, _ = frame.shape
        center_frame_y = altura // 2

        _, pos_y = self.detect_red_dot(frame)
        if pos_y is None:
            print("Erro: Laser não encontrado!")
            return

        erro_y = center_frame_y - pos_y
        self.vertical_errors.append(erro_y)

        elapsed_time = time.time() - self.calib_start_time
        print(f"[{len(self.vertical_errors)}] Erro vertical: {erro_y} | Tempo: {elapsed_time:.1f}s")

        if elapsed_time >= 5:  # Parar após 5 segundos
            if self.vertical_errors:
                media_erro = sum(self.vertical_errors) / len(self.vertical_errors)
                self.vertical_pixel_offset = int(media_erro)
                print(f"Calibração concluída! Offset vertical médio: {self.vertical_pixel_offset}")
            else:
                self.vertical_pixel_offset = 0
                print("Nenhum dado válido coletado.")
            
            self.calib_timer.stop()
            self.toggle_button_calib.setText("Iniciar Calibração")"""



    def send_commands(self, lista):
        if ser:
            ser.write(f"{str(lista)}\n".encode())

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

        cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
        cv2.putText(frame, f"({center_x}, {center_y})", (center_x + 10, center_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return center_x, center_y

    def update_threshold(self, value):
        self.threshold = value
        self.threshold_label.setText(f"Threshold: {value}")

    def update_distinction(self, value):
        self.distinction_threshold = value
        self.distinction_label.setText(f"Distinction: {value}")

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
            colors = [(0, 0, 255), (255, 0, 0), (0, 255, 255), (255, 0, 255)]

            for i, (center, bbox) in enumerate(detected_objects):
                color = colors[i % len(colors)]
                cv2.circle(frame, center, 5, color, -1)
                x, y, w, h = bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"Objeto {i+1}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            frame[motion_mask > 0] = (0, 255, 0)
            if large is not None:
                self.follow_object(large, frame, fire)

        self.previous_frame = gray_frame.copy()
        q_image = self.convert_cv_qt(frame)
        self.video_label.setPixmap(q_image)

    def follow_object(self, large, frame, fire=False):
        altura, comprimento, _ = frame.shape
        center_frame_x = comprimento // 2
        center_frame_y = altura // 2

        # Obtém o centro do objeto detectado
        x, y, w, h = cv2.boundingRect(large)
        center_x, center_y = x + w // 2, y + h // 2

        # Cálculo do ângulo horizontal:
        # FOV horizontal = 120° → ângulo por pixel:
        fov_horizontal = 120.0  # metade do FOV horizontal
        angle_per_pixel = fov_horizontal / comprimento
        error_x = center_frame_x - center_x  # erro em pixels
        angle_x = round(error_x * angle_per_pixel)  # ângulo horizontal correspondente
        angle_x = 90 + angle_x


        error_y = center_frame_y - center_y  # erro em pixels
        angle_y = round(error_y * angle_per_pixel)  # ângulo horizontal correspondente
        angle_y = 90 + angle_y

        fire_value = 1 if fire else 0

        # Envia o comando com os ângulos calculados (exemplo de protocolo)
        command_str = f"[{angle_x},{angle_y},{fire_value}]"
        self.send_commands(command_str)


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
    