import sys
import cv2
import time
import pyautogui
import mediapipe as mp
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
class GestureControlApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subway Surfers Gesture Controller")
        self.setGeometry(100, 100, 800, 600)
        self.video_label = QLabel("Video Feed")
        self.video_label.setFixedSize(640, 480)
        self.gesture_label = QLabel("Gesture: None")
        self.gesture_label.setAlignment(Qt.AlignCenter)
        self.start_button = QPushButton("Start Gesture Control")
        self.stop_button = QPushButton("Stop")
        self.start_button.clicked.connect(self.start_control)
        self.stop_button.clicked.connect(self.stop_control)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        layout.addWidget(self.gesture_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)
        self.use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        print(f"Using GPU: {self.use_gpu}")
        self.hands = mp.solutions.hands.Hands(max_num_hands=1, static_image_mode=False, model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils
        self.finger_tips = [4, 8, 12, 16, 20]
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.last_action_time = 0
        self.cooldown = 1
    def start_control(self):
        self.timer.start(30)
    def stop_control(self):
        self.timer.stop()
        self.video_label.setText("Video Stopped")
        self.gesture_label.setText("Gesture: None")
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self.use_gpu:
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(rgb)
            results = self.hands.process(gpu_frame.download())
        else:
            results = self.hands.process(rgb)

        gesture = None
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                gesture = self.classify_gesture(hand_landmarks)
                self.perform_action(gesture)
        if gesture:
            self.gesture_label.setText(f"Gesture: {gesture.upper()}")
        else:
            self.gesture_label.setText("Gesture: None")
        img = QImage(rgb.data, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        self.video_label.setPixmap(pixmap)
    def count_fingers(self, hand_landmarks):
        count = 0
        landmarks = hand_landmarks.landmark
        if landmarks[self.finger_tips[0]].x < landmarks[self.finger_tips[0] - 1].x:
            count += 1
        for tip_id in self.finger_tips[1:]:
            if landmarks[tip_id].y < landmarks[tip_id - 2].y:
                count += 1
        return count
    def classify_gesture(self, hand_landmarks):
        count = self.count_fingers(hand_landmarks)
        landmarks = hand_landmarks.landmark
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        index_mcp = landmarks[5]
        if count == 0:
            return "pause"
        is_thumb_up = (
            thumb_tip.y < thumb_ip.y < thumb_mcp.y and  
            all(landmarks[i].y > landmarks[i - 2].y for i in self.finger_tips[1:])  
        )
        if is_thumb_up:
            return "play_again"
        if count == 1 and thumb_tip.y > thumb_ip.y:
            return "roll"
        elif count == 1:
            return "jump"
        elif count == 2:
            return "left"
        elif count == 3:
            return "right"
        elif count == 5:
            return "hoverboard"
        else:
            return None
    def perform_action(self, gesture):
        if not gesture:
            return
        current_time = time.time()
        if current_time - self.last_action_time < self.cooldown:
            return
        key_map = {
            "jump": "up",
            "roll": "down",
            "left": "left",
            "right": "right",
            "hoverboard": "space",
            "pause": "esc",            # You may need to verify key binding for pause
            "play_again": "enter"      # Change to actual key used for "Play Again"
        }
        key = key_map.get(gesture)
        if key:
            pyautogui.keyDown(key)
            time.sleep(0.1)
            pyautogui.keyUp(key)
            self.last_action_time = current_time
    def perform_action(self, gesture):
        if not gesture:
            return
        current_time = time.time()
        if current_time - self.last_action_time < self.cooldown:
            return
        key_map = {
            "jump": "up",
            "roll": "down",
            "left": "left",
            "right": "right",
            "hoverboard": "space"
        }
        key = key_map.get(gesture)
        if key:
            pyautogui.keyDown(key)
            time.sleep(0.1)
            pyautogui.keyUp(key)
            self.last_action_time = current_time
    def closeEvent(self, event):
        self.cap.release()
        event.accept()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GestureControlApp()
    window.show()
    sys.exit(app.exec_())
