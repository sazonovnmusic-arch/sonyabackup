# TikTok Ads Geo Targeting Research Notes

## Proxy Configuration Used

Residential proxy (Gonzo) to bypass TikTok doc IP blocks:
```
http://GonzoNvv5Rfv_c_us_s_acc69)7(_ttl_6h:RqFaYSd6@62.169.20.75:1000
http://GonzoNvv5Rfv_c_fi_s_acc142(_ttl_240h:RqFaYSd6@pool.gonzoproxy.com:1000
```
Pattern: `login:pass@host:port` via `curl -x`.

## Key Pages

| URL | What It Contains |
|-----|-----------------|
| `ads.tiktok.com/help/article/placements-available-locations` | Regular-account geo list (~52 countries) grouped by registration country |
| `ads.tiktok.com/help/article/location-targeting` | How location targeting works (no country list) |
| `ads.tiktok.com/help/article/ad-targeting` | Targeting dimensions overview |

## What We Learned

1. **Regular accounts:** ~52 countries available, but WHICH ones depend on where the account was registered. A Brazil-registered account sees BR, CL, MX, EG, ID, etc. An Austria-registered account sees most of Western Europe + MENA.

2. **Agency accounts:** No public master list exists. The real list is inside Ads Manager UI (Campaign → Ad Group → Location dropdown). Agency accounts bypass registration-country restrictions and can target far more geos.

3. **Fake geo trap:** TikTok's frontend JS embeds a 249-country ISO lookup table. Scraping this and calling it "all agency geos" is a common mistake. That table includes India (banned since 2020), Antarctica, and sanctioned countries — none of which are ad-delivery markets.

4. **Jina AI trick:** `r.jina.ai/http://URL` converts any webpage to clean Markdown via a third-party service. Works well for bypassing JS-heavy pages and extracting text without rendering.
