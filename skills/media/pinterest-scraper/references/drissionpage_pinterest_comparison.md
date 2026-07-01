# DrissionPage vs Playwright for Pinterest (June 2026)

## Session: pinterest-scraper (DrissionPage test)

### Context
User asked to evaluate DrissionPage as Pinterest scraper. Ran head-to-head test.

### Key Findings

| Feature | Playwright | DrissionPage |
|---|---|---|
| Lines of code | More (~200 for full scraper) | Less (~100 for same logic) |
| API | `await page.wait_for_selector()`, `await element.fill()` | `page.ele()`, `element.input()` |
| Proxy auth | `proxy={"server":..., "username":..., "password":...}` | `set_proxy()` **does NOT support auth** — must use `--proxy-server` arg |
| Headless detect | Needs manual anti-detect scripts | Built-in anti-detect slightly better |
| Keyboard input | `page.keyboard.press("Enter")` | Append `\n` to `input()` |
| Screenshots | `await page.screenshot(path=...)` | `page.get_screenshot(path)` |
| Cookies save | `await context.cookies()` → JSON | `page.cookies()` → JSON (different load API) |
| Download images | `requests` with cookies | `requests` with cookies (same) |

### What Worked
- **Login**: Both succeeded on first try
- **Anti-detect**: Pinterest didn't flag either
- **Search**: Both navigated to results
- **URL collection**: Both gathered valid pinimg.com URLs

### What Broke
- DrissionPage `page.get(url)` on image URLs returns `bool` — cannot use for downloading images
- DrissionPage `set_proxy("http://user:pass@host:port")` silently ignores auth — must use Chromium `--proxy-server` arg
- Bulk-download-then-filter workflow was wasteful — preview-first approach is better

### Recommended Pattern
Use **DrissionPage for browsing** (less code), **requests for downloading** (works with cookies).

### Working DrissionPage Snippet
```python
from DrissionPage import ChromiumPage, ChromiumOptions
import re, time

co = ChromiumOptions()
co.headless(False)  # Required for Pinterest
co.set_argument('--no-sandbox')
co.set_argument('--disable-blink-features=AutomationControlled')
page = ChromiumPage(addr_or_opts=co)

# Login
page.get('https://www.pinterest.com/login/')
time.sleep(5)
page.ele('css:input[type="email"]').input(email)
page.ele('css:input[type="password"]').input(password)
page.ele('css:button[type="submit"]').click()
time.sleep(8)

# Search
page.ele('css:input[data-test-id="search-box-input"]').input(query + '\n')
time.sleep(6)

# Collect URLs (no download yet)
imgs = page.eles('css:img')
urls = []
for img in imgs:
    src = img.attr('src')
    if src and 'pinimg.com' in src and any(ext in src for ext in ['.jpg','.jpeg','.png','.webp']):
        urls.append(re.sub(r'/\d+x/', '/originals/', src))

# Screenshot for preview
page.get_screenshot('/tmp/preview.png')

# Download selected URLs with cookies
import requests
browser_cookies = {c['name']: c['value'] for c in page.cookies()}
headers = {'Referer': 'https://www.pinterest.com/'}
for url in selected_urls:
    resp = requests.get(url, headers=headers, cookies=browser_cookies)
    # save to disk
```
