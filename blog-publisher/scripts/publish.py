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

# R2 图片上传配置
R2_BUCKET = os.getenv("BLOG_R2_BUCKET", "blog-images")
R2_IMAGE_DOMAIN = os.getenv("BLOG_IMAGE_DOMAIN", "")

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


def upload_image_to_r2(image_path: Path, post_slug: str) -> Optional[str]:
    """使用 Wrangler 上传图片到 R2"""
    if not R2_IMAGE_DOMAIN:
        print("⚠️ 未配置 BLOG_IMAGE_DOMAIN，跳过图片上传")
        return None
    
    # 生成 R2 路径
    timestamp = datetime.now().strftime("%Y%m%d")
    ext = image_path.suffix.lower()
    r2_key = f"{timestamp}/{post_slug}/{image_path.name}"
    
    # 使用 wrangler 上传
    cmd = [
        "wrangler", "r2", "object", "put",
        f"{R2_BUCKET}/{r2_key}",
        "--file", str(image_path)
    ]
    
    print(f"📤 上传图片: {image_path.name} -> R2")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 上传失败: {result.stderr}")
        return None
    
    # 生成图片 URL
    image_url = f"{R2_IMAGE_DOMAIN.rstrip('/')}/{r2_key}"
    print(f"✅ 图片上传成功: {image_url}")
    return image_url


def download_image(url: str, temp_dir: Path) -> Optional[Path]:
    """下载远程图片到临时目录"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return None
        
        # 从 URL 提取文件名
        from urllib.parse import urlparse
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename:
            filename = f"image_{datetime.now().timestamp()}.jpg"
        
        local_path = temp_dir / filename
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return local_path
    except Exception as e:
        print(f"❌ 下载图片失败 {url}: {e}")
        return None


def process_images_in_content(content: str, post_slug: str, temp_dir: Path) -> str:
    """处理文章中的图片，上传到 R2 并替换 URL"""
    
    # 匹配 Markdown 图片语法: ![alt](url)
    md_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    # 匹配 HTML img 标签: <img src="url" ...>
    html_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    
    def replace_md_image(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        
        # 如果已经是 R2 域名，跳过
        if R2_IMAGE_DOMAIN and img_url.startswith(R2_IMAGE_DOMAIN):
            return match.group(0)
        
        # 下载并上传图片
        local_path = None
        if img_url.startswith(('http://', 'https://')):
            local_path = download_image(img_url, temp_dir)
        elif Path(img_url).exists():
            local_path = Path(img_url)
        
        if local_path:
            new_url = upload_image_to_r2(local_path, post_slug)
            if new_url:
                return f'![{alt_text}]({new_url})'
        
        return match.group(0)
    
    def replace_html_image(match):
        img_url = match.group(1)
        full_tag = match.group(0)
        
        # 如果已经是 R2 域名，跳过
        if R2_IMAGE_DOMAIN and img_url.startswith(R2_IMAGE_DOMAIN):
            return full_tag
        
        # 下载并上传图片
        local_path = None
        if img_url.startswith(('http://', 'https://')):
            local_path = download_image(img_url, temp_dir)
        elif Path(img_url).exists():
            local_path = Path(img_url)
        
        if local_path:
            new_url = upload_image_to_r2(local_path, post_slug)
            if new_url:
                return full_tag.replace(img_url, new_url)
        
        return full_tag
    
    # 处理 Markdown 图片
    content = re.sub(md_pattern, replace_md_image, content)
    
    # 处理 HTML 图片
    content = re.sub(html_pattern, replace_html_image, content)
    
    return content


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


def create_post_file(title: str, content: str, blog_path: Path, categories: list = None, tags: list = None, process_images: bool = True) -> Path:
    """创建博客文章文件"""
    import tempfile
    import shutil
    
    now = datetime.now()
    date_prefix = now.strftime("%Y-%m-%d")
    
    # 生成文件名
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    filename = f"{date_prefix}-{slug}.md"
    
    posts_dir = blog_path / "_posts"
    posts_dir.mkdir(exist_ok=True)
    
    file_path = posts_dir / filename
    
    # 处理图片上传
    if process_images and R2_IMAGE_DOMAIN:
        print("🖼️  处理文章图片...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            content = process_images_in_content(content, slug, temp_path)
    
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
    import tempfile
    
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
    
    # 生成 slug 用于图片路径
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # 处理内容中的图片
    if R2_IMAGE_DOMAIN:
        print("🖼️  处理文章图片...")
        with tempfile.TemporaryDirectory() as temp_dir:
            content = process_images_in_content(content, slug, Path(temp_dir))
    
    # 创建文章
    create_post_file(title, content, blog_path, process_images=False)
    
    # 提交推送
    if commit_and_push(blog_path, title):
        now = datetime.now().strftime("%Y-%m-%d")
        print(f"\n🎉 发布成功!")
        print(f"🔗 https://blackstoneblackstone.github.io/{now.replace('-', '/')}/{slug}/")
        return True
    
    return False


def publish_from_file(file_path: str, title: Optional[str] = None):
    """从文件发布"""
    import tempfile
    
    path = Path(file_path)
    if not path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blog_path = ensure_blog_repo()
    
    # 提取标题
    if not title:
        if content.startswith('---'):
            match = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
            if match:
                title = match.group(1)
        if not title:
            title = path.stem
    
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # 处理图片
    if R2_IMAGE_DOMAIN:
        print("🖼️  处理文章图片...")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 复制本地图片到临时目录
            file_dir = path.parent
            for img_match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content):
                img_path = img_match.group(2)
                if not img_path.startswith(('http://', 'https://', '/')):
                    local_img = file_dir / img_path
                    if local_img.exists():
                        shutil.copy(local_img, temp_path / local_img.name)
            
            content = process_images_in_content(content, slug, temp_path)
    
    # 如果文件已有前置元数据，直接使用
    if content.startswith('---'):
        now = datetime.now()
        date_prefix = now.strftime("%Y-%m-%d")
        filename = f"{date_prefix}-{slug}.md"
        
        posts_dir = blog_path / "_posts"
        posts_dir.mkdir(exist_ok=True)
        
        dest_path = posts_dir / filename
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 文章已复制: {dest_path}")
    else:
        # 没有前置元数据，需要生成
        create_post_file(title, content, blog_path, process_images=False)
    
    return commit_and_push(blog_path, title)


def publish_direct(title: str, content: str):
    """直接发布内容"""
    import tempfile
    
    blog_path = ensure_blog_repo()
    
    # 处理图片
    if R2_IMAGE_DOMAIN:
        print("🖼️  处理文章图片...")
        slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        with tempfile.TemporaryDirectory() as temp_dir:
            content = process_images_in_content(content, slug, Path(temp_dir))
    
    create_post_file(title, content, blog_path, process_images=False)
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
