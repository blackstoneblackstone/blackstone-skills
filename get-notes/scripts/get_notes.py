#!/usr/bin/env python3
"""
Get Notes - 笔记获取工具
从网页、文件、API 等多种来源获取笔记内容
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Optional, List, Dict, Any

# 配置
SCRIPT_DIR = Path(__file__).parent.resolve()
DB_PATH = SCRIPT_DIR / "notes.db"
IMAGES_DIR = SCRIPT_DIR / "images"
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
AUTO_EXTRACT_CONTENT = True
GENERATE_SUMMARY = True


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
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
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_source ON notes(source)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_notes_fetched_at ON notes(fetched_at)
    """)

    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")


def save_note(data: Dict[str, Any]) -> int:
    """保存笔记到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notes (source, source_url, title, content, content_html, summary, author, published_at, images, tags, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('source', 'unknown'),
        data.get('source_url', ''),
        data.get('title', ''),
        data.get('content', ''),
        data.get('content_html', ''),
        data.get('summary', ''),
        data.get('author', ''),
        data.get('published_at', ''),
        json.dumps(data.get('images', []), ensure_ascii=False),
        json.dumps(data.get('tags', []), ensure_ascii=False),
        json.dumps(data.get('metadata', {}), ensure_ascii=False)
    ))

    note_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return note_id


def fetch_url(url: str, save_images: bool = False) -> Optional[Dict[str, Any]]:
    """从 URL 获取内容"""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ 请先安装依赖: pip install requests beautifulsoup4")
        return None

    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    print(f"🌐 正在获取: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

    html = response.text
    soup = BeautifulSoup(html, 'lxml')

    # 提取标题
    title = soup.title.string.strip() if soup.title else ''

    # 尝试提取正文
    content = ''
    content_html = ''

    if AUTO_EXTRACT_CONTENT:
        try:
            from readability import Document
            doc = Document(html)
            content_html = doc.summary()
            content = BeautifulSoup(content_html, 'lxml').get_text(separator='\n').strip()
            # 如果 readability 提供了标题，使用它
            doc_title = doc.title()
            if doc_title:
                title = doc_title
        except ImportError:
            print("⚠️ readability-lxml 未安装，使用简单提取模式")
            # 简单提取：获取 body 文本
            body = soup.find('body')
            if body:
                # 移除脚本和样式
                for tag in body(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                content = body.get_text(separator='\n').strip()
                content_html = str(body)
    else:
        body = soup.find('body')
        if body:
            content = body.get_text(separator='\n').strip()
            content_html = str(body)

    # 清理内容
    content = re.sub(r'\n{3,}', '\n\n', content)

    # 提取作者
    author = ''
    author_meta = soup.find('meta', attrs={'name': 'author'})
    if author_meta:
        author = author_meta.get('content', '')

    # 提取发布时间
    published_at = ''
    for meta_name in ['article:published_time', 'publishdate', 'date']:
        meta = soup.find('meta', attrs={'property': meta_name}) or soup.find('meta', attrs={'name': meta_name})
        if meta:
            published_at = meta.get('content', '')
            break

    # 下载图片
    images = []
    if save_images:
        IMAGES_DIR.mkdir(exist_ok=True)
        img_tags = soup.find_all('img')
        for idx, img in enumerate(img_tags[:20]):  # 最多下载 20 张图片
            img_url = img.get('src') or img.get('data-src')
            if img_url:
                img_url = urljoin(url, img_url)
                try:
                    img_response = requests.get(img_url, headers=headers, timeout=10)
                    if img_response.status_code == 200:
                        # 确定文件扩展名
                        content_type = img_response.headers.get('content-type', '')
                        ext = '.jpg'
                        if 'png' in content_type:
                            ext = '.png'
                        elif 'gif' in content_type:
                            ext = '.gif'
                        elif 'webp' in content_type:
                            ext = '.webp'

                        img_filename = f"temp_{idx}{ext}"
                        img_path = IMAGES_DIR / img_filename
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        images.append(str(img_path.relative_to(SCRIPT_DIR)))
                        print(f"  📸 已下载图片: {img_filename}")
                except Exception as e:
                    print(f"  ⚠️ 下载图片失败: {img_url}")

    # 生成摘要
    summary = ''
    if GENERATE_SUMMARY and content:
        # 简单的摘要生成：取前 200 个字符
        summary = content[:200].strip()
        if len(content) > 200:
            summary += '...'

    return {
        'source': 'url',
        'source_url': url,
        'title': title,
        'content': content,
        'content_html': content_html,
        'summary': summary,
        'author': author,
        'published_at': published_at,
        'images': images,
        'tags': [],
        'metadata': {
            'fetch_time': datetime.now().isoformat(),
            'content_length': len(content)
        }
    }


def fetch_file(file_path: str) -> Optional[Dict[str, Any]]:
    """从本地文件获取内容"""
    path = Path(file_path)

    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return None

    print(f"📄 正在读取文件: {file_path}")

    content = ''
    content_html = ''
    title = path.stem

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(path, 'r', encoding='gbk') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None

    # 根据文件类型处理
    suffix = path.suffix.lower()

    if suffix == '.html' or suffix == '.htm':
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'lxml')
            title = soup.title.string.strip() if soup.title else title
            content_html = content
            # 提取纯文本
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n').strip()
        except ImportError:
            pass
    elif suffix == '.md' or suffix == '.markdown':
        # Markdown 文件，尝试提取标题
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

    # 生成摘要
    summary = ''
    if GENERATE_SUMMARY and content:
        summary = content[:200].strip()
        if len(content) > 200:
            summary += '...'

    return {
        'source': 'file',
        'source_url': str(path.absolute()),
        'title': title,
        'content': content,
        'content_html': content_html,
        'summary': summary,
        'author': '',
        'published_at': '',
        'images': [],
        'tags': [],
        'metadata': {
            'file_size': path.stat().st_size,
            'fetch_time': datetime.now().isoformat()
        }
    }


def export_to_markdown(note_id: int, output_path: Optional[str] = None):
    """导出笔记为 Markdown 文件"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ 笔记不存在: {note_id}")
        return

    # 解析数据
    columns = ['id', 'source', 'source_url', 'title', 'content', 'content_html',
               'summary', 'author', 'published_at', 'fetched_at', 'images', 'tags', 'metadata']
    note = dict(zip(columns, row))

    images = json.loads(note['images']) if note['images'] else []

    # 生成 Markdown
    md_content = f"""# {note['title'] or '无标题'}

**来源**: {note['source_url']}  
**来源类型**: {note['source']}  
**作者**: {note['author'] or '未知'}  
**获取时间**: {note['fetched_at']}

"""

    if note['summary']:
        md_content += f"""## 摘要

{note['summary']}

"""

    md_content += f"""## 正文

{note['content']}

"""

    if images:
        md_content += """## 图片

"""
        for img in images:
            md_content += f"- {img}\n"

    # 保存文件
    if output_path is None:
        output_path = SCRIPT_DIR / f"note_{note_id}.md"
    else:
        output_path = Path(output_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"✅ 已导出到: {output_path}")


