# IU Comment Scraper Skill

从 berriz.in 网站爬取 IU 相关内容的回复/评论，使用 OpenClaw browser 工具获取渲染后的页面，并保存到 SQLite 数据库。

## 快速开始

### 在 OpenClaw 会话中使用

```python
# 1. 使用 browser 工具获取页面
browser action=open targetUrl=https://berriz.in/zh-Hans/iu/archive/
browser action=snapshot

# 2. 保存 HTML 到文件，然后运行脚本
python3 scripts/iu_scraper_skill.py page.html

# 或者直接在 Python 中调用
from iu_scraper_skill import scrape_iu_comments
result = scrape_iu_comments(html_content)
```

### 命令行使用

```bash
# 从 HTML 文件读取
python3 scripts/iu_scraper_skill.py page.html

# 从 stdin 读取
cat page.html | python3 scripts/iu_scraper_skill.py
```

## 文件说明

- `iu_scraper_skill.py` - 主脚本，包含完整的爬取和保存功能
- `scrape_iu_comments_sqlite.py` - SQLite 版本核心模块
- `scrape_iu_comments_openclaw.py` - OpenClaw 集成版本
- `run_openclaw.py` - OpenClaw 运行脚本

## 数据库

SQLite 数据库文件：`iu_comments.db`

表结构：
```sql
CREATE TABLE iu_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comment_text TEXT NOT NULL,
    author TEXT,
    created_at TEXT,
    page_url TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 查询数据

```python
import sqlite3

conn = sqlite3.connect('iu_comments.db')
cursor = conn.cursor()

# 查看所有评论
cursor.execute("SELECT * FROM iu_comments ORDER BY fetched_at DESC LIMIT 50")
for row in cursor.fetchall():
    print(row)

conn.close()
```

## 依赖

- Python 3 (标准库，无需额外依赖)
- OpenClaw browser 工具 (用于获取渲染后的页面)
- SQLite (Python 内置)
