# Pinterest Scraper Test Results

Date: 2026-06-23
Tester: Hermes Agent
Status: ✅ Working

## Proxy Configuration Used

- **Working proxy**: Gonzoproxy FI pool, acc143
  - `GonzoNvv5Rfv_c_fi_s_acc143(_ttl_240h:RqFaYSd6@pool.gonzoproxy.com:1000`
  - IP: 178.75.160.251

- **Dead proxies** (do not use):
  - US proxy `62.169.20.75:1000` → 503 No exit node
  - FI pool acc142 → blocked by Pinterest (captcha triggered after multiple runs)
  - Backup proxy `45.14.112.25:24295` → blocked by Pinterest (captcha on login page)

## Test Execution

```bash
xvfb-run -a python3 pinterest_downloader.py 'stories aesthetic girl' 3
```

Results:
- ✅ Browser launched with headful mode + xvfb
- ✅ Pinterest login page loaded via proxy (networkidle + 5s sleep)
- ✅ Credentials filled: `input[type="email"]` and `input[type="password"]`
- ✅ Login successful, redirected to `https://www.pinterest.com/`
- ✅ 11 cookies saved to `/tmp/pinterest_cookies.json`
- ✅ Onboarding handled (0 interests selected, search still accessible)
- ✅ Search submitted for "stories aesthetic girl"
- ✅ 3 image URLs collected from `i.pinimg.com`
- ✅ 3 images downloaded to `/tmp/pinterest_images/`
  - stories_aesthetic_girl_001.jpg (121KB)
  - stories_aesthetic_girl_002.jpg (159KB)
  - stories_aesthetic_girl_003.jpg (15KB)

## Critical Findings

### Block Detection
Pinterest HTML always contains "captcha" and "blocked" in scripts (reCAPTCHA integration).
**Do NOT** use simple string search in HTML body.
Correct approach: check for visible `iframe[src*="recaptcha"]` or specific block messages.

### Headless Detection
Pinterest detects headless Chromium.
- `headless=True` → login works but onboarding/search may fail silently
- `headless=False` + `xvfb-run` → fully working
Required args: `--disable-blink-features=AutomationControlled`, antidetect init script

### Page Load Strategy
- `wait_until="domcontentloaded"` → too early, React form not rendered
- `wait_until="networkidle"` + `sleep(5)` → correct for login form
- `sleep(8)` after submit → correct for redirect

### Onboarding Behavior
After first login Pinterest shows "What interests you?" modal in Russian (Что вас интересует?).
Search bar at top is still accessible even without completing onboarding.
Clicking 3 interest cards + continue button also works for clean state.

## Image Quality

Default scraped URLs: `https://i.pinimg.com/236x/...` (low-res)
High-res conversion: replace `/236x/` with `/originals/`
Example:
- `https://i.pinimg.com/236x/54/33/83/543383267b5517191ed6e9435249264d.jpg`
- → `https://i.pinimg.com/originals/54/33/83/543383267b5517191ed6e9435249264d.jpg`
