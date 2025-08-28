#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneBot V11 机器人框架
一个基于OneBot V11协议的Python机器人框架，支持桌面环境和图形化界面
"""

__version__ = "1.0.0"
__author__ = "OneBot Framework Team"
__description__ = "OneBot V11 Python Robot Framework"

# 导入主要模块
from .core import OneBotFramework
from .config import ConfigManager
from .wordlib import LchliebedichWordLibManager
from .utils import get_logger
from .gui import MainWindow

__all__ = [
    'OneBotFramework',
    'ConfigManager',
    'LchliebedichWordLibManager',
    'get_logger',
    'MainWindow'
]