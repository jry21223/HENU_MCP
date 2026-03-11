#!/bin/bash

# 河大校园助手 MCP 服务器 - 启动脚本

if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: ./install.sh"
    exit 1
fi

echo "🚀 启动 MCP 服务器..."
source venv/bin/activate
python3 mcp_server.py --transport stdio