#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志查看窗口模块
提供日志的图形化查看界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import os
from typing import List, Optional
from datetime import datetime
import re

from ..utils.logger import get_logger

class LogWindow:
    """日志查看窗口类"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.logger = get_logger("LogWindow")
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("日志查看器")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        
        # 日志文件路径
        self.log_file_path: Optional[str] = None
        self.auto_refresh = False
        self.refresh_thread: Optional[threading.Thread] = None
        self.last_file_size = 0
        
        # 过滤设置
        self.filter_level = "ALL"
        self.filter_text = ""
        self.filter_regex = False
        
        self.setup_ui()
        self.load_default_log_file()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        self.setup_toolbar(main_frame)
        
        # 过滤器区域
        self.setup_filter_area(main_frame)
        
        # 日志显示区域
        self.setup_log_area(main_frame)
        
        # 底部状态栏
        self.setup_status_bar(main_frame)
        
    def setup_toolbar(self, parent):
        """设置工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文件操作
        file_frame = ttk.LabelFrame(toolbar_frame, text="文件操作", padding=5)
        file_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        ttk.Button(
            file_frame,
            text="打开文件",
            command=self.open_log_file
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            file_frame,
            text="刷新",
            command=self.refresh_log
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            file_frame,
            text="清空",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            file_frame,
            text="保存",
            command=self.save_log
        ).pack(side=tk.LEFT)
        
        # 自动刷新
        auto_frame = ttk.LabelFrame(toolbar_frame, text="自动刷新", padding=5)
        auto_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.auto_refresh_var = tk.BooleanVar()
        self.auto_refresh_var.trace('w', self.toggle_auto_refresh)
        ttk.Checkbutton(
            auto_frame,
            text="启用",
            variable=self.auto_refresh_var
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(auto_frame, text="间隔(秒):").pack(side=tk.LEFT)
        self.refresh_interval_var = tk.IntVar(value=5)
        ttk.Spinbox(
            auto_frame,
            from_=1,
            to=60,
            textvariable=self.refresh_interval_var,
            width=5
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # 显示选项
        display_frame = ttk.LabelFrame(toolbar_frame, text="显示选项", padding=5)
        display_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="自动滚动",
            variable=self.auto_scroll_var
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.word_wrap_var = tk.BooleanVar(value=True)
        self.word_wrap_var.trace('w', self.toggle_word_wrap)
        ttk.Checkbutton(
            display_frame,
            text="自动换行",
            variable=self.word_wrap_var
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.show_timestamp_var = tk.BooleanVar(value=True)
        self.show_timestamp_var.trace('w', self.refresh_log)
        ttk.Checkbutton(
            display_frame,
            text="显示时间",
            variable=self.show_timestamp_var
        ).pack(side=tk.LEFT)
        
    def setup_filter_area(self, parent):
        """设置过滤器区域"""
        filter_frame = ttk.LabelFrame(parent, text="过滤器", padding=5)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 日志级别过滤
        level_frame = ttk.Frame(filter_frame)
        level_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        ttk.Label(level_frame, text="级别:").pack(side=tk.LEFT)
        self.level_var = tk.StringVar(value="ALL")
        self.level_var.trace('w', self.apply_filter)
        level_combo = ttk.Combobox(
            level_frame,
            textvariable=self.level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10
        )
        level_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 文本过滤
        text_frame = ttk.Frame(filter_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        
        ttk.Label(text_frame, text="文本:").pack(side=tk.LEFT)
        self.filter_text_var = tk.StringVar()
        self.filter_text_var.trace('w', self.apply_filter)
        filter_entry = ttk.Entry(text_frame, textvariable=self.filter_text_var)
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        self.regex_var = tk.BooleanVar()
        self.regex_var.trace('w', self.apply_filter)
        ttk.Checkbutton(
            text_frame,
            text="正则",
            variable=self.regex_var
        ).pack(side=tk.LEFT)
        
        # 操作按钮
        action_frame = ttk.Frame(filter_frame)
        action_frame.pack(side=tk.RIGHT)
        
        ttk.Button(
            action_frame,
            text="清除过滤",
            command=self.clear_filter
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            action_frame,
            text="导出过滤结果",
            command=self.export_filtered_log
        ).pack(side=tk.LEFT)
        
    def setup_log_area(self, parent):
        """设置日志显示区域"""
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建文本框和滚动条
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置文本标签样式
        self.setup_text_tags()
        
        # 绑定右键菜单
        self.setup_context_menu()
        
    def setup_text_tags(self):
        """设置文本标签样式"""
        # 不同日志级别的颜色
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("CRITICAL", foreground="red", background="yellow")
        
        # 时间戳样式
        self.log_text.tag_configure("timestamp", foreground="blue")
        
        # 高亮搜索结果
        self.log_text.tag_configure("highlight", background="yellow")
        
    def setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="复制", command=self.copy_selected)
        self.context_menu.add_command(label="全选", command=self.select_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="查找", command=self.show_find_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="跳转到顶部", command=self.goto_top)
        self.context_menu.add_command(label="跳转到底部", command=self.goto_bottom)
        
        self.log_text.bind("<Button-3>", self.show_context_menu)
        
    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        # 分隔线
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
        
        # 状态信息
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        # 文件信息
        self.file_info_label = ttk.Label(status_frame, text="")
        self.file_info_label.pack(side=tk.RIGHT)
        
    def load_default_log_file(self):
        """加载默认日志文件"""
        try:
            # 尝试找到默认日志文件
            default_paths = [
                "logs/bot.log",
                "data/logs/bot.log",
                "bot.log"
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    self.log_file_path = path
                    self.refresh_log()
                    break
                    
        except Exception as e:
            self.logger.error(f"加载默认日志文件失败: {e}")
            
    def open_log_file(self):
        """打开日志文件"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="选择日志文件"
            )
            
            if filename:
                self.log_file_path = filename
                self.refresh_log()
                
        except Exception as e:
            self.logger.error(f"打开日志文件失败: {e}")
            messagebox.showerror("错误", f"打开日志文件失败: {e}")
            
    def refresh_log(self, *args):
        """刷新日志"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            self.status_label.config(text="未选择日志文件或文件不存在")
            return
            
        try:
            # 读取日志文件
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 更新文件大小信息
            file_size = os.path.getsize(self.log_file_path)
            self.last_file_size = file_size
            
            # 显示日志内容
            self.display_log_content(content)
            
            # 更新状态
            file_name = os.path.basename(self.log_file_path)
            file_size_mb = file_size / (1024 * 1024)
            self.file_info_label.config(text=f"{file_name} ({file_size_mb:.2f} MB)")
            self.status_label.config(text=f"已刷新 - {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.logger.error(f"刷新日志失败: {e}")
            self.status_label.config(text=f"刷新失败: {e}")
            
    def display_log_content(self, content: str):
        """显示日志内容"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        lines = content.split('\n')
        filtered_lines = self.filter_lines(lines)
        
        for line in filtered_lines:
            self.add_log_line(line)
            
        self.log_text.config(state=tk.DISABLED)
        
        # 自动滚动到底部
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
            
    def add_log_line(self, line: str):
        """添加日志行"""
        if not line.strip():
            self.log_text.insert(tk.END, "\n")
            return
            
        # 解析日志级别
        level = self.extract_log_level(line)
        
        # 解析时间戳
        timestamp = self.extract_timestamp(line)
        
        # 如果不显示时间戳，则移除时间戳部分
        display_line = line
        if not self.show_timestamp_var.get() and timestamp:
            display_line = line.replace(timestamp, "").strip()
            
        # 插入文本并应用样式
        start_pos = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, display_line + "\n")
        end_pos = self.log_text.index(tk.END)
        
        # 应用日志级别样式
        if level:
            self.log_text.tag_add(level, start_pos, end_pos)
            
        # 高亮搜索文本
        if self.filter_text_var.get():
            self.highlight_search_text(start_pos, end_pos, display_line)
            
    def extract_log_level(self, line: str) -> Optional[str]:
        """提取日志级别"""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            if level in line.upper():
                return level
        return None
        
    def extract_timestamp(self, line: str) -> Optional[str]:
        """提取时间戳"""
        # 常见的时间戳格式
        patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{2}:\d{2}:\d{2}',
            r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]',
            r'\[\d{2}:\d{2}:\d{2}\]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
                
        return None
        
    def filter_lines(self, lines: List[str]) -> List[str]:
        """过滤日志行"""
        filtered = []
        
        for line in lines:
            # 级别过滤
            if self.level_var.get() != "ALL":
                level = self.extract_log_level(line)
                if not level or level != self.level_var.get():
                    continue
                    
            # 文本过滤
            filter_text = self.filter_text_var.get()
            if filter_text:
                if self.regex_var.get():
                    try:
                        if not re.search(filter_text, line, re.IGNORECASE):
                            continue
                    except re.error:
                        # 正则表达式错误，使用普通文本搜索
                        if filter_text.lower() not in line.lower():
                            continue
                else:
                    if filter_text.lower() not in line.lower():
                        continue
                        
            filtered.append(line)
            
        return filtered
        
    def highlight_search_text(self, start_pos: str, end_pos: str, line: str):
        """高亮搜索文本"""
        search_text = self.filter_text_var.get()
        if not search_text:
            return
            
        try:
            if self.regex_var.get():
                # 正则表达式搜索
                for match in re.finditer(search_text, line, re.IGNORECASE):
                    start_idx = f"{start_pos.split('.')[0]}.{match.start()}"
                    end_idx = f"{start_pos.split('.')[0]}.{match.end()}"
                    self.log_text.tag_add("highlight", start_idx, end_idx)
            else:
                # 普通文本搜索
                start_idx = 0
                while True:
                    idx = line.lower().find(search_text.lower(), start_idx)
                    if idx == -1:
                        break
                    start_tag = f"{start_pos.split('.')[0]}.{idx}"
                    end_tag = f"{start_pos.split('.')[0]}.{idx + len(search_text)}"
                    self.log_text.tag_add("highlight", start_tag, end_tag)
                    start_idx = idx + 1
                    
        except Exception as e:
            self.logger.error(f"高亮搜索文本失败: {e}")
            
    def apply_filter(self, *args):
        """应用过滤器"""
        self.refresh_log()
        
    def clear_filter(self):
        """清除过滤器"""
        self.level_var.set("ALL")
        self.filter_text_var.set("")
        self.regex_var.set(False)
        
    def clear_log(self):
        """清空日志显示"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def save_log(self):
        """保存日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存日志"
            )
            
            if filename:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已保存到: {filename}")
                
        except Exception as e:
            self.logger.error(f"保存日志失败: {e}")
            messagebox.showerror("错误", f"保存日志失败: {e}")
            
    def export_filtered_log(self):
        """导出过滤后的日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="导出过滤结果"
            )
            
            if filename:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"过滤结果已导出到: {filename}")
                
        except Exception as e:
            self.logger.error(f"导出过滤结果失败: {e}")
            messagebox.showerror("错误", f"导出过滤结果失败: {e}")
            
    def toggle_auto_refresh(self, *args):
        """切换自动刷新"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
            
    def start_auto_refresh(self):
        """启动自动刷新"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return
            
        self.auto_refresh = True
        self.refresh_thread = threading.Thread(target=self._auto_refresh_worker, daemon=True)
        self.refresh_thread.start()
        
    def stop_auto_refresh(self):
        """停止自动刷新"""
        self.auto_refresh = False
        
    def _auto_refresh_worker(self):
        """自动刷新工作线程"""
        while self.auto_refresh:
            try:
                if self.log_file_path and os.path.exists(self.log_file_path):
                    current_size = os.path.getsize(self.log_file_path)
                    if current_size != self.last_file_size:
                        # 文件有变化，刷新日志
                        self.window.after(0, self.refresh_log)
                        
                time.sleep(self.refresh_interval_var.get())
                
            except Exception as e:
                self.logger.error(f"自动刷新失败: {e}")
                break
                
    def toggle_word_wrap(self, *args):
        """切换自动换行"""
        if self.word_wrap_var.get():
            self.log_text.config(wrap=tk.WORD)
        else:
            self.log_text.config(wrap=tk.NONE)
            
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.logger.error(f"显示右键菜单失败: {e}")
            
    def copy_selected(self):
        """复制选中文本"""
        try:
            selected_text = self.log_text.selection_get()
            self.window.clipboard_clear()
            self.window.clipboard_append(selected_text)
        except tk.TclError:
            # 没有选中文本
            pass
        except Exception as e:
            self.logger.error(f"复制文本失败: {e}")
            
    def select_all(self):
        """全选文本"""
        self.log_text.tag_add(tk.SEL, "1.0", tk.END)
        self.log_text.mark_set(tk.INSERT, "1.0")
        self.log_text.see(tk.INSERT)
        
    def goto_top(self):
        """跳转到顶部"""
        self.log_text.see("1.0")
        
    def goto_bottom(self):
        """跳转到底部"""
        self.log_text.see(tk.END)
        
    def show_find_dialog(self):
        """显示查找对话框"""
        find_window = tk.Toplevel(self.window)
        find_window.title("查找")
        find_window.geometry("400x150")
        find_window.transient(self.window)
        find_window.grab_set()
        
        # 查找文本
        ttk.Label(find_window, text="查找:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        find_var = tk.StringVar()
        find_entry = ttk.Entry(find_window, textvariable=find_var)
        find_entry.pack(fill=tk.X, padx=10, pady=5)
        find_entry.focus()
        
        # 选项
        options_frame = ttk.Frame(find_window)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        case_sensitive_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="区分大小写", variable=case_sensitive_var).pack(side=tk.LEFT)
        
        regex_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="正则表达式", variable=regex_var).pack(side=tk.LEFT, padx=(20, 0))
        
        # 按钮
        button_frame = ttk.Frame(find_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def find_text():
            search_text = find_var.get()
            if search_text:
                self.filter_text_var.set(search_text)
                self.regex_var.set(regex_var.get())
                find_window.destroy()
                
        ttk.Button(button_frame, text="查找", command=find_text).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=find_window.destroy).pack(side=tk.RIGHT)
        
        # 绑定回车键
        find_entry.bind("<Return>", lambda e: find_text())