#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI主窗口模块
提供图形化界面管理机器人框架
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import asyncio
import json
from typing import Optional
from datetime import datetime
import webbrowser

from .wordlib_window import WordLibWindow
from .config_window import ConfigWindow
from .log_window import LogWindow
from ..wordlib.manager import LchliebedichWordLibManager
from ..config.settings import ConfigManager
from ..utils.logger import get_logger

class MainWindow:
    """主窗口类"""
    
    def __init__(self, root: tk.Tk, wordlib_manager: LchliebedichWordLibManager, onebot_engine=None, onebot_framework=None):
        self.root = root
        self.wordlib_manager = wordlib_manager
        self.onebot_engine = onebot_engine
        self.onebot_framework = onebot_framework
        self.logger = get_logger("MainWindow")
        
        # 窗口状态
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # 子窗口
        self.wordlib_window: Optional[WordLibWindow] = None
        self.config_window: Optional[ConfigWindow] = None
        self.log_window: Optional[LogWindow] = None
        
        self.setup_ui()
        self.setup_menu()
        self.update_status()
        
        # 定时更新状态
        self.root.after(1000, self.update_status_loop)
        
    def setup_ui(self):
        """设置UI界面"""
        self.root.title("OneBot引擎启动器")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 设置图标（如果有的话）
        try:
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
            
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        self.setup_control_panel(main_frame)
        
        # 中间内容区域
        self.setup_content_area(main_frame)
        
        # 底部状态栏
        self.setup_status_bar(main_frame)
        
    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导入词库", command=self.import_wordlib)
        file_menu.add_command(label="导出词库", command=self.export_wordlib)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="词库管理", command=self.open_wordlib_window)
        tools_menu.add_command(label="配置设置", command=self.open_config_window)
        tools_menu.add_command(label="日志查看", command=self.open_log_window)
        tools_menu.add_separator()
        tools_menu.add_command(label="测试连接", command=self.test_connection)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def setup_control_panel(self, parent):
        """设置控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮框架
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        # 重载词库按钮（移到第一个位置）
        
        # 重载词库按钮
        ttk.Button(
            button_frame,
            text="重载词库",
            command=self.reload_wordlib
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空日志按钮
        ttk.Button(
            button_frame,
            text="清空日志",
            command=self.clear_logs
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # OneBot引擎控制按钮已移除 - 改为手动启动模式
        
        # 状态指示器
        status_frame = ttk.Frame(button_frame)
        status_frame.pack(side=tk.RIGHT)
        
        ttk.Label(status_frame, text="词库状态:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="已加载", foreground="green")
        self.status_label.pack(side=tk.LEFT, padx=(5, 10))
        
        # OneBot引擎状态指示器（仅显示连接状态）
        if self.onebot_engine:
            ttk.Label(status_frame, text="OneBot状态:").pack(side=tk.LEFT)
            self.engine_status_label = ttk.Label(status_frame, text="监听中", foreground="blue")
            self.engine_status_label.pack(side=tk.LEFT, padx=(5, 0))
        
    def setup_content_area(self, parent):
        """设置内容区域"""
        # 创建Notebook（标签页）
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 概览标签页
        self.setup_overview_tab()
        
        # 消息日志标签页
        self.setup_message_log_tab()
        
        # 统计信息标签页
        self.setup_stats_tab()
        
    def setup_overview_tab(self):
        """设置概览标签页"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="概览")
        
        # 机器人信息
        info_frame = ttk.LabelFrame(overview_frame, text="机器人信息", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.bot_info_text = scrolledtext.ScrolledText(
            info_frame, 
            height=6, 
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.bot_info_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置信息
        config_frame = ttk.LabelFrame(overview_frame, text="配置信息", padding=10)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.config_info_text = scrolledtext.ScrolledText(
            config_frame, 
            height=8, 
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.config_info_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_message_log_tab(self):
        """设置消息日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="消息日志")
        
        # 工具栏
        toolbar_frame = ttk.Frame(log_frame)
        toolbar_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(
            toolbar_frame,
            text="清空日志",
            command=self.clear_message_log
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            toolbar_frame,
            text="保存日志",
            command=self.save_message_log
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # 自动滚动选项
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar_frame,
            text="自动滚动",
            variable=self.auto_scroll_var
        ).pack(side=tk.RIGHT)
        
        # 消息日志文本框
        self.message_log_text = scrolledtext.ScrolledText(
            log_frame,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.message_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
    def setup_stats_tab(self):
        """设置统计信息标签页"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="统计信息")
        
        # 统计信息显示
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def setup_status_bar(self, parent):
        """设置状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        # 分隔线
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
        
        # 状态信息
        self.status_info_label = ttk.Label(status_frame, text="就绪")
        self.status_info_label.pack(side=tk.LEFT)
        
        # 时间显示
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.pack(side=tk.RIGHT)
        
    def reload_wordlib(self):
        """重载词库"""
        try:
            self.wordlib_manager.reload_all()
            self.status_label.config(text="已重载", foreground="green")
            self.log_message("词库已重载")
            messagebox.showinfo("成功", "词库重载完成")
        except Exception as e:
            self.logger.error(f"重载词库失败: {e}")
            messagebox.showerror("错误", f"重载词库失败: {e}")
            

            

            

            

        

            
    def clear_logs(self):
        """清空日志"""
        self.message_log_text.config(state=tk.NORMAL)
        self.message_log_text.delete(1.0, tk.END)
        self.message_log_text.config(state=tk.DISABLED)
        
    def clear_message_log(self):
        """清空消息日志"""
        self.clear_logs()
        
    def save_message_log(self):
        """保存消息日志"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存消息日志"
            )
            
            if filename:
                content = self.message_log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("成功", f"日志已保存到: {filename}")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存日志失败: {e}")
            
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.message_log_text.config(state=tk.NORMAL)
        self.message_log_text.insert(tk.END, log_entry)
        
        if self.auto_scroll_var.get():
            self.message_log_text.see(tk.END)
            
        self.message_log_text.config(state=tk.DISABLED)
        
    def update_status(self):
        """更新状态信息"""
        # 更新时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        
        # 更新OneBot引擎状态
        if self.onebot_engine:
            self.update_engine_status()
        
        # 更新词库信息
        self.update_wordlib_info()
        
        # 更新配置信息
        self.update_config_info()
        
        # 更新统计信息
        self.update_stats_info()
        
    def update_status_loop(self):
        """状态更新循环"""
        self.update_status()
        self.update_message_logs()
        self.root.after(5000, self.update_status_loop)  # 每5秒更新一次
        
    def update_message_logs(self):
        """更新消息日志"""
        try:
            if self.onebot_framework and hasattr(self.onebot_framework, 'message_handler'):
                # 从消息处理器获取最新消息
                message_handler = self.onebot_framework.message_handler
                if hasattr(message_handler, 'recent_messages'):
                    for message in message_handler.recent_messages:
                        if message.get('message_type') == 'group':
                            group_id = message.get('group_id', '未知群')
                            user_id = message.get('user_id', '未知用户')
                            raw_message = message.get('raw_message', '')
                            self.log_message(f"[群:{group_id}] {user_id}: {raw_message}")
                        elif message.get('message_type') == 'private':
                            user_id = message.get('user_id', '未知用户')
                            raw_message = message.get('raw_message', '')
                            self.log_message(f"[私聊] {user_id}: {raw_message}")
                    # 清空已处理的消息
                    message_handler.recent_messages.clear()
        except Exception as e:
            self.logger.error(f"更新消息日志失败: {e}")
        
    def update_wordlib_info(self):
        """更新机器人信息"""
        try:
            wordlib_count = len(self.wordlib_manager.get_all_entries())
            
            info_text = "机器人信息:\n"
            info_text += f"词库条目数: {wordlib_count}\n"
            info_text += f"词库状态: 已加载\n"
            
            # 添加OneBot引擎和机器人信息
            if self.onebot_engine:
                engine_status = "已连接" if self.onebot_engine.is_connected() else "监听中"
                info_text += f"引擎状态: {engine_status}\n"
                
                # 获取机器人信息
                bot_info = self.onebot_engine.get_bot_info()
                if self.onebot_framework and hasattr(self.onebot_framework, 'bot_info'):
                    framework_bot_info = self.onebot_framework.bot_info
                    if framework_bot_info.get('user_id'):
                        info_text += f"机器人QQ: {framework_bot_info['user_id']}\n"
                    if framework_bot_info.get('nickname'):
                        info_text += f"机器人昵称: {framework_bot_info['nickname']}\n"
                elif bot_info.get('qq'):
                    info_text += f"机器人QQ: {bot_info['qq']}\n"
                    if bot_info.get('nickname'):
                        info_text += f"机器人昵称: {bot_info['nickname']}\n"
                    
                # 获取登录状态和时间
                login_status = self.onebot_engine.get_login_status()
                info_text += f"登录状态: {login_status.value}\n"
                
                # 如果已登录，显示登录时间
                if hasattr(self.onebot_engine, 'login_time') and self.onebot_engine.login_time:
                    login_time_str = datetime.fromtimestamp(self.onebot_engine.login_time).strftime('%Y-%m-%d %H:%M:%S')
                    info_text += f"登录时间: {login_time_str}\n"
            else:
                info_text += "引擎状态: 未连接\n"
            
            info_text += f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            self.bot_info_text.config(state=tk.NORMAL)
            self.bot_info_text.delete(1.0, tk.END)
            self.bot_info_text.insert(1.0, info_text)
            self.bot_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"更新机器人信息失败: {e}")
            
    def update_config_info(self):
        """更新配置信息"""
        try:
            config_text = "配置信息:\n"
            config_text += f"词库管理器: 已加载\n"
            config_text += f"OneBot引擎: {'已连接' if self.onebot_engine else '未连接'}\n"
            
            self.config_info_text.config(state=tk.NORMAL)
            self.config_info_text.delete(1.0, tk.END)
            self.config_info_text.insert(1.0, config_text)
            self.config_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"更新配置信息失败: {e}")
            
    def update_stats_info(self):
        """更新统计信息"""
        try:
            stats_text = "统计信息:\n\n"
            stats_text += f"词库条目数: {len(self.wordlib_manager.get_all_entries())}\n"
            stats_text += f"引擎状态: {'已连接' if self.onebot_engine and self.onebot_engine.is_connected() else '监听中'}\n"
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
            
    def test_connection(self):
        """测试OneBot引擎连接"""
        try:
            if self.onebot_engine and self.onebot_engine.is_connected():
                messagebox.showinfo("连接测试", "OneBot引擎运行正常")
            else:
                messagebox.showwarning("连接测试", "OneBot引擎未运行")
        except Exception as e:
            messagebox.showerror("错误", f"连接测试失败: {e}")
            
    def import_wordlib(self):
        """导入词库"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="选择词库文件"
            )
            
            if filename:
                self.wordlib_manager.import_from_file(filename)
                messagebox.showinfo("成功", f"词库已从 {filename} 导入")
                
        except Exception as e:
            messagebox.showerror("错误", f"导入词库失败: {e}")
            
    def export_wordlib(self):
        """导出词库"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存词库文件"
            )
            
            if filename:
                self.wordlib_manager.export_to_file(filename)
                messagebox.showinfo("成功", f"词库已导出到: {filename}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出词库失败: {e}")
            
    def open_wordlib_window(self):
        """打开词库管理窗口"""
        if self.wordlib_window is None or not self.wordlib_window.window.winfo_exists():
            self.wordlib_window = WordLibWindow(self.root, self.wordlib_manager)
        else:
            self.wordlib_window.window.lift()
            
    def open_config_window(self):
        """打开配置窗口"""
        if self.config_window is None or not self.config_window.window.winfo_exists():
            config_manager = ConfigManager()
            config = config_manager.load_config()
            self.config_window = ConfigWindow(self.root, config)
        else:
            self.config_window.window.lift()
            
    def open_log_window(self):
        """打开日志窗口"""
        if self.log_window is None or not self.log_window.window.winfo_exists():
            self.log_window = LogWindow(self.root)
        else:
            self.log_window.window.lift()
            
    def show_help(self):
        """显示帮助"""
        help_text = """
 LchLiebedich - 使用说明

左上角文件 可导入词库
导入后还需在data\wordlib\config.json 添加词库名称 才可正常加载


"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        help_window.grab_set()
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
    def show_about(self):
        """显示关于信息"""
        about_text = """

