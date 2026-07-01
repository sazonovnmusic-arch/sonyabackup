---
id: pinterest-scraper
name: Pinterest Media Scraper
category: media
description: |
  Automated Pinterest image search and download via Playwright with proxy rotation.
  Handles login, onboarding bypass, anti-detection, cookie persistence, and image downloading.
triggers:
  - User asks to scrape/download images from Pinterest
  - User needs Pinterest automation (search, collect, download)
  - Proxy-based browser automation for Pinterest
toolsets: ["terminal", "file"]
---

# Pinterest Media Scraper

## Overview

Two working approaches for Pinterest automation:
1. **Playwright** — full control, proxy auth support, more boilerplate
2. **DrissionPage** — less code, built-in anti-detect, but proxy auth needs Chromium args

Both require `headful` (headless=False + xvfb-run on servers). Pinterest detects headless.

## Requirements

```bash
# Playwright approach
pip install playwright aiohttp aiofiles
playwright install chromium

# DrissionPage approach
pip install drissionpage aiohttp
# Reuses same Chromium from playwright install
```

On headless servers:
```bash
apt-get install -y xvfb
```

## Key Anti-Detection Measures

**CRITICAL: Pinterest detects headless browsers.** Always use `headless=False` with `xvfb-run`.

**CRITICAL: Proxy auth.** DrissionPage `set_proxy()` does NOT support username:password auth. Use `--proxy-server` Chromium arg instead, or stick with Playwright.

### Playwright Browser Launch
```python
browser = await playwright.chromium.launch(
    headless=False,  # NEVER True for Pinterest
    proxy={"server": "...", "username": "...", "password": "..."},
    args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--window-size=1920,1080",
        "--no-sandbox",
    ]
)
```

### DrissionPage Browser Launch
```python
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless(False)
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.set_argument('--window-size=1920,1080')
co.set_argument('--no-sandbox')
co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36')
# Proxy with auth via Chromium arg (NOT set_proxy()):
co.set_argument('--proxy-server=http://pool.gonzoproxy.com:1000')
page = ChromiumPage(addr_or_opts=co)
```

### Anti-Detect JS (both approaches)
```python
# Playwright
await context.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    window.chrome = {runtime: {}};
    delete navigator.__proto__.webdriver;
""")

# DrissionPage
page.run_js('''
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
    window.chrome = { runtime: {} };
    delete navigator.__proto__.webdriver;
''')
```

## Login Flow

### Playwright
1. Navigate to `https://www.pinterest.com/login/`
2. Wait `networkidle`
3. Sleep 5s for React to render form
4. Fill `input[type="email"]` and `input[type="password"]`
5. Click `button[type="submit"]`
6. Sleep 8s for redirect
7. Verify URL no longer contains `/login`
8. **Save cookies** to `/tmp/pinterest_cookies.json` for reuse

### DrissionPage
```python
page.get('https://www.pinterest.com/login/')
time.sleep(5)
page.ele('css:input[type="email"]').input(EMAIL)
time.sleep(1)
page.ele('css:input[type="password"]').input(PASSWORD)
page.ele('css:button[type="submit"]').click()
time.sleep(8)
# Cookies: page.cookies() returns list of dicts (different format than Playwright)
# Use json.dump to save, page.set.cookies() to load
```

## Onboarding Bypass

After first login Pinterest shows "What interests you?" modal:
1. Find visible `div[role="button"]` elements (interest cards)
2. Click first 3 visible cards
3. Sleep 2s
4. Find continue button by text: `['продолж', 'feed', 'continue', 'лент', 'далее']`
5. Click and sleep 8s for feed to load

## Search Flow

### Playwright
```python
search_input = await page.wait_for_selector(
    'input[data-test-id="search-box-input"]',
    timeout=15000
)
await search_input.fill(query)
await asyncio.sleep(1)
await page.keyboard.press("Enter")
await asyncio.sleep(6)
```

### DrissionPage
```python
search_input = page.ele('css:input[data-test-id="search-box-input"]', timeout=15)
search_input.input(query + '\n')  # DrissionPage: append \n for Enter
time.sleep(6)
```

## Image Collection

### Playwright
```python
imgs = await page.query_selector_all('img')
for img in imgs:
    src = await img.get_attribute('src')
    if src and 'pinimg.com' in src:
        # High-res: replace /236x/ with /originals/
        high_res = re.sub(r'/\d+x/', '/originals/', src)
```

