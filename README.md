# ACE: Assistant for Course Excellence (个人课程学习助理)

> 一个开源的智能学习助手，利用大语言模型和多Agent技术，为用户提供全流程学习支持，包括内容教学、出题判题、进度跟踪、智能答疑等。
> 目前仅适配的阿里云千问(qwen)大语言模型。使用前需申请阿里云千问大模型的API密钥。

---

## 🚀 功能简介

- **多Agent协作**：支持多Agent协同，涵盖教学、练习、测评等关键环节。
- **即时答疑**：结合语言模型，为用户提供高效的学习问题解答。
- **学习计划**：自由安排学习计划，复习和学习衔接，帮助用户高效达成目标。

---

## 📦 安装

### 使用 Conda 环境安装

1. 克隆项目到本地：
   ```bash
   git clone https://github.com/AlohaWorld/ACE.git
   cd ACE
   ```

2. 创建虚拟环境并安装依赖(需要你提前安装Anaconda)：
   ```bash
   conda create -n ACE python=3.11 -y
   conda activate ACE
   pip install -r requirements.txt
   ```

3. 申请阿里云百炼大模型的API-key：
   登录阿里云
   访问阿里云百炼大模型控制台：https://bailian.console.aliyun.com/
   创建应用并获取API-key。

4. 配置 API-key：
   ```bash
   cp .env.example .env
   vim .env
   ```

   在 `.env` 文件中填入你申请的 API-key。

5. 启动服务：
   ```bash
   python main.py
   ```

---

## 📝 文档

---

## 🛠️ 使用方法

1. 启动服务：
   ```bash
   python main.py
   ```

2. 输入学号（自行拟定）和姓名，并且输入课程大纲所在路径和文件。例如 `courses/icp.yaml` 文件以个性化学习体验。

---

## 🤝 贡献指南

我们欢迎任何形式的贡献，包括但不限于代码改进、功能需求或文档完善：

1. Fork 项目并创建新分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 提交代码并发起 Pull Request。

---

## 📄 许可证

该项目基于 [Apache License](LICENSE) 开源，欢迎自由使用与分发。

---

## 📞 联系方式

- **邮件**: alhoworld@foxmail.com
- **讨论区**: [Discussions](https://github.com/AlohaWorld/ACE/discussions)

---
