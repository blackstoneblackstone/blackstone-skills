---
name: daily-us-stock-video
description: Generate a polished daily Chinese US-stock analysis video from the newest NaNa说美股 YouTube upload or a user-supplied reference. Use when asked to make, update, preview, verify, or render a daily 美股复盘/美股分析节目 with HyperFrames, market and stock components, rewritten humorous narration, synchronized captions, privacy-safe imagery, and final MP4 delivery.
---

# Daily US Stock Video

Create a 1920×1080, 5–7 minute Chinese daily US-stock program. Default to the newest upload from `https://www.youtube.com/@NaNaShuoMeiGu`; a user URL overrides it.

## Required skills and tools

- Use `/hyperframes`, `/hyperframes-core`, `/hyperframes-animation`, `/hyperframes-cli`, and `/media-use` for the composition.
- Use `$cosyvoice-tts` for narration. Default to `cosyvoice-v3-flash` + `longyan_v3`. A user-specified voice always wins, but the model may change after a one-scene compatibility probe; for example, Elias works with `qwen3-tts-flash` when CosyVoice rejects it.
- Use `$imagegen` for every retained reference-video screenshot. Never edit screenshots with ad-hoc image scripts.
- Use `yt-dlp` from its latest GitHub revision when the system binary cannot download the reference.

## Workflow

1. Resolve the newest channel video and record URL, title, publication date, and duration. Download video and Chinese subtitles for local analysis.
2. Extract transcript, opening frames, contact sheet, and major topic timestamps. Do not publish downloaded media directly.
3. Build a 5–7 minute outline in this order: market overview, macro catalysts, sector rotation, selected stocks, risk calendar, closing takeaway. Insert an intentional 0.8–1.2 second pause between narration segments; place the transition inside this pause and keep captions empty there.
4. Preserve the source's useful humor: extract setups, reversals, memorable metaphors, and running jokes; rewrite them in original wording. Keep the narration observant and lightly witty throughout, with specific market metaphors and callbacks instead of generic banter. Never copy long passages or invent facts for a joke. Do not use the Chinese contrast template `不是……而是……` or cosmetic variants of it; rewrite as a direct claim, consequence, or punchline.
5. Write `SCRIPT.md` with one narration block per visual scene. Lock narration before synthesizing audio.
6. Rebuild all market and security visuals with HyperFrames components:
   - Use the market-overview component for indices, breadth, heatmap, and movers.
   - Use the stock-trend component for every named stock or ETF.
   - For each stock/ETF appearance, inspect the corresponding source-video chart, narration, axis labels, and stated period. Record whether it is intraday, multi-day, or daily. Configure the component and fetch data at that same time grain; never default to 5-minute intraday when the source argument uses daily candles, or vice versa.
   - Fetch the latest complete regular-session snapshot locally before rendering.
7. Prefer code-native reconstruction for news posts and macro charts. Use no screenshot when HTML/CSS/SVG can communicate the claim. Only when reconstruction is inadequate, capture a source frame and send it through Imagegen. Require: redesigned composition, removed NaNa watermark, removed presenter/author avatar, removed username/channel ID, removed account details/notifications, and no residual private information. If reliable removal cannot be proven, do not use the image. When no screenshot is retained, write a provenance file stating that the final render graph contains none.
8. Probe a user-specified voice on the first scene before batch synthesis. For MiniMax, resolve the credential region first: use `api.minimaxi.com` for a China-region key and `api.minimax.io` for an international key. Treat `invalid api key` from the wrong regional host as an endpoint mismatch before rejecting the voice. For a CosyVoice custom voice, match the voice prefix to its model, use the SpeechSynthesizer endpoint, and synthesize in chunks of at most 60 characters as described by `$cosyvoice-tts`; never request an entire 25–40 second scene in one call. If the requested model rejects that voice, keep the voice and try only a compatible model; report the endpoint/model change without printing the key. Never silently replace the requested voice. Synthesize narration scene-by-scene and verify every local file with `ffprobe`.
9. Sum measured narration durations before assembly. If the result exceeds 7 minutes, shorten the locked script first. When the content is already concise, a uniform, pitch-preserving `atempo` adjustment up to 1.15× is acceptable; preserve both original and delivery audio and record the factor in `SCRIPT.md`.
10. Calculate scene starts from measured delivery-audio durations plus the documented inter-segment pauses. Emit at least six decimal places for `data-start` and `data-duration`; shorten each authored narration clip by 2 ms at its tail to prevent decoder-rounding overlap, and reserve the same 2 ms safety gap between adjacent caption clips. Generate complete Chinese subtitles from the locked script and align every cue to its narration scene; emit no subtitle during transition pauses.
11. Assemble in HyperFrames. Keep source video muted; narration is always separate `<audio>` with a stable unique ID. Add captions as timed DOM elements with stable IDs, not as untracked source-video subtitles. Reserve a dedicated bottom caption band: remove or relocate charts, labels, footers, tickers, disclosures, and decorative elements from behind it. Captions may cover only an intentionally empty background zone and must not obscure decision-relevant content. Give repeated stock scenes unique composition IDs; do not mount the same `data-composition-id` multiple times. Prefer a fixed symbol inside each generated stock sub-composition over fragile serialized `data-variable-values` when Studio rewrites the host HTML.
12. Add one full-frame, seamless looping animated background layer spanning the complete program. Use a local privacy-safe image/texture and deterministic seek-safe motion such as slow drift, parallax, gradient breathing, or light grain. Keep it visible through intentionally open areas, including the caption band, while maintaining text contrast. Do not reset the loop at scene boundaries or use nondeterministic animation.
13. Run the hard gates in [checklist.md](references/checklist.md). Run `scripts/verify_sync.py` against the final media, subtitle file, and scene manifest when available. For narration-led programs, pass `--require-mono` and deliver exactly one final audio stream. Fix every error before claiming completion.
14. Open Studio, reload after the final source write, and actually press Play. Before playback, pause or close every other Studio preview, MP4 tab, audio preview, and local player. Play the first narration WAV alone for 20 seconds, then stop it and play the final MP4 from 0:00 to 0:20. Require one active media element, a progressing timecode, enabled audio, one clearly audible voice, captions, and no current console errors. If the WAV is clean but the MP4 doubles, inspect the render graph/player; if both double, regenerate TTS. Render MP4 only after the composition and checklist pass. Preserve the HyperFrames project, final MP4, original and delivery narration, subtitles, data snapshots, and verification report.

