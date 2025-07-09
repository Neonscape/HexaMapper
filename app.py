import sys
from PyQt6.QtWidgets import QApplication
from widgets.main_window import MainAppWindow
from modules.config import load_config

load_config()

app = QApplication(sys.argv)
window = MainAppWindow(title="HexMapper", size=(800, 600))

def main():
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
