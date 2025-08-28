#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计信息窗口模块
提供机器人运行统计信息的图形化显示界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from collections import defaultdict, deque

from ..utils.logger import get_logger

class StatsWindow:
    """统计信息窗口类"""
    
    def __init__(self, parent: tk.Tk, bot_framework=None):
        self.parent = parent
        self.bot_framework = bot_framework
        self.logger = get_logger("StatsWindow")
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("统计信息")
        self.window.geometry("900x700")
        self.window.transient(parent)
        
        # 统计数据
        self.stats_data = {
            'messages': {
                'total_received': 0,
                'total_sent': 0,
                'private_received': 0,
                'group_received': 0,
                'private_sent': 0,
                'group_sent': 0
            },
            'wordlib': {
                'total_entries': 0,
                'enabled_entries': 0,
                'matches_today': 0,
                'total_matches': 0
            },
            'performance': {
                'uptime': 0,
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'response_time_avg': 0.0
            },
            'errors': {
                'total_errors': 0,
                'errors_today': 0,
                'last_error': None
            }
        }
        
        # 历史数据（用于图表）
        self.history_data = {
            'messages_per_hour': deque(maxlen=24),  # 24小时
            'response_times': deque(maxlen=100),    # 最近100次响应
            'error_counts': deque(maxlen=24)        # 24小时错误统计
        }
        
        # 自动更新
        self.auto_update = True
        self.update_thread: Optional[threading.Thread] = None
        
        self.setup_ui()
        self.start_auto_update()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        self.setup_toolbar(main_frame)
        
        # 创建笔记本控件（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 各个统计页面
        self.setup_overview_tab()
        self.setup_messages_tab()
        self.setup_wordlib_tab()
        self.setup_performance_tab()
        self.setup_errors_tab()
        
    def setup_toolbar(self, parent):
        """设置工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        
        # 刷新按钮
        ttk.Button(
            toolbar_frame,
            text="刷新",
            command=self.refresh_stats
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 重置统计
        ttk.Button(
            toolbar_frame,
            text="重置统计",
            command=self.reset_stats
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 导出数据
        ttk.Button(
            toolbar_frame,
            text="导出数据",
            command=self.export_stats
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 自动更新
        self.auto_update_var = tk.BooleanVar(value=True)
        self.auto_update_var.trace('w', self.toggle_auto_update)
        ttk.Checkbutton(
            toolbar_frame,
            text="自动更新",
            variable=self.auto_update_var
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 更新间隔
        ttk.Label(toolbar_frame, text="间隔(秒):").pack(side=tk.LEFT)
        self.update_interval_var = tk.IntVar(value=5)
        ttk.Spinbox(
            toolbar_frame,
            from_=1,
            to=60,
            textvariable=self.update_interval_var,
            width=5
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # 最后更新时间
        self.last_update_label = ttk.Label(toolbar_frame, text="")
        self.last_update_label.pack(side=tk.RIGHT)
        
    def setup_overview_tab(self):
        """设置概览标签页"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="概览")
        
        # 创建滚动框架
        canvas = tk.Canvas(overview_frame)
        scrollbar = ttk.Scrollbar(overview_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 基本信息卡片
        self.create_info_card(scrollable_frame, "基本信息", [
            ("运行时间", "uptime_label"),
            ("启动时间", "start_time_label"),
            ("当前状态", "status_label"),
            ("版本信息", "version_label")
        ])
        
        # 消息统计卡片
        self.create_info_card(scrollable_frame, "消息统计", [
            ("总接收消息", "total_received_label"),
            ("总发送消息", "total_sent_label"),
            ("私聊消息", "private_messages_label"),
            ("群聊消息", "group_messages_label")
        ])
        
        # 词库统计卡片
        self.create_info_card(scrollable_frame, "词库统计", [
            ("总词库条目", "total_entries_label"),
            ("启用条目", "enabled_entries_label"),
            ("今日匹配", "matches_today_label"),
            ("总匹配次数", "total_matches_label")
        ])
        
        # 性能统计卡片
        self.create_info_card(scrollable_frame, "性能统计", [
            ("CPU使用率", "cpu_usage_label"),
            ("内存使用", "memory_usage_label"),
            ("平均响应时间", "response_time_label"),
            ("错误次数", "error_count_label")
        ])
        
    def create_info_card(self, parent, title: str, items: List[tuple]):
        """创建信息卡片"""
        # 卡片框架
        card_frame = ttk.LabelFrame(parent, text=title, padding=10)
        card_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建网格布局
        for i, (label_text, attr_name) in enumerate(items):
            row = i // 2
            col = (i % 2) * 2
            
            # 标签
            ttk.Label(card_frame, text=f"{label_text}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=2
            )
            
            # 值标签
            value_label = ttk.Label(card_frame, text="--", font=("Arial", 9, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 20), pady=2)
            
            # 保存引用
            setattr(self, attr_name, value_label)
            
    def setup_messages_tab(self):
        """设置消息统计标签页"""
        messages_frame = ttk.Frame(self.notebook)
        self.notebook.add(messages_frame, text="消息统计")
        
        # 左侧统计信息
        left_frame = ttk.Frame(messages_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 消息类型统计
        type_frame = ttk.LabelFrame(left_frame, text="消息类型统计", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建树形视图显示消息统计
        self.messages_tree = ttk.Treeview(type_frame, columns=("count", "percentage"), show="tree headings")
        self.messages_tree.heading("#0", text="类型")
        self.messages_tree.heading("count", text="数量")
        self.messages_tree.heading("percentage", text="百分比")
        
        self.messages_tree.column("#0", width=150)
        self.messages_tree.column("count", width=100)
        self.messages_tree.column("percentage", width=100)
        
        self.messages_tree.pack(fill=tk.BOTH, expand=True)
        
        # 时间段统计
        time_frame = ttk.LabelFrame(left_frame, text="时间段统计", padding=10)
        time_frame.pack(fill=tk.BOTH, expand=True)
        
        # 简单的文本显示（可以后续改为图表）
        self.time_stats_text = tk.Text(time_frame, height=10, state=tk.DISABLED)
        time_scrollbar = ttk.Scrollbar(time_frame, orient="vertical", command=self.time_stats_text.yview)
        self.time_stats_text.configure(yscrollcommand=time_scrollbar.set)
        
        self.time_stats_text.pack(side="left", fill="both", expand=True)
        time_scrollbar.pack(side="right", fill="y")
        
        # 右侧详细信息
        right_frame = ttk.Frame(messages_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 最近消息
        recent_frame = ttk.LabelFrame(right_frame, text="最近消息", padding=10)
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        self.recent_messages_tree = ttk.Treeview(
            recent_frame, 
            columns=("time", "type", "content"), 
            show="headings"
        )
        self.recent_messages_tree.heading("time", text="时间")
        self.recent_messages_tree.heading("type", text="类型")
        self.recent_messages_tree.heading("content", text="内容")
        
        self.recent_messages_tree.column("time", width=120)
        self.recent_messages_tree.column("type", width=80)
        self.recent_messages_tree.column("content", width=200)
        
        recent_scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.recent_messages_tree.yview)
        self.recent_messages_tree.configure(yscrollcommand=recent_scrollbar.set)
        
        self.recent_messages_tree.pack(side="left", fill="both", expand=True)
        recent_scrollbar.pack(side="right", fill="y")
        
    def setup_wordlib_tab(self):
        """设置词库统计标签页"""
        wordlib_frame = ttk.Frame(self.notebook)
        self.notebook.add(wordlib_frame, text="词库统计")
        
        # 词库概览
        overview_frame = ttk.LabelFrame(wordlib_frame, text="词库概览", padding=10)
        overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 统计信息网格
        stats_items = [
            ("总条目数", "wordlib_total_label"),
            ("启用条目", "wordlib_enabled_label"),
            ("禁用条目", "wordlib_disabled_label"),
            ("今日匹配", "wordlib_matches_today_label"),
            ("总匹配数", "wordlib_total_matches_label"),
            ("匹配率", "wordlib_match_rate_label")
        ]
        
        for i, (label_text, attr_name) in enumerate(stats_items):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(overview_frame, text=f"{label_text}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5
            )
            
            value_label = ttk.Label(overview_frame, text="--", font=("Arial", 9, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 30), pady=5)
            
            setattr(self, attr_name, value_label)
            
        # 分类统计
        category_frame = ttk.LabelFrame(wordlib_frame, text="分类统计", padding=10)
        category_frame.pack(fill=tk.BOTH, expand=True)
        
        self.category_tree = ttk.Treeview(
            category_frame, 
            columns=("count", "enabled", "matches"), 
            show="tree headings"
        )
        self.category_tree.heading("#0", text="分类")
        self.category_tree.heading("count", text="条目数")
        self.category_tree.heading("enabled", text="启用数")
        self.category_tree.heading("matches", text="匹配数")
        
        category_scrollbar = ttk.Scrollbar(category_frame, orient="vertical", command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=category_scrollbar.set)
        
        self.category_tree.pack(side="left", fill="both", expand=True)
        category_scrollbar.pack(side="right", fill="y")
        
    def setup_performance_tab(self):
        """设置性能统计标签页"""
        performance_frame = ttk.Frame(self.notebook)
        self.notebook.add(performance_frame, text="性能统计")
        
        # 系统资源
        resource_frame = ttk.LabelFrame(performance_frame, text="系统资源", padding=10)
        resource_frame.pack(fill=tk.X, pady=(0, 10))
        
        # CPU和内存使用率
        resource_items = [
            ("CPU使用率", "perf_cpu_label"),
            ("内存使用", "perf_memory_label"),
            ("磁盘使用", "perf_disk_label"),
            ("网络流量", "perf_network_label")
        ]
        
        for i, (label_text, attr_name) in enumerate(resource_items):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(resource_frame, text=f"{label_text}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5
            )
            
            value_label = ttk.Label(resource_frame, text="--", font=("Arial", 9, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 30), pady=5)
            
            setattr(self, attr_name, value_label)
            
        # 响应时间统计
        response_frame = ttk.LabelFrame(performance_frame, text="响应时间统计", padding=10)
        response_frame.pack(fill=tk.BOTH, expand=True)
        
        # 响应时间信息
        response_info_frame = ttk.Frame(response_frame)
        response_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        response_items = [
            ("平均响应时间", "resp_avg_label"),
            ("最快响应", "resp_min_label"),
            ("最慢响应", "resp_max_label"),
            ("响应次数", "resp_count_label")
        ]
        
        for i, (label_text, attr_name) in enumerate(response_items):
            col = i * 2
            
            ttk.Label(response_info_frame, text=f"{label_text}:").grid(
                row=0, column=col, sticky=tk.W, padx=(0, 10), pady=5
            )
            
            value_label = ttk.Label(response_info_frame, text="--", font=("Arial", 9, "bold"))
            value_label.grid(row=0, column=col+1, sticky=tk.W, padx=(0, 30), pady=5)
            
            setattr(self, attr_name, value_label)
            
        # 响应时间历史（简单文本显示）
        self.response_history_text = tk.Text(response_frame, height=15, state=tk.DISABLED)
        response_scrollbar = ttk.Scrollbar(response_frame, orient="vertical", command=self.response_history_text.yview)
        self.response_history_text.configure(yscrollcommand=response_scrollbar.set)
        
        self.response_history_text.pack(side="left", fill="both", expand=True)
        response_scrollbar.pack(side="right", fill="y")
        
    def setup_errors_tab(self):
        """设置错误统计标签页"""
        errors_frame = ttk.Frame(self.notebook)
        self.notebook.add(errors_frame, text="错误统计")
        
        # 错误概览
        error_overview_frame = ttk.LabelFrame(errors_frame, text="错误概览", padding=10)
        error_overview_frame.pack(fill=tk.X, pady=(0, 10))
        
        error_items = [
            ("总错误数", "error_total_label"),
            ("今日错误", "error_today_label"),
            ("最后错误时间", "error_last_time_label"),
            ("错误率", "error_rate_label")
        ]
        
        for i, (label_text, attr_name) in enumerate(error_items):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(error_overview_frame, text=f"{label_text}:").grid(
                row=row, column=col, sticky=tk.W, padx=(0, 10), pady=5
            )
            
            value_label = ttk.Label(error_overview_frame, text="--", font=("Arial", 9, "bold"))
            value_label.grid(row=row, column=col+1, sticky=tk.W, padx=(0, 30), pady=5)
            
            setattr(self, attr_name, value_label)
            
        # 错误详情
        error_detail_frame = ttk.LabelFrame(errors_frame, text="错误详情", padding=10)
        error_detail_frame.pack(fill=tk.BOTH, expand=True)
        
        self.errors_tree = ttk.Treeview(
            error_detail_frame, 
            columns=("time", "level", "message"), 
            show="headings"
        )
        self.errors_tree.heading("time", text="时间")
        self.errors_tree.heading("level", text="级别")
        self.errors_tree.heading("message", text="错误信息")
        
        self.errors_tree.column("time", width=150)
        self.errors_tree.column("level", width=80)
        self.errors_tree.column("message", width=400)
        
        errors_scrollbar = ttk.Scrollbar(error_detail_frame, orient="vertical", command=self.errors_tree.yview)
        self.errors_tree.configure(yscrollcommand=errors_scrollbar.set)
        
        self.errors_tree.pack(side="left", fill="both", expand=True)
        errors_scrollbar.pack(side="right", fill="y")
        
    def refresh_stats(self):
        """刷新统计信息"""
        try:
            # 从机器人框架获取统计数据
            if self.bot_framework:
                self.collect_stats_from_framework()
            else:
                self.generate_mock_stats()
                
            # 更新各个标签页
            self.update_overview_tab()
            self.update_messages_tab()
            self.update_wordlib_tab()
            self.update_performance_tab()
            self.update_errors_tab()
            
            # 更新最后更新时间
            self.last_update_label.config(
                text=f"最后更新: {datetime.now().strftime('%H:%M:%S')}"
            )
            
        except Exception as e:
            self.logger.error(f"刷新统计信息失败: {e}")
            
    def collect_stats_from_framework(self):
        """从机器人框架收集统计数据"""
        try:
            # 获取框架统计信息
            framework_stats = self.bot_framework.get_stats()
            
            # 更新统计数据
            self.stats_data.update(framework_stats)
            
        except Exception as e:
            self.logger.error(f"从框架收集统计数据失败: {e}")
            self.generate_mock_stats()
            
    def generate_mock_stats(self):
        """生成模拟统计数据（用于测试）"""
        import random
        
        # 模拟消息统计
        self.stats_data['messages']['total_received'] = random.randint(100, 1000)
        self.stats_data['messages']['total_sent'] = random.randint(50, 500)
        self.stats_data['messages']['private_received'] = random.randint(20, 200)
        self.stats_data['messages']['group_received'] = random.randint(80, 800)
        
        # 模拟词库统计
        self.stats_data['wordlib']['total_entries'] = random.randint(50, 200)
        self.stats_data['wordlib']['enabled_entries'] = random.randint(40, 180)
        self.stats_data['wordlib']['matches_today'] = random.randint(10, 100)
        self.stats_data['wordlib']['total_matches'] = random.randint(100, 1000)
        
        # 模拟性能统计
        self.stats_data['performance']['uptime'] = time.time() - 3600  # 1小时前启动
        self.stats_data['performance']['cpu_usage'] = random.uniform(5.0, 25.0)
        self.stats_data['performance']['memory_usage'] = random.uniform(50.0, 200.0)
        self.stats_data['performance']['response_time_avg'] = random.uniform(0.1, 2.0)
        
        # 模拟错误统计
        self.stats_data['errors']['total_errors'] = random.randint(0, 10)
        self.stats_data['errors']['errors_today'] = random.randint(0, 5)
        
    def update_overview_tab(self):
        """更新概览标签页"""
        try:
            # 基本信息
            uptime = self.stats_data['performance']['uptime']
            if isinstance(uptime, (int, float)):
                uptime_str = str(timedelta(seconds=int(time.time() - uptime)))
            else:
                uptime_str = "未知"
                
            self.uptime_label.config(text=uptime_str)
            self.start_time_label.config(text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.status_label.config(text="运行中" if self.bot_framework else "未连接")
            self.version_label.config(text="OneBot V11 Framework v1.0")
            
            # 消息统计
            self.total_received_label.config(text=str(self.stats_data['messages']['total_received']))
            self.total_sent_label.config(text=str(self.stats_data['messages']['total_sent']))
            self.private_messages_label.config(
                text=f"接收: {self.stats_data['messages']['private_received']} / 发送: {self.stats_data['messages']['private_sent']}"
            )
            self.group_messages_label.config(
                text=f"接收: {self.stats_data['messages']['group_received']} / 发送: {self.stats_data['messages']['group_sent']}"
            )
            
            # 词库统计
            self.total_entries_label.config(text=str(self.stats_data['wordlib']['total_entries']))
            self.enabled_entries_label.config(text=str(self.stats_data['wordlib']['enabled_entries']))
            self.matches_today_label.config(text=str(self.stats_data['wordlib']['matches_today']))
            self.total_matches_label.config(text=str(self.stats_data['wordlib']['total_matches']))
            
            # 性能统计
            self.cpu_usage_label.config(text=f"{self.stats_data['performance']['cpu_usage']:.1f}%")
            self.memory_usage_label.config(text=f"{self.stats_data['performance']['memory_usage']:.1f} MB")
            self.response_time_label.config(text=f"{self.stats_data['performance']['response_time_avg']:.2f}s")
            self.error_count_label.config(text=str(self.stats_data['errors']['total_errors']))
            
        except Exception as e:
            self.logger.error(f"更新概览标签页失败: {e}")
            
    def update_messages_tab(self):
        """更新消息统计标签页"""
        try:
            # 清空树形视图
            for item in self.messages_tree.get_children():
                self.messages_tree.delete(item)
                
            # 添加消息类型统计
            total_received = self.stats_data['messages']['total_received']
            total_sent = self.stats_data['messages']['total_sent']
            
            if total_received > 0:
                private_pct = (self.stats_data['messages']['private_received'] / total_received) * 100
                group_pct = (self.stats_data['messages']['group_received'] / total_received) * 100
            else:
                private_pct = group_pct = 0
                
            # 接收消息
            received_id = self.messages_tree.insert("", "end", text="接收消息", values=(total_received, "100%"))
            self.messages_tree.insert(received_id, "end", text="私聊消息", 
                                    values=(self.stats_data['messages']['private_received'], f"{private_pct:.1f}%"))
            self.messages_tree.insert(received_id, "end", text="群聊消息", 
                                    values=(self.stats_data['messages']['group_received'], f"{group_pct:.1f}%"))
            
            # 发送消息
            sent_id = self.messages_tree.insert("", "end", text="发送消息", values=(total_sent, "100%"))
            self.messages_tree.insert(sent_id, "end", text="私聊消息", 
                                    values=(self.stats_data['messages']['private_sent'], "--"))
            self.messages_tree.insert(sent_id, "end", text="群聊消息", 
                                    values=(self.stats_data['messages']['group_sent'], "--"))
            
            # 展开所有节点
            self.messages_tree.item(received_id, open=True)
            self.messages_tree.item(sent_id, open=True)
            
        except Exception as e:
            self.logger.error(f"更新消息统计标签页失败: {e}")
            
    def update_wordlib_tab(self):
        """更新词库统计标签页"""
        try:
            # 更新词库概览
            total = self.stats_data['wordlib']['total_entries']
            enabled = self.stats_data['wordlib']['enabled_entries']
            disabled = total - enabled
            matches_today = self.stats_data['wordlib']['matches_today']
            total_matches = self.stats_data['wordlib']['total_matches']
            
            self.wordlib_total_label.config(text=str(total))
            self.wordlib_enabled_label.config(text=str(enabled))
            self.wordlib_disabled_label.config(text=str(disabled))
            self.wordlib_matches_today_label.config(text=str(matches_today))
            self.wordlib_total_matches_label.config(text=str(total_matches))
            
            # 计算匹配率
            if total > 0:
                match_rate = (total_matches / total) if total > 0 else 0
                self.wordlib_match_rate_label.config(text=f"{match_rate:.2f}")
            else:
                self.wordlib_match_rate_label.config(text="--")
                
        except Exception as e:
            self.logger.error(f"更新词库统计标签页失败: {e}")
            
    def update_performance_tab(self):
        """更新性能统计标签页"""
        try:
            # 更新系统资源
            self.perf_cpu_label.config(text=f"{self.stats_data['performance']['cpu_usage']:.1f}%")
            self.perf_memory_label.config(text=f"{self.stats_data['performance']['memory_usage']:.1f} MB")
            self.perf_disk_label.config(text="--")
            self.perf_network_label.config(text="--")
            
            # 更新响应时间统计
            avg_time = self.stats_data['performance']['response_time_avg']
            self.resp_avg_label.config(text=f"{avg_time:.2f}s")
            self.resp_min_label.config(text="--")
            self.resp_max_label.config(text="--")
            self.resp_count_label.config(text="--")
            
        except Exception as e:
            self.logger.error(f"更新性能统计标签页失败: {e}")
            
    def update_errors_tab(self):
        """更新错误统计标签页"""
        try:
            # 更新错误概览
            total_errors = self.stats_data['errors']['total_errors']
            errors_today = self.stats_data['errors']['errors_today']
            
            self.error_total_label.config(text=str(total_errors))
            self.error_today_label.config(text=str(errors_today))
            self.error_last_time_label.config(text="--")
            self.error_rate_label.config(text="--")
            
        except Exception as e:
            self.logger.error(f"更新错误统计标签页失败: {e}")
            
    def reset_stats(self):
        """重置统计信息"""
        try:
            result = messagebox.askyesno(
                "确认重置",
                "确定要重置所有统计信息吗？此操作不可撤销。"
            )
            
            if result:
                if self.bot_framework:
                    self.bot_framework.reset_stats()
                    
                # 重置本地统计数据
                self.stats_data = {
                    'messages': {
                        'total_received': 0,
                        'total_sent': 0,
                        'private_received': 0,
                        'group_received': 0,
                        'private_sent': 0,
                        'group_sent': 0
                    },
                    'wordlib': {
                        'total_entries': 0,
                        'enabled_entries': 0,
                        'matches_today': 0,
                        'total_matches': 0
                    },
                    'performance': {
                        'uptime': time.time(),
                        'cpu_usage': 0.0,
                        'memory_usage': 0.0,
                        'response_time_avg': 0.0
                    },
                    'errors': {
                        'total_errors': 0,
                        'errors_today': 0,
                        'last_error': None
                    }
                }
                
                # 清空历史数据
                self.history_data = {
                    'messages_per_hour': deque(maxlen=24),
                    'response_times': deque(maxlen=100),
                    'error_counts': deque(maxlen=24)
                }
                
                # 刷新显示
                self.refresh_stats()
                
                messagebox.showinfo("成功", "统计信息已重置")
                
        except Exception as e:
            self.logger.error(f"重置统计信息失败: {e}")
            messagebox.showerror("错误", f"重置统计信息失败: {e}")
            
    def export_stats(self):
        """导出统计数据"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                title="导出统计数据"
            )
            
            if filename:
                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'stats': self.stats_data,
                    'history': {
                        'messages_per_hour': list(self.history_data['messages_per_hour']),
                        'response_times': list(self.history_data['response_times']),
                        'error_counts': list(self.history_data['error_counts'])
                    }
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                    
                messagebox.showinfo("成功", f"统计数据已导出到: {filename}")
                
        except Exception as e:
            self.logger.error(f"导出统计数据失败: {e}")
            messagebox.showerror("错误", f"导出统计数据失败: {e}")
            
    def toggle_auto_update(self, *args):
        """切换自动更新"""
        if self.auto_update_var.get():
            self.start_auto_update()
        else:
            self.stop_auto_update()
            
    def start_auto_update(self):
        """启动自动更新"""
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.auto_update = True
        self.update_thread = threading.Thread(target=self._auto_update_worker, daemon=True)
        self.update_thread.start()
        
    def stop_auto_update(self):
        """停止自动更新"""
        self.auto_update = False
        
    def _auto_update_worker(self):
        """自动更新工作线程"""
        while self.auto_update:
            try:
                # 在主线程中刷新统计信息
                self.window.after(0, self.refresh_stats)
                time.sleep(self.update_interval_var.get())
                
            except Exception as e:
                self.logger.error(f"自动更新失败: {e}")
                break
                
    def on_closing(self):
        """窗口关闭事件"""
        self.stop_auto_update()
        self.window.destroy()