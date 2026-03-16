---
name: save-skill-to-github
description: 自动将 QoderWork 技能保存到 GitHub 仓库 (git@github.com:blackstoneblackstone/blackstone-skills.git)。当用户说 "skill 保存到 github"、"保存技能到 github"、"提交技能" 或类似意图时触发。
---

# Save Skill to GitHub

## 触发条件

当用户表达以下意图时：
- "skill 保存到 github"
- "保存技能到 github"
- "提交技能"
- "skills 提交"
- "把技能提交到 github"

## 工作流程

### Step 1: 检查技能仓库

```bash
SKILLS_REPO_DIR="$HOME/.blackstone-skills"
SKILLS_REPO_URL="git@github.com:blackstoneblackstone/blackstone-skills.git"

# 检查仓库是否存在
if [ ! -d "$SKILLS_REPO_DIR/.git" ]; then
    # 克隆仓库
    git clone "$SKILLS_REPO_URL" "$SKILLS_REPO_DIR"
fi
```

### Step 2: 同步本地技能到仓库

```bash
cd "$SKILLS_REPO_DIR"

# 拉取最新变更
git pull origin main

# 复制 ~/.qoderwork/skills/ 下的所有技能（排除隐藏文件）
rsync -av --delete --exclude=".*" ~/.qoderwork/skills/ ./

# 检查变更
git status
```

### Step 3: 提交并推送

```bash
# 添加所有变更
git add .

# 检查是否有变更需要提交
if git diff --cached --quiet; then
    echo "没有变更需要提交"
    exit 0
fi

# 提交
git commit -m "Update skills

$(date '+%Y-%m-%d %H:%M:%S')

🤖 Generated with [Qoder][https://qoder.com]"

# 推送到 GitHub
git push origin main
```

## 输出

提交成功后输出：
```
✅ 技能已成功保存到 GitHub！
仓库: https://github.com/blackstoneblackstone/blackstone-skills
提交时间: 2026-03-16 16:50:00
```

## 注意事项

- 需要配置 SSH 密钥访问 GitHub
- 会覆盖仓库中的技能文件，确保本地是最新版本
- 忽略以 `.` 开头的隐藏文件和目录
