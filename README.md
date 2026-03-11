# 河大校园助手（MCP 服务器版）

河南大学校园助手的 MCP 实现，集成了课表查询和图书馆预约能力。

## 功能概览

- 课表：同步课表、查询当前课程/下一节课、查看本周有效课表
- 图书馆：查询区域、预约座位、查询记录、取消预约
- 运维：账号本地保存、登录会话复用、节次时间自动校准

## 分支说明

- 当前分支：`mcp-server`（本 README 对应实现）
- OpenClaw Skill 版本：<https://github.com/jry21223/HENU_MCP/tree/openclaw-skill>
- 项目主页：<https://github.com/jry21223/HENU_MCP>

## 快速开始

### 1. 安装

```bash
git clone https://github.com/jry21223/HENU_MCP.git
cd HENU_MCP
git checkout mcp-server
chmod +x install.sh
./install.sh
```

### 2. 启动

```bash
./run.sh
```

等价手动方式：

```bash
source venv/bin/activate
python3 mcp_server.py --transport stdio
```

### 3. 诊断（可选）

```bash
source venv/bin/activate
python3 diagnose_mcp.py
```

## MCP 客户端配置

### Cherry Studio（推荐）

```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "bash",
      "args": [
        "-lc",
        "cd \"<YOUR_PROJECT_PATH>\" && source venv/bin/activate && python3 mcp_server.py --transport stdio"
      ]
    }
  }
}
```

将 `<YOUR_PROJECT_PATH>` 替换为你的项目绝对路径（可通过 `pwd` 获取）。

### LangBot

在 MCP 管理页新增一个 `stdio` 服务，命令与参数可直接复用上面的 `bash -lc ...`。

## 常用工具

| 类别 | 工具 |
| --- | --- |
| 账号与系统 | `setup_account`, `system_status` |
| 课表 | `sync_schedule`, `latest_schedule_current_week`（推荐）, `latest_schedule`, `current_course` |
| 图书馆 | `library_locations`, `library_reserve`, `library_records`, `library_cancel` |
| 节次校准 | `set_calibration_source` |

## 推荐使用流程

1. 首次使用先调用 `setup_account` 保存账号并验证登录
2. 调用 `sync_schedule` 拉取最新课表
3. 日常查询优先使用 `latest_schedule_current_week` 和 `current_course`
4. 图书馆流程为：`library_locations` → `library_reserve` → `library_records` / `library_cancel`

## 关键文件

- 服务入口：`mcp_server.py`
- 图书馆核心：`library_core/henu_core.py`
- 安装脚本：`install.sh`
- 启动脚本：`run.sh`
- 依赖清单：`requirements.txt`

## 常见问题

- 虚拟环境不存在：先执行 `./install.sh`
- MCP 无法连接：执行 `python3 diagnose_mcp.py` 检查路径和 Python 环境
- 图书馆功能不可用：确认 `library_core/henu_core.py` 存在且可导入

## 数据与安全

- 账号与 Cookie 默认保存在本地（如 `henu_profile.json`、`henu_cookies.json`、`henu_library_cookies.json`）
- 项目不会主动上传你的账号数据到第三方服务器
- 图书馆预约核心已内置在 `library_core/henu_core.py`，不依赖外部目录
