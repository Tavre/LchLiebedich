#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OneBot引擎启动器
简化的启动器，直接启动OneBot引擎和词库管理功能
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.onebot_engine import OneBotEngine, OneBotConfig
from src.core.bot import OneBotFramework
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.config.settings import load_config
from src.wordlib.manager import LchliebedichWordLibManager

def main():
    """主程序入口"""
    # 设置日志
    logger = setup_logger(level="DEBUG")
    logger.info("OneBot引擎启动器启动")
    
    onebot_engine = None
    wordlib_manager = None
    
    try:
        # 加载配置
        config = load_config()
        logger.info("配置加载完成")
        
        # 创建OneBot框架（用于处理消息和API调用）
        onebot_framework = OneBotFramework(config)
        
        # 创建lchliebedich词库管理器
        wordlib_manager = LchliebedichWordLibManager(onebot_framework, config)
        logger.info("lchliebedich词库管理器初始化完成")
        
        # 创建OneBot连接监听器
        engine_config = OneBotConfig(
            config_path=os.path.join(project_root, config.onebot_engine.config_path),
            working_dir=os.path.join(project_root, config.onebot_engine.working_dir),
            login_timeout=config.onebot_engine.login_timeout
        )
        
        onebot_engine = OneBotEngine(engine_config)
        
        # 添加状态回调
        def on_engine_status(status: str, data: dict):
            if status == "monitoring_started":
                logger.info("OneBot连接监听器已启动")
            elif status == "status_changed":
                logger.info(f"OneBot状态变更: {data.get('old_status')} -> {data.get('new_status')}")
            elif status == "login_success":
                logger.info("OneBot引擎登录成功")
            elif status == "login_failed":
                logger.warning("OneBot引擎登录失败")
            elif status == "disconnected":
                logger.warning("OneBot引擎连接断开")
                
        onebot_engine.add_status_callback(on_engine_status)
        
        # OneBot连接监听器已创建，等待外部引擎连接
        logger.info("OneBot连接监听器已准备就绪，等待外部引擎连接")
        
        # 启动OneBot框架
        import asyncio
        import threading
        
        def start_onebot_framework():
            """在新线程中启动OneBot框架"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 创建任务并运行事件循环
                task = loop.create_task(onebot_framework.start())
                loop.run_forever()
            except Exception as e:
                logger.error(f"OneBot框架启动失败: {e}")
            finally:
                loop.close()
        
        # 在后台线程启动OneBot框架
        framework_thread = threading.Thread(target=start_onebot_framework, daemon=True)
        framework_thread.start()
        logger.info("OneBot框架已启动")
        
        # 创建GUI
        root = tk.Tk()
        app = MainWindow(root, wordlib_manager, onebot_engine, onebot_framework)
        
        # 设置窗口关闭事件
        def on_closing():
            logger.info("正在关闭程序...")
            if onebot_engine:
                logger.info("正在停止OneBot监听器...")
                # OneBot引擎现在是监听器模式，无需手动停止
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 启动GUI
        logger.info("启动GUI界面")
        root.mainloop()
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        messagebox.showerror("错误", f"程序启动失败: {e}")
        
        # 确保OneBot引擎被停止
        if onebot_engine and onebot_engine.is_running:
            onebot_engine.stop()
            
        sys.exit(1)

if __name__ == "__main__":
    main()