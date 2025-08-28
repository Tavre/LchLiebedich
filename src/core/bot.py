#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneBot V11 机器人核心模块
实现OneBot V11协议的通信和消息处理
"""

import asyncio
import json

import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

import websockets
from loguru import logger
import threading
from queue import Queue

from ..wordlib.manager import LchliebedichWordLibManager
from ..utils.logger import get_logger

@dataclass
class OneBotEvent:
    """OneBot事件"""
    time: int
    self_id: int
    post_type: str
    raw_data: Dict[str, Any]
    
@dataclass
class MessageEvent(OneBotEvent):
    """消息事件"""
    message_type: str  # private, group
    sub_type: str
    message_id: int
    user_id: int
    message: str
    raw_message: str
    sender: Dict[str, Any]
    group_id: Optional[int] = None

class OneBotAPI:
    """OneBot API客户端"""
    
    def __init__(self, config, server=None):
        self.config = config
        self.server = server
            
    async def send_private_msg(self, user_id: int, message: str, auto_escape: bool = False) -> Dict[str, Any]:
        """发送私聊消息"""
        if self.server and hasattr(self.server, 'send_websocket_message'):
            result = await self.server.send_websocket_message("send_private_msg", {
                "user_id": user_id,
                "message": message,
                "auto_escape": auto_escape
            })
            if result:
                return result
        
        logger.error("无法发送私聊消息: 没有可用的WebSocket连接")
        return {}
        
    async def send_group_msg(self, group_id: int, message: str, auto_escape: bool = False) -> Dict[str, Any]:
        """发送群消息"""
        if self.server and hasattr(self.server, 'send_websocket_message'):
            result = await self.server.send_websocket_message("send_group_msg", {
                "group_id": group_id,
                "message": message,
                "auto_escape": auto_escape
            })
            if result:
                return result
        
        logger.error("无法发送群消息: 没有可用的WebSocket连接")
        return {}
        
    async def send_msg(self, message_type: str, target_id: int, message: str, **kwargs) -> Dict[str, Any]:
        """发送消息（通用）"""
        if message_type == "private":
            return await self.send_private_msg(target_id, message, **kwargs)
        elif message_type == "group":
            return await self.send_group_msg(target_id, message, **kwargs)
        else:
            logger.error(f"不支持的消息类型: {message_type}")
            return {}
            
    async def get_login_info(self) -> Dict[str, Any]:
        """获取登录号信息"""
        if self.server and hasattr(self.server, 'send_websocket_message'):
            result = await self.server.send_websocket_message("get_login_info", {})
            if result:
                return result
        
        logger.error("无法获取登录信息: 没有可用的WebSocket连接")
        return {}
        
    async def get_stranger_info(self, user_id: int, no_cache: bool = False) -> Dict[str, Any]:
        """获取陌生人信息"""
        if self.server and hasattr(self.server, 'send_websocket_message'):
            result = await self.server.send_websocket_message("get_stranger_info", {
                "user_id": user_id,
                "no_cache": no_cache
            })
            if result:
                return result
        
        logger.error("无法获取陌生人信息: 没有可用的WebSocket连接")
        return {}
        
    async def get_group_info(self, group_id: int, no_cache: bool = False) -> Dict[str, Any]:
        """获取群信息"""
        if self.server and hasattr(self.server, 'send_websocket_message'):
            result = await self.server.send_websocket_message("get_group_info", {
                "group_id": group_id,
                "no_cache": no_cache
            })
            if result:
                return result
        
        logger.error("无法获取群信息: 没有可用的WebSocket连接")
        return {}
        
    async def get_group_member_info(self, group_id: int, user_id: int, no_cache: bool = False) -> Dict[str, Any]:
        """获取群成员信息"""
        if self.server and hasattr(self.server, 'send_websocket_message'):
            result = await self.server.send_websocket_message("get_group_member_info", {
                "group_id": group_id,
                "user_id": user_id,
                "no_cache": no_cache
            })
            if result:
                return result
        
        logger.error("无法获取群成员信息: 没有可用的WebSocket连接")
        return {}

class OneBotServer:
    """OneBot WebSocket服务器"""
    
    def __init__(self, config, event_handler):
        self.config = config
        self.event_handler = event_handler
        self.app = FastAPI(title="OneBot V11 Framework")
        self.websocket_connection = None
        self.setup_routes()
    
    async def send_websocket_message(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过WebSocket发送消息"""
        if not self.websocket_connection:
            logger.error("[OneBot] WebSocket连接不可用")
            return None
            
        try:
            message = {
                "action": action,
                "params": params,
                "echo": str(int(time.time() * 1000))
            }
            await self.websocket_connection.send_text(json.dumps(message))
            logger.debug(f"[OneBot] 发送WebSocket消息: {message}")
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"[OneBot] WebSocket发送消息失败: {e}")
            return None
        
    def setup_routes(self):
        """设置路由"""
            
        @self.app.websocket("/onebot/v11/ws")
        async def websocket_onebot(websocket: WebSocket):
            """OneBot v11 WebSocket端点"""
            logger.info(f"[OneBot] 收到OneBot WebSocket连接请求: {websocket.client}")
            logger.info(f"[OneBot] WebSocket headers: {dict(websocket.headers)}")
            logger.info(f"[OneBot] WebSocket query params: {dict(websocket.query_params)}")
            logger.info(f"[OneBot] WebSocket scope: {websocket.scope.get('path', 'unknown')}")
            try:
                # 检查是否请求了onebot子协议
                subprotocol = None
                if "sec-websocket-protocol" in websocket.headers:
                    protocols = websocket.headers["sec-websocket-protocol"].split(", ")
                    logger.info(f"[OneBot] 请求的子协议: {protocols}")
                    if "onebot" in protocols:
                        subprotocol = "onebot"
                        logger.info(f"[OneBot] 使用onebot子协议")
                
                logger.info(f"[OneBot] 准备接受WebSocket连接，子协议: {subprotocol}")
                await websocket.accept(subprotocol=subprotocol)
                logger.info(f"[OneBot] OneBot WebSocket连接已建立: {websocket.client}, 子协议: {subprotocol}")
                
                # 保存WebSocket连接
                self.websocket_connection = websocket
                
                while True:
                    # 接收消息
                    data = await websocket.receive_json()
                    
                    # 检查是否为API请求
                    if "action" in data:
                        # 处理API请求
                        action = data.get("action")
                        params = data.get("params", {})
                        echo = data.get("echo")
                        
                        logger.info(f"[OneBot] 收到API请求 - 动作:{action} 参数:{params}")
                        
                        # 处理API请求
                        try:
                            if action == "get_login_info":
                                result = {"user_id": 123456, "nickname": "测试机器人"}
                                response = {
                                    "status": "ok",
                                    "retcode": 0,
                                    "data": result,
                                    "echo": echo
                                }
                            elif action == "send_private_msg":
                                user_id = params.get("user_id")
                                message = params.get("message")
                                # 这里应该调用实际的发送消息逻辑
                                response = {
                                    "status": "ok",
                                    "retcode": 0,
                                    "data": {"message_id": 12345},
                                    "echo": echo
                                }
                            elif action == "send_group_msg":
                                group_id = params.get("group_id")
                                message = params.get("message")
                                # 这里应该调用实际的发送消息逻辑
                                response = {
                                    "status": "ok",
                                    "retcode": 0,
                                    "data": {"message_id": 12345},
                                    "echo": echo
                                }
                            else:
                                # 不支持的API
                                response = {
                                    "status": "failed",
                                    "retcode": -1,
                                    "data": None,
                                    "echo": echo
                                }
                        except Exception as e:
                            logger.error(f"[OneBot] API请求处理失败: {e}")
                            response = {
                                "status": "failed",
                                "retcode": -1,
                                "data": None,
                                "echo": echo
                            }
                        
                        # 发送API响应
                        await websocket.send_json(response)
                        logger.info(f"[OneBot] 发送API响应: {response}")
                        
                    else:
                        # 处理OneBot事件
                        post_type = data.get("post_type", "unknown")
                        if post_type == "message":
                            message_type = data.get("message_type", "unknown")
                            user_id = data.get("user_id", "unknown")
                            group_id = data.get("group_id", "")
                            message = data.get("message", "")
                            if message_type == "private":
                                logger.info(f"[OneBot] 收到私聊消息 - 用户:{user_id} 内容:{message}")
                            elif message_type == "group":
                                logger.info(f"[OneBot] 收到群聊消息 - 群:{group_id} 用户:{user_id} 内容:{message}")
                            else:
                                logger.info(f"[OneBot] 收到消息事件: {data}")
                        elif post_type == "notice":
                            notice_type = data.get("notice_type", "unknown")
                            logger.info(f"[OneBot] 收到通知事件 - 类型:{notice_type}")
                        elif post_type == "request":
                            request_type = data.get("request_type", "unknown")
                            logger.info(f"[OneBot] 收到请求事件 - 类型:{request_type}")
                        elif post_type == "meta_event":
                            meta_event_type = data.get("meta_event_type", "unknown")
                            if meta_event_type == "heartbeat":
                                logger.debug(f"[OneBot] 收到心跳事件")
                            else:
                                logger.info(f"[OneBot] 收到元事件 - 类型:{meta_event_type}")
                        else:
                            logger.info(f"[OneBot] 收到未知事件: {data}")
                        
                        # 处理事件
                        response = await self.event_handler(data)
                        
                        # 发送响应（如果有）
                        if response:
                            await websocket.send_json(response)
                            logger.info(f"[OneBot] 发送响应: {response}")
                        
            except WebSocketDisconnect:
                logger.info("OneBot WebSocket连接已断开")
            except Exception as e:
                logger.error(f"OneBot WebSocket连接错误: {e}")
                import traceback
                logger.error(f"OneBot WebSocket错误详情: {traceback.format_exc()}")
            finally:
                # 清除WebSocket连接
                self.websocket_connection = None
                logger.info("OneBot WebSocket连接已断开")
                
        @self.app.websocket("/")
        async def websocket_root(websocket: WebSocket):
            """WebSocket连接处理"""
            logger.info(f"[OneBot] 收到WebSocket连接请求: {websocket.client}")
            try:
                await websocket.accept()
                self.websocket_connection = websocket
                logger.info(f"[OneBot] WebSocket连接已建立: {websocket.client}")
                
                while True:
                    # 接收消息
                    data = await websocket.receive_json()
                    
                    # 根据消息类型记录不同级别的日志
                    post_type = data.get("post_type", "unknown")
                    if post_type == "message":
                        message_type = data.get("message_type", "unknown")
                        user_id = data.get("user_id", "unknown")
                        group_id = data.get("group_id", "")
                        message = data.get("message", "")
                        if message_type == "private":
                            logger.info(f"[OneBot] 收到私聊消息 - 用户:{user_id} 内容:{message}")
                        elif message_type == "group":
                            logger.info(f"[OneBot] 收到群聊消息 - 群:{group_id} 用户:{user_id} 内容:{message}")
                        else:
                            logger.info(f"[OneBot] 收到消息事件: {data}")
                    elif post_type == "notice":
                        notice_type = data.get("notice_type", "unknown")
                        logger.info(f"[OneBot] 收到通知事件 - 类型:{notice_type}")
                    elif post_type == "request":
                        request_type = data.get("request_type", "unknown")
                        logger.info(f"[OneBot] 收到请求事件 - 类型:{request_type}")
                    elif post_type == "meta_event":
                        meta_event_type = data.get("meta_event_type", "unknown")
                        if meta_event_type == "heartbeat":
                            logger.debug(f"[OneBot] 收到心跳事件")
                        else:
                            logger.info(f"[OneBot] 收到元事件 - 类型:{meta_event_type}")
                    else:
                        logger.info(f"[OneBot] 收到未知事件: {data}")
                    
                    # 处理事件
                    response = await self.event_handler(data)
                    
                    # 发送响应（如果有）
                    if response:
                        await websocket.send_json(response)
                        logger.info(f"[OneBot] 发送响应: {response}")
                        
            except WebSocketDisconnect:
                logger.info("WebSocket连接已断开")
            except Exception as e:
                logger.error(f"WebSocket连接错误: {e}")
                import traceback
                logger.error(f"WebSocket错误详情: {traceback.format_exc()}")
            finally:
                self.websocket_connection = None
                logger.info("WebSocket连接已断开")
            
    async def start(self):
        """启动服务器"""
        logger.info(f"正在启动WebSocket服务器，监听 {self.config.server.host}:{self.config.server.port}")
        config = uvicorn.Config(
            self.app,
            host=self.config.server.host,
            port=self.config.server.port,
            log_level="debug",
            access_log=True,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "root": {
                    "level": "DEBUG",
                    "handlers": ["default"],
                },
            }
        )
        server = uvicorn.Server(config)
        logger.info("HTTP服务器配置完成，开始启动...")
        try:
            # 在后台启动服务器
            import asyncio
            task = asyncio.create_task(server.serve())
            # 等待服务器启动
            await asyncio.sleep(1)
            logger.info(f"HTTP服务器已启动，监听 {self.config.server.host}:{self.config.server.port}")
            return task
        except Exception as e:
            logger.error(f"HTTP服务器启动失败: {e}")
            raise

