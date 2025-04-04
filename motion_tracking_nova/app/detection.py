# app/detection.py

import cv2
import numpy as np

def detect_red_dot(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
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

def detect_motion_objects(previous_frame, current_frame, threshold, distinction_threshold):
    diff = cv2.absdiff(previous_frame, current_frame)
    _, motion_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    new_objects = []
    for contour in contours:
        if cv2.contourArea(contour) > distinction_threshold:
            x, y, w, h = cv2.boundingRect(contour)
            center_x, center_y = x + w // 2, y + h // 2
            new_objects.append(((center_x, center_y), (x, y, w, h)))

    largest_contour = max(contours, key=cv2.contourArea) if contours else None
    return new_objects, motion_mask, largest_contour
