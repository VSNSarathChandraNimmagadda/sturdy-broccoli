import sys
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QSizePolicy
)
genai.configure(api_key="MY_API_KEY")
model = genai.GenerativeModel("models/gemini-1.5-pro")
engine = pyttsx3.init()
class GeminiApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gemini Voice/Text Assistant")
        self.setGeometry(100, 100, 600, 500)
        layout = QVBoxLayout()
        self.input_mode = QComboBox()
        self.input_mode.addItems(["Text", "Voice"])
        layout.addWidget(QLabel("Select Input Mode:"))
        layout.addWidget(self.input_mode)
        self.output_mode = QComboBox()
        self.output_mode.addItems(["Text", "Voice"])
        layout.addWidget(QLabel("Select Output Mode:"))
        layout.addWidget(self.output_mode)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter your question here...")
        self.input_text.setFixedHeight(80)
        layout.addWidget(self.input_text)
        self.ask_button = QPushButton("Ask Gemini")
        self.ask_button.clicked.connect(self.process_query)
        layout.addWidget(self.ask_button)
        layout.addWidget(QLabel("Gemini Response:"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.result_text)
        self.setLayout(layout)
    def process_query(self):
        mode = self.input_mode.currentText()
        output = self.output_mode.currentText()
        if mode == "Text":
            query = self.input_text.toPlainText().strip()
        else:
            query = self.get_voice_input()
            self.input_text.setText(query)
        if not query:
            self.result_text.setText("Please enter or speak a question.")
            return
        try:
            response = model.generate_content(query)
            answer = response.text
            formatted_answer = self.format_response(answer)
        except Exception as e:
            formatted_answer = f"Error: {e}"
            answer = formatted_answer
        self.result_text.setText(formatted_answer)
        if output == "Voice":
            clean_answer = self.clean_text_for_voice(answer)
            engine.say(clean_answer)
            engine.runAndWait()
    def get_voice_input(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.result_text.setText("Listening...")
            try:
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=5)
                return r.recognize_google(audio)
            except sr.UnknownValueError:
                return "Sorry, I couldn't understand you."
            except Exception as e:
                return f"Error: {e}"
    def format_response(self, text):
        lines = text.strip().split('\n')
        bullet_points = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if re.match(r'^\*+\s*\w+', line):
                line = re.sub(r'^\*+\s*', '', line)
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            line = re.sub(r'\*(.*?)\*', r'\1', line)
            if not (line.startswith("-") or line[0].isdigit()):
                bullet_points.append(f"• {line}")
            else:
                bullet_points.append(line)
        return "\n".join(bullet_points)
    def clean_text_for_voice(self, text):
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if re.match(r'^\*+\s*\w+', line):
                line = re.sub(r'^\*+\s*', '', line)
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
            line = re.sub(r'\*(.*?)\*', r'\1', line)
            if not re.search(r'[A-Za-z0-9]\s*\*\s*[A-Za-z0-9]', line):
                line = line.replace('*', '')
            cleaned_lines.append(line)
        return ' '.join(cleaned_lines)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GeminiApp()
    window.show()
    sys.exit(app.exec_())
