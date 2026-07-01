#!/usr/bin/env python3
"""
Fallback YouTube Transcriber (v3)
==================================
Production-ready transcript extractor for cloud VPS environments.

youtube-transcript-api v1.x reads proxy from HTTP_PROXY / HTTPS_PROXY env vars
(both upper- and lower-case). It does NOT accept a `proxies=` kwarg.

Fallback chain:
  1. youtube-transcript-api through residential proxy (fast, accurate)
  2. youtube-transcript-api direct (if server IP is not banned)
  3. yt-dlp --write-sub through proxy (extracts embedded subtitle tracks)
  4. Download audio → faster-whisper local transcription (last resort)

Requires:
  - youtube-transcript-api (pip install)
  - yt-dlp (pip install yt-dlp)
  - faster-whisper (pip install faster-whisper)
  - nodejs in PATH (yt-dlp needs a JS runtime for modern YouTube pages)
  - RESIDENTIAL_PROXY_URL env var (optional but strongly recommended for cloud VPS)

Usage:
    RESIDENTIAL_PROXY_URL=http://user:pass@host:port python3 transcriber.py VIDEO_ID
    python3 transcriber.py https://youtube.com/shorts/AbCdEfGhIjK
"""
import os
import sys
import json
import time
import subprocess
import tempfile
from typing import Optional, Dict, Any


