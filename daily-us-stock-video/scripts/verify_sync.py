#!/usr/bin/env python3
import argparse, json, re, subprocess, sys
from pathlib import Path

def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture_output=True, text=True)
    if result.returncode: raise SystemExit(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)

def srt_seconds(value):
    hours, minutes, tail = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(tail)

def parse_srt(path):
    text = path.read_text(encoding="utf-8-sig")
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")
    return [(srt_seconds(a), srt_seconds(b)) for a, b in pattern.findall(text)]

parser = argparse.ArgumentParser(description="Verify final video/audio/subtitle timing.")
parser.add_argument("video", type=Path)
parser.add_argument("--subtitle", type=Path)
parser.add_argument("--expected-scenes", type=int)
parser.add_argument("--scene-manifest", type=Path, help="Optional JSON array of scene objects with start and end fields")
parser.add_argument("--require-mono", action="store_true", help="Require exactly one mono audio stream")
args = parser.parse_args()

meta = probe(args.video)
duration = float(meta.get("format", {}).get("duration", 0))
video_streams = [s for s in meta.get("streams", []) if s.get("codec_type") == "video"]
audio_streams = [s for s in meta.get("streams", []) if s.get("codec_type") == "audio"]
errors, warnings = [], []
if not video_streams: errors.append("missing video stream")
if not audio_streams: errors.append("missing audio stream")
if len(audio_streams) > 1: errors.append(f"unexpected audio stream count {len(audio_streams)}")
if args.require_mono and audio_streams and audio_streams[0].get("channels") != 1:
    errors.append(f"expected mono audio, found {audio_streams[0].get('channels')} channels")
if duration <= 0: errors.append("invalid media duration")
if video_streams:
    width, height = video_streams[0].get("width"), video_streams[0].get("height")
    if (width, height) != (1920, 1080): errors.append(f"unexpected resolution {width}x{height}")

cues = []
if args.subtitle:
    cues = parse_srt(args.subtitle)
    if not cues: errors.append("subtitle contains no cues")
    previous_end = 0.0
    for index, (start, end) in enumerate(cues, 1):
        if start < previous_end - 0.001: errors.append(f"subtitle cue {index} overlaps the previous cue")
        if end <= start: errors.append(f"subtitle cue {index} has invalid duration")
        if end > duration + 0.05: errors.append(f"subtitle cue {index} extends beyond video")
        previous_end = max(previous_end, end)
    if duration - cues[-1][1] > 8: warnings.append(f"subtitle ends {duration - cues[-1][1]:.2f}s before video")
if args.expected_scenes and len(cues) < args.expected_scenes:
    errors.append(f"subtitle cue count {len(cues)} is below expected scene count {args.expected_scenes}")

scenes = []
if args.scene_manifest:
    payload = json.loads(args.scene_manifest.read_text(encoding="utf-8"))
    scenes = payload.get("scenes", payload) if isinstance(payload, dict) else payload
    if not isinstance(scenes, list) or not scenes:
        errors.append("scene manifest contains no scenes")
        scenes = []
    previous_end = 0.0
    for index, scene in enumerate(scenes, 1):
        start, end = float(scene["start"]), float(scene["end"])
        if start < previous_end - 0.001: errors.append(f"scene {index} overlaps the previous scene")
        if end <= start: errors.append(f"scene {index} has invalid duration")
        if end > duration + 0.05: errors.append(f"scene {index} extends beyond video")
        previous_end = end
    for cue_index, (cue_start, cue_end) in enumerate(cues, 1):
        owners = [index for index, scene in enumerate(scenes, 1) if cue_start >= float(scene["start"]) - 0.001 and cue_end <= float(scene["end"]) + 0.001]
        if len(owners) != 1: errors.append(f"subtitle cue {cue_index} is not contained by exactly one scene")

report = {"ok": not errors, "video": str(args.video.resolve()), "duration_seconds": duration, "resolution": [video_streams[0].get("width"), video_streams[0].get("height")] if video_streams else None, "audio_streams": len(audio_streams), "audio_channels": audio_streams[0].get("channels") if audio_streams else None, "subtitle_cues": len(cues), "scene_count": len(scenes), "errors": errors, "warnings": warnings}
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if report["ok"] else 1)
