import sys
from PyQt6.QtWidgets import QApplication, QToolBar
from PyQt6.QtCore import Qt
from widgets.main_window import MainAppWindow
from modules.map_engine import MapEngine2D

app = QApplication(sys.argv)
engine = MapEngine2D()
window = MainAppWindow(engine)

def startup_tasks():
    """
    Performs any tasks required at application startup.
    """
    pass

def shutdown_tasks():
    """
    Performs any tasks required at application shutdown.
    """
    pass

def run():
    """
    Runs the main application loop.
    """
    startup_tasks()
    sys.exit(app.exec())
    shutdown_tasks()
    
if __name__ == "__main__":
    run()
