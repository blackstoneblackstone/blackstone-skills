---
name: qwen-translator
description: 使用阿里云千问（Qwen）大模型进行高质量翻译。当用户提到「千问」、「Qwen」进行翻译，或需要调用千问模型进行文本翻译时触发。支持多语言互译，自动从 zshrc 读取 QWEN_KEY 和 QWEN_BASEURL 环境变量。
---

# 千问翻译 (Qwen Translator)

## 功能说明

使用阿里云千问大模型 API 进行智能翻译，支持多种语言之间的高质量互译。

## 环境变量

本技能从 zshrc 中读取以下环境变量：

- `QWEN_KEY` - 阿里云百炼平台的 API Key
- `QWEN_BASEURL` - 千问 API 的基础 URL（OpenAI 兼容模式端点）

## 使用方法

### 基本翻译

当用户需要翻译时，调用千问 API：

```python
import os
import requests

def translate_with_qwen(text, target_lang="中文", source_lang="自动检测"):
    """
    使用千问模型进行翻译（OpenAI 兼容模式）
    
    Args:
        text: 要翻译的文本
        target_lang: 目标语言（默认中文）
        source_lang: 源语言（默认自动检测）
    """
    api_key = os.environ.get("QWEN_KEY")
    base_url = os.environ.get("QWEN_BASEURL")
    
    if not api_key:
        return "错误：未设置 QWEN_KEY 环境变量，请检查 ~/.zshrc 配置"
    
    if not base_url:
        return "错误：未设置 QWEN_BASEURL 环境变量，请检查 ~/.zshrc 配置"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建翻译提示词
    if source_lang == "自动检测":
        prompt = f"请将以下文本翻译成{target_lang}，只返回翻译结果，不要添加任何解释：\n\n{text}"
    else:
        prompt = f"请将以下{source_lang}文本翻译成{target_lang}，只返回翻译结果，不要添加任何解释：\n\n{text}"
    
    # OpenAI 兼容模式接口
    payload = {
        "model": "qwen3-coder-plus",  # 或其他可用模型如 qwen3.5-plus, glm-5 等
        "messages": [
            {"role": "system", "content": "你是一个专业的翻译助手，擅长多种语言之间的高质量翻译。请准确翻译用户提供的文本，保持原文的语气和风格。"},
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "翻译失败")
    else:
        return f"翻译请求失败：{response.status_code} - {response.text}"
```

### 调用示例

```python
# 翻译为中文
translate_with_qwen("Hello, how are you?", target_lang="中文")

# 翻译为英文
translate_with_qwen("你好，今天天气怎么样？", target_lang="英文")

# 指定源语言
translate_with_qwen("Bonjour", source_lang="法语", target_lang="中文")
```

## 支持的模型

根据你的 Coding Plan 配置，可用模型包括：

| 模型名称 | 说明 |
|---------|------|
| qwen3.5-plus | 文本生成、深度思考、视觉理解 |
| qwen3-max-2026-01-23 | 文本生成、深度思考 |
| qwen3-coder-next | 文本生成 |
| qwen3-coder-plus | 文本生成（推荐用于翻译） |
| glm-5 | 文本生成、深度思考 |
| glm-4.7 | 文本生成、深度思考 |
| kimi-k2.5 | 文本生成、深度思考、视觉理解 |
| MiniMax-M2.5 | 文本生成、深度思考 |

默认使用 `qwen3-coder-plus`，可根据需求切换其他模型。

## 错误处理

常见错误及解决方案：

1. **401 Unauthorized**: API Key 无效或过期，请检查 `QWEN_KEY`
2. **429 Too Many Requests**: 请求频率过高，请稍后重试
3. **500 Internal Error**: 服务端错误，请稍后重试或联系阿里云支持

## 注意事项

- 确保 `QWEN_KEY` 已正确设置在 `~/.zshrc` 中并已 source
- 长文本建议分段翻译以获得更好效果
- 专业术语翻译可添加领域说明以获得更准确的翻译
