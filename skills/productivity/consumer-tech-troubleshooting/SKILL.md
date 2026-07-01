---
name: consumer-tech-troubleshooting
description: "Help users with hotel TVs, Smart TV streaming, geoblocks, sideloading, and travel networking. Pragmatic consumer electronics debugging without over-engineering."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [any]
metadata:
  hermes:
    tags: [smart-tv, hotel, streaming, vpn, geoblock, travel, consumer-electronics]
    related_skills: [server-management, hermes-profiles]
---

# Consumer Tech Troubleshooting

Class-level skill for helping users with consumer electronics while traveling or at home — Smart TVs, hotel Wi-Fi, streaming geoblocks, APK sideloading, networking.

## Core Principle

> Никита is aggressively pragmatic. He despises over-engineering. For ANY consumer-tech request (hotel, TV, device, streaming) start with EXACTLY ONE simple solution (HDMI cable, phone as hotspot, watch on laptop/phone). Only if rejected, THEN offer complex paths (Developer Mode, APK, proxy, DNS). Do NOT dump a wall of 5 options.

This principle overrides any default urge to be thorough. If the simple path works, stop there.

## Decision Tree

### 1. Does the user have a laptop and HDMI cable?
**Yes:** → Plug laptop into TV. Done. Nothing else matters.

### 2. No laptop / no cable?
Check what the user actually HAS:
- Phone only? → Offer phone screen mirroring (ONE sentence), or phone as Wi-Fi hotspot with VPN.
- MacBook only? → Watch on MacBook. Don't suggest complex hotspot routing unless asked.
- USB flash drive? → Maybe sideloading, but only if TV is Android TV.

### 3. Streaming geoblock (OKKO, RuTube, VK Video — Russia-only)
- **Simplest:** Look for same stream on YouTube (most Russian esports/events mirrored there).
- **Next:** Phone with Russian VPN as Wi-Fi hotspot → TV connects to phone.
- **Complex (only if asked):** Smart DNS, proxy in TV settings, Developer Mode + .ipk on webOS.

## Smart TV Platform Quick-ID

| Platform | Store | APK/IPK? | Developer Mode? | Notes |
|---|---|---|---|---|
| Android TV (Google TV) | Google Play Store / Content Store | APK sideload via USB, ADB, or Send files to TV | Via Settings → About → tap Build 7× | Most flexible |
| webOS (LG, some Aiwa, others) | LG Content Store | .ipk only, requires webOS Dev Manager on PC | Via "Developer Mode" app from store | No APK support |
| Tizen (Samsung) | Samsung App Store | .wgt / Tizen Studio | Yes, complex | Rare outside Korea |
| Roku | Roku Channel Store | No sideload | Hidden dev menu | Very locked |
| Fire TV (Amazon) | Amazon Appstore | APK via ADB, Downloader app | ADB over USB/Wi-Fi | Easy sideload |
| Apple TV | tvOS App Store | No sideload | Requires Xcode + dev cert | Ignore for most users |

**Critical:** If user says "Content Store has no Twitch" — first identify the platform. On webOS, Twitch may simply not be in the regional LG Content Store. On Android TV, it might be hidden by region. The fix differs completely.

## webOS Developer Mode (for .ipk sideloading)

ONLY applicable to webOS (LG, some Aiwa, etc.). Steps:

1. Open **LG Content Store** → search **"Developer Mode"** → install.
2. Open app → toggle **Dev Mode Status ON** → restart TV.
3. App shows a **Key** (device IP or code).
4. On PC/Mac: register at [developer.lge.com](https://developer.lge.com) → enter TV Key.
5. Download **webOS Dev Manager** (Windows/Mac) or CLI.
6. Install `.ipk` file to TV.

**Blocker:** Without a PC/Mac, Developer Mode is useless. The user cannot sideload apps from the TV itself. If no laptop — abandon this path immediately.

## Hotel Wi-Fi Restrictions

Common hotel network blocks:
- **Port filtering** — blocks VPN ports (1194, 443 with certain signatures)
- **MAC whitelisting** — captive portal, but TV can't authenticate
- **Speed throttling** — too slow for HD streaming
- **AP isolation** — devices can't see each other

**Workarounds:**
- Phone as hotspot bypasses all hotel restrictions (uses mobile data).
- If hotel Wi-Fi requires browser login: many TVs can't handle captive portals. Use phone hotspot.
- Ethernet in room? Often unrestricted. Worth trying before Wi-Fi.

## Platform-Specific Reference Files

- `references/smart-tv-platform-matrix.md` — Platform identification, store names, sideloading methods, developer mode steps per platform.
- `references/webos-developer-mode.md` — Exact steps for webOS Developer Mode activation, LG developer account, and .ipk installation.
- `references/hotel-networking.md` — Common hotel network restrictions and quick bypasses.
