# app/camera.py

import cv2
from picamera2 import Picamera2
from PyQt5.QtGui import QImage, QPixmap

class CameraManager:
    def __init__(self, resolution=(640, 480)):
        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_still_configuration({"size": resolution})
        )
        self.picam2.start()

    def get_frame(self):
        try:
            return self.picam2.capture_array()
        except Exception as e:
            print(f"Erro ao capturar frame: {e}")
            return None

    def to_qt_image(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qt_image)
