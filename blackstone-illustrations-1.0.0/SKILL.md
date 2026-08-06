---
name: blackstone-illustrations
description: 为中文文章、帖子、博客、Notion 文档、方法论和工作流内容规划或生成 Blackstone IP 正文配图。用于“文章配图”“正文插图”“配图建议”“shot list”“把观点画出来”“生成 Blackstone 插图”“去标题/改图”等任务；默认使用戴粗黑框眼镜、穿胸前绿色问号黑色 T 恤的 3D Blackstone 人物，在简洁白底中呈现清晰、克制、有记忆点的概念隐喻。
---

# Blackstone 正文配图

## 核心定位

把中文内容里的关键判断、流程、结构、状态或隐喻，转化成 16:9 横版 3D 正文配图。画面不是商业海报或密集 PPT，而是以 Blackstone 为核心行动者的简洁解释场景。

Blackstone 必须参与核心动作。固定识别特征是：侧梳棕色短发、粗黑框眼镜、黑色圆领 T 恤、胸前醒目的绿色问号、亲和而沉稳的成年男性形象。参考 `assets/blackstone-reference.png` 保持人物一致性。参考图中的 “Thanks boss!” 对话框不是固定元素，默认不要出现。

## 按需读取

- 设计人物或生图前读取 `references/blackstone-ip.md`。
- 规划画面与配色前读取 `references/style-dna.md`。
- 选择结构与发明隐喻时读取 `references/composition-patterns.md`。
- 调用 `image_gen` 前读取 `references/prompt-template.md`。
- 检查成图时读取 `references/qa-checklist.md`。

## 工作流

### 1. 消化内容

读取正文、链接、文档或截图，提炼核心观点、认知转折、关键流程以及适合视觉化的段落。不要平均配图；优先选择能成为认知锚点的内容。

### 2. 先给配图策略

用户只要求分析或规划时，输出 shot list，不生图。每张写清：放置段落、主题、核心意思、结构类型、Blackstone 的动作、主要元素和短标注。默认 4-8 张；短文 1-3 张；一般不超过 9 张。

### 3. 单张生成

用户明确要求生成时，直接调用内置 `image_gen`，每张单独生成，不把多张拼成一张。把 `assets/blackstone-reference.png` 作为角色身份参考图，并明确它不是待编辑的原图。

每张图只表达一个核心意思。提示词必须说明：16:9 横版、纯白或近纯白无缝背景、精致 3D 卡通渲染、Blackstone 是动作主体、胸前绿色问号清晰可见、大量留白、最多 3-5 个短中文标注、没有固定对话框、没有 PPT 或海报感。

### 4. 检查与迭代

按照 `references/qa-checklist.md` 检查。优先修复人物漂移、绿色问号缺失、参考图对话框被复刻、画面过满、文本错误和 Blackstone 仅作为装饰等问题。迭代时一次只改一个主要问题。

### 5. 交付

若用户在 workspace 中工作，将最终图保存到 `assets/<article-slug>-illustrations/`，依次命名为 `01-topic-name.png`、`02-topic-name.png`。不要覆盖既有资产，除非用户明确要求。

生成后简要说明图片数量、每张用途、保存路径以及可选图。

## 来源说明

本 Skill 改编自 MIT 授权的 Ian Xiaohei Illustrations；保留原作者 Ian 的衍生来源署名。视觉角色与生成规范已替换为 Blackstone IP。
