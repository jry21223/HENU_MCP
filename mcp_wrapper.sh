#!/bin/bash
# MCP服务器包装脚本 - 用于捕获错误和调试

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到脚本目录
cd "$SCRIPT_DIR" || exit 1

# 记录启动日志
echo "[$(date)] MCP服务器启动" >> mcp_debug.log
echo "工作目录: $SCRIPT_DIR" >> mcp_debug.log

# 启动MCP服务器，将stderr重定向到日志
python3 mcp_server.py --transport stdio 2>> mcp_debug.log
