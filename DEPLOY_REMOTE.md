# 远程部署指南（无需本地常驻）

本项目可部署到云服务器，通过 HTTPS 远程调用 MCP。

## 1. 准备

```bash
cp deploy/.env.example .env
# 编辑 .env，至少填写 MCP_DOMAIN 和 MCP_API_TOKEN
```

建议生成随机 Token：

```bash
openssl rand -hex 32
```

## 2. 初始化数据目录

```bash
bash deploy/init_data.sh
```

## 3. 启动

```bash
docker compose -f docker-compose.remote.yml up -d --build
```

## 4. 健康检查

```bash
curl -i https://<你的域名>/
# 返回 200: HENU MCP is running

curl -i https://<你的域名>/mcp
# 未带 Authorization 会返回 401
```

## 5. CherryStudio 配置

可导入 `cherrystudio_mcp_import_remote.json`，并替换：

- `<YOUR_DOMAIN>`
- `<YOUR_MCP_API_TOKEN>`

## 6. 账号配置（更安全做法）

推荐把账号放到环境变量，不写入磁盘：

- `.env` 中配置 `HENU_STUDENT_ID` 和 `HENU_PASSWORD`
- MCP 调用 `setup_account(save_password=false, student_id="", password="")`

这样本地 `henu_profile.json` 不会保存明文密码。

## 7. 升级

```bash
git pull
docker compose -f docker-compose.remote.yml up -d --build
```

## 8. 安全建议

- 仅通过 HTTPS 暴露服务
- 必须设置高强度 `MCP_API_TOKEN`
- 限制服务器防火墙来源 IP
- `data/` 目录权限保持 700，JSON 文件保持 600
- 不要把 `.env` 和 `data/` 提交到 Git
