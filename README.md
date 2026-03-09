# 河大一体化助手（课表 + 图书馆，CAS 登录）

本目录提供统一 MCP 服务，合并了：

- 教务课表查看（`https://xk.henu.edu.cn`）
- 图书馆座位预约（`https://zwyy.henu.edu.cn`）

## 功能

- CAS 登录并自动复用会话
- 课表同步与结构化输出
- 当前时段课程判断（含节次自动校准）
- 图书馆区域查询、预约、记录、取消

## 账号与配置文件

- 账号配置：`henu_profile.json`
- 课表 cookies：`henu_cookies.json`
- 图书馆 cookies：`henu_library_cookies.json`

## CLI（课表抓取）

```bash
python3 course_schedule.py setup
python3 course_schedule.py fetch --xn 2025 --xq 1
```

## CherryStudio 导入 JSON

```json
{
  "mcpServers": {
    "henu-campus-unified": {
      "command": "bash",
      "args": [
        "-lc",
        "cd \"<YOUR_HENU_MCP_DIR>/课表查看\" && python3 mcp_server.py --transport stdio"
      ]
    }
  }
}
```
