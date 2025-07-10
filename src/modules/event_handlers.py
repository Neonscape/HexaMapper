from typing import override, Literal, Optional
from PyQt6.QtCore import QObject, QEvent, Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QWheelEvent

class MapPanel2DEventHandler(QObject):
    @override
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.last_mouse_pos = QPoint()
        self.dragging = False
        self.drag_button: Optional[Literal['Left', 'Right', 'Middle']] = None

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Intercepts events for the objects it's installed on.
        
        Args:
            obj: The QObject for which the event was generated.
            event: The QEvent object.
        
        Returns:
            True if the event was handled and should not be processed further.
            False if the event should continue to be processed by the target object.
        """
        
        # --- Handle Mouse Press Events ---
        if event.type() == QEvent.Type.MouseButtonPress:
            mouse_event: QMouseEvent = event # Cast to QMouseEvent for specific properties
            
            self.last_mouse_pos = mouse_event.pos()
            self.dragging = True
            
            if mouse_event.buttons() & Qt.MouseButton.LeftButton:
                self.drag_button = "Left"
            elif mouse_event.buttons() & Qt.MouseButton.RightButton:
                self.drag_button = "Right"
            elif mouse_event.buttons() & Qt.MouseButton.MiddleButton:
                self.drag_button = "Middle"
            
            # Return False to allow the target widget to also receive the press event
            return False 

        # --- Handle Mouse Release Events ---
        elif event.type() == QEvent.Type.MouseButtonRelease:
            mouse_event: QMouseEvent = event
            self.dragging = False
            self.drag_button = None
            
            return False # Allow target widget to receive release event

        # --- Handle Mouse Move Events (for drag and hover) ---
        elif event.type() == QEvent.Type.MouseMove:
            mouse_event: QMouseEvent = event
            
            current_pos = mouse_event.pos()
            
            if self.drag_button == "Left" and self.dragging:
                self.engine.move_view(self.last_mouse_pos, current_pos)
            elif self.drag_button == "Right" and self.dragging:
                import numpy as np
                
                color = np.random.rand(4).astype(np.float32)
                color[3] = 1.0
                self.engine.paint_on_screen(current_pos, color)
            else: # Mouse moved without any button pressed (due to setMouseTracking(True) on widget)
                pass
            
            return False # Allow target widget to receive move event

        # --- Handle Mouse Wheel Events ---
        elif event.type() == QEvent.Type.Wheel:
            wheel_event: QWheelEvent = event
            angle_delta_y = wheel_event.angleDelta().y()
            pixel_delta_y = wheel_event.pixelDelta().y()

            if angle_delta_y > 0:
                scroll_direction = "Up (away from user)"
            else:
                scroll_direction = "Down (towards user)"

            return True # Consume the wheel event; prevent target widget from processing it further

        # Default: For all other event types, pass them through
        return super().eventFilter(obj, event)