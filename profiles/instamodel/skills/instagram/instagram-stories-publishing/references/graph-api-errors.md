# Instagram Graph API — Collected Errors & Fixes

## Error: "Application does not have permission for this action"
**Message:** `(#10) Application does not have permission for this action`
**Cause:** The Facebook App has NOT completed Business Verification and therefore lacks Advanced Access for `instagram_content_publish`. Token is valid for reading (`GET /media`) but NOT for creating stories (`POST /media`).
**Fix:** Submit the app for Business Verification at https://developers.facebook.com/apps/ → App Review → Business Verification. After approval, request Advanced Access for `instagram_content_publish`. Alternatively, use a third-party service (e.g., PostMyPost) that is already verified.

## Error: "Session has expired"
**Message:** `Session has expired on Tuesday, 23-Jun-26 16:00:00 PDT`
**Cause:** Using a short-lived token from Graph API Explorer without exchanging for long-lived.
**Fix:** Exchange token via `GET /oauth/access_token?grant_type=fb_exchange_token&...` (see SKILL.md).

## Error: "Your account has limitations" (Instagram)
**Message:** "Для вашего аккаунта установлены ограничения... Повторите попытку позже."
**Cause:** Instagram rate-limits linking attempts between Creator account and Facebook Page.
**Fix:** Wait 24-72 hours. Do not retry aggressively — it extends the block.

## Error: "Failed to create a Page"
**Message:** "Не удалось создать Страницу: Недавно вы пытались создать Страницу слишком много раз."
**Cause:** Facebook rate-limits Page creation attempts.
**Fix:** Wait 24-48 hours. Or use an existing old Page. Or create from a different Facebook account.

## Error: "PostMyPost API not supported"
**Message:** "Ваш тариф не поддерживает API"
**Cause:** PostMyPost requires paid tier for API access.
**Fix:** Upgrade PostMyPost plan, or use direct Graph API (this skill).

## Error: "Tunnel URL not found"
**Cause:** cloudflared didn't start or didn't output URL within 45 seconds.
**Fix:** Check `/tmp/cloudflared` exists and is executable. Ensure port 8000 is free.

## Error: "Container creation failed"
**Cause:** Image URL not accessible from Facebook's servers, or token lacks `instagram_content_publish` permission.
**Fix:** Verify tunnel URL is reachable via `curl`. Check token permissions in Graph API Explorer.
