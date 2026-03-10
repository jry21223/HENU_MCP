# MCP 配置指南

## 常见配置错误和解决方案

### 错误1：路径不正确
```
❌ "args": ["/Users/jerry/HENU_MCP/mcp_server.py"]
```
**解决方案**: 使用你实际的文件路径

### 错误2：缺少transport字段
```json
❌ {
  "command": "python3",
  "args": ["path/to/mcp_server.py"]
}
```
**解决方案**: 添加 `"transport": "stdio"`

### 错误3：JSON格式错误
```json
❌ {
  "mcpServers": {
    "henu-campus": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "transport": "stdio"
    }
  }
}  // ← 多余的逗号
```

## 正确的配置示例

### 1. 基础配置（最常用）
```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "python3",
      "args": ["/Users/你的用户名/HENU_MCP/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

### 2. 带环境变量的配置
```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "python3",
      "args": ["/Users/你的用户名/HENU_MCP/mcp_server.py"],
      "transport": "stdio",
      "env": {
        "PYTHONPATH": "/Users/你的用户名/HENU_MCP",
        "DEBUG": "1"
      }
    }
  }
}
```

### 3. 使用虚拟环境
```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "/Users/你的用户名/HENU_MCP/venv/bin/python",
      "args": ["/Users/你的用户名/HENU_MCP/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

## 如何获取正确的路径

### 方法1：使用终端
```bash
cd /path/to/your/HENU_MCP
pwd
# 输出：/Users/jerry/HENU_MCP
```

### 方法2：使用Python
```bash
cd /path/to/your/HENU_MCP
python3 -c "import os; print(os.path.abspath('mcp_server.py'))"
```

### 方法3：使用ls命令验证
```bash
ls -la /Users/你的用户名/HENU_MCP/mcp_server.py
# 如果文件存在，会显示文件信息
```

## 测试配置

配置完成后，可以通过以下方式测试：

1. **直接运行服务器**
```bash
cd /path/to/your/HENU_MCP
python3 mcp_server.py
```

2. **检查依赖**
```bash
cd /path/to/your/HENU_MCP
pip3 install -r requirements.txt
```

3. **验证MCP客户端连接**
   - 重启你的MCP客户端
   - 查看是否出现 "henu-campus" 服务器
   - 尝试调用 `system_status` 工具

## 常见问题排查

### 问题1：找不到模块
**错误信息**: `ModuleNotFoundError: No module named 'xxx'`
**解决方案**: 
```bash
cd /path/to/your/HENU_MCP
pip3 install -r requirements.txt
```

### 问题2：权限问题
**错误信息**: `Permission denied`
**解决方案**: 
```bash
chmod +x /path/to/your/HENU_MCP/mcp_server.py
```

### 问题3：Python版本问题
**解决方案**: 确保使用Python 3.9+
```bash
python3 --version
```