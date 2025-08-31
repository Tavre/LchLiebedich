#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt5帮助窗口模块
提供详细的用户指南和帮助文档
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QTextEdit, QPushButton, QScrollArea, QFrame, QSplitter,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QGridLayout,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon, QDesktopServices
from siui.components import SiDenseHContainer, SiDenseVContainer
from siui.components.widgets import SiLabel, SiPushButton, SiLineEdit
from siui.templates.application.application import SiliconApplication

import webbrowser
from typing import Dict, List

class HelpWindowQt(SiliconApplication):
    """帮助窗口类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("lchliebedich - 帮助文档")
        self.setGeometry(200, 200, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # 设置窗口图标
        self.setWindowIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
        
        self.setup_ui()
        self.load_help_content()
        
    def setup_ui(self):
        """设置UI界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧导航树
        self.setup_navigation_tree(splitter)
        
        # 右侧内容区域
        self.setup_content_area(splitter)
        
        # 设置分割器比例
        splitter.setSizes([250, 750])
        
    def setup_navigation_tree(self, parent):
        """设置导航树"""
        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        
        # 标题
        title_label = SiLabel("帮助目录")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        nav_layout.addWidget(title_label)
        
        # 导航树
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.itemClicked.connect(self.on_nav_item_clicked)
        nav_layout.addWidget(self.nav_tree)
        
        # 搜索框
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 5, 0, 0)
        
        self.search_input = SiLineEdit()
        self.search_input.setPlaceholderText("搜索帮助内容...")
        self.search_input.textChanged.connect(self.search_help_content)
        search_layout.addWidget(self.search_input)
        
        search_btn = SiPushButton("搜索")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        
        nav_layout.addWidget(search_frame)
        
        parent.addWidget(nav_frame)
        
    def setup_content_area(self, parent):
        """设置内容区域"""
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        
        # 工具栏
        toolbar_frame = QFrame()
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(0, 0, 0, 10)
        
        # 返回按钮
        self.back_btn = SiPushButton("← 返回")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        toolbar_layout.addWidget(self.back_btn)
        
        # 前进按钮
        self.forward_btn = SiPushButton("前进 →")
        self.forward_btn.clicked.connect(self.go_forward)
        self.forward_btn.setEnabled(False)
        toolbar_layout.addWidget(self.forward_btn)
        
        toolbar_layout.addStretch()
        
        # 打印按钮
        print_btn = SiPushButton("打印")
        print_btn.clicked.connect(self.print_content)
        toolbar_layout.addWidget(print_btn)
        
        # 导出按钮
        export_btn = SiPushButton("导出")
        export_btn.clicked.connect(self.export_content)
        toolbar_layout.addWidget(export_btn)
        
        content_layout.addWidget(toolbar_frame)
        
        # 内容显示区域
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                line-height: 1.6;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
        """)
        content_layout.addWidget(self.content_area)
        
        parent.addWidget(content_frame)
        
        # 历史记录
        self.history = []
        self.history_index = -1
        
    def load_help_content(self):
        """加载帮助内容"""
        # 创建导航树项目
        help_sections = {
            "快速开始": {
                "安装和配置": "installation",
                "第一次使用": "first_use",
                "基本设置": "basic_setup"
            },
            "功能介绍": {
                "词库管理": "wordlib_management",
                "OneBot连接": "onebot_connection",
                "消息处理": "message_processing",
                "统计分析": "statistics",
                "日志查看": "log_viewing"
            },
            "高级功能": {
                "伪代码系统": "pseudocode_system",
                "自定义插件": "custom_plugins",
                "API接口": "api_interface",
                "批量操作": "batch_operations"
            },
            "故障排除": {
                "常见问题": "common_issues",
                "错误代码": "error_codes",
                "性能优化": "performance_optimization",
                "调试技巧": "debugging_tips"
            },
            "参考资料": {
                "快捷键列表": "keyboard_shortcuts",
                "配置文件格式": "config_format",
                "API文档": "api_documentation",
                "更新日志": "changelog"
            }
        }
        
        for section_name, subsections in help_sections.items():
            section_item = QTreeWidgetItem(self.nav_tree, [section_name])
            section_item.setData(0, Qt.UserRole, f"section_{section_name}")
            
            for subsection_name, content_id in subsections.items():
                subsection_item = QTreeWidgetItem(section_item, [subsection_name])
                subsection_item.setData(0, Qt.UserRole, content_id)
        
        # 展开所有项目
        self.nav_tree.expandAll()
        
        # 显示欢迎页面
        self.show_welcome_page()
        
    def show_welcome_page(self):
        """显示欢迎页面"""
        welcome_content = """
        <h1 style="color: #2c3e50; text-align: center;">欢迎使用 lchliebedich</h1>
        
        <div style="text-align: center; margin: 20px 0;">
            <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiByeD0iMTAiIGZpbGw9IiMzNDk4ZGIiLz4KPHN2ZyB4PSIyMCIgeT0iMjAiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+CjxwYXRoIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMiAxNWwtNS01IDEuNDEtMS40MUwxMCAxNC4xN2w3LjU5LTcuNTlMMTkgOGwtOSA5eiIvPgo8L3N2Zz4KPC9zdmc+" alt="Logo" style="width: 80px; height: 80px;">
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2 style="color: #495057;">🚀 快速开始</h2>
            <p>lchliebedich 是一个功能强大的QQ机器人词库管理工具，基于OneBot V11协议开发。</p>
            <ul>
                <li><strong>词库管理：</strong>轻松导入、编辑和管理机器人词库</li>
                <li><strong>实时监控：</strong>查看消息日志和统计信息</li>
                <li><strong>伪代码支持：</strong>丰富的伪代码功能，让机器人更智能</li>
                <li><strong>现代化界面：</strong>基于PyQt5的美观界面</li>
            </ul>
        </div>
        
        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1976d2;">💡 使用提示</h3>
            <p>点击左侧导航树浏览不同的帮助主题，或使用搜索功能快速找到您需要的信息。</p>
        </div>
        
        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #f57c00;">⚡ 快捷键</h3>
            <p>按 <kbd>Ctrl+F1</kbd> 随时打开此帮助窗口</p>
            <p>按 <kbd>F1</kbd> 查看关于信息</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <p style="color: #6c757d;">版本 1.0.0 | <a href="https://github.com/Tavre/lchliebedich">GitHub项目地址</a></p>
        </div>
        """
        
        self.content_area.setHtml(welcome_content)
        self.add_to_history("welcome", "欢迎页面")
        
    def on_nav_item_clicked(self, item, column):
        """导航项目点击事件"""
        content_id = item.data(0, Qt.UserRole)
        if content_id and not content_id.startswith("section_"):
            self.show_help_content(content_id, item.text(0))
            
    def show_help_content(self, content_id: str, title: str):
        """显示帮助内容"""
        content = self.get_help_content(content_id)
        self.content_area.setHtml(content)
        self.add_to_history(content_id, title)
        
    def get_help_content(self, content_id: str) -> str:
        """获取帮助内容"""
        content_map = {
            "installation": self.get_installation_content(),
            "first_use": self.get_first_use_content(),
            "basic_setup": self.get_basic_setup_content(),
            "wordlib_management": self.get_wordlib_management_content(),
            "onebot_connection": self.get_onebot_connection_content(),
            "message_processing": self.get_message_processing_content(),
            "statistics": self.get_statistics_content(),
            "log_viewing": self.get_log_viewing_content(),
            "pseudocode_system": self.get_pseudocode_system_content(),
            "custom_plugins": self.get_custom_plugins_content(),
            "api_interface": self.get_api_interface_content(),
            "batch_operations": self.get_batch_operations_content(),
            "common_issues": self.get_common_issues_content(),
            "error_codes": self.get_error_codes_content(),
            "performance_optimization": self.get_performance_optimization_content(),
            "debugging_tips": self.get_debugging_tips_content(),
            "keyboard_shortcuts": self.get_keyboard_shortcuts_content(),
            "config_format": self.get_config_format_content(),
            "api_documentation": self.get_api_documentation_content(),
            "changelog": self.get_changelog_content()
        }
        
        return content_map.get(content_id, "<h1>内容未找到</h1><p>请选择其他帮助主题。</p>")
        
    def get_installation_content(self) -> str:
        """安装和配置内容"""
        return """
        <h1>安装和配置</h1>
        
        <h2>系统要求</h2>
        <ul>
            <li>Python 3.7 或更高版本</li>
            <li>Windows 10/11, macOS 10.14+, 或 Linux</li>
            <li>至少 100MB 可用磁盘空间</li>
        </ul>
        
        <h2>安装步骤</h2>
        <ol>
            <li><strong>下载项目：</strong>
                <pre><code>git clone https://github.com/Tavre/lchliebedich.git
