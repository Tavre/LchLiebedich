#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt5配置窗口模块
使用PyQt-SiliconUI主题的配置管理界面
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit,
    QLabel, QPushButton, QListWidget, QSplitter, QGroupBox,
    QGridLayout, QMessageBox, QFileDialog, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QFormLayout, QScrollArea,
    QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from siui.components import SiDenseHContainer, SiDenseVContainer
from siui.components.widgets import SiLabel, SiPushButton, SiLineEdit, SiCheckBox
from siui.templates.application.application import SiliconApplication

import json
import re
from typing import Dict, Any, List, Tuple

from ..config.settings import ConfigManager
from ..utils.logger import get_logger

class ConfigWindowQt(SiliconApplication):
    """PyQt5配置窗口类"""
    
    def __init__(self, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        
        self.config_manager = config_manager or ConfigManager()
        self.logger = get_logger("ConfigWindowQt")
        
        # 配置数据
        self.config_data = {}
        self.config_widgets = {}
        self.validation_errors = {}
        
        # 配置验证规则
        self.validation_rules = {
            'app.name': {'type': str, 'required': True, 'min_length': 1, 'max_length': 50},
            'app.version': {'type': str, 'required': True, 'pattern': r'^\d+\.\d+\.\d+$'},
            'onebot.host': {'type': str, 'required': True, 'pattern': r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$|^localhost$'},
            'onebot.port': {'type': int, 'required': True, 'min': 1, 'max': 65535},
            'onebot.access_token': {'type': str, 'required': False, 'min_length': 0, 'max_length': 100},
            'wordlib.auto_reload': {'type': bool, 'required': True},
            'wordlib.max_size': {'type': int, 'required': True, 'min': 1, 'max': 1000000},
            'logging.level': {'type': str, 'required': True, 'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR']},
            'logging.max_files': {'type': int, 'required': True, 'min': 1, 'max': 100}
        }
        
        self.setup_ui()
        self.load_config()
        self.setup_validation()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("配置管理器")
        self.resize(800, 600)
        
        # 创建主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 主布局
        main_layout = QVBoxLayout(main_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个配置页面
        self.setup_general_tab()
        self.setup_onebot_tab()
        self.setup_wordlib_tab()
        self.setup_logging_tab()
        self.setup_advanced_tab()
        
        # 操作按钮
        self.setup_buttons(main_layout)
        
    def setup_general_tab(self):
        """设置常规配置页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # 应用程序设置
        app_group = QGroupBox("应用程序设置")
        app_layout = QFormLayout(app_group)
        
        # 应用名称
        self.app_name_edit = SiLineEdit()
        app_layout.addRow("应用名称:", self.app_name_edit)
        self.config_widgets['app.name'] = self.app_name_edit
        
        # 版本
        self.app_version_edit = SiLineEdit()
        app_layout.addRow("版本:", self.app_version_edit)
        self.config_widgets['app.version'] = self.app_version_edit
        
        # 调试模式
        self.debug_mode_check = SiCheckBox("启用调试模式")
        app_layout.addRow(self.debug_mode_check)
        self.config_widgets['app.debug'] = self.debug_mode_check
        
        scroll_layout.addWidget(app_group)
        
        # 界面设置
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)
        
        # 主题
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "深色", "浅色"])
        ui_layout.addRow("主题:", self.theme_combo)
        self.config_widgets['ui.theme'] = self.theme_combo
        
        # 语言
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        ui_layout.addRow("语言:", self.language_combo)
        self.config_widgets['ui.language'] = self.language_combo
        
        scroll_layout.addWidget(ui_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "常规")
        
    def setup_onebot_tab(self):
        """设置OneBot配置页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # OneBot引擎设置
        engine_group = QGroupBox("OneBot引擎设置")
        engine_layout = QFormLayout(engine_group)
        
        # 配置文件路径
        self.onebot_config_path_edit = SiLineEdit()
        engine_layout.addRow("配置文件路径:", self.onebot_config_path_edit)
        self.config_widgets['onebot_engine.config_path'] = self.onebot_config_path_edit
        
        # 工作目录
        self.onebot_working_dir_edit = SiLineEdit()
        engine_layout.addRow("工作目录:", self.onebot_working_dir_edit)
        self.config_widgets['onebot_engine.working_dir'] = self.onebot_working_dir_edit
        
        # 登录超时
        self.onebot_login_timeout_spin = QSpinBox()
        self.onebot_login_timeout_spin.setRange(10, 300)
        self.onebot_login_timeout_spin.setSuffix(" 秒")
        engine_layout.addRow("登录超时:", self.onebot_login_timeout_spin)
        self.config_widgets['onebot_engine.login_timeout'] = self.onebot_login_timeout_spin
        
        scroll_layout.addWidget(engine_group)
        
        # OneBot框架设置
        framework_group = QGroupBox("OneBot框架设置")
        framework_layout = QFormLayout(framework_group)
        
        # 监听地址
        self.onebot_host_edit = SiLineEdit()
        framework_layout.addRow("监听地址:", self.onebot_host_edit)
        self.config_widgets['onebot.host'] = self.onebot_host_edit
        
        # 监听端口
        self.onebot_port_spin = QSpinBox()
        self.onebot_port_spin.setRange(1, 65535)
        framework_layout.addRow("监听端口:", self.onebot_port_spin)
        self.config_widgets['onebot.port'] = self.onebot_port_spin
        
        # 访问令牌
        self.onebot_token_edit = QLineEdit()
        self.onebot_token_edit.setEchoMode(QLineEdit.Password)
        framework_layout.addRow("访问令牌:", self.onebot_token_edit)
        self.config_widgets['onebot.access_token'] = self.onebot_token_edit
        
        scroll_layout.addWidget(framework_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "OneBot")
        
    def setup_wordlib_tab(self):
        """设置词库配置页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # 词库设置
        wordlib_group = QGroupBox("词库设置")
        wordlib_layout = QFormLayout(wordlib_group)
        
        # 词库目录
        self.wordlib_dir_edit = SiLineEdit()
        wordlib_layout.addRow("词库目录:", self.wordlib_dir_edit)
        self.config_widgets['wordlib.directory'] = self.wordlib_dir_edit
        
        # 自动重载
        self.wordlib_auto_reload_check = SiCheckBox("自动重载词库")
        wordlib_layout.addRow(self.wordlib_auto_reload_check)
        self.config_widgets['wordlib.auto_reload'] = self.wordlib_auto_reload_check
        
        # 重载间隔
        self.wordlib_reload_interval_spin = QSpinBox()
        self.wordlib_reload_interval_spin.setRange(1, 3600)
        self.wordlib_reload_interval_spin.setSuffix(" 秒")
        wordlib_layout.addRow("重载间隔:", self.wordlib_reload_interval_spin)
        self.config_widgets['wordlib.reload_interval'] = self.wordlib_reload_interval_spin
        
        # 编码格式
        self.wordlib_encoding_combo = QComboBox()
        self.wordlib_encoding_combo.addItems(["utf-8", "gbk", "gb2312"])
        wordlib_layout.addRow("编码格式:", self.wordlib_encoding_combo)
        self.config_widgets['wordlib.encoding'] = self.wordlib_encoding_combo
        
        scroll_layout.addWidget(wordlib_group)
        
        # 处理设置
        processing_group = QGroupBox("处理设置")
        processing_layout = QFormLayout(processing_group)
        
        # 最大处理时间
        self.wordlib_max_process_time_spin = QSpinBox()
        self.wordlib_max_process_time_spin.setRange(1, 60)
        self.wordlib_max_process_time_spin.setSuffix(" 秒")
        processing_layout.addRow("最大处理时间:", self.wordlib_max_process_time_spin)
        self.config_widgets['wordlib.max_process_time'] = self.wordlib_max_process_time_spin
        
        # 缓存大小
        self.wordlib_cache_size_spin = QSpinBox()
        self.wordlib_cache_size_spin.setRange(10, 1000)
        self.wordlib_cache_size_spin.setSuffix(" MB")
        processing_layout.addRow("缓存大小:", self.wordlib_cache_size_spin)
        self.config_widgets['wordlib.cache_size'] = self.wordlib_cache_size_spin
        
        scroll_layout.addWidget(processing_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "词库")
        
    def setup_logging_tab(self):
        """设置日志配置页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # 日志设置
        logging_group = QGroupBox("日志设置")
        logging_layout = QFormLayout(logging_group)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        logging_layout.addRow("日志级别:", self.log_level_combo)
        self.config_widgets['logging.level'] = self.log_level_combo
        
        # 日志文件
        self.log_file_edit = SiLineEdit()
        logging_layout.addRow("日志文件:", self.log_file_edit)
        self.config_widgets['logging.file'] = self.log_file_edit
        
        # 最大文件大小
        self.log_max_size_spin = QSpinBox()
        self.log_max_size_spin.setRange(1, 1000)
        self.log_max_size_spin.setSuffix(" MB")
        logging_layout.addRow("最大文件大小:", self.log_max_size_spin)
        self.config_widgets['logging.max_size'] = self.log_max_size_spin
        
        # 备份数量
        self.log_backup_count_spin = QSpinBox()
        self.log_backup_count_spin.setRange(1, 100)
        logging_layout.addRow("备份数量:", self.log_backup_count_spin)
        self.config_widgets['logging.backup_count'] = self.log_backup_count_spin
        
        # 控制台输出
        self.log_console_check = SiCheckBox("启用控制台输出")
        logging_layout.addRow(self.log_console_check)
        self.config_widgets['logging.console'] = self.log_console_check
        
        scroll_layout.addWidget(logging_group)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "日志")
        
    def setup_advanced_tab(self):
        """设置高级配置页面"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 原始配置编辑器
        config_group = QGroupBox("原始配置 (JSON)")
        config_layout = QVBoxLayout(config_group)
        
        self.raw_config_edit = QTextEdit()
        self.raw_config_edit.setFont(QFont("Consolas", 10))
        self.raw_config_edit.setPlaceholderText("在此处编辑原始JSON配置...")
        config_layout.addWidget(self.raw_config_edit)
        
        # 操作按钮
        btn_container = SiDenseHContainer()
        
        self.format_json_btn = SiPushButton("格式化JSON")
        self.format_json_btn.clicked.connect(self.format_json)
        
        self.validate_json_btn = SiPushButton("验证JSON")
        self.validate_json_btn.clicked.connect(self.validate_json)
        
        btn_container.addWidget(self.format_json_btn)
        btn_container.addWidget(self.validate_json_btn)
        
        config_layout.addWidget(btn_container)
        layout.addWidget(config_group)
        
        self.tab_widget.addTab(tab, "高级")
        
    def setup_buttons(self, parent_layout):
        """设置操作按钮"""
        btn_container = SiDenseHContainer()
        
        self.save_btn = SiPushButton("保存配置")
        self.save_btn.clicked.connect(self.save_config)
        
        self.reload_btn = SiPushButton("重载配置")
        self.reload_btn.clicked.connect(self.load_config)
        
        self.reset_btn = SiPushButton("重置默认")
        self.reset_btn.clicked.connect(self.reset_config)
        
        self.export_btn = SiPushButton("导出配置")
        self.export_btn.clicked.connect(self.export_config)
        
        self.import_btn = SiPushButton("导入配置")
        self.import_btn.clicked.connect(self.import_config)
        
        btn_container.addWidget(self.save_btn)
        btn_container.addWidget(self.reload_btn)
        btn_container.addWidget(self.reset_btn)
        btn_container.addWidget(self.export_btn)
        btn_container.addWidget(self.import_btn)
        
        parent_layout.addWidget(btn_container)
        
    def load_config(self):
        """加载配置"""
        try:
            # 从配置管理器加载配置
            if self.config_manager:
                self.config_data = self.config_manager.get_all_config()
            else:
                self.config_data = {}
                
            # 更新界面控件
            self.update_widgets_from_config()
            
            # 更新原始配置编辑器
            self.raw_config_edit.setPlainText(
                json.dumps(self.config_data, indent=2, ensure_ascii=False)
            )
            
            self.logger.info("配置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置失败: {e}")
            
    def update_widgets_from_config(self):
        """从配置更新界面控件"""
        for key, widget in self.config_widgets.items():
            try:
                value = self.get_config_value(key)
                if value is not None:
                    self.set_widget_value(widget, value)
            except Exception as e:
                self.logger.warning(f"更新控件 {key} 失败: {e}")
                
    def get_config_value(self, key: str):
        """获取配置值"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
                
        return value
        
    def set_widget_value(self, widget, value):
        """设置控件值"""
        if isinstance(widget, SiLineEdit):
            widget.lineEdit().setText(str(value))
        elif isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, SiCheckBox) or isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QComboBox):
            index = widget.findText(str(value))
            if index >= 0:
                widget.setCurrentIndex(index)
        elif isinstance(widget, QSpinBox):
            widget.setValue(int(value))
            
    def save_config(self):
        """保存配置"""
        try:
            # 验证所有配置
            validation_errors = self.validate_all_config()
            if validation_errors:
                self.show_validation_errors(validation_errors)
                return
                
            # 从界面控件收集配置
            self.collect_config_from_widgets()
            
            # 尝试解析原始配置
            try:
                raw_config = json.loads(self.raw_config_edit.toPlainText())
                # 验证原始配置的JSON格式
                if not isinstance(raw_config, dict):
                    QMessageBox.warning(self, "配置格式错误", "原始配置必须是JSON对象格式")
                    return
                self.config_data.update(raw_config)
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "JSON格式错误", f"原始配置JSON格式不正确: {e}")
                return
                
            # 最终验证合并后的配置
            if not self.validate_final_config():
                return
                
            # 保存到配置管理器
            if self.config_manager:
                self.config_manager.save_config(self.config_data)
                
            QMessageBox.information(self, "成功", "配置保存成功")
            self.logger.info("配置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
            
    def validate_final_config(self) -> bool:
        """验证最终配置"""
        try:
            # 检查必要的配置节点是否存在
            required_sections = ['app', 'onebot', 'wordlib', 'logging']
            missing_sections = []
            
            for section in required_sections:
                if section not in self.config_data:
                    missing_sections.append(section)
                    
            if missing_sections:
                QMessageBox.warning(
                    self, "配置不完整", 
                    f"缺少必要的配置节点: {', '.join(missing_sections)}"
                )
                return False
                
            # 检查OneBot连接配置的完整性
            onebot_config = self.config_data.get('onebot', {})
            if not onebot_config.get('host') or not onebot_config.get('port'):
                QMessageBox.warning(
                    self, "OneBot配置不完整", 
                    "OneBot的主机地址和端口不能为空"
                )
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"最终配置验证失败: {e}")
            QMessageBox.critical(self, "验证错误", f"配置验证过程中发生错误: {e}")
            return False
            
    def collect_config_from_widgets(self):
        """从界面控件收集配置"""
        for key, widget in self.config_widgets.items():
            try:
                value = self.get_widget_value(widget)
                self.set_config_value(key, value)
            except Exception as e:
                self.logger.warning(f"收集控件 {key} 值失败: {e}")
                
    def get_widget_value(self, widget):
        """获取控件值"""
        if isinstance(widget, SiLineEdit):
            return widget.lineEdit().text()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, SiCheckBox) or isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        return None
        
    def set_config_value(self, key: str, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config_data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
    def reset_config(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要重置为默认配置吗？\n\n此操作将丢失所有自定义设置！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.config_manager:
                    self.config_manager.reset_to_default()
                    
                self.load_config()
                QMessageBox.information(self, "成功", "配置已重置为默认值")
                self.logger.info("配置已重置为默认值")
                
            except Exception as e:
                self.logger.error(f"重置配置失败: {e}")
                QMessageBox.critical(self, "错误", f"重置配置失败: {e}")
                
    def export_config(self):
        """导出配置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出配置", "config_export.json", "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                    
                QMessageBox.information(self, "成功", f"配置已导出到: {file_path}")
                self.logger.info(f"配置已导出到: {file_path}")
                
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            QMessageBox.critical(self, "错误", f"导出配置失败: {e}")
            
    def import_config(self):
        """导入配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入配置", "", "JSON文件 (*.json);;所有文件 (*.*)"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                    
                self.config_data.update(imported_config)
                self.update_widgets_from_config()
                
                # 更新原始配置编辑器
                self.raw_config_edit.setPlainText(
                    json.dumps(self.config_data, indent=2, ensure_ascii=False)
                )
                
                QMessageBox.information(self, "成功", f"配置已从 {file_path} 导入")
                self.logger.info(f"配置已从 {file_path} 导入")
                
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            QMessageBox.critical(self, "错误", f"导入配置失败: {e}")
            
    def format_json(self):
        """格式化JSON"""
        try:
            raw_text = self.raw_config_edit.toPlainText()
            if raw_text.strip():
                config = json.loads(raw_text)
                formatted = json.dumps(config, indent=2, ensure_ascii=False)
                self.raw_config_edit.setPlainText(formatted)
                
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "JSON格式错误", f"JSON格式不正确: {e}")
            
    def validate_json(self):
        """验证JSON"""
        try:
            raw_text = self.raw_config_edit.toPlainText()
            if raw_text.strip():
                json.loads(raw_text)
                QMessageBox.information(self, "验证成功", "JSON格式正确")
            else:
                QMessageBox.warning(self, "验证失败", "配置内容为空")
                
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "验证失败", f"JSON格式不正确: {e}")
            
    def setup_validation(self):
        """设置实时验证"""
        for key, widget in self.config_widgets.items():
            if isinstance(widget, (SiLineEdit, QLineEdit)):
                widget.textChanged.connect(lambda text, k=key: self.validate_field_realtime(k, text))
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(lambda value, k=key: self.validate_field_realtime(k, value))
            elif isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(lambda text, k=key: self.validate_field_realtime(k, text))
                
    def validate_field_realtime(self, key: str, value):
        """实时验证单个字段"""
        try:
            error_msg = self.validate_config_value(key, value)
            widget = self.config_widgets.get(key)
            
            if error_msg:
                # 设置错误样式
                if isinstance(widget, (SiLineEdit, QLineEdit)):
                    widget.setStyleSheet("border: none; background-color: #5A3A3A;")
                    widget.setToolTip(f"错误: {error_msg}")
                self.validation_errors[key] = error_msg
            else:
                # 清除错误样式
                if isinstance(widget, (SiLineEdit, QLineEdit)):
                    widget.setStyleSheet("")
                    widget.setToolTip("")
                self.validation_errors.pop(key, None)
                
        except Exception as e:
            self.logger.warning(f"实时验证字段 {key} 失败: {e}")
            
    def validate_config_value(self, key: str, value) -> str:
        """验证单个配置值"""
        if key not in self.validation_rules:
            return ""
            
        rule = self.validation_rules[key]
        
        # 检查必填项
        if rule.get('required', False) and (value is None or value == ""):
            return "此字段为必填项"
            
        # 如果值为空且非必填，跳过其他验证
        if not rule.get('required', False) and (value is None or value == ""):
            return ""
            
        # 类型验证
        expected_type = rule.get('type')
        if expected_type == str and not isinstance(value, str):
            try:
                value = str(value)
            except:
                return f"值必须是字符串类型"
        elif expected_type == int:
            try:
                value = int(value)
            except (ValueError, TypeError):
                return f"值必须是整数类型"
        elif expected_type == bool and not isinstance(value, bool):
            return f"值必须是布尔类型"
            
        # 字符串长度验证
        if expected_type == str and isinstance(value, str):
            min_length = rule.get('min_length')
            max_length = rule.get('max_length')
            
            if min_length is not None and len(value) < min_length:
                return f"长度不能少于 {min_length} 个字符"
            if max_length is not None and len(value) > max_length:
                return f"长度不能超过 {max_length} 个字符"
                
        # 数值范围验证
        if expected_type == int and isinstance(value, int):
            min_val = rule.get('min')
            max_val = rule.get('max')
            
            if min_val is not None and value < min_val:
                return f"值不能小于 {min_val}"
            if max_val is not None and value > max_val:
                return f"值不能大于 {max_val}"
                
        # 正则表达式验证
        pattern = rule.get('pattern')
        if pattern and isinstance(value, str):
            if not re.match(pattern, value):
                if key == 'app.version':
                    return "版本号格式应为: x.y.z (如: 1.0.0)"
                elif key == 'onebot.host':
                    return "主机地址格式不正确 (如: 127.0.0.1 或 localhost)"
                else:
                    return "格式不正确"
                    
        # 选择项验证
        choices = rule.get('choices')
        if choices and value not in choices:
            return f"值必须是以下选项之一: {', '.join(choices)}"
            
        return ""
        
    def validate_all_config(self) -> List[Tuple[str, str]]:
        """验证所有配置"""
        errors = []
        
        for key, widget in self.config_widgets.items():
            try:
                value = self.get_widget_value(widget)
                error_msg = self.validate_config_value(key, value)
                if error_msg:
                    errors.append((key, error_msg))
            except Exception as e:
                errors.append((key, f"验证失败: {e}"))
                
        return errors
        
    def show_validation_errors(self, errors: List[Tuple[str, str]]):
        """显示验证错误"""
        if not errors:
            return
            
        error_text = "配置验证失败:\n\n"
        for key, error in errors:
            error_text += f"• {key}: {error}\n"
            
        QMessageBox.warning(self, "配置验证失败", error_text)

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.logger.info("配置管理窗口已关闭")
        event.accept()