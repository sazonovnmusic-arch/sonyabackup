#!/usr/bin/env python3
"""
YouTube Trend Scout — Find fast-growing Shorts channels.
Searches YouTube Data API for recent Shorts with 100K+ views,
then checks channel age and growth metrics.

Usage: python3 trend_scout.py [--max-queries 20] [--min-views 100000]

Requires: YOUTUBE_API_KEY in .env file
"""
import requests
import time
import json
import os
import argparse
from datetime import datetime, timedelta

SEARCH_QUERIES = [
    "amazing facts you didn't know shorts",
    "mind blowing facts shorts",
    "top 5 things shorts",
    "psychology tricks shorts",
    "did you know facts shorts",
    "life hacks shorts",
    "secrets you didn't know shorts",
    "scary facts shorts",
    "weird history facts shorts",
    "space facts shorts",
    "animal facts shorts",
    "body secrets shorts",
    "things you didn't know shorts",
    "hidden details shorts",
    "dark history shorts",
    "unsolved mysteries shorts",
    "survival hacks shorts",
    "technology facts shorts",
    "crazy facts shorts",
    "datos curiosos shorts",
    "curiosidades shorts",
    "rochak tathya shorts",
    "흥미로운 사실",
    "面白い事実",
]

def load_api_key():
    env_path = os.path.expanduser("~/.hermes/profiles/youtube/.env")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("YOUTUBE_API_KEY") and not line.startswith("#"):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("YOUTUBE_API_KEY not found in .env")

def search_shorts(api_key, query, published_after, max_results=10):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "order": "viewCount",
        "maxResults": max_results,
        "publishedAfter": published_after,
        "videoDuration": "short",
    }
    resp = requests.get(url, params=params, timeout=15)
    return resp.json()

def get_video_stats(api_key, video_ids):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "key": api_key,
        "id": ",".join(video_ids[:50]),
        "part": "statistics,snippet",
    }
    resp = requests.get(url, params=params, timeout=15)
    return resp.json()

def get_channel_details(api_key, channel_ids):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "key": api_key,
        "id": ",".join(channel_ids[:50]),
        "part": "snippet,statistics",
    }
    resp = requests.get(url, params=params, timeout=15)
    return resp.json()

def main():
    parser = argparse.ArgumentParser(description="YouTube Trend Scout")
    parser.add_argument("--max-queries", type=int, default=20, help="Max search queries to run")
    parser.add_argument("--min-views", type=int, default=100000, help="Min views threshold")
    parser.add_argument("--max-age-days", type=int, default=60, help="Max channel age in days")
    args = parser.parse_args()

    api_key = load_api_key()
    published_after = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    age_threshold = datetime.utcnow() - timedelta(days=args.max_age_days)

    all_candidates = []

    for i, query in enumerate(SEARCH_QUERIES[:args.max_queries]):
        print(f"[{i+1}/{min(args.max_queries, len(SEARCH_QUERIES))}] '{query}'...")
        try:
            data = search_shorts(api_key, query, published_after)
            video_ids = [item["id"]["videoId"] for item in data.get("items", []) if "videoId" in item.get("id", {})]
            if not video_ids:
                continue
            vids_data = get_video_stats(api_key, video_ids)
            for v in vids_data.get("items", []):
                views = int(v["statistics"].get("viewCount", 0))
                if views >= args.min_views:
                    all_candidates.append({
                        "videoId": v["id"],
                        "title": v["snippet"]["title"],
                        "channelId": v["snippet"]["channelId"],
                        "channelTitle": v["snippet"]["channelTitle"],
                        "views": views,
                        "publishedAt": v["snippet"]["publishedAt"],
                    })
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
        time.sleep(3)

    print(f"\nVideos with {args.min_views}+ views: {len(all_candidates)}")

    channel_ids = list(set(c["channelId"] for c in all_candidates))
    print(f"Unique channels: {len(channel_ids)}")

    young_channels = []
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i+50]
        try:
            ch_data = get_channel_details(api_key, batch)
            for ch in ch_data.get("items", []):
                created = datetime.strptime(ch["snippet"]["publishedAt"][:10], "%Y-%m-%d")
                if created > age_threshold:
                    subs = int(ch["statistics"].get("subscriberCount", 0))
                    total_views = int(ch["statistics"].get("viewCount", 0))
                    young_channels.append({
                        "channelId": ch["id"],
                        "channelTitle": ch["snippet"]["title"],
                        "channelCreated": ch["snippet"]["publishedAt"][:10],
                        "subscribers": subs,
                        "totalViews": total_views,
                        "videoCount": int(ch["statistics"].get("videoCount", 0)),
                        "country": ch["snippet"].get("country", "unknown"),
                        "viewsSubsRatio": round(total_views / max(subs, 1), 1),
                    })
        except Exception as e:
            print(f"  Channel batch error: {str(e)[:80]}")
        time.sleep(3)

    young_channels.sort(key=lambda x: x["subscribers"], reverse=True)
    print(f"\n=== Channels younger than {args.max_age_days} days: {len(young_channels)} ===\n")
    for ch in young_channels:
        print(f"  📺 {ch['channelTitle']}")
        print(f"     Created: {ch['channelCreated']} | Subs: {ch['subscribers']:,} | Views: {ch['totalViews']:,} | Videos: {ch['videoCount']} | Ratio: {ch['viewsSubsRatio']}x")
        print(f"     https://www.youtube.com/channel/{ch['channelId']}")
        print()

    output_path = "/tmp/trend_scout_results.json"
    with open(output_path, "w") as f:
        json.dump(young_channels, f, indent=2)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()