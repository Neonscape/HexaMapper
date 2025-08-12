from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from qtpy.QtCore import Qt
from widgets.controllers.controller_base import BaseController
from widgets.map_widget import MapWidget

class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_control = None
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        self.title_label = QLabel("Properties")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.layout.addWidget(self.title_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(8)
        self.layout.addWidget(self.content_widget)
        
        # 初始状态显示提示
        self.show_hint("No widget selected")
    
    def show_hint(self, text):
        """显示提示信息"""
        self.clear()
        hint_label = QLabel(text)
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: #888; font-style: italic;")
        self.content_layout.addWidget(hint_label)
    
    def clear(self):
        """清空内容区域"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def set_control(self, control: MapWidget):
        """设置当前控件并更新面板"""
        self.current_control = control
        self.clear()
        
        if control is None:
            self.show_hint("No widget selected")
            return
        
        # 显示控件类型
        type_label = QLabel(f"Widget type: {type(control).__name__}")
        type_label.setStyleSheet("font-weight: bold;")
        self.content_layout.addWidget(type_label)
        
        # 动态构建属性编辑器
        if hasattr(control, 'config') and control.config:
            self.build_property_editors(control.config)
    
    def build_property_editors(self, config):
        """根据配置动态构建属性编辑器"""
        for field_name, field_info in config.__fields__.items():
            field_type = field_info.type_
            field_value = getattr(config, field_name)
            
            # 创建控制器
            controller = BaseController.create_controller(
                field_name, 
                field_type, 
                field_value,
                field_info.field_info.description or field_name
            )
            
            if controller:
                # 连接值改变信号
                controller.valueChanged.connect(
                    lambda value, fn=field_name: self.on_property_changed(fn, value)
                )
                self.content_layout.addWidget(controller)
    
    def on_property_changed(self, property_name, value):
        """处理属性值改变"""
        if self.current_control and hasattr(self.current_control, 'config'):
            # 更新控件配置
            setattr(self.current_control.config, property_name, value)
            
            # 触发控件更新
            self.current_control.update()
            
            # 可选：添加到历史记录
            # 这里需要根据实际需求实现
