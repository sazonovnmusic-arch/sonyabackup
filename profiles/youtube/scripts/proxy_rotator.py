"""
Universal Proxy Rotator (HTTP / HTTPS / SOCKS5 / SOCKS4)
========================================================
Поддерживает любые proxy форматы. Автоопределение типа.

Примеры URL:
- HTTP:   http://user:pass@host:port
- HTTPS:  https://user:pass@host:port
- SOCKS5: socks5://user:pass@host:port
- SOCKS4: socks4://user:pass@host:port
"""
import os
import time
import random
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class Proxy:
    url: str
    scheme: str = 'http'  # http | https | socks5 | socks4
    host: str = ''
    port: int = 8080
    last_used: float = 0
    fail_count: int = 0
    success_count: int = 0
    
    def __post_init__(self):
        if not self.host:
            self._parse_url()
    
    def _parse_url(self):
        """Парсим URL в компоненты."""
        m = re.match(r'^(\w+)://(?:([^:@]+):([^@]+)@)?([^:]+):(\d+)', self.url)
        if m:
            self.scheme = m.group(1).lower()
            self.host = m.group(4)
            self.port = int(m.group(5))


class ProxyRotator:
    """Универсальный rotator для любых типов proxy."""
    
    def __init__(self, strategy: str = 'round_robin', min_interval: float = 30.0):
        self.proxies: List[Proxy] = []
        self.strategy = strategy
        self.min_interval = min_interval
        self.current_index = 0
        self.rotation_count = 0
        self._load_from_env()
    
    def _load_from_env(self):
        """Загружает proxy из переменных окружения (любые форматы)."""
        urls = []
        
        sources = [
            os.getenv('RESIDENTIAL_PROXY_URL'),
            os.getenv('RESIDENTIAL_PROXY_URLS'),
            os.getenv('SOCKS5_PROXY_URL'),
            os.getenv('SOCKS5_PROXY_URLS'),
            os.getenv('HTTP_PROXY_URL'),
            os.getenv('PROXY_URL'),
        ]
        
        for src in sources:
            if not src:
                continue
            if ',' in src:
                urls.extend([u.strip() for u in src.split(',') if u.strip()])
            else:
                urls.append(src.strip())
        
        # Нумерованные
        for prefix in ['RESIDENTIAL_PROXY', 'SOCKS5_PROXY', 'PROXY']:
            i = 1
            while True:
                val = os.getenv(f'{prefix}_{i}')
                if not val:
                    break
                urls.append(val.strip())
                i += 1
        
        # Уникальные
        seen = set()
        for url in urls:
            if url not in seen:
                seen.add(url)
                self.proxies.append(Proxy(url=url))
        
        if self.proxies:
            print(f"[ProxyRotator] Загружено {len(self.proxies)} proxy")
            for i, p in enumerate(self.proxies):
                print(f"  [{i}] {p.scheme.upper()} {p.host}:{p.port}")
        else:
            print("[ProxyRotator] ⚠️ Нет proxy!")
    
    def _generate_session_id(self) -> str:
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    
    def _rotate_session_in_url(self, url: str) -> str:
        """Меняем session ID в URL для получения нового IP."""
        patterns = [
            (r'(sess-[a-z0-9]+)', f'sess-{self._generate_session_id()}'),
            (r'(session-[a-z0-9]+)', f'session-{self._generate_session_id()}'),
            (r'(sp[a-z0-9]{5,})', f'sp{self._generate_session_id()}'),
            (r'(rnd[a-z0-9]{5,})', f'rnd{self._generate_session_id()}'),
            (r'(sid[a-z0-9]{5,})', f'sid{self._generate_session_id()}'),
            (r'(sessid[a-z0-9]+)', f'sessid{self._generate_session_id()}'),
        ]
        
        new_url = url
        for pattern, replacement in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                new_url = re.sub(pattern, replacement, url, flags=re.IGNORECASE, count=1)
                print(f"[ProxyRotator] 🔄 Session rotated: {new_url.split('@')[-1][:30]}...")
                break
        
        return new_url
    
    def get_next(self, force_new_session: bool = False) -> Optional[Proxy]:
        """Возвращает следующий proxy по стратегии."""
        if not self.proxies:
            return None
        
        now = time.time()
        available = [p for p in self.proxies if (now - p.last_used) >= self.min_interval]
        if not available:
            available = sorted(self.proxies, key=lambda p: p.last_used)
            available = available[:max(1, len(available) // 2)]
        
        if self.strategy == 'round_robin':
            idx = self.current_index % len(available)
            proxy = available[idx]
            self.current_index += 1
        elif self.strategy == 'random':
            proxy = random.choice(available)
        elif self.strategy == 'least_failures':
            proxy = min(available, key=lambda p: p.fail_count)
        else:
            proxy = available[0]
        
        if force_new_session:
            proxy.url = self._rotate_session_in_url(proxy.url)
        
        proxy.last_used = now
        self.rotation_count += 1
        
        return proxy
    
    def mark_success(self, proxy: Proxy):
        proxy.success_count += 1
        proxy.fail_count = max(0, proxy.fail_count - 1)
    
    def mark_failure(self, proxy: Proxy):
        proxy.fail_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        total = sum(p.success_count + p.fail_count for p in self.proxies) or 1
        return {
            'total_proxies': len(self.proxies),
            'rotations': self.rotation_count,
            'proxies': [
                {
                    'scheme': p.scheme,
                    'host': p.host,
                    'port': p.port,
                    'success': p.success_count,
                    'failures': p.fail_count,
                    'rate': f"{p.success_count / (p.success_count + p.fail_count) * 100:.0f}%" if (p.success_count + p.fail_count) > 0 else "N/A",
                    'last': f"{time.time() - p.last_used:.0f}s"
                }
                for p in self.proxies
            ]
        }


_rotator: Optional[ProxyRotator] = None

def get_rotator() -> ProxyRotator:
    global _rotator
    if _rotator is None:
        _rotator = ProxyRotator(
            strategy=os.getenv('PROXY_STRATEGY', 'round_robin'),
            min_interval=float(os.getenv('PROXY_MIN_INTERVAL', '30.0'))
        )
    return _rotator


def set_env_proxy(proxy: Optional[Proxy], force_new_session: bool = False):
    """Устанавливает proxy в env vars (requests/PySocks читают)."""
    if proxy is None:
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
            os.environ.pop(key, None)
        print("[Proxy] Cleared")
        return
    
    if force_new_session:
        rot = get_rotator()
        proxy.url = rot._rotate_session_in_url(proxy.url)
    
    # PySocks через requests понимает socks5:// в HTTP_PROXY
    os.environ['HTTP_PROXY'] = proxy.url
    os.environ['HTTPS_PROXY'] = proxy.url
    os.environ['http_proxy'] = proxy.url
    os.environ['https_proxy'] = proxy.url
    
    # Для socks указываем ALL_PROXY (some libs read this)
    if proxy.scheme in ('socks5', 'socks4'):
        os.environ['ALL_PROXY'] = proxy.url
        os.environ['all_proxy'] = proxy.url
    
    print(f"[Proxy] {proxy.scheme.upper()} {proxy.host}:{proxy.port} (rotations: {get_rotator().rotation_count})")


if __name__ == "__main__":
    # Test
    rot = ProxyRotator(strategy='round_robin', min_interval=0)
    for i in range(5):
        p = rot.get_next(force_new_session=(i % 2 == 0))
        if p:
            print(f"#{i}: {p.scheme.upper()} {p.host}:{p.port}")
        time.sleep(0.1)
    print(rot.get_stats())
