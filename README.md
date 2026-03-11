# 河大校园助手 - MCP服务器版本

这是河南大学校园助手的MCP (Model Context Protocol) 服务器版本，提供教务系统课表查询和图书馆座位预约功能。

## 项目分支说明

- **当前分支**: `mcp-server` - MCP服务器实现
- **其他分支**: [`openclaw-skill`](https://github.com/jry21223/HENU_MCP/tree/openclaw-skill) - OpenClaw Skill版本
- **主分支**: [`main`](https://github.com/jry21223/HENU_MCP) - 项目概述和导航

## 功能特性

- 🎓 **教务系统集成**: 自动登录河大教务系统，获取个人课表
- 📚 **图书馆座位预约**: 支持图书馆座位预约、查询、取消
- 🔐 **安全认证**: 本地存储登录凭证，支持会话复用
- ⏰ **智能时间**: 自动识别当前课程和下一节课
- 📊 **数据导出**: 支持JSON和Markdown格式的课表导出

## 安装使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置MCP客户端

#### Cherry Studio 配置（推荐）

```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "bash",
      "args": [
        "-lc",
        "cd \"<YOUR_PROJECT_PATH>\" && python3 mcp_server.py --transport stdio"
      ]
    }
  }
}
```

**注意**: 请将 `<YOUR_PROJECT_PATH>` 替换为你实际的项目路径。

**获取项目路径**：
```bash
cd /path/to/your/HENU_MCP
git checkout mcp-server
pwd
# 复制输出的路径
```

#### 其他MCP客户端配置

**使用uvx：**
```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "uvx",
      "args": ["-y", "python", "<YOUR_PROJECT_PATH>/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

**直接使用python3：**
```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "python3",
      "args": ["<YOUR_PROJECT_PATH>/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

### 3. 可用工具

- `setup_account` - 设置学号密码
- `sync_schedule` - 同步课表数据
- `current_course` - 查询当前课程
- `library_reserve` - 预约图书馆座位
- `library_records` - 查询预约记录
- `library_cancel` - 取消预约

## 项目结构

```
mcp-server/
├── mcp_server.py           # MCP服务器主程序
├── course_schedule.py      # 课表相关功能
├── schedule_cleaner.py     # 课表数据清理
├── library_core/          # 图书馆预约核心模块
├── requirements.txt        # Python依赖
└── README.md              # 本文档
```

## 注意事项

1. 首次使用需要通过 `setup_account` 配置学号密码
2. 图书馆功能需要 `library_core` 模块支持
3. 所有数据本地存储，不会上传到服务器
4. 支持会话保持，避免频繁登录

## 相关分支

- [OpenClaw Skill版本](https://github.com/jry21223/HENU_MCP/tree/openclaw-skill) - 适用于OpenClaw的skill版本
- [项目主页](https://github.com/jry21223/HENU_MCP) - 项目概述和版本选择指南