cd lchliebedich</code></pre>
            </li>
            <li><strong>安装依赖：</strong>
                <pre><code>pip install -r requirements.txt</code></pre>
            </li>
            <li><strong>运行程序：</strong>
                <pre><code>python main.py</code></pre>
            </li>
        </ol>
        
        <h2>配置文件</h2>
        <p>首次运行时，程序会自动创建配置文件 <code>config.yaml</code>。您可以根据需要修改以下设置：</p>
        <ul>
            <li><strong>OneBot设置：</strong>配置机器人连接信息</li>
            <li><strong>词库路径：</strong>设置词库文件存储位置</li>
            <li><strong>日志级别：</strong>调整日志详细程度</li>
        </ul>
        
        <div style="background: #d4edda; padding: 10px; border-radius: 5px; margin: 15px 0;">
            <strong>提示：</strong>建议在首次使用前备份重要的词库文件。
        </div>
        """
        
    def get_first_use_content(self) -> str:
        """第一次使用内容"""
        return """
        <h1>第一次使用</h1>
        
        <h2>启动程序</h2>
        <p>运行 <code>python main.py</code> 启动程序。程序支持两种界面模式：</p>
        <ul>
            <li><strong>Tkinter界面：</strong>轻量级，兼容性好</li>
            <li><strong>PyQt5界面：</strong>现代化，功能丰富（推荐）</li>
        </ul>
        
        <h2>基本配置</h2>
        <ol>
            <li><strong>配置OneBot连接：</strong>
                <ul>
                    <li>打开"工具" → "配置管理"</li>
                    <li>在"OneBot设置"中填入正确的连接信息</li>
                    <li>点击"测试连接"验证配置</li>
                </ul>
            </li>
            <li><strong>导入词库：</strong>
                <ul>
                    <li>点击"文件" → "导入词库"</li>
                    <li>选择词库文件（支持.txt格式）</li>
                    <li>词库会自动加载到系统中</li>
                </ul>
            </li>
            <li><strong>测试功能：</strong>
                <ul>
                    <li>在消息页面发送测试消息</li>
                    <li>查看机器人响应是否正常</li>
                </ul>
            </li>
        </ol>
        
        <h2>界面介绍</h2>
        <ul>
            <li><strong>概览页面：</strong>显示系统状态和基本信息</li>
            <li><strong>词库页面：</strong>管理和编辑词库内容</li>
            <li><strong>消息页面：</strong>查看实时消息日志</li>
            <li><strong>统计页面：</strong>查看使用统计和图表</li>
        </ul>
        
        <div style="background: #fff3cd; padding: 10px; border-radius: 5px; margin: 15px 0;">
            <strong>注意：</strong>确保QQ机器人框架（如go-cqhttp）已正确配置并运行。
        </div>
        """
        
    def get_wordlib_management_content(self) -> str:
        """词库管理内容"""
        return """
        <h1>词库管理</h1>
        
        <h2>词库格式</h2>
        <p>lchliebedich 支持特定格式的词库文件：</p>
        <pre><code># 这是注释
