# IU Comment Scraper

爬取 berriz.in 网站上 IU 回复的评论数据。

## 功能

- 获取帖子 ID、作者、内容
- 获取 IU 回复内容
- 韩文自动翻译中文
- 图片下载保存

## 使用

### OpenClaw 会话
```
给我 IU 的回帖
```

### 命令行
```bash
python3 scripts/iu_api_scraper.py
```

数据保存到 `scripts/iu_comments.db`，图片保存到 `scripts/images/`
