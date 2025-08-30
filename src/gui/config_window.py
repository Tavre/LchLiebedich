#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理窗口模块
提供配置的图形化管理界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any
import os

from ..config.settings import ConfigManager, BotConfig
from ..utils.logger import get_logger

class ConfigWindow:
    """配置管理窗口类"""
    
    def __init__(self, parent: tk.Tk, config: BotConfig):
        self.parent = parent
        self.config = config
        self.config_manager = ConfigManager()
        self.logger = get_logger("ConfigWindow")
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("配置设置")
        self.window.geometry("700x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 配置变量
        self.config_vars = {}
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # OneBot配置标签页
        self.setup_onebot_tab()
        
        # 服务器配置标签页
        self.setup_server_tab()
        
        # 数据库配置标签页
        self.setup_storage_tab()
        
        # 日志配置标签页
        self.setup_log_tab()
        
        # 词库配置标签页
        self.setup_wordlib_tab()
        
        # 按钮区域
        self.setup_button_area(main_frame)
        
    def setup_onebot_tab(self):
        """设置OneBot配置标签页"""
        onebot_frame = ttk.Frame(self.notebook)
        self.notebook.add(onebot_frame, text="OneBot")
        
        # 滚动框架
        canvas = tk.Canvas(onebot_frame)
        scrollbar = ttk.Scrollbar(onebot_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # OneBot服务器配置
        server_group = ttk.LabelFrame(scrollable_frame, text="OneBot服务器配置", padding=10)
        server_group.pack(fill=tk.X, pady=(0, 10))
        
        # 主机地址
        host_frame = ttk.Frame(server_group)
        host_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(host_frame, text="主机地址:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['onebot_host'] = tk.StringVar()
        ttk.Entry(host_frame, textvariable=self.config_vars['onebot_host']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 端口
        port_frame = ttk.Frame(server_group)
        port_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(port_frame, text="端口:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['onebot_port'] = tk.IntVar()
        ttk.Entry(port_frame, textvariable=self.config_vars['onebot_port']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 访问令牌
        token_frame = ttk.Frame(server_group)
        token_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(token_frame, text="访问令牌:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['onebot_access_token'] = tk.StringVar()
        token_entry = ttk.Entry(token_frame, textvariable=self.config_vars['onebot_access_token'], show="*")
        token_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 显示/隐藏令牌按钮
        self.token_visible = False
        def toggle_token_visibility():
            if self.token_visible:
                token_entry.config(show="*")
                toggle_btn.config(text="显示")
            else:
                token_entry.config(show="")
                toggle_btn.config(text="隐藏")
            self.token_visible = not self.token_visible
            
        toggle_btn = ttk.Button(token_frame, text="显示", command=toggle_token_visibility, width=6)
        toggle_btn.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 签名密钥
        secret_frame = ttk.Frame(server_group)
        secret_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(secret_frame, text="签名密钥:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['onebot_secret'] = tk.StringVar()
        secret_entry = ttk.Entry(secret_frame, textvariable=self.config_vars['onebot_secret'], show="*")
        secret_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 显示/隐藏密钥按钮
        self.secret_visible = False
        def toggle_secret_visibility():
            if self.secret_visible:
                secret_entry.config(show="*")
                secret_toggle_btn.config(text="显示")
            else:
                secret_entry.config(show="")
                secret_toggle_btn.config(text="隐藏")
            self.secret_visible = not self.secret_visible
            
        secret_toggle_btn = ttk.Button(secret_frame, text="显示", command=toggle_secret_visibility, width=6)
        secret_toggle_btn.pack(side=tk.RIGHT, padx=(5, 10))
        
        # 超时设置
        timeout_frame = ttk.Frame(server_group)
        timeout_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(timeout_frame, text="超时时间(秒):").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['onebot_timeout'] = tk.IntVar()
        ttk.Entry(timeout_frame, textvariable=self.config_vars['onebot_timeout']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 连接测试
        test_frame = ttk.Frame(server_group)
        test_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(test_frame, text="测试连接", command=self.test_onebot_connection).pack(side=tk.LEFT)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def setup_server_tab(self):
        """设置服务器配置标签页"""
        server_frame = ttk.Frame(self.notebook)
        self.notebook.add(server_frame, text="服务器")
        
        # HTTP服务器配置
        http_group = ttk.LabelFrame(server_frame, text="HTTP服务器配置", padding=10)
        http_group.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # 监听地址
        host_frame = ttk.Frame(http_group)
        host_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(host_frame, text="监听地址:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['server_host'] = tk.StringVar()
        ttk.Entry(host_frame, textvariable=self.config_vars['server_host']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 监听端口
        port_frame = ttk.Frame(http_group)
        port_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(port_frame, text="监听端口:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['server_port'] = tk.IntVar()
        ttk.Entry(port_frame, textvariable=self.config_vars['server_port']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 调试模式
        debug_frame = ttk.Frame(http_group)
        debug_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(debug_frame, text="调试模式:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['server_debug'] = tk.BooleanVar()
        ttk.Checkbutton(debug_frame, variable=self.config_vars['server_debug']).pack(side=tk.RIGHT)
        
        # 工作线程数
        workers_frame = ttk.Frame(http_group)
        workers_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(workers_frame, text="工作线程数:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['server_workers'] = tk.IntVar()
        ttk.Entry(workers_frame, textvariable=self.config_vars['server_workers']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
    def setup_storage_tab(self):
        """设置存储配置标签页"""
        storage_frame = ttk.Frame(self.notebook)
        self.notebook.add(storage_frame, text="存储")
        
        # 存储配置
        storage_group = ttk.LabelFrame(storage_frame, text="存储配置", padding=10)
        storage_group.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # 存储类型
        type_frame = ttk.Frame(storage_group)
        type_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(type_frame, text="存储类型:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['storage_type'] = tk.StringVar()
        type_combo = ttk.Combobox(type_frame, textvariable=self.config_vars['storage_type'], 
                                 values=["json"], state="readonly")
        type_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 数据目录
        dir_frame = ttk.Frame(storage_group)
        dir_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(dir_frame, text="数据目录:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['storage_data_dir'] = tk.StringVar()
        dir_entry = ttk.Entry(dir_frame, textvariable=self.config_vars['storage_data_dir'])
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        def browse_data_dir():
            dirname = filedialog.askdirectory(
                title="选择数据目录"
            )
            if dirname:
                self.config_vars['storage_data_dir'].set(dirname)
                
        ttk.Button(dir_frame, text="浏览", command=browse_data_dir).pack(side=tk.RIGHT)
        
        # 自动备份
        backup_frame = ttk.Frame(storage_group)
        backup_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(backup_frame, text="自动备份:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['storage_auto_backup'] = tk.BooleanVar()
        ttk.Checkbutton(backup_frame, variable=self.config_vars['storage_auto_backup']).pack(side=tk.RIGHT)
        
        # 备份间隔
        interval_frame = ttk.Frame(storage_group)
        interval_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(interval_frame, text="备份间隔(小时):").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['storage_backup_interval'] = tk.IntVar()
        ttk.Entry(interval_frame, textvariable=self.config_vars['storage_backup_interval']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
    def setup_log_tab(self):
        """设置日志配置标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="日志")
        
        # 日志配置
        log_group = ttk.LabelFrame(log_frame, text="日志配置", padding=10)
        log_group.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # 日志级别
        level_frame = ttk.Frame(log_group)
        level_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(level_frame, text="日志级别:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['log_level'] = tk.StringVar()
        level_combo = ttk.Combobox(
            level_frame,
            textvariable=self.config_vars['log_level'],
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly"
        )
        level_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 日志文件路径
        file_frame = ttk.Frame(log_group)
        file_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(file_frame, text="日志文件:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['log_file'] = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.config_vars['log_file'])
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        def browse_log_file():
            filename = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("所有文件", "*.*")],
                title="选择日志文件"
            )
            if filename:
                self.config_vars['log_file'].set(filename)
                
        ttk.Button(file_frame, text="浏览", command=browse_log_file).pack(side=tk.RIGHT)
        
        # 最大文件大小
        size_frame = ttk.Frame(log_group)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(size_frame, text="最大文件大小(MB):").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['log_max_size'] = tk.IntVar()
        ttk.Entry(size_frame, textvariable=self.config_vars['log_max_size']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 保留天数
        retention_frame = ttk.Frame(log_group)
        retention_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(retention_frame, text="保留天数:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['log_retention'] = tk.IntVar()
        ttk.Entry(retention_frame, textvariable=self.config_vars['log_retention']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 控制台输出
        console_frame = ttk.Frame(log_group)
        console_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(console_frame, text="控制台输出:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['log_console'] = tk.BooleanVar()
        ttk.Checkbutton(console_frame, variable=self.config_vars['log_console']).pack(side=tk.RIGHT)
        
    def setup_wordlib_tab(self):
        """设置词库配置标签页"""
        wordlib_frame = ttk.Frame(self.notebook)
        self.notebook.add(wordlib_frame, text="词库")
        
        # 词库配置
        wordlib_group = ttk.LabelFrame(wordlib_frame, text="词库配置", padding=10)
        wordlib_group.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        # 词库路径
        path_frame = ttk.Frame(wordlib_group)
        path_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(path_frame, text="词库路径:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['wordlib_path'] = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.config_vars['wordlib_path'])
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        def browse_wordlib_path():
            dirname = filedialog.askdirectory(title="选择词库目录")
            if dirname:
                self.config_vars['wordlib_path'].set(dirname)
                
        ttk.Button(path_frame, text="浏览", command=browse_wordlib_path).pack(side=tk.RIGHT)
        
        # 自动重载
        reload_frame = ttk.Frame(wordlib_group)
        reload_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(reload_frame, text="自动重载:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['wordlib_auto_reload'] = tk.BooleanVar()
        ttk.Checkbutton(reload_frame, variable=self.config_vars['wordlib_auto_reload']).pack(side=tk.RIGHT)
        
        # 编码格式
        encoding_frame = ttk.Frame(wordlib_group)
        encoding_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(encoding_frame, text="编码格式:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['wordlib_encoding'] = tk.StringVar()
        encoding_combo = ttk.Combobox(
            encoding_frame,
            textvariable=self.config_vars['wordlib_encoding'],
            values=["utf-8", "gbk", "gb2312"],
            state="readonly"
        )
        encoding_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # JSON存储路径
        json_path_frame = ttk.Frame(wordlib_group)
        json_path_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(json_path_frame, text="JSON存储路径:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['wordlib_json_storage_path'] = tk.StringVar()
        json_path_entry = ttk.Entry(json_path_frame, textvariable=self.config_vars['wordlib_json_storage_path'])
        json_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        def browse_json_path():
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
                title="选择JSON存储文件"
            )
            if filename:
                self.config_vars['wordlib_json_storage_path'].set(filename)
                
        ttk.Button(json_path_frame, text="浏览", command=browse_json_path).pack(side=tk.RIGHT)
        
        # 缓存大小
        cache_frame = ttk.Frame(wordlib_group)
        cache_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(cache_frame, text="缓存大小:").pack(side=tk.LEFT, anchor=tk.W)
        self.config_vars['wordlib_cache_size'] = tk.IntVar()
        ttk.Entry(cache_frame, textvariable=self.config_vars['wordlib_cache_size']).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
    def setup_button_area(self, parent):
        """设置按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        # 左侧按钮
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(
            left_buttons,
            text="重置",
            command=self.reset_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            left_buttons,
            text="导入",
            command=self.import_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            left_buttons,
            text="导出",
            command=self.export_config
        ).pack(side=tk.LEFT)
        
        # 右侧按钮
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(
            right_buttons,
            text="取消",
            command=self.window.destroy
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            right_buttons,
            text="应用",
            command=self.apply_config
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            right_buttons,
            text="确定",
            command=self.save_and_close
        ).pack(side=tk.LEFT)
        
    def load_config(self):
        """加载配置到界面"""
        try:
            # OneBot配置
            self.config_vars['onebot_host'].set(self.config.onebot.host)
            self.config_vars['onebot_port'].set(self.config.onebot.port)
            self.config_vars['onebot_access_token'].set(self.config.onebot.access_token or "")
            self.config_vars['onebot_secret'].set(self.config.onebot.secret or "")
            self.config_vars['onebot_timeout'].set(self.config.onebot.timeout)
            
            # 服务器配置
            self.config_vars['server_host'].set(self.config.server.host)
            self.config_vars['server_port'].set(self.config.server.port)
            self.config_vars['server_debug'].set(self.config.server.debug)
            self.config_vars['server_workers'].set(self.config.server.workers)
            
            # 存储配置
            self.config_vars['storage_type'].set(self.config.storage.type)
            self.config_vars['storage_data_dir'].set(self.config.storage.data_dir)
            self.config_vars['storage_auto_backup'].set(self.config.storage.auto_backup)
            self.config_vars['storage_backup_interval'].set(self.config.storage.backup_interval)
            
            # 日志配置
            self.config_vars['log_level'].set(self.config.log.level)
            self.config_vars['log_file'].set(self.config.log.file)
            # 处理max_size字段，如果是字符串则提取数字部分
            max_size = self.config.log.max_size
            if isinstance(max_size, str):
                # 提取字符串中的数字部分，如"10 MB" -> 10
                import re
                match = re.search(r'(\d+)', max_size)
                max_size = int(match.group(1)) if match else 10
            self.config_vars['log_max_size'].set(max_size)
            # 处理retention字段，如果是字符串则提取数字部分
            retention = self.config.log.retention
            if isinstance(retention, str):
                # 提取字符串中的数字部分，如"7 days" -> 7
                match = re.search(r'(\d+)', retention)
                retention = int(match.group(1)) if match else 7
            self.config_vars['log_retention'].set(retention)
            self.config_vars['log_console'].set(self.config.log.console)
            
            # 词库配置
            self.config_vars['wordlib_path'].set(self.config.wordlib.path)
            self.config_vars['wordlib_auto_reload'].set(self.config.wordlib.auto_reload)
            self.config_vars['wordlib_encoding'].set(self.config.wordlib.encoding)
            self.config_vars['wordlib_json_storage_path'].set(self.config.wordlib.json_storage_path)
            self.config_vars['wordlib_cache_size'].set(self.config.wordlib.cache_size)
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            messagebox.showerror("错误", f"加载配置失败: {e}")
            
    def apply_config(self):
        """应用配置"""
        try:
            # 验证配置
            if not self.validate_config():
                return
                
            # 更新配置对象
            self.update_config_object()
            
            # 更新ConfigManager的配置对象并保存
            self.config_manager.config = self.config
            self.config_manager.save_config()
            
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
            
    def save_and_close(self):
        """保存并关闭"""
        self.apply_config()
        self.window.destroy()
        
    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "确定要重置所有配置吗？"):
            try:
                # 重新加载默认配置
                default_config = BotConfig()
                self.config = default_config
                self.load_config()
                messagebox.showinfo("成功", "配置已重置")
            except Exception as e:
                self.logger.error(f"重置配置失败: {e}")
                messagebox.showerror("错误", f"重置配置失败: {e}")
                
    def import_config(self):
        """导入配置"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("YAML文件", "*.yaml"), ("TOML文件", "*.toml"), ("所有文件", "*.*")],
                title="选择配置文件"
            )
            
            if filename:
                imported_config = self.config_manager.load_config(filename)
                self.config = imported_config
                self.load_config()
                messagebox.showinfo("成功", "配置已导入")
                
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            messagebox.showerror("错误", f"导入配置失败: {e}")
            
    def export_config(self):
        """导出配置"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".yaml",
                filetypes=[("YAML文件", "*.yaml"), ("TOML文件", "*.toml"), ("所有文件", "*.*")],
                title="保存配置文件"
            )
            
            if filename:
                # 更新配置对象
                self.update_config_object()
                
                # 保存到指定文件
                self.config_manager.save_config(self.config, filename)
                messagebox.showinfo("成功", f"配置已导出到: {filename}")
                
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            messagebox.showerror("错误", f"导出配置失败: {e}")
            
    def validate_config(self) -> bool:
        """验证配置"""
        try:
            # 验证端口号
            onebot_port = self.config_vars['onebot_port'].get()
            server_port = self.config_vars['server_port'].get()
            
            if not (1 <= onebot_port <= 65535):
                messagebox.showerror("错误", "OneBot端口号必须在1-65535之间")
                return False
                
            if not (1 <= server_port <= 65535):
                messagebox.showerror("错误", "服务器端口号必须在1-65535之间")
                return False
                
            # 验证路径
            storage_dir = self.config_vars['storage_data_dir'].get()
            if storage_dir:
                storage_parent_dir = os.path.dirname(storage_dir)
                if storage_parent_dir and not os.path.exists(storage_parent_dir):
                    if messagebox.askyesno("确认", f"存储目录 {storage_parent_dir} 不存在，是否创建？"):
                        os.makedirs(storage_parent_dir, exist_ok=True)
                    else:
                        return False
                        
            wordlib_path = self.config_vars['wordlib_path'].get()
            if wordlib_path and not os.path.exists(wordlib_path):
                if messagebox.askyesno("确认", f"词库目录 {wordlib_path} 不存在，是否创建？"):
                    os.makedirs(wordlib_path, exist_ok=True)
                else:
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"验证配置失败: {e}")
            messagebox.showerror("错误", f"验证配置失败: {e}")
            return False
            
    def update_config_object(self):
        """更新配置对象"""
        # OneBot配置
        self.config.onebot.host = self.config_vars['onebot_host'].get()
        self.config.onebot.port = self.config_vars['onebot_port'].get()
        self.config.onebot.access_token = self.config_vars['onebot_access_token'].get() or None
        self.config.onebot.secret = self.config_vars['onebot_secret'].get() or None
        self.config.onebot.timeout = self.config_vars['onebot_timeout'].get()
        
        # 服务器配置
        self.config.server.host = self.config_vars['server_host'].get()
        self.config.server.port = self.config_vars['server_port'].get()
        self.config.server.debug = self.config_vars['server_debug'].get()
        self.config.server.workers = self.config_vars['server_workers'].get()
        
        # 存储配置
        self.config.storage.type = self.config_vars['storage_type'].get()
        self.config.storage.data_dir = self.config_vars['storage_data_dir'].get()
        self.config.storage.auto_backup = self.config_vars['storage_auto_backup'].get()
        self.config.storage.backup_interval = self.config_vars['storage_backup_interval'].get()
        
        # 日志配置
        self.config.log.level = self.config_vars['log_level'].get()
        self.config.log.file = self.config_vars['log_file'].get()
        # 将整数值转换为带单位的字符串格式
        max_size_value = self.config_vars['log_max_size'].get()
        self.config.log.max_size = f"{max_size_value} MB"
        # 将整数值转换为带单位的字符串格式
        retention_value = self.config_vars['log_retention'].get()
        self.config.log.retention = f"{retention_value} days"
        self.config.log.console = self.config_vars['log_console'].get()
        
        # 词库配置
        self.config.wordlib.path = self.config_vars['wordlib_path'].get()
        self.config.wordlib.auto_reload = self.config_vars['wordlib_auto_reload'].get()
        self.config.wordlib.encoding = self.config_vars['wordlib_encoding'].get()
        self.config.wordlib.json_storage_path = self.config_vars['wordlib_json_storage_path'].get()
        self.config.wordlib.cache_size = self.config_vars['wordlib_cache_size'].get()
        
    def test_onebot_connection(self):
        """测试OneBot连接"""
        try:
            # 这里可以添加实际的连接测试逻辑
            host = self.config_vars['onebot_host'].get()
            port = self.config_vars['onebot_port'].get()
            
            messagebox.showinfo("测试连接", f"连接测试功能待实现\n目标: {host}:{port}")
            
        except Exception as e:
            self.logger.error(f"测试连接失败: {e}")
            messagebox.showerror("错误", f"测试连接失败: {e}")