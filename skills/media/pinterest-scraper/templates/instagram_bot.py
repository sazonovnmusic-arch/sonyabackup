#!/usr/bin/env python3
"""
Instagram automation via Playwright.
Supports: login, DM sending, post uploading.
Uses headful browser with xvfb-run for servers.
"""

import asyncio
import os
import re
import random
import sys
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ============ PROXY CONFIG ============
PROXY_URL = "http://GonzoNvv5Rfv_c_fi_s_acc143(_ttl_240h:RqFaYSd6@pool.gonzoproxy.com:1000"

# ============ INSTAGRAM LOGIN ============
INSTAGRAM_USERNAME = ""  # Set before running
INSTAGRAM_PASSWORD = ""  # Set before running

# ============ SETTINGS ============
TIMEOUT_MS = 90000
COOKIES_FILE = Path("/tmp/instagram_cookies.json")


class InstagramBot:
    def __init__(self, proxy_url: str = PROXY_URL):
        self.proxy_url = proxy_url
        self.browser = None
        self.context = None
        self.page = None

    def _get_proxy_dict(self):
        parsed = urlparse(self.proxy_url)
        return {
            "server": f"http://{parsed.hostname}:{parsed.port}",
            "username": parsed.username,
            "password": parsed.password,
        }

    async def _launch_browser(self):
        print("[INFO] Launching browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            proxy=self._get_proxy_dict(),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--no-sandbox",
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = {runtime: {}};
            delete navigator.__proto__.webdriver;
        """)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(TIMEOUT_MS)

    async def _close_browser(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def _save_cookies(self):
        cookies = await self.context.cookies()
        COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)
        print(f"[INFO] Saved {len(cookies)} cookies")

    async def login(self, username: str, password: str):
        print(f"[INFO] Logging into Instagram as {username}...")
        await self.page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=TIMEOUT_MS)
        await asyncio.sleep(3)

        # Check if already logged in
        if "accounts/login" not in self.page.url:
            print("[INFO] Already on main page, might be logged in")
            # Check for profile icon
            profile = await self.page.query_selector('img[data-testid="user-avatar-current-user"]')
            if profile:
                print("[OK] Already logged in")
                return True

        # Fill login form
        try:
            username_input = await self.page.wait_for_selector('input[name="username"]', timeout=10000)
            await username_input.fill(username)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            pass_input = await self.page.query_selector('input[name="password"]')
            await pass_input.fill(password)
            await asyncio.sleep(random.uniform(0.5, 1.0))

            login_btn = await self.page.query_selector('button[type="submit"]')
            await login_btn.click()
            print("[INFO] Login submitted, waiting...")
            await asyncio.sleep(8)
        except Exception as e:
            print(f"[ERROR] Login form error: {e}")
            return False

        # Handle "Save Your Login Info?" popup
        await self._dismiss_save_login()

        # Handle "Turn on Notifications" popup
        await self._dismiss_notifications()

        # Check if we're logged in
        current_url = self.page.url
        print(f"[INFO] Current URL: {current_url}")

        if "accounts/login" in current_url or "challenge" in current_url:
            # Check for 2FA
            if await self._handle_2fa():
                return True
            print("[ERROR] Login failed or challenge required")
            await self.page.screenshot(path="/tmp/instagram_login_error.png", full_page=True)
            return False

        print("[OK] Logged in successfully")
        await self._save_cookies()
        return True

    async def _dismiss_save_login(self):
        """Click 'Not Now' on 'Save Your Login Info?' popup."""
        try:
            not_now = await self.page.wait_for_selector('button:has-text("Not Now")', timeout=8000)
            if not_now:
                await not_now.click()
                print("[INFO] Dismissed 'Save Login Info' popup")
                await asyncio.sleep(2)
        except:
            pass

    async def _dismiss_notifications(self):
        """Click 'Not Now' on notification popup."""
        try:
            not_now = await self.page.wait_for_selector('button:has-text("Not Now")', timeout=8000)
            if not_now:
                await not_now.click()
                print("[INFO] Dismissed notifications popup")
                await asyncio.sleep(2)
        except:
            pass

    async def _handle_2fa(self):
        """Handle 2FA code input if presented."""
        try:
            code_input = await self.page.wait_for_selector('input[name="verificationCode"]', timeout=5000)
            if code_input:
                print("[WARN] 2FA required! Enter code in browser or provide via script.")
                # Wait for manual input or implement TOTP
                await asyncio.sleep(30)
                return "accounts/login" not in self.page.url
        except:
            pass
        return False

    async def send_dm(self, recipient: str, message: str):
        """Send a DM to a user."""
        print(f"[INFO] Sending DM to {recipient}...")

        # Click messages icon
        try:
            msg_link = await self.page.wait_for_selector('a[href="/direct/inbox/"]', timeout=10000)
            await msg_link.click()
            await asyncio.sleep(4)
        except:
            await self.page.goto("https://www.instagram.com/direct/inbox/", wait_until="networkidle")
            await asyncio.sleep(4)

        # Click "New message" button
        try:
            new_msg_btn = await self.page.wait_for_selector('svg[aria-label="New message"]', timeout=10000)
            await new_msg_btn.click()
            await asyncio.sleep(3)
        except:
            print("[ERROR] Could not find 'New message' button")
            return False

        # Search for recipient
        try:
            search_input = await self.page.wait_for_selector('input[name="queryBox"]', timeout=10000)
            await search_input.fill(recipient)
            await asyncio.sleep(3)

            # Click on user in results
            user_result = await self.page.wait_for_selector(f'div:has-text("{recipient}")', timeout=10000)
            await user_result.click()
            await asyncio.sleep(1)

            # Click "Chat" button
            chat_btn = await self.page.query_selector('button:has-text("Chat")')
            if chat_btn:
                await chat_btn.click()
                await asyncio.sleep(3)
        except Exception as e:
            print(f"[ERROR] Could not find recipient: {e}")
            return False

        # Type and send message
        try:
            msg_input = await self.page.wait_for_selector('div[contenteditable="true"]', timeout=10000)
            await msg_input.fill(message)
            await asyncio.sleep(1)

            send_btn = await self.page.query_selector('button:has-text("Send")')
            if send_btn:
                await send_btn.click()
                print(f"[OK] DM sent to {recipient}")
                await asyncio.sleep(2)
                return True
        except Exception as e:
            print(f"[ERROR] Could not send message: {e}")
            return False

        return False

    async def upload_post(self, image_path: str, caption: str = ""):
        """Upload a post to Instagram."""
        print(f"[INFO] Uploading post: {image_path}")

        # Click create button (+ icon)
        try:
            create_btn = await self.page.wait_for_selector('svg[aria-label="New post"]', timeout=10000)
            await create_btn.click()
            await asyncio.sleep(3)
        except:
            print("[ERROR] Could not find 'New post' button")
            return False

        # Upload file
        try:
            file_input = await self.page.wait_for_selector('input[type="file"]', timeout=10000)
            await file_input.set_input_files(image_path)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[ERROR] Could not upload file: {e}")
            return False

        # Click "Next" twice
        for _ in range(2):
            try:
                next_btn = await self.page.wait_for_selector('button:has-text("Next")', timeout=10000)
                await next_btn.click()
                await asyncio.sleep(3)
            except:
                print("[WARN] Could not click Next")

        # Add caption
        try:
            caption_input = await self.page.wait_for_selector('div[aria-label="Write a caption..."]', timeout=10000)
            await caption_input.fill(caption)
            await asyncio.sleep(1)
        except:
            print("[WARN] Could not add caption")

        # Click "Share"
        try:
            share_btn = await self.page.wait_for_selector('button:has-text("Share")', timeout=10000)
            await share_btn.click()
            print("[OK] Post shared!")
            await asyncio.sleep(5)
            return True
        except Exception as e:
            print(f"[ERROR] Could not share post: {e}")
            return False

    async def run(self, mode: str = "login", **kwargs):
        try:
            await self._launch_browser()

            if mode == "login":
                username = kwargs.get("username", "")
                password = kwargs.get("password", "")
                if not username or not password:
                    print("[ERROR] Username and password required")
                    return False
                return await self.login(username, password)

            elif mode == "dm":
                username = kwargs.get("username", "")
                password = kwargs.get("password", "")
                recipient = kwargs.get("recipient", "")
                message = kwargs.get("message", "")
                if not all([username, password, recipient, message]):
                    print("[ERROR] Missing required parameters for DM")
                    return False
                await self.login(username, password)
                return await self.send_dm(recipient, message)

            elif mode == "post":
                username = kwargs.get("username", "")
                password = kwargs.get("password", "")
                image_path = kwargs.get("image_path", "")
                caption = kwargs.get("caption", "")
                if not all([username, password, image_path]):
                    print("[ERROR] Missing required parameters for post")
                    return False
                await self.login(username, password)
                return await self.upload_post(image_path, caption)

            else:
                print(f"[ERROR] Unknown mode: {mode}")
                return False

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self._close_browser()


async def main():
    if len(sys.argv) < 2:
        print("""
Instagram Bot Usage:

1. Login test:
   xvfb-run python3 instagram_bot.py login username password

2. Send DM:
   xvfb-run python3 instagram_bot.py dm username password recipient "message text"

3. Upload post:
   xvfb-run python3 instagram_bot.py post username password /path/to/image.jpg "Caption text"
        """)
        sys.exit(1)

    mode = sys.argv[1]
    bot = InstagramBot()

    if mode == "login":
        await bot.run("login", username=sys.argv[2], password=sys.argv[3])
    elif mode == "dm":
        await bot.run("dm", username=sys.argv[2], password=sys.argv[3],
                     recipient=sys.argv[4], message=sys.argv[5])
    elif mode == "post":
        await bot.run("post", username=sys.argv[2], password=sys.argv[3],
                     image_path=sys.argv[4], caption=" ".join(sys.argv[5:]))
    else:
        print(f"Unknown mode: {mode}")


if __name__ == "__main__":
    asyncio.run(main())
