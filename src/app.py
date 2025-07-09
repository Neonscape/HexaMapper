import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QToolBar
from PyQt6.QtCore import Qt
from widgets.main_window import MainAppWindow

app = QApplication(sys.argv)
window = MainAppWindow(title="PyQt6 App", size=(800, 600))

def main():
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
