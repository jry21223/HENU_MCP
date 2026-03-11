# LangBot MCP 配置指南

LangBot 是一个支持 MCP (Model Context Protocol) 的 AI 平台。本指南将帮你配置河大校园助手 MCP 服务器。

## 前提条件

1. **LangBot 已安装并运行**
2. **河大校园助手 MCP 服务器已部署**（参考 [README.md](README.md) 安装）
3. **模型支持函数调用**（Function Calling）

## 配置步骤

### 1. 启用模型函数调用

在 LangBot 中：
1. 进入模型设置
2. 找到你要使用的模型（如 GPT-4、Claude 等）
3. **启用 Function Calling 功能**

### 2. 添加 MCP 服务器

#### 方法一：通过 Web 界面配置

1. **进入插件管理**
   - 点击 "Plugin Management"（插件管理）
   - 选择 "MCP Management"（MCP 管理）

2. **创建 MCP 服务器**
   - 点击右上角 "Add"（添加）
   - 选择 "Create MCP Server"（创建 MCP 服务器）

3. **填写服务器信息**
   ```
   名称: 河大校园助手
   描述: 河南大学教务系统和图书馆预约助手
   命令: bash
   参数: ["-c", "cd /path/to/HENU_MCP && source venv/bin/activate && python3 mcp_server.py --transport stdio"]
   ```

   **重要**: 将 `/path/to/HENU_MCP` 替换为你的实际项目路径

4. **测试连接**
   - 点击 "Test"（测试）按钮
   - 确保连接成功

5. **提交配置**
   - 点击 "Submit"（提交）保存配置

#### 方法二：通过配置文件

如果 LangBot 支持配置文件，可以直接编辑配置：

```json
{
  "mcpServers": {
    "henu-campus": {
      "name": "河大校园助手",
      "description": "河南大学教务系统和图书馆预约助手",
      "command": "bash",
      "args": [
        "-c",
        "cd /path/to/HENU_MCP && source venv/bin/activate && python3 mcp_server.py --transport stdio"
      ],
      "transport": "stdio"
    }
  }
}
```

### 3. 启用 MCP 服务器

1. **连接服务器**
   - 在 MCP 管理界面找到刚创建的服务器
   - 点击服务器卡片上的**开关**来连接服务器

2. **查看服务器详情**
   - 点击服务器卡片查看详细信息
   - 确认所有工具都已加载

### 4. 配置管道设置

1. **选择运行器**
   - 在管道设置中选择 **Local Agent** 作为运行器

2. **选择支持函数调用的模型**
   - 确保使用支持 Function Calling 的模型
   - 推荐模型：GPT-4、Claude 3.5 Sonnet、Gemini Pro

## 可用工具

配置成功后，LangBot 将可以使用以下工具：

### 教务系统工具
- `setup_account` - 设置学号密码
- `sync_schedule` - 同步课表数据
- `current_course` - 查询当前课程
- `latest_schedule` - 获取最新课表
- `latest_schedule_current_week` - 获取本周课表

### 图书馆工具
- `library_locations` - 查看图书馆区域
- `library_reserve` - 预约图书馆座位
- `library_records` - 查询预约记录
- `library_cancel` - 取消预约

### 系统工具
- `system_status` - 查看系统状态
- `set_calibration_source` - 设置节次时间校准

## 使用示例

配置完成后，你可以在 LangBot 中这样使用：

```
用户：我今天有什么课？
AI：让我查询一下你的课表...
[调用 current_course 工具]
AI：根据查询结果，你今天有以下课程：...

用户：帮我预约图书馆座位
AI：我先查看可用区域...
[调用 library_locations 工具]
AI：可预约区域有：一楼东、一楼西...
[调用 library_reserve 工具]
AI：预约成功！
```

## 故障排除

### 连接失败

1. **检查路径**
   ```bash
   # 确认项目路径正确
   cd /path/to/HENU_MCP
   pwd
   ```

2. **检查虚拟环境**
   ```bash
   # 确认虚拟环境存在
   ls -la venv/
   
   # 测试激活
   source venv/bin/activate
   python3 mcp_server.py --help
   ```

3. **检查依赖**
   ```bash
   # 运行诊断工具
   source venv/bin/activate
   python3 diagnose_mcp.py
   ```

### 工具调用失败

1. **确认模型支持函数调用**
   - 检查模型是否启用了 Function Calling
   - 尝试更换支持的模型

2. **检查服务器状态**
   - 在 MCP 管理界面查看服务器是否正常连接
   - 重新连接服务器

3. **查看日志**
   - 检查 LangBot 的错误日志
   - 查看 MCP 服务器的输出

### 权限问题

如果遇到权限错误：

```bash
# 确保脚本有执行权限
chmod +x /path/to/HENU_MCP/run.sh

# 确保虚拟环境可访问
chmod -R 755 /path/to/HENU_MCP/venv/
```

## 高级配置

### 自定义启动脚本

创建专门的 LangBot 启动脚本：

```bash
#!/bin/bash
# langbot_start.sh

cd /path/to/HENU_MCP
source venv/bin/activate

# 设置环境变量（如果需要）
export PYTHONPATH=/path/to/HENU_MCP:$PYTHONPATH

# 启动 MCP 服务器
python3 mcp_server.py --transport stdio
```

然后在 LangBot 中使用：
```json
{
  "command": "bash",
  "args": ["/path/to/HENU_MCP/langbot_start.sh"]
}
```

### 环境变量配置

如果需要特殊环境变量：

```json
{
  "command": "bash",
  "args": ["-c", "cd /path/to/HENU_MCP && source venv/bin/activate && CUSTOM_VAR=value python3 mcp_server.py --transport stdio"],
  "env": {
    "PYTHONPATH": "/path/to/HENU_MCP",
    "CUSTOM_CONFIG": "production"
  }
}
```

## 注意事项

1. **路径问题**: 确保所有路径都是绝对路径
2. **权限问题**: 确保 LangBot 有权限访问项目目录
3. **网络问题**: 如果是远程部署，确保网络连接正常
4. **资源限制**: MCP 服务器会占用一定的系统资源
5. **安全考虑**: 不要在配置中暴露敏感信息

## 相关链接

- [LangBot 官方文档](https://docs.langbot.app/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [河大校园助手项目](https://github.com/jry21223/HENU_MCP)
- [工具使用指南](TOOL_USAGE_GUIDE.md)