import main
from main import RGBScanner, ImageWindow

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QTextEdit, QLabel
from PyQt5.QtCore import Qt, QTimer

import sys, subprocess, os, pyautogui

class EmittingStream:
    def __init__(self, console):
        self.console = console
    def write(self, text):
        if text.strip():
            self.console.append(text)
            self.console.moveCursor(self.console.textCursor().End)  # Auto Scrolls to the Bottom
    def flush(self):
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CS2 Killmage")
        self.resize(700, 600)
        self.setStyleSheet("background-color: #242424")
        self.setFixedSize(self.width(), self.height())

        self.title = self.create_label("CS2 Killmage", 0, 12, 700 , 50)
        self.title.setStyleSheet("""font-size: 30px; font-family: "Segoe UI"; font-weight: bold; background: transparent; color: #FFFFFF;""")
        self.title.setAlignment(Qt.AlignCenter)

        #* Console *#
        self.console = self.create_textbox(325, 75, 330, 360)
        sys.stdout = EmittingStream(self.console)

        #* Tolerance *#
        self.title = self.create_label("Tolerance:", 50, 75, 180, 40)
        self.tolerance_value = self.create_line_edit(170, 75, 75, 40)
        self.tolerance_value.setPlaceholderText("Ex. 85")

        #* Health Region *#
        self.title = self.create_label("Health Region:", 50, 125, 185, 40)
        self.health_region_value = self.create_line_edit(50, 165, 225, 40)
        self.health_region_value.setPlaceholderText("x1, y1, x2, y2")

        #* Avatar Region *#
        self.title = self.create_label("Avatar Region:", 50, 215, 180, 40)
        self.avatar_region_value = self.create_line_edit(50, 255, 225, 40)
        self.avatar_region_value.setPlaceholderText("x1, y1, x2, y2")

        #* Kill Feed Region *#
        self.title = self.create_label("Kill Region:", 50, 305, 180, 40)
        self.kill_region_value = self.create_line_edit(50, 345, 225, 40)
        self.kill_region_value.setPlaceholderText("x1, y1, x2, y2")

        #* Resolution Buttons *#
        self.resolution_button = self.create_button("🖥️ Resolution", 375, 525, 225, 40)
        self.resolution_button.clicked.connect(self.resolution_1440p_change)

        self.resolution_1440p = self.create_button("🖥️ 2560 x 1440", 375, 525, 225, 40)
        self.resolution_1440p.clicked.connect(self.resolution_1080p_change)
        self.resolution_1440p.hide()

        self.resolution_1080p = self.create_button("🖥️ 1920 x 1080", 375, 525, 225, 40)
        self.resolution_1080p.clicked.connect(self.resolution_720p_change)
        self.resolution_1080p.hide()
        
        self.resolution_720p = self.create_button("🖥️ 1280 x 720", 375, 525, 225, 40)
        self.resolution_720p.clicked.connect(self.resolution_1440p_change)
        self.resolution_720p.hide()

        #* SAVE Button *#
        self.save_button = self.create_button("Save", 50, 450, 225, 60)
        self.save_button.clicked.connect(self.save_settings)

        #* START Button *#
        self.start_button = self.create_button("START", 325, 450, 330, 60)
        self.start_button.clicked.connect(self.start_program)

        #* STOP Button *#
        self.stop_button = self.create_button("STOP", 325, 450, 330, 60)
        self.stop_button.hide()
        self.stop_button.clicked.connect(self.stop_program)

        #* X & Y Coordinate *#
        self.pixel_locator()
        self.load_settings()
        self.x_coordinate = self.create_label("X: ", 60, 520, 130, 45)
        self.y_coordinate = self.create_label("Y: ", 60, 550, 130, 45)

        #* Folder Button *#
        self.folder_button = self.create_button("📁", 650, 550, 35, 35)
        self.folder_button.setStyleSheet("""QPushButton {font-size: 22px; background: transparent; color: #FFFFFF; border-radius: 8px;}""")
        self.folder_button.clicked.connect(self.folder_location)

    def start_program(self):
        self.start_button.hide()
        self.stop_button.show()

        main.tolerance_white = int(self.tolerance_value.text()) # Grabs the Tolerance Value from GUI and applies it to Main.py
        main.health_region = tuple(map(int, self.health_region_value.text().split(',')))
        main.avatar_region = tuple(map(int, self.avatar_region_value.text().split(',')))
        main.kill_region = tuple(map(int, self.kill_region_value.text().split(',')))

        # Initialize image window
        self.image_window = ImageWindow()
        self.scanner = RGBScanner()
        self.scanner.trigger_detected.connect(self.image_window.show_image)
        self.scanner.start()

    def stop_program(self):
        self.start_button.show()
        self.stop_button.hide()

        if hasattr(self, "scanner") and self.scanner.isRunning():
            # self.scanner.requestInterruption()  # asks the thread to stop
            self.scanner.terminate()            # force stops if it doesn’t respond
            self.scanner.wait()                 # waits for the thread to finish
            print("🛑 Program Stopped!")

    def save_settings(self):
        with open("settings.txt", "w") as f:
            f.write(f"tolerance_white={self.tolerance_value.text()}\n")
            f.write(f"health_region={self.health_region_value.text()}\n")
            f.write(f"avatar_region={self.avatar_region_value.text()}\n")
            f.write(f"kill_region={self.kill_region_value.text()}\n")
        print("💾 Settings saved!")

    def load_settings(self):

        if not os.path.exists("settings.txt"):
            print("⚙️ No settings file found, using defaults.")
            return

        with open("settings.txt", "r") as f:
            for line in f:
                if "=" not in line:
                    continue
                key, value = line.strip().split("=", 1)
                if key == "tolerance_white":
                    self.tolerance_value.setText(value)
                elif key == "health_region":
                    self.health_region_value.setText(value)
                elif key == "avatar_region":
                    self.avatar_region_value.setText(value)
                elif key == "kill_region":
                    self.kill_region_value.setText(value)
        print("✅ Settings loaded!")

    def resolution_1440p_change(self):
        self.health_region_value.setText("827, 1400, 828, 1401")
        self.avatar_region_value.setText("1278, 1356, 1279, 1357")
        self.kill_region_value.setText("2545, 100, 2546, 680")
        self.resolution_button.hide()
        self.resolution_720p.hide()
        self.resolution_1440p.show()

    def resolution_1080p_change(self):
        self.health_region_value.setText("620, 1050, 621, 1051")
        self.avatar_region_value.setText("959, 1017, 960, 1018")
        self.kill_region_value.setText("1910, 75, 1911, 510")
        self.resolution_1440p.hide()
        self.resolution_1080p.show()

    def resolution_720p_change(self):
        self.health_region_value.setText("414, 700, 415, 701")
        self.avatar_region_value.setText("639, 678, 640, 679")
        self.kill_region_value.setText("1273, 50, 1274, 340")
        self.resolution_1080p.hide()
        self.resolution_720p.show()

    def folder_location(self):
        print("📂 Folder Opened!")
        folder_path = os.path.dirname(os.path.abspath(sys.argv[0]))  # Program folder
        if sys.platform == "win32":
            subprocess.Popen(f'explorer "{folder_path}"')

    def pixel_locator(self):
        def update_coords():
            x, y = pyautogui.position()
            self.x_coordinate.setText(f"X: {x}")
            self.y_coordinate.setText(f"Y: {y}")

        # Create and start a QTimer (50 ms refresh)
        self.coord_timer = QTimer()
        self.coord_timer.timeout.connect(update_coords)
        self.coord_timer.start(1)

    # ---- Function to create a Label ---- #
    def create_label(self, text, x, y, width, height):
        label = QLabel(text, self)
        label.setGeometry(x, y, width, height)
        label.setAlignment(Qt.AlignLeft)
        label.setStyleSheet("""font-size: 25px; font-family: "Segoe UI"; background: transparent; color: #FFFFFF;""")
        return label

    # ---- Function to create a Button ---- #
    def create_button(self, text, x, y, width, height):
        button = QPushButton(text, self)
        button.setGeometry(x, y, width, height)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet("""
        QPushButton {font-size: 22px; font-family: "Segoe UI"; background: #1E1E1E; color: #FFFFFF; border: 2px solid #FFFFFF; border-radius: 8px; padding-left: 3px;}
        QPushButton:hover {background-color: #444444;}
        """)
        return button

    # ---- Function to create a Line_Edit ---- #
    def create_line_edit(self, x, y, width, height):
        line_edit = QLineEdit(self)
        line_edit.setGeometry(x, y, width, height)
        line_edit.setStyleSheet("""font-size: 18px; font-family: "Segoe UI"; color: #FFFFFF; border: 2px solid #FFFFFF; border-radius: 8px; padding-left: 4px;""")
        line_edit.setContextMenuPolicy(Qt.NoContextMenu)
        line_edit.setAlignment(Qt.AlignCenter)
        return line_edit

    # ---- Function to create a Text_box ---- #
    def create_textbox(self, x, y, width, height):
        text_box = QTextEdit(self)
        text_box.setReadOnly(True)
        text_box.setGeometry(x, y, width, height)
        text_box.setStyleSheet("""font-size: 14px; font-family: "Segoe UI"; color: #FFFFFF; border: 2px solid #FFFFFF; border-radius: 8px; padding-left: 4px;""")
        text_box.setContextMenuPolicy(Qt.NoContextMenu)
        return text_box

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

#TODO: Make Text Boxes Int Values only. Make the DXCam error go away.