# Cloud IP Blocking Workaround for youtube-transcript-api

## Problem

youtube-transcript-api fails on cloud VPS IPs (AWS, Google Cloud, Hetzner, etc.) with:

```
RequestBlocked: Could not retrieve a transcript ... YouTube is blocking requests from your IP
```

## Root Cause

YouTube aggressively blocks datacenter IP ranges from scraping subtitles.
Residential proxy is required for reliable access.

## Solutions (fallback chain)

### 1. Residential Proxy (Recommended)

Configure `HTTP_PROXY` / `HTTPS_PROXY` env vars or pass proxy to requests:

```bash
# HTTP proxy format
RESIDENTIAL_PROXY_URL=http://user:pass@host:port
```

**Note:** `youtube-transcript-api` v1.x does NOT accept `proxies` parameter.
However, it **DOES** read proxy settings from `HTTP_PROXY` / `HTTPS_PROXY` 
environment variables (both uppercase and lowercase work). The library uses 
`requests` internally, which respects these env vars automatically.

```python
import os
os.environ['HTTP_PROXY'] = 'http://user:pass@host:port'
os.environ['HTTPS_PROXY'] = 'http://user:pass@host:port'
# lowercase variants also respected:
os.environ['http_proxy'] = 'http://user:pass@host:port'
os.environ['https_proxy'] = 'http://user:pass@host:port'

from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
transcript = list(api.fetch(video_id))  # uses proxy automatically
```

**HTTP vs SOCKS5**: HTTP(S) proxies work immediately. SOCKS5 requires 
`pip install PySocks` and may need extra patching. Prefer HTTP(S) unless 
provider only offers SOCKS5.

**Shared vs Static proxy**: Shared residential proxies (many users per IP) 
may still get `RequestBlocked` on some videos if the IP is overloaded. For 
production bots, use **static/dedicated residential proxy** (single IP only 
for you).

### 2. yt-dlp (Bypass via video download)

yt-dlp can extract subtitle tracks directly via `--list-subs` / `--write-sub`.
Requires `nodejs` in PATH for modern YouTube pages.

```bash
# List available subtitles
yt-dlp --list-subs "https://youtube.com/watch?v=VIDEO_ID"

# Download subtitles only
yt-dlp --write-sub --sub-langs ru,en --skip-download "URL"
```

**Caveat:** YouTube may require cookies/sign-in. Use `--cookies-from-browser chrome`
or export cookies manually.

### 3. Local Whisper Transcription (Last Resort)

Download audio via yt-dlp + proxy → transcribe with faster-whisper.

```python
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio_path, language="ru")
```

## Testing

Test proxy connectivity:
```bash
curl -x "$RESIDENTIAL_PROXY_URL" https://ipinfo.io/json
```

## Providers

| Service | Price | Notes |
|---------|-------|-------|
| PacketStream | ~$1/GB | P2P residential |
| IPRoyal | ~$7/GB | Rotating residential |
| Smartproxy | ~$12.5/GB | Large pool |

## Reference Implementation

See `scripts/transcriber.py` in youtube-content skill for full fallback chain.
