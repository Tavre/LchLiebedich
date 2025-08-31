# LchLiebedich - V0.2.1

一个基于OneBot V11协议的机器人框架，使用python编写，支持桌面环境和图形化界面，并且使用伪代码编写运行功能，小白也可快速上手

Tips：初版bug有点多 后续会慢慢修复的 欢迎反馈
QQ群：
## 系统要求

- Python 3.8+
- Windows

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动机器人

双击“start.bat”即可启动机器人
扫码登录onebot engine终端 也可以到engine\qr-0.png查看二维码


## 目录结构

```
lchliebedich/
├── main.py                 # 主程序入口
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖列表
├── README.md             # 说明文档
├── src/                  # 源代码目录
│   ├── __init__.py
│   ├── core/             # 核心模块
│   │   ├── __init__.py
│   │   └── bot.py        # OneBot框架核心
│   ├── config/           # 配置模块
│   │   ├── __init__.py
│   │   └── settings.py   # 配置管理
│   ├── wordlib/          # 词库模块
│   │   ├── __init__.py
│   │   ├── manager.py    # 词库管理
│   │   └── lchliebedich_engine.py
│   ├── utils/            # 工具模块
│   │   ├── __init__.py
│   │   └── logger.py     # 日志工具
│   └── gui/              # GUI模块
│       ├── __init__.py
│       ├── main_window.py      # 主窗口
│       ├── wordlib_window.py   # 词库管理窗口
│       ├── config_window.py    # 配置窗口
│       ├── log_window.py       # 日志查看窗口
│       └── stats_window.py     # 统计信息窗口
├── data/                 # 数据目录
│   ├── wordlib/          # 词库文件
│   │   └── lchliebedich_example.txt   # 示例词库
│   └── logs/             # 日志文件
└── logs/                 # 日志目录
```

## 词库系统

### 伪代码支持

框架支持丰富的伪代码功能：

可根据目录data\wordlib\lchliebedich_example.txt查看示例

## 许可证

GPL-3.0 license

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志
### v0.1.2.1
- 新增 “|”和“&”函数
- 新增运算符函数
- 重构UI（仍有部分不影响使用的小bug）

### v0.1.1
- 修复了%时间%显示时间戳的bug
- 修复无法直接关闭窗口的bug
- 修复模糊匹配的bug
- 优化onebot链接
- 新增%群名%变量

### v0.1.0
- 初始版本发布
- 实现OneBot V11协议支持
- 添加图形化界面
- 实现词库系统和伪代码功能
- 添加日志和配置系统