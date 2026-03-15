---
name: iu-comment-scraper
description: 从 berriz.in 网站爬取 IU 相关内容的前 50 条回复/评论，使用 OpenClaw browser 工具获取渲染后的页面，并保存到 SQLite 数据库。使用当需要抓取 IU 粉丝网站数据、保存评论数据到数据库、或进行数据分析时。
---

# IU Comment Scraper

从 berriz.in 网站爬取 IU 相关内容的回复/评论数据，使用 OpenClaw browser 工具获取 JavaScript 渲染后的页面，并保存到 SQLite 数据库。

## 前置要求

- **OpenClaw browser 工具** - 用于获取渲染后的页面内容
- **Python 3** - 脚本使用标准库，无需额外依赖
- **SQLite** - Python 内置，无需安装

## 使用方法

### 方式 1: 在 OpenClaw 会话中直接调用

```python
# 使用 OpenClaw browser 工具获取页面
browser action=open targetUrl=https://berriz.in/zh-Hans/iu/archive/
browser action=snapshot

# 然后调用处理脚本
python3 /home/blackstone/.openclaw/workspace/skills/iu-comment-scraper/scripts/scrape_iu_comments_openclaw.py <html_file>
```

### 方式 2: 使用 sessions_spawn 调用

```
 sessions_spawn task="获取 berriz.in 网站 IU 页面的评论数据并保存到 SQLite"
```

### 方式 3: 命令行运行

```bash
# 从 HTML 文件读取
python3 scripts/scrape_iu_comments_openclaw.py page.html

# 从 stdin 读取
cat page.html | python3 scripts/scrape_iu_comments_openclaw.py
```

## 数据库结构

SQLite 数据库文件：`iu_comments.db`

```sql
CREATE TABLE iu_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_text TEXT NOT NULL,
    author TEXT,
    created_at TEXT,
    page_url TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_author ON iu_comments(author);
CREATE INDEX idx_created_at ON iu_comments(created_at);
CREATE INDEX idx_fetched_at ON iu_comments(fetched_at);
```

## 查询示例

```python
import sqlite3

conn = sqlite3.connect('iu_comments.db')
cursor = conn.cursor()

# 查看所有评论
cursor.execute("SELECT * FROM iu_comments ORDER BY fetched_at DESC LIMIT 50")
for row in cursor.fetchall():
    print(row)

# 按作者统计
cursor.execute("SELECT author, COUNT(*) as count FROM iu_comments GROUP BY author ORDER BY count DESC")
for row in cursor.fetchall():
    print(row)

# 按日期统计
cursor.execute("SELECT DATE(fetched_at) as date, COUNT(*) as count FROM iu_comments GROUP BY date ORDER BY date DESC")
for row in cursor.fetchall():
    print(row)

conn.close()
```

## 完整工作流程

### 步骤 1: 使用 OpenClaw browser 获取页面

```
browser action=open targetUrl=https://berriz.in/zh-Hans/iu/archive/
browser action=snapshot
```

### 步骤 2: 保存 HTML 到文件

将 browser snapshot 返回的 HTML 内容保存为 `page.html`

### 步骤 3: 运行爬虫脚本

```bash
python3 scripts/scrape_iu_comments_openclaw.py page.html
```

### 步骤 4: 查看结果

脚本会输出：
- 解析到的评论数量
- 保存到数据库的评论数量
- 数据库中的总评论数
- 最新 5 条评论预览

## 文件结构

```
iu-comment-scraper/
├── SKILL.md                          # 技能文档
└── scripts/
    ├── scrape_iu_comments_sqlite.py      # SQLite 版本主脚本
    ├── scrape_iu_comments_openclaw.py    # OpenClaw 集成版本
    ├── scrape_iu_comments.py             # 标准库版本（备用）
    ├── scrape_iu_comments_browser.py     # Playwright 版本（备用）
    ├── run.sh                            # 运行脚本
    ├── install.sh                        # 安装脚本
    └── init_db.sql                       # 数据库初始化 SQL（PostgreSQL 版本）
```

## 输出示例

```
==================================================
IU Comment Scraper - 处理数据
==================================================

1. 解析评论数据...
   HTML 大小：269085 字节
✓ 从 HTML 结构中提取到 25 条评论
✓ 解析到 25 条评论

2. 保存数据到 SQLite...
   数据库：/path/to/iu_comments.db
✓ 数据库已创建：/path/to/iu_comments.db
✓ 成功保存 25 条评论

3. 验证数据...
✓ 数据库中共有 25 条评论

最新数据预览:
  [1] Unknown: 这是一条评论内容...
  [2] Unknown: 这是另一条评论...
  
==================================================
完成！
==================================================
```

## 注意事项

### ⚠️ JavaScript 渲染内容

berriz.in 网站使用 Next.js 框架，内容是 JavaScript 动态渲染的。**必须使用 OpenClaw browser 工具**获取渲染后的页面，静态 HTML 中不包含评论数据。

### 📝 数据去重

脚本会自动去重，避免重复保存相同的评论。

### 🔄 多次运行

可以多次运行脚本获取最新数据，新数据会追加到数据库中。

## 扩展

### 获取其他页面

修改脚本中的 `BASE_URL` 配置：

```python
BASE_URL = "https://berriz.in/zh-Hans/iu/archive/"
# 可以改为其他页面
# BASE_URL = "https://berriz.in/zh-Hans/iu/"
```

### 批量获取

可以创建循环脚本，批量获取多个页面的评论数据。

### 数据分析

使用 SQLite 查询进行数据分析：
- 评论趋势分析
- 热门评论作者
- 评论时间分布
