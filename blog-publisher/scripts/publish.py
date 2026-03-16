#!/usr/bin/env python3
"""
Blog Publisher - 博客发布工具
将内容发布到黑石的 GitHub Pages 博客
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import requests

# 配置
SCRIPT_DIR = Path(__file__).parent.resolve()
BLOG_REPO = "git@github.com:blackstoneblackstone/blackstoneblackstone.github.io.git"
BLOG_LOCAL_PATH = Path.home() / ".blog-cache" / "blackstoneblackstone.github.io"
SSH_KEY_PATH = Path.home() / ".ssh" / "id_ed25519"

# Get 笔记 API 配置
GETNOTE_API_KEY = os.getenv("GETNOTE_API_KEY", "")
GETNOTE_CLIENT_ID = os.getenv("GETNOTE_CLIENT_ID", "")

# 作者信息
AUTHOR = "黑石"


def run_git_command(cmd: list, cwd: Optional[Path] = None, env: Optional[Dict] = None) -> tuple:
    """运行 git 命令"""
    default_env = os.environ.copy()
    if env:
        default_env.update(env)
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=default_env,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def ensure_blog_repo() -> Path:
    """确保博客仓库存在"""
    if not BLOG_LOCAL_PATH.exists():
        print(f"📥 克隆博客仓库...")
        BLOG_LOCAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        env = {}
        if SSH_KEY_PATH.exists():
            env["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY_PATH}"
        
        code, stdout, stderr = run_git_command(
            ["git", "clone", BLOG_REPO, str(BLOG_LOCAL_PATH)],
            env=env
        )
        
        if code != 0:
            print(f"❌ 克隆失败: {stderr}")
            sys.exit(1)
        
        print(f"✅ 仓库已克隆到 {BLOG_LOCAL_PATH}")
    else:
        # 更新仓库
        print(f"🔄 更新博客仓库...")
        env = {}
        if SSH_KEY_PATH.exists():
            env["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY_PATH}"
        
        run_git_command(["git", "pull"], cwd=BLOG_LOCAL_PATH, env=env)
    
    return BLOG_LOCAL_PATH


def get_note_from_getnote(title_keyword: str) -> Optional[Dict[str, Any]]:
    """从 Get 笔记获取文章"""
    if not GETNOTE_API_KEY or not GETNOTE_CLIENT_ID:
        print("❌ 未配置 Get 笔记 API 密钥")
        return None
    
    headers = {
        'Authorization': GETNOTE_API_KEY,
        'X-Client-ID': GETNOTE_CLIENT_ID
    }
    
    try:
        # 搜索笔记
        response = requests.get(
            'https://openapi.biji.com/open/api/v1/resource/note/list?since_id=0',
            headers=headers,
            timeout=30
        )
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ 获取笔记列表失败: {data}")
            return None
        
        # 查找匹配的笔记
        for note in data.get('data', {}).get('notes', []):
            note_title = note.get('title', '')
            if title_keyword.lower() in note_title.lower():
                print(f"🔍 找到笔记: {note_title}")
                
                # 获取详情
                detail_resp = requests.get(
                    f"https://openapi.biji.com/open/api/v1/resource/note/detail?id={note['id']}",
                    headers=headers,
                    timeout=30
                )
                detail = detail_resp.json()
                
                if detail.get('success'):
                    return detail['data']['note']
        
        print(f"❌ 未找到包含 '{title_keyword}' 的笔记")
        return None
        
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def generate_front_matter(title: str, content: str, categories: list = None, tags: list = None) -> str:
    """生成 Jekyll 前置元数据"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S +0800")
    
    # 生成摘要（前200字）
    excerpt = content[:200].strip().replace('\n', ' ')
    if len(content) > 200:
        excerpt += "..."
    
    # 转义引号
    title_escaped = title.replace('"', '\\"')
    excerpt_escaped = excerpt.replace('"', '\\"')
    
    categories_str = ', '.join(categories) if categories else '随笔'
    tags_str = ', '.join(tags) if tags else ''
    
    front_matter = f"""---
layout: post
title: "{title_escaped}"
date: {date_str}
categories: [{categories_str}]
tags: [{tags_str}]
author: {AUTHOR}
excerpt: {excerpt_escaped}
---

"""
    return front_matter


