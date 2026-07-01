---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs."
platforms: [linux, macos, windows]
---

# YouTube Content Tool

## When to use

Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video. Transforms transcripts into structured content (chapters, summaries, threads, blog posts).

Extract transcripts from YouTube videos and convert them into useful formats.

## Setup

Use `uv` so the dependency is installed into the same Hermes-managed environment
that runs the helper script:

```bash
uv pip install youtube-transcript-api
```

## Helper Scripts

| Script | Purpose |
|--------|---------|
| `scripts/fetch_transcript.py` | Quick transcript fetch (CLI) |
| `scripts/transcriber.py` | Full fallback chain with proxy support |
| `scripts/proxy_rotator.py` | Universal proxy pool manager with session rotation (SOCKS5 / HTTP) |

Run via `uv run python3`:

```bash
# JSON output with metadata
uv run python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Full fallback chain (auto-rotates proxy if configured)
python3 SKILL_DIR/scripts/transcriber.py "URL"
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps` via `uv run python3`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `uv pip install youtube-transcript-api` and retry.

## Pitfalls

### Cloud IP Blocking

**Critical**: youtube-transcript-api frequently fails on cloud VPS IPs (AWS, Google Cloud, DigitalOcean, etc.) with `RequestBlocked`. YouTube actively bans datacenter IP ranges.

**Detection**: error contains "blocking requests from your IP" or "Sign in to confirm you're not a bot".

**Solutions** (in order of preference):
1. **Residential proxy** — configure `HTTP_PROXY` / `HTTPS_PROXY` env vars. Pass proxy URL to any network tool. See `references/cloud-ip-blocking.md` for provider recommendations and pricing.
2. **yt-dlp fallback** — use `yt-dlp --write-sub` to extract subtitle tracks directly. Requires `nodejs` in PATH (Hermes installs it at `~/.hermes/node/bin/node`). May require cookies if YouTube demands sign-in.
3. **Local Whisper** — download audio via yt-dlp → transcribe with `faster-whisper`. Last resort; slow but works without YouTube API cooperation.

### youtube-transcript-api v1.x API Changes

The v1.x library uses `api.fetch(video_id)` instead of legacy `get_transcript(video_id)`. It does **not** accept a `proxies` keyword argument — proxy must be configured via environment variables (`HTTP_PROXY`, `HTTPS_PROXY`) or global requests session.

**HTTP vs SOCKS5**: HTTP(S) proxies work immediately. SOCKS5 requires `pip install PySocks` and works transparently when `ALL_PROXY` env var is set. See `references/proxy-session-rotation.md` for provider-specific patterns.

**Session rotation**: Some providers (GonzoProxy, Bright Data, PacketStream) support IP rotation by changing a session token in the proxy username. The `scripts/proxy_rotator.py` helper automates this. See `references/proxy-session-rotation.md`.

Always check the installed version before assuming method signatures:
```python
from youtube_transcript_api import YouTubeTranscriptApi
import inspect
print(inspect.signature(YouTubeTranscriptApi.fetch))
```

### Concrete v1.x Working Pattern

The current v1.x API uses an **instance method** on `YouTubeTranscriptApi`. Here is a known-good minimal snippet:

```python
from youtube_transcript_api import YouTubeTranscriptApi

video_id = "3mqGhFe-49Y"
api = YouTubeTranscriptApi()
transcript = api.fetch(video_id, languages=["ru"])

for item in transcript:
    # item is a FetchedTranscriptSnippet dataclass
    print(f"{item.start:.1f}s: {item.text}")
    # attributes: start (float), duration (float), text (str)
```

**Key details:**
- Instantiate `YouTubeTranscriptApi()` first; `fetch` is an instance method, not a classmethod or standalone function.
- Result is a `FetchedTranscript` (list-like) of `FetchedTranscriptSnippet` dataclass objects. Access fields via attributes (`item.start`, `item.text`), **not** dict subscript (`item["start"]`).
- `languages` parameter accepts an iterable of ISO language codes in priority order (e.g., `["ru", "en"]`).

### yt-dlp Requires JavaScript Runtime

yt-dlp needs a JS engine (Node, Deno, or Bun) for modern YouTube page extraction. Hermes bundles Node at `~/.hermes/node/bin/node`. Ensure it's in PATH or pass `--js-runtimes node:/path/to/node`.

Without JS runtime: yt-dlp falls back to limited extraction, may miss formats, and often fails with "No supported JavaScript runtime could be found".

### Cookie Authentication for yt-dlp

When YouTube detects automation, it serves a "Sign in to confirm you're not a bot" challenge. yt-dlp can bypass this with authenticated cookies:
```bash
# Export cookies from your browser
tyt-dlp --cookies-from-browser chrome "URL"

# Or use a cookies.txt file
tyt-dlp --cookies /path/to/cookies.txt "URL"
```

Without cookies: yt-dlp may fail on popular videos or channels. This is a YouTube anti-bot measure, not a yt-dlp bug.

## Fallback Chain for Production Use

For automated workflows (bots, cron jobs), implement a robust fallback:

```python
# Pseudocode — see SKILL_DIR/scripts/transcriber.py for full implementation
def get_transcript_with_fallback(video_id):
    # 1. Try youtube-transcript-api (fast, no proxy needed if IP clean)
    result = try_youtube_transcript_api(video_id)
    if result: return result
    
    # 2. Try youtube-transcript-api with residential proxy
    result = try_youtube_transcript_api_with_proxy(video_id)
    if result: return result
    
    # 3. Try yt-dlp --write-sub through proxy
    result = try_ytdlp_subtitles(video_id)
    if result: return result
    
    # 4. Last resort: download audio → whisper transcribe
    result = try_whisper_transcription(video_id)
    if result: return result
    
    raise AllMethodsFailed()
```

The reference implementation (`scripts/transcriber.py`) implements this exact chain with proper error handling and cleanup.
