import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QSlider,
    QHBoxLayout, QGridLayout, QGroupBox, QSizePolicy, QScrollArea
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt, QElapsedTimer

from .camera import CameraManager
from .detection import detect_red_dot, detect_motion_objects
from .control import (
    send_commands, update_servo, calibrate_motors,
    read_serial_feedback, perform_motion_sequence,
    start_calibration_step, trigger_fire_command
)
from .easter_eggs import play_motion

class MotionTrackingApp(QWidget):
    def __init__(self):
        super().__init__()

        self.camera = CameraManager()
        self.manual_override_timer = QElapsedTimer()

        self.video_label = QLabel(self)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.toggle_button = QPushButton("Iniciar Rastreamento")
        self.toggle_button.clicked.connect(self.toggle_tracking)

        self.fire_button = QPushButton("Disparar")
        self.fire_button.clicked.connect(self.trigger_fire)

        self.calib_button = QPushButton("Iniciar Calibração")
        self.calib_button.setCheckable(True)
        self.calib_button.clicked.connect(self.toggle_calibration)

        self.servo_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.servo_x_slider.setMinimum(0)
        self.servo_x_slider.setMaximum(180)
        self.servo_x_slider.setValue(90)
        self.servo_x_slider.sliderReleased.connect(self.on_servo_x_release)

        self.servo_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.servo_y_slider.setMinimum(0)
        self.servo_y_slider.setMaximum(180)
        self.servo_y_slider.setValue(90)
        self.servo_y_slider.sliderReleased.connect(self.on_servo_y_release)

        self.yes_button = QPushButton("Diz que sim")
        self.no_button = QPushButton("Diz que não")
        self.mega_yes_button = QPushButton("Mega sim")
        self.mega_no_button = QPushButton("Mega não")

        self.yes_button.clicked.connect(lambda: play_motion('y', self.servo_y_slider.value(), fast=False))
        self.no_button.clicked.connect(lambda: play_motion('x', self.servo_x_slider.value(), fast=False))
        self.mega_yes_button.clicked.connect(lambda: play_motion('y', self.servo_y_slider.value(), fast=True))
        self.mega_no_button.clicked.connect(lambda: play_motion('x', self.servo_x_slider.value(), fast=True))

        self.threshold = 5
        self.distinction_threshold = 6000
        self.tolerancia = 1
        self.previous_frame = None
        self.tracking_enabled = False
        self.calibrating = False

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.fire_button)
        layout.addWidget(self.calib_button)

        servo_group = QGroupBox("Servos")
        servo_layout = QVBoxLayout()
        servo_layout.addWidget(QLabel("Servo X"))
        servo_layout.addWidget(self.servo_x_slider)
        servo_layout.addWidget(QLabel("Servo Y"))
        servo_layout.addWidget(self.servo_y_slider)
        servo_group.setLayout(servo_layout)
        layout.addWidget(servo_group)

        easter_group = QGroupBox("Easter Eggs")
        easter_layout = QVBoxLayout()
        easter_layout.addWidget(self.yes_button)
        easter_layout.addWidget(self.no_button)
        easter_layout.addWidget(self.mega_yes_button)
        easter_layout.addWidget(self.mega_no_button)
        easter_group.setLayout(easter_layout)
        layout.addWidget(easter_group)

        self.setLayout(layout)
        self.setWindowTitle("Rastreamento de Movimento")
        self.resize(800, 700)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.calib_timer = QTimer()
        self.calib_timer.timeout.connect(self.calibration_loop)

        self.feedback_timer = QTimer()
        self.feedback_timer.timeout.connect(self.sync_sliders_with_arduino)
        self.feedback_timer.start(100)

    def toggle_tracking(self):
        self.tracking_enabled = not self.tracking_enabled
        self.toggle_button.setText(
            "Parar Rastreamento" if self.tracking_enabled else "Iniciar Rastreamento"
        )

    def trigger_fire(self):
        trigger_fire_command()

    def on_servo_x_release(self):
        update_servo('x', self.servo_x_slider.value())
        self.manual_override_timer.start()

    def on_servo_y_release(self):
        update_servo('y', self.servo_y_slider.value())
        self.manual_override_timer.start()

    def toggle_calibration(self, checked):
        if checked:
            self.calibrating = True
            self.calib_button.setText("Parar Calibração")
            self.calib_timer.start(200)
        else:
            self.calibrating = False
            self.calib_button.setText("Iniciar Calibração")
            self.calib_timer.stop()

    def calibration_loop(self):
        def get_vals():
            return self.servo_x_slider.value(), self.servo_y_slider.value()

        def set_vals(x, y):
            self.servo_x_slider.setValue(x)
            self.servo_y_slider.setValue(y)

        def finish():
            self.calib_button.setChecked(False)
            self.toggle_calibration(False)

        frame, pos_x, pos_y = start_calibration_step(
            camera=self.camera,
            get_slider_vals=get_vals,
            set_slider_vals=set_vals,
            finish_callback=finish,
            tolerancia=self.tolerancia
        )

        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(img))

    def sync_sliders_with_arduino(self):
        if self.manual_override_timer.isValid() and self.manual_override_timer.elapsed() < 300:
            return  # skip update if within 300ms of manual override

        def set_x(val): self.servo_x_slider.setValue(val)
        def set_y(val): self.servo_y_slider.setValue(val)
        read_serial_feedback(set_x, set_y)

    def follow_object(self, bbox):
        x, y, w, h = bbox
        center_x = x + w // 2
        center_y = y + h // 2

        frame_h, frame_w = self.previous_frame.shape
        mid_x = frame_w // 2
        mid_y = frame_h // 2

        tol = self.tolerancia

        if center_x < mid_x - tol:
            send_commands("[2,0,0]")  # esquerda
        elif center_x > mid_x + tol:
            send_commands("[1,0,0]")  # direita

        if center_y < mid_y - tol:
            send_commands("[0,1,0]")  # cima
        elif center_y > mid_y + tol:
            send_commands("[0,2,0]")  # baixo

    def update_frame(self):
        frame = self.camera.get_frame()
        if frame is None:
            return

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.tracking_enabled and self.previous_frame is not None:
            detected_objects, motion_mask, large = detect_motion_objects(
                self.previous_frame, gray_frame,
                self.threshold, self.distinction_threshold
            )

            colors = [(0, 0, 255), (255, 0, 0), (0, 255, 255), (255, 0, 255)]

            for i, (center, bbox) in enumerate(detected_objects):
                color = colors[i % len(colors)]
                cv2.circle(frame, center, 5, color, -1)
                x, y, w, h = bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"Objeto {i+1}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            frame[motion_mask > 0] = (0, 255, 0)

            if large:
                self.follow_object(large)

        self.previous_frame = gray_frame.copy()
        self.video_label.setPixmap(self.camera.to_qt_image(frame))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotionTrackingApp()
    window.show()
    sys.exit(app.exec())