## Transition and SFX contract

- Treat every topic, sector, stock, or ETF change as a segment boundary. Record its outgoing subject, incoming subject, pause start/end, visual transition, SFX identity, start, duration, authored volume, and provenance in `STORYBOARD.md`. A program with N segments normally has N−1 transition pairs. Default pause duration is 1.0 second, acceptable range 0.8–1.2 seconds.
- Design one coherent sound family. Use a restrained soft whoosh for topic changes; add a short tonal tick or market-terminal accent for stock changes. Every visual transition must have exactly one matching timed `<audio>` clip with a stable unique ID.
- Default to deterministic local synthesis or an approved local SFX library for sub-second effects. MiniMax may generate source material only when its documented audio or instrumental model fits the request. Do not claim TTS sound tags or full-song generation as a dedicated SFX API.
- When MiniMax is used, preserve provider, region, model, prompt, raw asset, crop/edit steps, and final SFX provenance.
- Measure every SFX with `ffprobe` and `volumedetect` or `ebur128`. Mix below narration, avoid clipping and masked boundary words, and keep each SFX inside the documented pause without extending the intended gap.
- Preserve transition SFX with the project and verify that Studio playback enables both narration and SFX.

## Non-negotiable gates

- No `NaNa`, `NANA`, channel logo, watermark, presenter cutout, username, or private account information may appear in any frame.
- Narration, visuals, and subtitles must describe the same topic at the same time. Scene boundaries must derive from measured narration durations.
- A subtitle covering any chart, label, footer, ticker, disclosure, or decision-relevant element is a failure; the caption band must be intentionally empty behind the subtitle.
- Missing or mismatched source time-grain evidence for a stock/ETF component is a failure.
- Missing inter-segment pauses or a background loop that restarts at cuts is a failure.
- Any `不是……而是……` construction in the locked narration is a script-review failure.
- Any source screenshot must have a corresponding Imagegen-derived asset and an entry in the screenshot provenance table.
- A model fallback may change the TTS model, never the user-confirmed voice.
- A clean `ffprobe` stream count does not prove audible single-voice output; the isolated first-20-second WAV and MP4 playback gate is mandatory.
- Do not diagnose a doubled voice by downmixing or waveform equality alone. Distinguish TTS-baked doubling, two active players, duplicate render-graph inputs, and stereo playback anomalies.
- `hyperframes check` passing does not replace Studio playback; both must pass.
- A visual transition without exactly one synchronized SFX clip, or an SFX clip without a documented boundary, is a failure.
- Missing evidence is a failure, not a warning.

## Output contract

Deliver:

- `BRIEF.md`, `STORYBOARD.md`, and `SCRIPT.md`
- HyperFrames source and local market-data snapshots
- scene narration files and one merged narration file
- Chinese `.srt`
- screenshot provenance table, if screenshots exist
- `verification-report.json`
- final 1920×1080 MP4

Read [program-format.md](references/program-format.md) when planning scenes. Read [checklist.md](references/checklist.md) before any visual assembly and again before delivery.