### DrissionPage
```python
imgs = page.eles('css:img')
for img in imgs:
    src = img.attr('src')
    # Filter for actual images, not .mjs files
    if src and 'pinimg.com' in src and any(ext in src for ext in ['.jpg', '.jpeg', '.png', '.webp']):
        high_res = re.sub(r'/\d+x/', '/originals/', src)
```

## Workflow: Preview Before Download

**Pinterest search results are noisy.** Do NOT bulk-download all images and filter afterward — that wastes disk space and bandwidth. Instead:

1. **Scroll viewport** and collect visible image URLs into memory (no disk writes)
2. **Screenshot each viewport** (`page.get_screenshot()` / `page.screenshot()`)
3. **Review screenshots** (via vision tool or with user) to identify matching images
4. **Download ONLY selected URLs** — pass through requests with Pinterest cookies + Referer

This avoids downloading 200 images only to discard 195 of them.

## Pitfalls

- **DrissionPage `page.get()` on image URLs returns `bool`, not Response.** Always use `requests.get()` with Pinterest cookies for downloads.
- **Filter image URLs by extension.** `pinimg.com` serves `.mjs` (JS modules) alongside images — skip anything not `.jpg/.jpeg/.png/.webp`.
- **`.webp/originals/` returns 403** for some images. Try `.jpg` fallback or download as-is from the `originals/` URL.
- **DrissionPage proxy auth** — `set_proxy()` does NOT support username:password. Use `--proxy-server` Chromium arg, or stick with Playwright for proxy auth.
- **One IP = one account.** Pinterest resets passwords if you log in from multiple IPs within 30 minutes.

## Block Detection

**Do NOT** check for words "captcha" or "blocked" in HTML — Pinterest always includes recaptcha scripts. Check instead:

```python
# Visible captcha iframe
captcha = await page.query_selector('iframe[src*="recaptcha"], iframe[src*="captcha"]')
if captcha and await captcha.is_visible():
    return True  # Actually blocked

# Or specific block messages in rendered page
block_patterns = [
    "your account has been suspended",
    "access denied",
    "too many requests",
    "unusual activity",
]
```

## Proxy Rotation

Gonzoproxy pool: change digit in login to rotate IP:
- `GonzoNvv5Rfv_c_fi_s_acc142(_ttl_240h` → `acc143`, `acc144`, etc.

**Only rotate when blocked** — frequent rotation causes logout.

## Download

### Playwright
Use `aiohttp` through same proxy with Referer header:
```python
async with session.get(url, proxy=proxy_str, proxy_auth=proxy_auth,
                       headers={"Referer": "https://www.pinterest.com/"}) as resp:
```

### DrissionPage
Browser cookies are required for anti-hotlink bypass:
```python
browser_cookies = {c['name']: c['value'] for c in page.cookies()}
headers = {
    'Referer': 'https://www.pinterest.com/',
    'User-Agent': 'Mozilla/5.0 ...',
}
resp = requests.get(url, headers=headers, cookies=browser_cookies, timeout=30)
```
**Note:** `page.get()` on image URLs returns bool — use requests with cookies instead.

## Cookie Format Differences

| Format | Playwright | DrissionPage |
|---|---|---|
| Save | `await context.cookies()` → JSON list of dicts | `page.cookies()` → JSON list of dicts |
| Load | `await context.add_cookies(cookies)` | `page.set.cookies()` or pass via CDP |
| Fields | `name`, `value`, `domain`, `path`, `expires`, `httpOnly`, `secure`, `sameSite` | Same, but format differs slightly — always serialize through json |

## Files

- [templates/pinterest_downloader.py](templates/pinterest_downloader.py) — Full working Playwright script
- [templates/pinterest_viewer_drissionpage.py](templates/pinterest_viewer_drissionpage.py) — Preview-first DrissionPage viewer (scroll + screenshot + collect URLs)
- [references/drissionpage_test_results.md](references/drissionpage_test_results.md) — Initial DrissionPage evaluation
- [references/drissionpage_pinterest_comparison.md](references/drissionpage_pinterest_comparison.md) — Detailed comparison: Playwright vs DrissionPage for Pinterest
