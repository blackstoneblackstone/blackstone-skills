#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IU Comment Scraper - OpenClaw 完整集成脚本
自动使用 OpenClaw browser 工具获取页面并保存到 SQLite 数据库

这个脚本设计为在 OpenClaw 主会话中直接调用
"""

import os
import sys
import json
import time
from datetime import datetime

# 配置
BASE_URL = "https://berriz.in/zh-Hans/iu/archive/"
MAX_COMMENTS = 50
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'iu_comments.db')
OUTPUT_DIR = SCRIPT_DIR

# 导入处理模块
sys.path.insert(0, SCRIPT_DIR)
from scrape_iu_comments_sqlite import parse_comments, create_database, save_comments, count_comments, query_comments

def fetch_with_browser(url):
    """
    使用 OpenClaw browser 工具获取页面
    
    在 OpenClaw 环境中，这会调用 browser 工具
    返回 HTML 内容
    """
    print(f"🌐 打开浏览器：{url}")
    
    # 这里需要调用 OpenClaw browser 工具
    # 在实际 OpenClaw 会话中，应该使用:
    # browser action=open targetUrl=<url>
    # browser action=snapshot
    
    # 由于这是在 Python 脚本中，我们需要通过 subprocess 调用 OpenClaw
    # 或者由调用者提供 browser 工具的支持
    
    # 返回 None 表示需要调用者提供 browser 支持
    return None

def process_html_to_db(html_content, db_path=None):
    """处理 HTML 并保存到数据库"""
    if db_path is None:
        db_path = DB_PATH
    
    print("=" * 60)
    print("💕 IU Comment Scraper - SQLite 版本")
    print("=" * 60)
    
    # 1. 解析评论
    print(f"\n📊 解析评论数据...")
    print(f"   HTML 大小：{len(html_content):,} 字节")
    comments = parse_comments(html_content)
    
    if not comments:
        print("⚠️  未找到评论数据")
        print("\n提示:")
        print("  - 网站内容可能是动态加载的")
        print("  - 请确保使用 browser 工具获取渲染后的页面")
        return {
            'success': False,
            'message': '未找到评论数据',
            'comments_count': 0,
            'saved_count': 0
        }
    
    print(f"✅ 解析到 {len(comments)} 条评论")
    
    # 2. 保存到数据库
    print(f"\n💾 保存数据到 SQLite...")
    print(f"   数据库：{db_path}")
    conn = create_database(db_path)
    
    saved_count = save_comments(conn, comments)
    print(f"✅ 成功保存 {saved_count} 条评论")
    
    # 3. 验证数据
    print(f"\n📈 验证数据...")
    total = count_comments(conn)
    print(f"✅ 数据库中共有 {total} 条评论")
    
    # 4. 获取预览
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
        'db_path': db_path,
        'total_comments': total,
        'saved_count': saved_count,
        'comments_count': len(comments),
        'preview': preview
    }

def main(html_content=None, db_path=None):
    """
    主函数
    
    参数:
        html_content: HTML 内容字符串（可选，如果为 None 则从文件读取）
        db_path: SQLite 数据库路径（可选）
    
    返回:
        dict: 处理结果
    """
    
    # 如果提供了 HTML 内容，直接处理
    if html_content:
        return process_html_to_db(html_content, db_path)
    
    # 否则从文件读取
    html_file = None
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        # 查找最近的 HTML 文件
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith('.html') or f.endswith('.htm'):
                html_file = os.path.join(OUTPUT_DIR, f)
                break
    
    if html_file and os.path.exists(html_file):
        print(f"📄 读取 HTML 文件：{html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return process_html_to_db(html_content, db_path)
    
    # 没有 HTML 内容，显示使用说明
    print("💕 IU Comment Scraper - OpenClaw 集成版本")
    print("=" * 60)
    print("\n使用方法:")
    print("\n1. 在 OpenClaw 中调用:")
    print("   - 使用 browser 工具获取页面")
    print("   - 调用此脚本处理 HTML 内容")
    print("\n2. 命令行运行:")
    print(f"   python3 {os.path.basename(__file__)} page.html")
    print("\n3. Python 调用:")
    print("   from run_openclaw import main")
    print("   result = main(html_content='<html>...</html>')")
    
    return None

if __name__ == '__main__':
    result = main()
    if result:
        print(f"\n📊 结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
