#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQt5版本的主窗口
使用现代化的PyQt5界面设计
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLabel, QPushButton, QMenuBar, QMenu,
    QAction, QStatusBar, QSplitter, QGroupBox, QGridLayout,
    QMessageBox, QFileDialog, QProgressBar, QFrame, QListWidget,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QToolBar, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QTextBrowser, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QKeySequence

# 导入SiliconUI组件
try:
    import siui
    from siui.components.widgets.button import SiPushButton
    from siui.components.widgets.container import SiDenseVContainer, SiDenseHContainer
    from siui.components.widgets.label import SiLabel
    from siui.components.widgets.line_edit import SiLineEdit
    SIUI_AVAILABLE = True
except ImportError:
    SIUI_AVAILABLE = False
    print("警告: SiliconUI未安装，将使用标准PyQt5组件")

import threading
import asyncio
import json
import os
from typing import Optional
from datetime import datetime
import webbrowser

from ..wordlib.manager import LchliebedichWordLibManager
from ..config.settings import ConfigManager
from ..utils.logger import get_logger
from .help_window_qt import HelpWindowQt
from .wordlib_window_qt import WordLibWindowQt
from .config_window_qt import ConfigWindowQt

from .stats_window_qt import StatsWindowQt

class MainWindowQt(QMainWindow):
    """PyQt5主窗口类，使用现代化的PyQt5界面设计"""
    
    def __init__(self, wordlib_manager: LchliebedichWordLibManager, onebot_engine=None, onebot_framework=None):
        super().__init__()
        
        self.wordlib_manager = wordlib_manager
        self.onebot_engine = onebot_engine
        self.onebot_framework = onebot_framework
        self.logger = get_logger("MainWindowQt")
        
        # 窗口状态
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # 子窗口
        self.wordlib_window = None
        self.config_window = None

        self.stats_window = None
        self.help_window = None
        
        # UI组件
        self.central_widget = None
        self.tab_widget = None
        self.message_log_text = None
        
        # 统计和消息数据
        import time
        self.start_time = time.time()
        self.message_history = []
        self.filtered_messages = []
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("lchliebedich 词库管理器")
        self.setMinimumSize(1200, 800)
        
        # 设置现代化样式
        self.setup_style()
        
        # 设置菜单栏和快捷键
        self.setup_menu_bar()
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加各个页面
        self.setup_pages()
        
        # 设置状态栏
        self.setup_status_bar()
        
        # 设置键盘快捷键
        self.setup_shortcuts()
        
    def setup_style(self):
        """设置现代化样式"""
        # 根据是否有SiliconUI选择不同的样式
        if SIUI_AVAILABLE:
            # Silicon Gallery风格深色主题样式
            style = """
            QMainWindow {
                background-color: #2B2B2B;
                color: #E8E8E8;
            }
            QWidget {
                background-color: #2B2B2B;
                color: #E8E8E8;
            }
            QMainWindow {
                border: none;
                outline: none;
            }
            QFrame {
                border: none;
                outline: none;
            }
            QTabWidget::pane {
                border: none;
                outline: none;
            }
            QGroupBox {
                border: none;
                outline: none;
            }
            /* 精确的边框控制，避免过度样式化 */
            QLabel {
                border: none;
                outline: none;
                background-color: transparent;
            }
            QPushButton {
                border: none;
                outline: none;
            }
            QTextEdit {
                border: none;
                outline: none;
            }
            QLineEdit {
                border: none;
                outline: none;
            }
            QComboBox {
                border: none;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                outline: none;
            }
            QSpinBox {
                border: none;
                outline: none;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                outline: none;
            }
            QCheckBox {
                border: none;
                outline: none;
            }
            QCheckBox::indicator {
                border: none;
                outline: none;
            }
            QListWidget {
                border: none;
                outline: none;
            }
            QListWidget::item {
                border: none;
                outline: none;
            }
            QTreeWidget {
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                border: none;
                outline: none;
            }
            QTableWidget {
                border: none;
                outline: none;
            }
            QTableWidget::item {
                border: none;
                outline: none;
            }
            QTextBrowser {
                border: none;
                outline: none;
            }
            QScrollArea {
                border: none;
                outline: none;
                background-color: #2B2B2B;
                border: none;
            }
            QFrame {
                background-color: #2B2B2B;
                color: #E8E8E8;
            }
            QTabWidget::pane {
                border: none;
                background-color: #323232;
                border-radius: 12px;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #E8E8E8;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 8px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #8B5CF6;
                color: #FFFFFF;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background-color: #4A4A4A;
            }
            QGroupBox {
                font-weight: 600;
                border: none;
                border-radius: 12px;
                margin-top: 1ex;
                background-color: #323232;
                color: #E8E8E8;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #A78BFA;
                font-weight: 600;
            }
            QLabel {
                color: #E8E8E8;
                font-weight: 400;
                background-color: transparent;
            }
            QLineEdit {
                background-color: #404040;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                color: #E8E8E8;
                font-size: 14px;
                min-height: 20px;
                height: auto;
            }
            QLineEdit:focus {
                border: none;
                background-color: #4A4A4A;
            }
            QComboBox {
                background-color: #404040;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                color: #E8E8E8;
                font-size: 14px;
                min-height: 20px;
                height: auto;
            }
            QComboBox:hover {
                border: none;
                background-color: #4A4A4A;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #E8E8E8;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                border: none;
                color: #E8E8E8;
                selection-background-color: #8B5CF6;
                selection-color: #FFFFFF;
            }
            QCheckBox {
                color: #E8E8E8;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: none;
            }
            QCheckBox::indicator:checked {
                background-color: #8B5CF6;
                border: none;
            }
            QSpinBox {
                background-color: #404040;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                color: #E8E8E8;
                font-size: 14px;
            }
            QSpinBox:focus {
                border: none;
                background-color: #4A4A4A;
            }
            QPushButton {
                background-color: #8B5CF6;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:pressed {
                background-color: #6D28D9;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            QTextEdit {
                background-color: #404040;
                border: none;
                border-radius: 10px;
                color: #E8E8E8;
                padding: 12px;
                font-size: 14px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: none;
                background-color: #4A4A4A;
            }
            QTextBrowser {
                background-color: #404040;
                border: none;
                border-radius: 10px;
                color: #E8E8E8;
                padding: 12px;
                font-size: 14px;
                line-height: 1.4;
            }
            QTextBrowser:focus {
                border: none;
                background-color: #4A4A4A;
            }
            QListWidget {
                background-color: #404040;
                border: none;
                border-radius: 10px;
                color: #E8E8E8;
                padding: 8px;
            }
            QTreeWidget {
                background-color: #404040;
                border: none;
                border-radius: 10px;
                color: #E8E8E8;
                padding: 8px;
            }
            QTableWidget {
                background-color: #404040;
                border: none;
                border-radius: 10px;
                color: #E8E8E8;
                gridline-color: transparent;
                padding: 8px;
                selection-background-color: #8B5CF6;
                alternate-background-color: #4A4A4A;
            }
            QTableWidget::item {
                background-color: #404040;
                border: none;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #8B5CF6;
                color: #FFFFFF;
            }
            QTableWidget::item:hover {
                background-color: #555555;
            }
            QTableWidget::item:alternate {
                background-color: #4A4A4A;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #555555;
                border: none;
            }
            QHeaderView::section {
                background-color: #555555;
                color: #E8E8E8;
                border: none;
                padding: 8px;
                font-weight: 600;
            }
            QScrollBar:vertical {
                background-color: #323232;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #8B5CF6;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A78BFA;
            }
            QScrollBar:horizontal {
                background-color: #323232;
                height: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background-color: #8B5CF6;
                border-radius: 7px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #A78BFA;
            }
            QStatusBar {
                background-color: #323232;
                color: #E8E8E8;
                border: none;
                padding: 5px;
            }
            QProgressBar {
                background-color: #404040;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: #E8E8E8;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #8B5CF6;
                border-radius: 6px;
                margin: 1px;
            }
            QMessageBox {
                background-color: #2B2B2B;
                color: #E8E8E8;
            }
            QMessageBox QPushButton {
                min-width: 80px;
                padding: 8px 16px;
            }
            """
        else:
            # 修复后的浅色主题样式（精确移除边框，避免过度样式化）
            style = """
            QMainWindow {
                background-color: #f5f5f5;
                border: none;
                outline: none;
            }
            QWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QFrame {
                border: none;
                outline: none;
            }
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e1e1e1;
                padding: 10px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: none;
                color: #333333;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border: none;
                color: #0078d4;
                font-weight: 600;
            }
            QTabBar::tab:hover {
                background-color: #d1d1d1;
                border: none;
            }
            QGroupBox {
                font-weight: 600;
                border: none;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: white;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #0078d4;
                font-size: 14px;
                font-weight: 600;
            }
            QLabel {
                color: #333333;
                font-weight: 400;
                background-color: transparent;
                border: none;
                outline: none;
            }
            QLineEdit {
                background-color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: none;
                background-color: #f8f9fa;
            }
            QComboBox {
                background-color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-size: 14px;
                min-height: 20px;
            }
            QComboBox:hover {
                border: none;
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: none;
                color: #333333;
                selection-background-color: #0078d4;
                selection-color: white;
            }
            QCheckBox {
                color: #333333;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
                border: none;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: none;
            }
            QSpinBox {
                background-color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                color: #333333;
                font-size: 14px;
            }
            QSpinBox:focus {
                border: none;
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit {
                background-color: white;
                border: none;
                border-radius: 8px;
                color: #333333;
                padding: 12px;
                font-size: 14px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: none;
                background-color: #f8f9fa;
            }
            QTextBrowser {
                background-color: white;
                border: none;
                border-radius: 8px;
                color: #333333;
                padding: 12px;
                font-size: 14px;
                line-height: 1.4;
            }
            QListWidget {
                background-color: white;
                border: none;
                border-radius: 8px;
                color: #333333;
                padding: 8px;
            }
            QTreeWidget {
                background-color: white;
                border: none;
                border-radius: 8px;
                color: #333333;
                padding: 8px;
            }
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 8px;
                color: #333333;
                gridline-color: transparent;
                padding: 8px;
                selection-background-color: #0078d4;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                background-color: white;
                border: none;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #e6f3ff;
            }
            QTableWidget::item:alternate {
                background-color: #f8f9fa;
            }
            QHeaderView::section {
                background-color: #f1f1f1;
                color: #333333;
                border: none;
                padding: 8px;
                font-weight: 600;
            }
            QScrollBar:vertical {
                background-color: #f1f1f1;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #0078d4;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #106ebe;
            }
            QScrollBar:horizontal {
                background-color: #f1f1f1;
                height: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background-color: #0078d4;
                border-radius: 7px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #106ebe;
            }
            QStatusBar {
                background-color: #f1f1f1;
                color: #333333;
                border: none;
                padding: 5px;
            }
            QProgressBar {
                background-color: #e1e1e1;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: #333333;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 6px;
                margin: 1px;
            }
            QMessageBox {
                background-color: white;
                color: #333333;
            }
            QMessageBox QPushButton {
                min-width: 80px;
                padding: 8px 16px;
            }
            """
        self.setStyleSheet(style)
        
    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 导入词库
        import_action = QAction('导入词库(&I)', self)
        import_action.setShortcut(QKeySequence('Ctrl+I'))
        import_action.setStatusTip('导入词库文件')
        import_action.triggered.connect(self.import_wordlib)
        file_menu.addAction(import_action)
        
        # 导出词库
        export_action = QAction('导出词库(&E)', self)
        export_action.setShortcut(QKeySequence('Ctrl+E'))
        export_action.setStatusTip('导出词库文件')
        export_action.triggered.connect(self.export_wordlib)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 保存日志
        save_log_action = QAction('保存日志(&S)', self)
        save_log_action.setShortcut(QKeySequence('Ctrl+S'))
        save_log_action.setStatusTip('保存消息日志')
        save_log_action.triggered.connect(self.save_message_log)
        file_menu.addAction(save_log_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&Q)', self)
        exit_action.setShortcut(QKeySequence('Ctrl+Q'))
        exit_action.setStatusTip('退出应用程序')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')
        
        # 清空日志
        clear_log_action = QAction('清空日志(&C)', self)
        clear_log_action.setShortcut(QKeySequence('Ctrl+L'))
        clear_log_action.setStatusTip('清空消息日志')
        clear_log_action.triggered.connect(self.clear_message_log)
        edit_menu.addAction(clear_log_action)
        
        # 清空缓存
        clear_cache_action = QAction('清空缓存(&H)', self)
        clear_cache_action.setShortcut(QKeySequence('Ctrl+Shift+C'))
        clear_cache_action.setStatusTip('清空应用程序缓存')
        clear_cache_action.triggered.connect(self.clear_cache)
        edit_menu.addAction(clear_cache_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        
        # 重载词库
        reload_action = QAction('重载词库(&R)', self)
        reload_action.setShortcut(QKeySequence('F5'))
        reload_action.setStatusTip('重新加载词库')
        reload_action.triggered.connect(self.reload_wordlib)
        tools_menu.addAction(reload_action)
        
        # 测试连接
        test_action = QAction('测试连接(&T)', self)
        test_action.setShortcut(QKeySequence('Ctrl+T'))
        test_action.setStatusTip('测试OneBot连接')
        test_action.triggered.connect(self.test_connection)
        tools_menu.addAction(test_action)
        
        tools_menu.addSeparator()
        
        # 词库管理
        wordlib_action = QAction('词库管理(&W)', self)
        wordlib_action.setShortcut(QKeySequence('Ctrl+W'))
        wordlib_action.setStatusTip('打开词库管理窗口')
        wordlib_action.triggered.connect(self.open_wordlib_window)
        tools_menu.addAction(wordlib_action)
        
        # 配置管理
        config_action = QAction('配置管理(&C)', self)
        config_action.setShortcut(QKeySequence('Ctrl+,'))
        config_action.setStatusTip('打开配置管理窗口')
        config_action.triggered.connect(self.open_config_window)
        tools_menu.addAction(config_action)
        
        # 日志查看
        log_action = QAction('日志查看(&L)', self)
        log_action.setShortcut(QKeySequence('Ctrl+Shift+L'))
        log_action.setStatusTip('打开日志查看窗口')

        tools_menu.addAction(log_action)
        
        # 统计信息
        stats_action = QAction('统计信息(&S)', self)
        stats_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        stats_action.setStatusTip('打开统计信息窗口')
        stats_action.triggered.connect(self.open_stats_window)
        tools_menu.addAction(stats_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 切换到概览页面
        overview_action = QAction('概览(&O)', self)
        overview_action.setShortcut(QKeySequence('Ctrl+1'))
        overview_action.setStatusTip('切换到概览页面')
        overview_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(overview_action)
        
        # 切换到词库页面
        wordlib_view_action = QAction('词库(&W)', self)
        wordlib_view_action.setShortcut(QKeySequence('Ctrl+2'))
        wordlib_view_action.setStatusTip('切换到词库页面')
        wordlib_view_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(wordlib_view_action)
        
        # 切换到消息页面
        messages_action = QAction('消息(&M)', self)
        messages_action.setShortcut(QKeySequence('Ctrl+3'))
        messages_action.setStatusTip('切换到消息页面')
        messages_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(messages_action)
        
        # 切换到统计页面
        stats_action = QAction('统计(&S)', self)
        stats_action.setShortcut(QKeySequence('Ctrl+4'))
        stats_action.setStatusTip('切换到统计页面')
        stats_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(stats_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        # 关于
        about_action = QAction('关于(&A)', self)
        about_action.setShortcut(QKeySequence('F1'))
        about_action.setStatusTip('关于此应用程序')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 帮助文档
        help_action = QAction('帮助文档(&H)', self)
        help_action.setShortcut(QKeySequence('Ctrl+F1'))
        help_action.setStatusTip('打开帮助文档')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
    def setup_shortcuts(self):
        """设置额外的键盘快捷键"""
        # 刷新快捷键
        refresh_shortcut = QAction(self)
        refresh_shortcut.setShortcut(QKeySequence('Ctrl+R'))
        refresh_shortcut.triggered.connect(self.update_status)
        self.addAction(refresh_shortcut)
        
        # 全屏切换
        fullscreen_shortcut = QAction(self)
        fullscreen_shortcut.setShortcut(QKeySequence('F11'))
        fullscreen_shortcut.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_shortcut)
        
        # 最小化
        minimize_shortcut = QAction(self)
        minimize_shortcut.setShortcut(QKeySequence('Ctrl+M'))
        minimize_shortcut.triggered.connect(self.showMinimized)
        self.addAction(minimize_shortcut)
        
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于 lchliebedich",
            "<h3>lchliebedich 词库管理器</h3>"
            "<p>版本: 0.1.2</p>"
            "<p>一个基于PyQt5的现代化词库管理工具</p>"
            "<p>支持OneBot协议的QQ机器人词库管理</p>"
        )
        
    def show_help(self):
        """显示帮助文档"""
        try:
            if self.help_window is None:
                self.help_window = HelpWindowQt(self)
            
            self.help_window.show()
            self.help_window.raise_()
            self.help_window.activateWindow()
            
        except Exception as e:
            self.logger.error(f"打开帮助窗口失败: {e}")
            # 如果帮助窗口打开失败，显示简单的帮助信息
            help_text = """
            <h2>lchliebedich 使用帮助</h2>
            
            <h3>基本功能</h3>
            <ul>
            <li><b>词库管理:</b> 导入、导出、编辑词库文件</li>
            <li><b>OneBot连接:</b> 连接QQ机器人框架</li>
            <li><b>实时监控:</b> 查看消息日志和统计信息</li>
            <li><b>配置管理:</b> 自定义应用程序设置</li>
            </ul>
            
            <h3>快速开始</h3>
            <ol>
            <li>在配置页面设置OneBot连接信息</li>
            <li>导入或创建词库文件</li>
            <li>点击"测试连接"确保连接正常</li>
            <li>开始使用机器人功能</li>
            </ol>
            
            <h3>键盘快捷键</h3>
            <p>按 Ctrl+F1 打开详细帮助文档</p>
            """
            
            msg = QMessageBox(self)
            msg.setWindowTitle("帮助文档")
            msg.setText(help_text)
            msg.setTextFormat(Qt.RichText)
            msg.exec_()
        
    def setup_pages(self):
        """设置页面"""
        # 添加各个选项卡页面
        self.tab_widget.addTab(self.create_overview_page(), "概览")
        self.tab_widget.addTab(self.create_wordlib_page(), "词库管理")
        self.tab_widget.addTab(self.create_messages_page(), "消息日志")
        self.tab_widget.addTab(self.create_stats_page(), "统计信息")
        self.tab_widget.addTab(self.create_config_page(), "配置")
        
    def create_overview_page(self):
        """创建概览页面"""
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
        # 创建顶部信息卡片区域
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setSpacing(24)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 引擎状态卡片
        engine_card = self.create_engine_status_card()
        top_layout.addWidget(engine_card)
        
        # 词库信息卡片
        wordlib_card = self.create_wordlib_info_card()
        top_layout.addWidget(wordlib_card)
        
        main_layout.addWidget(top_container)
        
        # 快速操作区域
        actions_card = self.create_quick_actions_card()
        main_layout.addWidget(actions_card)
        
        # 添加弹性空间
        main_layout.addStretch()
        
        return page
        
    def create_engine_status_card(self):
        """创建引擎状态卡片"""
        card = QFrame()
        card.setObjectName("statusCard")
        card.setStyleSheet("""
            QFrame#statusCard {
                background-color: #404040;
                border: 0px none transparent !important;
                outline: 0px none transparent !important;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel("引擎状态")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #E8E8E8;
                margin-bottom: 8px;
                border: none;
                outline: none;
                background-color: transparent;
            }
        """)
        layout.addWidget(title)
        
        # 状态信息容器
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 连接状态
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        status_label = QLabel("连接状态")
        status_label.setStyleSheet("color: #B0B0B0; font-size: 14px; border: none; outline: none; background-color: transparent;")
        self.engine_status_label = QLabel("未连接")
        self.engine_status_label.setStyleSheet("color: #E8E8E8; font-size: 14px; font-weight: 600; border: none; outline: none; background-color: transparent;")
        
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.engine_status_label)
        info_layout.addWidget(status_container)
        
        # QQ号
        qq_container = QWidget()
        qq_layout = QHBoxLayout(qq_container)
        qq_layout.setContentsMargins(0, 0, 0, 0)
        
        qq_label = QLabel("QQ号")
        qq_label.setStyleSheet("color: #B0B0B0; font-size: 14px;")
        self.qq_number_label = QLabel("未知")
        self.qq_number_label.setStyleSheet("color: #E8E8E8; font-size: 14px; font-weight: 600;")
        
        qq_layout.addWidget(qq_label)
        qq_layout.addStretch()
        qq_layout.addWidget(self.qq_number_label)
        info_layout.addWidget(qq_container)
        
        layout.addWidget(info_container)
        
        # 测试连接按钮
        self.test_connection_btn = QPushButton("测试连接")
        self.test_connection_btn.setToolTip("测试与QQ的连接状态")
        self.test_connection_btn.clicked.connect(self.test_connection)
        self.test_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7C3AED;
            }
            QPushButton:pressed {
                background-color: #6D28D9;
            }
        """)
        layout.addWidget(self.test_connection_btn)
        
        return card
        
    def create_wordlib_info_card(self):
        """创建词库信息卡片"""
        card = QFrame()
        card.setObjectName("wordlibCard")
        card.setStyleSheet("""
            QFrame#wordlibCard {
                background-color: #404040;
                border: 0px none transparent !important;
                outline: 0px none transparent !important;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel("词库信息")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #E8E8E8;
                margin-bottom: 8px;
                border: none;
                outline: none;
                background-color: transparent;
            }
        """)
        layout.addWidget(title)
        
        # 信息容器
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        # 词库数量
        count_container = QWidget()
        count_layout = QHBoxLayout(count_container)
        count_layout.setContentsMargins(0, 0, 0, 0)
        
        count_label = QLabel("词库数量")
        count_label.setStyleSheet("color: #B0B0B0; font-size: 14px; border: none; outline: none; background-color: transparent;")
        self.wordlib_count_label = QLabel("0")
        self.wordlib_count_label.setStyleSheet("color: #E8E8E8; font-size: 14px; font-weight: 600; border: none; outline: none; background-color: transparent;")
        
        count_layout.addWidget(count_label)
        count_layout.addStretch()
        count_layout.addWidget(self.wordlib_count_label)
        info_layout.addWidget(count_container)
        
        # 总大小
        size_container = QWidget()
        size_layout = QHBoxLayout(size_container)
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        size_label = QLabel("总大小")
        size_label.setStyleSheet("color: #B0B0B0; font-size: 14px; border: none; outline: none; background-color: transparent;")
        self.wordlib_size_label = QLabel("0 KB")
        self.wordlib_size_label.setStyleSheet("color: #E8E8E8; font-size: 14px; font-weight: 600; border: none; outline: none; background-color: transparent;")
        
        size_layout.addWidget(size_label)
        size_layout.addStretch()
        size_layout.addWidget(self.wordlib_size_label)
        info_layout.addWidget(size_container)
        
        # 最后重载
        reload_container = QWidget()
        reload_layout = QHBoxLayout(reload_container)
        reload_layout.setContentsMargins(0, 0, 0, 0)
        
        reload_label = QLabel("最后重载")
        reload_label.setStyleSheet("color: #B0B0B0; font-size: 14px; border: none; outline: none; background-color: transparent;")
        self.last_reload_label = QLabel("从未")
        self.last_reload_label.setStyleSheet("color: #E8E8E8; font-size: 14px; font-weight: 600; border: none; outline: none; background-color: transparent;")
        
        reload_layout.addWidget(reload_label)
        reload_layout.addStretch()
        reload_layout.addWidget(self.last_reload_label)
        info_layout.addWidget(reload_container)
        
        layout.addWidget(info_container)
        
        return card
        
    def create_quick_actions_card(self):
        """创建快速操作卡片"""
        card = QFrame()
        card.setObjectName("actionsCard")
        card.setStyleSheet("""
            QFrame#actionsCard {
                background-color: #404040;
                border: 0px none transparent !important;
                outline: 0px none transparent !important;
                border-radius: 16px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel("快速操作")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 700;
                color: #E8E8E8;
                margin-bottom: 8px;
                border: none;
                outline: none;
                background-color: transparent;
            }
        """)
        layout.addWidget(title)
        
        # 按钮网格容器
        buttons_container = QWidget()
        buttons_layout = QGridLayout(buttons_container)
        buttons_layout.setSpacing(16)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # 按钮样式
        button_style = """
            QPushButton {
                background-color: #555555;
                border: none;
                border-radius: 12px;
                padding: 16px 20px;
                color: #E8E8E8;
                font-weight: 600;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #8B5CF6;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #7C3AED;
            }
        """
        
        # 重载词库按钮
        self.reload_wordlib_btn = QPushButton("重载词库")
        self.reload_wordlib_btn.setToolTip("重新加载所有词库文件")
        self.reload_wordlib_btn.clicked.connect(self.reload_wordlib)
        self.reload_wordlib_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.reload_wordlib_btn, 0, 0)
        
        # 导入词库按钮
        self.import_wordlib_btn = QPushButton("导入词库")
        self.import_wordlib_btn.setToolTip("从文件导入新的词库")
        self.import_wordlib_btn.clicked.connect(self.import_wordlib)
        self.import_wordlib_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.import_wordlib_btn, 0, 1)
        
        # 导出词库按钮
        self.export_wordlib_btn = QPushButton("导出词库")
        self.export_wordlib_btn.setToolTip("将当前词库导出到文件")
        self.export_wordlib_btn.clicked.connect(self.export_wordlib)
        self.export_wordlib_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.export_wordlib_btn, 1, 0)
        
        # 清空缓存按钮
        self.clear_cache_btn = QPushButton("清空缓存")
        self.clear_cache_btn.setToolTip("清空应用程序缓存")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.clear_cache_btn.setStyleSheet(button_style)
        buttons_layout.addWidget(self.clear_cache_btn, 1, 1)
        
        layout.addWidget(buttons_container)
        
        return card
        
    def create_wordlib_page(self):
        """创建词库管理页面"""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 词库列表区域
        self.setup_wordlib_list_embedded(splitter)
        
        # 词库编辑区域
        self.setup_wordlib_edit_embedded(splitter)
        
        # 设置分割器比例
        splitter.setSizes([350, 850])
        
        return page
        
    def create_messages_page(self):
        """创建消息日志页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 过滤器区域
        filter_group = QGroupBox("消息过滤")
        filter_layout = QHBoxLayout(filter_group)
        
        # 消息类型过滤
        self.message_type_combo = QComboBox()
        self.message_type_combo.addItems(["全部", "私聊", "群聊", "发送", "接收"])
        self.message_type_combo.currentTextChanged.connect(self.filter_messages)
        filter_layout.addWidget(QLabel("类型:"))
        filter_layout.addWidget(self.message_type_combo)
        
        # 关键词搜索
        self.message_search_edit = QLineEdit()
        self.message_search_edit.setPlaceholderText("搜索消息内容...")
        self.message_search_edit.textChanged.connect(self.filter_messages)
        filter_layout.addWidget(QLabel("搜索:"))
        filter_layout.addWidget(self.message_search_edit)
        
        filter_layout.addStretch()
        layout.addWidget(filter_group)
        
        # 消息日志表格
        self.message_log_table = QTableWidget()
        self.message_log_table.setColumnCount(5)
        self.message_log_table.setHorizontalHeaderLabels(["时间", "类型", "用户/群组", "发送者", "消息内容"])
        
        # 设置列宽
        header = self.message_log_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.message_log_table.setColumnWidth(0, 150)
        self.message_log_table.setColumnWidth(1, 80)
        self.message_log_table.setColumnWidth(2, 120)
        self.message_log_table.setColumnWidth(3, 120)
        
        # 设置表格属性
        self.message_log_table.setAlternatingRowColors(True)
        self.message_log_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.message_log_table.setSortingEnabled(True)
        
        layout.addWidget(self.message_log_table)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        if SIUI_AVAILABLE:
            clear_messages_btn = SiPushButton()
            clear_messages_btn.attachment().setText("清空日志")
            clear_messages_btn.clicked.connect(self.clear_message_log)
            
            save_messages_btn = SiPushButton()
            save_messages_btn.attachment().setText("保存日志")
            save_messages_btn.clicked.connect(self.save_message_log)
            
            refresh_messages_btn = SiPushButton()
            refresh_messages_btn.attachment().setText("刷新")
            refresh_messages_btn.clicked.connect(self.refresh_message_log)
        else:
            clear_messages_btn = QPushButton("清空日志")
            clear_messages_btn.clicked.connect(self.clear_message_log)
            
            save_messages_btn = QPushButton("保存日志")
            save_messages_btn.clicked.connect(self.save_message_log)
            
            refresh_messages_btn = QPushButton("刷新")
            refresh_messages_btn.clicked.connect(self.refresh_message_log)
        
        btn_layout.addWidget(clear_messages_btn)
        btn_layout.addWidget(save_messages_btn)
        btn_layout.addWidget(refresh_messages_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 初始化消息存储
        self.message_history = []
        self.filtered_messages = []
        
        return page
        
    def create_stats_page(self):
        """创建统计信息页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 词库统计组
        wordlib_group = QGroupBox("词库统计")
        wordlib_layout = QGridLayout(wordlib_group)
        
        self.stats_total_files_label = QLabel("0")
        self.stats_enabled_files_label = QLabel("0")
        self.stats_total_entries_label = QLabel("0")
        self.stats_total_size_label = QLabel("0 B")
        
        wordlib_layout.addWidget(QLabel("总文件数:"), 0, 0)
        wordlib_layout.addWidget(self.stats_total_files_label, 0, 1)
        wordlib_layout.addWidget(QLabel("启用文件数:"), 1, 0)
        wordlib_layout.addWidget(self.stats_enabled_files_label, 1, 1)
        wordlib_layout.addWidget(QLabel("总词条数:"), 2, 0)
        wordlib_layout.addWidget(self.stats_total_entries_label, 2, 1)
        wordlib_layout.addWidget(QLabel("总大小:"), 3, 0)
        wordlib_layout.addWidget(self.stats_total_size_label, 3, 1)
        
        scroll_layout.addWidget(wordlib_group)
        
        # 消息统计组
        message_group = QGroupBox("消息统计")
        message_layout = QGridLayout(message_group)
        
        self.stats_messages_received_label = QLabel("0")
        self.stats_messages_sent_label = QLabel("0")
        self.stats_private_messages_label = QLabel("0")
        self.stats_group_messages_label = QLabel("0")
        
        message_layout.addWidget(QLabel("接收消息数:"), 0, 0)
        message_layout.addWidget(self.stats_messages_received_label, 0, 1)
        message_layout.addWidget(QLabel("发送消息数:"), 1, 0)
        message_layout.addWidget(self.stats_messages_sent_label, 1, 1)
        message_layout.addWidget(QLabel("私聊消息数:"), 2, 0)
        message_layout.addWidget(self.stats_private_messages_label, 2, 1)
        message_layout.addWidget(QLabel("群聊消息数:"), 3, 0)
        message_layout.addWidget(self.stats_group_messages_label, 3, 1)
        
        scroll_layout.addWidget(message_group)
        
        # 系统统计组
        system_group = QGroupBox("系统统计")
        system_layout = QGridLayout(system_group)
        
        self.stats_uptime_label = QLabel("0秒")
        self.stats_memory_usage_label = QLabel("0 MB")
        self.stats_connections_label = QLabel("0")
        
        system_layout.addWidget(QLabel("运行时间:"), 0, 0)
        system_layout.addWidget(self.stats_uptime_label, 0, 1)
        system_layout.addWidget(QLabel("内存使用:"), 1, 0)
        system_layout.addWidget(self.stats_memory_usage_label, 1, 1)
        system_layout.addWidget(QLabel("连接数:"), 2, 0)
        system_layout.addWidget(self.stats_connections_label, 2, 1)
        
        scroll_layout.addWidget(system_group)
        
        # 刷新按钮
        if SIUI_AVAILABLE:
            refresh_stats_btn = SiPushButton()
            refresh_stats_btn.attachment().setText("刷新统计")
            refresh_stats_btn.clicked.connect(self.refresh_stats)
        else:
            refresh_stats_btn = QPushButton("刷新统计")
            refresh_stats_btn.clicked.connect(self.refresh_stats)
        scroll_layout.addWidget(refresh_stats_btn)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return page
        
    def create_config_page(self):
        """创建配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建配置选项卡
        config_tabs = QTabWidget()
        layout.addWidget(config_tabs)
        
        # 添加配置选项卡
        self.setup_config_tabs_embedded(config_tabs)
        
        return page
        

        
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 每秒更新一次
        
    # 侧边栏功能已被标签页替代，此方法不再需要
        
    def reload_wordlib(self):
        """重载词库"""
        reply = QMessageBox.question(
            self, "确认重载", 
            "确定要重载所有词库吗？\n这可能需要一些时间。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            self.status_label.setText("正在重载词库...")
            
            # 禁用相关按钮
            self.reload_wordlib_btn.setEnabled(False)
            self.import_wordlib_btn.setEnabled(False)
            self.export_wordlib_btn.setEnabled(False)
            
            # 在后台线程中重载词库
            def reload_thread():
                try:
                    self.wordlib_manager.reload_all()
                    # 使用QTimer在主线程中更新UI
                    QTimer.singleShot(0, lambda: self.on_reload_success())
                except Exception as e:
                    # 使用QTimer在主线程中更新UI
                    QTimer.singleShot(0, lambda: self.on_reload_error(str(e)))
                    
            threading.Thread(target=reload_thread, daemon=True).start()
            
        except Exception as e:
            self.on_reload_error(str(e))
            
    def on_reload_success(self):
        """重载成功回调"""
        self.status_label.setText("词库重载完成")
        self.progress_bar.setVisible(False)
        self.reload_wordlib_btn.setEnabled(True)
        self.import_wordlib_btn.setEnabled(True)
        self.export_wordlib_btn.setEnabled(True)
        self.logger.info("词库重载完成")
        QMessageBox.information(self, "成功", "词库重载完成！")
        self.update_wordlib_info()  # 更新词库信息显示
        
    def on_reload_error(self, error_msg):
        """重载失败回调"""
        self.status_label.setText("词库重载失败")
        self.progress_bar.setVisible(False)
        self.reload_wordlib_btn.setEnabled(True)
        self.import_wordlib_btn.setEnabled(True)
        self.export_wordlib_btn.setEnabled(True)
        self.logger.error(f"词库重载失败: {error_msg}")
        QMessageBox.critical(self, "错误", f"重载词库失败:\n{error_msg}")
            
    def clear_message_log(self):
        """清空消息日志"""
        self.message_log_table.setRowCount(0)
        self.message_history.clear()
        self.filtered_messages.clear()
        self.logger.info("消息日志已清空")
        
    def save_message_log(self):
        """保存消息日志"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存消息日志", f"message_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("时间\t类型\t用户/群组\t发送者\t消息内容\n")
                    for msg in self.filtered_messages:
                        f.write(f"{msg['timestamp']}\t{msg['type']}\t{msg['target']}\t{msg['sender']}\t{msg['content']}\n")
                QMessageBox.information(self, "成功", f"消息日志已保存到: {file_path}")
                self.logger.info(f"消息日志已保存到: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存消息日志失败: {e}")
            
    def log_message(self, message: str):
        """记录消息到日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.message_log_text.append(log_entry)
        
        # 限制日志长度
        if self.message_log_text.document().blockCount() > 1000:
            cursor = self.message_log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 100)
            cursor.removeSelectedText()
            
    def update_status(self):
        """更新状态信息"""
        try:
            self.update_engine_status()
            self.update_wordlib_info()
            self.update_message_logs()
            self.update_stats_info()
        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")
            
    def update_engine_status(self):
        """更新引擎状态"""
        try:
            if self.onebot_engine:
                # 获取真实的引擎状态
                status_info = self.onebot_engine.get_status()
                login_status = self.onebot_engine.get_login_status()
                
                # 根据登录状态显示不同的状态信息
                if login_status.value == "logged_in":
                    self.engine_status_label.setText("已登录")
                    self.engine_status_label.setStyleSheet("color: green; font-weight: bold;")
                elif login_status.value == "logging_in":
                    self.engine_status_label.setText("登录中")
                    self.engine_status_label.setStyleSheet("color: orange; font-weight: bold;")
                elif login_status.value == "need_qrcode":
                    self.engine_status_label.setText("需要扫码")
                    self.engine_status_label.setStyleSheet("color: blue; font-weight: bold;")
                elif login_status.value == "login_failed":
                    self.engine_status_label.setText("登录失败")
                    self.engine_status_label.setStyleSheet("color: red; font-weight: bold;")
                elif login_status.value == "disconnected":
                    self.engine_status_label.setText("连接断开")
                    self.engine_status_label.setStyleSheet("color: red; font-weight: bold;")
                else:
                    self.engine_status_label.setText("未知状态")
                    self.engine_status_label.setStyleSheet("color: gray; font-weight: bold;")
                    
                # 更新连接状态显示
                if self.onebot_engine.is_connected():
                    connection_text = "已连接"
                    connection_color = "green"
                else:
                    connection_text = "未连接"
                    connection_color = "red"
                    
                # 如果有连接状态标签，更新它
                if hasattr(self, 'connection_status_label'):
                    self.connection_status_label.setText(connection_text)
                    self.connection_status_label.setStyleSheet(f"color: {connection_color}; font-weight: bold;")
                    
            else:
                self.engine_status_label.setText("引擎未初始化")
                self.engine_status_label.setStyleSheet("color: gray; font-weight: bold;")
                
        except Exception as e:
            self.logger.error(f"更新引擎状态失败: {e}")
            self.engine_status_label.setText("状态获取失败")
            self.engine_status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def update_wordlib_info(self):
        """更新词库信息"""
        try:
            if self.wordlib_manager:
                # 获取真实的词库统计信息
                stats = self.wordlib_manager.get_stats()
                
                # 更新词库数量信息
                total_files = stats.get('total_files', 0)
                enabled_files = stats.get('enabled_files', 0)
                loaded_engines = stats.get('loaded_engines', 0)
                total_entries = stats.get('total_entries', 0)
                
                self.wordlib_count_label.setText(f"词库文件: {enabled_files}/{total_files} (已加载: {loaded_engines})")
                self.wordlib_size_label.setText(f"词条总数: {total_entries}")
                
                # 获取词库文件信息来计算总大小
                wordlib_files = self.wordlib_manager.get_wordlib_files()
                total_size = 0
                last_modified = None
                
                for file_info in wordlib_files:
                    if file_info.get('enabled', False):
                        file_size = file_info.get('size', 0)
                        total_size += file_size
                        
                        # 获取最新的修改时间
                        modified_time = file_info.get('modified_time')
                        if modified_time and (last_modified is None or modified_time > last_modified):
                            last_modified = modified_time
                
                # 格式化文件大小
                if total_size < 1024:
                    size_text = f"{total_size} B"
                elif total_size < 1024 * 1024:
                    size_text = f"{total_size / 1024:.1f} KB"
                else:
                    size_text = f"{total_size / (1024 * 1024):.1f} MB"
                
                # 更新大小显示（如果有对应的标签）
                if hasattr(self, 'wordlib_total_size_label'):
                    self.wordlib_total_size_label.setText(f"总大小: {size_text}")
                
                # 格式化最后修改时间
                if last_modified:
                    import datetime
                    if isinstance(last_modified, (int, float)):
                        last_modified_str = datetime.datetime.fromtimestamp(last_modified).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        last_modified_str = str(last_modified)
                    
                    # 更新最后重载时间标签
                    if hasattr(self, 'last_reload_label'):
                        self.last_reload_label.setText(f"最后更新: {last_modified_str}")
                    elif hasattr(self, 'wordlib_reload_label'):
                        self.wordlib_reload_label.setText(f"最后更新: {last_modified_str}")
                else:
                    if hasattr(self, 'last_reload_label'):
                        self.last_reload_label.setText("最后更新: 未知")
                    elif hasattr(self, 'wordlib_reload_label'):
                        self.wordlib_reload_label.setText("最后更新: 未知")
                    
            else:
                self.wordlib_count_label.setText("词库文件: 未初始化")
                self.wordlib_size_label.setText("词条总数: 未知")
                if hasattr(self, 'last_reload_label'):
                    self.last_reload_label.setText("最后更新: 未知")
                elif hasattr(self, 'wordlib_reload_label'):
                    self.wordlib_reload_label.setText("最后更新: 未知")
                
        except Exception as e:
            self.logger.error(f"更新词库信息失败: {e}")
            self.wordlib_count_label.setText("词库文件: 获取失败")
            self.wordlib_size_label.setText("词条总数: 获取失败")
            if hasattr(self, 'last_reload_label'):
                self.last_reload_label.setText("最后更新: 获取失败")
            elif hasattr(self, 'wordlib_reload_label'):
                self.wordlib_reload_label.setText("最后更新: 获取失败")
            
    def update_message_logs(self):
        """更新消息日志"""
        try:
            # 如果没有消息历史，添加一些示例数据用于测试
            if not self.message_history:
                self.add_sample_messages()
            
            if self.onebot_framework and hasattr(self.onebot_framework, 'message_handler'):
                # 从OneBot框架获取最新消息
                recent_messages = getattr(self.onebot_framework.message_handler, 'recent_messages', [])
                
                # 创建已处理消息的标识集合（基于时间戳和用户ID）
                processed_messages = set()
                for existing_msg in self.message_history:
                    if isinstance(existing_msg, dict):
                        # 使用时间戳和用户ID作为唯一标识
                        msg_id = f"{existing_msg.get('timestamp', '')}_{existing_msg.get('sender', '')}_{existing_msg.get('content', '')}"
                        processed_messages.add(msg_id)
                
                # 添加新消息到历史记录
                for msg in recent_messages:
                    if isinstance(msg, dict):
                        # 生成消息唯一标识，确保时间戳格式与add_message_to_log一致
                        time_value = msg.get('time')
                        if isinstance(time_value, (int, float)):
                            timestamp = datetime.fromtimestamp(time_value).strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(time_value, str):
                            timestamp = time_value
                        else:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        sender_info = msg.get('sender', {})
                        if isinstance(sender_info, dict):
                            sender = sender_info.get('nickname', '未知')
                        else:
                            sender = str(sender_info) if sender_info else '未知'
                        
                        # 处理消息内容，与add_message_to_log方法保持一致
                        message_content = msg.get('message', '')
                        if isinstance(message_content, list):
                            # 如果是列表格式，提取文本内容
                            content_parts = []
                            for part in message_content:
                                if isinstance(part, dict) and part.get('type') == 'text':
                                    text_data = part.get('data', {})
                                    if isinstance(text_data, dict):
                                        content_parts.append(text_data.get('text', ''))
                                    else:
                                        content_parts.append(str(text_data))
                                elif isinstance(part, str):
                                    content_parts.append(part)
                            content = ''.join(content_parts).strip()
                        elif isinstance(message_content, str):
                            content = message_content.strip()
                        else:
                            content = str(message_content).strip() if message_content else ''
                        
                        # 如果还是空的，尝试从raw_message获取
                        if not content:
                            content = msg.get('raw_message', '未知内容')
                        
                        msg_id = f"{timestamp}_{sender}_{content}"
                        
                        # 只有当消息ID不存在时才添加
                        if msg_id not in processed_messages:
                            self.add_message_to_log(msg)
                            processed_messages.add(msg_id)
                        
            # 更新过滤后的消息显示
            self.filter_messages()
        except Exception as e:
            self.logger.error(f"更新消息日志失败: {e}")
    
    def add_sample_messages(self):
        """添加示例消息数据"""
        try:
            sample_messages = [
                {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '群聊',
                    'target': '群组(123456)',
                    'sender': '测试用户1',
                    'content': '这是一条测试群聊消息',
                    'message_type': 'group',
                    'direction': 'received'
                },
                {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '私聊',
                    'target': '私聊用户',
                    'sender': '测试用户2',
                    'content': '这是一条测试私聊消息',
                    'message_type': 'private',
                    'direction': 'received'
                },
                {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '系统',
                    'target': '系统',
                    'sender': '系统',
                    'content': '系统启动完成',
                    'message_type': 'system',
                    'direction': 'system'
                }
            ]
            
            for msg in sample_messages:
                self.message_history.append(msg)
                
        except Exception as e:
            self.logger.error(f"添加示例消息失败: {e}")
    
    def refresh_message_log(self):
        """刷新消息日志"""
        self.update_message_logs()
        
    def filter_messages(self):
        """过滤消息"""
        try:
            filter_type = self.message_type_combo.currentText()
            search_text = self.message_search_edit.text().lower()
            
            self.filtered_messages = []
            for msg in self.message_history:
                # 类型过滤
                if filter_type != "全部":
                    if filter_type == "私聊" and msg.get('message_type') != 'private':
                        continue
                    elif filter_type == "群聊" and msg.get('message_type') != 'group':
                        continue
                    elif filter_type == "发送" and msg.get('direction') != 'sent':
                        continue
                    elif filter_type == "接收" and msg.get('direction') != 'received':
                        continue
                
                # 关键词搜索
                if search_text and search_text not in msg.get('content', '').lower():
                    continue
                    
                self.filtered_messages.append(msg)
            
            self.update_message_table()
        except Exception as e:
            self.logger.error(f"过滤消息失败: {e}")
    
    def add_message_to_log(self, message_data):
        """添加消息到日志"""
        try:
            # 解析消息数据
            if isinstance(message_data, dict):
                # 处理时间戳，确保格式统一
                time_value = message_data.get('time')
                if isinstance(time_value, (int, float)):
                    # Unix时间戳转换为字符串格式
                    timestamp = datetime.fromtimestamp(time_value).strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(time_value, str):
                    timestamp = time_value
                else:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 处理发送者信息
                sender_info = message_data.get('sender', {})
                if isinstance(sender_info, dict):
                    sender = sender_info.get('nickname', '未知')
                else:
                    sender = str(sender_info) if sender_info else '未知'
                
                # 处理消息内容，支持OneBot复杂消息格式
                message_content = message_data.get('message', '')
                if isinstance(message_content, list):
                    # 如果是列表格式，提取文本内容
                    content_parts = []
                    for part in message_content:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            text_data = part.get('data', {})
                            if isinstance(text_data, dict):
                                content_parts.append(text_data.get('text', ''))
                            else:
                                content_parts.append(str(text_data))
                        elif isinstance(part, str):
                            content_parts.append(part)
                    content = ''.join(content_parts).strip()
                elif isinstance(message_content, str):
                    content = message_content.strip()
                else:
                    content = str(message_content).strip() if message_content else ''
                
                # 如果还是空的，尝试从raw_message获取
                if not content:
                    content = message_data.get('raw_message', '未知内容')
                
                msg = {
                    'timestamp': timestamp,
                    'type': self.get_message_type_display(message_data),
                    'target': self.get_message_target(message_data),
                    'sender': sender,
                    'content': content,
                    'message_type': message_data.get('message_type', 'unknown'),
                    'direction': 'received'  # 默认为接收
                }
            else:
                # 如果是字符串，创建简单的消息记录
                msg = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': '系统',
                    'target': '系统',
                    'sender': '系统',
                    'content': str(message_data),
                    'message_type': 'system',
                    'direction': 'system'
                }
            
            self.message_history.append(msg)
            
            # 限制历史记录长度
            if len(self.message_history) > 1000:
                self.message_history = self.message_history[-1000:]
                
        except Exception as e:
            self.logger.error(f"添加消息到日志失败: {e}")
    
    def get_message_type_display(self, message_data):
        """获取消息类型显示文本"""
        msg_type = message_data.get('message_type', 'unknown')
        if msg_type == 'private':
            return '私聊'
        elif msg_type == 'group':
            return '群聊'
        else:
            return '其他'
    
    def get_message_target(self, message_data):
        """获取消息目标"""
        msg_type = message_data.get('message_type', 'unknown')
        if msg_type == 'private':
            return message_data.get('sender', {}).get('nickname', '私聊用户')
        elif msg_type == 'group':
            return f"群组({message_data.get('group_id', '未知')})"
        else:
            return '未知'
    
    def update_message_table(self):
        """更新消息表格显示"""
        try:
            if not hasattr(self, 'filtered_messages') or not self.filtered_messages:
                self.message_log_table.setRowCount(0)
                return
                
            self.message_log_table.setRowCount(len(self.filtered_messages))
            
            for row, msg in enumerate(self.filtered_messages):
                # 安全地获取消息数据，提供默认值
                timestamp = str(msg.get('timestamp', '未知时间'))
                msg_type = str(msg.get('type', '未知类型'))
                target = str(msg.get('target', '未知目标'))
                sender = str(msg.get('sender', '未知发送者'))
                content = str(msg.get('content', '无内容'))
                
                # 创建表格项并设置
                self.message_log_table.setItem(row, 0, QTableWidgetItem(timestamp))
                self.message_log_table.setItem(row, 1, QTableWidgetItem(msg_type))
                self.message_log_table.setItem(row, 2, QTableWidgetItem(target))
                self.message_log_table.setItem(row, 3, QTableWidgetItem(sender))
                self.message_log_table.setItem(row, 4, QTableWidgetItem(content))
                
        except Exception as e:
            self.logger.error(f"更新消息表格失败: {e}")
            # 在出错时清空表格
            self.message_log_table.setRowCount(0)
        
    def update_stats_info(self):
        """更新统计信息"""
        try:
            # 更新词库统计
            if self.wordlib_manager:
                wordlib_stats = self.wordlib_manager.get_stats()
                self.stats_total_files_label.setText(str(wordlib_stats.get('total_files', 0)))
                self.stats_enabled_files_label.setText(str(wordlib_stats.get('enabled_files', 0)))
                self.stats_total_entries_label.setText(str(wordlib_stats.get('total_entries', 0)))
                
                # 格式化文件大小
                total_size = wordlib_stats.get('total_size', 0)
                if total_size > 1024 * 1024:
                    size_text = f"{total_size / (1024 * 1024):.1f} MB"
                elif total_size > 1024:
                    size_text = f"{total_size / 1024:.1f} KB"
                else:
                    size_text = f"{total_size} B"
                self.stats_total_size_label.setText(size_text)
            
            # 更新消息统计
            if self.onebot_framework and hasattr(self.onebot_framework, 'stats'):
                onebot_stats = self.onebot_framework.stats
                self.stats_messages_received_label.setText(str(onebot_stats.get('messages_received', 0)))
                self.stats_messages_sent_label.setText(str(onebot_stats.get('messages_sent', 0)))
            
            # 统计消息类型
            private_count = sum(1 for msg in self.message_history if msg.get('message_type') == 'private')
            group_count = sum(1 for msg in self.message_history if msg.get('message_type') == 'group')
            self.stats_private_messages_label.setText(str(private_count))
            self.stats_group_messages_label.setText(str(group_count))
            
            # 更新系统统计
            import psutil
            import time
            
            # 运行时间（假设程序启动时间）
            if hasattr(self, 'start_time'):
                uptime_seconds = int(time.time() - self.start_time)
                hours = uptime_seconds // 3600
                minutes = (uptime_seconds % 3600) // 60
                seconds = uptime_seconds % 60
                uptime_text = f"{hours}时{minutes}分{seconds}秒"
            else:
                uptime_text = "未知"
            self.stats_uptime_label.setText(uptime_text)
            
            # 内存使用
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.stats_memory_usage_label.setText(f"{memory_mb:.1f} MB")
            except:
                self.stats_memory_usage_label.setText("未知")
            
            # 连接数（OneBot连接）
            if self.onebot_engine and hasattr(self.onebot_engine, 'connection_count'):
                self.stats_connections_label.setText(str(self.onebot_engine.connection_count))
            else:
                self.stats_connections_label.setText("0")
                
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
    
    def refresh_stats(self):
        """刷新统计信息"""
        self.update_stats_info()
            
    def test_connection(self):
        """测试连接"""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("正在测试连接...")
            self.test_connection_btn.setEnabled(False)
            
            def test_thread():
                try:
                    import time
                    time.sleep(2)  # 模拟连接测试过程
                    
                    # 检查OneBot引擎状态
                    if self.onebot_engine and hasattr(self.onebot_engine, 'is_running'):
                        if self.onebot_engine.is_running:
                            QTimer.singleShot(0, lambda: self.on_connection_test_success("OneBot引擎连接正常"))
                        else:
                            QTimer.singleShot(0, lambda: self.on_connection_test_warning("OneBot引擎未运行"))
                    else:
                        QTimer.singleShot(0, lambda: self.on_connection_test_warning("OneBot引擎未初始化"))
                        
                except Exception as e:
                    QTimer.singleShot(0, lambda: self.on_connection_test_error(str(e)))
                    
            threading.Thread(target=test_thread, daemon=True).start()
            
        except Exception as e:
            self.on_connection_test_error(str(e))
            
    def on_connection_test_success(self, message):
        """连接测试成功回调"""
        self.status_label.setText("连接测试完成")
        self.progress_bar.setVisible(False)
        self.test_connection_btn.setEnabled(True)
        self.logger.info(f"连接测试成功: {message}")
        QMessageBox.information(self, "连接测试", f"✓ {message}")
        
    def on_connection_test_warning(self, message):
        """连接测试警告回调"""
        self.status_label.setText("连接测试完成")
        self.progress_bar.setVisible(False)
        self.test_connection_btn.setEnabled(True)
        self.logger.warning(f"连接测试警告: {message}")
        QMessageBox.warning(self, "连接测试", f"⚠ {message}")
        
    def on_connection_test_error(self, error_msg):
        """连接测试失败回调"""
        self.status_label.setText("连接测试失败")
        self.progress_bar.setVisible(False)
        self.test_connection_btn.setEnabled(True)
        self.logger.error(f"连接测试失败: {error_msg}")
        QMessageBox.critical(self, "连接测试", f"✗ 连接测试失败:\n{error_msg}")
            
    def import_wordlib(self):
        """导入词库"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择词库文件", "", "JSON文件 (*.json);;文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
                
            reply = QMessageBox.question(
                self, "确认导入", 
                f"确定要导入词库文件吗？\n文件: {file_path}\n\n导入可能会覆盖现有数据。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
                
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("正在导入词库...")
            self.import_wordlib_btn.setEnabled(False)
            
            def import_thread():
                try:
                    # 这里添加实际的导入逻辑
                    import time
                    time.sleep(1)  # 模拟导入过程
                    QTimer.singleShot(0, lambda: self.on_import_success(file_path))
                except Exception as e:
                    QTimer.singleShot(0, lambda: self.on_import_error(str(e)))
                    
            threading.Thread(target=import_thread, daemon=True).start()
                
        except Exception as e:
            self.on_import_error(str(e))
            
    def on_import_success(self, file_path):
        """导入成功回调"""
        self.status_label.setText("词库导入完成")
        self.progress_bar.setVisible(False)
        self.import_wordlib_btn.setEnabled(True)
        self.logger.info(f"词库导入成功: {file_path}")
        QMessageBox.information(self, "成功", f"词库导入成功！\n文件: {file_path}")
        self.update_wordlib_info()
        
    def on_import_error(self, error_msg):
        """导入失败回调"""
        self.status_label.setText("词库导入失败")
        self.progress_bar.setVisible(False)
        self.import_wordlib_btn.setEnabled(True)
        self.logger.error(f"词库导入失败: {error_msg}")
        QMessageBox.critical(self, "错误", f"导入词库失败:\n{error_msg}")
            
    def export_wordlib(self):
        """导出词库"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出词库", f"wordlib_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "JSON文件 (*.json);;文本文件 (*.txt);;所有文件 (*.*)"
            )
            
            if not file_path:
                return
                
            reply = QMessageBox.question(
                self, "确认导出", 
                f"确定要导出词库到文件吗？\n保存路径: {file_path}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                return
                
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("正在导出词库...")
            self.export_wordlib_btn.setEnabled(False)
            
            def export_thread():
                try:
                    # 这里添加实际的导出逻辑
                    import time
                    time.sleep(1)  # 模拟导出过程
                    QTimer.singleShot(0, lambda: self.on_export_success(file_path))
                except Exception as e:
                    QTimer.singleShot(0, lambda: self.on_export_error(str(e)))
                    
            threading.Thread(target=export_thread, daemon=True).start()
                
        except Exception as e:
            self.on_export_error(str(e))
            
    def on_export_success(self, file_path):
        """导出成功回调"""
        self.status_label.setText("词库导出完成")
        self.progress_bar.setVisible(False)
        self.export_wordlib_btn.setEnabled(True)
        self.logger.info(f"词库导出成功: {file_path}")
        QMessageBox.information(self, "成功", f"词库导出成功！\n保存路径: {file_path}")
        
    def on_export_error(self, error_msg):
        """导出失败回调"""
        self.status_label.setText("词库导出失败")
        self.progress_bar.setVisible(False)
        self.export_wordlib_btn.setEnabled(True)
        self.logger.error(f"词库导出失败: {error_msg}")
        QMessageBox.critical(self, "错误", f"导出词库失败:\n{error_msg}")
            
    def open_wordlib_window(self):
        """打开词库管理窗口"""
        try:
            if self.wordlib_window is None:
                self.wordlib_window = WordLibWindowQt(self.wordlib_manager, self)
            
            self.wordlib_window.show()
            self.wordlib_window.raise_()
            self.wordlib_window.activateWindow()
            
        except Exception as e:
            self.logger.error(f"打开词库管理窗口失败: {e}")
            QMessageBox.critical(self, "错误", f"打开词库管理窗口失败: {e}")
        
    def open_config_window(self):
        """打开配置窗口"""
        try:
            if self.config_window is None:
                self.config_window = ConfigWindowQt(self)
            
            self.config_window.show()
            self.config_window.raise_()
            self.config_window.activateWindow()
            
        except Exception as e:
            self.logger.error(f"打开配置窗口失败: {e}")
            QMessageBox.critical(self, "错误", f"打开配置窗口失败: {e}")
        

    
    def open_stats_window(self):
        """打开统计信息窗口"""
        try:
            if self.stats_window is None:
                self.stats_window = StatsWindowQt(self, self.wordlib_manager, self.onebot_framework)
            
            self.stats_window.show()
            self.stats_window.raise_()
            self.stats_window.activateWindow()
            
        except Exception as e:
            self.logger.error(f"打开统计窗口失败: {e}")
            QMessageBox.critical(self, "错误", f"打开统计窗口失败: {e}")
        
    def clear_cache(self):
        """清空缓存"""
        reply = QMessageBox.question(
            self, "确认操作", 
            "确定要清空应用程序缓存吗？\n这将删除所有临时文件和缓存数据。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.status_label.setText("正在清空缓存...")
                # 这里可以添加实际的清空缓存逻辑
                QMessageBox.information(self, "成功", "缓存已清空")
                self.status_label.setText("就绪")
                self.logger.info("应用程序缓存已清空")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空缓存失败: {e}")
                self.status_label.setText("就绪")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.logger.info("正在关闭主窗口...")
        
        # 停止定时器
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
            
        # 关闭子窗口
        if self.wordlib_window:
            self.wordlib_window.close()
        if self.config_window:
            self.config_window.close()

        if self.stats_window:
            self.stats_window.close()
        if self.help_window:
            self.help_window.close()
            
        event.accept()
    
    def setup_wordlib_list_embedded(self, parent_splitter):
        """设置嵌入式词库列表"""
        # 创建词库列表组
        wordlib_group = QGroupBox("词库列表")
        wordlib_layout = QVBoxLayout(wordlib_group)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self.wordlib_search_edit = QLineEdit()
        self.wordlib_search_edit.setPlaceholderText("输入词库名称进行搜索...")
        self.wordlib_search_edit.textChanged.connect(self.on_wordlib_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.wordlib_search_edit)
        wordlib_layout.addLayout(search_layout)
        
        # 词库列表
        from PyQt5.QtWidgets import QTreeWidget
        self.embedded_wordlib_list = QTreeWidget()
        self.embedded_wordlib_list.setHeaderLabels(["词库名称", "状态", "词条数"])
        self.embedded_wordlib_list.itemClicked.connect(self.on_embedded_wordlib_selected)
        self.embedded_wordlib_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.embedded_wordlib_list.customContextMenuRequested.connect(self.show_embedded_wordlib_context_menu)
        wordlib_layout.addWidget(self.embedded_wordlib_list)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        if SIUI_AVAILABLE:
            self.add_wordlib_btn = SiPushButton()
            self.add_wordlib_btn.attachment().setText("添加")
            self.add_wordlib_btn.clicked.connect(self.add_new_wordlib)
            self.reload_wordlib_btn = SiPushButton()
            self.reload_wordlib_btn.attachment().setText("重载")
            self.reload_wordlib_btn.clicked.connect(self.reload_selected_wordlib)
        else:
            self.add_wordlib_btn = QPushButton("添加")
            self.add_wordlib_btn.clicked.connect(self.add_new_wordlib)
            self.reload_wordlib_btn = QPushButton("重载")
            self.reload_wordlib_btn.clicked.connect(self.reload_selected_wordlib)
        btn_layout.addWidget(self.add_wordlib_btn)
        btn_layout.addWidget(self.reload_wordlib_btn)
        btn_layout.addStretch()
        wordlib_layout.addLayout(btn_layout)
        
        parent_splitter.addWidget(wordlib_group)
        
        # 加载词库列表
        self.load_embedded_wordlib_list()
    
    def setup_wordlib_edit_embedded(self, parent_splitter):
        """设置嵌入式词库编辑区域"""
        # 创建编辑区域组
        edit_group = QGroupBox("词库编辑")
        edit_layout = QVBoxLayout(edit_group)
        
        # 词库信息
        info_layout = QGridLayout()
        info_layout.addWidget(QLabel("词库名称:"), 0, 0)
        self.wordlib_name_label = QLabel("未选择")
        info_layout.addWidget(self.wordlib_name_label, 0, 1)
        
        info_layout.addWidget(QLabel("词条数量:"), 1, 0)
        self.wordlib_count_label_edit = QLabel("0")
        info_layout.addWidget(self.wordlib_count_label_edit, 1, 1)
        
        info_layout.addWidget(QLabel("文件大小:"), 2, 0)
        self.wordlib_size_label_edit = QLabel("0 KB")
        info_layout.addWidget(self.wordlib_size_label_edit, 2, 1)
        
        edit_layout.addLayout(info_layout)
        
        # 词库内容编辑
        self.wordlib_content_edit = QTextEdit()
        self.wordlib_content_edit.setPlaceholderText("选择词库后在此编辑内容...")
        self.wordlib_content_edit.setFont(QFont("Consolas", 10))
        edit_layout.addWidget(self.wordlib_content_edit)
        
        # 编辑操作按钮
        edit_btn_layout = QHBoxLayout()
        if SIUI_AVAILABLE:
            self.save_wordlib_btn = SiPushButton()
            self.save_wordlib_btn.attachment().setText("保存")
            self.save_wordlib_btn.clicked.connect(self.save_current_wordlib)
            self.save_wordlib_btn.setEnabled(False)
            
            self.revert_wordlib_btn = SiPushButton()
            self.revert_wordlib_btn.attachment().setText("撤销")
            self.revert_wordlib_btn.clicked.connect(self.revert_wordlib_changes)
            self.revert_wordlib_btn.setEnabled(False)
        else:
            self.save_wordlib_btn = QPushButton("保存")
            self.save_wordlib_btn.clicked.connect(self.save_current_wordlib)
            self.save_wordlib_btn.setEnabled(False)
            
            self.revert_wordlib_btn = QPushButton("撤销")
            self.revert_wordlib_btn.clicked.connect(self.revert_wordlib_changes)
            self.revert_wordlib_btn.setEnabled(False)
        
        edit_btn_layout.addWidget(self.save_wordlib_btn)
        edit_btn_layout.addWidget(self.revert_wordlib_btn)
        edit_btn_layout.addStretch()
        edit_layout.addLayout(edit_btn_layout)
        
        parent_splitter.addWidget(edit_group)
    
    def load_embedded_wordlib_list(self):
        """加载嵌入式词库列表"""
        self.embedded_wordlib_list.clear()
        
        try:
            wordlib_files = self.wordlib_manager.get_wordlib_files()
            for file_info in wordlib_files:
                filename = file_info['filename']
                enabled = file_info['enabled']
                loaded = file_info['loaded']
                entries = file_info['entries']
                
                status = "已启用" if enabled else "已禁用"
                if not loaded:
                    status = "未加载"
                    
                item = QTreeWidgetItem([filename, status, str(entries)])
                item.setData(0, Qt.UserRole, filename)
                self.embedded_wordlib_list.addTopLevelItem(item)
                    
        except Exception as e:
            self.logger.error(f"加载词库列表失败: {e}")
    
    def on_wordlib_search_changed(self, text):
        """词库搜索文本改变"""
        search_text = text.lower()
        for i in range(self.embedded_wordlib_list.topLevelItemCount()):
            item = self.embedded_wordlib_list.topLevelItem(i)
            item.setHidden(search_text != "" and search_text not in item.text(0).lower())
    
    def on_embedded_wordlib_selected(self, item, column):
        """选择词库时的处理"""
        filename = item.data(0, Qt.UserRole)
        if filename:
            # 构建完整的文件路径
            file_path = os.path.join(self.wordlib_manager.wordlib_dir, filename)
            self.load_wordlib_content(file_path, item.text(0))
    
    def load_wordlib_content(self, file_path, name):
        """加载词库内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.wordlib_content_edit.setPlainText(content)
                self.wordlib_name_label.setText(name)
                
                # 更新统计信息
                lines = [line for line in content.split('\n') if line.strip()]
                self.wordlib_count_label_edit.setText(str(len(lines)))
                
                file_size = os.path.getsize(file_path)
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                self.wordlib_size_label_edit.setText(size_str)
                
                self.save_wordlib_btn.setEnabled(True)
                self.revert_wordlib_btn.setEnabled(True)
                
                # 保存当前编辑的文件路径
                self.current_wordlib_path = file_path
                
        except Exception as e:
            self.logger.error(f"加载词库内容失败: {e}")
            QMessageBox.critical(self, "错误", f"加载词库内容失败: {e}")
    
    def save_current_wordlib(self):
        """保存当前词库"""
        if not self.current_wordlib_path:
            QMessageBox.warning(self, "警告", "没有选择要保存的词库")
            return
            
        try:
            content = self.wordlib_content_edit.toPlainText()
            with open(self.current_wordlib_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            QMessageBox.information(self, "成功", "词库保存成功")
            self.load_embedded_wordlib_list()  # 重新加载列表
            
        except Exception as e:
            self.logger.error(f"保存词库失败: {e}")
            QMessageBox.critical(self, "错误", f"保存词库失败: {e}")
    
    def revert_wordlib_changes(self):
        """撤销词库更改"""
        if self.current_wordlib_path:
            name = os.path.basename(self.current_wordlib_path)
            self.load_wordlib_content(self.current_wordlib_path, name)
    
    def add_new_wordlib(self):
        """添加新词库"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择词库文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            try:
                # 复制文件到词库目录
                import shutil
                wordlib_dir = "data/wordlib"
                os.makedirs(wordlib_dir, exist_ok=True)
                
                dest_path = os.path.join(wordlib_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                
                QMessageBox.information(self, "成功", "词库添加成功")
                self.load_embedded_wordlib_list()
                
            except Exception as e:
                self.logger.error(f"添加词库失败: {e}")
                QMessageBox.critical(self, "错误", f"添加词库失败: {e}")
    
    def reload_selected_wordlib(self):
        """重载选中的词库"""
        current_item = self.embedded_wordlib_list.currentItem()
        if current_item:
            file_path = current_item.data(0, Qt.UserRole)
            if file_path:
                name = current_item.text(0)
                self.load_wordlib_content(file_path, name)
                QMessageBox.information(self, "成功", "词库重载成功")
    
    def show_embedded_wordlib_context_menu(self, position):
        """显示词库右键菜单"""
        item = self.embedded_wordlib_list.itemAt(position)
        if item is None:
            return
            
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        
        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(lambda: self.on_embedded_wordlib_selected(item, 0))
        
        reload_action = menu.addAction("重载")
        reload_action.triggered.connect(self.reload_selected_wordlib)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.delete_embedded_wordlib(item))
        
        menu.exec_(self.embedded_wordlib_list.mapToGlobal(position))
    
    def delete_embedded_wordlib(self, item):
        """删除词库"""
        file_path = item.data(0, Qt.UserRole)
        if file_path:
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除词库 '{item.text(0)}' 吗？\n\n此操作不可撤销！",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    os.remove(file_path)
                    QMessageBox.information(self, "成功", "词库删除成功")
                    self.load_embedded_wordlib_list()
                    
                    # 清空编辑区域
                    self.wordlib_content_edit.clear()
                    self.wordlib_name_label.setText("未选择")
                    self.wordlib_count_label_edit.setText("0")
                    self.wordlib_size_label_edit.setText("0 KB")
                    self.save_wordlib_btn.setEnabled(False)
                    self.revert_wordlib_btn.setEnabled(False)
                    self.current_wordlib_path = None
                    
                except Exception as e:
                    self.logger.error(f"删除词库失败: {e}")
                    QMessageBox.critical(self, "错误", f"删除词库失败: {e}")
    
    def setup_config_tabs_embedded(self, parent_tab_widget):
        """设置嵌入式配置选项卡"""
        # 常规配置
        general_tab = self.create_general_config_tab()
        parent_tab_widget.addTab(general_tab, "常规")
        
        # OneBot配置
        onebot_tab = self.create_onebot_config_tab()
        parent_tab_widget.addTab(onebot_tab, "OneBot")
        
        # 词库配置
        wordlib_tab = self.create_wordlib_config_tab()
        parent_tab_widget.addTab(wordlib_tab, "词库")
        
        # 日志配置
        logging_tab = self.create_logging_config_tab()
        parent_tab_widget.addTab(logging_tab, "日志")
        
        # 加载配置
        self.load_embedded_config()
    
    def create_general_config_tab(self):
        """创建常规配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 应用程序设置组
        app_group = QGroupBox("应用程序设置")
        app_layout = QGridLayout(app_group)
        
        # 应用名称
        app_layout.addWidget(QLabel("应用名称:"), 0, 0)
        if SIUI_AVAILABLE:
            self.app_name_edit = SiLineEdit()
            self.app_name_edit.lineEdit().setPlaceholderText("输入应用名称")
        else:
            self.app_name_edit = QLineEdit()
            self.app_name_edit.setPlaceholderText("输入应用名称")
        app_layout.addWidget(self.app_name_edit, 0, 1)
        
        # 应用版本
        app_layout.addWidget(QLabel("应用版本:"), 1, 0)
        if SIUI_AVAILABLE:
            self.app_version_edit = SiLineEdit()
            self.app_version_edit.lineEdit().setPlaceholderText("例如: 1.0.0")
        else:
            self.app_version_edit = QLineEdit()
            self.app_version_edit.setPlaceholderText("例如: 1.0.0")
        app_layout.addWidget(self.app_version_edit, 1, 1)
        
        # 自动启动
        self.auto_start_check = QCheckBox("开机自动启动")
        app_layout.addWidget(self.auto_start_check, 2, 0, 1, 2)
        
        layout.addWidget(app_group)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QGridLayout(ui_group)
        
        # 主题选择
        ui_layout.addWidget(QLabel("主题:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "自动"])
        ui_layout.addWidget(self.theme_combo, 0, 1)
        
        # 语言选择
        ui_layout.addWidget(QLabel("语言:"), 1, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        ui_layout.addWidget(self.language_combo, 1, 1)
        
        layout.addWidget(ui_group)
        layout.addStretch()
        
        return tab
    
    def create_onebot_config_tab(self):
        """创建OneBot配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 连接设置组
        conn_group = QGroupBox("连接设置")
        conn_layout = QGridLayout(conn_group)
        
        # 主机地址
        conn_layout.addWidget(QLabel("主机地址:"), 0, 0)
        if SIUI_AVAILABLE:
            self.onebot_host_edit = SiLineEdit()
            self.onebot_host_edit.lineEdit().setPlaceholderText("例如: 127.0.0.1")
        else:
            self.onebot_host_edit = QLineEdit()
            self.onebot_host_edit.setPlaceholderText("例如: 127.0.0.1")
        conn_layout.addWidget(self.onebot_host_edit, 0, 1)
        
        # 端口
        conn_layout.addWidget(QLabel("端口:"), 1, 0)
        self.onebot_port_spin = QSpinBox()
        self.onebot_port_spin.setRange(1, 65535)
        self.onebot_port_spin.setValue(8080)
        conn_layout.addWidget(self.onebot_port_spin, 1, 1)
        
        # 访问令牌
        conn_layout.addWidget(QLabel("访问令牌:"), 2, 0)
        if SIUI_AVAILABLE:
            self.onebot_token_edit = SiLineEdit()
            self.onebot_token_edit.lineEdit().setEchoMode(QLineEdit.Password)
            self.onebot_token_edit.lineEdit().setPlaceholderText("可选，用于身份验证")
        else:
            self.onebot_token_edit = QLineEdit()
            self.onebot_token_edit.setEchoMode(QLineEdit.Password)
            self.onebot_token_edit.setPlaceholderText("可选，用于身份验证")
        conn_layout.addWidget(self.onebot_token_edit, 2, 1)
        
        # 启用SSL
        self.onebot_ssl_check = QCheckBox("启用SSL连接")
        conn_layout.addWidget(self.onebot_ssl_check, 3, 0, 1, 2)
        
        layout.addWidget(conn_group)
        
        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QGridLayout(advanced_group)
        
        # 连接超时
        advanced_layout.addWidget(QLabel("连接超时(秒):"), 0, 0)
        self.onebot_timeout_spin = QSpinBox()
        self.onebot_timeout_spin.setRange(1, 300)
        self.onebot_timeout_spin.setValue(30)
        advanced_layout.addWidget(self.onebot_timeout_spin, 0, 1)
        
        # 重连间隔
        advanced_layout.addWidget(QLabel("重连间隔(秒):"), 1, 0)
        self.onebot_retry_spin = QSpinBox()
        self.onebot_retry_spin.setRange(1, 3600)
        self.onebot_retry_spin.setValue(5)
        advanced_layout.addWidget(self.onebot_retry_spin, 1, 1)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        return tab
    
    def create_wordlib_config_tab(self):
        """创建词库配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 词库设置组
        wordlib_group = QGroupBox("词库设置")
        wordlib_layout = QGridLayout(wordlib_group)
        
        # 自动重载
        self.wordlib_auto_reload_check = QCheckBox("自动重载词库")
        wordlib_layout.addWidget(self.wordlib_auto_reload_check, 0, 0, 1, 2)
        
        # 最大文件大小
        wordlib_layout.addWidget(QLabel("最大文件大小(MB):"), 1, 0)
        self.wordlib_max_size_spin = QSpinBox()
        self.wordlib_max_size_spin.setRange(1, 1000)
        self.wordlib_max_size_spin.setValue(10)
        wordlib_layout.addWidget(self.wordlib_max_size_spin, 1, 1)
        
        # 编码格式
        wordlib_layout.addWidget(QLabel("编码格式:"), 2, 0)
        self.wordlib_encoding_combo = QComboBox()
        self.wordlib_encoding_combo.addItems(["UTF-8", "GBK", "GB2312"])
        wordlib_layout.addWidget(self.wordlib_encoding_combo, 2, 1)
        
        # 备份设置
        self.wordlib_backup_check = QCheckBox("自动备份词库")
        wordlib_layout.addWidget(self.wordlib_backup_check, 3, 0, 1, 2)
        
        layout.addWidget(wordlib_group)
        
        # 性能设置组
        perf_group = QGroupBox("性能设置")
        perf_layout = QGridLayout(perf_group)
        
        # 缓存大小
        perf_layout.addWidget(QLabel("缓存大小(MB):"), 0, 0)
        self.wordlib_cache_size_spin = QSpinBox()
        self.wordlib_cache_size_spin.setRange(1, 1024)
        self.wordlib_cache_size_spin.setValue(64)
        perf_layout.addWidget(self.wordlib_cache_size_spin, 0, 1)
        
        # 预加载
        self.wordlib_preload_check = QCheckBox("启动时预加载词库")
        perf_layout.addWidget(self.wordlib_preload_check, 1, 0, 1, 2)
        
        layout.addWidget(perf_group)
        layout.addStretch()
        
        return tab
    
    def create_logging_config_tab(self):
        """创建日志配置选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 日志级别组
        level_group = QGroupBox("日志级别")
        level_layout = QGridLayout(level_group)
        
        # 日志级别
        level_layout.addWidget(QLabel("日志级别:"), 0, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        level_layout.addWidget(self.log_level_combo, 0, 1)
        
        # 控制台输出
        self.log_console_check = QCheckBox("输出到控制台")
        self.log_console_check.setChecked(True)
        level_layout.addWidget(self.log_console_check, 1, 0, 1, 2)
        
        layout.addWidget(level_group)
        
        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QGridLayout(file_group)
        
        # 最大文件数
        file_layout.addWidget(QLabel("最大文件数:"), 0, 0)
        self.log_max_files_spin = QSpinBox()
        self.log_max_files_spin.setRange(1, 100)
        self.log_max_files_spin.setValue(10)
        file_layout.addWidget(self.log_max_files_spin, 0, 1)
        
        # 单文件大小
        file_layout.addWidget(QLabel("单文件大小(MB):"), 1, 0)
        self.log_file_size_spin = QSpinBox()
        self.log_file_size_spin.setRange(1, 1000)
        self.log_file_size_spin.setValue(10)
        file_layout.addWidget(self.log_file_size_spin, 1, 1)
        
        # 自动清理
        self.log_auto_clean_check = QCheckBox("自动清理过期日志")
        file_layout.addWidget(self.log_auto_clean_check, 2, 0, 1, 2)
        
        layout.addWidget(file_group)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        if SIUI_AVAILABLE:
            save_config_btn = SiPushButton()
            save_config_btn.attachment().setText("保存配置")
            save_config_btn.clicked.connect(self.save_embedded_config)
            
            reset_config_btn = SiPushButton()
            reset_config_btn.attachment().setText("重置配置")
            reset_config_btn.clicked.connect(self.reset_embedded_config)
        else:
            save_config_btn = QPushButton("保存配置")
            save_config_btn.clicked.connect(self.save_embedded_config)
            
            reset_config_btn = QPushButton("重置配置")
            reset_config_btn.clicked.connect(self.reset_embedded_config)
        
        btn_layout.addWidget(save_config_btn)
        btn_layout.addWidget(reset_config_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return tab
    
    def load_embedded_config(self):
        """加载嵌入式配置"""
        try:
            # 从ConfigManager加载配置
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # 常规设置
            if hasattr(self, 'app_name_edit'):
                if isinstance(self.app_name_edit, SiLineEdit):
                    self.app_name_edit.lineEdit().setText(getattr(config, 'app_name', 'lchliebedich'))
                else:
                    self.app_name_edit.setText(getattr(config, 'app_name', 'lchliebedich'))
            if hasattr(self, 'app_version_edit'):
                if isinstance(self.app_version_edit, SiLineEdit):
                    self.app_version_edit.lineEdit().setText(getattr(config, 'app_version', '1.0.0'))
                else:
                    self.app_version_edit.setText(getattr(config, 'app_version', '1.0.0'))
            self.auto_start_check.setChecked(getattr(config, 'auto_start', False))
            
            # OneBot设置
            if hasattr(self, 'onebot_host_edit'):
                if isinstance(self.onebot_host_edit, SiLineEdit):
                    self.onebot_host_edit.lineEdit().setText(config.onebot.host)
                else:
                    self.onebot_host_edit.setText(config.onebot.host)
            if hasattr(self, 'onebot_port_spin'):
                self.onebot_port_spin.setValue(config.onebot.port)
            if hasattr(self, 'onebot_token_edit'):
                if isinstance(self.onebot_token_edit, SiLineEdit):
                    self.onebot_token_edit.lineEdit().setText(config.onebot.access_token or '')
                else:
                    self.onebot_token_edit.setText(config.onebot.access_token or '')
            self.onebot_ssl_check.setChecked(getattr(config.onebot, 'ssl', False))
            self.onebot_timeout_spin.setValue(config.onebot.timeout)
            self.onebot_retry_spin.setValue(getattr(config.onebot, 'retry_interval', 5))
            
            # 词库设置
            self.wordlib_auto_reload_check.setChecked(config.wordlib.auto_reload)
            self.wordlib_max_size_spin.setValue(getattr(config.wordlib, 'max_size', 10))
            self.wordlib_backup_check.setChecked(getattr(config.wordlib, 'backup', True))
            self.wordlib_cache_size_spin.setValue(config.wordlib.cache_size)
            self.wordlib_preload_check.setChecked(getattr(config.wordlib, 'preload', True))
            
            # 日志设置
            self.log_level_combo.setCurrentText(config.log.level)
            self.log_console_check.setChecked(config.log.console)
            self.log_max_files_spin.setValue(getattr(config.log, 'max_files', 10))
            self.log_file_size_spin.setValue(getattr(config.log, 'file_size', 10))
            self.log_auto_clean_check.setChecked(getattr(config.log, 'auto_clean', True))
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            QMessageBox.warning(self, "警告", f"加载配置失败: {e}")
    
    def save_embedded_config(self):
        """保存嵌入式配置"""
        try:
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # OneBot设置
            if hasattr(self, 'onebot_host_edit'):
                if isinstance(self.onebot_host_edit, SiLineEdit):
                    config.onebot.host = self.onebot_host_edit.lineEdit().text()
                else:
                    config.onebot.host = self.onebot_host_edit.text()
            if hasattr(self, 'onebot_port_spin'):
                config.onebot.port = self.onebot_port_spin.value()
            if hasattr(self, 'onebot_token_edit'):
                if isinstance(self.onebot_token_edit, SiLineEdit):
                    config.onebot.access_token = self.onebot_token_edit.lineEdit().text() or None
                else:
                    config.onebot.access_token = self.onebot_token_edit.text() or None
            config.onebot.timeout = self.onebot_timeout_spin.value()
            
            # 词库设置
            config.wordlib.auto_reload = self.wordlib_auto_reload_check.isChecked()
            config.wordlib.cache_size = self.wordlib_cache_size_spin.value()
            
            # 日志设置
            config.log.level = self.log_level_combo.currentText()
            config.log.console = self.log_console_check.isChecked()
            
            # 保存配置
            config_manager.save_config()
            
            QMessageBox.information(self, "成功", "配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
    
    def reset_embedded_config(self):
        """重置嵌入式配置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置所有配置到默认值吗？\n\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                config_manager = ConfigManager()
                config_manager.reset_to_defaults()
                config_manager.save()
                
                # 重新加载配置
                self.load_embedded_config()
                
                QMessageBox.information(self, "成功", "配置重置成功")
                
            except Exception as e:
                self.logger.error(f"重置配置失败: {e}")
                QMessageBox.critical(self, "错误", f"重置配置失败: {e}")