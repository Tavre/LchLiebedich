#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt5统计窗口模块
使用PyQt-SiliconUI主题的统计信息界面
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QGroupBox,
    QFormLayout, QProgressBar, QTextEdit, QSplitter,
    QHeaderView, QAbstractItemView, QMessageBox, QFileDialog,
    QComboBox, QDateTimeEdit, QSpinBox, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QPalette, QColor
from siui.components import SiDenseHContainer, SiDenseVContainer
from siui.components.widgets import SiLabel, SiPushButton, SiLineEdit
from siui.templates.application.application import SiliconApplication

import json
import csv
import time
import psutil
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    FigureCanvas = None
    Figure = None

from ..utils.logger import get_logger

class StatsWindowQt(SiliconApplication):
    """PyQt5统计窗口类"""
    
    def __init__(self, wordlib_manager=None, onebot_engine=None, parent=None):
        super().__init__(parent)
        
        self.wordlib_manager = wordlib_manager
        self.onebot_engine = onebot_engine
        self.logger = get_logger("StatsWindowQt")
        
        # 统计数据
        self.stats_data = {
            'message_stats': defaultdict(int),
            'user_stats': defaultdict(int),
            'group_stats': defaultdict(int),
            'wordlib_stats': defaultdict(int),
            'time_stats': defaultdict(int),
            'performance_stats': defaultdict(list)
        }
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        
        self.setup_ui()
        self.load_stats()
        self.start_auto_update()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("统计信息")
        self.resize(1200, 800)
        
        # 创建主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 创建工具栏
        self.setup_toolbar(main_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个统计页面
        self.setup_overview_tab()
        self.setup_message_stats_tab()
        self.setup_user_stats_tab()
        self.setup_wordlib_stats_tab()
        self.setup_performance_tab()
        self.setup_charts_tab()
        
        # 创建状态栏
        self.setup_status_bar(main_layout)
        
    def setup_toolbar(self, parent_layout):
        """设置工具栏"""
        toolbar_container = SiDenseHContainer()
        
        # 刷新按钮
        self.refresh_btn = SiPushButton("刷新统计")
        self.refresh_btn.clicked.connect(self.refresh_stats)
        
        # 导出按钮
        self.export_btn = SiPushButton("导出数据")
        self.export_btn.clicked.connect(self.export_stats)
        
        # 清空按钮
        self.clear_btn = SiPushButton("清空统计")
        self.clear_btn.clicked.connect(self.clear_stats)
        
        # 自动更新开关
        self.auto_update_check = QCheckBox("自动更新")
        self.auto_update_check.setChecked(True)
        self.auto_update_check.toggled.connect(self.toggle_auto_update)
        
        # 更新间隔
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 300)
        self.update_interval_spin.setValue(30)
        self.update_interval_spin.setSuffix(" 秒")
        self.update_interval_spin.valueChanged.connect(self.change_update_interval)
        
        toolbar_container.addWidget(self.refresh_btn)
        toolbar_container.addWidget(self.export_btn)
        toolbar_container.addWidget(self.clear_btn)
        toolbar_container.addWidget(SiLabel("|"))
        toolbar_container.addWidget(self.auto_update_check)
        toolbar_container.addWidget(SiLabel("更新间隔:"))
        toolbar_container.addWidget(self.update_interval_spin)
        
        parent_layout.addWidget(toolbar_container)
        
    def setup_overview_tab(self):
        """设置概览页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建概览卡片
        cards_container = QHBoxLayout()
        
        # 消息统计卡片
        self.message_card = self.create_stats_card("消息统计", [
            ("总消息数", "0"),
            ("今日消息", "0"),
            ("平均每小时", "0")
        ])
        cards_container.addWidget(self.message_card)
        
        # 用户统计卡片
        self.user_card = self.create_stats_card("用户统计", [
            ("活跃用户", "0"),
            ("新用户", "0"),
            ("总用户数", "0")
        ])
        cards_container.addWidget(self.user_card)
        
        # 群组统计卡片
        self.group_card = self.create_stats_card("群组统计", [
            ("活跃群组", "0"),
            ("总群组数", "0"),
            ("平均群成员", "0")
        ])
        cards_container.addWidget(self.group_card)
        
        # 词库统计卡片
        self.wordlib_card = self.create_stats_card("词库统计", [
            ("词库数量", "0"),
            ("触发次数", "0"),
            ("命中率", "0%")
        ])
        cards_container.addWidget(self.wordlib_card)
        
        layout.addLayout(cards_container)
        
        # 实时活动图表区域
        activity_group = QGroupBox("实时活动")
        activity_layout = QVBoxLayout(activity_group)
        
        # 活动时间线
        self.activity_text = QTextEdit()
        self.activity_text.setMaximumHeight(200)
        self.activity_text.setReadOnly(True)
        activity_layout.addWidget(self.activity_text)
        
        layout.addWidget(activity_group)
        
        # 系统状态
        system_group = QGroupBox("系统状态")
        system_layout = QFormLayout(system_group)
        
        self.uptime_label = SiLabel("0 天 0 小时 0 分钟")
        self.memory_usage_label = SiLabel("0 MB")
        self.cpu_usage_label = SiLabel("0%")
        self.connection_status_label = SiLabel("未连接")
        
        system_layout.addRow("运行时间:", self.uptime_label)
        system_layout.addRow("内存使用:", self.memory_usage_label)
        system_layout.addRow("CPU使用:", self.cpu_usage_label)
        system_layout.addRow("连接状态:", self.connection_status_label)
        
        layout.addWidget(system_group)
        
        self.tab_widget.addTab(tab, "概览")
        
    def setup_message_stats_tab(self):
        """设置消息统计页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 过滤器
        filter_container = SiDenseHContainer()
        
        filter_container.addWidget(SiLabel("时间范围:"))
        self.msg_time_combo = QComboBox()
        self.msg_time_combo.addItems(["今天", "昨天", "本周", "本月", "全部"])
        self.msg_time_combo.currentTextChanged.connect(self.update_message_stats)
        filter_container.addWidget(self.msg_time_combo)
        
        filter_container.addWidget(SiLabel("消息类型:"))
        self.msg_type_combo = QComboBox()
        self.msg_type_combo.addItems(["全部", "文本", "图片", "语音", "视频", "文件"])
        self.msg_type_combo.currentTextChanged.connect(self.update_message_stats)
        filter_container.addWidget(self.msg_type_combo)
        
        layout.addWidget(filter_container)
        
        # 消息统计表格
        self.message_table = QTableWidget()
        self.message_table.setColumnCount(6)
        self.message_table.setHorizontalHeaderLabels([
            "时间", "消息数量", "用户数", "群组数", "平均长度", "类型分布"
        ])
        self.message_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.message_table)
        
        self.tab_widget.addTab(tab, "消息统计")
        
    def setup_user_stats_tab(self):
        """设置用户统计页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 用户排行榜
        ranking_group = QGroupBox("用户排行榜")
        ranking_layout = QVBoxLayout(ranking_group)
        
        # 排行榜类型选择
        ranking_combo = QComboBox()
        ranking_combo.addItems(["消息数量", "活跃度", "词库触发", "在线时长"])
        ranking_layout.addWidget(ranking_combo)
        
        # 排行榜表格
        self.user_ranking_table = QTableWidget()
        self.user_ranking_table.setColumnCount(4)
        self.user_ranking_table.setHorizontalHeaderLabels(["排名", "用户ID", "昵称", "数值"])
        ranking_layout.addWidget(self.user_ranking_table)
        
        splitter.addWidget(ranking_group)
        
        # 用户详细信息
        detail_group = QGroupBox("用户详细信息")
        detail_layout = QVBoxLayout(detail_group)
        
        # 用户搜索
        search_container = SiDenseHContainer()
        search_container.addWidget(SiLabel("搜索用户:"))
        self.user_search_edit = SiLineEdit()
        self.user_search_edit.setPlaceholderText("输入用户ID或昵称...")
        search_container.addWidget(self.user_search_edit)
        
        self.user_search_btn = SiPushButton("搜索")
        search_container.addWidget(self.user_search_btn)
        
        detail_layout.addWidget(search_container)
        
        # 用户信息显示
        self.user_info_text = QTextEdit()
        self.user_info_text.setReadOnly(True)
        detail_layout.addWidget(self.user_info_text)
        
        splitter.addWidget(detail_group)
        
        layout.addWidget(splitter)
        self.tab_widget.addTab(tab, "用户统计")
        
    def setup_wordlib_stats_tab(self):
        """设置词库统计页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 词库统计表格
        self.wordlib_table = QTableWidget()
        self.wordlib_table.setColumnCount(7)
        self.wordlib_table.setHorizontalHeaderLabels([
            "词库名称", "触发次数", "成功次数", "成功率", "平均响应时间", "最后触发", "状态"
        ])
        self.wordlib_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.wordlib_table)
        
        # 词库详细信息
        detail_group = QGroupBox("词库详细信息")
        detail_layout = QVBoxLayout(detail_group)
        
        self.wordlib_detail_text = QTextEdit()
        self.wordlib_detail_text.setReadOnly(True)
        self.wordlib_detail_text.setMaximumHeight(150)
        detail_layout.addWidget(self.wordlib_detail_text)
        
        layout.addWidget(detail_group)
        
        self.tab_widget.addTab(tab, "词库统计")
        
    def setup_performance_tab(self):
        """设置性能统计页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 性能指标卡片
        perf_cards_container = QHBoxLayout()
        
        # 响应时间卡片
        self.response_time_card = self.create_stats_card("响应时间", [
            ("平均响应", "0 ms"),
            ("最快响应", "0 ms"),
            ("最慢响应", "0 ms")
        ])
        perf_cards_container.addWidget(self.response_time_card)
        
        # 吞吐量卡片
        self.throughput_card = self.create_stats_card("吞吐量", [
            ("每秒请求", "0"),
            ("每分钟消息", "0"),
            ("峰值QPS", "0")
        ])
        perf_cards_container.addWidget(self.throughput_card)
        
        # 错误率卡片
        self.error_rate_card = self.create_stats_card("错误率", [
            ("总错误数", "0"),
            ("错误率", "0%"),
            ("最近错误", "无")
        ])
        perf_cards_container.addWidget(self.error_rate_card)
        
        layout.addLayout(perf_cards_container)
        
        # 性能历史图表
        history_group = QGroupBox("性能历史")
        history_layout = QVBoxLayout(history_group)
        
        # 图表类型选择
        chart_type_container = SiDenseHContainer()
        chart_type_container.addWidget(SiLabel("图表类型:"))
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["响应时间", "吞吐量", "错误率", "内存使用", "CPU使用"])
        chart_type_container.addWidget(self.chart_type_combo)
        
        chart_type_container.addWidget(SiLabel("时间范围:"))
        self.chart_time_combo = QComboBox()
        self.chart_time_combo.addItems(["最近1小时", "最近6小时", "最近24小时", "最近7天"])
        chart_type_container.addWidget(self.chart_time_combo)
        
        history_layout.addWidget(chart_type_container)
        
        # 图表显示区域（这里用文本框模拟，实际可以集成matplotlib或其他图表库）
        self.performance_chart = QTextEdit()
        self.performance_chart.setReadOnly(True)
        self.performance_chart.setPlaceholderText("性能图表将在此显示...")
        history_layout.addWidget(self.performance_chart)
        
        layout.addWidget(history_group)
        
        self.tab_widget.addTab(tab, "性能统计")
        
    def setup_charts_tab(self):
        """设置图表页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 图表控制面板
        control_group = QGroupBox("图表控制")
        control_layout = QHBoxLayout(control_group)
        
        # 图表类型选择
        control_layout.addWidget(SiLabel("图表类型:"))
        self.main_chart_type_combo = QComboBox()
        self.main_chart_type_combo.addItems([
            "消息趋势图", "用户活跃度", "群组活跃度", "词库使用率", 
            "响应时间分布", "错误统计", "系统资源使用", "实时性能监控"
        ])
        control_layout.addWidget(self.main_chart_type_combo)
        
        # 时间范围选择
        control_layout.addWidget(SiLabel("时间范围:"))
        self.main_chart_time_combo = QComboBox()
        self.main_chart_time_combo.addItems(["最近1小时", "最近6小时", "最近24小时", "最近7天", "最近30天"])
        control_layout.addWidget(self.main_chart_time_combo)
        
        # 图表样式选择
        control_layout.addWidget(SiLabel("图表样式:"))
        self.chart_style_combo = QComboBox()
        self.chart_style_combo.addItems(["线图", "柱状图", "饼图", "散点图", "热力图"])
        control_layout.addWidget(self.chart_style_combo)
        
        # 控制按钮
        self.generate_chart_btn = SiPushButton("生成图表")
        self.generate_chart_btn.clicked.connect(self.generate_chart)
        control_layout.addWidget(self.generate_chart_btn)
        
        self.save_chart_btn = SiPushButton("保存图表")
        self.save_chart_btn.clicked.connect(self.save_chart)
        control_layout.addWidget(self.save_chart_btn)
        
        layout.addWidget(control_group)
        
        # 图表显示区域
        if MATPLOTLIB_AVAILABLE:
            # 使用matplotlib图表
            self.chart_figure = Figure(figsize=(12, 8))
            self.chart_canvas = FigureCanvas(self.chart_figure)
            layout.addWidget(self.chart_canvas)
        else:
            # 降级到文本显示
            self.main_chart_area = QTextEdit()
            self.main_chart_area.setReadOnly(True)
            self.main_chart_area.setPlaceholderText("matplotlib未安装，无法显示图表。请安装matplotlib以获得完整功能。")
            layout.addWidget(self.main_chart_area)
        
        self.tab_widget.addTab(tab, "图表分析")
        
    def setup_status_bar(self, parent_layout):
        """设置状态栏"""
        status_container = SiDenseHContainer()
        
        self.status_label = SiLabel("就绪")
        self.last_update_label = SiLabel("最后更新: 从未")
        self.data_source_label = SiLabel("数据源: 本地")
        
        status_container.addWidget(self.status_label)
        status_container.addWidget(self.last_update_label)
        status_container.addWidget(self.data_source_label)
        
        parent_layout.addWidget(status_container)
        
    def create_stats_card(self, title: str, stats: List[tuple]) -> QGroupBox:
        """创建统计卡片"""
        card = QGroupBox(title)
        layout = QFormLayout(card)
        
        # 存储标签引用以便后续更新
        if not hasattr(self, 'card_labels'):
            self.card_labels = {}
        self.card_labels[title] = {}
        
        for label, value in stats:
            value_label = SiLabel(value)
            value_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            layout.addRow(f"{label}:", value_label)
            self.card_labels[title][label] = value_label
            
        return card
        
    def update_card_value(self, card_title: str, label: str, value: str):
        """更新卡片值"""
        if (card_title in self.card_labels and 
            label in self.card_labels[card_title]):
            self.card_labels[card_title][label].setText(value)
            
    def load_stats(self):
        """加载统计数据"""
        try:
            # 从各个组件收集统计数据
            self.collect_message_stats()
            self.collect_user_stats()
            self.collect_wordlib_stats()
            self.collect_performance_stats()
            
            # 更新界面显示
            self.update_overview()
            self.update_message_stats()
            self.update_user_stats()
            self.update_wordlib_stats()
            self.update_performance_stats()
            
            self.last_update_label.setText(f"最后更新: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.logger.error(f"加载统计数据失败: {e}")
            
    def collect_message_stats(self):
        """收集消息统计"""
        # 这里应该从实际的消息处理组件收集数据
        # 暂时使用模拟数据
        now = datetime.now()
        today = now.date()
        
        self.stats_data['message_stats'] = {
            'total_messages': 12345,
            'today_messages': 234,
            'hourly_average': 15.6,
            'message_types': {
                'text': 8000,
                'image': 2000,
                'voice': 1500,
                'video': 500,
                'file': 345
            }
        }
        
    def collect_user_stats(self):
        """收集用户统计"""
        self.stats_data['user_stats'] = {
            'active_users': 156,
            'new_users': 12,
            'total_users': 1234,
            'user_ranking': [
                {'user_id': '123456', 'nickname': '用户A', 'messages': 500},
                {'user_id': '234567', 'nickname': '用户B', 'messages': 450},
                {'user_id': '345678', 'nickname': '用户C', 'messages': 400},
            ]
        }
        
    def collect_wordlib_stats(self):
        """收集词库统计"""
        if self.wordlib_manager:
            try:
                wordlibs = self.wordlib_manager.get_all_wordlibs()
                self.stats_data['wordlib_stats'] = {
                    'total_wordlibs': len(wordlibs),
                    'total_triggers': 567,
                    'success_rate': 85.6,
                    'wordlib_details': []
                }
                
                for wordlib in wordlibs:
                    detail = {
                        'name': wordlib.get('name', 'Unknown'),
                        'triggers': 45,
                        'success': 38,
                        'success_rate': 84.4,
                        'avg_response_time': 125,
                        'last_trigger': '2024-01-15 14:30:25',
                        'status': 'active'
                    }
                    self.stats_data['wordlib_stats']['wordlib_details'].append(detail)
                    
            except Exception as e:
                self.logger.error(f"收集词库统计失败: {e}")
                
    def collect_performance_stats(self):
        """收集性能统计"""
        try:
            # 收集真实的系统性能数据
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 网络统计
            net_io = psutil.net_io_counters()
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            process_cpu = process.cpu_percent()
            
            # 更新性能历史数据
            current_time = datetime.now()
            if not hasattr(self, 'performance_history'):
                self.performance_history = {
                    'timestamps': [],
                    'cpu_usage': [],
                    'memory_usage': [],
                    'process_memory': [],
                    'response_times': []
                }
            
            # 保持最近100个数据点
            max_points = 100
            self.performance_history['timestamps'].append(current_time)
            self.performance_history['cpu_usage'].append(cpu_percent)
            self.performance_history['memory_usage'].append(memory.percent)
            self.performance_history['process_memory'].append(process_memory)
            
            # 模拟响应时间（实际应该从业务逻辑中获取）
            response_time = np.random.normal(0.15, 0.05)  # 平均150ms，标准差50ms
            self.performance_history['response_times'].append(max(0.01, response_time))
            
            # 限制历史数据长度
            for key in self.performance_history:
                if len(self.performance_history[key]) > max_points:
                    self.performance_history[key] = self.performance_history[key][-max_points:]
            
            self.stats_data['performance_stats'] = {
                'avg_response_time': np.mean(self.performance_history['response_times'][-10:]) * 1000 if self.performance_history['response_times'] else 125.6,
                'min_response_time': np.min(self.performance_history['response_times']) * 1000 if self.performance_history['response_times'] else 45.2,
                'max_response_time': np.max(self.performance_history['response_times']) * 1000 if self.performance_history['response_times'] else 1250.8,
                'requests_per_second': 12.5,  # 这个需要从实际业务逻辑中获取
                'messages_per_minute': 25.8,  # 这个需要从实际业务逻辑中获取
                'peak_qps': 45.2,  # 这个需要从实际业务逻辑中获取
                'total_errors': 23,  # 这个需要从实际业务逻辑中获取
                'error_rate': 1.8,  # 这个需要从实际业务逻辑中获取
                'memory_usage': process_memory,
                'cpu_usage': cpu_percent,
                'system_memory_percent': memory.percent,
                'system_memory_total': memory.total / 1024 / 1024 / 1024,  # GB
                'system_memory_available': memory.available / 1024 / 1024 / 1024,  # GB
                'disk_usage': disk.percent,
                'disk_total': disk.total / 1024 / 1024 / 1024,  # GB
                'disk_free': disk.free / 1024 / 1024 / 1024,  # GB
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'uptime': psutil.boot_time()
            }
            
        except Exception as e:
            self.logger.error(f"收集性能统计失败: {e}")
            # 使用默认值
            self.stats_data['performance_stats'] = {
                'avg_response_time': 125.6,
                'min_response_time': 45.2,
                'max_response_time': 1250.8,
                'requests_per_second': 12.5,
                'messages_per_minute': 25.8,
                'peak_qps': 45.2,
                'total_errors': 23,
                'error_rate': 1.8,
                'memory_usage': 156.7,
                'cpu_usage': 15.6
            }
        
    def update_overview(self):
        """更新概览页面"""
        # 更新消息统计卡片
        msg_stats = self.stats_data['message_stats']
        self.update_card_value("消息统计", "总消息数", str(msg_stats.get('total_messages', 0)))
        self.update_card_value("消息统计", "今日消息", str(msg_stats.get('today_messages', 0)))
        self.update_card_value("消息统计", "平均每小时", f"{msg_stats.get('hourly_average', 0):.1f}")
        
        # 更新用户统计卡片
        user_stats = self.stats_data['user_stats']
        self.update_card_value("用户统计", "活跃用户", str(user_stats.get('active_users', 0)))
        self.update_card_value("用户统计", "新用户", str(user_stats.get('new_users', 0)))
        self.update_card_value("用户统计", "总用户数", str(user_stats.get('total_users', 0)))
        
        # 更新群组统计卡片
        self.update_card_value("群组统计", "活跃群组", "25")
        self.update_card_value("群组统计", "总群组数", "45")
        self.update_card_value("群组统计", "平均群成员", "156")
        
        # 更新词库统计卡片
        wordlib_stats = self.stats_data['wordlib_stats']
        self.update_card_value("词库统计", "词库数量", str(wordlib_stats.get('total_wordlibs', 0)))
        self.update_card_value("词库统计", "触发次数", str(wordlib_stats.get('total_triggers', 0)))
        self.update_card_value("词库统计", "命中率", f"{wordlib_stats.get('success_rate', 0):.1f}%")
        
        # 更新系统状态
        perf_stats = self.stats_data['performance_stats']
        self.memory_usage_label.setText(f"{perf_stats.get('memory_usage', 0):.1f} MB")
        self.cpu_usage_label.setText(f"{perf_stats.get('cpu_usage', 0):.1f}%")
        
        # 更新活动时间线
        activity_text = "最近活动:\n"
        activity_text += f"[{datetime.now().strftime('%H:%M:%S')}] 收到新消息\n"
        activity_text += f"[{(datetime.now() - timedelta(minutes=2)).strftime('%H:%M:%S')}] 词库触发\n"
        activity_text += f"[{(datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S')}] 用户加入群组\n"
        self.activity_text.setPlainText(activity_text)
        
    def update_message_stats(self):
        """更新消息统计页面"""
        # 清空表格
        self.message_table.setRowCount(0)
        
        # 添加示例数据
        sample_data = [
            ["今天", "234", "45", "12", "25.6", "文本:80%, 图片:15%, 其他:5%"],
            ["昨天", "456", "67", "15", "28.3", "文本:75%, 图片:20%, 其他:5%"],
            ["前天", "389", "52", "11", "22.1", "文本:85%, 图片:10%, 其他:5%"]
        ]
        
        for row_data in sample_data:
            row = self.message_table.rowCount()
            self.message_table.insertRow(row)
            for col, data in enumerate(row_data):
                self.message_table.setItem(row, col, QTableWidgetItem(str(data)))
                
    def update_user_stats(self):
        """更新用户统计页面"""
        # 更新用户排行榜
        self.user_ranking_table.setRowCount(0)
        
        user_stats = self.stats_data['user_stats']
        ranking = user_stats.get('user_ranking', [])
        
        for i, user in enumerate(ranking):
            row = self.user_ranking_table.rowCount()
            self.user_ranking_table.insertRow(row)
            self.user_ranking_table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            self.user_ranking_table.setItem(row, 1, QTableWidgetItem(user['user_id']))
            self.user_ranking_table.setItem(row, 2, QTableWidgetItem(user['nickname']))
            self.user_ranking_table.setItem(row, 3, QTableWidgetItem(str(user['messages'])))
            
    def update_wordlib_stats(self):
        """更新词库统计页面"""
        # 清空表格
        self.wordlib_table.setRowCount(0)
        
        wordlib_stats = self.stats_data['wordlib_stats']
        details = wordlib_stats.get('wordlib_details', [])
        
        for detail in details:
            row = self.wordlib_table.rowCount()
            self.wordlib_table.insertRow(row)
            self.wordlib_table.setItem(row, 0, QTableWidgetItem(detail['name']))
            self.wordlib_table.setItem(row, 1, QTableWidgetItem(str(detail['triggers'])))
            self.wordlib_table.setItem(row, 2, QTableWidgetItem(str(detail['success'])))
            self.wordlib_table.setItem(row, 3, QTableWidgetItem(f"{detail['success_rate']:.1f}%"))
            self.wordlib_table.setItem(row, 4, QTableWidgetItem(f"{detail['avg_response_time']:.1f}ms"))
            self.wordlib_table.setItem(row, 5, QTableWidgetItem(detail['last_trigger']))
            self.wordlib_table.setItem(row, 6, QTableWidgetItem(detail['status']))
            
    def update_performance_stats(self):
        """更新性能统计页面"""
        perf_stats = self.stats_data['performance_stats']
        
        # 更新响应时间卡片
        self.update_card_value("响应时间", "平均响应", f"{perf_stats.get('avg_response_time', 0):.1f} ms")
        self.update_card_value("响应时间", "最快响应", f"{perf_stats.get('min_response_time', 0):.1f} ms")
        self.update_card_value("响应时间", "最慢响应", f"{perf_stats.get('max_response_time', 0):.1f} ms")
        
        # 更新吞吐量卡片
        self.update_card_value("吞吐量", "每秒请求", f"{perf_stats.get('requests_per_second', 0):.1f}")
        self.update_card_value("吞吐量", "每分钟消息", f"{perf_stats.get('messages_per_minute', 0):.1f}")
        self.update_card_value("吞吐量", "峰值QPS", f"{perf_stats.get('peak_qps', 0):.1f}")
        
        # 更新错误率卡片
        self.update_card_value("错误率", "总错误数", str(perf_stats.get('total_errors', 0)))
        self.update_card_value("错误率", "错误率", f"{perf_stats.get('error_rate', 0):.1f}%")
        self.update_card_value("错误率", "最近错误", "网络超时")
        
    def generate_chart(self):
        """生成图表"""
        chart_type = self.main_chart_type_combo.currentText()
        time_range = self.main_chart_time_combo.currentText()
        chart_style = self.chart_style_combo.currentText()
        
        if not MATPLOTLIB_AVAILABLE:
            # 降级到文本显示
            chart_text = f"图表类型: {chart_type}\n"
            chart_text += f"时间范围: {time_range}\n"
            chart_text += f"图表样式: {chart_style}\n\n"
            chart_text += "matplotlib未安装，无法显示图表。\n"
            chart_text += "请安装matplotlib以获得完整功能：pip install matplotlib\n\n"
            chart_text += "模拟数据:\n"
            chart_text += "时间\t\t数值\n"
            chart_text += "10:00\t\t125\n"
            chart_text += "11:00\t\t156\n"
            chart_text += "12:00\t\t189\n"
            chart_text += "13:00\t\t234\n"
            chart_text += "14:00\t\t198\n"
            
            if hasattr(self, 'main_chart_area'):
                self.main_chart_area.setPlainText(chart_text)
            return
        
        try:
            # 清除之前的图表
            self.chart_figure.clear()
            
            # 根据图表类型生成不同的图表
            if chart_type == "消息趋势图":
                self._generate_message_trend_chart(time_range, chart_style)
            elif chart_type == "用户活跃度":
                self._generate_user_activity_chart(time_range, chart_style)
            elif chart_type == "系统资源使用":
                self._generate_system_resource_chart(time_range, chart_style)
            elif chart_type == "实时性能监控":
                self._generate_realtime_performance_chart()
            elif chart_type == "响应时间分布":
                self._generate_response_time_chart(time_range, chart_style)
            else:
                self._generate_default_chart(chart_type, time_range, chart_style)
            
            # 刷新画布
            self.chart_canvas.draw()
            
        except Exception as e:
            self.logger.error(f"生成图表失败: {e}")
            # 显示错误信息
            ax = self.chart_figure.add_subplot(111)
            ax.text(0.5, 0.5, f"生成图表时出错:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='red')
            ax.set_title(f"错误 - {chart_type}")
            self.chart_canvas.draw()
        
    def _generate_message_trend_chart(self, time_range, chart_style):
        """生成消息趋势图"""
        ax = self.chart_figure.add_subplot(111)
        
        # 生成模拟数据
        hours = list(range(24))
        messages = [np.random.randint(50, 200) for _ in hours]
        
        if chart_style == "线图":
            ax.plot(hours, messages, marker='o', linewidth=2, markersize=4)
        elif chart_style == "柱状图":
            ax.bar(hours, messages, alpha=0.7)
        
        ax.set_title(f"消息趋势图 - {time_range}", fontsize=14, fontweight='bold')
        ax.set_xlabel("小时")
        ax.set_ylabel("消息数量")
        ax.grid(True, alpha=0.3)
        
    def _generate_user_activity_chart(self, time_range, chart_style):
        """生成用户活跃度图"""
        ax = self.chart_figure.add_subplot(111)
        
        # 生成模拟数据
        users = ['用户A', '用户B', '用户C', '用户D', '用户E']
        activity = [np.random.randint(10, 100) for _ in users]
        
        if chart_style == "柱状图":
            bars = ax.bar(users, activity, alpha=0.7, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
            # 添加数值标签
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{int(height)}', ha='center', va='bottom')
        elif chart_style == "饼图":
            ax.pie(activity, labels=users, autopct='%1.1f%%', startangle=90)
        
        ax.set_title(f"用户活跃度 - {time_range}", fontsize=14, fontweight='bold')
        
    def _generate_system_resource_chart(self, time_range, chart_style):
        """生成系统资源使用图"""
        if hasattr(self, 'performance_history') and self.performance_history['timestamps']:
            # 使用真实数据
            timestamps = self.performance_history['timestamps'][-50:]  # 最近50个数据点
            cpu_data = self.performance_history['cpu_usage'][-50:]
            memory_data = self.performance_history['memory_usage'][-50:]
            
            ax = self.chart_figure.add_subplot(111)
            
            if chart_style == "线图":
                ax.plot(timestamps, cpu_data, label='CPU使用率 (%)', marker='o', markersize=3)
                ax.plot(timestamps, memory_data, label='内存使用率 (%)', marker='s', markersize=3)
            
            ax.set_title(f"系统资源使用 - {time_range}", fontsize=14, fontweight='bold')
            ax.set_xlabel("时间")
            ax.set_ylabel("使用率 (%)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 格式化时间轴
            ax.tick_params(axis='x', rotation=45)
        else:
            # 使用模拟数据
            self._generate_default_chart("系统资源使用", time_range, chart_style)
    
    def _generate_realtime_performance_chart(self):
        """生成实时性能监控图"""
        if hasattr(self, 'performance_history') and self.performance_history['timestamps']:
            # 创建子图
            fig = self.chart_figure
            fig.suptitle('实时性能监控', fontsize=16, fontweight='bold')
            
            # CPU使用率
            ax1 = fig.add_subplot(2, 2, 1)
            timestamps = self.performance_history['timestamps'][-20:]
            cpu_data = self.performance_history['cpu_usage'][-20:]
            ax1.plot(timestamps, cpu_data, 'b-', linewidth=2)
            ax1.set_title('CPU使用率')
            ax1.set_ylabel('%')
            ax1.grid(True, alpha=0.3)
            
            # 内存使用率
            ax2 = fig.add_subplot(2, 2, 2)
            memory_data = self.performance_history['memory_usage'][-20:]
            ax2.plot(timestamps, memory_data, 'r-', linewidth=2)
            ax2.set_title('内存使用率')
            ax2.set_ylabel('%')
            ax2.grid(True, alpha=0.3)
            
            # 响应时间
            ax3 = fig.add_subplot(2, 2, 3)
            response_times = [t * 1000 for t in self.performance_history['response_times'][-20:]]  # 转换为ms
            ax3.plot(timestamps, response_times, 'g-', linewidth=2)
            ax3.set_title('响应时间')
            ax3.set_ylabel('ms')
            ax3.grid(True, alpha=0.3)
            
            # 进程内存使用
            ax4 = fig.add_subplot(2, 2, 4)
            process_memory = self.performance_history['process_memory'][-20:]
            ax4.plot(timestamps, process_memory, 'm-', linewidth=2)
            ax4.set_title('进程内存使用')
            ax4.set_ylabel('MB')
            ax4.grid(True, alpha=0.3)
            
            # 调整布局
            fig.tight_layout()
        else:
            self._generate_default_chart("实时性能监控", "实时", "线图")
    
    def _generate_response_time_chart(self, time_range, chart_style):
        """生成响应时间分布图"""
        ax = self.chart_figure.add_subplot(111)
        
        if hasattr(self, 'performance_history') and self.performance_history['response_times']:
            response_times = [t * 1000 for t in self.performance_history['response_times']]  # 转换为ms
            
            if chart_style == "散点图":
                x = list(range(len(response_times)))
                ax.scatter(x, response_times, alpha=0.6)
            else:
                # 直方图显示分布
                ax.hist(response_times, bins=20, alpha=0.7, edgecolor='black')
                ax.set_xlabel('响应时间 (ms)')
                ax.set_ylabel('频次')
        else:
            # 模拟数据
            response_times = np.random.normal(150, 50, 100)  # 平均150ms，标准差50ms
            ax.hist(response_times, bins=20, alpha=0.7, edgecolor='black')
            ax.set_xlabel('响应时间 (ms)')
            ax.set_ylabel('频次')
        
        ax.set_title(f"响应时间分布 - {time_range}", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def _generate_default_chart(self, chart_type, time_range, chart_style):
        """生成默认图表"""
        ax = self.chart_figure.add_subplot(111)
        
        # 生成模拟数据
        x = list(range(10))
        y = [np.random.randint(10, 100) for _ in x]
        
        if chart_style == "线图":
            ax.plot(x, y, marker='o')
        elif chart_style == "柱状图":
            ax.bar(x, y, alpha=0.7)
        elif chart_style == "散点图":
            ax.scatter(x, y)
        
        ax.set_title(f"{chart_type} - {time_range}", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    def save_chart(self):
        """保存图表"""
        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "警告", "matplotlib未安装，无法保存图表")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存图表", 
                f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG文件 (*.png);;PDF文件 (*.pdf);;SVG文件 (*.svg);;所有文件 (*.*)"
            )
            
            if file_path:
                self.chart_figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "成功", f"图表已保存到: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存图表失败: {e}")
    
    def refresh_stats(self):
        """刷新统计数据"""
        self.status_label.setText("刷新中...")
        self.load_stats()
        self.status_label.setText("就绪")
        
        # 如果当前在图表页面，自动刷新图表
        if self.tab_widget.currentIndex() == 5:  # 图表分析页面索引
            self.generate_chart()
        
    def export_stats(self):
        """导出统计数据"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出统计数据", 
                f"stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON文件 (*.json);;CSV文件 (*.csv);;所有文件 (*.*)"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.stats_data, f, indent=2, ensure_ascii=False, default=str)
                elif file_path.endswith('.csv'):
                    # 导出为CSV格式
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(["类型", "项目", "值"])
                        
                        for category, data in self.stats_data.items():
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    writer.writerow([category, key, str(value)])
                                    
                QMessageBox.information(self, "成功", f"统计数据已导出到: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出统计数据失败: {e}")
            
    def clear_stats(self):
        """清空统计数据"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空所有统计数据吗？\n\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重置统计数据
            self.stats_data = {
                'message_stats': defaultdict(int),
                'user_stats': defaultdict(int),
                'group_stats': defaultdict(int),
                'wordlib_stats': defaultdict(int),
                'time_stats': defaultdict(int),
                'performance_stats': defaultdict(list)
            }
            
            # 更新显示
            self.load_stats()
            QMessageBox.information(self, "成功", "统计数据已清空")
            
    def start_auto_update(self):
        """开始自动更新"""
        if self.auto_update_check.isChecked():
            interval = self.update_interval_spin.value() * 1000  # 转换为毫秒
            self.update_timer.start(interval)
            
    def toggle_auto_update(self, enabled: bool):
        """切换自动更新"""
        if enabled:
            self.start_auto_update()
        else:
            self.update_timer.stop()
            
    def change_update_interval(self, interval: int):
        """改变更新间隔"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.start_auto_update()
            
    def update_stats(self):
        """定时更新统计数据"""
        self.load_stats()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        if self.update_timer.isActive():
            self.update_timer.stop()
            
        self.logger.info("统计窗口已关闭")
        event.accept()