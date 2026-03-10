# 河大校园助手 OpenClaw Skill

这是一个为河南大学学生设计的OpenClaw skill，提供教务系统课表查询和图书馆座位预约功能。

## 安装方法

1. 将此skill目录复制到OpenClaw的skills目录：
   ```bash
   cp -r skill ~/.openclaw/workspace/skills/henu_campus_assistant
   ```

2. 安装Python依赖：
   ```bash
   cd ~/.openclaw/workspace/skills/henu_campus_assistant
   pip3 install -r requirements.txt
   ```

3. 在OpenClaw中刷新skills或重启Gateway

## 使用方法

安装后，你可以直接向OpenClaw询问：

- "帮我查看今天的课表"
- "现在在上什么课？"
- "帮我预约图书馆座位"
- "查看我的图书馆预约记录"

OpenClaw会自动识别这些请求并使用此skill来处理。

## 首次使用

首次使用前需要配置学号和密码：

"帮我设置河大账号，学号是xxx，密码是xxx"

## 功能特性

- ✅ 课表同步和查询
- ✅ 当前课程状态查询
- ✅ 图书馆座位预约
- ✅ 预约记录查询和取消
- ✅ 账号信息本地安全存储

## 注意事项

1. 账号信息仅保存在本地，不会上传
2. 图书馆功能需要额外的library_core模块（可选）
3. 首次使用需要配置学号密码