#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
词库管理窗口模块
提供词库的图形化管理界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Optional
import re

from ..wordlib.manager import LchliebedichWordLibManager
from ..utils.logger import get_logger

class WordLibWindow:
    """词库管理窗口类"""
    
    def __init__(self, parent: tk.Tk, wordlib_manager: LchliebedichWordLibManager):
        self.parent = parent
        self.wordlib_manager = wordlib_manager
        self.logger = get_logger("WordLibWindow")
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("词库管理")
        self.window.geometry("900x700")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 当前选中的词库条目
        self.current_entry: Optional[dict] = None
        
        self.setup_ui()
        self.load_wordlib_list()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧词库列表
        self.setup_wordlib_list(main_frame)
        
        # 右侧编辑区域
        self.setup_edit_area(main_frame)
        
        # 底部按钮区域
        self.setup_button_area(main_frame)
        
    def setup_wordlib_list(self, parent):
        """设置词库列表"""
        # 左侧框架
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # 搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_changed)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 分类筛选
        filter_frame = ttk.Frame(left_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filter_frame, text="分类:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="全部")
        self.category_var.trace('w', self.on_category_changed)
        self.category_combo = ttk.Combobox(
            filter_frame, 
            textvariable=self.category_var,
            state="readonly",
            width=15
        )
        self.category_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 词库列表
        list_frame = ttk.LabelFrame(left_frame, text="词库列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("trigger", "category", "enabled")
        self.wordlib_tree = ttk.Treeview(
            list_frame, 
            columns=columns, 
            show="tree headings",
            height=15
        )
        
        # 设置列
        self.wordlib_tree.heading("#0", text="ID")
        self.wordlib_tree.heading("trigger", text="触发词")
        self.wordlib_tree.heading("category", text="分类")
        self.wordlib_tree.heading("enabled", text="状态")
        
        self.wordlib_tree.column("#0", width=50, minwidth=50)
        self.wordlib_tree.column("trigger", width=150, minwidth=100)
        self.wordlib_tree.column("category", width=80, minwidth=60)
        self.wordlib_tree.column("enabled", width=60, minwidth=50)
        
        # 滚动条
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.wordlib_tree.yview)
        self.wordlib_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.wordlib_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.wordlib_tree.bind("<<TreeviewSelect>>", self.on_item_selected)
        self.wordlib_tree.bind("<Double-1>", self.on_item_double_click)
        
        # 右键菜单
        self.setup_context_menu()
        
    def setup_edit_area(self, parent):
        """设置编辑区域"""
        # 右侧框架
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 编辑表单
        edit_frame = ttk.LabelFrame(right_frame, text="词库编辑", padding=10)
        edit_frame.pack(fill=tk.BOTH, expand=True)
        
        # 触发词
        trigger_frame = ttk.Frame(edit_frame)
        trigger_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(trigger_frame, text="触发词:").pack(side=tk.LEFT)
        self.trigger_var = tk.StringVar()
        trigger_entry = ttk.Entry(trigger_frame, textvariable=self.trigger_var)
        trigger_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 分类和优先级
        meta_frame = ttk.Frame(edit_frame)
        meta_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(meta_frame, text="分类:").pack(side=tk.LEFT)
        self.edit_category_var = tk.StringVar()
        category_entry = ttk.Entry(meta_frame, textvariable=self.edit_category_var, width=15)
        category_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(meta_frame, text="优先级:").pack(side=tk.LEFT)
        self.priority_var = tk.IntVar(value=1)
        priority_spin = ttk.Spinbox(
            meta_frame, 
            from_=1, 
            to=10, 
            textvariable=self.priority_var,
            width=10
        )
        priority_spin.pack(side=tk.LEFT, padx=(10, 20))
        
        # 启用状态
        self.enabled_var = tk.BooleanVar(value=True)
        enabled_check = ttk.Checkbutton(
            meta_frame, 
            text="启用", 
            variable=self.enabled_var
        )
        enabled_check.pack(side=tk.LEFT, padx=(10, 0))
        
        # 匹配类型
        match_frame = ttk.Frame(edit_frame)
        match_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(match_frame, text="匹配类型:").pack(side=tk.LEFT)
        self.match_type_var = tk.StringVar(value="exact")
        match_combo = ttk.Combobox(
            match_frame,
            textvariable=self.match_type_var,
            values=["exact", "contains", "startswith", "endswith", "regex"],
            state="readonly",
            width=15
        )
        match_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 回复内容
        reply_frame = ttk.Frame(edit_frame)
        reply_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        ttk.Label(reply_frame, text="回复内容:").pack(anchor=tk.W)
        
        # 回复文本框
        self.reply_text = scrolledtext.ScrolledText(
            reply_frame,
            height=10,
            wrap=tk.WORD
        )
        self.reply_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # 伪代码帮助
        help_frame = ttk.Frame(reply_frame)
        help_frame.pack(fill=tk.X)
        
        ttk.Button(
            help_frame,
            text="伪代码帮助",
            command=self.show_pseudocode_help
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            help_frame,
            text="测试回复",
            command=self.test_reply
        ).pack(side=tk.LEFT, padx=(10, 0))
        
    def setup_button_area(self, parent):
        """设置按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 左侧按钮
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(
            left_buttons,
            text="新建",
            command=self.new_entry
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            left_buttons,
            text="保存",
            command=self.save_entry
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            left_buttons,
            text="删除",
            command=self.delete_entry
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧按钮
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(
            right_buttons,
            text="导入",
            command=self.import_wordlib
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            right_buttons,
            text="导出",
            command=self.export_wordlib
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            right_buttons,
            text="关闭",
            command=self.window.destroy
        ).pack(side=tk.LEFT)
        
    def setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="编辑", command=self.edit_selected)
        self.context_menu.add_command(label="复制", command=self.copy_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="启用/禁用", command=self.toggle_enabled)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self.delete_entry)
        
        self.wordlib_tree.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.wordlib_tree.identify_row(event.y)
        if item:
            self.wordlib_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def load_wordlib_list(self):
        """加载词库列表"""
        try:
            # 清空现有项目
            for item in self.wordlib_tree.get_children():
                self.wordlib_tree.delete(item)
                
            # 获取所有词库条目
            entries = self.wordlib_manager.get_all_entries()
            
            # 更新分类列表
            categories = set(["全部"])
            for entry in entries:
                if entry.category:
                    categories.add(entry.category)
                    
            self.category_combo['values'] = sorted(list(categories))
            
            # 添加到树形控件
            for entry in entries:
                self.add_entry_to_tree(entry)
                
        except Exception as e:
            self.logger.error(f"加载词库列表失败: {e}")
            messagebox.showerror("错误", f"加载词库列表失败: {e}")
            
    def add_entry_to_tree(self, entry: dict):
        """添加词库条目到树形控件"""
        status = "启用" if entry.enabled else "禁用"
        self.wordlib_tree.insert(
            "", 
            tk.END,
            text=str(entry.id) if entry.id else "新建",
            values=(entry.trigger, entry.category or "默认", status),
            tags=("enabled" if entry.enabled else "disabled",)
        )
        
    def on_search_changed(self, *args):
        """搜索内容变化"""
        self.filter_wordlib_list()
        
    def on_category_changed(self, *args):
        """分类筛选变化"""
        self.filter_wordlib_list()
        
    def filter_wordlib_list(self):
        """筛选词库列表"""
        search_text = self.search_var.get().lower()
        category = self.category_var.get()
        
        # 清空现有项目
        for item in self.wordlib_tree.get_children():
            self.wordlib_tree.delete(item)
            
        # 获取所有词库条目
        entries = self.wordlib_manager.get_all_entries()
        
        # 筛选条目
        for entry in entries:
            # 分类筛选
            if category != "全部" and entry.category != category:
                continue
                
            # 搜索筛选
            if search_text:
                if (search_text not in entry.trigger.lower() and 
                    search_text not in (entry.response or "").lower()):
                    continue
                    
            self.add_entry_to_tree(entry)
            
    def on_item_selected(self, event):
        """列表项选择事件"""
        selection = self.wordlib_tree.selection()
        if selection:
            item = selection[0]
            entry_id = self.wordlib_tree.item(item, "text")
            
            if entry_id and entry_id != "新建":
                try:
                    entry = self.wordlib_manager.get_entry(int(entry_id))
                    if entry:
                        self.load_entry_to_form(entry)
                except ValueError:
                    pass
                    
    def on_item_double_click(self, event):
        """列表项双击事件"""
        self.edit_selected()
        
    def load_entry_to_form(self, entry: dict):
        """加载词库条目到表单"""
        self.current_entry = entry
        
        self.trigger_var.set(entry.trigger)
        self.edit_category_var.set(entry.category or "")
        self.priority_var.set(entry.priority)
        self.enabled_var.set(entry.enabled)
        self.match_type_var.set(entry.match_type)
        
        self.reply_text.delete(1.0, tk.END)
        if entry.response:
            self.reply_text.insert(1.0, entry.response)
            
    def clear_form(self):
        """清空表单"""
        self.current_entry = None
        
        self.trigger_var.set("")
        self.edit_category_var.set("")
        self.priority_var.set(1)
        self.enabled_var.set(True)
        self.match_type_var.set("exact")
        
        self.reply_text.delete(1.0, tk.END)
        
    def new_entry(self):
        """新建词库条目"""
        self.clear_form()
        
    def save_entry(self):
        """保存词库条目"""
        try:
            # 验证输入
            trigger = self.trigger_var.get().strip()
            if not trigger:
                messagebox.showerror("错误", "触发词不能为空")
                return
                
            reply = self.reply_text.get(1.0, tk.END).strip()
            if not reply:
                messagebox.showerror("错误", "回复内容不能为空")
                return
                
            # 创建或更新词库条目
            if self.current_entry and self.current_entry.id:
                # 更新现有条目
                self.wordlib_manager.update_entry(
                    self.current_entry.id,
                    trigger=trigger,
                    response=reply,
                    category=self.edit_category_var.get().strip() or None,
                    enabled=self.enabled_var.get(),
                    priority=self.priority_var.get(),
                    match_type=self.match_type_var.get()
                )
                messagebox.showinfo("成功", "词库条目已更新")
            else:
                # 新建条目
                entry_id = self.wordlib_manager.add_entry(
                    trigger=trigger,
                    response=reply,
                    category=self.edit_category_var.get().strip() or None,
                    enabled=self.enabled_var.get(),
                    priority=self.priority_var.get(),
                    match_type=self.match_type_var.get()
                )
                # 获取新创建的条目
                self.current_entry = self.wordlib_manager.get_entry(entry_id)
                messagebox.showinfo("成功", "词库条目已添加")
                
            # 重新加载列表
            self.load_wordlib_list()
            
        except Exception as e:
            self.logger.error(f"保存词库条目失败: {e}")
            messagebox.showerror("错误", f"保存词库条目失败: {e}")
            
    def delete_entry(self):
        """删除词库条目"""
        selection = self.wordlib_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的词库条目")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的词库条目吗？"):
            try:
                item = selection[0]
                entry_id = self.wordlib_tree.item(item, "text")
                
                if entry_id and entry_id != "新建":
                    self.wordlib_manager.delete_entry(int(entry_id))
                    self.load_wordlib_list()
                    self.clear_form()
                    messagebox.showinfo("成功", "词库条目已删除")
                    
            except Exception as e:
                self.logger.error(f"删除词库条目失败: {e}")
                messagebox.showerror("错误", f"删除词库条目失败: {e}")
                
    def edit_selected(self):
        """编辑选中的条目"""
        # 选中的条目已经通过on_item_selected加载到表单了
        pass
        
    def copy_selected(self):
        """复制选中的条目"""
        if self.current_entry:
            # 清除ID，作为新条目
            self.current_entry = None
            # 触发词添加"_副本"后缀
            current_trigger = self.trigger_var.get()
            self.trigger_var.set(f"{current_trigger}_副本")
            
    def toggle_enabled(self):
        """切换启用状态"""
        selection = self.wordlib_tree.selection()
        if not selection:
            return
            
        try:
            item = selection[0]
            entry_id = self.wordlib_tree.item(item, "text")
            
            if entry_id and entry_id != "新建":
                entry = self.wordlib_manager.get_entry(int(entry_id))
                if entry:
                    new_enabled = not entry.enabled
                    self.wordlib_manager.update_entry(int(entry_id), enabled=new_enabled)
                    self.load_wordlib_list()
                    
        except Exception as e:
            self.logger.error(f"切换启用状态失败: {e}")
            
    def test_reply(self):
        """测试回复"""
        try:
            reply_content = self.reply_text.get(1.0, tk.END).strip()
            if not reply_content:
                messagebox.showwarning("警告", "回复内容为空")
                return
                
            # 创建测试用的消息事件
            test_event = {
                "user_id": 123456,
                "group_id": 789012,
                "message": self.trigger_var.get(),
                "sender": {
                    "user_id": 123456,
                    "nickname": "测试用户",
                    "card": ""
                }
            }
            
            # 处理伪代码
            processor = self.wordlib_manager.pseudocode_processor
            processed_reply = processor.process(reply_content, test_event)
            
            # 显示结果
            result_window = tk.Toplevel(self.window)
            result_window.title("回复测试结果")
            result_window.geometry("500x300")
            result_window.transient(self.window)
            
            ttk.Label(result_window, text="原始内容:").pack(anchor=tk.W, padx=10, pady=(10, 0))
            
            original_text = scrolledtext.ScrolledText(result_window, height=5, wrap=tk.WORD)
            original_text.pack(fill=tk.X, padx=10, pady=5)
            original_text.insert(1.0, reply_content)
            original_text.config(state=tk.DISABLED)
            
            ttk.Label(result_window, text="处理结果:").pack(anchor=tk.W, padx=10, pady=(10, 0))
            
            result_text = scrolledtext.ScrolledText(result_window, height=5, wrap=tk.WORD)
            result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            result_text.insert(1.0, processed_reply)
            result_text.config(state=tk.DISABLED)
            
            ttk.Button(
                result_window,
                text="关闭",
                command=result_window.destroy
            ).pack(pady=10)
            
        except Exception as e:
            self.logger.error(f"测试回复失败: {e}")
            messagebox.showerror("错误", f"测试回复失败: {e}")
            
    def show_pseudocode_help(self):
        """显示伪代码帮助"""
        help_text = """
伪代码语法说明

1. 变量替换
   {user_id} - 用户ID
   {user_name} - 用户昵称
   {group_id} - 群组ID
   {message} - 原始消息内容

2. 条件语句
   [if 条件]内容[/if]
   [if user_id == 123456]你是管理员[/if]
   [if group_id]这是群聊[/if]

3. 随机选择
   [random]选项1|选项2|选项3[/random]
   [random]你好|您好|Hi[/random]

4. 内置函数
   [func:time:now] - 当前时间
   [func:time:date] - 当前日期
   [func:random:1:100] - 1到100的随机数
   [func:user:name] - 用户昵称（同{user_name}）
   [func:user:id] - 用户ID（同{user_id}）

5. 组合使用
   [if user_id == 123456]
   管理员{user_name}，当前时间是[func:time:now]
   [random]欢迎|您好|Hi[/random]！
   [/if]

注意：
- 条件语句支持 ==, !=, >, <, >=, <= 比较运算符
- 随机选择使用 | 分隔选项
- 函数参数使用 : 分隔
"""
        
        help_window = tk.Toplevel(self.window)
        help_window.title("伪代码语法帮助")
        help_window.geometry("600x500")
        help_window.transient(self.window)
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
        
        ttk.Button(
            help_window,
            text="关闭",
            command=help_window.destroy
        ).pack(pady=10)
        
    def import_wordlib(self):
        """导入词库"""
        messagebox.showinfo("提示", "导入功能待实现")
        
    def export_wordlib(self):
        """导出词库"""
        messagebox.showinfo("提示", "导出功能待实现")