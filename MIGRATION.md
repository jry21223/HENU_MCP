# Skill 对齐摘要

## 目标

让 `openclaw-skill` 与 `mcp-server` 在能力上保持一致，但以 CLI 方式供 OpenClaw 调用。

## 已完成

- 对齐工具能力：账号、课表、图书馆、节次校准、系统状态
- 增加命令：`latest_schedule_current_week`、`set_calibration_source`
- 内置图书馆核心：`library_core/henu_core.py`
- Skill 层改为薄封装：`scripts/henu_campus_mcp.py`

## 现状

- 使用方式：`python3 henu_cli.py <command> ...`
- 依赖：`requests`、`pycryptodome`、`lxml`、`mcp`
