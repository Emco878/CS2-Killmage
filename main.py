from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import (QTimer, Qt, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal)
import os, sys, time, numpy, dxcam, pygame, random, mouse

target_value_white = (255, 255, 255)
target_value_red = (225, 1, 1)
tolerance_white = 85
tolerance_red = 5
monitor_index = 0 # changes what monitor gets scanned
scan_step = 1
cooldown = 0.6

health_region = (827, 1400, 828, 1401) # Health Bar
avatar_region = (1240, 1370, 1241, 1371) # Avatar
kill_region = (2545, 100, 2546, 680) # Kill Feed

folder_path = "images"
image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")
all_files = os.listdir(folder_path) 
images = [f for f in all_files if f.lower().endswith(image_extensions)]

pygame.mixer.init()
sound = pygame.mixer.Sound("sound-effect.wav")   

class ImageWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Image Pop-Up")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(alignment=Qt.AlignCenter)
        layout.addWidget(self.image_label)
        self.setLayout(layout)
 
        # Opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.image_label.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        # Animations
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.setDuration(500)

        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(500)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self.hide)

    def random_image_logic(self):
        image_path = select_random_image()
        pixmap = QPixmap(image_path)

        max_px_size = 1000  # pixels
        min_px_size = 800
        if pixmap.width() > max_px_size or pixmap.height() > max_px_size:
            pixmap = pixmap.scaled(max_px_size, max_px_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif pixmap.width() < min_px_size or pixmap.height() < min_px_size:
            pixmap = pixmap.scaled(min_px_size, min_px_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.image_label.setPixmap(pixmap)
        self.resize(pixmap.size())

        # Center after resizing (ensures geometry is updated)
        QTimer.singleShot(0, self.center_on_screen)
        print(f"📷 Displaying Image: {image_path} ({pixmap.width()}x{pixmap.height()})")

    def center_on_screen(self):
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        window_geo = self.frameGeometry()
        window_geo.moveCenter(screen_geo.center())
        self.move(window_geo.topLeft())

    def show_image(self):
        self.random_image_logic()

        self.opacity_effect.setOpacity(0)
        sound.play() # Plays 'sound-effect.wav'
        self.show()
        self.fade_in.start()
        QTimer.singleShot(350, self.fade_out.start)

def select_random_image():
        if not images:
            print("🚫 No image files found in folder.")
            return None

        random_image = random.choice(images)
        return os.path.join(folder_path, random_image)

def color_match(frame, color_white, color_red, tolerance, step):
    sampled = frame[::step, ::step, :3]
    diff = numpy.abs(sampled - color_white)
    diff = numpy.abs(sampled - color_red)
    mask = numpy.all(diff <= tolerance, axis=-1)
    return numpy.any(mask)

class RGBScanner(QThread):
    trigger_detected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_click_time = 0
        self.click_window = 0.5  # seconds allowed after a click
        self.last_trigger_time = 0

        # Register a one-time click listener
        mouse.on_click(self.on_mouse_click)

    def on_mouse_click(self):
        self.last_click_time = time.time()

    def run(self):
        print("🔷 Starting...")
        cam = dxcam.create(device_idx=monitor_index, output_idx=monitor_index)

        while True:
            frame_bottom_left = cam.grab(region=health_region)
            frame_top_right = cam.grab(region=avatar_region)
            frame_top_right = cam.grab(region=kill_region)

            if frame_bottom_left is None or frame_top_right is None:
                continue

            bottom_has_white = color_match(frame_bottom_left, target_value_white, target_value_white, tolerance_white, scan_step)
            bottom_left_has_white = color_match(frame_bottom_left, target_value_white, target_value_white, tolerance_white, scan_step)
            top_right_has_red = color_match(frame_top_right, target_value_red, target_value_red, tolerance_red, scan_step)

            # ✅ Trigger only when both RGB colors found AND recent click occurred
            now = time.time()
            if bottom_has_white and bottom_left_has_white and top_right_has_red:
                if now - self.last_click_time <= self.click_window:
                    if now - self.last_trigger_time > cooldown:
                        self.last_trigger_time = now
                        print("\n💀 Kill Detected!")
                        self.trigger_detected.emit()

            time.sleep(0.05)