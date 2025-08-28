#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lchliebedich词库管理器
"""

import os
import json
from typing import Dict, List, Any, Optional
from .lchliebedich_engine import LchliebedichEngine
from .base_manager import WordLibManager


class LchliebedichWordLibManager(WordLibManager):
    def __init__(self, bot, config):
        """lchliebedich词库管理器"""
        super().__init__(bot, 'lchliebedich')
        # 从配置对象中提取词库目录路径
        if hasattr(config, 'wordlib') and hasattr(config.wordlib, 'data_dir'):
            self.wordlib_dir = config.wordlib.data_dir
        else:
            self.wordlib_dir = "data/wordlib"
        self.engines: Dict[str, LchliebedichEngine] = {}
        self.enabled_files: List[str] = []
        self.config_file = os.path.join(self.wordlib_dir, "config.json")
        
        # 确保词库目录存在
        os.makedirs(self.wordlib_dir, exist_ok=True)
        
        # 加载配置
        self._load_config()
        
        # 自动加载启用的词库文件
        self._load_enabled_files()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.enabled_files = config.get('enabled_files', [])
        except Exception as e:
            print(f"加载词库配置失败: {e}")
            self.enabled_files = []
    
    def _load_enabled_files(self):
        """自动加载启用的词库文件"""
        # 如果没有启用的文件，尝试加载所有.txt文件
        if not self.enabled_files:
            for filename in os.listdir(self.wordlib_dir):
                if filename.endswith('.txt'):
                    self.load_wordlib_file(filename)
        else:
            # 加载配置中启用的文件
            for filename in self.enabled_files:
                file_path = os.path.join(self.wordlib_dir, filename)
                if os.path.exists(file_path):
                    engine = LchliebedichEngine()
                    if engine.load_lexicon_file(file_path):
                        self.engines[filename] = engine
                        print(f"词库文件加载成功: {filename}")
                    else:
                        print(f"词库文件加载失败: {filename}")
                else:
                    print(f"启用的词库文件不存在: {filename}")
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config = {
                'enabled_files': self.enabled_files
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存词库配置失败: {e}")
    
    def load_wordlib_file(self, filename: str) -> bool:
        """加载词库文件"""
        file_path = os.path.join(self.wordlib_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"词库文件不存在: {file_path}")
            return False
        
        engine = LchliebedichEngine()
        if engine.load_lexicon_file(file_path):
            self.engines[filename] = engine
            if filename not in self.enabled_files:
                self.enabled_files.append(filename)
                self._save_config()
            print(f"词库文件加载成功: {filename}")
            return True
        else:
            print(f"词库文件加载失败: {filename}")
            return False
    
    def unload_wordlib_file(self, filename: str) -> bool:
        """卸载词库文件"""
        if filename in self.engines:
            del self.engines[filename]
        
        if filename in self.enabled_files:
            self.enabled_files.remove(filename)
            self._save_config()
        
        print(f"词库文件已卸载: {filename}")
        return True
    
    def reload_all_wordlibs(self):
        """重新加载所有词库"""
        self.engines.clear()
        
        # 重新加载启用的词库文件（与初始化逻辑保持一致）
        self._load_enabled_files()
    
    def reload_all(self):
        """重新加载所有词库（别名方法）"""
        return self.reload_all_wordlibs()
    
    def get_wordlib_files(self) -> List[Dict[str, Any]]:
        """获取词库文件列表"""
        files = []
        
        if os.path.exists(self.wordlib_dir):
            for filename in os.listdir(self.wordlib_dir):
                if filename.endswith('.txt'):
                    file_path = os.path.join(self.wordlib_dir, filename)
                    files.append({
                        'filename': filename,
                        'enabled': filename in self.enabled_files,
                        'loaded': filename in self.engines,
                        'size': os.path.getsize(file_path),
                        'entries': len(self.engines[filename].entries) if filename in self.engines else 0
                    })
        
        return files
    
    def toggle_wordlib_file(self, filename: str) -> bool:
        """切换词库文件启用状态"""
        if filename in self.enabled_files:
            # 禁用
            self.unload_wordlib_file(filename)
            return False
        else:
            # 启用
            return self.load_wordlib_file(filename)
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """处理消息"""
        for filename, engine in self.engines.items():
            if filename in self.enabled_files:
                response = engine.process_message(message, context)
                if response:
                    return response
        
        return None
    
    def find_response(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """查找消息的回复（兼容性方法）"""
        return self.process_message(message, context)
    
    def create_sample_wordlib(self):
        """创建示例词库文件"""
        sample_content = '''// lchliebedich词库示例文件
// 这是注释行，以//、##或&&开头

// 基础问候
你好
你好！我是机器人助手。

早上好
早上好！今天是 %date%，祝你有美好的一天！

// 带参数的回复
测试参数(.*) (.*)
参数1: %括号1%
参数2: %括号2%
原始内容: %参数-1%

// 变量使用
测试变量
A:Hello
B:World
%A% %B%！

// 条件判断
测试条件
如果:%QQ%==123456
你是管理员！
else
你是普通用户。
如果尾

// 随机回复
随机测试
#->var:
[
    "回复1",
    "回复2", 
    "回复3"
]
#->var:replies
$随机数 replies 1$

// 图片回复
发图
$图片 https://q4.qlogo.cn/g?b=qq&nk=%QQ%&s=140$

// 表情回复
笑脸
$Emoy 13$

// 时间相关
现在几点
现在是 %datetime%
时间戳：%时间戳%

// 群聊专用
群信息
如果:$群聊消息$
群号：%群号%
群成员：%昵称%(%QQ%)
else
这不是群聊消息
如果尾
'''
        
        sample_file = os.path.join(self.wordlib_dir, "lchliebedich_example.txt")
        try:
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            print(f"示例词库文件已创建: {sample_file}")
            return True
        except Exception as e:
            print(f"创建示例词库文件失败: {e}")
            return False
    
    def get_all_entries(self) -> List[Dict[str, Any]]:
        """获取所有词库条目"""
        all_entries = []
        for engine in self.engines.values():
            all_entries.extend(engine.entries)
        return all_entries
    
    def get_entry(self, entry_id: int) -> Optional[Any]:
        """根据索引获取词库条目"""
        all_entries = []
        for engine in self.engines.values():
            all_entries.extend(engine.entries)
        
        if 0 <= entry_id < len(all_entries):
            return all_entries[entry_id]
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_entries = sum(len(engine.entries) for engine in self.engines.values())
        
        return {
            'total_files': len(self.get_wordlib_files()),
            'enabled_files': len(self.enabled_files),
            'loaded_engines': len(self.engines),
            'total_entries': total_entries
        }