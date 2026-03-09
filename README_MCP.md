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

## 远程部署

- 使用 `docker-compose.remote.yml` + `deploy/Caddyfile`
- 详细步骤见：`DEPLOY_REMOTE.md`
- 远程导入模板：`cherrystudio_mcp_import_remote.json`

## 配置文件

- 账号配置：`henu_profile.json`
- 课表 cookies：`henu_cookies.json`
- 图书馆 cookies：`henu_library_cookies.json`

## 安全模式（推荐）

1. 设置环境变量：`HENU_STUDENT_ID`、`HENU_PASSWORD`
2. 初始化账号时使用：`setup_account(save_password=false, student_id="", password="")`
