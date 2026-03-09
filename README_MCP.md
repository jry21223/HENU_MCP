# 河大一体化 MCP 接入说明（课表 + 图书馆）

本目录的 `mcp_server.py` 已合并课表查看与图书馆预约能力。  
只需要配置这一个 MCP 服务，只保存这一份账号密码配置。

## 1. 安装依赖

```bash
cd "/Users/jerry/Desktop/Study/HENU_MCP/课表查看"
pip install -r requirements.txt
```

## 2. 本地启动（stdio）

```bash
/Users/jerry/.pyenv/versions/3.11.14/bin/python3 mcp_server.py --transport stdio
```

## 3. CherryStudio 本机配置

路径：`设置 -> MCP 服务器 -> 添加服务器`

- 类型：`stdio`
- 命令：`bash`
- 参数：

```bash
-lc
cd "/Users/jerry/Desktop/Study/HENU_MCP/课表查看" && /Users/jerry/.pyenv/versions/3.11.14/bin/python3 mcp_server.py --transport stdio
```

可直接导入：`cherrystudio_mcp_import.json`

## 4. CherryStudio 导入 JSON（可直接粘贴）

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

## 5. MCP 工具（精简）

- `setup_account`：统一保存学号密码，可同时保存图书馆默认区域/座位
- `sync_schedule`：同步课表并生成结构化结果
- `current_course`：判断当前课程与下一节课（自动校准节次时间）
- `latest_schedule`：读取最新结构化课表
- `library_locations`：查询图书馆可用区域
- `library_reserve`：预约图书馆座位（默认使用已保存区域/座位）
- `library_records`：查询图书馆预约记录
- `library_cancel`：取消图书馆预约
- `set_calibration_source`：更新 xiqueer 节次校准源
- `system_status`：查看账号、时间、节次配置、输出文件状态

## 6. 账号与会话文件

- 唯一账号配置：`henu_xk_profile.json`
- 课表会话：`henu_xk_cookies.json`
- 图书馆会话：`henu_library_cookies.json`

说明：会话可以分开存，但账号密码只维护在 `henu_xk_profile.json` 一处。

## 7. 常用调用顺序

1. `setup_account(student_id, password, library_location, library_seat_no)`
2. `sync_schedule()`
3. `current_course()`
4. `library_reserve()` 或 `library_records()`

## 8. 常见问题

1. 导入后看不到工具：
   先停用旧 MCP，再只保留 `henu-campus-unified` 并重启 CherryStudio。
2. `current_course` 时间不准：
   先执行 `system_status()` 查看服务器时间，再用 `set_calibration_source(...)` 更新校准源。
3. 图书馆预约提示缺少区域/座位：
   首次执行 `setup_account(..., library_location, library_seat_no)` 保存默认值。