问题1
答案1
答案2

问题2
答案1</code></pre>
        
        <h2>伪代码功能</h2>
        <p>词库支持丰富的伪代码功能：</p>
        <ul>
            <li><code>%用户名%</code> - 获取发送者昵称</li>
            <li><code>%群名%</code> - 获取群聊名称</li>
            <li><code>%时间%</code> - 获取当前时间</li>
            <li><code>%随机数%</code> - 生成随机数</li>
            <li><code>%天气%</code> - 获取天气信息</li>
        </ul>
        
        <h2>词库操作</h2>
        <h3>导入词库</h3>
        <ol>
            <li>点击"文件" → "导入词库"</li>
            <li>选择词库文件</li>
            <li>系统会自动解析并加载词库</li>
        </ol>
        
        <h3>编辑词库</h3>
        <ol>
            <li>在词库页面选择要编辑的词库</li>
            <li>双击条目进行编辑</li>
            <li>使用工具栏按钮添加、删除条目</li>
        </ol>
        
        <h3>导出词库</h3>
        <ol>
            <li>点击"文件" → "导出词库"</li>
            <li>选择导出格式和位置</li>
            <li>支持多种格式：TXT、JSON、CSV</li>
        </ol>
        
        <h2>批量操作</h2>
        <ul>
            <li><strong>批量导入：</strong>一次导入多个词库文件</li>
            <li><strong>批量编辑：</strong>使用查找替换功能</li>
            <li><strong>批量删除：</strong>选择多个条目进行删除</li>
        </ul>
        
        <div style="background: #d1ecf1; padding: 10px; border-radius: 5px; margin: 15px 0;">
            <strong>技巧：</strong>使用Ctrl+F快速搜索词库内容，支持正则表达式。
        </div>
        """
        
    def get_keyboard_shortcuts_content(self) -> str:
        """快捷键列表内容"""
        return """
        <h1>快捷键列表</h1>
        
        <h2>全局快捷键</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <th style="border: none; padding: 8px; text-align: left; background-color: #f5f5f5;">快捷键</th>
                    <th style="border: none; padding: 8px; text-align: left; background-color: #f5f5f5;">功能</th>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+I</kbd></td>
                    <td style="border: none; padding: 8px;">导入词库</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+E</kbd></td>
                    <td style="border: none; padding: 8px;">导出词库</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>F5</kbd></td>
                    <td style="border: none; padding: 8px;">重载词库</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+T</kbd></td>
                    <td style="border: none; padding: 8px;">测试连接</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+W</kbd></td>
                    <td style="border: none; padding: 8px;">词库管理</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+,</kbd></td>
                    <td style="border: none; padding: 8px;">配置管理</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>F11</kbd></td>
                    <td style="border: none; padding: 8px;">全屏切换</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>F1</kbd></td>
                    <td style="border: none; padding: 8px;">关于</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+F1</kbd></td>
                    <td style="border: none; padding: 8px;">帮助文档</td>
                </tr>
                </table>
        
        <h2>页面切换</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <th style="border: none; padding: 8px; text-align: left; background-color: #f5f5f5;">快捷键</th>
                    <th style="border: none; padding: 8px; text-align: left; background-color: #f5f5f5;">页面</th>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+1</kbd></td>
                    <td style="border: none; padding: 8px;">概览页面</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+2</kbd></td>
                    <td style="border: none; padding: 8px;">词库页面</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+3</kbd></td>
                    <td style="border: none; padding: 8px;">消息页面</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+4</kbd></td>
                    <td style="border: none; padding: 8px;">统计页面</td>
                </tr>
                </table>
        
        <h2>编辑快捷键</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                <tr>
                    <th style="border: none; padding: 8px; text-align: left; background-color: #f5f5f5;">快捷键</th>
                    <th style="border: none; padding: 8px; text-align: left; background-color: #f5f5f5;">功能</th>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+F</kbd></td>
                    <td style="border: none; padding: 8px;">查找</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+H</kbd></td>
                    <td style="border: none; padding: 8px;">查找替换</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+A</kbd></td>
                    <td style="border: none; padding: 8px;">全选</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+C</kbd></td>
                    <td style="border: none; padding: 8px;">复制</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+V</kbd></td>
                    <td style="border: none; padding: 8px;">粘贴</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+Z</kbd></td>
                    <td style="border: none; padding: 8px;">撤销</td>
                </tr>
                <tr>
                    <td style="border: none; padding: 8px;"><kbd>Ctrl+Y</kbd></td>
                    <td style="border: none; padding: 8px;">重做</td>
                </tr>
                </table>
        
        <div style="background: #e7f3ff; padding: 10px; border-radius: 5px; margin: 15px 0;">
            <strong>提示：</strong>您可以在配置中自定义快捷键设置。
        </div>
        """
        
    def get_common_issues_content(self) -> str:
        """常见问题内容"""
        return """
        <h1>常见问题</h1>
        
        <h2>连接问题</h2>
        <h3>Q: 无法连接到OneBot服务器</h3>
        <p><strong>A:</strong> 请检查以下项目：</p>
        <ul>
            <li>确认OneBot服务器（如go-cqhttp）正在运行</li>
            <li>检查IP地址和端口号是否正确</li>
            <li>确认防火墙没有阻止连接</li>
            <li>查看OneBot服务器日志是否有错误信息</li>
        </ul>
        
        <h3>Q: 连接频繁断开</h3>
        <p><strong>A:</strong> 可能的解决方案：</p>
        <ul>
            <li>增加心跳间隔时间</li>
            <li>检查网络稳定性</li>
            <li>更新OneBot服务器版本</li>
        </ul>
        
        <h2>词库问题</h2>
        <h3>Q: 词库导入失败</h3>
        <p><strong>A:</strong> 请确认：</p>
        <ul>
            <li>词库文件格式正确（UTF-8编码）</li>
            <li>文件没有被其他程序占用</li>
            <li>词库内容符合格式要求</li>
        </ul>
        
        <h3>Q: 机器人不回复消息</h3>
        <p><strong>A:</strong> 检查项目：</p>
        <ul>
            <li>词库是否正确加载</li>
            <li>触发词是否匹配</li>
            <li>机器人是否有发言权限</li>
            <li>查看日志中的错误信息</li>
        </ul>
        
        <h2>性能问题</h2>
        <h3>Q: 程序运行缓慢</h3>
        <p><strong>A:</strong> 优化建议：</p>
        <ul>
            <li>减少词库大小</li>
            <li>关闭不必要的日志记录</li>
            <li>增加系统内存</li>
            <li>使用SSD硬盘</li>
        </ul>
        
        <h3>Q: 内存占用过高</h3>
        <p><strong>A:</strong> 解决方法：</p>
        <ul>
            <li>定期重启程序</li>
            <li>清理日志文件</li>
            <li>优化词库结构</li>
        </ul>
        
        <h2>界面问题</h2>
        <h3>Q: 界面显示异常</h3>
        <p><strong>A:</strong> 尝试以下方法：</p>
        <ul>
            <li>重启程序</li>
            <li>检查系统DPI设置</li>
            <li>更新显卡驱动</li>
            <li>切换到Tkinter界面模式</li>
        </ul>
        
        <div style="background: #f8d7da; padding: 10px; border-radius: 5px; margin: 15px 0;">
            <strong>仍有问题？</strong>请访问 <a href="https://github.com/Tavre/lchliebedich/issues">GitHub Issues</a> 提交问题报告。
        </div>
        """
        
    # 其他内容方法的简化实现
    def get_basic_setup_content(self) -> str:
        return "<h1>基本设置</h1><p>基本设置内容...</p>"
        
    def get_onebot_connection_content(self) -> str:
        return "<h1>OneBot连接</h1><p>OneBot连接配置说明...</p>"
        
    def get_message_processing_content(self) -> str:
        return "<h1>消息处理</h1><p>消息处理机制说明...</p>"
        
    def get_statistics_content(self) -> str:
        return "<h1>统计分析</h1><p>统计功能使用说明...</p>"
        
    def get_log_viewing_content(self) -> str:
        return "<h1>日志查看</h1><p>日志查看功能说明...</p>"
        
    def get_pseudocode_system_content(self) -> str:
        return "<h1>伪代码系统</h1><p>伪代码功能详细说明...</p>"
        
    def get_custom_plugins_content(self) -> str:
        return "<h1>自定义插件</h1><p>插件开发指南...</p>"
        
    def get_api_interface_content(self) -> str:
        return "<h1>API接口</h1><p>API接口文档...</p>"
        
    def get_batch_operations_content(self) -> str:
        return "<h1>批量操作</h1><p>批量操作功能说明...</p>"
        
    def get_error_codes_content(self) -> str:
        return "<h1>错误代码</h1><p>错误代码对照表...</p>"
        
    def get_performance_optimization_content(self) -> str:
        return "<h1>性能优化</h1><p>性能优化建议...</p>"
        
    def get_debugging_tips_content(self) -> str:
        return "<h1>调试技巧</h1><p>调试方法和技巧...</p>"
        
    def get_config_format_content(self) -> str:
        return "<h1>配置文件格式</h1><p>配置文件格式说明...</p>"
        
    def get_api_documentation_content(self) -> str:
        return "<h1>API文档</h1><p>完整的API文档...</p>"
        
    def get_changelog_content(self) -> str:
        return "<h1>更新日志</h1><p>版本更新历史...</p>"
        
    def search_help_content(self, text: str):
        """搜索帮助内容"""
        if not text.strip():
            return
            
        # 简单的搜索实现
        search_results = []
        for i in range(self.nav_tree.topLevelItemCount()):
            top_item = self.nav_tree.topLevelItem(i)
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                if text.lower() in child_item.text(0).lower():
                    search_results.append(child_item)
        
        # 高亮搜索结果
        for item in search_results:
            item.setSelected(True)
            
    def perform_search(self):
        """执行搜索"""
        text = self.search_input.text()
        self.search_help_content(text)
        
    def add_to_history(self, content_id: str, title: str):
        """添加到历史记录"""
        # 清除前进历史
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
            
        self.history.append((content_id, title))
        self.history_index = len(self.history) - 1
        
        # 更新按钮状态
        self.back_btn.setEnabled(self.history_index > 0)
        self.forward_btn.setEnabled(False)
        
    def go_back(self):
        """返回上一页"""
        if self.history_index > 0:
            self.history_index -= 1
            content_id, title = self.history[self.history_index]
            
            if content_id == "welcome":
                self.show_welcome_page()
            else:
                content = self.get_help_content(content_id)
                self.content_area.setHtml(content)
            
            # 更新按钮状态
            self.back_btn.setEnabled(self.history_index > 0)
            self.forward_btn.setEnabled(self.history_index < len(self.history) - 1)
            
    def go_forward(self):
        """前进到下一页"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            content_id, title = self.history[self.history_index]
            
            if content_id == "welcome":
                self.show_welcome_page()
            else:
                content = self.get_help_content(content_id)
                self.content_area.setHtml(content)
            
            # 更新按钮状态
            self.back_btn.setEnabled(self.history_index > 0)
            self.forward_btn.setEnabled(self.history_index < len(self.history) - 1)
            
    def print_content(self):
        """打印内容"""
        # 简单的打印实现
        QMessageBox.information(self, "打印", "打印功能暂未实现")
        
    def export_content(self):
        """导出内容"""
        # 简单的导出实现
        QMessageBox.information(self, "导出", "导出功能暂未实现")