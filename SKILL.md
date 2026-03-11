---
name: henu_campus_assistant
description: 河南大学校园助手，支持课表查询与图书馆预约（与 mcp-server 能力对齐）
---

# 河大校园助手

面向 OpenClaw 的本地 Skill，使用 CLI 调用内置核心能力。

## 功能

- 课表：`setup_account`、`sync_schedule`、`latest_schedule`、`latest_schedule_current_week`、`current_course`
- 图书馆：`library_locations`、`library_reserve`、`library_records`、`library_cancel`
- 系统：`set_calibration_source`、`system_status`

## 执行方式

当用户询问课表/课程/图书馆相关需求时，使用 `bash` 执行：

```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py <command> [args]
```

常用命令：

- `setup_account --student_id "<学号>" --password "<密码>"`
- `sync_schedule`
- `latest_schedule_current_week`
- `current_course`
- `library_locations`
- `library_reserve --location "<区域>" --seat_no "<座位号>" --preferred_time "10:30"`
- `library_records`
- `library_cancel --record_id "<记录ID>"`
- `set_calibration_source --data "<DATA>" --cookie "<COOKIE>"`
- `system_status`

## 注意

- 首次使用先执行 `setup_account`
- 图书馆核心已内置：`library_core/henu_core.py`
- 账号与 Cookie 仅本地保存
