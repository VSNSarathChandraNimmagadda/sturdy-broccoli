import sys
import cv2
import pyautogui
import mediapipe as mp
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap


class TruckGestureController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Truck Gesture Control")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = QLabel("Video Feed")
        self.video_label.setFixedSize(640, 480)

        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        self.start_button.clicked.connect(self.start_control)
        self.stop_button.clicked.connect(self.stop_control)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.gesture_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.hands = mp.solutions.hands.Hands(max_num_hands=1,
                                              min_detection_confidence=0.5,
                                              min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils
        self.finger_tips = [4, 8, 12, 16, 20]

        self.current_key = None
        self.last_action = None  # to prevent key spamming

    def start_control(self):
        self.timer.start(30)

    def stop_control(self):
        self.timer.stop()
        self.video_label.setText("Video Stopped")
        self.gesture_label.setText("Gesture: None")
        if self.current_key:
            pyautogui.keyUp(self.current_key)
            self.current_key = None

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        gesture = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                gesture = self.classify_gesture(hand_landmarks)
                self.perform_action(gesture)

        self.gesture_label.setText(f"Gesture: {gesture.upper() if gesture else 'None'}")
        img = QImage(rgb.data, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(img))

    def count_fingers(self, hand_landmarks):
        count = 0
        landmarks = hand_landmarks.landmark
        # Simple upward count (skip thumb)
        for tip_id in self.finger_tips[1:]:
            if landmarks[tip_id].y < landmarks[tip_id - 2].y:
                count += 1
        return count

    def classify_gesture(self, hand_landmarks):
        count = self.count_fingers(hand_landmarks)
        if count == 1:
            return "accelerate"
        elif count == 2:
            return "brake"
        elif count == 3:
            return "gear_drive"
        elif count == 4:
            return "gear_reverse"
        elif count == 5:
            return "pause"
        else:
            return None

    def perform_action(self, gesture):
        # Release previous key if necessary
        if self.current_key and gesture not in ["accelerate", "brake"]:
            pyautogui.keyUp(self.current_key)
            self.current_key = None

        if gesture == "accelerate":
            if self.current_key != "space":
                if self.current_key:
                    pyautogui.keyUp(self.current_key)
                pyautogui.keyDown("space")
                self.current_key = "space"

        elif gesture == "brake":
            if self.current_key != "b":
                if self.current_key:
                    pyautogui.keyUp(self.current_key)
                pyautogui.keyDown("b")
                self.current_key = "b"

        elif gesture == "gear_drive" and self.last_action != "gear_drive":
            pyautogui.press("d")
            self.last_action = "gear_drive"

        elif gesture == "gear_reverse" and self.last_action != "gear_reverse":
            pyautogui.press("r")
            self.last_action = "gear_reverse"

        elif gesture == "pause" and self.last_action != "pause":
            pyautogui.press("p")
            self.last_action = "pause"

        elif gesture is None:
            self.last_action = None
            if self.current_key:
                pyautogui.keyUp(self.current_key)
                self.current_key = None

    def closeEvent(self, event):
        self.cap.release()
        if self.current_key:
            pyautogui.keyUp(self.current_key)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TruckGestureController()
    window.show()
    sys.exit(app.exec_())
