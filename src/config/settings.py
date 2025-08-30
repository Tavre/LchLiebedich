#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
支持YAML和TOML格式的配置文件
"""

import os
import yaml
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from loguru import logger

class OneBotConfig(BaseModel):
    """OneBot配置"""
    host: str = Field(default="127.0.0.1", description="OneBot WebSocket反向连接地址")
    port: int = Field(default=8028, description="OneBot WebSocket反向连接端口")
    path: str = Field(default="/onebot/v11/ws", description="WebSocket路径")
    access_token: Optional[str] = Field(default=None, description="访问令牌")
    secret: Optional[str] = Field(default=None, description="签名密钥")
    timeout: int = Field(default=30, description="请求超时时间")
    retry_count: int = Field(default=3, description="重试次数")
    retry_interval: int = Field(default=5, description="重试间隔(秒)")
    heartbeat_interval: int = Field(default=5000, description="心跳间隔(毫秒)")
    reconnect_interval: int = Field(default=5000, description="重连间隔(毫秒)")

class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8080, description="服务器监听端口")
    debug: bool = Field(default=False, description="调试模式")
    workers: int = Field(default=1, description="工作线程数")

class StorageConfig(BaseModel):
    """存储配置"""
    type: str = Field(default="json", description="存储类型")
    data_dir: str = Field(default="data", description="数据目录")
    auto_backup: bool = Field(default=True, description="是否启用自动备份")
    backup_interval: int = Field(default=24, description="备份间隔(小时)")

class LogConfig(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    file: str = Field(default="logs/bot.log", description="日志文件路径")
    max_size: str = Field(default="10 MB", description="单个日志文件最大大小")
    retention: str = Field(default="7 days", description="日志保留时间")
    rotation: str = Field(default="1 day", description="日志轮转间隔")
    console: bool = Field(default=True, description="是否输出到控制台")

class WordLibConfig(BaseModel):
    """词库配置"""
    path: str = Field(default="data/wordlib", description="词库文件夹路径")
    json_storage_path: str = Field(default="data/wordlib.json", description="词库数据文件路径")
    encoding: str = Field(default="utf-8", description="词库文件编码")
    auto_reload: bool = Field(default=True, description="是否启用文件监控")
    enable_pseudocode: bool = Field(default=True, description="是否启用伪代码处理")
    default_match_type: str = Field(default="exact", description="默认匹配类型")
    case_sensitive: bool = Field(default=False, description="是否区分大小写")
    max_reply_length: int = Field(default=1000, description="最大回复长度")
    cache_size: int = Field(default=1000, description="缓存大小")

class OneBotEngineConfig(BaseModel):
    """OneBot监听配置"""
    config_path: str = Field(default="engine/appsettings.json", description="OneBot引擎配置文件路径")
    working_dir: str = Field(default="engine", description="OneBot引擎工作目录")
    login_timeout: int = Field(default=60, description="登录超时时间(秒)")

class BotConfig(BaseModel):
    """机器人总配置"""
    onebot: OneBotConfig = Field(default_factory=OneBotConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    wordlib: WordLibConfig = Field(default_factory=WordLibConfig)
    onebot_engine: OneBotEngineConfig = Field(default_factory=OneBotEngineConfig)
    
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[BotConfig] = None
        
    def load_config(self) -> BotConfig:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"配置文件 {self.config_path} 不存在，创建默认配置")
            self.config = BotConfig()
            self.save_config()
            return self.config
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    data = yaml.safe_load(f)
                elif self.config_path.suffix.lower() == '.toml':
                    data = toml.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")
                    
            self.config = BotConfig(**data)
            logger.info(f"配置文件 {self.config_path} 加载成功")
            return self.config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
            self.config = BotConfig()
            return self.config
            
    def save_config(self) -> None:
        """保存配置文件"""
        if self.config is None:
            return
            
        try:
            # 确保配置文件目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    yaml.dump(self.config.model_dump(), f, default_flow_style=False, allow_unicode=True, indent=2)
                elif self.config_path.suffix.lower() == '.toml':
                    toml.dump(self.config.model_dump(), f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {self.config_path.suffix}")
                    
            logger.info(f"配置文件 {self.config_path} 保存成功")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            
    def update_config(self, **kwargs) -> None:
        """更新配置"""
        if self.config is None:
            self.config = BotConfig()
            
        # 更新配置字段
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
        self.save_config()
        
    def get_config(self) -> BotConfig:
        """获取配置"""
        if self.config is None:
            return self.load_config()
        return self.config

# 全局配置管理器实例
_config_manager = ConfigManager()

def load_config(config_path: str = "config.yaml") -> BotConfig:
    """加载配置"""
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager.load_config()

def get_config() -> BotConfig:
    """获取当前配置"""
    return _config_manager.get_config()

def save_config() -> None:
    """保存配置"""
    _config_manager.save_config()

def update_config(**kwargs) -> None:
    """更新配置"""
    _config_manager.update_config(**kwargs)