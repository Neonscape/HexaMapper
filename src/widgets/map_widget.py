from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtCore import QRectF, QPointF, Qt
from pydantic import BaseModel

class WidgetConfig(BaseModel):
    """控件配置基类，所有控件配置应继承此类"""
    pass

class MapWidget(QGraphicsItem):
    """地图控件基类，所有可交互控件应继承此类"""
    
    def __init__(self, config: WidgetConfig):
        super().__init__()
        self.config = config
        self.selected = False
        
    def hit_test(self, pos: QPointF) -> bool:
        """检测点击位置是否在控件范围内"""
        return self.boundingRect().contains(pos)
        
    def set_selected(self, selected: bool):
        """设置选中状态并触发重绘"""
        self.selected = selected
        self.update()
        
    def boundingRect(self) -> QRectF:
        """返回控件边界矩形，子类必须实现"""
        raise NotImplementedError("Subclasses must implement boundingRect")
        
    def paint(self, painter, option, widget):
        """基础渲染逻辑，子类可扩展"""
        if self.selected:
            # 绘制选中边框
            painter.setPen(Qt.GlobalColor.blue)
            painter.drawRect(self.boundingRect())
