#!/usr/bin/env python3
"""
Full channel analytics for sostv — fetch all videos with stats, compare periods,
break down by franchise, analyze duration impact, and identify trends.

Usage:
  python channel_analytics.py                          # full analysis
  python channel_analytics.py --channel UC50sOtfTWbnxQmILslaWYZw  # Buzz TV
  python channel_analytics.py --recent 20              # focus on last 20 videos
  python channel_analytics.py --compare-days 30        # compare last 30 vs prev 30 days

Requires YOUTUBE_API_KEY in ~/.hermes/profiles/youtube/.env
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone, timedelta

DEFAULT_CHANNEL_ID = "UCsRu63L7bGHR7oafkuLROhw"  # sostv

# Franchise keyword mapping (lowercase search terms)
FRANCHISE_KEYWORDS = {
    # Fatigued franchises (DO NOT use — documented in references/fresh-topic-research.md)
    "Головоломка": ["головолом", "inside out", "райли", "riley", "bing bong", "бинг", "бонго", "эмоци"],
    "Зверополис": ["зверопол", "zootopia", "джуди", "judy", "ник ник", "nick wilde", "ник уайлд"],
    "ВАЛЛ-И": ["валл", "wall-e", "walle"],
    "Человек-паук": ["паук", "spider", "spider-man"],
    # Secondary franchises (use sparingly)
    "История Игрушек": ["история игрушек", "toy story", "вуди", "woody", "buzz lightyear", "баз", "энди", "andу", "бонни", "bonnie", "сид"],
    "Миньоны/Гадкий Я": ["миньон", "гадкий", "gru", "minion", "despicable", "грю"],
    "Супер Марио": ["марио", "mario"],
    # New priority franchises (untapped — validated June 2026)
    "Ральф": ["ральф", "ralph", "wreck-it", "венелопа", "venelop"],
    "Суперсемейка": ["суперсемейн", "incredib", "синдром", "syndrome", "frozone"],
    "Холодное сердце": ["холодн", "frozen", "эльза", "elsa", "anna", "анна"],
    "Шрек": ["шрек", "shrek", "fiona", "фиона"],
    "Лука": ["лука", "luca pixar", "альберто", "alberto"],
    "Моана": ["моана", "moana", "мауи", "maui"],
    "Мадагаскар": ["мадагаскар", "madagascar", "пингвин", "penguin", "skipper", "скиппер"],
    "Коко": ["коко", "coco pixar", "hector", "гектор", "miguel", "мигель"],
    "Король Лев": ["король лев", "lion king", "mufasa", "муфаса", "scar", "шрам", "simba", "симба"],
    "Энканто": ["энканто", "encanto", "mirabel", "мирабель", "bruno", "бруно"],
    "Как приручить дракона": ["дракон", "dragon", "toothless", "беззубик", "hiccup", "иккинг", "httyd"],
    "Boss Baby": ["boss baby", "босс младенец", "босс-младенец"],
    "Paddington": ["паддингтон", "paddington"],
    "Wednesday": ["wednesday", "уэнсдей", "addams", "аддамс"],
}

def load_api_key():
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        env_path = os.path.expanduser("~/.hermes/profiles/youtube/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("YOUTUBE_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        break
    if not key:
        print("ERROR: YOUTUBE_API_KEY not found", file=sys.stderr)
        sys.exit(1)
    return key

def parse_duration(duration_str):
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)

def get_channel_info(api_key, channel_id):
    url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={channel_id}&key={api_key}"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    if not data.get("items"):
        print(f"Channel {channel_id} not found", file=sys.stderr)
        sys.exit(1)
    return data["items"][0]

def get_all_videos(api_key, channel_id, max_pages=4):
    # Get uploads playlist
    ch = get_channel_info(api_key, channel_id)
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    
    all_videos = []
    next_page = None
    for _ in range(max_pages):
        url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={uploads}&maxResults=50&key={api_key}"
        if next_page:
            url += f"&pageToken={next_page}"
        with urllib.request.urlopen(url) as resp:
            data = json.load(resp)
        for item in data.get("items", []):
            all_videos.append({
                "id": item["contentDetails"]["videoId"],
                "publishedAt": item["contentDetails"]["videoPublishedAt"],
                "title": item["snippet"]["title"],
            })
        next_page = data.get("nextPageToken")
        if not next_page:
            break
    
    # Get stats in batches
    all_stats = []
    for i in range(0, len(all_videos), 50):
        batch = all_videos[i:i+50]
        ids = ",".join(v["id"] for v in batch)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id={ids}&key={api_key}"
        with urllib.request.urlopen(url) as resp:
            data = json.load(resp)
        for item in data.get("items", []):
            s = item["statistics"]
            cd = item["contentDetails"]
            sn = item["snippet"]
            all_stats.append({
                "id": item["id"],
                "title": sn["title"],
                "publishedAt": sn["publishedAt"],
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
                "dur_sec": parse_duration(cd.get("duration", "PT0S")),
            })
    
    all_stats.sort(key=lambda x: x["publishedAt"], reverse=True)
    return ch, all_stats

def classify_franchise(title):
    title_lower = title.lower()
    for franchise, keywords in FRANCHISE_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return franchise
    return "Другое"

def format_num(n):
    return f"{n:,}"

def run_analysis(api_key, channel_id, recent_n=30, compare_days=30):
    ch, videos = get_all_videos(api_key, channel_id)
    stats = ch["statistics"]
    
    print("=" * 65)
    print(f"📊 CHANNEL ANALYSIS: {ch['snippet']['title']}")
    print("=" * 65)
    print(f"Subscribers: {int(stats['subscriberCount']):,}")
    print(f"Total views: {int(stats['viewCount']):,}")
    print(f"Total videos: {stats['videoCount']}")
    print(f"Created: {ch['snippet']['publishedAt'][:10]}")
    print(f"Videos analyzed: {len(videos)}")
    
    # Assign franchises
    for v in videos:
        v["franchise"] = classify_franchise(v["title"])
    
    # Latest N videos
    print(f"\n{'=' * 65}")
    print(f"🎬 LATEST {min(recent_n, len(videos))} VIDEOS")
    print("=" * 65)
    now = datetime.now(timezone.utc)
    for v in videos[:recent_n]:
        pub = datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00"))
        days = (now - pub).days
        like_rate = (v["likes"] / v["views"] * 100) if v["views"] > 0 else 0
        print(f"  {v['publishedAt'][:10]} | {format_num(v['views']):>10} | {days:>3}d | {v['dur_sec']:>3}s | {like_rate:.1f}% | {v['franchise']:<20} | {v['title'][:40]}")
    
    # Trend: groups of 10
    print(f"\n{'=' * 65}")
    print("📈 TREND ANALYSIS (groups of 10)")
    print("=" * 65)
    print(f"{'Group':<25} {'Avg Views':>12} {'Median':>10} {'Min':>10} {'Max':>10}")
    print("-" * 70)
    for i in range(0, min(len(videos), 50), 10):
        group = videos[i:i+10]
        if not group:
            break
        views = [v["views"] for v in group]
        avg = sum(views) / len(views)
        med = sorted(views)[len(views) // 2]
        label = f"Videos {i+1}-{i+len(group)}"
        print(f"{label:<25} {format_num(int(avg)):>12} {format_num(med):>10} {format_num(min(views)):>10} {format_num(max(views)):>10}")
    
    # Period comparison
    print(f"\n{'=' * 65}")
    print(f"📊 PERIOD COMPARISON (last {compare_days}d vs previous {compare_days}d)")
    print("=" * 65)
    d_recent = now - timedelta(days=compare_days)
    d_prev = now - timedelta(days=compare_days * 2)
    
    recent = [v for v in videos if datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00")) > d_recent]
    previous = [v for v in videos if d_prev < datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00")) <= d_recent]
    
    for label, group in [(f"Last {compare_days}d", recent), (f"Previous {compare_days}d", previous)]:
        if not group:
            print(f"  {label}: no data")
            continue
        views = [v["views"] for v in group]
        avg = sum(views) / len(views)
        med = sorted(views)[len(views) // 2]
        print(f"  {label} ({len(group)} videos): avg {format_num(int(avg))}, median {format_num(med)}, total {format_num(sum(views))}")
    
    if recent and previous:
        r_avg = sum(v["views"] for v in recent) / len(recent)
        p_avg = sum(v["views"] for v in previous) / len(previous)
        if p_avg > 0:
            change = ((r_avg - p_avg) / p_avg) * 100
            direction = "📈" if change > 0 else "📉"
            print(f"\n  {direction} Change: {change:+.0f}%")
    
    # Franchise breakdown
    print(f"\n{'=' * 65}")
    print("🎭 FRANCHISE BREAKDOWN (all videos)")
    print("=" * 65)
    franchise_data = defaultdict(lambda: {"count": 0, "views": []})
    for v in videos:
        franchise_data[v["franchise"]]["count"] += 1
        franchise_data[v["franchise"]]["views"].append(v["views"])
    
    print(f"{'Franchise':<25} {'Videos':>6} {'Avg Views':>12} {'Max':>10}")
    print("-" * 55)
    for fr, data in sorted(franchise_data.items(), key=lambda x: sum(x[1]["views"]) / max(len(x[1]["views"]), 1), reverse=True):
        avg = sum(data["views"]) / len(data["views"])
        mx = max(data["views"])
        print(f"{fr:<25} {data['count']:>6} {format_num(int(avg)):>12} {format_num(mx):>10}")
    
    # Duration analysis
    print(f"\n{'=' * 65}")
    print("⏱ DURATION ANALYSIS (last 20 videos)")
    print("=" * 65)
    recent20 = videos[:20]
    short = [v for v in recent20 if v["dur_sec"] <= 50]
    long = [v for v in recent20 if v["dur_sec"] > 50]
    if short:
        print(f"  ≤50s: {len(short)} videos, avg {format_num(sum(v['views'] for v in short) // max(len(short), 1))} views")
    if long:
        print(f"  >50s: {len(long)} videos, avg {format_num(sum(v['views'] for v in long) // max(len(long), 1))} views")
    
    # Top 10 all-time
    print(f"\n{'=' * 65}")
    print("🏆 TOP 10 ALL-TIME")
    print("=" * 65)
    for i, v in enumerate(sorted(videos, key=lambda x: x["views"], reverse=True)[:10], 1):
        print(f"  {i:>2}. {format_num(v['views']):>10} | {v['publishedAt'][:10]} | {v['title'][:50]}")
    
    # Worst 5 recent
    print(f"\n{'=' * 65}")
    print("⚠️ WORST 5 (recent 10)")
    print("=" * 65)
    for v in sorted(videos[:10], key=lambda x: x["views"])[:5]:
        print(f"  {format_num(v['views']):>10} | {v['publishedAt'][:10]} | {v['title'][:50]}")

def main():
    parser = argparse.ArgumentParser(description="Full channel analytics")
    parser.add_argument("--channel", default=DEFAULT_CHANNEL_ID, help="Channel ID")
    parser.add_argument("--recent", type=int, default=30, help="Number of recent videos to show")
    parser.add_argument("--compare-days", type=int, default=30, help="Days for period comparison")
    args = parser.parse_args()
    
    api_key = load_api_key()
    run_analysis(api_key, args.channel, args.recent, args.compare_days)

if __name__ == "__main__":
    main()