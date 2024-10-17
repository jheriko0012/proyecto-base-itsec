import sys
import cv2
import os
import numpy as np
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QHBoxLayout, QGridLayout, QLCDNumber, QDialog, 
                             QScrollArea, QMessageBox, QWidget as QWidgetGallery)
from PyQt6.QtCore import QTimer, QTime
from PyQt6.QtGui import QPixmap, QImage
import mediapipe as mp

# Crea la carpeta para los videos si no existe
if not os.path.exists('videos'):
    os.makedirs('videos')

class VideoPlayer(QDialog):
    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle("Reproducción de Video")
        self.setGeometry(100, 100, 800, 600)

        self.label_video = QLabel(self)
        self.label_video.setFixedSize(800, 600)

        self.cap = cv2.VideoCapture(video_path)
        self.timer_playback = QTimer(self)
        self.timer_playback.timeout.connect(self.update_video_preview)
        self.timer_playback.start(30)

    def update_video_preview(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.timer_playback.stop()
                self.cap.release()
                self.close()
                return

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QPixmap(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888))
            self.label_video.setPixmap(qt_image)
        else:
            self.timer_playback.stop()
            self.close()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Detección de Somnolencia")
        self.setGeometry(100, 100, 800, 400)

        self.face_mesh = mp.solutions.face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils

        main_layout = QHBoxLayout()
        stats_layout = QGridLayout()

        self.label_parpadeos = QLabel("Pestañeos")
        self.contador_parpadeos = QLCDNumber(self)
        self.contador_parpadeos.display(0)

        self.label_microsuenos = QLabel("Microsueños") 
        self.contador_microsuenos = QLCDNumber(self)
        self.contador_microsuenos.display(0)

        self.label_cronometro = QLabel("Cronómetro:")
        self.cronometro = QLCDNumber(self)
        self.cronometro.display("00:00:00")

        stats_layout.addWidget(self.label_parpadeos, 0, 0)
        stats_layout.addWidget(self.contador_parpadeos, 0, 1)
        stats_layout.addWidget(self.label_microsuenos, 1, 0)
        stats_layout.addWidget(self.contador_microsuenos, 1, 1)
        stats_layout.addWidget(self.label_cronometro, 2, 0)
        stats_layout.addWidget(self.cronometro, 2, 1)

        main_layout.addLayout(stats_layout)

        right_layout = QVBoxLayout()

        self.label_imagen = QLabel(self)
        self.label_imagen.setFixedSize(1280, 720)
        self.label_imagen.setStyleSheet("border: 10px solid black;")

        self.boton_historial = QPushButton("Mostrar historial", self)
        self.boton_historial.clicked.connect(self.show_history)

        self.boton_iniciar = QPushButton("Iniciar Detección", self)
        self.boton_iniciar.clicked.connect(self.start_detection)

        right_layout.addWidget(self.label_imagen)
        right_layout.addWidget(self.boton_historial)
        right_layout.addWidget(self.boton_iniciar)

        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.time = QTime(0, 0, 0)
        self.timer.start(1000)

        self.cap = None
        self.detection_active = False
        self.video_writer = None
        self.blink_counter = 0
        self.micro_sleep_counter = 0

    def show_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Galería de Videos")
        dialog.setGeometry(150, 150, 800, 600)

        layout = QVBoxLayout(dialog)
        scroll_area = QScrollArea(dialog)
        scroll_area.setWidgetResizable(True)

        grid_layout = QGridLayout()
        video_files = os.listdir('videos')
        video_files = [f for f in video_files if f.endswith(('.avi', '.mp4'))]

        if not video_files:
            QMessageBox.information(self, "Información", "No hay videos guardados en el historial.")
            return

        for i, video in enumerate(video_files):
            # Crear un QLabel para la miniatura
            thumbnail_label = QLabel()
            thumbnail_label.setFixedSize(160, 90)
            thumbnail_label.setStyleSheet("border: 1px solid black; margin: 5px;")
            thumbnail_label.setScaledContents(True)

            # Crear miniatura del video
            cap = cv2.VideoCapture(os.path.join('videos', video))
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (160, 90))
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QPixmap(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888))
                thumbnail_label.setPixmap(qt_image)

            thumbnail_label.mousePressEvent = lambda event, video=video: self.play_video(video)

            # Añadir miniatura al layout
            grid_layout.addWidget(thumbnail_label, i // 5, i % 5)  # Organizar en una cuadrícula

        scroll_area.setWidget(QWidgetGallery())
        scroll_area.widget().setLayout(grid_layout)
        layout.addWidget(scroll_area)

        close_button = QPushButton("Cerrar", dialog)
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.exec()

    def play_video(self, video_name):
        video_path = os.path.join('videos', video_name)
        self.video_player = VideoPlayer(video_path)
        self.video_player.exec()

    def start_detection(self):
        if not self.detection_active:
            self.cap = cv2.VideoCapture(0)  # Usa la cámara en tiempo real
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter('videos/detectado.avi', fourcc, 20.0, (1280, 720))
            self.detection_active = True
            self.boton_iniciar.setText("Detener Detección")
            self.timer_detection = QTimer(self)
            self.timer_detection.timeout.connect(self.detect)
            self.timer_detection.start(30)
        else:
            self.detection_active = False
            self.timer_detection.stop()
            self.boton_iniciar.setText("Iniciar Detección")
            if self.cap:
                self.cap.release()
            if self.video_writer:
                self.video_writer.release()
            self.label_imagen.clear()

    def update_time(self):
        self.time = self.time.addSecs(1)
        self.cronometro.display(self.time.toString("hh:mm:ss"))

    def detect(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.timer_detection.stop()
                self.boton_iniciar.setText("Iniciar Detección")
                self.cap.release()
                if self.video_writer:
                    self.video_writer.release()
                return

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(frame_rgb)

            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(frame, face_landmarks)

                    # Detección de pestañeos (simplificada)
                    left_eye = np.array([(landmark.x, landmark.y) for landmark in face_landmarks.landmark[mp.solutions.face_mesh.FACEMESH_LEFT_EYE]])
                    right_eye = np.array([(landmark.x, landmark.y) for landmark in face_landmarks.landmark[mp.solutions.face_mesh.FACEMESH_RIGHT_EYE]])

                    # Calcular la relación de aspecto del ojo
                    left_eye_aspect_ratio = (left_eye[1][1] - left_eye[5][1]) / (left_eye[3][0] - left_eye[0][0])
                    right_eye_aspect_ratio = (right_eye[1][1] - right_eye[5][1]) / (right_eye[3][0] - right_eye[0][0])

                    # Contar pestañeos
                    if left_eye_aspect_ratio < 0.2 and right_eye_aspect_ratio < 0.2:
                        self.blink_counter += 1
                        self.contador_parpadeos.display(self.blink_counter)

            if self.video_writer:
                self.video_writer.write(frame)

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QPixmap(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888))
            self.label_imagen.setPixmap(qt_image)

    def closeEvent(self, event):
        self.detection_active = False
        if self.cap:
            self.cap.release()
        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
