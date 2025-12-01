"""
Target Analyzer - Automatisk gruppemåling med computer vision
Bruker OpenCV til å måle gruppestørrelse fra bilder av skiver
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QGroupBox, QFileDialog, QTableWidget,
                            QTableWidgetItem, QMessageBox, QSpinBox, QDoubleSpinBox,
                            QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QImage
from src.database.database import get_database
from src.utils.i18n import tr
import cv2
import numpy as np
from datetime import datetime
import os


class TargetAnalyzer(QWidget):
    """Widget for automatisk målanalyse"""
    
    def __init__(self):
        super().__init__()
        self.db = get_database()
        self.current_image = None
        self.detected_shots = []
        self.init_ui()
    
    def init_ui(self):
        """Initialiserer brukergrensesnittet"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tittel
        title = QLabel("📷 Target Analyzer - Automatisk Gruppemåling")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        subtitle = QLabel("Last opp bilde av skive → AI måler automatisk gruppestørrelse, ES og MOA")
        subtitle.setStyleSheet("color: gray; font-size: 11pt;")
        layout.addWidget(subtitle)
        
        # Hovedlayout med bilde og resultater side-ved-side
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)
        
        # Venstre side - Bildeopplasting og visning
        left_widget = self.create_image_section()
        main_layout.addWidget(left_widget, 3)
        
        # Høyre side - Resultater og analyse
        right_widget = self.create_results_section()
        main_layout.addWidget(right_widget, 2)
        
        # Kontroller nederst
        controls_layout = self.create_controls()
        layout.addLayout(controls_layout)
    
    def create_image_section(self):
        """Oppretter bildeseksjon"""
        group = QGroupBox("📸 Skivebilde")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Bildedisplay
        self.image_label = QLabel()
        self.image_label.setMinimumSize(600, 600)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
            }
        """)
        self.image_label.setText("Klikk 'Last opp bilde' for å starte")
        layout.addWidget(self.image_label)
        
        # Last opp knapp
        upload_btn = QPushButton("📁 Last opp bilde av skive")
        upload_btn.setMinimumHeight(40)
        upload_btn.clicked.connect(self.upload_image)
        layout.addWidget(upload_btn)
        
        return group
    
    def create_results_section(self):
        """Oppretter resultatseksjon"""
        group = QGroupBox("📊 Analyseresultater")
        group.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Resultatvisning
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(300)
        self.results_text.setStyleSheet("font-size: 11pt;")
        self.results_text.setText("Last opp et bilde for å se resultater...")
        layout.addWidget(self.results_text)
        
        # Skuddtabell
        group_shots = QGroupBox("Detekterte skudd")
        shots_layout = QVBoxLayout()
        group_shots.setLayout(shots_layout)
        
        self.shots_table = QTableWidget()
        self.shots_table.setColumnCount(3)
        self.shots_table.setHorizontalHeaderLabels(["Skudd #", "X (mm)", "Y (mm)"])
        self.shots_table.setMaximumHeight(200)
        shots_layout.addWidget(self.shots_table)
        
        layout.addWidget(group_shots)
        
        return group
    
    def create_controls(self):
        """Oppretter kontroller"""
        layout = QHBoxLayout()
        
        # Parametre for analyse
        params_group = QGroupBox("Analyseparametre")
        params_layout = QHBoxLayout()
        params_group.setLayout(params_layout)
        
        params_layout.addWidget(QLabel("Avstand (m):"))
        self.distance = QSpinBox()
        self.distance.setRange(10, 1000)
        self.distance.setValue(100)
        self.distance.setSuffix(" m")
        params_layout.addWidget(self.distance)
        
        params_layout.addWidget(QLabel("Skive størrelse (cm):"))
        self.target_size = QDoubleSpinBox()
        self.target_size.setRange(10, 100)
        self.target_size.setValue(20.0)
        self.target_size.setSuffix(" cm")
        self.target_size.setDecimals(1)
        params_layout.addWidget(self.target_size)
        
        params_layout.addWidget(QLabel("Sensitivitet:"))
        self.sensitivity = QSpinBox()
        self.sensitivity.setRange(1, 10)
        self.sensitivity.setValue(5)
        params_layout.addWidget(self.sensitivity)
        
        layout.addWidget(params_group)
        
        # Handlingsknapper
        analyze_btn = QPushButton("🔍 Analyser bilde")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.clicked.connect(self.analyze_image)
        layout.addWidget(analyze_btn)
        
        save_btn = QPushButton("💾 Lagre resultater")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_results)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        return layout
    
    def upload_image(self):
        """Last opp bilde"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Velg skivebilde",
            "",
            "Bilder (*.png *.jpg *.jpeg *.bmp);;Alle filer (*.*)"
        )
        
        if file_path:
            # Last inn med OpenCV
            self.current_image = cv2.imread(file_path)
            
            if self.current_image is not None:
                # Vis bilde
                self.display_image(self.current_image)
                self.results_text.setText(f"✅ Bilde lastet: {os.path.basename(file_path)}\n\nKlikk 'Analyser bilde' for å starte...")
            else:
                QMessageBox.critical(self, "Feil", "Kunne ikke laste bildet!")
    
    def display_image(self, image, shots=None):
        """Viser bilde i GUI"""
        # Lag en kopi for visning
        display_img = image.copy()
        
        # Tegn detekterte skudd hvis tilgjengelig
        if shots is not None and len(shots) > 0:
            for i, shot in enumerate(shots):
                x, y = shot
                # Tegn sirkel rundt skudd
                cv2.circle(display_img, (int(x), int(y)), 10, (0, 255, 0), 2)
                # Nummerer skudd
                cv2.putText(display_img, str(i+1), (int(x)+15, int(y)+5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Konverter BGR til RGB
        rgb_image = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        
        # Skaler ned hvis for stort
        height, width = rgb_image.shape[:2]
        max_size = 600
        if height > max_size or width > max_size:
            scale = min(max_size/height, max_size/width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            rgb_image = cv2.resize(rgb_image, (new_width, new_height))
        
        # Konverter til QPixmap
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        self.image_label.setPixmap(pixmap)
    
    def analyze_image(self):
        """Analyserer bildet for å finne skudd"""
        if self.current_image is None:
            QMessageBox.warning(self, "Ingen bilde", "Last opp et bilde først!")
            return
        
        try:
            # Kjør deteksjon
            shots = self.detect_shots(self.current_image, self.sensitivity.value())
            
            if len(shots) == 0:
                QMessageBox.warning(
                    self, "Ingen skudd funnet",
                    "Kunne ikke detektere skudd. Prøv å justere sensitivitet eller last opp et tydeligere bilde."
                )
                return
            
            self.detected_shots = shots
            
            # Beregn statistikk
            results = self.calculate_group_stats(shots)
            
            # Vis resultater
            self.display_results(results)
            
            # Oppdater tabell
            self.update_shots_table(shots)
            
            # Vis bilde med markerte skudd
            self.display_image(self.current_image, shots)
            
        except Exception as e:
            QMessageBox.critical(self, "Feil ved analyse", f"En feil oppstod:\n{str(e)}")
    
    def detect_shots(self, image, sensitivity):
        """Detekterer skudd i bildet"""
        # Konverter til gråskala
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Bruk Gaussian blur for å redusere støy
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Bruk Hough Circle detection for å finne skudd
        # Juster parametre basert på sensitivitet
        min_radius = max(5, 20 - sensitivity * 2)
        max_radius = min(50, 30 + sensitivity * 2)
        param1 = 50
        param2 = max(10, 30 - sensitivity * 2)
        
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius
        )
        
        shots = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                shots.append((x, y))
        
        # Alternativ metode hvis Hough ikke finner noe: blob detection
        if len(shots) == 0:
            # Bruk SimpleBlobDetector
            params = cv2.SimpleBlobDetector_Params()
            params.filterByArea = True
            params.minArea = 50
            params.maxArea = 5000
            params.filterByCircularity = True
            params.minCircularity = 0.3
            params.filterByConvexity = True
            params.minConvexity = 0.5
            
            detector = cv2.SimpleBlobDetector_create(params)
            
            # Inverter bildet (skudd er ofte mørke hull)
            inverted = cv2.bitwise_not(gray)
            keypoints = detector.detect(inverted)
            
            for kp in keypoints:
                shots.append((int(kp.pt[0]), int(kp.pt[1])))
        
        return shots
    
    def calculate_group_stats(self, shots):
        """Beregner statistikk for gruppen"""
        if len(shots) < 2:
            return None
        
        # Konverter til numpy array
        points = np.array(shots, dtype=np.float32)
        
        # Finn centrum av gruppe
        center_x = np.mean(points[:, 0])
        center_y = np.mean(points[:, 1])
        
        # Beregn avstand fra hver shot til centrum
        distances = []
        for x, y in points:
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            distances.append(dist)
        
        # Finn ekstreme spread (lengste avstand mellom to skudd)
        max_spread_pixels = 0
        for i in range(len(points)):
            for j in range(i+1, len(points)):
                dist = np.sqrt(
                    (points[i][0] - points[j][0])**2 + 
                    (points[i][1] - points[j][1])**2
                )
                max_spread_pixels = max(max_spread_pixels, dist)
        
        # Konverter piksler til mm basert på kjent skive-størrelse
        # Anta at bildet viser hele skiven
        image_height = self.current_image.shape[0]
        target_size_mm = self.target_size.value() * 10  # cm til mm
        pixels_per_mm = image_height / target_size_mm
        
        max_spread_mm = max_spread_pixels / pixels_per_mm
        
        # Beregn gjennomsnittlig avstand fra centrum
        avg_distance_pixels = np.mean(distances)
        avg_distance_mm = avg_distance_pixels / pixels_per_mm
        
        # Beregn MOA ved gitt avstand
        distance_m = self.distance.value()
        moa = (max_spread_mm / 10) / (distance_m / 100) / 2.908  # 1 MOA = 2.908 cm ved 100m
        mrad = (max_spread_mm / 10) / (distance_m / 10)  # 1 MRAD = 10 cm ved 100m
        
        return {
            'shot_count': len(shots),
            'center': (center_x, center_y),
            'max_spread_mm': max_spread_mm,
            'avg_radius_mm': avg_distance_mm,
            'moa': moa,
            'mrad': mrad,
            'distance_m': distance_m
        }
    
    def display_results(self, results):
        """Viser resultater i tekstfeltet"""
        if results is None:
            self.results_text.setText("❌ Kunne ikke beregne statistikk")
            return
        
        text = f"""
<h3>✅ Analyse ferdig!</h3>

<p><b>Antall skudd detektert:</b> {results['shot_count']}</p>

<p><b>Gruppestørrelse (Extreme Spread):</b><br>
• {results['max_spread_mm']:.1f} mm<br>
• {results['max_spread_mm']/10:.2f} cm<br>
• {results['moa']:.2f} MOA<br>
• {results['mrad']:.3f} MRAD</p>

<p><b>Gjennomsnittlig radius:</b><br>
• {results['avg_radius_mm']:.1f} mm fra centrum</p>

<p><b>Avstand:</b> {results['distance_m']} meter</p>

<hr>

<p style="color: #555; font-size: 10pt;">
<b>Tips:</b> Gruppestørrelsen måles center-to-center mellom de to ytterste skuddene.
Dette er standard i precision shooting.
</p>
        """
        
        self.results_text.setHtml(text)
    
    def update_shots_table(self, shots):
        """Oppdaterer skuddtabellen"""
        self.shots_table.setRowCount(len(shots))
        
        # Beregn pixels per mm
        image_height = self.current_image.shape[0]
        target_size_mm = self.target_size.value() * 10
        pixels_per_mm = image_height / target_size_mm
        
        for i, (x, y) in enumerate(shots):
            # Konverter til mm relativt til centrum
            center_x = self.current_image.shape[1] / 2
            center_y = self.current_image.shape[0] / 2
            
            x_mm = (x - center_x) / pixels_per_mm
            y_mm = (center_y - y) / pixels_per_mm  # Y invertert
            
            self.shots_table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.shots_table.setItem(i, 1, QTableWidgetItem(f"{x_mm:.1f}"))
            self.shots_table.setItem(i, 2, QTableWidgetItem(f"{y_mm:.1f}"))
    
    def save_results(self):
        """Lagrer resultater til database"""
        if len(self.detected_shots) == 0:
            QMessageBox.warning(self, "Ingen data", "Analyser et bilde først!")
            return
        
        # Beregn statistikk på nytt
        results = self.calculate_group_stats(self.detected_shots)
        
        if results is None:
            return
        
        # TODO: Integrer med eksisterende shooting sessions
        # For nå, vis bare bekreftelse
        
        msg = f"""
Vil du lagre disse resultatene?

Gruppe: {results['max_spread_mm']:.1f} mm ({results['moa']:.2f} MOA)
Skudd: {results['shot_count']}
Avstand: {results['distance_m']} m

(Integrering med shooting sessions kommer i neste versjon)
        """
        
        reply = QMessageBox.question(
            self, "Lagre resultater",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self, "Lagret",
                "Resultater lagret! (Feature under utvikling)"
            )
