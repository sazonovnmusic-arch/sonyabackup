---
name: media-buying
description: Automated media buying and traffic arbitrage via ad-platform APIs (TikTok Ads, Meta/Facebook Ads). Covers campaign management, creative upload, analytics, and auto-shutoff workflows.
version: 1.0.0
author: agent
tags: [marketing, advertising, tiktok, meta, facebook, api, automation, arbitrage]
---

# Media Buying & Traffic Arbitrage

Automate the creation, monitoring, and optimization of paid advertising campaigns through platform APIs. Primary focus: TikTok Ads API; secondary: Meta Marketing API.

## 1. Prerequisites

### TikTok Developer Account
1. Register at https://ads.tiktok.com/business/apps
2. Create an app → get **App ID** + **App Secret**
3. Complete OAuth flow → get **Access Token**
4. Note your **Advertiser ID**

### Credentials
Store in profile `.env`:
```bash
TIKTOK_APP_ID=***
TIKTOK_APP_SECRET=***
TIKTOK_ACCESS_TOKEN=***
TIKTOK_ADVERTISER_ID=***
```

## 2. API Quick Reference

### Campaign Lifecycle
```bash
# List campaigns
GET /open_api/v1.3/campaign/get/
  -H "Access-Token: $TIKTOK_ACCESS_TOKEN"

# Create campaign
POST /open_api/v1.3/campaign/create/
{
  "advertiser_id": "xxx",
  "campaign_name": "MyCampaign",
  "objective_type": "CONVERSIONS",
  "budget_mode": "BUDGET_MODE_DAY",
  "budget": 100.00
}

# Toggle status
POST /campaign/status/update/
{"campaign_ids": ["xxx"], "operation_status": "ENABLE|DISABLE"}
```

### Creative Upload
```bash
POST /open_api/v1.3/tt_video/create/
- multipart/form-data
- video_file: binary
```

### Reporting
```bash
POST /open_api/v1.3/report/integrated/get/
{
  "advertiser_id": "xxx",
  "dimensions": ["campaign_id", "adgroup_id"],
  "metrics": ["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "conversions"],
  "time_range": {"start_date": "2024-01-01", "end_date": "2024-01-07"}
}
```

## 3. Auto-Shutoff Algorithm

```
Every 30 minutes:
  For each ACTIVE campaign:
    If Spend > Budget * 0.9     → NOTIFY "90% budget spent"
    If CTR < 0.5% AND Spend > $10 → DISABLE, NOTIFY "poor CTR"
    If CPA > Target * 2           → DISABLE, NOTIFY "CPA too high"
    If Status = REJECTED           → NOTIFY "ad rejected"
```

## 4. Campaign Structure

```
Campaign
  → Objective: APP_INSTALL | CONVERSIONS | TRAFFIC | LEAD_GEN
  → Budget: daily | total
  → Status: ENABLE | DISABLE

  Ad Group
    → Audience: age, gender, interests, custom_audience
    → Bidding: lowest_cost | cost_cap | bid_cap
    → Schedule: start_time, end_time
    → Placement: TikTok only / Pangle / etc

    Ad
      → Video ID (from tt_video/create)
      → Headline text
      → CTA: DOWNLOAD_NOW | LEARN_MORE | SHOP_NOW
      → Landing page URL
```

## 5. Metrics Glossary

| Metric | Meaning | Action Threshold |
|--------|---------|------------------|
| CTR | Click-Through Rate (clicks/impressions) | < 0.5% → pause |
| CPC | Cost Per Click | Spike 2x → investigate |
| CPM | Cost Per 1000 impressions | Benchmark vs vertical |
| CPA | Cost Per Acquisition | > 2x target → pause |
| ROI | Return on Investment | Negative → restructure |
| Spend | Total spent | 90% budget → alert |

## 6. Working Around Geo-Blocked Documentation

TikTok's official help center (`ads.tiktok.com/help`) frequently blocks cloud/datacenter IPs with `403` or `ERR_HTTP_RESPONSE_CODE_FAILURE`. When you need to scrape docs:

1. **Use a residential proxy** (e.g. Gonzo HTTP proxy):  
   ```bash
   curl -x "http://USER:PASS@HOST:PORT" -A "Mozilla/5.0" "https://r.jina.ai/http://ads.tiktok.com/help/article/ARTICLE_SLUG"
   ```
2. **Jina AI summarizer** (`r.jina.ai/http://URL`) strips JS and returns clean Markdown — ideal for headless extraction.
3. **Never trust raw JS arrays** from TikTok pages as "available geo lists." The site embeds a 249-country ISO lookup table that is NOT the same as ad-delivery markets.

## 7. How to Find the REAL TikTok Ads Geo List

**For regular ad accounts:**  
Read `https://ads.tiktok.com/help/article/placements-available-locations` (via proxy). It shows ~52 countries grouped by **account registration country**. Example: an Australia-registered account can target AU, US, UK, EG, KR, etc.

**For agency accounts:**  
There is **no public doc** with a "master list of all agency geos." Agency accounts bypass most registration-country restrictions, but the authoritative list lives inside the Ads Manager UI:
- Create Campaign → Ad Group → **Location** → open the dropdown.
- Screenshot or export what you see — that is the ground truth.

**Pitfall — fake geo lists:**  
Some agents scrape the 249-country ISO table from TikTok's frontend JS and claim it as "all available agency geos." This is wrong — it includes India (banned), Antarctica, and sanctioned countries that cannot be targeted. Always verify against the live UI or the official placements-available-locations page.

## 8. Pitfalls

1. **Moderation surprises** — TikTok rejects creatives without explanation. Always maintain backup creatives.
2. **Pixel required** — Conversion campaigns need TikTok Pixel installed on the landing page.
3. **Rate limits** — 1000 requests/minute per app. Batch operations when possible.
4. **Business verification** — Unverified accounts have spend caps.
5. **Duplicate tokens** — If a profile inherits `.env` from default, check for stale `TELEGRAM_BOT_TOKEN` lines that collide with the ad-bot token.
6. **Proxy for doc research** — Always route documentation scraping through a residential proxy; TikTok aggressively blocks cloud IPs.

## References

- `references/tiktok-api-endpoints.md` — condensed endpoint list with examples
- `references/tiktok-creative-specs.md` — video formats, sizes, requirements
- `scripts/auto_shutoff.py` — standalone watchdog script for campaign monitoring

## Related Skills

- `hermes-profiles` — isolate ad-buying profile from personal/coding profiles
- `server-monitoring` — host health for the API automation server
- `cronjob` — schedule periodic campaign checks
