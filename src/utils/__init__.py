#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
提供机器人框架的通用工具函数
"""

from .logger import (
    LoggerManager,
    setup_logger,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical
)

__all__ = [
    'LoggerManager',
    'setup_logger',
    'get_logger',
    'debug',
    'info',
    'warning',
    'error',
    'critical'
]