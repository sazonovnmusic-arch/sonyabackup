# Residential Proxy Session Rotation (GonzoProxy Pattern)

## Session-Based IP Rotation

Some residential proxy providers change the assigned IP based on a session
identifier embedded in the proxy username.

### How it works

Instead of buying multiple proxies, you get ONE endpoint but change the
session string in the login to receive a different IP:

```
Username pattern:  GonzoNvv5Rfv_c_US_s_acc69)7(_ttl_6h
                               ^^^^^^^^
                               session ID
```

Change `acc69)7(` → `acc69)8(` → new IP from the provider's pool.

This is cheaper than multiple static IPs and simpler than rotating through
a list of endpoints.

### Supported providers

| Provider | Session token | Format example |
|----------|---------------|----------------|
| GonzoProxy | `accNNN)N(` in username | `GonzoPREFIX_c_CC_s_sessID_ttl_Xh` |
| Bright Data (Luminati) | `session-XXXX` | `lum-customer-USER-zone-residential-session-RND` |
| PacketStream | `sess-XXXX` | `customer-USER-sess-ID` |
| Oxylabs | `rndXXXX` or `sidXXXX` | `user-rnd12345678` |

### Usage in youtube-content scripts

The `proxy_rotator.py` helper auto-detects session tokens and rotates them:

```python
from proxy_rotator import get_rotator, set_env_proxy

rot = get_rotator()
proxy = rot.get_next(force_new_session=True)
set_env_proxy(proxy)
```

When `force_new_session=True`, it mutates the URL:
- Finds `sess-*`, `session-*`, `sp*`, `rnd*`, `sid*`, `sessid*` in the URL
- Replaces with a new random 8-character string
- Same endpoint, **different IP**

### Testing

```bash
# Check current IP through proxy
curl -x "socks5://user:pass@host:port" https://ipinfo.io/json

# Rotate session and check again
# (use proxy_rotator.py get_next(force_new_session=True))
```

### Cost

| Scenario | Traffic | PacketStream cost | GonzoProxy cost |
|----------|---------|-------------------|-----------------|
| Light (5-10 Shorts/day) | ~200 MB/month | ~$0.20 | ~$0.50 |
| Normal (20 Shorts/day) | ~800 MB/month | ~$0.80 | ~$2.00 |
| Heavy (bulk processing) | ~5 GB/month | ~$5.00 | ~$10.00 |

## Configuration in `.env`

```bash
# Single proxy
SOCKS5_PROXY_URL=socks5://user:pass@host:port

# Multiple for rotation
SOCKS5_PROXY_URLS=socks5://u:p@h1:1000,socks5://u:p@h2:1000

# Settings
PROXY_STRATEGY=round_robin   # or random, least_failures
PROXY_MIN_INTERVAL=3.0       # seconds between same proxy reuse
```
