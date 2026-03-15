#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IU Comment Scraper - SQLite 版本
从 berriz.in 网站爬取 IU 相关内容的回复/评论，并保存到 SQLite 数据库

使用方式：
1. 使用 OpenClaw browser 工具获取渲染后的页面 HTML
2. 将 HTML 保存为文件，作为参数传入此脚本
3. 脚本解析 HTML 并保存到 SQLite 数据库

或者直接使用 OpenClaw sessions_spawn 调用此 skill
"""

import sqlite3
import re
import sys
import os
import json
from datetime import datetime
from html.parser import HTMLParser

# 配置
BASE_URL = "https://berriz.in/zh-Hans/iu/archive/"
MAX_COMMENTS = 50
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'iu_comments.db')

class CommentParser(HTMLParser):
    """解析 HTML 中的评论内容"""
    
    def __init__(self):
        super().__init__()
        self.comments = []
        self.current_data = ""
        self.in_comment = False
        self.comment_depth = 0
        self.tag_stack = []
        
        # 可能的评论相关 class 和 id
        self.comment_indicators = [
            'comment', 'reply', 'response', 'post', 'message',
            'content', 'text', 'body', 'article', 'section',
            'user', 'author', 'nickname', 'username',
            'time', 'date', 'created', 'updated',
            'like', 'count', 'vote', 'star', 'rating',
            'list', 'item', 'card', 'wrapper', 'container'
        ]
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_attr = attrs_dict.get('class', '').lower()
        id_attr = attrs_dict.get('id', '').lower()
        
        self.tag_stack.append(tag)
        
        # 检查是否进入评论区域
        all_attrs = class_attr + ' ' + id_attr
        if any(ind in all_attrs for ind in self.comment_indicators):
            if not self.in_comment:
                self.in_comment = True
                self.comment_depth = len(self.tag_stack)
                self.current_data = ""
                
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
            
        # 如果离开评论区域，保存数据
        if self.in_comment and len(self.tag_stack) < self.comment_depth:
            if self.current_data.strip():
                text = self.current_data.strip()
                if len(text) > 20 and len(text) < 5000:  # 过滤太短或太长的内容
                    # 过滤掉明显的非评论内容
                    if not self._is_noise(text):
                        self.comments.append({
                            'text': text[:2000],
                            'author': 'Unknown',
                            'created_at': datetime.now().isoformat(),
                            'page_url': BASE_URL
                        })
            self.in_comment = False
            self.current_data = ""
            
    def handle_data(self, data):
        if self.in_comment:
            self.current_data += data
    
    def _is_noise(self, text):
        """检查是否是噪音内容"""
        noise_keywords = [
            'copyright', 'ⓒ', 'Kakao', 'privacy', 'terms', 'policy',
            '使用条款', '隐私政策', '营业执照', '客服中心', '咨询电话',
            'service@', 'support@', '.woff', '.css', '.js', 'static',
            'self.__next_f', 'push(', 'function', 'webpack'
        ]
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in noise_keywords)

def extract_json_data(html):
    """尝试从页面中提取 JSON 数据"""
    comments = []
    
    # 查找可能的 JSON 数据块
    json_patterns = [
        r'"comment[^"]*"\s*:\s*"([^"]+)"',
        r'"content[^"]*"\s*:\s*"([^"]+)"',
        r'"text[^"]*"\s*:\s*"([^"]+)"',
        r'"message[^"]*"\s*:\s*"([^"]+)"',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            text = match.strip()
            if len(text) > 20 and len(text) < 2000:
                comments.append({
                    'text': text,
                    'author': 'Unknown',
                    'created_at': datetime.now().isoformat(),
                    'page_url': BASE_URL
                })
    
    return comments

def parse_comments(html):
    """解析评论数据"""
    comments = []
    
    # 方法 1: 尝试提取 JSON 数据
    json_comments = extract_json_data(html)
    if json_comments:
        print(f"✓ 从 JSON 中提取到 {len(json_comments)} 条评论")
        return json_comments[:MAX_COMMENTS]
    
    # 方法 2: 使用 HTML 解析器
    parser = CommentParser()
    try:
        parser.feed(html)
    except Exception as e:
        print(f"⚠ HTML 解析失败：{e}")
    
    if parser.comments:
        print(f"✓ 从 HTML 结构中提取到 {len(parser.comments)} 条评论")
        # 去重
        seen = set()
        unique_comments = []
        for c in parser.comments:
            text_hash = hash(c['text'][:100])
            if text_hash not in seen:
                seen.add(text_hash)
                unique_comments.append(c)
        return unique_comments[:MAX_COMMENTS]
    
    return comments

def create_database(db_path):
    """创建 SQLite 数据库和表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS iu_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_text TEXT NOT NULL,
            author TEXT,
            created_at TEXT,
            page_url TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_author ON iu_comments(author)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON iu_comments(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fetched_at ON iu_comments(fetched_at)")
    
    conn.commit()
    print(f"✓ 数据库已创建：{db_path}")
    return conn

def save_comments(conn, comments):
    """保存评论到数据库"""
    cursor = conn.cursor()
    saved_count = 0
    
    for comment in comments:
        try:
            cursor.execute("""
                INSERT INTO iu_comments (comment_text, author, created_at, page_url)
                VALUES (?, ?, ?, ?)
            """, (comment['text'], comment['author'], comment['created_at'], comment['page_url']))
            saved_count += 1
        except Exception as e:
            print(f"⚠ 保存失败：{e}")
            continue
    
    conn.commit()
    return saved_count

def count_comments(conn):
    """统计评论数量"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM iu_comments")
    return cursor.fetchone()[0]

def query_comments(conn, limit=10):
    """查询最新评论"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, author, substr(comment_text, 1, 60), created_at 
        FROM iu_comments 
        ORDER BY fetched_at DESC 
        LIMIT ?
    """, (limit,))
    return cursor.fetchall()

def main(html_content=None, db_path=None):
    """主函数"""
    print("=" * 50)
    print("IU Comment Scraper - SQLite 版本")
    print("=" * 50)
    
    # 确定数据库路径
    if db_path is None:
        db_path = DB_PATH
    
    # 1. 获取或读取 HTML 内容
    if html_content is None:
        # 检查是否有命令行参数
        if len(sys.argv) > 1:
            html_file = sys.argv[1]
            if os.path.exists(html_file):
                print(f"\n1. 读取 HTML 文件：{html_file}")
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                print(f"✓ HTML 读取成功 (大小：{len(html_content)} 字节)")
            else:
                print(f"✗ 文件不存在：{html_file}")
                sys.exit(1)
        else:
            print("\n使用方法:")
            print("  python3 scrape_iu_comments_sqlite.py <html_file>")
            print("\n或者在 Python 中直接调用:")
            print("  from scrape_iu_comments_sqlite import main")
            print("  main(html_content='<html>...</html>')")
            return
    else:
        print(f"\n1. 处理 HTML 内容 (大小：{len(html_content)} 字节)")
    
    # 2. 解析评论
    print("\n2. 解析评论数据...")
    comments = parse_comments(html_content)
    
    if not comments:
        print("⚠ 未找到评论数据")
        print("\n提示：")
        print("  - 网站内容可能是动态加载的")
        print("  - 请使用 OpenClaw browser 工具获取渲染后的页面")
        print("  - 或者检查 HTML 文件是否包含完整内容")
    else:
        print(f"✓ 解析到 {len(comments)} 条评论")
    
    # 3. 保存到数据库
    print(f"\n3. 保存数据到 SQLite...")
    conn = create_database(db_path)
    
    saved_count = save_comments(conn, comments)
    print(f"✓ 成功保存 {saved_count} 条评论")
    
    # 4. 验证数据
    print(f"\n4. 验证数据...")
    total = count_comments(conn)
    print(f"✓ 数据库中共有 {total} 条评论")
    
    if total > 0:
        print("\n最新数据预览:")
        rows = query_comments(conn, 5)
        for row in rows:
            print(f"  [{row[0]}] {row[1]}: {row[2]}... ({row[3]})")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    
    return {
        'db_path': db_path,
        'total_comments': total,
        'saved_count': saved_count,
        'comments': comments
    }

if __name__ == '__main__':
    result = main()
    print(f"\n结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
