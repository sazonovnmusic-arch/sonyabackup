"""
Fallback YouTube Transcriber for sostv (v4 — PROXY ROTATOR)
=============================================================

Стратегия:
1. Берём proxy из pool (ротация по round-robin)
2. Для каждого запроса — новый session ID → новый IP
3. Throttle между запросами
4. Fallback цепочка: proxy → direct → yt-dlp → whisper

Установка:
- RESIDENTIAL_PROXY_URL (единственный)
- RESIDENTIAL_PROXY_URLS (несколько через запятую)
- RESIDENTIAL_PROXY_1, _2, _3... (нумерованные)
- PROXY_STRATEGY = round_robin | random | least_failures
- PROXY_MIN_INTERVAL = 30.0 (секунд между запросами с одного IP)
- TRANSCRIBE_THROTTLE = 5.0 (секунд между attempts)
"""
import os
import sys
import time
import json
import subprocess
from typing import Optional, Dict, Any

# Добавляем путь к скриптам
sys.path.insert(0, os.path.dirname(__file__))


class FallbackTranscriber:
    """Транскрайбер с proxy rotation и fallback."""
    
    def __init__(self):
        self.proxy_url = os.getenv('RESIDENTIAL_PROXY_URL')
        self.yt_api_key = os.getenv('YOUTUBE_API_KEY')
        self.throttle_seconds = float(os.getenv('TRANSCRIBE_THROTTLE', '5.0'))
        self.rotator = None
        self._init_rotator()
        
    def _init_rotator(self):
        """Инициализация rotator."""
        try:
            from proxy_rotator import get_rotator, set_env_proxy
            self.rotator = get_rotator()
            print(f"[FallbackTranscriber] Rotator загружен: {self.rotator.get_stats()['total_proxies']} proxy")
        except ImportError:
            self.rotator = None
            print("[FallbackTranscriber] Rotator не найден, использую env proxy")
    
    def _setup_proxy(self, force_new_session: bool = True):
        """Устанавливаем proxy через rotator или env. Поддерживает SOCKS5."""
        if self.rotator:
            from proxy_rotator import set_env_proxy
            proxy = self.rotator.get_next(force_new_session=force_new_session)
            set_env_proxy(proxy, force_new_session=force_new_session)
        elif self.proxy_url:
            for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
                os.environ[key] = self.proxy_url
    
    def _clear_proxy(self):
        """Очищаем proxy из env."""
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
            os.environ.pop(key, None)
    
    def _extract_video_id(self, url_or_id: str) -> str:
        """Извлекает video_id из URL или возвращает как есть."""
        s = url_or_id.strip()
        if 'youtube.com/shorts/' in s:
            return s.split('shorts/')[1].split('?')[0]
        if 'youtube.com/watch' in s:
            return s.split('v=')[1].split('&')[0]
        if 'youtu.be/' in s:
            return s.split('youtu.be/')[1].split('?')[0]
        return s
    
    def _throttle(self):
        """Ждём между запросами."""
        time.sleep(self.throttle_seconds)
    
    def _try_ytt_api(self, video_id: str, use_proxy: bool = True) -> Optional[Dict]:
        """Пробуем youtube-transcript-api с proxy или без."""
        if use_proxy:
            self._setup_proxy(force_new_session=True)
        else:
            self._clear_proxy()
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            ytt = YouTubeTranscriptApi()
            
            self._throttle()
            transcript = list(ytt.fetch(video_id))
            
            segments = [{'text': seg.text, 'start': seg.start, 'duration': seg.duration}
                       for seg in transcript]
            text = ' '.join([seg['text'] for seg in segments])
            
            result = {
                'method': 'youtube-transcript-api' + ('+proxy+rotate' if use_proxy else ''),
                'segments_count': len(segments),
                'transcript': segments,
                'text': text
            }
            
            # Уведомляем rotator об успехе
            if self.rotator and use_proxy:
                from proxy_rotator import get_rotator
                rot = get_rotator()
                current = rot.proxies[0]  # Approximation
                rot.mark_success(current)
            
            return result
            
        except Exception as e:
            err_msg = str(e)[:100]
            print(f"[{'Proxy' if use_proxy else 'Direct'} YTT failed] {type(e).__name__}: {err_msg}")
            
            # Уведомляем rotator о неудаче
            if self.rotator and use_proxy:
                from proxy_rotator import get_rotator
                rot = get_rotator()
                if rot.proxies:
                    rot.mark_failure(rot.proxies[0])
            
            return {'method': 'youtube-transcript-api' + ('+proxy' if use_proxy else ''), 'error': err_msg}
    
    def _try_ytdlp(self, video_id: str) -> Optional[Dict]:
        """yt-dlp субтитры."""
        try:
            self._setup_proxy(force_new_session=True)
            env = os.environ.copy()
            
            import tempfile
            tmpdir = tempfile.mkdtemp()
            
            # Проверяем наличие
            result = subprocess.run(
                ['yt-dlp', '--list-subs', f'https://youtube.com/watch?v={video_id}'],
                capture_output=True, text=True, timeout=30, env=env
            )
            if result.returncode != 0 or 'no subtitles' in result.stdout.lower():
                return None
            
            # Скачиваем
            result = subprocess.run(
                ['yt-dlp', '--write-sub', '--sub-langs', 'ru,en,auto',
                 '--skip-download', '--convert-subs', 'json',
                 '-o', f'{tmpdir}/%(id)s.%(ext)s',
                 f'https://youtube.com/watch?v={video_id}'],
                capture_output=True, text=True, timeout=60, env=env
            )
            
            import glob
            json_files = glob.glob(f'{tmpdir}/*.json')
            if not json_files:
                return None
            
            with open(json_files[0]) as f:
                data = json.load(f)
            
            segments = []
            if isinstance(data, list):
                segments = [{'text': s.get('text',''), 'start': s.get('tStartMs',0)/1000,
                           'duration': s.get('dDurationMs',0)/1000} for s in data]
            elif isinstance(data, dict) and 'events' in data:
                for ev in data['events']:
                    segs = ev.get('segs', [])
                    text = ''.join([s.get('utf8','') for s in segs])
                    segments.append({'text': text, 'start': ev.get('tStartMs',0)/1000,
                                   'duration': ev.get('dDurationMs',1000)/1000})
            
            for f in json_files:
                os.remove(f)
            os.rmdir(tmpdir)
            
            text = ' '.join([s['text'] for s in segments])
            return {
                'method': 'yt-dlp+proxy',
                'segments_count': len(segments),
                'transcript': segments,
                'text': text
            }
        except Exception as e:
            print(f"[yt-dlp failed] {type(e).__name__}: {str(e)[:100]}")
            return None
    
    def _try_whisper(self, video_id: str) -> Optional[Dict]:
        """Крайний fallback: скачать аудио → whisper."""
        try:
            import tempfile
            tmpdir = tempfile.mkdtemp()
            audio_path = os.path.join(tmpdir, f'{video_id}.mp3')
            
            self._setup_proxy(force_new_session=True)
            env = os.environ.copy()
            
            result = subprocess.run(
                ['yt-dlp', '-x', '--audio-format', 'mp3',
                 '-o', audio_path,
                 f'https://youtube.com/watch?v={video_id}'],
                capture_output=True, text=True, timeout=120, env=env
            )
            
            if result.returncode != 0 or not os.path.exists(audio_path):
                return {'method': 'whisper-fallback', 'error': f'yt-dlp: {result.stderr[:200]}'}
            
            from faster_whisper import WhisperModel
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments_iter, info = model.transcribe(audio_path, beam_size=5)
            
            segments = []
            text_parts = []
            for seg in segments_iter:
                segments.append({'text': seg.text, 'start': seg.start, 'duration': seg.end - seg.start})
                text_parts.append(seg.text)
            
            os.remove(audio_path)
            os.rmdir(tmpdir)
            
            return {
                'method': 'whisper-local',
                'segments_count': len(segments),
                'transcript': segments,
                'text': ' '.join(text_parts),
                'language': info.language
            }
        except Exception as e:
            print(f"[Whisper failed] {type(e).__name__}: {str(e)[:100]}")
            return None
    
    def get_transcript(self, video_id_or_url: str) -> Dict[str, Any]:
        """Главный метод: пробует все способы."""
        video_id = self._extract_video_id(video_id_or_url)
        print(f"🎯 FallbackTranscriber: {video_id}")
        
        # 1. С proxy (ротация)
        result = self._try_ytt_api(video_id, use_proxy=True)
        if result and result.get('text'):
            return result
        
        # 2. Без proxy
        result = self._try_ytt_api(video_id, use_proxy=False)
        if result and result.get('text'):
            return result
        
        # 3. yt-dlp
        result = self._try_ytdlp(video_id)
        if result and result.get('text'):
            return result
        
        # 4. Whisper
        result = self._try_whisper(video_id)
        if result and result.get('text'):
            return result
        
        last_err = result.get('error', 'Unknown') if result else 'All methods exhausted'
        return {
            'method': 'failed',
            'transcript': None,
            'text': '',
            'error': f'Все методы исчерпаны. Proxy: {"Yes" if (self.rotator or self.proxy_url) else "No"}. {last_err}'
        }


def get_video_transcript(video_id_or_url: str) -> str:
    """Удобная функция."""
    result = FallbackTranscriber().get_transcript(video_id_or_url)
    return result.get('text') or f"[ОШИБКА] {result.get('error', 'Unknown')}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = FallbackTranscriber().get_transcript(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Usage: python transcriber.py VIDEO_ID_OR_URL")