class FallbackTranscriber:
    """Robust YouTube transcript extractor with multi-method fallback."""

    def __init__(self, proxy_url: Optional[str] = None, throttle: float = 2.0):
        self.proxy_url = proxy_url or os.getenv('RESIDENTIAL_PROXY_URL')
        self.throttle_seconds = float(os.getenv('TRANSCRIBE_THROTTLE', str(throttle)))
        self.yt_api_key = os.getenv('YOUTUBE_API_KEY')
        self._setup_proxy_env()

    def _setup_proxy_env(self):
        """Export proxy to env so youtube-transcript-api (via requests) picks it up."""
        if self.proxy_url:
            for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
                os.environ[key] = self.proxy_url

    def _extract_video_id(self, url_or_id: str) -> str:
        """Normalise any YouTube URL format to an 11-char video ID."""
        s = url_or_id.strip()
        if 'youtube.com/shorts/' in s:
            return s.split('shorts/')[1].split('?')[0]
        if 'youtube.com/watch' in s:
            return s.split('v=')[1].split('&')[0]
        if 'youtu.be/' in s:
            return s.split('youtu.be/')[1].split('?')[0]
        if 'youtube.com/embed/' in s:
            return s.split('embed/')[1].split('?')[0]
        return s

    def _throttle(self):
        time.sleep(self.throttle_seconds)

    def _try_ytt_proxy(self, video_id: str) -> Optional[Dict]:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            self._throttle()
            transcript = list(api.fetch(video_id))
            segments = [
                {'text': seg.text, 'start': seg.start, 'duration': seg.duration}
                for seg in transcript
            ]
            return {
                'method': 'youtube-transcript-api+proxy',
                'proxy': bool(self.proxy_url),
                'segments_count': len(segments),
                'transcript': segments,
                'text': ' '.join(s['text'] for s in segments),
            }
        except Exception as e:
            print(f"[proxy YTT] {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            return None

    def _try_ytt_direct(self, video_id: str) -> Optional[Dict]:
        saved = {k: os.environ.pop(k, None) for k in
                 ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy')}
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            self._throttle()
            transcript = list(api.fetch(video_id))
            segments = [
                {'text': seg.text, 'start': seg.start, 'duration': seg.duration}
                for seg in transcript
            ]
            return {
                'method': 'youtube-transcript-api',
                'segments_count': len(segments),
                'transcript': segments,
                'text': ' '.join(s['text'] for s in segments),
            }
        except Exception as e:
            print(f"[direct YTT] {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            return None
        finally:
            for k, v in saved.items():
                if v:
                    os.environ[k] = v
                elif k in os.environ:
                    del os.environ[k]
            self._setup_proxy_env()

    def _try_ytdlp(self, video_id: str) -> Optional[Dict]:
        try:
            env = os.environ.copy()
            node_bin = os.path.expanduser('~/.hermes/node/bin')
            if os.path.exists(node_bin):
                env['PATH'] = node_bin + ':' + env.get('PATH', '')

            tmpdir = tempfile.mkdtemp()
            result = subprocess.run(
                [
                    'yt-dlp',
                    '--write-sub', '--sub-langs', 'ru,en,-live_chat',
                    '--skip-download',
                    '--convert-subs', 'json',
                    '-o', os.path.join(tmpdir, '%(id)s.%(ext)s'),
                    f'https://youtube.com/watch?v={video_id}',
                ],
                capture_output=True, text=True, timeout=90, env=env,
            )

            if result.returncode != 0:
                err = result.stderr[:200]
                print(f"[yt-dlp] failed: {err}", file=sys.stderr)
                return None

            import glob
            json_files = glob.glob(os.path.join(tmpdir, '*.json'))
            if not json_files:
                return None

            segments = []
            for jf in json_files:
                with open(jf) as fh:
                    data = json.load(fh)
                if isinstance(data, dict) and 'events' in data:
                    for ev in data['events']:
                        segs = ev.get('segs', [])
                        text = ''.join(s.get('utf8', '') for s in segs)
                        if text:
                            segments.append({
                                'text': text,
                                'start': ev.get('tStartMs', 0) / 1000.0,
                                'duration': ev.get('dDurationMs', 1000) / 1000.0,
                            })

            for f in json_files:
                os.remove(f)
            os.rmdir(tmpdir)

            if not segments:
                return None

            return {
                'method': 'yt-dlp',
                'segments_count': len(segments),
                'transcript': segments,
                'text': ' '.join(s['text'] for s in segments),
            }
        except Exception as e:
            print(f"[yt-dlp] {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            return None

    def _try_whisper(self, video_id: str) -> Optional[Dict]:
        try:
            tmpdir = tempfile.mkdtemp()
            audio_path = os.path.join(tmpdir, f'{video_id}.mp3')

            env = os.environ.copy()
            node_bin = os.path.expanduser('~/.hermes/node/bin')
            if os.path.exists(node_bin):
                env['PATH'] = node_bin + ':' + env.get('PATH', '')

            dl = subprocess.run(
                ['yt-dlp', '-x', '--audio-format', 'mp3',
                 '-o', audio_path,
                 f'https://youtube.com/watch?v={video_id}'],
                capture_output=True, text=True, timeout=120, env=env,
            )
            if dl.returncode != 0 or not os.path.exists(audio_path):
                print(f"[whisper] yt-dlp audio download failed: {dl.stderr[:150]}", file=sys.stderr)
                return None

            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segs_iter, info = model.transcribe(audio_path, beam_size=5)

            segments = []
            texts = []
            for seg in segs_iter:
                segments.append({
                    'text': seg.text,
                    'start': seg.start,
                    'duration': seg.end - seg.start,
                })
                texts.append(seg.text)

            os.remove(audio_path)
            os.rmdir(tmpdir)

            return {
                'method': 'whisper-local',
                'segments_count': len(segments),
                'transcript': segments,
                'text': ' '.join(texts),
                'language': info.language,
            }
        except Exception as e:
            print(f"[whisper] {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            return None

    def get_transcript(self, video_id_or_url: str) -> Dict[str, Any]:
        video_id = self._extract_video_id(video_id_or_url)
        print(f"[FallbackTranscriber] video={video_id} proxy={'yes' if self.proxy_url else 'no'}")

        result = self._try_ytt_proxy(video_id)
        if result and result.get('text'):
            return result

        result = self._try_ytt_direct(video_id)
        if result and result.get('text'):
            return result

        result = self._try_ytdlp(video_id)
        if result and result.get('text'):
            return result

        result = self._try_whisper(video_id)
        if result and result.get('text'):
            return result

        last_err = (result or {}).get('error', 'Unknown')
        return {
            'method': 'failed',
            'transcript': None,
            'text': '',
            'error': (
                f"All methods exhausted. proxy={'yes' if self.proxy_url else 'no'}. "
                f"Last error: {last_err}. "
                f"Install deps: uv pip install youtube-transcript-api yt-dlp faster-whisper"
            ),
        }


def get_video_transcript(video_id_or_url: str) -> str:
    result = FallbackTranscriber().get_transcript(video_id_or_url)
    return result.get('text') or f"[ERROR] {result.get('error', 'Unknown error')}"


if __name__ == '__main__':
    if len(sys.argv) > 1:
        out = FallbackTranscriber().get_transcript(sys.argv[1])
        json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print("Usage: python3 transcriber.py VIDEO_ID_OR_URL")
