from loguru import logger
from modules.map_engine import MapEngine2D
from modules.tools.base_tool import ToolBase
from widgets.map_widget import MapWidget
from qtpy.QtCore import QPointF

class SelectTool(ToolBase):
    def __init__(self, engine: MapEngine2D):
        super().__init__(engine)
        self.engine = engine
        self.name = "select_tool"
        self.tooltip = "选择工具"
        self.icon_name = "cursor_default"
        
    def get_settings(self) -> dict:
        """获取工具配置（选择工具没有配置项）"""
        return {}
    
    def mouse_press(self, event):
        """处理鼠标按下事件"""
        # 转换坐标到控件场景坐标系
        screen_pos = event.pos()
        scene_pos = self.engine.map_panel.screen_to_control_scene(screen_pos)
        
        # 检测命中控件
        items = self.engine.map_panel.control_scene.items(scene_pos)
        for item in items:
            if isinstance(item, MapWidget):
                # 清除之前的选择
                for other in self.engine.map_panel.control_scene.items():
                    if isinstance(other, MapWidget) and other != item:
                        other.set_selected(False)
                
                # 设置当前选中状态
                item.set_selected(True)
                
                logger.info(f"Selected object {item}.")
                
                # 更新属性面板
                main_window = self.engine.map_panel.window()
                if hasattr(main_window, 'properties_panel'):
                    main_window.properties_panel.set_control(item)
                
                # 消费事件，不传递给其他工具
                event.accept()
                return
        
        # 未命中控件时清除所有选择
        logger.info(f"Selected nothing.")
        for item in self.engine.map_panel.control_scene.items():
            if isinstance(item, MapWidget):
                item.set_selected(False)
        
        # 清除属性面板
        main_window = self.engine.map_panel.window()
        if hasattr(main_window, 'properties_panel'):
            main_window.properties_panel.clear()
