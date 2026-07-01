#!/usr/bin/env python3
"""
Pinterest viewer: scroll, screenshot viewport, collect visible URLs.
Preview-first workflow — no downloading until user selects images.
Uses DrissionPage (less code than Playwright).
"""
import json, os, re, sys, time
from pathlib import Path
from DrissionPage import ChromiumPage, ChromiumOptions

# --- CONFIG ---
EMAIL = os.environ.get("PINTEREST_EMAIL", "")
PASSWORD=*** "")
OUTPUT_DIR = Path("/tmp/pinterest_viewer")
QUERY = "aesthetic wallpaper"  # Change per session
MAX_SCREENS = 5
SCROLL_STEP = 900
# ---------------


def get_chromium_path():
    import glob
    candidates = glob.glob('/root/.cache/ms-playwright/chromium-*/chrome-linux*/chrome')
    if candidates:
        return candidates[0]
    raise RuntimeError("Chromium not found. Run: playwright install chromium")


def setup_browser():
    co = ChromiumOptions()
    co.headless(False)  # NEVER True for Pinterest
    co.set_paths(browser_path=get_chromium_path())
    co.set_argument('--window-size=1920,1080')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--disable-infobars')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    )
    co.set_argument('--lang=en-US')
    page = ChromiumPage(addr_or_opts=co)
    page.run_js('''
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        window.chrome = { runtime: {} };
        delete navigator.__proto__.webdriver;
    ''')
    return page


def login(page):
    page.get('https://www.pinterest.com/login/')
    time.sleep(5)
    if '/login' not in page.url:
        print("[OK] Already logged in")
        return True
    try:
        page.ele('css:input[type="email"]', timeout=10).input(EMAIL)
        time.sleep(1)
        page.ele('css:input[type="password"]', timeout=10).input(PASSWORD)
        time.sleep(1)
        page.ele('css:button[type="submit"]', timeout=10).click()
        time.sleep(8)
        if '/login' not in page.url:
            print("[OK] Login successful")
            return True
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
    return False


def search_pinterest(page, query):
    print(f"[INFO] Searching: {query}")
    try:
        inp = page.ele('css:input[data-test-id="search-box-input"]', timeout=15)
        inp.input(query + '\n')
        time.sleep(8)
        print(f"[INFO] URL: {page.url}")
        return True
    except Exception as e:
        print(f"[ERROR] Search: {e}")
        return False


def collect_visible_urls(page):
    urls = []
    imgs = page.eles('css:img')
    for img in imgs:
        try:
            src = img.attr('src')
            if src and 'pinimg.com' in src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                urls.append(re.sub(r'/\d+x/', '/originals/', src))
        except:
            pass
    return urls


def download_selected(page, urls_to_download, out_dir):
    import requests
    out_dir.mkdir(parents=True, exist_ok=True)
    browser_cookies = {c['name']: c['value'] for c in page.cookies()}
    headers = {
        'Referer': 'https://www.pinterest.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    }
    downloaded = []
    for url in urls_to_download:
        try:
            fname = url.split('/')[-1]
            fpath = out_dir / fname
            resp = requests.get(url, headers=headers, cookies=browser_cookies, timeout=30)
            if resp.status_code == 200:
                with open(fpath, 'wb') as f:
                    f.write(resp.content)
                downloaded.append(str(fpath))
                print(f"[OK] {fname}")
            else:
                print(f"[WARN] HTTP {resp.status_code}")
        except Exception as e:
            print(f"[ERROR] {e}")
    return downloaded


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 50)
    page = setup_browser()
    try:
        login(page)
        search_pinterest(page, QUERY)

        all_data = []
        for i in range(1, MAX_SCREENS + 1):
            print(f"\n[INFO] Screen {i}/{MAX_SCREENS}")
            urls = collect_visible_urls(page)
            screenshot_path = OUTPUT_DIR / f"screen_{i}.png"
            page.get_screenshot(str(screenshot_path))
            data = {"screen": i, "urls": urls, "screenshot": str(screenshot_path)}
            all_data.append(data)
            with open(OUTPUT_DIR / f"screen_{i}.json", 'w') as f:
                json.dump(data, f, indent=2)
            print(f"[OK] Screenshot: {screenshot_path} | URLs: {len(urls)}")
            page.scroll.down(SCROLL_STEP)
            time.sleep(4)

        # Save master index
        with open(OUTPUT_DIR / "index.json", 'w') as f:
            json.dump(all_data, f, indent=2)
        print(f"\n[OK] Done. Data in {OUTPUT_DIR}")
        print("Next: review screenshots, pick URLs, call download_selected()")

    except Exception as e:
        print(f"[FATAL] {e}")
        import traceback; traceback.print_exc()
    finally:
        page.quit()


if __name__ == '__main__':
    main()
