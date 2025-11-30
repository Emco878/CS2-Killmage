from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import (QTimer, Qt, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal)
import os, time, numpy, dxcam, pygame, random, mouse

target_value_ct = (255, 255, 255)   # CT has a different RGB Value compared to T
target_value_t = (255, 255, 192)    # T has a different RGB Value compared to CT    
target_value_red = (225, 1, 1)
tolerance_white = 0
tolerance_red = 5
monitor_index = 0 # changes what monitor gets scanned
scan_step = 1
cooldown = 0.6

health_region = (828, 1400, 829, 1401) # Health Bar
avatar_region = (1304, 1402, 1305, 1403) # Avatar
kill_region = (2545, 100, 2546, 680) # Kill Feed

folder_path = "images"
image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp")
all_files = os.listdir(folder_path) 
images = [f for f in all_files if f.lower().endswith(image_extensions)]

pygame.mixer.init()
sound = pygame.mixer.Sound("sound-effect.wav")   
mute_audio = False

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
        print(f"\n📷 Displaying Image: {image_path} ({pixmap.width()}x{pixmap.height()})")

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

        if not mute_audio:
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

def color_match(frame, color1, color2, tolerance, step):
    sampled = frame[::step, ::step, :3]
    diff1 = numpy.abs(sampled - color1)
    diff2 = numpy.abs(sampled - color2)
    mask1 = numpy.all(diff1 <= tolerance, axis=-1)
    mask2 = numpy.all(diff2 <= tolerance, axis=-1)
    return numpy.any(mask1) or numpy.any(mask2)


class RGBScanner(QThread):
    trigger_detected = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_click_time = 0
        self.click_window = 1.0       # seconds allowed after a click
        self.last_trigger_time = 0
        self.cooldown = 0.5           # minimum delay between triggers
        self.running = True
        self.cam = None

        # Register a one-time mouse click listener
        mouse.on_click(self.on_mouse_click)

    def on_mouse_click(self):
        """Called when the user clicks the mouse."""
        self.last_click_time = time.time()

    def stop(self):
        """Stop scanning and release DXCam safely."""
        self.running = False
        if self.cam:
            try:
                self.cam.stop()
            except Exception:
                pass
        self.cam = None

    def run(self):
        print("🔷 Program Started!")

        # Initialize DXCam
        try:
            self.cam = dxcam.create(device_idx=monitor_index, output_idx=monitor_index)
            if not self.cam:
                print("⚠️ Failed to initialize DXCam capture.")
                return
        except Exception as e:
            print(f"❌ DXCam initialization failed: {e}")
            return

        try:
            while self.running:
                try:
                    # --- Capture one full frame ---
                    frame = self.cam.grab()
                    if frame is None:
                        time.sleep(0.05)
                        continue

                    frame_health = frame[health_region[1]:health_region[3], health_region[0]:health_region[2]]
                    frame_avatar = frame[avatar_region[1]:avatar_region[3], avatar_region[0]:avatar_region[2]]
                    frame_kill   = frame[kill_region[1]:kill_region[3], kill_region[0]:kill_region[2]]

                    if any(r.size == 0 for r in (frame_health, frame_avatar, frame_kill)):
                        time.sleep(0.05)
                        continue

                    # --- Color detection ---
                    health_has_white = color_match(frame_health, target_value_ct, target_value_t, tolerance_white, scan_step)
                    avatar_has_white = color_match(frame_avatar, target_value_ct, target_value_t, tolerance_white, scan_step)
                    kill_has_red = color_match(frame_kill, target_value_red, target_value_red, tolerance_red, scan_step)

                    now = time.time()

                    # --- Detection logic ---
                    if health_has_white and avatar_has_white and kill_has_red:
                        if now - self.last_click_time <= self.click_window:
                            if now - self.last_trigger_time > self.cooldown:
                                self.last_trigger_time = now
                                print("💀 Kill Detected!")
                                self.trigger_detected.emit()
                                time.sleep(cooldown)

                    time.sleep(0.05)

                except Exception as e:
                    print(f"⚠️ Error in scan loop: {e}")
                    time.sleep(0.2)
                    continue

        except Exception as e:
            print(f"🚨 Fatal scanner error: {e}")

        finally:
            self.stop()
            print("🛑 Scanner stopped safely.")