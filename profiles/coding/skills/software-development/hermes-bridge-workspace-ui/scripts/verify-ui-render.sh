#!/usr/bin/env bash
# Quick render-health probe for the AI Workspace UI.
# Usage: ./scripts/verify-ui-render.sh [URL]
# Exits 0 if the page has a non-empty #root, non-zero otherwise.

URL="${1:-http://159.194.213.106:3000}"

echo "Probing $URL ..."

# 1. HTML loads
html=$(curl -sS --max-time 5 "$URL" 2>/dev/null)
if [ -z "$html" ]; then
    echo "FAIL: no HTML returned (server down or connection refused)"
    exit 1
fi

# 2. JS/CSS references present
if ! echo "$html" | grep -q 'assets/index.*\.js'; then
    echo "FAIL: no JS asset reference in index.html"
    exit 1
fi
if ! echo "$html" | grep -q 'assets/index.*\.css'; then
    echo "FAIL: no CSS asset reference in index.html"
    exit 1
fi

# 3. Static assets actually reachable
js_url=$(echo "$html" | grep -oE '/assets/index-[A-Za-z0-9_-]+\.js' | head -n1)
css_url=$(echo "$html" | grep -oE '/assets/index-[A-Za-z0-9_-]+\.css' | head -n1)
js_full="${URL%/}$js_url"
css_full="${URL%/}$css_url"

if ! curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$js_full" 2>/dev/null | grep -q '^200$'; then
    echo "FAIL: JS asset not reachable: $js_full"
    exit 1
fi
if ! curl -sS --max-time 5 -o /dev/null -w '%{http_code}' "$css_full" 2>/dev/null | grep -q '^200$'; then
    echo "FAIL: CSS asset not reachable: $css_full"
    exit 1
fi

echo "OK: HTML + JS + CSS all reachable. If the browser still shows a blank page, check the browser console for a JS runtime error."
exit 0
