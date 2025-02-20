import sys
import cv2
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QFileDialog, QSizePolicy, QMessageBox


OUTPUT_FOURCC_FORMAT = 'mp4v'


def openVideofileCapture(filename: str):
    capture = cv2.VideoCapture(filename)
    if not capture.isOpened():
        return None
    return capture


def processFrame(frame: np.ndarray) -> np.ndarray:
    left_lo  = frame[:, :640, 1].astype(np.uint16)  
    right_hi = frame[:, 640:, 1].astype(np.uint16)  

    combined_16 = (right_hi << 8) | left_lo

    combined_8 = (combined_16 >> 8).astype(np.uint8)

    inverted = 255 - combined_8

    out = cv2.cvtColor(inverted, cv2.COLOR_GRAY2BGR)
    return out






class VideoFileProcessorWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Videofile process tool')
        self.setMinimumSize(480, 200)

        self._input_videofile, self._output_videofile = None, None
        self._input_capture, self._output_writer = None, None
        self._is_working = False
        self._work_progress = 0.0

        # Layout for all GUI widgets
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Input videofile
        self.inputfile_choose_label = QLabel()
        self.central_layout.addWidget(self.inputfile_choose_label)
    
        self.inputfile_choose_button = QPushButton('Выбрать исходный видеофайл')
        self.inputfile_choose_button.clicked.connect(self._chooseInputVideofile)
        self.central_layout.addWidget(self.inputfile_choose_button)

        # Output videofile
        self.outputfile_choose_label = QLabel()
        self.central_layout.addWidget(self.outputfile_choose_label)

        self.outputfile_choose_button = QPushButton('Сохранять в')
        self.outputfile_choose_button.clicked.connect(self._chooseOutputVideofile)
        self.central_layout.addWidget(self.outputfile_choose_button)

        # Work progress
        self.work_progress_label = QLabel()
        self.central_layout.addWidget(self.work_progress_label)

        self.work_progressbar = QProgressBar()
        self.work_progressbar.setMinimum(0) ; self.work_progressbar.setMaximum(100)
        self.central_layout.addWidget(self.work_progressbar)

        # Control button
        self.work_control_button = QPushButton()
        self.work_control_button.clicked.connect(self._workProcessControl)
        self.central_layout.addWidget(self.work_control_button)
        
        self._updateWidgetsState()
    
    @pyqtSlot()
    def _updateWidgetsState(self):

        # Input videofile
        if self._input_videofile:
            self.inputfile_choose_label.setText(f'Входной файл: {self._input_videofile}')
        else:
            self.inputfile_choose_label.setText('Выберите входной видеофайл')
        self.inputfile_choose_button.setEnabled(not self._is_working)

        # Output videofile
        if self._output_videofile:
            self.outputfile_choose_label.setText(f'Файл для записи результата: {self._output_videofile}')
        else:
            self.outputfile_choose_label.setText('Выберите файл для записи результата')
        self.outputfile_choose_button.setEnabled(not self._is_working)

        # Work progress
        if self._is_working:
            self.work_progress_label.setText('Идёт обработка')
            self.work_progressbar.setValue(int(self._work_progress * 100))
        else:
            self.work_progress_label.setText('Обработайте файл')
            self.work_progressbar.setValue(0)
    
        # Control button
        self.work_control_button.setEnabled(self._input_videofile is not None and self._output_videofile is not None)
        self.work_control_button.setText('Начать работу' if not self._is_working else 'Завершить работу')

    ######################################## Choose files ########################################
    
    @pyqtSlot()
    def _chooseInputVideofile(self):
        if self._is_working:
            return
        filename, _ = QFileDialog.getOpenFileName(self, 'Выберите видеофайл', '', 'Video Files (*.mp4 *.avi)')
        if filename:
            self._input_videofile = filename
        else:
            self._input_videofile = None
        self._updateWidgetsState()

    @pyqtSlot()
    def _chooseOutputVideofile(self):
        if self._is_working:
            return
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранять результат обработки в файл', '', 'Video Files (*.mp4)')
        if filename:
            self._output_videofile = filename
        else:
            self._output_videofile = None
        self._updateWidgetsState()
    
    ######################################## Work process ########################################
    
    @pyqtSlot()
    def _workProcessControl(self):
        if not self._is_working:
            if not self._input_videofile:
                QMessageBox.critical(self, 'Ошибка', 'Не выбран исходный видеофайл')
                return
            if not self._output_videofile:
                QMessageBox.critical(self, 'Ошибка', 'Не выбран видеофайл для записи результата')
                return

            # Input capturer
            self._input_capture = openVideofileCapture(self._input_videofile)
            if self._input_capture is None:
                QMessageBox.critical(self, 'Ошибка', 'Не удалось открыть исходный файл')
                return
            
            # Get first frame
            ret, input_frame = self._input_capture.read()
            if not ret:
                self._input_capture.release()
                self._input_capture = None
                QMessageBox.critical(self, 'Ошибка', 'Не удалось прочитать первый кадр')
                return
            
            # Get input video parameters
            self._input_width = self._input_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            self._input_height = self._input_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self._fps = int(round(self._input_capture.get(cv2.CAP_PROP_FPS)))
            self._total_frames = int(round(self._input_capture.get(cv2.CAP_PROP_FRAME_COUNT)))

            print(f'Input format: width = {self._input_width}; height = {self._input_height}; ' \
                f'fps = {self._fps}; total_frames = {self._total_frames}\n' \
                f'shape = {input_frame.shape}; dtype={input_frame.dtype}')

            # Process first frame and get output video parameters
            processed_frame = processFrame(input_frame)
            self._output_width, self._output_height = processed_frame.shape[1], processed_frame.shape[0]
            print(f'Result format: width = {self._output_width}; height = {self._output_height}; ' \
                f'fps = {self._fps}; total_frames = {self._total_frames}\n' \
                f'shape = {processed_frame.shape}; dtype={processed_frame.dtype}')
            
            # Ouput writer
            fourcc = cv2.VideoWriter_fourcc(*OUTPUT_FOURCC_FORMAT)
            self._output_writer = cv2.VideoWriter(self._output_videofile, fourcc, fps=self._fps, frameSize=(self._output_width, self._output_height))
            if not self._output_writer.isOpened():
                self._input_capture.release()
                self._input_capture, self._output_writer = None, None
                QMessageBox.critical(self, 'Ошибка', 'Не удалось начать запись в видеофайл')
                return
            
            # Write first frame
            self._output_writer.write(processed_frame)

            # Start work process
            self._is_working = True
            self._processVideo()
        else:
            self._stopWork()
        self._updateWidgetsState()

    def _stopWork(self):
        if not self._is_working:
            return
        self._output_writer.release()
        self._input_capture.release()
        self._input_writer, self._output_writer = None, None
        self._input_videofile, self._output_videofile = None, None
        self._is_working = False
    
    def _processVideo(self):
        processed_frames = 1
        while True:
            ret, input_frame = self._input_capture.read()
            if not ret:
                break
            processed_frame = processFrame(input_frame)
            self._output_writer.write(processed_frame)
            
            processed_frames += 1
            self._work_progress = processed_frames / self._total_frames
            self._updateWidgetsState()
            
            QApplication.processEvents()
        print(f'Proccessed {processed_frames} frames')
        self._stopWork()
        QMessageBox.information(self, 'Результат', 'Файл успешно обработан')
        self._updateWidgetsState()

    ######################################## Other GUI events ########################################

    @pyqtSlot()
    def closeEvent(self, event):
        if self._is_working:
            self._stopWork()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoFileProcessorWindow()
    window.show()
    sys.exit(app.exec())
