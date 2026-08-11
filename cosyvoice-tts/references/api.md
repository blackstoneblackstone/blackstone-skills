# API reference

- Workspace host: `https://llm-3k6f0rmm4n75d6bs.cn-beijing.maas.aliyuncs.com`
- Generation endpoint: `/api/v1/services/aigc/multimodal-generation/generation`
- CosyVoice non-real-time endpoint: `/api/v1/services/audio/tts/SpeechSynthesizer`
- Authentication: `Authorization: Bearer <key>`
- Default model: `qwen3-tts-flash`
- Default voice: `Cherry`
- Non-streaming audio URL: `output.audio.url`; download it immediately because it expires after 24 hours.
- Qwen3-TTS input limit: 512 tokens. The script splits conservatively by characters and punctuation.
- `instructions` and `optimize_instructions` apply to Qwen3-TTS-Instruct-Flash models.
- CosyVoice v3.5 custom voices use a model-matched voice ID, `format: wav`, `rate`, `sample_rate`, and optional `language_hints` in `input`.
- A voice beginning `cosyvoice-v3.5-flash-` must use model `cosyvoice-v3.5-flash`. The v3.5 series is available in the China (Beijing) region.
- `InvalidParameter` with `url error` from the multimodal endpoint usually means the CosyVoice request was sent to the wrong endpoint path.
- The workspace `/compatible-mode/v1/models` endpoint can be used for read-only model discovery.

Official documentation: https://help.aliyun.com/zh/model-studio/qwen-tts-api

CosyVoice HTTP documentation: https://help.aliyun.com/en/model-studio/cosyvoice-tts-http-api
