---
name: henu_campus_assistant
description: 河南大学校园助手，支持课表查询、图书馆预约、研讨室预约（与 mcp-server 能力对齐）
---

# 河大校园助手

面向 OpenClaw 的本地 Skill，使用 CLI 调用内置核心能力。

## 功能

- 课表：`setup_account`、`sync_schedule`、`latest_schedule`、`latest_schedule_current_week`、`current_course`
- 图书馆：`library_locations`、`library_reserve`、`library_current`、`library_auto_signin`、`library_records`、`library_cancel`
- 研讨室：`seminar_groups`、`seminar_group_save`、`seminar_group_delete`、`seminar_filters`、`seminar_records`、`seminar_rooms`、`seminar_room_detail`、`seminar_reserve`、`seminar_cancel`
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
- `library_current`
- `library_auto_signin`
- `library_records`
- `library_cancel --record_id "<记录ID>"`
- `seminar_group_save --group_name "<组名>" --member_ids "<学号1,学号2,学号3>" [--note "<备注>"]`
- `seminar_groups`
- `seminar_group_delete --group_name "<组名>"`
- `seminar_filters`
- `seminar_records --record_type 1 --mode books`
- `seminar_rooms --target_date "2026-03-14" --members 0 [--library_names "<馆舍名>"]`
- `seminar_room_detail --area_id "<房间ID>" [--target_date "2026-03-14"]`
- `seminar_reserve --area_id "<房间ID>" --target_date "2026-03-14" --start_time "14:00" --end_time "16:00" --group_name "<组名>" --title "<主题>" --content "<超过10字的申请说明>" --mobile "<手机号>"`
- `seminar_cancel --record_id "<记录ID>"`
- `set_calibration_source --data "<DATA>" --cookie "<COOKIE>"`
- `system_status`

## 注意

- 首次使用先执行 `setup_account`
- 图书馆核心已内置：`library_core/henu_core.py`
- 研讨室 `group` 保存的是同行成员学号，不含自己；建议保存 3-9 个学号，预约时会自动去重并排除当前账号
- 研讨室预约会按照房间限制校验总人数，通常为 4-5 人起、最多 10 人
- 研讨室申请说明必须多于 10 个字
- 研讨室可先用 `seminar_records` 查记录，再用 `seminar_cancel` 取消
- 账号与 Cookie 仅本地保存
