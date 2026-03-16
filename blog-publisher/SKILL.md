---
name: blog-publisher
description: 将内容发布到黑石的 GitHub Pages 博客 (blackstoneblackstone.github.io)。支持从 Get 笔记、本地文件或直接输入发布文章。需要发布博客文章时使用。
metadata: {"clawdbot":{"emoji":"📝","requires":{"anyBins":["git","ssh"]},"os":["linux","darwin","win32"]}}
---

# Blog Publisher - 博客发布工具

将内容发布到黑石的 GitHub Pages 博客。

## 功能

- ✅ 从 Get 笔记获取文章并发布
- ✅ 从本地 Markdown 文件发布
- ✅ 直接输入内容发布
- ✅ 自动生成 Jekyll 格式的前置元数据
- ✅ 自动提交并推送到 GitHub
- ✅ 图文文章图片自动上传（使用 Wrangler + R2，支持 Markdown 中的图片链接）

## 使用方法

### 在会话中调用

```
把这篇笔记发到我的博客
发布这篇文章到我的 blog
将 Get 笔记 "AI 吸血鬼" 发布到博客
```

### 命令行运行

```bash
cd /path/to/blog-publisher
python3 scripts/publish.py --note "笔记标题"           # 从 Get 笔记发布
python3 scripts/publish.py --file /path/to/article.md  # 从文件发布
python3 scripts/publish.py --title "标题" --content "内容"  # 直接发布
```

## 配置

编辑 `scripts/publish.py` 修改配置：

```python
# 博客仓库配置
BLOG_REPO = "git@github.com:blackstoneblackstone/blackstoneblackstone.github.io.git"
BLOG_LOCAL_PATH = Path.home() / ".blog-cache" / "blackstoneblackstone.github.io"

# Get 笔记 API 配置
GETNOTE_API_KEY = "your-api-key"
GETNOTE_CLIENT_ID = "your-client-id"

# 作者信息
AUTHOR = "黑石"
```

## 数据字段

| 字段 | 说明 | 默认值 |
|------|------|--------|
| title | 文章标题 | 必填 |
| date | 发布日期 | 当前时间 |
| categories | 分类 | ["随笔"] |
| tags | 标签 | [] |
| author | 作者 | 黑石 |
| excerpt | 摘要 | 自动提取前200字 |

## 文件结构

```
blog-publisher/
├── SKILL.md
├── README.md
└── scripts/
    └── publish.py      # 发布脚本
```

## 依赖安装

```bash
pip install requests
```

## 注意事项

### 🔑 SSH 密钥

确保已配置 GitHub SSH 密钥，或者设置 `GITHUB_TOKEN` 环境变量使用 HTTPS。

### 🖼️ 图片处理（图文文章）

如果 Markdown 文章包含图片链接，发布流程会：

1. **提取图片**：从 Markdown 内容中提取所有图片链接（支持 `![alt](url)` 和 `<img>` 标签）
2. **上传到 R2**：使用 Wrangler CLI 将图片上传到 Cloudflare R2
3. **替换 URL**：将图片链接替换为 R2 的公开 URL

**配置 R2 上传：**

```bash
# 设置 R2 存储桶名称
export BLOG_R2_BUCKET="your-blog-images-bucket"

# 设置图片域名（用于生成 URL）
export BLOG_IMAGE_DOMAIN="https://images.yourdomain.com"
```

**Wrangler 配置要求：**

确保本地已配置 Wrangler 并有权限访问 R2：
```bash
wrangler whoami  # 检查登录状态
wrangler r2 bucket list  # 检查 R2 权限
```

### 📝 文章格式

发布的文章会自动转换为 Jekyll 格式：

```markdown
---
layout: post
title: "文章标题"
date: 2026-03-16 10:30:00 +0800
categories: [分类]
tags: [标签]
author: 黑石
excerpt: 摘要...
---

正文内容...
```

## 示例

### 从 Get 笔记发布

```bash
python3 scripts/publish.py --note "AI 吸血鬼"
```

### 从文件发布

```bash
python3 scripts/publish.py --file ~/Documents/my-article.md --title "我的标题"
```

### 直接发布

```bash
python3 scripts/publish.py --title "新文章" --content "这里是文章内容..."
```
