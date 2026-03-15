# Blackstone Skills

个人 Qoder 技能仓库，存储和管理自定义 AI 技能。

## 什么是 Qoder Skills

[Qoder](https://qoder.com) 是一个 AI 驱动的开发工具，支持通过 Skills（技能）扩展其能力。每个 Skill 是一个独立的模块，包含特定的领域知识和工具调用能力，让 AI 能够更好地完成特定任务。

## 仓库结构

```
blackstone-skills/
├── README.md              # 本文件
├── sql-toolkit-1.0.0/     # SQL 工具包技能
│   ├── SKILL.md           # 技能定义和使用指南
│   └── _meta.json         # 技能元数据
└── ...                    # 其他技能
```

## 技能列表

### sql-toolkit v1.0.0

一个全面的 SQL 数据库工具包，支持 SQLite、PostgreSQL 和 MySQL。

**功能：**
- 数据库模式设计和修改
- 复杂查询编写（JOIN、聚合、窗口函数、CTE）
- 迁移脚本管理
- 查询优化和索引建议
- 数据库备份与恢复
- 慢查询调试

**适用场景：**
- 需要直接操作关系型数据库
- 设计数据库模式
- 编写和优化 SQL 查询
- 执行数据库迁移

## 如何使用

1. 在 Qoder 中导入技能
2. 在对话中直接描述你的数据库需求
3. AI 会自动调用相应的工具和方法

## 添加新技能

1. 创建新的技能目录，命名格式为 `{skill-name}-{version}`
2. 编写 `SKILL.md` 文件，定义技能的能力和使用方法
3. 添加 `_meta.json` 文件，包含技能的元数据
4. 提交并推送到本仓库

## 参考

- [Qoder 文档](https://docs.qoder.com)
- [Skills 开发指南](https://docs.qoder.com/skills)
