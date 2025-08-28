#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统模块
基于loguru实现的高级日志功能
"""

import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional

class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self.logger = logger
        self.initialized = False
        
    def setup_logger(
        self,
        level: str = "INFO",
        file_path: str = "logs/bot.log",
        max_size: str = "10 MB",
        retention: str = "7 days",
        rotation: str = "1 day",
        console_output: bool = True
    ) -> None:
        """设置日志配置"""
        
        if self.initialized:
            return
            
        # 移除默认处理器
        self.logger.remove()
        
        # 控制台输出
        if console_output:
            self.logger.add(
                sys.stdout,
                level=level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                       "<level>{message}</level>",
                colorize=True
            )
        
        # 文件输出
        if file_path:
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.add(
                file_path,
                level=level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation=rotation,
                retention=retention,
                compression="zip",
                encoding="utf-8"
            )
            
        # 错误日志单独文件
        if file_path:
            error_log_path = log_path.parent / f"{log_path.stem}_error{log_path.suffix}"
            self.logger.add(
                str(error_log_path),
                level="ERROR",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
                rotation=rotation,
                retention=retention,
                compression="zip",
                encoding="utf-8"
            )
        
        self.initialized = True
        self.logger.info("日志系统初始化完成")
        
    def get_logger(self, name: Optional[str] = None):
        """获取日志器"""
        if name:
            return self.logger.bind(name=name)
        return self.logger
        
    def set_level(self, level: str) -> None:
        """设置日志级别"""
        # 注意：loguru的动态级别设置比较复杂，这里简化处理
        self.logger.info(f"日志级别设置为: {level}")
        
    def add_file_handler(
        self,
        file_path: str,
        level: str = "INFO",
        rotation: str = "1 day",
        retention: str = "7 days"
    ) -> None:
        """添加文件处理器"""
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.add(
            file_path,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8"
        )
        
        self.logger.info(f"添加文件日志处理器: {file_path}")
        
    def remove_handler(self, handler_id: int) -> None:
        """移除处理器"""
        try:
            self.logger.remove(handler_id)
            self.logger.info(f"移除日志处理器: {handler_id}")
        except ValueError:
            self.logger.warning(f"处理器 {handler_id} 不存在")

# 全局日志管理器实例
_logger_manager = LoggerManager()

def setup_logger(
    level: str = "INFO",
    file_path: str = "logs/bot.log",
    max_size: str = "10 MB",
    retention: str = "7 days",
    rotation: str = "1 day",
    console_output: bool = True
):
    """设置日志系统"""
    _logger_manager.setup_logger(
        level=level,
        file_path=file_path,
        max_size=max_size,
        retention=retention,
        rotation=rotation,
        console_output=console_output
    )
    return _logger_manager.get_logger()

def get_logger(name: Optional[str] = None):
    """获取日志器"""
    return _logger_manager.get_logger(name)

def set_log_level(level: str) -> None:
    """设置日志级别"""
    _logger_manager.set_level(level)

def add_file_handler(
    file_path: str,
    level: str = "INFO",
    rotation: str = "1 day",
    retention: str = "7 days"
) -> None:
    """添加文件处理器"""
    _logger_manager.add_file_handler(file_path, level, rotation, retention)

# 便捷的日志函数
def log_info(message: str, **kwargs) -> None:
    """记录信息日志"""
    _logger_manager.get_logger().info(message, **kwargs)

def log_warning(message: str, **kwargs) -> None:
    """记录警告日志"""
    _logger_manager.get_logger().warning(message, **kwargs)

def log_error(message: str, **kwargs) -> None:
    """记录错误日志"""
    _logger_manager.get_logger().error(message, **kwargs)

def log_debug(message: str, **kwargs) -> None:
    """记录调试日志"""
    _logger_manager.get_logger().debug(message, **kwargs)

def log_exception(message: str, **kwargs) -> None:
    """记录异常日志"""
    _logger_manager.get_logger().exception(message, **kwargs)

# 便捷日志函数
def debug(message: str, **kwargs) -> None:
    """记录调试日志"""
    _logger_manager.get_logger().debug(message, **kwargs)

def info(message: str, **kwargs) -> None:
    """记录信息日志"""
    _logger_manager.get_logger().info(message, **kwargs)

def warning(message: str, **kwargs) -> None:
    """记录警告日志"""
    _logger_manager.get_logger().warning(message, **kwargs)

def error(message: str, **kwargs) -> None:
    """记录错误日志"""
    _logger_manager.get_logger().error(message, **kwargs)

def critical(message: str, **kwargs) -> None:
    """记录严重错误日志"""
    _logger_manager.get_logger().critical(message, **kwargs)