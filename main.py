from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton, QLabel, QGridLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThreadPool, QRunnable, QTimer, QSize, QObject
from PyQt5.QtGui import QPixmap
import sys
import os
import json
import subprocess
import psutil
from PIL import Image
import numpy as np
import time


class UpdateBlenderSignals(QObject):
    finished = pyqtSignal()


class UpdateBlenderImage(QRunnable):
    def __init__(self, image_path, label, qt_frame, blender_to_qt_path):
        super(UpdateBlenderImage, self).__init__()
        self.image_path = image_path
        self.label = label
        self.qt_frame = qt_frame
        self.blender_frame = 0
        self.blender_to_qt_path = blender_to_qt_path
        self.signals = UpdateBlenderSignals()

    @pyqtSlot()
    def run(self):
        self.pixmap = QPixmap(self.image_path)
        while not os.path.isfile(self.blender_to_qt_path):
            time.sleep(0.25)
        self.get_blender_frame()
        while self.blender_frame != self.qt_frame:
            time.sleep(0.1)
            self.get_blender_frame()
        self.pixmap = QPixmap(self.image_path)
        self.label.setPixmap(self.pixmap)
        self.signals.finished.emit()

    def get_blender_frame(self):
        with open(self.blender_to_qt_path, 'r') as f:
            blender_to_qt_dict = json.load(f)
            self.blender_frame = blender_to_qt_dict['blender_frame']


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.qt_to_blender_path = os.path.abspath("qt_to_blender.json")
        self.qt_frame = 0
        self.qt_to_blender_dict = {'qt_frame': self.qt_frame}
        with open(self.qt_to_blender_path, 'w+') as f:
            json.dump(self.qt_to_blender_dict, f)
        self.blender_to_qt_path = os.path.abspath("blender_to_qt.json")
        self.blender_frame = 0
        self.blender_to_qt_dict = {'blender_frame': self.blender_frame}
        with open(self.blender_to_qt_path, 'w+') as f:
            json.dump(self.blender_to_qt_dict, f)
        self.blender_image_path = os.path.abspath("blender_out.png")
        self.all_text = []
        self.blender_process = None
        self.window_width = 1200
        self.window_height = 600
        self.blender_button = None
        self.blender_path_label = None
        self.console_text = None
        self.blender_pixmap = None
        self.grid = None
        self.thread_pool = QThreadPool()
        self.update_blender_image = None

        self.config = {}
        if os.path.isfile('config.json'):
            with open('config.json', 'r') as f:
                self.config = json.load(f)
            if self.config['blender_path'] == '':
                self.config.update({'blender_path': 'not set'})
        else:
            self.config = {'blender_path': 'not set'}
            with open('config.json', 'w+') as f:
                json.dump(self.config, f)
        self.init_ui()
        self.launch_blender()



    def text_to_console(self, new_text):
        self.all_text.append(new_text)
        new_output = ""
        for text in self.all_text[-4:]:
            new_output += text + '\n'
        self.console_text.setText(new_output)

    def new_update_blender(self):
        self.qt_frame += 1
        self.qt_to_blender_dict.update({"qt_frame": self.qt_frame})
        with open(self.qt_to_blender_path, 'w+') as f:
            json.dump(self.qt_to_blender_dict, f)
        self.update_blender_image = UpdateBlenderImage(self.blender_image_path, self.blender_image, self.qt_frame, self.blender_to_qt_path)
        self.update_blender_image.signals.finished.connect(self.new_update_blender)
        self.thread_pool.start(self.update_blender_image)

    def init_ui(self):
        self.setGeometry(0, 0, self.window_width, self.window_height)
        self.setWindowTitle("Blender Presenter")
        self.grid = QGridLayout(self)
        self.setLayout(self.grid)
        self.blender_grid = QGridLayout()
        self.grid.addLayout(self.blender_grid, 0, 0)
        self.blender_button = QPushButton(f'Update')
        self.blender_button.setMaximumSize(self.blender_button.sizeHint())
        self.blender_button.setToolTip('Set Blender Executable Path')
        self.blender_button.clicked.connect(self.on_configure_blender)
        self.blender_grid.addWidget(self.blender_button, 0, 0)

        blender_path = self.config['blender_path']
        self.blender_path_label = QLabel(f"Blender Path: {blender_path}")
        self.blender_grid.addWidget(self.blender_path_label, 0, 1)

        self.blender_image = QLabel()
        if not os.path.isfile(self.blender_image_path):
            test_image = np.ones((400, 400, 4), dtype=np.uint8)
            test_image[:, :, 1:] = test_image[:, :, 1:]*255
            im = Image.fromarray(test_image)
            im.save(self.blender_image_path)

        self.grid.addWidget(self.blender_image, 1, 0)
        self.console_text = QLabel("")
        self.grid.addWidget(self.console_text, 2, 0)
        self.show()

    def launch_blender(self):
        close_all_blenders()
        blender_path = self.config['blender_path']
        blender_script_path = os.path.abspath("blender_run.py")
        try:
            self.blender_process = subprocess.Popen([f'{blender_path}',
                                                     '--background',
                                                     '--python',
                                                     f'{blender_script_path}',
                                                     f'{self.blender_to_qt_path}',
                                                     f'{self.qt_to_blender_path}',
                                                     f'{self.blender_image_path}'])
            self.text_to_console("Blender Found")
        except FileNotFoundError:
            self.text_to_console("Blender not found")
        except PermissionError:
            self.text_to_console("Blender not found")
        self.new_update_blender()

    @pyqtSlot()
    def on_configure_blender(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        blender_path, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "All Files (*)", options=options)
        self.config.update({'blender_path': blender_path})
        self.blender_path_label.setText(f'Blender Path: {blender_path}')
        self.blender_path_label.resize(self.blender_button.sizeHint())
        with open('config.json', 'w+') as f:
            json.dump(self.config, f)
        self.launch_blender()


def close_all_blenders():
    for p in psutil.process_iter():
        if "blender" in p.name():
            blender_pid = p.pid
            os.kill(blender_pid, 1)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())
