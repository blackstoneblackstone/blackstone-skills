#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IU Comment Scraper - API 版本
直接调用 berriz.in API 获取数据，支持翻译和图片下载

使用方式:
    python3 iu_api_scraper.py
"""

import os
import sys
import json
import time
import sqlite3
import hashlib
import requests
import random
from datetime import datetime
from pathlib import Path
import re

# ==================== 配置 ====================

# API 配置
LIST_API = "https://svc-api.berriz.in/service/v2/community/5/artist/archive"
REPLY_API = "https://svc-api.berriz.in/service/v1/comment/{comment_id}/replies"
COMMENT_DETAIL_API = "https://svc-api.berriz.in/service/v1/comment/comments/{comment_id}"

# 默认请求头（不需要 Cookie，公开 API）
# 使用常见的 User-Agent 避免被封
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]

def get_headers():
    """获取请求头，随机 User-Agent 模拟真人"""
    import random
    return {
        "accept": "application/json",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "user-agent": random.choice(USER_AGENTS),
        "referer": "https://berriz.in/",
        "origin": "https://berriz.in",
    }

# 数据库配置
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "iu_comments.db"
IMAGES_DIR = SCRIPT_DIR / "images"

# 翻译配置（使用免费翻译 API）
TRANSLATE_API = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=ko&tl=zh-CN&dt=t&q={text}"

# 抓取配置
MAX_POSTS = 50  # 最多抓取多少个帖子
PAGE_SIZE = 20  # 每页多少条

# 防封配置
REQUEST_DELAY_MIN = 0.5  # 最小延迟（秒）
REQUEST_DELAY_MAX = 1.5  # 最大延迟（秒）
PAGE_DELAY_MIN = 1.0  # 页间最小延迟（秒）
PAGE_DELAY_MAX = 3.0  # 页间最大延迟（秒）

# ==================== 工具函数 ====================



def contains_korean(text):
    """检查是否包含韩文"""
    if not text:
        return False
    korean_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\ua960-\ua97f]')
    return bool(korean_pattern.search(text))

def translate_text(text):
    """翻译韩文到中文"""
    if not text or not contains_korean(text):
        return text
    
    try:
        # 简单处理：只翻译韩文部分
        encoded_text = requests.utils.quote(text)
        url = TRANSLATE_API.format(text=encoded_text)
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result = ""
            for item in data[0]:
                if item[0]:
                    result += item[0]
            return result
    except Exception as e:
        print(f"⚠️ 翻译失败：{e}")
    
    return text

def download_image(url, post_id, comment_id):
    """下载图片并保存到本地"""
    try:
        # 生成唯一文件名
        img_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        ext = url.split(".")[-1].split("?")[0] if "." in url else "jpg"
        filename = f"{post_id}_{comment_id}_{img_hash}.{ext}"
        filepath = IMAGES_DIR / filename
        
        # 如果已存在，跳过
        if filepath.exists():
            return str(filepath)
        
        # 下载
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return str(filepath)
    except Exception as e:
        print(f"⚠️ 图片下载失败 {url}: {e}")
    
    return None

def create_database(db_path):
    """创建数据库和表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 主表：帖子和回复
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS iu_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id TEXT NOT NULL,
            comment_id TEXT NOT NULL,
            
            -- 原始帖子信息
            post_author TEXT,
            post_author_ko TEXT,
            post_content TEXT,
            post_content_zh TEXT,
            post_created_at TEXT,
            
            -- IU 回复信息
            iu_reply_content TEXT,
            iu_reply_content_zh TEXT,
            iu_reply_created_at TEXT,
            
            -- 图片
            images TEXT,
            
            -- 元数据
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(post_id, comment_id)
        )
    """)
    
    # 索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_post_id ON iu_comments(post_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comment_id ON iu_comments(comment_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fetched_at ON iu_comments(fetched_at)")
    
    conn.commit()
    return conn

# ==================== 核心抓取逻辑 ====================

def fetch_post_list(page=1, page_size=PAGE_SIZE):
    """获取帖子列表"""
    params = {
        "communityId": 5,
        "pageSize": page_size,
        "languageCode": "zh-Hans",
    }
    
    try:
        resp = requests.get(LIST_API, headers=get_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # 数据结构：data.contents 是列表
        return data.get("data", {}).get("contents", [])
    except Exception as e:
        print(f"❌ 获取帖子列表失败：{e}")
        return []

def fetch_comment_replies(comment_id):
    """获取评论的回复（包括 IU 的回复）"""
    url = REPLY_API.format(comment_id=comment_id)
    params = {
        "contentTypeCode": 102,
        "contentId": comment_id,
        "pageSize": 50,
        "languageCode": "zh-Hans",
    }
    
    try:
        resp = requests.get(url, headers=get_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("list", [])
    except Exception as e:
        print(f"❌ 获取评论回复失败 {comment_id}: {e}")
        return []

def extract_text_from_content(content_obj):
    """从内容对象中提取文本"""
    if not content_obj:
        return ""
    
    if isinstance(content_obj, str):
        return content_obj
    
    if isinstance(content_obj, dict):
        # 尝试多个可能的字段
        for key in ["text", "content", "message", "body"]:
            if key in content_obj:
                return content_obj[key]
    
    return str(content_obj)

def extract_images_from_content(content_obj):
    """从内容对象中提取图片 URL"""
    images = []
    
    if not content_obj:
        return images
    
    if isinstance(content_obj, dict):
        # 查找图片字段
        for key in ["images", "attachments", "media", "photos"]:
            if key in content_obj and isinstance(content_obj[key], list):
                for item in content_obj[key]:
                    if isinstance(item, str):
                        images.append(item)
                    elif isinstance(item, dict) and "url" in item:
                        images.append(item["url"])
    
    return images

def process_post(post_data):
    """处理单个帖子数据（这是 IU 的回复，需要获取原帖）"""
    result = {
        "post_id": post_data.get("postId", ""),
        "comment_id": post_data.get("contentId", ""),
        
        "post_author": None,
        "post_author_ko": None,
        "post_content": None,
        "post_content_zh": None,
        "post_created_at": None,
        
        "iu_reply_content": None,
        "iu_reply_content_zh": None,
        "iu_reply_created_at": None,
        
        "images": [],
    }
    
    # IU 回复的内容（body 字段）
    iu_content = post_data.get("body", "")
    result["iu_reply_content"] = iu_content if iu_content else None
    
    # 翻译 IU 回复
    if result["iu_reply_content"] and contains_korean(result["iu_reply_content"]):
        result["iu_reply_content_zh"] = translate_text(result["iu_reply_content"])
    
    # IU 回复时间
    result["iu_reply_created_at"] = post_data.get("createdAt", "")
    
    # 原帖信息（从 replyInfo 获取）
    parent_id = None
    reply_info = post_data.get("replyInfo", {})
    if reply_info.get("isReply"):
        result["post_author"] = reply_info.get("authorName", "Unknown")
        result["post_author_ko"] = result["post_author"] if contains_korean(result["post_author"] or "") else None
        
        # 原帖 ID（parentCommentSeq）- 用于获取原帖内容
        parent_id = reply_info.get("parentCommentSeq", "")
        if parent_id:
            result["comment_id"] = str(parent_id)
    
    # 提取图片
    images = []
    image_url = post_data.get("imageUrl")
    if image_url:
        images.append(image_url)
    
    # 下载图片
    downloaded_images = []
    for img_url in images[:10]:
        saved_path = download_image(img_url, result["post_id"], result["comment_id"])
        if saved_path:
            downloaded_images.append(saved_path)
    
    result["images"] = downloaded_images
    
    # 获取原帖详情（使用 parentCommentSeq 调用 comment detail API）
    if parent_id:
        time.sleep(0.3)
        original_post = fetch_original_post(str(parent_id))
        if original_post:
            # 原帖内容在 element.text
            elem = original_post.get("element", {})
            result["post_content"] = elem.get("text", "")
            result["post_created_at"] = elem.get("createdAt", "")
            
            # 原帖作者（从原帖 API 获取更准确）
            author = original_post.get("author", {})
            result["post_author"] = author.get("authorDisplayName", result["post_author"])
            result["post_author_ko"] = result["post_author"] if contains_korean(result["post_author"] or "") else None
            
            # 翻译原帖内容
            if result["post_content"] and contains_korean(result["post_content"]):
                result["post_content_zh"] = translate_text(result["post_content"])
            
            # 原帖图片
            media = original_post.get("media", {})
            photos = media.get("photo", [])
            for photo in photos[:5]:
                if isinstance(photo, dict) and "url" in photo:
                    saved_path = download_image(photo["url"], result["post_id"], result["comment_id"])
                    if saved_path and saved_path not in result["images"]:
                        result["images"].append(saved_path)
    
    return result

def fetch_original_post(parent_comment_seq):
    """获取原帖详情（通过 comment detail API）"""
    url = COMMENT_DETAIL_API.format(comment_id=parent_comment_seq)
    params = {"languageCode": "zh-Hans"}
    
    try:
        resp = requests.get(url, headers=get_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # 返回 data.content 对象
        return data.get("data", {}).get("content", {})
    except Exception as e:
        print(f"⚠️ 获取原帖失败 {parent_comment_seq}: {e}")
    
    return None



def save_to_database(conn, data):
    """保存数据到数据库"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO iu_comments 
            (post_id, comment_id, post_author, post_author_ko, post_content, post_content_zh,
             post_created_at, iu_reply_content, iu_reply_content_zh, iu_reply_created_at, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["post_id"],
            data["comment_id"],
            data["post_author"],
            data["post_author_ko"],
            data["post_content"],
            data["post_content_zh"],
            data["post_created_at"],
            data["iu_reply_content"],
            data["iu_reply_content_zh"],
            data["iu_reply_created_at"],
            json.dumps(data["images"], ensure_ascii=False),
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ 保存失败：{e}")
        return False

# ==================== 主函数 ====================

def scrape_iu_comments(max_posts=MAX_POSTS):
    """主函数：抓取 IU 评论数据"""
    print("=" * 60)
    print("💕 IU Comment Scraper - API 版本")
    print("=" * 60)
    
    # 创建数据库
    conn = create_database(DB_PATH)
    cursor = conn.cursor()
    print(f"\n📁 数据库：{DB_PATH}")
    print(f"📂 图片目录：{IMAGES_DIR}")
    
    # 获取已保存的 comment_id 列表（避免重复抓取）
    cursor.execute("SELECT comment_id FROM iu_comments")
    existing_ids = set(row[0] for row in cursor.fetchall())
    print(f"📊 数据库中已有 {len(existing_ids)} 条数据")
    
    total_saved = 0
    total_skipped = 0
    total_posts = 0
    page = 1
    
    while total_posts < max_posts:
        print(f"\n📄 获取第 {page} 页...")
        posts = fetch_post_list(page=page)
        
        if not posts:
            print("⚠️ 没有更多数据了")
            break
        
        print(f"   获取到 {len(posts)} 条帖子")
        
        for i, post in enumerate(posts, 1):
            if total_posts >= max_posts:
                break
            
            comment_id = post.get("contentId", "")
            post_id = post.get("postId", "")
            
            # 检查是否已存在
            if comment_id in existing_ids:
                print(f"\n   [{total_posts + 1}] ⏭️  跳过已保存的帖子 {comment_id}")
                total_skipped += 1
                total_posts += 1
                continue
            
            print(f"\n   [{total_posts + 1}] 处理帖子 {comment_id}...")
            
            # 处理帖子
            data = process_post(post)
            
            # 保存数据库
            if save_to_database(conn, data):
                total_saved += 1
                existing_ids.add(comment_id)  # 添加到已存在列表
                print(f"   ✓ 已保存")
                
                # 显示摘要
                author = data["post_author"] or "Unknown"
                content_preview = (data["post_content"] or "")[:50].replace("\n", " ")
                iu_preview = (data["iu_reply_content"] or "无回复")[:30].replace("\n", " ")
                
                print(f"   👤 作者：{author}")
                print(f"   📝 内容：{content_preview}...")
                print(f"   💬 IU 回复：{iu_preview}...")
                if data["images"]:
                    print(f"   🖼️ 图片：{len(data['images'])} 张")
            
            total_posts += 1
            # 随机延迟，模拟真人操作
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        
        page += 1
        # 页间更大的随机延迟
        time.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
    
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✨ 完成！新保存 {total_saved} 条，跳过 {total_skipped} 条")
    print("=" * 60)
    
    return {
        "success": True,
        "total_saved": total_saved,
        "total_skipped": total_skipped,
        "db_path": str(DB_PATH),
        "images_dir": str(IMAGES_DIR),
    }

if __name__ == "__main__":
    result = scrape_iu_comments()
    print(f"\n📊 结果：{json.dumps(result, ensure_ascii=False, indent=2)}")