def list_notes(limit: int = 10):
    """列出最近的笔记"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, source, source_url, fetched_at
        FROM notes
        ORDER BY fetched_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 暂无笔记")
        return

    print(f"\n📚 最近 {len(rows)} 条笔记:\n")
    print(f"{'ID':<5} {'标题':<40} {'来源':<10} {'获取时间'}")
    print("-" * 80)

    for row in rows:
        note_id, title, source, url, fetched_at = row
        title = (title[:37] + '...') if title and len(title) > 40 else (title or '无标题')
        print(f"{note_id:<5} {title:<40} {source:<10} {fetched_at}")


def main():
    parser = argparse.ArgumentParser(description='Get Notes - 笔记获取工具')
    parser.add_argument('url', nargs='?', help='要获取的网页 URL')
    parser.add_argument('--file', '-f', help='从本地文件读取')
    parser.add_argument('--api', help='从 API 接口获取')
    parser.add_argument('--save-images', '-i', action='store_true', help='保存图片')
    parser.add_argument('--export', '-e', type=int, help='导出指定 ID 的笔记为 Markdown')
    parser.add_argument('--list', '-l', action='store_true', help='列出最近的笔记')
    parser.add_argument('--limit', type=int, default=10, help='列出笔记的数量限制')
    parser.add_argument('--init', action='store_true', help='初始化数据库')

    args = parser.parse_args()

    # 初始化数据库
    if args.init or not DB_PATH.exists():
        init_database()

    if args.list:
        list_notes(args.limit)
        return

    if args.export:
        export_to_markdown(args.export)
        return

    # 获取笔记
    data = None

    if args.file:
        data = fetch_file(args.file)
    elif args.api:
        print("⚠️ API 功能需要自定义实现")
        return
    elif args.url:
        data = fetch_url(args.url, save_images=args.save_images)
    else:
        parser.print_help()
        return

    if data:
        note_id = save_note(data)
        print(f"\n✅ 笔记已保存，ID: {note_id}")
        print(f"   标题: {data.get('title', '无标题')}")
        print(f"   内容长度: {len(data.get('content', ''))} 字符")

        # 自动导出为 Markdown
        export_to_markdown(note_id)


if __name__ == '__main__':
    main()
