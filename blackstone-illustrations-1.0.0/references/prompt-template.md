# 生图提示词模板

每张图单独调用内置 `image_gen`。将 `assets/blackstone-reference.png` 作为 reference image，用于锁定人物身份与服装；不要把它当成待编辑图片。

```text
Use case: stylized-concept
Asset type: 16:9 horizontal illustration embedded in a Chinese article
Primary request: Create one standalone conceptual illustration about {主题}.
Input images: Image 1 is the identity reference for Blackstone. Preserve the recurring character's face, brown side-swept hairstyle, thick black glasses, black crew-neck T-shirt, and bright green question-mark chest emblem. Do not copy Image 1's speech bubble, coffee mug, pose, or composition.
Scene/backdrop: seamless pure white or near-white studio background with generous negative space
Subject: Blackstone is actively {核心动作}; he must cause the key transformation, not stand beside it
Style/medium: polished premium 3D cartoon render, friendly adult proportions, refined skin and hair, clean product-illustration finish, not photorealistic and not childish
Composition/framing: wide 16:9 composition; main group occupies 40%-65%; {具体布局与主要物件}
Lighting/mood: soft high-key studio lighting, subtle grounding shadow, calm, intelligent, lightly playful
Color palette: black and white dominant; bright green reserved for the shirt question mark and one optional key accent; restrained low-saturation supporting colors
Text (verbatim): {无文字，或逐条列出必须出现的短中文}
Constraints: one image communicates only {核心意思}; preserve Blackstone identity; green question mark must remain clearly visible; use at most 3-5 short labels; no fixed speech bubble; no "Thanks boss!"; no watermark
Avoid: PPT infographic, formal flowchart, poster title, dense text, complex background, cyberpunk glow, plastic toy look, childlike proportions, extra characters, duplicated limbs, deformed hands, identity drift
```

若中文不是必要信息，优先无文字生成，再由正文解释含义。若必须保留文字，逐字列出并在成图后检查。

## 编辑提示

```text
Edit only the specified issue in the provided illustration. Preserve Blackstone's face, brown side-swept hair, thick black glasses, black T-shirt, bright green question-mark emblem, pose, scene, framing, lighting, and aspect ratio. Change only: {修改项}. Do not add a speech bubble, "Thanks boss!", new text, or extra objects.
```
