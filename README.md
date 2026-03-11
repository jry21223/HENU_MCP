# 河大校园助手 - OpenClaw Skill版本

这是一个为河南大学学生设计的 OpenClaw skill，提供与 `mcp-server` 分支同等能力的课表查询和图书馆座位预约功能。

## 项目分支说明

- **当前分支**: `openclaw-skill` - OpenClaw Skill实现
- **其他分支**: [`mcp-server`](https://github.com/jry21223/HENU_MCP/tree/mcp-server) - MCP服务器版本
- **主分支**: [`main`](https://github.com/jry21223/HENU_MCP) - 项目概述和导航

## 功能特性

- 🎓 **智能课表**: 查询个人课表、当前课程、下一节课信息
- 📅 **本周课表过滤**: 支持按当前周次过滤课程
- ⏰ **节次自动校准**: 支持喜鹊抓包参数配置与自动校准
- 📚 **图书馆服务**: 预约座位、查询预约记录、取消预约
- 🔐 **安全存储**: 账号信息本地加密存储，不会上传
- 💬 **自然交互**: 支持自然语言对话，无需记忆命令
- ⚡ **即时响应**: 快速获取课程和预约信息

## 快速开始

### 1. 安装skill

```bash
# 克隆OpenClaw skill分支
git clone -b openclaw-skill https://github.com/jry21223/HENU_MCP.git henu_campus_assistant

# 复制到OpenClaw skills目录
cp -r henu_campus_assistant ~/.openclaw/workspace/skills/

# 安装依赖
cd ~/.openclaw/workspace/skills/henu_campus_assistant
pip3 install -r requirements.txt
```

### 2. 在OpenClaw中刷新skills

重启OpenClaw Gateway或使用刷新命令

### 3. 开始使用

直接与OpenClaw对话：

```
你: "帮我设置河大账号，学号是2021001，密码是mypassword"
你: "查看今天的课表"
你: "现在在上什么课？"
你: "帮我预约图书馆座位"
```

## 支持的对话示例

### 课表相关
- "我今天有什么课？"
- "现在在上什么课？"
- "下一节课是什么？"
- "帮我同步最新课表"

### 图书馆相关
- "预约图书馆座位"
- "查看我的预约记录"
- "取消图书馆预约"
- "有哪些图书馆区域可以预约？"

### 账号管理
- "设置我的河大账号"
- "查看系统状态"

## 项目结构

```
openclaw-skill/
├── SKILL.md              # OpenClaw skill定义
├── henu_cli.py          # 命令行接口
├── mcp_server.py        # 与mcp分支对齐的核心实现
├── course_schedule.py   # 课表抓取
├── schedule_cleaner.py  # 课表清洗
├── library_core/
│   └── henu_core.py     # 图书馆核心（内置）
├── scripts/
│   └── henu_campus_mcp.py # Skill调用包装层
├── requirements.txt      # Python依赖
├── README.md            # 本文档
└── MIGRATION.md         # 迁移说明
```

## 技术特点

- **零配置**: 无需单独部署MCP服务进程
- **能力对齐**: 与 `mcp-server` 分支工具行为一致
- **内置图书馆核心**: 不依赖外部 `../图书馆自动预约/web`
- **可扩展**: 易于添加新功能和改进

## 故障排除

### 常见问题

1. **登录失败**
   - 检查学号密码是否正确
   - 确认河大CAS系统正常运行

2. **图书馆功能不可用**
   - 检查 `library_core/henu_core.py` 是否存在
   - 检查依赖是否已安装

3. **课表解析失败**
   - 可能是教务系统页面结构变更
   - 查看错误日志获取详细信息

### 获取帮助

如果遇到问题，可以：
1. 查看 [MIGRATION.md](MIGRATION.md) 了解技术细节
2. 检查OpenClaw日志获取错误信息
3. 在项目仓库提交issue

## 相关分支

- [MCP服务器版本](https://github.com/jry21223/HENU_MCP/tree/mcp-server) - 适用于支持MCP协议的客户端
- [项目主页](https://github.com/jry21223/HENU_MCP) - 项目概述和版本选择指南
