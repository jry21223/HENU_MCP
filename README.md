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

### 快速安装（推荐）

**对于 Debian/Ubuntu 系统（包括服务器）：**

```bash
# 1. 克隆项目并切换到 mcp-server 分支
git clone https://github.com/jry21223/HENU_MCP.git
cd HENU_MCP
git checkout mcp-server

# 2. 运行安装脚本（自动创建虚拟环境）
chmod +x install.sh
./install.sh

# 3. 启动服务器
./run.sh
```

### 手动安装

如果自动安装失败，可以手动安装：

```bash
# 1. 安装系统依赖（如果需要）
sudo apt update
sudo apt install python3 python3-venv python3-pip

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 验证安装
python3 diagnose_mcp.py
```

### 启动服务器

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动MCP服务器
python3 mcp_server.py --transport stdio

# 或使用快速启动脚本
./run.sh
```

### MCP客户端配置

#### Cherry Studio 配置（推荐）

**使用虚拟环境的配置（推荐）：**

```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "bash",
      "args": [
        "-c",
        "cd \"<YOUR_PROJECT_PATH>\" && source venv/bin/activate && python3 mcp_server.py --transport stdio"
      ]
    }
  }
}
```

**直接使用系统Python（如果没有虚拟环境）：**

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
# 复制输出的路径到配置中
```

**测试连接**：
```bash
# 运行诊断工具检查配置
python3 diagnose_mcp.py
```

#### 其他MCP客户端配置

**LangBot 配置：**

LangBot 支持通过 Web 界面配置 MCP 服务器：

1. 进入 Plugin Management → MCP Management
2. 点击 Add → Create MCP Server
3. 填写配置：
   ```
   名称: 河大校园助手
   命令: bash
   参数: ["-c", "cd \"<YOUR_PROJECT_PATH>\" && source venv/bin/activate && python3 mcp_server.py --transport stdio"]
   ```
4. 测试连接并提交
5. 启用服务器开关

详细配置请参考：[LANGBOT_CONFIG.md](LANGBOT_CONFIG.md)

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

### 可用工具

- `setup_account` - 设置学号密码
- `sync_schedule` - 同步课表数据
- `current_course` - 查询当前课程
- `latest_schedule` - 获取最新课表
- `library_locations` - 查看图书馆区域
- `library_reserve` - 预约图书馆座位
- `library_records` - 查询预约记录
- `library_cancel` - 取消预约
- `set_calibration_source` - 设置喜鹊API自动获取节次时间
- `system_status` - 查看系统状态



## 项目结构

```
mcp-server/
├── mcp_server.py           # MCP服务器主程序
├── course_schedule.py      # 课表相关功能
├── schedule_cleaner.py     # 课表数据清理
├── diagnose_mcp.py         # 诊断工具
├── install.sh              # 自动安装脚本
├── run.sh                  # 快速启动脚本
├── requirements.txt        # Python依赖
├── TOOL_USAGE_GUIDE.md     # 工具使用指南
├── WEEK_FILTER_GUIDE.md    # 周次过滤说明
└── README.md              # 本文档
```

## 注意事项

1. **虚拟环境**: 推荐使用虚拟环境避免依赖冲突
2. **首次配置**: 需要通过 `setup_account` 配置学号密码
3. **图书馆功能**: 需要 `library_core` 模块支持
4. **数据安全**: 所有数据本地存储，不会上传到服务器
5. **会话保持**: 支持登录状态保持，避免频繁重新登录

## 故障排除

### 安装问题

- **虚拟环境错误**: 确保安装了 `python3-venv`
- **依赖安装失败**: 尝试使用国内镜像源
- **权限问题**: 使用 `sudo` 安装系统依赖

### 连接问题

- **MCP连接失败**: 运行 `python3 diagnose_mcp.py` 检查
- **路径错误**: 确保配置中的路径正确
- **Python版本**: 需要 Python 3.8+

更多问题请查看 [TOOL_USAGE_GUIDE.md](TOOL_USAGE_GUIDE.md)

## 相关分支

- [OpenClaw Skill版本](https://github.com/jry21223/HENU_MCP/tree/openclaw-skill) - 适用于OpenClaw的skill版本
- [项目主页](https://github.com/jry21223/HENU_MCP) - 项目概述和版本选择指南