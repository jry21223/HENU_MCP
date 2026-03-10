# 项目精简与 Skill 迁移说明

## 精简对比

### 原项目结构
```
课表查看/
├── mcp_server.py          (1317 行)
├── course_schedule.py     (602 行)
├── schedule_cleaner.py    (222 行)
├── requirements.txt
├── README.md / README_MCP.md
├── henu_profile.json
├── henu_cookies.json
├── henu_library_cookies.json
├── period_time_config.json
├── period_time_calibration_state.json
├── xiqueer_period_time_request.json
└── output/
```

**原代码总行数**: ~2141 行

### 精简后 Skill 结构
```
skill/
├── SKILL.md                     (OpenClaw Skill 配置)
├── scripts/
│   └── henu_campus_mcp.py       (精简版 MCP 服务器，~500 行)
├── requirements.txt
└── .gitignore

配置文件（运行时生成）:
├── henu_profile.json
├── henu_cookies.json
├── henu_library_cookies.json
├── period_time_config.json
└── output/
```

**精简后代码总行数**: ~500 行

## 精简内容说明

### 保留的核心功能
1. ✅ CAS 登录与会话复用
2. ✅ 课表抓取与解析
3. ✅ 当前课程状态判断
4. ✅ 图书馆座位预约
5. ✅ 预约记录查询与取消

### 移除的功能
1. ❌ 命令行交互界面（setup/show/fetch 命令）
2. ❌ xiqueer 自动校准功能（简化版保留基本节次时间配置）
3. ❌ 复杂的节次时间归一化逻辑
4. ❌ 多路径课表发现策略（保留主要路径）
5. ❌ 详细的调试和日志输出

### 简化的逻辑
1. 课表解析：移除对多种表格格式的兼容，专注于标准格式
2. 时间校准：使用固定的默认节次时间配置
3. 错误处理：统一简化错误返回格式
4. 文件输出：只保留必要的 JSON 和 Markdown 输出

## 使用方法

### 方式一：作为 OpenClaw Skill 使用

1. **安装 Skill**
   ```bash
   cp -r skill ~/.openclaw/workspace/skills/henu-campus-assistant
   ```

2. **配置 MCP**
   编辑 `~/.openclaw/config.json`：
   ```json
   {
     "mcpServers": {
       "henu-campus": {
         "command": "python3",
         "args": ["~/.openclaw/workspace/skills/henu-campus-assistant/scripts/henu_campus_mcp.py"],
         "transport": "stdio"
       }
     }
   }
   ```

3. **重启 OpenClaw** 或刷新 skills

4. **使用**
   - 告诉 Agent "配置河大账号"
   - 询问 "我今天有什么课"
   - 说 "预约明天图书馆座位"

### 方式二：独立运行 MCP 服务器

```bash
cd skill
pip3 install -r requirements.txt
python3 scripts/henu_campus_mcp.py --transport stdio
```

### 方式三：在 CherryStudio 中使用

```json
{
  "mcpServers": {
    "henu-campus": {
      "command": "bash",
      "args": [
        "-lc",
        "cd /path/to/skill && python3 scripts/henu_campus_mcp.py --transport stdio"
      ]
    }
  }
}
```

## 功能使用示例

### 1. 配置账号
```
用户: 配置我的河大账号，学号 20240001，密码 ******
Agent: 调用 setup_account(student_id="20240001", password="******")
```

### 2. 同步课表
```
用户: 同步我的课表
Agent: 调用 sync_schedule()
```

### 3. 查询当前课程
```
用户: 我现在在上什么课？下一节是什么？
Agent: 调用 current_course()
```

### 4. 图书馆预约
```
用户: 帮我预约明天图书馆的座位
Agent: 调用 library_reserve()
```

### 5. 查看预约记录
```
用户: 查看我的图书馆预约记录
Agent: 调用 library_records()
```

## 注意事项

1. **账号安全**: 密码保存在本地 `henu_profile.json`，请妥善保管
2. **图书馆模块**: 如需图书馆功能，确保 `henu_core.py` 在正确路径
3. **课表解析**: 如学校系统改版，可能需要更新解析逻辑
4. **依赖安装**: 首次使用需要安装 Python 依赖

## 迁移检查清单

- [ ] 安装 Python 3.9+
- [ ] 安装依赖: `pip3 install -r requirements.txt`
- [ ] 复制 Skill 到 OpenClaw 目录
- [ ] 配置 OpenClaw MCP 设置
- [ ] 测试 setup_account 工具
- [ ] 测试 sync_schedule 工具
- [ ] 测试 current_course 工具
- [ ] 如有需要，配置图书馆模块路径
