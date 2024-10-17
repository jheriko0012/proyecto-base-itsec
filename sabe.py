import sys
import cv2
import time
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QGridLayout, QLCDNumber
from PyQt6.QtCore import QTimer, QTime

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.setWindowTitle("Detección de Somnolencia")
        self.setGeometry(100, 100, 800, 400)

        # Crear el layout principal
        main_layout = QHBoxLayout()

        # Crear el layout de la izquierda para mostrar las estadísticas
        stats_layout = QGridLayout()

        # Etiquetas y contadores
        self.label_parpadeos = QLabel("Pestañeos")
        self.contador_parpadeos = QLCDNumber(self)
        self.contador_parpadeos.display(0)

        self.label_microsuenos = QLabel("Microsueños")
        self.contador_microsuenos = QLCDNumber(self)
        self.contador_microsuenos.display(0)

        self.label_cronometro = QLabel("Cronómetro:")
        self.cronometro = QLCDNumber(self)
        self.cronometro.display("00:00:00")

        # Añadir widgets al layout de estadísticas
        stats_layout.addWidget(self.label_parpadeos, 0, 0)
        stats_layout.addWidget(self.contador_parpadeos, 0, 1)
        stats_layout.addWidget(self.label_microsuenos, 1, 0)
        stats_layout.addWidget(self.contador_microsuenos, 1, 1)
        stats_layout.addWidget(self.label_cronometro, 2, 0)
        stats_layout.addWidget(self.cronometro, 2, 1)

        # Añadir el layout de estadísticas al layout principal
        main_layout.addLayout(stats_layout)

        # Crear el layout de la derecha para la imagen de la cámara y los botones
        right_layout = QVBoxLayout()

        # Área de visualización de la cámara
        self.label_imagen = QLabel(self)
        self.label_imagen.setFixedSize(480, 360)
        self.label_imagen.setStyleSheet("border: 2px solid black;")

        # Botones
        self.boton_historial = QPushButton("Mostrar historial", self)
        self.boton_historial.clicked.connect(self.show_history)

        self.boton_iniciar = QPushButton("Iniciar Detección", self)
        self.boton_iniciar.clicked.connect(self.start_detection)

        # Añadir widgets al layout de la derecha
        right_layout.addWidget(self.label_imagen)
        right_layout.addWidget(self.boton_historial)
        right_layout.addWidget(self.boton_iniciar)

        # Añadir el layout de la derecha al layout principal
        main_layout.addLayout(right_layout)

        # Establecer el layout principal
        self.setLayout(main_layout)

        # Configuración del temporizador para el cronómetro
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.time = QTime(0, 0, 0)
        self.timer.start(1000)

        # Variables para detección
        self.cap = None
        self.detection_active = False

    def show_history(self):
        # Mostrar el historial de videos
        print("Mostrar historial de videos")  # Aquí podrías abrir otra ventana o mostrar el historial.

    def start_detection(self):
        if not self.detection_active:
            self.cap = cv2.VideoCapture(0)
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
            self.label_imagen.clear()

    def update_time(self):
        self.time = self.time.addSecs(1)
        self.cronometro.display(self.time.toString("hh:mm:ss"))

    def detect(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Aquí iría el código de detección facial y somnolencia
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Cargar el clasificador en cascada de la cara y realizar la detección
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                # Convertir el frame a un formato que pueda ser mostrado en PyQt
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QPixmap(QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888))
                self.label_imagen.setPixmap(qt_image)

    def closeEvent(self, event):
        self.detection_active = False
        if self.cap:
            self.cap.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
