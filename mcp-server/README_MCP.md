# 河大一体化 MCP 接入说明（课表 + 图书馆）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 本地启动（stdio）

```bash
python3 mcp_server.py --transport stdio
```

## CherryStudio 手动配置

- 类型：`stdio`
- 命令：`bash`
- 参数：

```bash
-lc
cd "<YOUR_HENU_MCP_DIR>/课表查看" && python3 mcp_server.py --transport stdio
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

## 配置文件

- 账号配置：`henu_profile.json`
- 课表 cookies：`henu_cookies.json`
- 图书馆 cookies：`henu_library_cookies.json`