版本: 0.1.0

基于OneBot V11协议的机器人框架

开发者: Tavre
项目地址：https://github.com/Tavre/lchliebedich
"""
        messagebox.showinfo("关于", about_text)
        
    def on_closing(self):
        """窗口关闭事件"""
        if self.onebot_engine and self.onebot_engine.is_connected():
            if messagebox.askokcancel("退出", "OneBot连接监听器正在运行，确定要退出吗？"):
                self.root.destroy()
        else:
            self.root.destroy()
            
    # OneBot引擎控制方法已移除 - 改为手动启动模式
            
    def update_engine_status(self):
         """更新OneBot连接状态"""
         if not self.onebot_engine:
             return
             
         try:
             # 检查OneBot连接状态
             login_status = self.onebot_engine.get_login_status()
             if login_status.name == "LOGGED_IN":
                 self.engine_status_label.config(text="已连接", foreground="green")
             elif login_status.name == "CONNECTING":
                 self.engine_status_label.config(text="连接中", foreground="orange")
             elif login_status.name == "DISCONNECTED":
                 self.engine_status_label.config(text="未连接", foreground="red")
             else:
                 self.engine_status_label.config(text="监听中", foreground="blue")
         except Exception as e:
            self.logger.error(f"获取连接状态失败: {e}")
            self.engine_status_label.config(text="监听中", foreground="blue")