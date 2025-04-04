# run.py

import sys
from PyQt5.QtWidgets import QApplication
from app import MotionTrackingApp

def main():
    app = QApplication(sys.argv)
    window = MotionTrackingApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
