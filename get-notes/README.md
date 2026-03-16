# Get Notes

从多种来源获取和管理笔记内容的工具。

## 功能

- 从网页 URL 获取文章内容（自动提取正文）
- 从本地文件读取笔记（Markdown、TXT、HTML）
- 自动提取网页正文，去除广告和导航
- 保存网页图片到本地
- 生成内容摘要
- SQLite 数据库存储笔记
- 导出为 Markdown 格式

## 安装依赖

```bash
pip install requests beautifulsoup4 lxml readability-lxml
```

## 使用方法

### 初始化数据库

```bash
python3 scripts/get_notes.py --init
```

### 获取网页笔记

```bash
python3 scripts/get_notes.py "https://example.com/article"

# 保存图片
python3 scripts/get_notes.py "https://example.com/article" --save-images
```

### 读取本地文件

```bash
python3 scripts/get_notes.py --file /path/to/note.md
python3 scripts/get_notes.py --file /path/to/note.txt
python3 scripts/get_notes.py --file /path/to/note.html
```

### 列出笔记

```bash
python3 scripts/get_notes.py --list
python3 scripts/get_notes.py --list --limit 20
```

### 导出笔记

```bash
python3 scripts/get_notes.py --export 1
```

## 文件结构

```
get-notes/
├── SKILL.md              # 技能文档
├── README.md             # 本文件
└── scripts/
    ├── get_notes.py      # 主脚本
    ├── notes.db          # SQLite 数据库（运行后生成）
    └── images/           # 下载的图片（运行后生成）
```

## 数据库结构

笔记存储在 SQLite 数据库中，包含以下字段：

- `id` - 笔记唯一 ID
- `source` - 来源类型（url/file/api）
- `source_url` - 原始 URL 或文件路径
- `title` - 标题
- `content` - 正文内容
- `content_html` - HTML 格式内容
- `summary` - 摘要
- `author` - 作者
- `published_at` - 发布时间
- `fetched_at` - 获取时间
- `images` - 图片路径列表（JSON）
- `tags` - 标签（JSON）
- `metadata` - 额外元数据（JSON）

## 许可证

MIT
