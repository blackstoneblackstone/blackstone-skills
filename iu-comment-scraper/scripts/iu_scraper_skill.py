#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IU Comment Scraper Skill
完整的 OpenClaw skill 实现，可直接在会话中调用

使用方式:
    python3 iu_scraper_skill.py
    
或者在 OpenClaw 会话中:
    调用此脚本，它会自动使用 browser 工具获取页面并保存数据
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from html.parser import HTMLParser
import re

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
        self.current_comment = None
        self.current_data = ""
        self.tag_stack = []
        self.in_comment = False
        self.in_author = False
        self.in_text = False
        
        self.comment_indicators = ['comment-item', 'comment', 'reply', 'post', 'message']
        self.author_indicators = ['author', 'username', 'nickname', 'user']
        self.text_indicators = ['comment-text', 'text', 'content', 'body', 'message']
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_attr = attrs_dict.get('class', '').lower()
        
        self.tag_stack.append(tag)
        
        # 检查是否进入评论项
        if any(ind in class_attr for ind in self.comment_indicators):
            if not self.in_comment:
                self.in_comment = True
                self.current_comment = {'text': '', 'author': 'Unknown'}
                self.current_data = ""
        
        # 检查是否进入作者区域
        if self.in_comment and any(ind in class_attr for ind in self.author_indicators):
            self.in_author = True
            self.current_data = ""
        
        # 检查是否进入文本区域
        if self.in_comment and any(ind in class_attr for ind in self.text_indicators):
            self.in_text = True
            self.current_data = ""
    
    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        
        if self.in_comment:
            if self.in_author:
                if self.current_data.strip():
                    self.current_comment['author'] = self.current_data.strip()
                self.in_author = False
            
            if self.in_text:
                if self.current_data.strip():
                    self.current_comment['text'] += self.current_data.strip() + " "
                self.in_text = False
            
            # 检查是否离开评论项
            if tag == 'div' and self.current_comment and self.current_comment.get('text'):
                text = self.current_comment['text'].strip()
                if len(text) > 10 and len(text) < 5000 and not self._is_noise(text):
                    self.comments.append({
                        'text': text[:2000],
                        'author': self.current_comment['author'],
                        'created_at': datetime.now().isoformat(),
                        'page_url': BASE_URL
                    })
                self.current_comment = None
                self.in_comment = False
    
    def handle_data(self, data):
        if self.in_comment:
            self.current_data += data
    
    def _is_noise(self, text):
        noise_keywords = [
            'copyright', 'ⓒ', 'Kakao', 'privacy', 'terms', 'policy',
            '使用条款', '隐私政策', '营业执照', '客服中心', '咨询电话',
            'service@', 'support@', '.woff', '.css', '.js', 'static',
            'self.__next_f', 'push(', 'function', 'webpack'
        ]
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in noise_keywords)

def parse_comments(html):
    """解析评论数据"""
    parser = CommentParser()
    try:
        parser.feed(html)
    except Exception as e:
        print(f"⚠ HTML 解析失败：{e}")
    
    if parser.comments:
        # 去重
        seen = set()
        unique_comments = []
        for c in parser.comments:
            text_hash = hash(c['text'][:100])
            if text_hash not in seen:
                seen.add(text_hash)
                unique_comments.append(c)
        return unique_comments[:MAX_COMMENTS]
    
    return []

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
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_author ON iu_comments(author)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON iu_comments(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fetched_at ON iu_comments(fetched_at)")
    
    conn.commit()
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
        except:
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

def scrape_iu_comments(html_content=None):
    """
    主函数：爬取 IU 评论并保存到 SQLite 数据库
    
    参数:
        html_content: HTML 内容（如果为 None，需要从外部提供）
    
    返回:
        dict: 处理结果
    """
    if not html_content:
        return {
            'success': False,
            'message': '需要提供 HTML 内容',
            'hint': '请使用 OpenClaw browser 工具获取页面后传入 HTML 内容'
        }
    
    print("=" * 60)
    print("💕 IU Comment Scraper")
    print("=" * 60)
    
    # 1. 解析评论
    print(f"\n📊 解析评论数据...")
    print(f"   HTML 大小：{len(html_content):,} 字节")
    comments = parse_comments(html_content)
    
    if not comments:
        print("⚠️  未找到评论数据")
        return {
            'success': False,
            'message': '未找到评论数据',
            'comments_count': 0,
            'saved_count': 0
        }
    
    print(f"✅ 解析到 {len(comments)} 条评论")
    
    # 2. 保存到数据库
    print(f"\n💾 保存数据到 SQLite...")
    print(f"   数据库：{DB_PATH}")
    conn = create_database(DB_PATH)
    
    saved_count = save_comments(conn, comments)
    print(f"✅ 成功保存 {saved_count} 条评论")
    
    # 3. 验证数据
    total = count_comments(conn)
    print(f"📈 数据库中共有 {total} 条评论")
    
    # 4. 预览
    preview = []
    if total > 0:
        print("\n📋 最新数据预览:")
        rows = query_comments(conn, 5)
        for i, row in enumerate(rows, 1):
            preview.append({
                'id': row[0],
                'author': row[1],
                'text': row[2],
                'created_at': row[3]
            })
            text_preview = row[2][:50].replace('\n', ' ')
            print(f"   [{i}] {text_preview}...")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✨ 完成！")
    print("=" * 60)
    
    return {
        'success': True,
        'db_path': DB_PATH,
        'total_comments': total,
        'saved_count': saved_count,
        'comments_count': len(comments),
        'preview': preview
    }

def main():
    """命令行入口"""
    html_file = None
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    
    if html_file and os.path.exists(html_file):
        print(f"📄 读取 HTML 文件：{html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        result = scrape_iu_comments(html_content)
        print(f"\n📊 结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    
    print("💕 IU Comment Scraper Skill")
    print("=" * 60)
    print("\n使用方法:")
    print("\n1. 在 OpenClaw 会话中:")
    print("   - 使用 browser 工具获取页面 HTML")
    print("   - 调用 scrape_iu_comments(html_content)")
    print("\n2. 命令行:")
    print(f"   python3 {os.path.basename(__file__)} page.html")
    
    return None

if __name__ == '__main__':
    main()
