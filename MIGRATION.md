# OpenClaw Skill 对齐说明

## 当前状态

`openclaw-skill` 分支已与 `mcp-server` 分支对齐核心功能，Skill 通过 CLI 调用相同后端逻辑。

## 对齐内容

- 课表能力：
  - `setup_account`
  - `sync_schedule`
  - `latest_schedule`
  - `latest_schedule_current_week`
  - `current_course`
- 图书馆能力：
  - `library_locations`
  - `library_reserve`
  - `library_records`
  - `library_cancel`
- 校准能力：
  - `set_calibration_source`
  - 自动节次校准与状态查看
- 系统能力：
  - `system_status`

## 技术实现

- `scripts/henu_campus_mcp.py` 作为 Skill 包装层，导出与 MCP 同名函数。
- `henu_cli.py` 提供命令行入口，将用户请求映射到上述函数。
- 核心实现与 `mcp-server` 保持一致：
  - `mcp_server.py`
  - `course_schedule.py`
  - `schedule_cleaner.py`
  - `library_core/henu_core.py`

## 依赖

当前依赖与核心实现一致：

- `requests`
- `pycryptodome`
- `lxml`
- `mcp`

## 备注

- Skill 使用方式仍是命令行调用，不需要单独启动 MCP 服务进程。
- 图书馆核心已内置在 Skill 仓库中，不依赖外部 `../图书馆自动预约/web` 目录。
