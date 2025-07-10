import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QToolBar
from PyQt6.QtCore import Qt
from widgets.main_window import MainAppWindow
from modules.shader_manager import shader_manager
from modules.map_engine import MapEngine2D

app = QApplication(sys.argv)
engine = MapEngine2D()
window = MainAppWindow(engine, title="PyQt6 App", size=(800, 600))

def startup_tasks():
    pass

def main():
    startup_tasks()
    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()
