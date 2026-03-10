---
name: henu-campus-assistant
description: |
  河南大学(HENU)校园一体化助手，支持教务课表查看和图书馆座位预约。
  
  使用场景：
  - 查询个人课表、当前正在上的课程、下一节课信息
  - 预约图书馆座位、查询预约记录、取消预约
  
  触发关键词：课表、课程、上课、图书馆、座位、预约、河大、HENU
version: 1.0.0
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
        - pip3
    primaryEnv: null
    emoji: "🎓"
    homepage: https://github.com/yourusername/henu-campus-assistant
---

# 河大校园助手 (HENU Campus Assistant)

该 Skill 提供河南大学教务系统和图书馆的统一接入能力。

## 前置要求

1. Python 3.9+ 已安装
2. 依赖包：`pip3 install requests pycryptodome mcp lxml`
3. 图书馆功能需要 `library_core/henu_core.py` 模块（可选）

## MCP 配置

在 OpenClaw 配置中添加：

```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "python3",
      "args": ["~/.openclaw/workspace/skills/henu-campus-assistant/scripts/henu_campus_mcp.py"],
      "transport": "stdio"
    }
  }
}
```

## 可用工具

### 账号管理
- **setup_account** - 初始化账号配置
  - 参数: `student_id` (学号), `password` (密码)
  - 可选: `library_location` (图书馆区域), `library_seat_no` (默认座位号)
  - 必须先执行此工具保存账号，其他工具才能使用

### 课表功能
- **sync_schedule** - 同步课表
  - 可选参数: `xn` (学年如 2025), `xq` (学期 1/2)
  - 成功后生成结构化课表文件

- **current_course** - 获取当前课程状态
  - 返回当前正在上的课和下一节课
  - 可选: `timezone` (时区，默认 Asia/Shanghai)

- **latest_schedule** - 获取最新课表数据
  - 返回完整的一周课表结构

### 图书馆功能
- **library_locations** - 查看可预约区域列表
  - 返回所有图书馆区域和 area_id

- **library_reserve** - 预约座位
  - 可选: `location` (区域名), `seat_no` (座位号), `target_date` (日期 YYYY-MM-DD), `preferred_time` (时间如 08:00)
  - 若不传参数，使用 setup_account 时设置的默认值
  - 若不传日期，默认为明天

- **library_records** - 查询预约记录
  - 可选: `record_type` (1=普通, 3=研习, 4=考研), `page`, `limit`

- **library_cancel** - 取消预约
  - 参数: `record_id` (记录ID)

### 系统
- **system_status** - 查看系统状态
  - 返回账号配置、模块可用性等

## 使用流程

### 首次使用

1. **配置账号**（必须）
   ```
   调用 setup_account 保存学号和密码
   可选同时设置图书馆默认区域和座位号
   ```

2. **同步课表**
   ```
   调用 sync_schedule 抓取课表
   ```

3. **日常使用**
   ```
   - current_course: 查当前/下一节课
   - library_reserve: 预约明天座位
   - library_records: 查预约记录
   ```

## 工作流程指南

### 课表查询流程
1. 用户询问"我今天有什么课"或"现在在上什么课"
2. 先调用 **system_status** 确认账号已配置
3. 调用 **current_course** 获取当前课程状态
4. 以友好的格式展示给用户

### 图书馆预约流程
1. 用户说"帮我预约图书馆座位"
2. 如果用户未指定区域/座位：
   - 调用 **system_status** 检查是否有默认值
   - 如果没有，调用 **library_locations** 展示可选区域
   - 询问用户选择
3. 调用 **library_reserve** 进行预约
4. 确认预约结果

### 取消预约流程
1. 用户说"取消图书馆预约"
2. 调用 **library_records** 获取当前预约记录
3. 让用户确认要取消的记录
4. 调用 **library_cancel** 取消指定记录

## 注意事项

1. **账号安全**: 密码保存在本地 JSON 文件中，不会上传
2. **会话复用**: 登录后会自动保存 cookies，避免重复登录
3. **图书馆依赖**: 若 library_core 模块不可用，图书馆功能将返回错误
4. **课表格式**: 课表解析依赖特定 HTML 结构，如学校系统改版可能需要更新

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 登录失败 | 检查学号密码是否正确；确认 CAS 系统正常 |
| 课表解析失败 | 可能是学校系统改版，检查原始 HTML 文件 |
| 图书馆功能不可用 | 确认 henu_core.py 模块存在且路径正确 |
| 当前课程判断错误 | 检查 period_time_config.json 节次时间配置 |
