#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt5词库管理窗口模块
使用PyQt-SiliconUI主题的词库管理界面
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit,
    QLabel, QPushButton, QListWidget, QSplitter, QGroupBox,
    QGridLayout, QMessageBox, QFileDialog, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QMainWindow, QWidget, QProgressBar, QStatusBar, QToolBar,
    QAction, QHeaderView, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSortFilterProxyModel
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem

# 尝试导入SiliconUI组件
try:
    import siui
    from siui.components.widgets.button import SiPushButton
    from siui.components.widgets.line_edit import SiLineEdit
    SIUI_AVAILABLE = True
except ImportError:
    SIUI_AVAILABLE = False
    print("警告: SiliconUI未安装，将使用标准PyQt5组件")

import os
import json
from typing import Optional, Dict, List
from datetime import datetime

from ..wordlib.manager import LchliebedichWordLibManager
from ..utils.logger import get_logger

class WordLibWindowQt(QMainWindow):
    """PyQt5词库管理窗口类"""
    
    def __init__(self, wordlib_manager: LchliebedichWordLibManager, parent=None):
        super().__init__(parent)
        
        self.wordlib_manager = wordlib_manager
        self.logger = get_logger("WordLibWindowQt")
        
        # 当前选中的词库
        self.current_wordlib = None
        self.current_wordlib_path = None
        
        # 搜索和过滤相关
        self.search_text = ""
        self.filter_model = None
        
        self.setup_ui()
        self.setup_style()
        self.load_wordlib_list()
        
    def on_search_changed(self, text):
        """搜索文本改变时的处理"""
        self.search_text = text.lower()
        self.filter_wordlib_list()
        
    def filter_wordlib_list(self):
        """过滤词库列表"""
        for i in range(self.wordlib_list.topLevelItemCount()):
            item = self.wordlib_list.topLevelItem(i)
            if self.search_text == "" or self.search_text in item.text(0).lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
                
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.wordlib_list.itemAt(position)
        if item is None:
            return
            
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        # 编辑
        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(lambda: self.on_wordlib_selected(item, 0))
        
        # 重载
        reload_action = menu.addAction("重载")
        reload_action.triggered.connect(self.reload_wordlib)
        
        # 复制
        duplicate_action = menu.addAction("复制")
        duplicate_action.triggered.connect(self.duplicate_wordlib)
        
        menu.addSeparator()
        
        # 删除
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(self.delete_wordlib)
        
        menu.exec_(self.wordlib_list.mapToGlobal(position))
        
    def duplicate_wordlib(self):
        """复制词库"""
        current_item = self.wordlib_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要复制的词库")
            return
            
        try:
            original_name = current_item.text(0)
            new_name = f"{original_name}_副本"
            
            # 检查新名称是否已存在
            counter = 1
            while self.wordlib_manager.wordlib_exists(new_name):
                new_name = f"{original_name}_副本{counter}"
                counter += 1
                
            # 复制词库
            self.wordlib_manager.duplicate_wordlib(original_name, new_name)
            
            QMessageBox.information(self, "成功", f"词库已复制为: {new_name}")
            self.load_wordlib_list()
            self.logger.info(f"词库复制成功: {original_name} -> {new_name}")
            
        except Exception as e:
             QMessageBox.critical(self, "错误", f"复制词库失败: {e}")
             self.logger.error(f"复制词库失败: {e}")
             
    def delete_wordlib(self):
        """删除词库"""
        current_item = self.wordlib_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的词库")
            return
            
        wordlib_name = current_item.text(0)
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除词库 '{wordlib_name}' 吗？\n\n注意：此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            # 删除词库
            if hasattr(self.wordlib_manager, 'delete_wordlib'):
                self.wordlib_manager.delete_wordlib(wordlib_name)
            else:
                # 如果没有delete_wordlib方法，从配置中移除
                if hasattr(self.wordlib_manager, 'wordlibs') and wordlib_name in self.wordlib_manager.wordlibs:
                    del self.wordlib_manager.wordlibs[wordlib_name]
                    
            QMessageBox.information(self, "成功", f"词库 '{wordlib_name}' 已删除")
            self.load_wordlib_list()
            self.clear_wordlib_info()
            self.logger.info(f"词库删除成功: {wordlib_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除词库失败: {e}")
            self.logger.error(f"删除词库失败: {e}")
            
    def clear_wordlib_info(self):
        """清空词库信息显示"""
        self.wordlib_name_edit.clear()
        self.wordlib_path_edit.clear()
        self.wordlib_status_label.setText("未选择")
        self.wordlib_size_label.setText("0 B")
        
        # 禁用编辑按钮
        self.save_btn.setEnabled(False)
        self.reload_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        if hasattr(self, 'delete_wordlib_btn'):
            self.delete_wordlib_btn.setEnabled(False)
        if hasattr(self, 'duplicate_btn'):
            self.duplicate_btn.setEnabled(False)

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("词库管理器")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        # 创建工具栏
        self.setup_toolbar()
        
        # 创建主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 设置词库列表区域
        self.setup_wordlib_list(splitter)
        
        # 设置编辑区域
        self.setup_edit_area(splitter)
        
        # 设置分割器比例
        splitter.setSizes([350, 850])
        
        # 创建状态栏
        self.setup_status_bar()
        
    def setup_style(self):
        """设置样式"""
        # 根据是否有SiliconUI选择不同的样式
        if SIUI_AVAILABLE:
            # SiliconUI深色主题样式
            style = """
            QMainWindow {
                background-color: #1C191F;
                color: #E5E5E5;
            }
            QWidget {
                background-color: #1C191F;
                color: #E5E5E5;
            }
            QGroupBox {
                font-weight: bold;
                border: none;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #25222A;
                color: #E5E5E5;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #c58bc2;
            }
            QPushButton {
                background-color: #4C4554;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: #E5E5E5;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #855198;
                border: none;
            }
            QPushButton:pressed {
                background-color: #52389a;
            }
            QPushButton:disabled {
                background-color: #332E38;
                color: #979797;
                border: none;
            }
            QLineEdit {
                background-color: #332E38;
                border: none;
                border-radius: 4px;
                padding: 6px;
                color: #E5E5E5;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: none;
            }
            QTreeWidget {
                background-color: #332E38;
                border: none;
                border-radius: 4px;
                color: #E5E5E5;
                alternate-background-color: #403a46;
            }
            QTreeWidget::item:selected {
                background-color: #855198;
            }
            QTreeWidget::item:hover {
                background-color: #403a46;
            }
            QHeaderView::section {
                background-color: #4C4554;
                color: #E5E5E5;
                border: none;
                padding: 4px;
            }
            QTextEdit {
                background-color: #332E38;
                border: none;
                border-radius: 4px;
                color: #E5E5E5;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: none;
            }
            QLabel {
                color: #DFDFDF;
            }
            QToolBar {
                background-color: #25222A;
                border: none;
                color: #E5E5E5;
            }
            QStatusBar {
                background-color: #25222A;
                color: #DFDFDF;
                border: none;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #332E38;
                color: #E5E5E5;
            }
            QProgressBar::chunk {
                background-color: #855198;
                border-radius: 3px;
            }
            QMenu {
                background-color: #25222A;
                color: #E5E5E5;
                border: none;
            }
            QMenu::item:selected {
                background-color: #855198;
            }
            QScrollBar:vertical {
                background-color: #25222A;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #50FFFFFF;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #70FFFFFF;
            }
            QScrollBar:horizontal {
                background-color: #25222A;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #50FFFFFF;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #70FFFFFF;
            }
            """
        else:
            # 原有的深色主题样式
            style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: none;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QLineEdit {
                border: none;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
                background-color: #404040;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: none;
            }
            QTreeWidget {
                border: none;
                border-radius: 4px;
                background-color: #404040;
                alternate-background-color: #4a4a4a;
                color: #ffffff;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QTreeWidget::item:hover {
                background-color: #505050;
            }
            QHeaderView::section {
                background-color: #505050;
                color: #ffffff;
                padding: 4px;
                border: none;
            }
            QTextEdit {
                border: none;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }
            QLabel {
                color: #ffffff;
            }
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                color: #ffffff;
            }
            QStatusBar {
                background-color: #3c3c3c;
                color: #ffffff;
                border: none;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: none;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            QScrollBar:horizontal {
                background-color: #404040;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #666666;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #777777;
            }
            """
        self.setStyleSheet(style)
        
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setMovable(False)
        
        # 新建词库
        new_action = QAction("新建", self)
        new_action.setToolTip("创建新的词库文件")
        new_action.triggered.connect(self.new_wordlib)
        toolbar.addAction(new_action)
        
        # 导入词库
        import_action = QAction("导入", self)
        import_action.setToolTip("从文件导入词库")
        import_action.triggered.connect(self.import_wordlib)
        toolbar.addAction(import_action)
        
        # 导出词库
        export_action = QAction("导出", self)
        export_action.setToolTip("导出选中的词库")
        export_action.triggered.connect(self.export_wordlib)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # 刷新
        refresh_action = QAction("刷新", self)
        refresh_action.setToolTip("刷新词库列表")
        refresh_action.triggered.connect(self.load_wordlib_list)
        toolbar.addAction(refresh_action)
        
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("就绪")
        
    def setup_wordlib_list(self, parent):
        """设置词库列表区域"""
        # 创建词库列表容器
        wordlib_widget = QWidget()
        parent.addWidget(wordlib_widget)
        
        # 创建布局
        layout = QVBoxLayout(wordlib_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 词库列表组
        wordlib_group = QGroupBox("词库列表")
        layout.addWidget(wordlib_group)
        
        group_layout = QVBoxLayout(wordlib_group)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        if SIUI_AVAILABLE:
            self.search_input = SiLineEdit()
            self.search_input.lineEdit().setPlaceholderText("输入关键词搜索词库...")
            self.search_input.lineEdit().textChanged.connect(self.on_search_changed)
        else:
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("输入关键词搜索词库...")
            self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        group_layout.addLayout(search_layout)
        
        # 词库树形控件
        self.wordlib_list = QTreeWidget()
        self.wordlib_list.setHeaderLabels(["名称", "类型", "大小", "修改时间"])
        self.wordlib_list.setAlternatingRowColors(True)
        self.wordlib_list.setSortingEnabled(True)
        self.wordlib_list.itemClicked.connect(self.on_wordlib_selected)
        self.wordlib_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wordlib_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # 设置列宽
        header = self.wordlib_list.header()
        header.resizeSection(0, 150)  # 名称
        header.resizeSection(1, 80)   # 类型
        header.resizeSection(2, 80)   # 大小
        header.resizeSection(3, 120)  # 修改时间
        
        group_layout.addWidget(self.wordlib_list)
        
        # 词库操作按钮
        button_group = QGroupBox("操作")
        layout.addWidget(button_group)
        
        button_layout = QGridLayout(button_group)
        
        if SIUI_AVAILABLE:
            self.new_wordlib_btn = SiPushButton()
            self.new_wordlib_btn.attachment().setText("新建")
            self.new_wordlib_btn.setToolTip("创建新的词库文件")
            self.new_wordlib_btn.clicked.connect(self.new_wordlib)
            
            self.delete_wordlib_btn = SiPushButton()
            self.delete_wordlib_btn.attachment().setText("删除")
            self.delete_wordlib_btn.setToolTip("删除选中的词库")
            self.delete_wordlib_btn.clicked.connect(self.delete_wordlib)
            self.delete_wordlib_btn.setEnabled(False)
            
            self.refresh_btn = SiPushButton()
            self.refresh_btn.attachment().setText("刷新")
            self.refresh_btn.setToolTip("刷新词库列表")
            self.refresh_btn.clicked.connect(self.load_wordlib_list)
            
            self.duplicate_btn = SiPushButton()
            self.duplicate_btn.attachment().setText("复制")
            self.duplicate_btn.setToolTip("复制选中的词库")
        else:
            self.new_wordlib_btn = QPushButton("新建")
            self.new_wordlib_btn.setToolTip("创建新的词库文件")
            self.new_wordlib_btn.clicked.connect(self.new_wordlib)
            
            self.delete_wordlib_btn = QPushButton("删除")
            self.delete_wordlib_btn.setToolTip("删除选中的词库")
            self.delete_wordlib_btn.clicked.connect(self.delete_wordlib)
            self.delete_wordlib_btn.setEnabled(False)
            
            self.refresh_btn = QPushButton("刷新")
            self.refresh_btn.setToolTip("刷新词库列表")
            self.refresh_btn.clicked.connect(self.load_wordlib_list)
            
            self.duplicate_btn = QPushButton("复制")
            self.duplicate_btn.setToolTip("复制选中的词库")
        
        button_layout.addWidget(self.new_wordlib_btn, 0, 0)
        button_layout.addWidget(self.delete_wordlib_btn, 0, 1)
        button_layout.addWidget(self.refresh_btn, 1, 0)
        self.duplicate_btn.clicked.connect(self.duplicate_wordlib)
        self.duplicate_btn.setEnabled(False)
        button_layout.addWidget(self.duplicate_btn, 1, 1)
        
        # 统计信息
        stats_group = QGroupBox("统计信息")
        layout.addWidget(stats_group)
        
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("词库总数: 0\n总词条: 0")
        self.stats_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.stats_label)
        
    def setup_edit_area(self, parent):
        """设置编辑区域"""
        # 右侧容器
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 词库信息区域
        self.setup_wordlib_info(right_layout)
        
        # 编辑区域
        self.setup_editor(right_layout)
        
        # 操作按钮
        self.setup_edit_buttons(right_layout)
        
        parent.addWidget(right_widget)
        
    def setup_wordlib_info(self, parent_layout):
        """设置词库信息区域"""
        info_group = QGroupBox("词库信息")
        info_layout = QGridLayout(info_group)
        
        # 词库名称
        info_layout.addWidget(QLabel("名称:"), 0, 0)
        if SIUI_AVAILABLE:
            self.wordlib_name_edit = SiLineEdit()
            self.wordlib_name_edit.lineEdit().setReadOnly(True)
        else:
            self.wordlib_name_edit = QLineEdit()
            self.wordlib_name_edit.setReadOnly(True)
        info_layout.addWidget(self.wordlib_name_edit, 0, 1)
        
        # 词库路径
        info_layout.addWidget(QLabel("路径:"), 1, 0)
        if SIUI_AVAILABLE:
            self.wordlib_path_edit = SiLineEdit()
            self.wordlib_path_edit.lineEdit().setReadOnly(True)
        else:
            self.wordlib_path_edit = QLineEdit()
            self.wordlib_path_edit.setReadOnly(True)
        info_layout.addWidget(self.wordlib_path_edit, 1, 1)
        
        # 词库状态
        info_layout.addWidget(QLabel("状态:"), 2, 0)
        self.wordlib_status_label = QLabel("未选择")
        info_layout.addWidget(self.wordlib_status_label, 2, 1)
        
        # 词库大小
        info_layout.addWidget(QLabel("大小:"), 3, 0)
        self.wordlib_size_label = QLabel("0 B")
        info_layout.addWidget(self.wordlib_size_label, 3, 1)
        
        parent_layout.addWidget(info_group)
        
    def setup_editor(self, parent_layout):
        """设置编辑器"""
        editor_group = QGroupBox("词库内容")
        editor_layout = QVBoxLayout(editor_group)
        
        # 编辑器
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setPlaceholderText("请选择一个词库进行编辑...")
        self.editor.textChanged.connect(self.on_content_changed)
        editor_layout.addWidget(self.editor)
        
        parent_layout.addWidget(editor_group)
        
    def setup_edit_buttons(self, parent_layout):
        """设置编辑按钮"""
        btn_layout = QHBoxLayout()
        
        if SIUI_AVAILABLE:
            self.save_btn = SiPushButton()
            self.save_btn.attachment().setText("保存")
            self.save_btn.clicked.connect(self.save_wordlib)
            self.save_btn.setEnabled(False)
            
            self.reload_btn = SiPushButton()
            self.reload_btn.attachment().setText("重载")
            self.reload_btn.clicked.connect(self.reload_wordlib)
            self.reload_btn.setEnabled(False)
            
            self.import_btn = SiPushButton()
            self.import_btn.attachment().setText("导入")
            self.import_btn.clicked.connect(self.import_wordlib)
            
            self.export_btn = SiPushButton()
            self.export_btn.attachment().setText("导出")
            self.export_btn.clicked.connect(self.export_wordlib)
            self.export_btn.setEnabled(False)
        else:
            self.save_btn = QPushButton("保存")
            self.save_btn.clicked.connect(self.save_wordlib)
            self.save_btn.setEnabled(False)
            
            self.reload_btn = QPushButton("重载")
            self.reload_btn.clicked.connect(self.reload_wordlib)
            self.reload_btn.setEnabled(False)
            
            self.import_btn = QPushButton("导入")
            self.import_btn.clicked.connect(self.import_wordlib)
            
            self.export_btn = QPushButton("导出")
            self.export_btn.clicked.connect(self.export_wordlib)
            self.export_btn.setEnabled(False)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reload_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.export_btn)
        
        parent_layout.addLayout(btn_layout)
        
    def load_wordlib_list(self):
        """加载词库列表"""
        try:
            self.wordlib_list.clear()
            
            if not self.wordlib_manager:
                return
                
            # 获取词库列表
            if hasattr(self.wordlib_manager, 'get_wordlib_list'):
                wordlibs = self.wordlib_manager.get_wordlib_list()
            else:
                # 如果没有get_wordlib_list方法，尝试从配置中获取
                wordlibs = []
                if hasattr(self.wordlib_manager, 'wordlibs'):
                    for name, wordlib in self.wordlib_manager.wordlibs.items():
                        import os
                        from datetime import datetime
                        
                        # 获取文件信息
                        file_path = wordlib.get('path', '')
                        file_size = 0
                        modified_time = "未知"
                        
                        if file_path and os.path.exists(file_path):
                            try:
                                stat = os.stat(file_path)
                                file_size = stat.st_size
                                modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                        
                        wordlibs.append({
                            'name': name,
                            'status': wordlib.get('enabled', True) and '启用' or '禁用',
                            'size': file_size,
                            'modified': modified_time,
                            'path': file_path
                        })
            
            for wordlib_info in wordlibs:
                item = QTreeWidgetItem()
                item.setText(0, wordlib_info.get('name', '未知'))
                item.setText(1, wordlib_info.get('status', '未知'))
                
                # 格式化文件大小
                size = wordlib_info.get('size', 0)
                if size > 1024 * 1024:
                    size_text = f"{size / (1024 * 1024):.1f} MB"
                elif size > 1024:
                    size_text = f"{size / 1024:.1f} KB"
                else:
                    size_text = f"{size} B"
                item.setText(2, size_text)
                
                # 修改时间
                item.setText(3, wordlib_info.get('modified', '未知'))
                
                # 存储完整信息
                item.setData(0, Qt.UserRole, wordlib_info)
                
                self.wordlib_list.addTopLevelItem(item)
                
            # 更新统计信息
            total_words = sum(1 for w in wordlibs if w.get('status') == '启用')
            self.stats_label.setText(f"词库总数: {len(wordlibs)}\n启用词库: {total_words}")
                
            self.logger.info(f"已加载 {len(wordlibs)} 个词库")
            
        except Exception as e:
            self.logger.error(f"加载词库列表失败: {e}")
            QMessageBox.critical(self, "错误", f"加载词库列表失败: {e}")
            
    def on_wordlib_selected(self, item, column):
        """词库选择事件"""
        try:
            wordlib_info = item.data(0, Qt.UserRole)
            if not wordlib_info:
                return
                
            self.current_wordlib = wordlib_info
            self.current_wordlib_path = wordlib_info.get('path')
            
            # 更新词库信息
            self.wordlib_name_edit.setText(wordlib_info.get('name', ''))
            self.wordlib_path_edit.setText(wordlib_info.get('path', ''))
            self.wordlib_status_label.setText(wordlib_info.get('status', '未知'))
            
            # 格式化文件大小
            size = wordlib_info.get('size', 0)
            if size > 1024 * 1024:
                size_text = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_text = f"{size / 1024:.1f} KB"
            else:
                size_text = f"{size} B"
            self.wordlib_size_label.setText(size_text)
            
            # 加载词库内容
            self.load_wordlib_content()
            
            # 启用相关按钮
            self.reload_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.delete_wordlib_btn.setEnabled(True)
            self.duplicate_btn.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"选择词库失败: {e}")
            QMessageBox.critical(self, "错误", f"选择词库失败: {e}")
            
    def load_wordlib_content(self):
        """加载词库内容"""
        try:
            if not self.current_wordlib_path or not os.path.exists(self.current_wordlib_path):
                self.editor.setPlainText("词库文件不存在")
                return
                
            with open(self.current_wordlib_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.editor.setPlainText(content)
            self.logger.info(f"已加载词库内容: {self.current_wordlib_path}")
            
        except Exception as e:
            self.logger.error(f"加载词库内容失败: {e}")
            self.editor.setPlainText(f"加载失败: {e}")
            
    def on_content_changed(self):
        """内容变更事件"""
        if self.current_wordlib_path:
            self.save_btn.setEnabled(True)
            
    def save_wordlib(self):
        """保存词库"""
        try:
            if not self.current_wordlib_path:
                QMessageBox.warning(self, "警告", "请先选择一个词库")
                return
                
            content = self.editor.toPlainText()
            
            with open(self.current_wordlib_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.save_btn.setEnabled(False)
            QMessageBox.information(self, "成功", "词库保存成功")
            self.logger.info(f"词库保存成功: {self.current_wordlib_path}")
            
            # 刷新列表
            self.load_wordlib_list()
            
        except Exception as e:
            self.logger.error(f"保存词库失败: {e}")
            QMessageBox.critical(self, "错误", f"保存词库失败: {e}")
            
    def reload_wordlib(self):
        """重载词库"""
        try:
            if not self.current_wordlib_path:
                QMessageBox.warning(self, "警告", "请先选择一个词库")
                return
                
            # 重新加载内容
            self.load_wordlib_content()
            
            # 通知词库管理器重载
            if self.wordlib_manager:
                self.wordlib_manager.reload_wordlib(self.current_wordlib_path)
                
            QMessageBox.information(self, "成功", "词库重载成功")
            self.logger.info(f"词库重载成功: {self.current_wordlib_path}")
            
        except Exception as e:
            self.logger.error(f"重载词库失败: {e}")
            QMessageBox.critical(self, "错误", f"重载词库失败: {e}")
            
    def new_wordlib(self):
        """新建词库"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "新建词库", "", "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if file_path:
                # 创建空文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("# 新建词库\n# 请在此处编写词库内容\n")
                    
                QMessageBox.information(self, "成功", f"词库创建成功: {file_path}")
                self.logger.info(f"词库创建成功: {file_path}")
                
                # 刷新列表
                self.load_wordlib_list()
                
        except Exception as e:
            self.logger.error(f"创建词库失败: {e}")
            QMessageBox.critical(self, "错误", f"创建词库失败: {e}")
            
    def delete_wordlib(self):
        """删除词库"""
        try:
            if not self.current_wordlib_path:
                QMessageBox.warning(self, "警告", "请先选择一个词库")
                return
                
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除词库 '{self.current_wordlib.get('name', '')}' 吗？\n\n此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                os.remove(self.current_wordlib_path)
                QMessageBox.information(self, "成功", "词库删除成功")
                self.logger.info(f"词库删除成功: {self.current_wordlib_path}")
                
                # 清空编辑器
                self.editor.clear()
                self.current_wordlib = None
                self.current_wordlib_path = None
                
                # 禁用按钮
                self.save_btn.setEnabled(False)
                self.reload_btn.setEnabled(False)
                self.export_btn.setEnabled(False)
                
                # 刷新列表
                self.load_wordlib_list()
                
        except Exception as e:
            self.logger.error(f"删除词库失败: {e}")
            QMessageBox.critical(self, "错误", f"删除词库失败: {e}")
            
    def import_wordlib(self):
        """导入词库"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入词库", "", "文本文件 (*.txt);;JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if file_path:
                # 选择目标位置
                target_path, _ = QFileDialog.getSaveFileName(
                    self, "保存到", os.path.basename(file_path), "文本文件 (*.txt);;所有文件 (*.*)"
                )
                
                if target_path:
                    # 复制文件
                    import shutil
                    shutil.copy2(file_path, target_path)
                    
                    QMessageBox.information(self, "成功", f"词库导入成功: {target_path}")
                    self.logger.info(f"词库导入成功: {file_path} -> {target_path}")
                    
                    # 刷新列表
                    self.load_wordlib_list()
                    
        except Exception as e:
            self.logger.error(f"导入词库失败: {e}")
            QMessageBox.critical(self, "错误", f"导入词库失败: {e}")
            
    def export_wordlib(self):
        """导出词库"""
        try:
            if not self.current_wordlib_path:
                QMessageBox.warning(self, "警告", "请先选择一个词库")
                return
                
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出词库", 
                f"{self.current_wordlib.get('name', 'wordlib')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if file_path:
                # 复制文件
                import shutil
                shutil.copy2(self.current_wordlib_path, file_path)
                
                QMessageBox.information(self, "成功", f"词库导出成功: {file_path}")
                self.logger.info(f"词库导出成功: {self.current_wordlib_path} -> {file_path}")
                
        except Exception as e:
            self.logger.error(f"导出词库失败: {e}")
            QMessageBox.critical(self, "错误", f"导出词库失败: {e}")
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查是否有未保存的更改
        if self.save_btn.isEnabled():
            reply = QMessageBox.question(
                self, "确认关闭", 
                "有未保存的更改，确定要关闭吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        self.logger.info("词库管理窗口已关闭")
        event.accept()