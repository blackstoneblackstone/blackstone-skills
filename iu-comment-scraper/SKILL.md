---
name: iu-comment-scraper
description: 从 berriz.in API 爬取 IU 回复的评论数据，自动翻译韩文到中文，下载图片。需要抓取 IU 粉丝网站评论数据时使用。
---

# IU Comment Scraper

从 berriz.in 网站爬取 IU 回复的评论数据，直接调用官方 API，支持韩文翻译和图片下载。

## 功能

- ✅ 获取帖子列表（IU 回复过的所有帖子）
- ✅ 获取每个帖子的原始作者和内容
- ✅ 获取 IU 的回复内容
- ✅ 自动翻译韩文到中文
- ✅ 下载并保存帖子图片
- ✅ SQLite 数据库存储

## 使用方法

### 在 OpenClaw 会话中调用

```
帮我抓取 berriz.in 上 IU 回复的评论数据
```

AI 会自动：
1. 调用 API 获取帖子列表
2. 获取每个帖子的详情和 IU 回复
3. 翻译所有韩文内容
4. 下载图片到本地
5. 保存到 SQLite 数据库

### 命令行运行

```bash
cd /path/to/iu-comment-scraper
python3 scripts/iu_api_scraper.py
```

## 数据字段

| 字段 | 说明 |
|------|------|
| post_id | 帖子 ID |
| comment_id | 评论 ID |
| post_author | 帖子作者 |
| post_author_ko | 作者名（韩文原版） |
| post_content | 帖子内容（韩文） |
| post_content_zh | 帖子内容（中文翻译） |
| post_created_at | 发帖时间 |
| iu_reply_content | IU 回复内容（韩文） |
| iu_reply_content_zh | IU 回复内容（中文翻译） |
| iu_reply_created_at | IU 回复时间 |
| images | 下载的图片路径（JSON 数组） |

## 数据库结构

```sql
CREATE TABLE iu_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    post_author TEXT,
    post_author_ko TEXT,
    post_content TEXT,
    post_content_zh TEXT,
    post_created_at TEXT,
    iu_reply_content TEXT,
    iu_reply_content_zh TEXT,
    iu_reply_created_at TEXT,
    images TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 查询示例

```python
import sqlite3
import json

conn = sqlite3.connect('iu_comments.db')
cursor = conn.cursor()

# 查看所有数据
cursor.execute("SELECT post_id, post_author, post_content_zh, iu_reply_content_zh FROM iu_comments LIMIT 10")
for row in cursor.fetchall():
    print(row)

# 查看有图片的帖子
cursor.execute("SELECT post_id, images FROM iu_comments WHERE images IS NOT NULL AND images != '[]'")
for row in cursor.fetchall():
    images = json.loads(row[1])
    print(f"帖子 {row[0]}: {len(images)} 张图片")

conn.close()
```

## 配置

编辑 `scripts/iu_api_scraper.py` 修改配置：

```python
# Cookie（需要从浏览器复制，定期更新）
DEFAULT_COOKIE = "your_cookie_here"

# 最多抓取多少条帖子
MAX_POSTS = 50

# 图片保存目录
IMAGES_DIR = SCRIPT_DIR / "images"
```

## 注意事项

### ⚠️ Cookie 有效期

API 需要登录 Cookie，Cookie 过期后需要从浏览器重新复制。

### 🔄 翻译限制

使用 Google 翻译 API，大量请求可能触发限制。

### 📸 图片下载

图片保存在 `scripts/images/` 目录，按 `帖子 ID_ 评论 ID_ 哈希。扩展名` 命名。

## 文件结构

```
iu-comment-scraper/
├── SKILL.md
├── README.md
└── scripts/
    ├── iu_api_scraper.py      # 主脚本
    ├── iu_comments.db         # SQLite 数据库（运行后生成）
    └── images/                # 下载的图片（运行后生成）
```
