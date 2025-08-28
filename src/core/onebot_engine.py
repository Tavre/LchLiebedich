#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneBot连接监听器
负责监听和解析OneBot引擎的状态信息
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass

from ..config.settings import OneBotConfig
from ..utils.logger import get_logger


class LoginStatus(Enum):
    """登录状态枚举"""
    UNKNOWN = "unknown"
    LOGGING_IN = "logging_in"
    LOGGED_IN = "logged_in"
    LOGIN_FAILED = "login_failed"
    DISCONNECTED = "disconnected"
    NEED_QRCODE = "need_qrcode"


@dataclass
class OneBotConfig:
    """OneBot监听配置"""
    config_path: str  # 配置文件路径
    working_dir: str  # 工作目录
    login_timeout: int = 60  # 登录超时时间(秒)
    # 移除了引擎启动相关配置


class OneBotEngine:
    """OneBot连接监听器"""
    
    def __init__(self, config: OneBotConfig):
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.status_callbacks: list[Callable[[str, Dict[str, Any]], None]] = []
        
        # 登录状态相关
        self.login_status = LoginStatus.UNKNOWN
        self.login_start_time: Optional[float] = None
        self.login_time: Optional[float] = None  # 登录成功时间
        self.qrcode_path: Optional[str] = None
        self.bot_info: Dict[str, Any] = {}
        self.output_buffer: list[str] = []
        self.max_buffer_size = 1000  # 最大缓冲区大小
        
        # 启动监听
        self._start_monitoring()
        
    def add_status_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """添加状态回调函数"""
        self.status_callbacks.append(callback)
        
    def remove_status_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """移除状态回调函数"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
            
    def _notify_status(self, status: str, data: Dict[str, Any] = None):
        """通知状态变化"""
        if data is None:
            data = {}
        
        for callback in self.status_callbacks:
            try:
                callback(status, data)
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")
                
    def _validate_config(self) -> bool:
        """验证配置"""
        if not os.path.exists(self.config.config_path):
            self.logger.error(f"OneBot配置文件不存在: {self.config.config_path}")
            return False
            
        if not os.path.exists(self.config.working_dir):
            self.logger.error(f"OneBot工作目录不存在: {self.config.working_dir}")
            return False
            
        return True
        
    def _read_config_file(self) -> Dict[str, Any]:
        """读取OneBot配置文件"""
        try:
            with open(self.config.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"读取OneBot配置文件失败: {e}")
            return {}
            
    def _write_config_file(self, config_data: Dict[str, Any]):
        """写入OneBot配置文件"""
        try:
            with open(self.config.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
            self.logger.info("OneBot配置文件已更新")
        except Exception as e:
            self.logger.error(f"写入OneBot配置文件失败: {e}")
            
    def update_config(self, updates: Dict[str, Any]):
        """更新OneBot配置"""
        config_data = self._read_config_file()
        
        # 深度合并配置
        def deep_merge(base: dict, updates: dict):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
                    
        deep_merge(config_data, updates)
        self._write_config_file(config_data)
        
    def _start_monitoring(self):
        """启动OneBot连接监听器"""
        self.logger.info("OneBot连接监听器已启动，等待外部引擎连接...")
        self.login_status = LoginStatus.UNKNOWN
        self._notify_status("monitoring_started", {
            "message": "OneBot监听器已启动，等待外部引擎连接"
        })
        
    # 进程监控方法已移除 - 改为监听模式
                
    def get_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "login_status": self.login_status.value,
            "bot_info": self.bot_info,
            "login_time": self.login_time,
            "config": {
                "working_dir": self.config.working_dir,
                "config_path": self.config.config_path
            }
        }
        
    def is_connected(self) -> bool:
        """检查是否已连接到OneBot"""
        return self.login_status == LoginStatus.LOGGED_IN
        
    # 输出读取方法已移除 - 改为监听模式
    
    def simulate_external_connection(self, status_data: Dict[str, Any]):
        """模拟外部OneBot引擎连接（用于测试或接收外部状态）"""
        if "login_status" in status_data:
            old_status = self.login_status
            self.login_status = LoginStatus(status_data["login_status"])
            
            if old_status != self.login_status:
                self.logger.info(f"OneBot状态变更: {old_status.value} -> {self.login_status.value}")
                
                if self.login_status == LoginStatus.LOGGED_IN:
                    self.login_time = time.time()
                elif self.login_status == LoginStatus.DISCONNECTED:
                    self.login_time = None
                    
                self._notify_status("status_changed", {
                    "old_status": old_status.value,
                    "new_status": self.login_status.value
                })
        
        if "bot_info" in status_data:
            self.bot_info.update(status_data["bot_info"])
            
        if "qrcode_path" in status_data:
            self.qrcode_path = status_data["qrcode_path"]
            
        # 添加到输出缓冲区以保持兼容性
        if "log_line" in status_data:
            self._add_to_buffer(status_data["log_line"])
    
    def _add_to_buffer(self, line: str):
        """添加日志行到缓冲区"""
        self.output_buffer.append(line)
        if len(self.output_buffer) > self.max_buffer_size:
            self.output_buffer.pop(0)
            return
        """处理单行输出（已简化为监听模式）"""
        # 此方法已简化，实际状态更新通过 simulate_external_connection 方法进行
        pass
            
    def get_login_status(self) -> LoginStatus:
        """获取登录状态"""
        return self.login_status
        
    def get_bot_info(self) -> Dict[str, Any]:
        """获取机器人信息"""
        return self.bot_info.copy()
        
    def get_qrcode_path(self) -> Optional[str]:
        """获取二维码路径"""
        return self.qrcode_path
        
    def get_recent_logs(self, lines: int = 50) -> list[str]:
        """获取最近的日志"""
        return self.output_buffer[-lines:] if self.output_buffer else []
        
    def get_engine_logs(self, lines: int = 50) -> tuple[list[str], list[str]]:
        """获取引擎日志（保持兼容性）"""
        recent_logs = self.get_recent_logs(lines)
        return recent_logs, []  # stderr已合并到stdout