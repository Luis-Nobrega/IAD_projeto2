from PyQt5.QtWidgets import QSlider, QLabel, QVBoxLayout, QGroupBox
from PyQt5.QtCore import Qt

def create_tracker_group(initial_value=3, callback=None):
    label = QLabel(f"Consistência: {initial_value}")
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(1)
    slider.setMaximum(10)
    slider.setValue(initial_value)

    if callback:
        slider.valueChanged.connect(callback)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(slider)

    group = QGroupBox("Rastreamento")
    group.setLayout(layout)

    return slider, label, group
