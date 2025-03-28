import sys
import cv2
import serial
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QSlider, QHBoxLayout
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

        self.setWindowTitle("Rastreamento de Movimento")
        self.resize(640, 480)

    def calibrate_motors(self):
        """Envia comando para centralizar os servos."""
        if ser:
            print("Enviando comando de calibração dos motores...")
            ser.write(b"CALIBRAR\n")

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

    def calib_step(self):
        if self.fim:
            self.calib_timer.stop()
            self.toggle_button.setText("Iniciar Rastreamento")
            print("Calibração concluída")
            return

        frame = self.picam2.capture_array()
        altura, comprimento, _ = frame.shape
        center_frame_x = comprimento // 2
        center_frame_y = altura // 2

        cv2.line(frame, (center_frame_x, center_frame_y - 20), (center_frame_x, center_frame_y + 20), (0, 0, 0), 2)
        cv2.line(frame, (center_frame_x - 20, center_frame_y), (center_frame_x + 20, center_frame_y), (0, 0, 0), 2)

        q_image = self.convert_cv_qt(frame)
        self.video_label.setPixmap(q_image)

        self.pos_x, self.pos_y = self.detect_red_dot(frame)

        if self.pos_x is None or self.pos_y is None:
            print("Erro: Laser não encontrado!")
            return

        if self.pos_x < center_frame_x - self.tolerancia:
            self.send_commands("[1,0,0]")
        elif self.pos_x > center_frame_x + self.tolerancia:
            self.send_commands("[2,0,0]")
        else:
            self.x_ok = 1

        if self.pos_y < center_frame_y - self.tolerancia:
            self.send_commands("[0,1,0]")
        elif self.pos_y > center_frame_y + self.tolerancia:
            self.send_commands("[0,2,0]")
        else:
            self.y_ok = 1

        if self.x_ok and self.y_ok:
            self.fim = 1

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

        print(center_x, center_y)
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
            print("Erro: Frame não capturado!")
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
                print(f"Objeto {i+1}: x = {center[0]}, y = {center[1]}")

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
