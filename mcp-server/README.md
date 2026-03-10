# 河大校园助手 MCP 服务器版本

这是河南大学校园助手的MCP (Model Context Protocol) 服务器版本，提供教务系统课表查询和图书馆座位预约功能。

## 功能特性

- 🎓 **教务系统集成**: 自动登录河大教务系统，获取个人课表
- 📚 **图书馆座位预约**: 支持图书馆座位预约、查询、取消
- 🔐 **安全认证**: 本地存储登录凭证，支持会话复用
- ⏰ **智能时间**: 自动识别当前课程和下一节课
- 📊 **数据导出**: 支持JSON和Markdown格式的课表导出

## 安装使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置MCP客户端

在你的MCP客户端配置中添加：

```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "python3",
      "args": ["path/to/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

### 3. 可用工具

- `setup_account` - 设置学号密码
- `sync_schedule` - 同步课表数据
- `current_course` - 查询当前课程
- `library_reserve` - 预约图书馆座位
- `library_records` - 查询预约记录
- `library_cancel` - 取消预约

## 项目结构

```
mcp-server/
├── mcp_server.py           # MCP服务器主程序
├── course_schedule.py      # 课表相关功能
├── schedule_cleaner.py     # 课表数据清理
├── library_core/          # 图书馆预约核心模块
├── requirements.txt        # Python依赖
└── README.md              # 本文档
```

## 注意事项

1. 首次使用需要通过 `setup_account` 配置学号密码
2. 图书馆功能需要 `library_core` 模块支持
3. 所有数据本地存储，不会上传到服务器
4. 支持会话保持，避免频繁登录

## 相关项目

- [OpenClaw Skill版本](../openclaw-skill/) - 适用于OpenClaw的skill版本