def create_post_file(title: str, content: str, blog_path: Path, categories: list = None, tags: list = None) -> Path:
    """创建博客文章文件"""
    now = datetime.now()
    date_prefix = now.strftime("%Y-%m-%d")
    
    # 生成文件名
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    filename = f"{date_prefix}-{slug}.md"
    
    posts_dir = blog_path / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    file_path = posts_dir / filename
    
    # 生成完整内容
    front_matter = generate_front_matter(title, content, categories, tags)
    full_content = front_matter + content
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"✅ 文章已创建: {file_path}")
    return file_path


def commit_and_push(blog_path: Path, title: str):
    """提交并推送到 GitHub"""
    env = {}
    if SSH_KEY_PATH.exists():
        env["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY_PATH}"
    
    # 添加文件
    run_git_command(["git", "add", "."], cwd=blog_path, env=env)
    
    # 提交
    commit_msg = f"Add post: {title}\n\n🤖 Generated with [Qoder][https://qoder.com]"
    code, stdout, stderr = run_git_command(
        ["git", "commit", "-m", commit_msg],
        cwd=blog_path,
        env=env
    )
    
    if code != 0 and "nothing to commit" not in stderr.lower():
        print(f"⚠️ 提交警告: {stderr}")
    
    # 推送
    print(f"🚀 推送到 GitHub...")
    code, stdout, stderr = run_git_command(
        ["git", "push", "origin", "main"],
        cwd=blog_path,
        env=env
    )
    
    if code != 0:
        print(f"❌ 推送失败: {stderr}")
        return False
    
    print(f"✅ 推送成功!")
    return True


def publish_from_getnote(title_keyword: str):
    """从 Get 笔记发布"""
    note = get_note_from_getnote(title_keyword)
    if not note:
        return False
    
    title = note.get('title', '无标题')
    content = note.get('content', '')
    
    if not content:
        print("❌ 笔记内容为空")
        return False
    
    # 确保仓库
    blog_path = ensure_blog_repo()
    
    # 创建文章
    create_post_file(title, content, blog_path)
    
    # 提交推送
    if commit_and_push(blog_path, title):
        now = datetime.now().strftime("%Y-%m-%d")
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        print(f"\n🎉 发布成功!")
        print(f"🔗 https://blackstoneblackstone.github.io/{now.replace('-', '/')}/{slug}/")
        return True
    
    return False


def publish_from_file(file_path: str, title: Optional[str] = None):
    """从文件发布"""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 如果文件已有前置元数据，直接使用
    if content.startswith('---'):
        blog_path = ensure_blog_repo()
        now = datetime.now()
        date_prefix = now.strftime("%Y-%m-%d")
        
        # 提取标题
        if not title:
            match = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
            if match:
                title = match.group(1)
            else:
                title = path.stem
        
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        filename = f"{date_prefix}-{slug}.md"
        
        posts_dir = blog_path / "_posts"
        posts_dir.mkdir(exist_ok=True)
        
        dest_path = posts_dir / filename
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 文章已复制: {dest_path}")
    else:
        # 没有前置元数据，需要生成
        if not title:
            title = path.stem
        
        blog_path = ensure_blog_repo()
        create_post_file(title, content, blog_path)
    
    return commit_and_push(blog_path, title)


def publish_direct(title: str, content: str):
    """直接发布内容"""
    blog_path = ensure_blog_repo()
    create_post_file(title, content, blog_path)
    return commit_and_push(blog_path, title)


def main():
    parser = argparse.ArgumentParser(description='Blog Publisher - 博客发布工具')
    parser.add_argument('--note', '-n', help='从 Get 笔记发布（输入标题关键词）')
    parser.add_argument('--file', '-f', help='从文件发布')
    parser.add_argument('--title', '-t', help='文章标题（直接发布时使用）')
    parser.add_argument('--content', '-c', help='文章内容（直接发布时使用）')
    
    args = parser.parse_args()
    
    if args.note:
        success = publish_from_getnote(args.note)
    elif args.file:
        success = publish_from_file(args.file, args.title)
    elif args.title and args.content:
        success = publish_direct(args.title, args.content)
    else:
        parser.print_help()
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
