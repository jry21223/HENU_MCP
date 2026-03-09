# 河大一体化助手（课表 + 图书馆，CAS 登录）

本目录提供统一 MCP 服务，合并了：

- 教务课表查看（`https://xk.henu.edu.cn`）
- 图书馆座位预约（`https://zwyy.henu.edu.cn`）

两者共用同一套账号密码配置，统一走 CAS 登录。

## 功能

- 复用 CAS 加密登录流程
- 自动校验真实登录态（非 `kingo.guest`）
- 课表同步并输出结构化 `schedule_clean_latest.json/.md`
- 当前时间判定“正在上的课/下一节课”
- 节次时间自动校准（xiqueer 优先，教务页面回退）
- 图书馆区域查询、预约、记录查询、取消预约

## 账号与文件

- 唯一账号配置：`henu_xk_profile.json`
- 课表 cookies：`henu_xk_cookies.json`
- 图书馆 cookies：`henu_library_cookies.json`
- 课表输出目录：`output/`

## CLI（课表抓取）

```bash
cd "/Users/jerry/Desktop/Study/HENU_MCP/课表查看"
python3 course_schedule.py setup
python3 course_schedule.py fetch --xn 2025 --xq 1
```

## MCP

统一 MCP 入口：`mcp_server.py`  
接入说明见：`README_MCP.md`

## CherryStudio 导入 JSON

```json
{
  "mcpServers": {
    "henu-campus-unified": {
      "command": "bash",
      "args": [
        "-lc",
        "cd \"/Users/jerry/Desktop/Study/HENU_MCP/课表查看\" && /Users/jerry/.pyenv/versions/3.11.14/bin/python3 mcp_server.py --transport stdio"
      ]
    }
  }
}
```

## 推荐使用流程

1. `setup_account(student_id, password, library_location, library_seat_no)`
2. `sync_schedule()`
3. `current_course()`
4. `library_reserve()` 或 `library_records()`
