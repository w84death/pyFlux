import sys
import os
import time
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QVBoxLayout, QFileDialog, QCheckBox, QInputDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ImageFetcher(QThread):
    image_ready = pyqtSignal(str)

    def __init__(self, request_id):
        super().__init__()
        self.request_id = request_id

    def run(self):
        while True:
            time.sleep(0.5)
            result = requests.get(
                'https://api.bfl.ml/v1/get_result',
                headers={
                    'accept': 'application/json',
                    'x-key': os.environ.get("BFL_API_KEY"),
                },
                params={
                    'id': self.request_id,
                },
            ).json()
            if result["status"] == "Ready":
                self.image_ready.emit(result['result']['sample'])
                break

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'pyFlux'
        self.check_api_key()
        self.initUI()

    def check_api_key(self):
        config_file = 'config.txt'
        api_key = None

        if os.path.exists(config_file):
            with open(config_file, 'r') as file:
                api_key = file.read().strip()

        if not api_key:
            api_key, ok = QInputDialog.getText(self, 'API Key Required', 'Enter your BFL API Key:')
            if ok and api_key:
                with open(config_file, 'w') as file:
                    file.write(api_key)
                os.environ["BFL_API_KEY"] = api_key
            else:
                QMessageBox.critical(self, 'Error', 'API Key is required to proceed.')
                sys.exit(1)
        else:
            os.environ["BFL_API_KEY"] = api_key

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        top_row = QHBoxLayout()

        self.prompt_label = QLabel('Prompt:', self)
        top_row.addWidget(self.prompt_label)

        self.prompt_input = QLineEdit(self)
        top_row.addWidget(self.prompt_input)

        self.aspect_ratio_label = QLabel('Aspect Ratio:', self)
        top_row.addWidget(self.aspect_ratio_label)

        self.aspect_ratio_var = QComboBox(self)
        self.aspect_ratio_var.addItems(['16:9', '4:3', '1:1', '21:9', '3:4'])
        top_row.addWidget(self.aspect_ratio_var)

        self.raw_checkbox = QCheckBox('RAW', self)
        top_row.addWidget(self.raw_checkbox)

        self.submit_button = QPushButton('Submit', self)
        self.submit_button.clicked.connect(self.on_submit)
        top_row.addWidget(self.submit_button)

        layout.addLayout(top_row)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.save_button = QPushButton('Save Image', self)
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def on_submit(self):
        prompt = self.prompt_input.text()
        aspect_ratio = self.aspect_ratio_var.currentText()
        raw_mode = self.raw_checkbox.isChecked()

        # Build the payload
        payload = {
            'prompt': prompt,
            'aspect_ratio': aspect_ratio,
            'output_format': 'png',
            'raw': raw_mode
        }
        response = requests.post(
            'https://api.bfl.ml/v1/flux-pro-1.1-ultra',
            headers={
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'x-key': os.environ.get("BFL_API_KEY"),
            },
            json=payload
        )
        response_data = response.json()
        request_id = response_data['id']

        # Show loading icon
        self.loading_movie = QMovie("loading.gif")
        self.image_label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self.image_fetcher = ImageFetcher(request_id)
        self.image_fetcher.image_ready.connect(self.display_image)
        self.image_fetcher.start()

    def display_image(self, image_url):
        self.image_url = image_url
        pixmap = QPixmap()
        pixmap.loadFromData(requests.get(image_url).content)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.save_button.setEnabled(True)

    def resizeEvent(self, event):
        if hasattr(self, 'image_url'):
            pixmap = QPixmap()
            pixmap.loadFromData(requests.get(self.image_url).content)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super().resizeEvent(event)

    def save_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'wb') as file:
                file.write(requests.get(self.image_url).content)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())