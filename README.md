# py-xiaozhi

<div align="center">

![py-xiaozhi](assets/logo.png)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)


_✨ 基于 Python 实现的小智语音客户端 ✨_

</div>

## 📖 项目简介

py-xiaozhi 是一个使用 Python 开发的小智语音客户端，让您能够在没有硬件设备的情况下体验 AI 小智的语音交互功能。本项目基于 [Huang-junsen/py-xiaozhi](https://github.com/Huang-junsen/py-xiaozhi) 进行了优化和功能扩展。

### 🎥 演示


### 📚 相关项目
- 原始硬件项目：[Huang-junsen/py-xiaozhi](https://github.com/Huang-junsen/py-xiaozhi)
-

## ✨ 核心特性

### 🎨 现代化界面
- 支持亮色/暗色主题动态切换
- 简洁优雅的消息气泡界面
- 实时情感状态展示
- 清晰的连接和录音状态显示

### 🎤 语音交互
- 便捷的"按住说话"语音输入
- 流畅的语音识别反馈
- 实时对话内容显示

### 🔧 系统集成
- 智能音量控制（支持 Windows/macOS）
- 首次使用验证码引导
- 完善的会话状态管理

### 🔐 安全性能
- 加密音频数据传输
- 安全的会话管理机制
- 验证码身份认证

## 🚀 快速开始

### 环境要求
- Python 3.8+ (推荐 3.12)
- 支持 Windows/Linux/macOS

### 安装步骤

#### Windows 环境
```bash
# 1. 克隆项目
git clone https://github.com/RiderTimeDecade/py-xiaozhi.git
cd py-xiaozhi

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 opus
# 将 opus.dll 复制到 C:\Windows\System32 目录
```

#### Linux/macOS 环境
```bash
# 克隆并安装
git clone https://github.com/RiderTimeDecade/py-xiaozhi.git
cd py-xiaozhi
pip3 install -r requirements.txt
```

#### 使用虚拟环境（推荐）
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行应用
```bash
python main.py
```

## 📝 使用指南

### 基本操作
1. 启动应用后，GUI 界面会自动连接服务器
2. 首次使用会显示验证码，请妥善保存
3. 界面功能区：
   - 左侧边栏：主题切换、消息管理等
   - 中央区域：对话内容展示
   - 状态栏：连接状态、情感状态显示
   - 底部控制区：音量调节、语音输入

### 语音交互
- 按住"按住说话"按钮进行语音输入
- 松开按钮结束录音
- 通过音量滑块调节系统音量
- 点击主题按钮切换显示模式

## 🔄 项目进展

### ✅ 已实现功能
- [x] 修复 goodbye 后重连问题
- [x] 全新 GUI 界面实现
- [x] 优化代码结构，实现模块化
- [x] Windows 音量控制集成
- [x] MAC 地址自动获取

### 📋 开发计划
- [ ] WebSocket 通信实现（进行中）
- [ ] Electron 版本 GUI
- [ ] 第三方音乐库集成

## 🤝 参与贡献
欢迎提交 Issues 和 Pull Requests！我们期待您的贡献。

## ⚠️ 免责声明
本项目仅供学习和研究使用，禁止用于商业目的。

## 👏 致谢
特别感谢以下开源贡献者：
- [Xiaoxia](https://github.com/78)
- [Huang-junsen](https://github.com/Huang-junsen)

## 📄 开源协议
本项目采用 [MIT](LICENSE) 协议开源。
