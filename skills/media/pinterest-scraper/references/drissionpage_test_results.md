# DrissionPage Pinterest Test Results

Session: 2025-06-24, model: kimi-k2.6:cloud

## Test Setup

- Server: Ubuntu 22.04, headless (xvfb-run)
- Browser: Chromium from playwright install (~200 MB)
- Account: mybropalach@yandex.ru
- No proxy (set_proxy() doesn't support auth)
- Package: drissionpage==4.1.1.4

## Results

### Login
- ✅ First-attempt login SUCCESS
- ✅ Pinterest did NOT detect headless
- ✅ Anti-detect JS injections worked
- ✅ 15 cookies saved after login

### Search
- ✅ Search by query (anime wallpaper)
- ✅ Navigation to results page

### Image Collection
- ✅ 88 unique URLs in 5 scrolls
- ⚠️ Selector `img` returned JS files (.mjs) alongside images — need file extension filter
- Filter needed: `.jpg` / `.jpeg` / `.png` / `.webp` in src

### Downloads
- ✅ 8 real JPEG images downloaded successfully
- Sample resolutions: 1080×1920, 1340×1785, 736×980
- ⚠️ webp/originals/ URLs returned 403 (anti-hotlink)
- Fix: use requests with browser cookies, or download via page.get()
- ⚠️ page.get() on images returns bool, not Response — use requests+cookies

### Cookie Format
- DrissionPage cookies: list of dicts with keys `domain`, `expiry`, `httpOnly`, `name`, `path`, `secure`, `value`
- No `sameSite` field (unlike Playwright)
- Load: `page.set.cookies()` — NOT `set_cookie()` (method doesn't exist)
- Save: standard json.dump

## Key Differences from Playwright

| Aspect | Playwright | DrissionPage |
|---|---|---|
| Element find | `await page.wait_for_selector('input[type="email"]')` | `page.ele('css:input[type="email"]')` |
| Fill input | `await input.fill(text)` | `input.input(text)` |
| Press Enter | `await page.keyboard.press('Enter')` | Append `'\n'` to input string |
| Get attr | `await img.get_attribute('src')` | `img.attr('src')` |
| Screenshot | `await page.screenshot(...)` | `page.get_screenshot(...)` |
| Cookies | `await context.cookies()` | `page.cookies()` |
| Set cookies | `await context.add_cookies(list)` | `page.set.cookies()` |
| Proxy auth | Built-in `proxy={"username":...}` | NOT supported in set_proxy() — use Chromium args |
| Scroll | `await page.evaluate('window.scrollBy(0, 800)')` | `page.scroll.down(800)` |
| Async/await | Required | NOT required (blocking by default) |

## Proxy Auth Workaround for DrissionPage

```python
co.set_argument('--proxy-server=http://pool.gonzoproxy.com:1000')
# Then handle auth via:
# 1. Whitelisted IP (no auth needed)
# 2. Or proxy.pac / proxy auto-config
# 3. Or use Playwright instead
```

## Verdict

- **Anti-detect:** Better than manual Playwright scripts — less boilerplate
- **API simplicity:** Lower — fewer lines of code for same result
- **Proxy support:** Worse — no built-in auth
- **Cookie handling:** Different format, slightly incompatible with Playwright cookies
- **Overall:** Good choice if proxy doesn't need auth or if auth handled at network level
