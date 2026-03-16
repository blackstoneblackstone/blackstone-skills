# Blog Publisher

将内容发布到黑石的 GitHub Pages 博客。

## 功能

- 从 Get 笔记获取文章并发布
- 从本地 Markdown 文件发布
- 直接输入内容发布
- 自动生成 Jekyll 格式
- 自动提交并推送到 GitHub

## 安装依赖

```bash
pip install requests
```

## 配置环境变量

```bash
export GETNOTE_API_KEY="your-api-key"
export GETNOTE_CLIENT_ID="your-client-id"
```

## 使用方法

### 从 Get 笔记发布

```bash
python3 scripts/publish.py --note "AI 吸血鬼"
```

### 从文件发布

```bash
python3 scripts/publish.py --file ~/article.md --title "文章标题"
```

### 直接发布

```bash
python3 scripts/publish.py --title "标题" --content "内容"
```

## 文件结构

```
blog-publisher/
├── SKILL.md              # 技能文档
├── README.md             # 本文件
└── scripts/
    └── publish.py        # 发布脚本
```
