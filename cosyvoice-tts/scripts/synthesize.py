#!/usr/bin/env python3
"""Synthesize verified local speech through Alibaba MaaS or MiniMax."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import wave
from pathlib import Path

DEFAULT_BASE_URL = "https://llm-3k6f0rmm4n75d6bs.cn-beijing.maas.aliyuncs.com"
ENDPOINT = "/api/v1/services/aigc/multimodal-generation/generation"
COSYVOICE_ENDPOINT = "/api/v1/services/audio/tts/SpeechSynthesizer"
MINIMAX_BASE_URL = "https://api.minimax.io"
MINIMAX_ENDPOINT = "/v1/t2a_v2"
LANGUAGES = {"Auto", "Chinese", "English", "German", "Italian", "Portuguese", "Spanish", "Japanese", "Korean", "French", "Russian"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert text to a verified local audio file.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--input-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider", choices=["cosyvoice", "minimax"], default="cosyvoice")
    parser.add_argument("--model")
    parser.add_argument("--voice")
    parser.add_argument("--language", default="Chinese", choices=sorted(LANGUAGES))
    parser.add_argument("--instructions")
    parser.add_argument("--speed", type=float, choices=[x / 10 for x in range(5, 21)])
    parser.add_argument("--format", choices=["wav", "mp3", "m4a", "flac", "ogg"])
    parser.add_argument("--chunk-size", type=int, default=450)
    parser.add_argument("--volume", type=float, default=1.0)
    parser.add_argument("--pitch", type=int, default=0)
    parser.add_argument("--sample-rate", type=int, default=32000)
    parser.add_argument("--bitrate", type=int, default=128000)
    parser.add_argument("--base-url")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def keychain_secret(service: str) -> str | None:
    if sys.platform != "darwin":
        return None
    result = subprocess.run(
        ["security", "find-generic-password", "-a", os.environ.get("USER", ""), "-s", service, "-w"],
        text=True, capture_output=True,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def api_key(provider: str) -> str:
    if provider == "minimax":
        key = os.environ.get("MINIMAX_API_KEY") or keychain_secret("minimax-api-key")
        if key:
            return key
        raise SystemExit("No MiniMax API key found. Set MINIMAX_API_KEY or add macOS Keychain item 'minimax-api-key'.")
    key = os.environ.get("COSYVOICE_API_KEY")
    if key:
        return key
    key = keychain_secret("cosyvoice-api-key")
    if key:
        return key
    raise SystemExit("No API key found. Set COSYVOICE_API_KEY or add macOS Keychain item 'cosyvoice-api-key'.")


def split_text(text: str, limit: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise SystemExit("Input text is empty.")
    if limit < 50:
        raise SystemExit("--chunk-size must be at least 50.")
    pieces = re.split(r"(?<=[。！？!?；;\n])", text)
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        piece = piece.strip()
        while len(piece) > limit:
            room = limit - len(current)
            if room > 0:
                current += piece[:room]
                piece = piece[room:]
            chunks.append(current)
            current = ""
        if current and len(current) + len(piece) > limit:
            chunks.append(current)
            current = piece
        else:
            current += piece
    if current:
        chunks.append(current)
    return chunks


def request_audio(base_url: str, key: str, payload: dict, endpoint: str = ENDPOINT) -> tuple[bytes, str | None]:
    req = urllib.request.Request(
        base_url.rstrip("/") + endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"TTS API HTTP {exc.code}: {detail[:1000]}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"TTS API connection failed: {exc.reason}") from None
    audio = body.get("output", {}).get("audio", {})
    url = audio.get("url")
    if not url:
        raise SystemExit(f"TTS API returned no audio URL: {json.dumps(body, ensure_ascii=False)[:1000]}")
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read(), body.get("request_id")


def request_minimax_audio(base_url: str, key: str, payload: dict) -> tuple[bytes, str | None]:
    req = urllib.request.Request(
        base_url.rstrip("/") + MINIMAX_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"MiniMax TTS API HTTP {exc.code}: {detail[:1000]}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"MiniMax TTS API connection failed: {exc.reason}") from None
    base_resp = body.get("base_resp") or {}
    if base_resp.get("status_code") not in (None, 0):
        raise SystemExit(f"MiniMax TTS API error {base_resp.get('status_code')}: {base_resp.get('status_msg', 'unknown error')}")
    audio = (body.get("data") or {}).get("audio")
    if not audio:
        raise SystemExit(f"MiniMax TTS API returned no audio: {json.dumps(body, ensure_ascii=False)[:1000]}")
    if audio.startswith("http://") or audio.startswith("https://"):
        with urllib.request.urlopen(audio, timeout=120) as response:
            return response.read(), body.get("trace_id")
    try:
        return bytes.fromhex(audio), body.get("trace_id")
    except ValueError:
        raise SystemExit("MiniMax TTS API returned malformed hex audio.") from None


def join_wavs(parts: list[Path], output: Path) -> float:
    params = None
    frames: list[bytes] = []
    total_frames = 0
    for part in parts:
        with wave.open(str(part), "rb") as wav:
            current = wav.getparams()
            signature = current[:3]
            if params is None:
                params = current
            elif signature != params[:3]:
                raise SystemExit("Generated WAV chunks use incompatible audio parameters.")
            data = wav.readframes(current.nframes)
            frames.append(data)
            # Some generated WAV URLs use a streaming placeholder in the
            # header's nframes field. Count the bytes actually downloaded.
            total_frames += len(data) // (current.nchannels * current.sampwidth)
    assert params is not None
    with wave.open(str(output), "wb") as wav:
        wav.setparams(params)
        for data in frames:
            wav.writeframes(data)
    return total_frames / params.framerate


def transcode(source: Path, output: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required for non-WAV output.")
    result = subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(source), str(output)], capture_output=True, text=True)
    if result.returncode:
        raise SystemExit(f"ffmpeg failed: {result.stderr.strip()}")


def main() -> None:
    args = parse_args()
    text = args.text if args.text is not None else args.input_file.read_text(encoding="utf-8")
    instructions = args.instructions
    model = args.model or (os.environ.get("MINIMAX_TTS_MODEL", "speech-2.8-hd") if args.provider == "minimax" else "qwen3-tts-flash")
    effective_chunk_size = min(args.chunk_size, 60) if model.startswith("cosyvoice-") else args.chunk_size
    chunks = split_text(text, effective_chunk_size)
    voice = args.voice or (None if args.provider == "minimax" else "Cherry")
    if args.provider == "minimax" and not voice:
        raise SystemExit("--voice must be a valid MiniMax voice_id when --provider minimax is selected.")
    if args.speed is not None and args.provider == "cosyvoice" and not model.startswith("cosyvoice-"):
        speed_text = f"语速调整为正常语速的 {args.speed:.1f} 倍。"
        instructions = f"{instructions} {speed_text}".strip() if instructions else speed_text
    if args.provider == "minimax" and instructions:
        raise SystemExit("--instructions is supported only by the cosyvoice provider.")
    if instructions and model == "qwen3-tts-flash":
        model = "qwen3-tts-instruct-flash"
    output_format = args.format or args.output.suffix.lstrip(".").lower() or "wav"
    output = args.output.with_suffix("." + output_format).expanduser().resolve()
    plan = {"provider": args.provider, "model": model, "voice": voice, "language": args.language, "chunks": len(chunks), "output": str(output)}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return
    key = api_key(args.provider)
    output.parent.mkdir(parents=True, exist_ok=True)
    request_ids: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cosyvoice-tts-") as temp_dir:
        parts: list[Path] = []
        for index, chunk in enumerate(chunks):
            if args.provider == "minimax":
                payload = {
                    "model": model,
                    "text": chunk,
                    "stream": False,
                    "language_boost": "auto" if args.language == "Auto" else args.language,
                    "output_format": "hex",
                    "voice_setting": {"voice_id": voice, "speed": args.speed or 1.0, "vol": args.volume, "pitch": args.pitch},
                    "audio_setting": {"sample_rate": args.sample_rate, "bitrate": args.bitrate, "format": "wav", "channel": 1},
                }
                audio, request_id = request_minimax_audio(args.base_url or MINIMAX_BASE_URL, key, payload)
            else:
                if model.startswith("cosyvoice-"):
                    if instructions:
                        raise SystemExit("--instructions is not supported by the CosyVoice v3.5 HTTP path in this skill.")
                    language_hints = {
                        "Chinese": "zh", "English": "en", "German": "de", "Italian": "it",
                        "Portuguese": "pt", "Spanish": "es", "Japanese": "ja", "Korean": "ko",
                        "French": "fr", "Russian": "ru",
                    }
                    input_data = {
                        "text": chunk,
                        "voice": voice,
                        "format": "wav",
                        "sample_rate": args.sample_rate,
                        "rate": args.speed or 1.0,
                    }
                    if args.language != "Auto":
                        input_data["language_hints"] = [language_hints[args.language]]
                    payload = {"model": model, "input": input_data}
                    audio, request_id = request_audio(
                        args.base_url or DEFAULT_BASE_URL, key, payload, COSYVOICE_ENDPOINT
                    )
                else:
                    input_data = {"text": chunk, "voice": voice, "language_type": args.language}
                    if instructions:
                        input_data.update({"instructions": instructions, "optimize_instructions": True})
                    payload = {"model": model, "input": input_data}
                    audio, request_id = request_audio(args.base_url or DEFAULT_BASE_URL, key, payload)
            part = Path(temp_dir) / f"part-{index:04d}.wav"
            part.write_bytes(audio)
            parts.append(part)
            if request_id:
                request_ids.append(request_id)
        merged = Path(temp_dir) / "merged.wav"
        duration = join_wavs(parts, merged)
        if output_format == "wav":
            shutil.copy2(merged, output)
        else:
            transcode(merged, output)
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit("Audio output validation failed.")
    result = {**plan, "duration_seconds": round(duration, 3), "bytes": output.stat().st_size, "request_ids": request_ids}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
