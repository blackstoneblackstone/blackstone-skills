---
name: get-notes
description: 从多种来源获取和管理笔记内容，包括网页剪藏、本地文件、API 等。支持 Markdown、HTML、纯文本格式，可自动提取正文、保存图片、生成摘要。需要收集或整理笔记内容时使用。
metadata: {"clawdbot":{"emoji":"📝","requires":{"anyBins":["curl","wget"]},"os":["linux","darwin","win32"]}}
---

# Get Notes - 笔记获取工具

从网页、API、本地文件等多种来源获取笔记内容，支持自动提取正文、翻译、保存图片等功能。

## 功能

- ✅ 从网页 URL 获取文章内容（自动提取正文）
- ✅ 从本地文件读取笔记（Markdown、TXT、HTML）
- ✅ 从 API 接口获取笔记数据
- ✅ 自动提取网页正文（去除广告和导航）
- ✅ 保存网页图片到本地
- ✅ 生成内容摘要
- ✅ 导出为多种格式（Markdown、JSON、HTML）
- ✅ SQLite 数据库存储笔记

## 使用方法

### 在会话中调用

```
获取 https://example.com/article 的笔记
```

AI 会自动：
1. 下载网页内容
2. 提取正文和标题
3. 保存图片到本地
4. 生成摘要
5. 保存到数据库

### 命令行运行

```bash
cd /path/to/get-notes
python3 scripts/get_notes.py https://example.com/article
```

## 支持的来源

### 1. 网页 URL

```bash
# 获取单个网页
python3 scripts/get_notes.py "https://example.com/article"

# 获取并指定输出格式
python3 scripts/get_notes.py "https://example.com/article" --format markdown

# 获取并保存图片
python3 scripts/get_notes.py "https://example.com/article" --save-images
```

### 2. 本地文件

```bash
# 读取 Markdown 文件
python3 scripts/get_notes.py --file /path/to/note.md

# 读取文本文件
python3 scripts/get_notes.py --file /path/to/note.txt

# 读取 HTML 文件
python3 scripts/get_notes.py --file /path/to/note.html
```

### 3. API 接口

```bash
# 从 API 获取
python3 scripts/get_notes.py --api "https://api.example.com/notes" --api-key "your-key"
```

## 数据字段

| 字段 | 说明 |
|------|------|
| id | 笔记唯一 ID |
| source | 来源类型（url/file/api） |
| source_url | 原始 URL 或文件路径 |
| title | 标题 |
| content | 正文内容 |
| content_html | HTML 格式内容 |
| summary | 摘要 |
| author | 作者 |
| published_at | 发布时间 |
| fetched_at | 获取时间 |
| images | 图片路径列表（JSON） |
| tags | 标签（JSON） |
| metadata | 额外元数据（JSON） |

## 数据库结构

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    content_html TEXT,
    summary TEXT,
    author TEXT,
    published_at TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    images TEXT,
    tags TEXT,
    metadata TEXT
);

CREATE INDEX idx_notes_source ON notes(source);
CREATE INDEX idx_notes_fetched_at ON notes(fetched_at);
```

## 查询示例

```python
import sqlite3
import json

conn = sqlite3.connect('notes.db')
cursor = conn.cursor()

# 查看所有笔记
cursor.execute("SELECT id, title, source_url, fetched_at FROM notes ORDER BY fetched_at DESC LIMIT 10")
for row in cursor.fetchall():
    print(f"[{row[0]}] {row[1]} - {row[2]}")

# 搜索笔记内容
cursor.execute("SELECT title, content FROM notes WHERE content LIKE '%关键词%'")
results = cursor.fetchall()

# 查看带图片的笔记
cursor.execute("SELECT title, images FROM notes WHERE images IS NOT NULL AND images != '[]'")
for row in cursor.fetchall():
    images = json.loads(row[1])
    print(f"{row[0]}: {len(images)} 张图片")

conn.close()
```

## 配置

编辑 `scripts/get_notes.py` 修改配置：

```python
# 数据库路径
DB_PATH = SCRIPT_DIR / "notes.db"

# 图片保存目录
IMAGES_DIR = SCRIPT_DIR / "images"

# 请求超时（秒）
REQUEST_TIMEOUT = 30

# User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# 是否自动提取正文
AUTO_EXTRACT_CONTENT = True

# 是否生成摘要
GENERATE_SUMMARY = True
```

## 依赖安装

```bash
pip install requests beautifulsoup4 lxml readability-lxml
```

## 文件结构

```
get-notes/
├── SKILL.md
├── README.md
└── scripts/
    ├── get_notes.py      # 主脚本
    ├── notes.db          # SQLite 数据库（运行后生成）
    └── images/           # 下载的图片（运行后生成）
```

## 注意事项

### ⚠️ 尊重版权

获取网页内容时请遵守网站的 robots.txt 和使用条款，仅用于个人学习研究。

### 🔄 网络请求限制

大量请求可能触发网站的反爬机制，建议：
- 添加适当的延迟
- 使用合理的 User-Agent
- 遵守网站的速率限制

### 📸 图片下载

图片保存在 `scripts/images/` 目录，按 `笔记ID_序号.扩展名` 命名。

## 示例输出

```markdown
# 笔记标题

**来源**: https://example.com/article  
**作者**: 作者名  
**获取时间**: 2026-03-16 10:30:00

## 摘要

这是文章的自动生成的摘要...

## 正文

这里是提取的正文内容...

## 图片

- images/note_1_001.jpg
- images/note_1_002.jpg
```