class MessageHandler:
    """消息处理器"""
    
    def __init__(self, wordlib_manager: LchliebedichWordLibManager):
        self.wordlib_manager = wordlib_manager
        self.handlers: List[Callable] = []
        self.recent_messages: List[Dict[str, Any]] = []
        
    def add_handler(self, handler: Callable):
        """添加消息处理器"""
        self.handlers.append(handler)
        
    def remove_handler(self, handler: Callable):
        """移除消息处理器"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            
    async def handle_message(self, event: MessageEvent) -> Optional[str]:
        """处理消息"""
        # 保存消息到最近消息列表
        message_data = {
            "message_type": event.message_type,
            "user_id": event.user_id,
            "group_id": event.group_id,
            "raw_message": event.raw_message,
            "time": event.time
        }
        self.recent_messages.append(message_data)
        
        # 限制最近消息数量，避免内存泄漏
        if len(self.recent_messages) > 100:
            self.recent_messages = self.recent_messages[-50:]
        
        # 确保message是字符串类型
        if isinstance(event.message, list):
            # 如果是列表，提取文本内容
            message_parts = []
            for part in event.message:
                if isinstance(part, dict) and part.get('type') == 'text':
                    message_parts.append(part.get('data', {}).get('text', ''))
                elif isinstance(part, str):
                    message_parts.append(part)
            message = ''.join(message_parts).strip()
        elif isinstance(event.message, str):
            message = event.message.strip()
        else:
            message = str(event.message).strip()
        
        # 构建完整的OneBot上下文（兼容lchliebedich变量系统）
        context = {
            # 基础信息
            "self_id": event.self_id,
            "user_id": event.user_id,
            "group_id": event.group_id,
            "message_id": event.message_id,
            "message_type": event.message_type,
            "sub_type": event.sub_type,
            "time": event.time,
            
            # 消息内容
            "message": event.message,
            "raw_message": event.raw_message,
            
            # 发送者信息
            "sender": event.sender,
            
            # 原始数据
            "raw_data": event.raw_data,
            
            # 兼容性字段
            "user_name": event.sender.get("nickname", "用户"),
            "nickname": event.sender.get("nickname", "用户")  # 添加nickname字段支持%昵称%变量
        }
        
        # 首先尝试词库匹配
        response = self.wordlib_manager.find_response(message, context)
        if response:
            return response
            
        # 调用自定义处理器
        for handler in self.handlers:
            try:
                result = await handler(event)
                if result:
                    return result
            except Exception as e:
                logger.error(f"处理器执行失败: {e}")
                
        return None

class OneBotFramework:
    """OneBot V11 机器人框架"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger("OneBotFramework")
        
        # 初始化组件
        self.wordlib_manager = LchliebedichWordLibManager(self, self.config)
        self.message_handler = MessageHandler(self.wordlib_manager)
        self.server = OneBotServer(config, self._handle_event)
        self.api = OneBotAPI(config, self.server)
        
        # 状态
        self.running = False
        self.bot_info = {}
        self.event_queue = Queue()
        
        # 统计信息
        self.stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "start_time": int(time.time())
        }
        
    async def _handle_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理OneBot事件"""
        try:
            post_type = data.get("post_type")
            
            if post_type == "message":
                return await self._handle_message_event(data)
            elif post_type == "notice":
                return await self._handle_notice_event(data)
            elif post_type == "request":
                return await self._handle_request_event(data)
            elif post_type == "meta_event":
                return await self._handle_meta_event(data)
            else:
                self.logger.warning(f"[OneBot] 未知事件类型: {post_type}")
                
        except Exception as e:
            self.logger.error(f"[OneBot] 处理事件失败: {e}")
            
        return None
        
    async def _handle_message_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息事件"""
        try:
            message_type = data.get("message_type")
            user_id = data.get("user_id")
            group_id = data.get("group_id")
            message = data.get("message", "")
            
            # 记录消息处理日志
            if message_type == "private":
                self.logger.info(f"[OneBot] 开始处理私聊消息 - 用户:{user_id}")
            elif message_type == "group":
                self.logger.info(f"[OneBot] 开始处理群聊消息 - 群:{group_id} 用户:{user_id}")
            
            # 创建消息事件对象
            event = MessageEvent(
                time=data.get("time", int(time.time())),
                self_id=data.get("self_id"),
                post_type=data.get("post_type"),
                message_type=message_type,
                sub_type=data.get("sub_type"),
                message_id=data.get("message_id"),
                user_id=user_id,
                message=data.get("message", ""),
                raw_message=data.get("raw_message", ""),
                sender=data.get("sender", {}),
                group_id=data.get("group_id"),
                raw_data=data
            )
            
            self.stats["messages_received"] += 1
            nickname = event.sender.get('nickname', f'用户{event.user_id}')
            self.logger.info(f"[OneBot] 消息内容: {event.message} (发送者: {nickname})")
            
            # 处理消息
            self.logger.debug(f"[OneBot] 开始处理消息: '{message}'")
            response = await self.message_handler.handle_message(event)
            self.logger.debug(f"[OneBot] 消息处理结果: {response}")
            
            if response:
                self.stats["messages_sent"] += 1
                if message_type == "private":
                    self.logger.info(f"[OneBot] 回复私聊消息 - 用户:{user_id} 内容:{response}")
                elif message_type == "group":
                    self.logger.info(f"[OneBot] 回复群聊消息 - 群:{group_id} 用户:{user_id} 内容:{response}")
                
                # 主动发送消息
                try:
                    if message_type == "private":
                        await self.api.send_private_msg(user_id, response)
                    elif message_type == "group":
                        await self.api.send_group_msg(group_id, response)
                    self.logger.debug(f"[OneBot] 消息发送成功")
                except Exception as send_error:
                    self.logger.error(f"[OneBot] 消息发送失败: {send_error}")
                
                return None
            else:
                # 词库中没有匹配的指令，只在日志中记录，不发送消息
                if message_type == "private":
                    self.logger.info(f"[OneBot] 词库无匹配 - 私聊消息 用户:{user_id} 内容:'{message}'")
                elif message_type == "group":
                    self.logger.info(f"[OneBot] 词库无匹配 - 群聊消息 群:{group_id} 用户:{user_id} 内容:'{message}'")
                self.logger.debug(f"[OneBot] 消息处理完成，无需回复")
                
        except Exception as e:
            self.logger.error(f"[OneBot] 处理消息事件失败: {e}")
            
        return None
        
    async def _handle_notice_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理通知事件"""
        notice_type = data.get("notice_type")
        user_id = data.get("user_id")
        group_id = data.get("group_id")
        
        if notice_type == "group_increase":
            self.logger.info(f"[OneBot] 群成员增加 - 群:{group_id} 用户:{user_id}")
        elif notice_type == "group_decrease":
            self.logger.info(f"[OneBot] 群成员减少 - 群:{group_id} 用户:{user_id}")
        elif notice_type == "friend_add":
            self.logger.info(f"[OneBot] 好友添加 - 用户:{user_id}")
        else:
            self.logger.info(f"[OneBot] 收到通知事件 - 类型:{notice_type}")
        return None
        
    async def _handle_request_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理请求事件"""
        request_type = data.get("request_type")
        user_id = data.get("user_id")
        group_id = data.get("group_id")
        comment = data.get("comment", "")
        
        if request_type == "friend":
            self.logger.info(f"[OneBot] 好友请求 - 用户:{user_id} 验证消息:{comment}")
        elif request_type == "group":
            self.logger.info(f"[OneBot] 群请求 - 群:{group_id} 用户:{user_id} 验证消息:{comment}")
        else:
            self.logger.info(f"[OneBot] 收到请求事件 - 类型:{request_type}")
        return None
        
    async def _handle_meta_event(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理元事件"""
        meta_event_type = data.get("meta_event_type")
        
        if meta_event_type == "lifecycle":
            sub_type = data.get("sub_type")
            if sub_type == "connect":
                self.logger.info("[OneBot] OneBot连接建立")
                # 获取机器人信息
                try:
                    self.bot_info = await self.api.get_login_info()
                    nickname = self.bot_info.get('nickname', '未知')
                    user_id = self.bot_info.get('user_id', '未知')
                    self.logger.info(f"[OneBot] 机器人信息 - 昵称:{nickname} ID:{user_id}")
                except Exception as e:
                    self.logger.warning(f"[OneBot] 获取机器人信息失败: {e}")
            elif sub_type == "enable":
                self.logger.info("[OneBot] OneBot启用")
            elif sub_type == "disable":
                self.logger.info("[OneBot] OneBot禁用")
        elif meta_event_type == "heartbeat":
            # 心跳事件使用debug级别，避免日志过多
            pass
        else:
            self.logger.info(f"[OneBot] 收到元事件 - 类型:{meta_event_type}")
            
        return None
        
    async def send_message(self, message_type: str, target_id: int, message: str) -> bool:
        """发送消息"""
        try:
            if message_type == "private":
                self.logger.info(f"[OneBot] 发送私聊消息 - 用户:{target_id} 内容:{message}")
            elif message_type == "group":
                self.logger.info(f"[OneBot] 发送群聊消息 - 群:{target_id} 内容:{message}")
            
            result = await self.api.send_msg(message_type, target_id, message)
            if result:
                self.stats["messages_sent"] += 1
                self.logger.info(f"[OneBot] 消息发送成功")
                return True
            else:
                self.logger.warning(f"[OneBot] 消息发送失败")
                return False
        except Exception as e:
            self.logger.error(f"[OneBot] 发送消息异常: {e}")
        return False
        
    def add_message_handler(self, handler: Callable):
        """添加消息处理器"""
        self.message_handler.add_handler(handler)
        
    def remove_message_handler(self, handler: Callable):
        """移除消息处理器"""
        self.message_handler.remove_handler(handler)
        
    async def start(self):
        """启动框架"""
        if self.running:
            return
            
        self.running = True
        self.logger.info("OneBot框架启动中...")
        
        try:
            # 启动HTTP服务器
            self.server_task = await self.server.start()
            self.logger.info("OneBot框架启动完成")
        except Exception as e:
            self.logger.error(f"启动框架失败: {e}")
            self.running = False
            raise
            
    def stop(self):
        """停止框架"""
        if not self.running:
            return
            
        self.running = False
        self.logger.info("OneBot框架停止")
        
        # 停止词库文件监控
        self.wordlib_manager.stop_file_watcher()
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = int(time.time()) - self.stats["start_time"]
        return {
            **self.stats,
            "uptime": uptime,
            "running": self.running,
            "bot_info": self.bot_info,
            "wordlib_count": len(self.wordlib_manager.entries_cache)
        }
        
    def get_wordlib_manager(self) -> LchliebedichWordLibManager:
        """获取词库管理器"""
        return self.wordlib_manager