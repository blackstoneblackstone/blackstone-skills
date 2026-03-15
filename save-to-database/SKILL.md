---
name: save-to-database
description: 通用数据库保存技能。将任意数据保存到 SQLite 数据库，支持自定义表结构和字段。当用户说"保存到数据库"、"记录到数据库"或需要持久化存储数据时使用。
---

# Save to Database

通用的 SQLite 数据库保存技能，支持任意数据结构的存储和查询。

## 功能

- ✅ 自动创建数据库和表
- ✅ 支持自定义表名和字段
- ✅ 智能推断数据结构
- ✅ 支持 JSON、文本、数字等多种类型
- ✅ 避免重复保存（基于唯一键）
- ✅ 支持数据查询和导出

## 使用方法

### 在 OpenClaw 会话中调用

**简单保存：**
```
把这些数据保存到数据库
```

**指定表名：**
```
保存到 users 表
```

**带字段说明：**
```
保存用户信息到数据库，包含姓名、年龄、邮箱
```

**查询数据：**
```
查看数据库里保存了什么
```

**导出数据：**
```
导出数据库为 Excel
```

## 数据库位置

默认保存在技能目录：
```
save-to-database/scripts/data.db
```

## 支持的字段类型

| 类型 | 说明 | 示例 |
|------|------|------|
| TEXT | 文本 | "张三" |
| INTEGER | 整数 | 25 |
| REAL | 浮点数 | 3.14 |
| JSON | JSON 对象 | {"key": "value"} |
| TIMESTAMP | 时间戳 | 自动添加 |

## 示例场景

### 1. 保存聊天记录
```
保存这段对话到数据库
```

### 2. 保存商品信息
```
保存商品数据：名称=iPhone 15，价格=7999，数量=10
```

### 3. 保存任务列表
```
记录待办事项：买牛奶、开会、写报告
```

### 4. 保存爬虫数据
```
把抓取的数据存到数据库
```

## 查询示例

```python
import sqlite3
import json

conn = sqlite3.connect('save-to-database/scripts/data.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("表列表:", tables)

# 查看某个表的数据
cursor.execute("SELECT * FROM default_data LIMIT 10")
for row in cursor.fetchall():
    print(row)

conn.close()
```

## 文件结构

```
save-to-database/
├── SKILL.md
├── README.md
└── scripts/
    ├── db_manager.py        # 数据库管理脚本
    └── data.db              # SQLite 数据库（运行后生成）
```

## 注意事项

### ⚠️ 表名规范
- 默认表名：`default_data`
- 表名只能包含字母、数字、下划线
- 避免使用 SQL 关键字

### 🔄 避免重复
- 默认使用 `data_hash` 字段去重
- 相同数据不会重复保存

### 📦 大数据量
- 单次保存建议不超过 1000 条
- 大量数据分批保存
