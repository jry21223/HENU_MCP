---
name: henu_campus_assistant
description: 河南大学校园一体化助手，支持教务课表查看和图书馆座位预约
---

# 河大校园助手 (HENU Campus Assistant)

这个skill为河南大学学生提供教务系统和图书馆的统一接入能力。

## 功能特性

- **课表管理**: 查询个人课表、当前课程、下一节课信息
- **本周过滤**: 按当前周次过滤课表（与 MCP 版本一致）
- **节次校准**: 支持喜鹊抓包参数设置与自动校准
- **图书馆服务**: 预约座位、查询预约记录、取消预约

## 使用方法

当用户询问关于课表、课程、图书馆座位等相关问题时，使用 `bash` 工具执行相应的Python脚本。

### 安装依赖（首次使用）
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && pip3 install -r requirements.txt
```

### 账号设置
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py setup_account --student_id "学号" --password "密码"
```

### 同步课表
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py sync_schedule
```

### 获取本周课表（推荐）
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py latest_schedule_current_week
```

### 查询当前课程
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py current_course
```

### 查看图书馆区域
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py library_locations
```

### 预约图书馆座位
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py library_reserve --location "区域名" --seat_no "座位号"
```

### 查询预约记录
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py library_records
```

### 取消预约
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py library_cancel --record_id "记录ID"
```

### 设置节次校准源（喜鹊抓包）
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py set_calibration_source --data "<DATA>" --cookie "<COOKIE>"
```

### 查看系统状态
```bash
cd ~/.openclaw/workspace/skills/henu_campus_assistant && python3 henu_cli.py system_status
```

## 触发关键词

当用户提到以下关键词时，主动使用此skill：
- 课表、课程、上课、下课
- 图书馆、座位、预约
- 河大、HENU、河南大学

## 注意事项

1. 首次使用需要配置学号和密码
2. 密码保存在本地，不会上传
3. 图书馆核心已内置在 skill 目录 `library_core/henu_core.py`
