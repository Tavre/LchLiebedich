#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SiliconUI组件的基本功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

# 导入SiliconUI组件
try:
    import siui
    from siui.components.widgets.button import SiPushButton
    from siui.components.widgets.container import SiDenseVContainer
    from siui.components.widgets.label import SiLabel
    print("SiliconUI导入成功")
except ImportError as e:
    print(f"SiliconUI导入失败: {e}")
    sys.exit(1)

class TestSiUIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SiliconUI 测试窗口")
        self.setGeometry(300, 300, 400, 300)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建SiliconUI标签
        try:
            label = SiLabel()
            label.setText("这是一个SiliconUI标签")
            layout.addWidget(label)
            
            # 创建SiliconUI按钮
            button = SiPushButton()
            button.attachment().setText("SiliconUI按钮")
            button.clicked.connect(self.on_button_clicked)
            layout.addWidget(button)
            
            print("SiliconUI组件创建成功")
        except Exception as e:
            print(f"创建SiliconUI组件失败: {e}")
    
    def on_button_clicked(self):
        print("SiliconUI按钮被点击")

def main():
    app = QApplication(sys.argv)
    
    # 测试窗口
    window = TestSiUIWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()