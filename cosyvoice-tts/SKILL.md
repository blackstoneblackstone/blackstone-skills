---
name: cosyvoice-tts
description: Convert text or UTF-8 text files into verified local speech audio through Alibaba Cloud MaaS CosyVoice/Qwen TTS or MiniMax Speech. Use when the user asks to synthesize narration, voice-over, spoken Chinese or multilingual audio, long-form TTS, select CosyVoice or MiniMax, or save generated speech locally.
---

# CosyVoice and MiniMax TTS

Generate and verify a local audio file with the bundled script. Never place API keys in prompts, source files, command output, or generated metadata.

## Workflow

1. Resolve the output path. Default to a descriptive `.wav` file in the current workspace.
2. Choose exactly one input source: `--text` or `--input-file`.
3. Select `--provider cosyvoice` (default) or `--provider minimax`. MiniMax requires an explicit `--voice <voice_id>`. For a voice ID prefixed with `cosyvoice-v3.5-flash-`, use the matching `--model cosyvoice-v3.5-flash`; never send a cloned voice through the Qwen TTS path.
4. Run `scripts/synthesize.py`. CosyVoice reads `COSYVOICE_API_KEY` or Keychain `cosyvoice-api-key`; MiniMax reads `MINIMAX_API_KEY` or Keychain `minimax-api-key`.
5. Report the provider, model, voice, output path, duration, and number of chunks from the JSON summary.
6. Render playable audio in Codex with `![audio](/absolute/path/to/file.wav)`.

## Command

```bash
python3 /Users/yondu/.codex/skills/cosyvoice-tts/scripts/synthesize.py \
  --text "你好，这是一次语音合成测试。" \
  --output /absolute/path/to/output.wav
```

MiniMax:

```bash
python3 /Users/yondu/.codex/skills/cosyvoice-tts/scripts/synthesize.py \
  --provider minimax \
  --voice '<MiniMax voice_id>' \
  --model speech-2.8-hd \
  --text "你好，这是 MiniMax 语音合成测试。" \
  --output /absolute/path/to/output.wav
```

CosyVoice v3.5 cloned/custom voice:

```bash
python3 /Users/yondu/.codex/skills/cosyvoice-tts/scripts/synthesize.py \
  --provider cosyvoice \
  --model cosyvoice-v3.5-flash \
  --voice 'cosyvoice-v3.5-flash-<voice-id>' \
  --speed 1.0 \
  --sample-rate 24000 \
  --input-file /absolute/path/to/script.txt \
  --output /absolute/path/to/output.wav
```

Useful options:

- `--input-file FILE`: read UTF-8 text from a file.
- `--provider cosyvoice|minimax`: choose the TTS backend.
- `--voice ID`: choose a provider-specific voice; required for MiniMax.
- `--language Chinese`: set `Auto`, `Chinese`, `English`, `German`, `Italian`, `Portuguese`, `Spanish`, `Japanese`, `Korean`, `French`, or `Russian`.
- `--model MODEL`: override the provider default (`qwen3-tts-flash` or `speech-2.8-hd`).
- `MINIMAX_TTS_MODEL`: override only the MiniMax speech model. Do not reuse the generic `MINIMAX_MODEL`, which may point to a text model.
- `--instructions TEXT`: use expressive instructions; the script automatically selects `qwen3-tts-instruct-flash` when the default model is unchanged.
- `--speed 0.5..2.0`: translate speed into an instruction and use the instruct model.
- `--volume`, `--pitch`, `--sample-rate`, `--bitrate`: MiniMax audio controls.
- `--format wav|mp3|m4a|flac|ogg`: select the final format. Non-WAV output requires `ffmpeg`.
- `--chunk-size N`: split long input at punctuation. Default: 450 characters.
- `--dry-run`: validate configuration and print the planned request without calling the API.

## CosyVoice custom-voice rules

- Match the voice prefix and model exactly; for example, `cosyvoice-v3.5-flash-*` requires `cosyvoice-v3.5-flash`.
- Use `/api/v1/services/audio/tts/SpeechSynthesizer` for models beginning with `cosyvoice-`. The bundled script selects it automatically.
- Use the China/Beijing workspace endpoint for CosyVoice v3.5 unless the user authorizes another official DashScope endpoint.
- Probe one short scene before batch synthesis. Verify the downloaded WAV with `ffprobe`; require one audio stream and one channel for narration delivery.
- Keep CosyVoice custom-voice requests at 60 characters or less per chunk. The bundled script enforces this cap automatically because a single 25–40 second response can contain baked-in overlapping speech even though the WAV is mono.
- Generate all scenes with one provider, model, voice, rate, and sample rate. Never mix fallback voices inside one program.
- If the default multimodal endpoint returns `InvalidParameter` or `url error`, treat it as an endpoint-path mismatch before rejecting the voice.

## Guardrails

- Use only the configured MaaS host unless the user explicitly supplies `--base-url`.
- Use only the official MiniMax endpoint unless the user explicitly supplies `--base-url`.
- Do not print or persist the API key.
- Treat model and voice compatibility errors as actionable failures; do not claim an audio file exists without validating it.
- Preserve the generated local file because remote result URLs expire.
- Use `--instructions` only with an instruct-capable CosyVoice model; MiniMax rejects this option.

Read [references/api.md](references/api.md) for Qwen and CosyVoice endpoint selection, custom voices, or troubleshooting. Read [references/minimax-api.md](references/minimax-api.md) for MiniMax endpoint changes, voice IDs, or troubleshooting.
