#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IU Comment Scraper - OpenClaw Browser 集成版本
使用 OpenClaw browser 工具获取渲染后的页面，然后保存到 SQLite 数据库

这个脚本设计为通过 OpenClaw sessions_spawn 调用
"""

import os
import sys
import json
from datetime import datetime

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from scrape_iu_comments_sqlite import parse_comments, create_database, save_comments, count_comments, query_comments

# 配置
BASE_URL = "https://berriz.in/zh-Hans/iu/archive/"
MAX_COMMENTS = 50
DB_PATH = os.path.join(SCRIPT_DIR, 'iu_comments.db')

def scrape_with_openclaw_browser():
    """
    使用 OpenClaw browser 工具获取页面内容
    
    这个函数需要在 OpenClaw 环境中调用，使用 browser 工具
    返回渲染后的 HTML 内容
    """
    # 注意：这个函数应该在 OpenClaw 会话中通过 browser 工具调用
    # 这里提供一个接口说明
    
    print("请使用 OpenClaw browser 工具获取页面内容:")
    print("""
    browser action=open targetUrl=https://berriz.in/zh-Hans/iu/archive/
    browser action=snapshot
    """)
    
    return None

def process_html(html_content, db_path=None):
    """处理 HTML 内容并保存到数据库"""
    if db_path is None:
        db_path = DB_PATH
    
    print("=" * 50)
    print("IU Comment Scraper - 处理数据")
    print("=" * 50)
    
    # 1. 解析评论
    print(f"\n1. 解析评论数据...")
    print(f"   HTML 大小：{len(html_content)} 字节")
    comments = parse_comments(html_content)
    
    if not comments:
        print("⚠ 未找到评论数据")
        return {
            'success': False,
            'message': '未找到评论数据',
            'comments_count': 0
        }
    
    print(f"✓ 解析到 {len(comments)} 条评论")
    
    # 2. 保存到数据库
    print(f"\n2. 保存数据到 SQLite...")
    print(f"   数据库：{db_path}")
    conn = create_database(db_path)
    
    saved_count = save_comments(conn, comments)
    print(f"✓ 成功保存 {saved_count} 条评论")
    
    # 3. 验证数据
    print(f"\n3. 验证数据...")
    total = count_comments(conn)
    print(f"✓ 数据库中共有 {total} 条评论")
    
    # 4. 获取预览
    preview = []
    if total > 0:
        print("\n最新数据预览:")
        rows = query_comments(conn, 5)
        for row in rows:
            preview.append({
                'id': row[0],
                'author': row[1],
                'text': row[2],
                'created_at': row[3]
            })
            print(f"  [{row[0]}] {row[1]}: {row[2]}...")
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
    
    return {
        'success': True,
        'db_path': db_path,
        'total_comments': total,
        'saved_count': saved_count,
        'comments_count': len(comments),
        'preview': preview
    }

def main():
    """主函数 - 支持多种调用方式"""
    
    # 方式 1: 从文件读取 HTML
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
        if os.path.exists(html_file):
            print(f"读取 HTML 文件：{html_file}")
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            result = process_html(html_content)
            print(f"\n结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            print(f"文件不存在：{html_file}")
            sys.exit(1)
    
    # 方式 2: 从 stdin 读取 HTML
    if not sys.stdin.isatty():
        print("从 stdin 读取 HTML...")
        html_content = sys.stdin.read()
        result = process_html(html_content)
        print(f"\n结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    
    # 方式 3: 显示使用说明
    print("IU Comment Scraper - SQLite 版本")
    print("=" * 50)
    print("\n使用方法:")
    print("\n1. 从文件读取 HTML:")
    print(f"   python3 {os.path.basename(__file__)} page.html")
    print("\n2. 从 stdin 读取 HTML:")
    print("   cat page.html | python3 scrape_iu_comments_sqlite.py")
    print("\n3. 在 Python 中调用:")
    print("   from scrape_iu_comments_openclaw import process_html")
    print("   result = process_html(html_content)")
    print("\n4. 使用 OpenClaw browser 工具:")
    print("   - 先用 browser 工具获取页面 HTML")
    print("   - 保存为文件或通过 stdin 传入")
    print("   - 运行此脚本处理并保存")
    
    return None

if __name__ == '__main__':
    main()
