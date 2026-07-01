#!/usr/bin/env python3
"""
Search YouTube Shorts by keyword, sort by views, and optionally fetch transcripts.

Usage:
  python search_youtube.py "hidden details inside out" --max 15
  python search_youtube.py "easter eggs encanto" --max 10 --transcripts
  python search_youtube.py "fan theory toy story" --max 10 --lang es

Requires YOUTUBE_API_KEY in environment or ~/.hermes/profiles/youtube/.env
"""
import argparse
import json
import os
import sys
import urllib.request

def load_api_key():
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        env_path = os.path.expanduser("~/.hermes/profiles/youtube/.env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("YOUTUBE_API_KEY="):
                        key = line.strip().split("=", 1)[1]
                        break
    if not key:
        print("ERROR: YOUTUBE_API_KEY not found in env or ~/.hermes/profiles/youtube/.env", file=sys.stderr)
        sys.exit(1)
    return key

def search_videos(api_key, query, max_results=10, order="viewCount", lang=None, duration="short"):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": duration,
        "order": order,
        "maxResults": str(max_results),
        "key": api_key,
    }
    if lang:
        params["relevanceLanguage"] = lang
    url += "?" + "&".join(f"{k}={urllib.parse.quote(v)}" for k, v in params.items())
    
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    
    ids = [item["id"]["videoId"] for item in data.get("items", [])]
    return ids

def get_video_stats(api_key, video_ids):
    if not video_ids:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids[:50]),
        "key": api_key,
    }
    url += "?" + "&".join(f"{k}={urllib.parse.quote(v)}" for k, v in params.items())
    
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    
    results = []
    for v in data.get("items", []):
        views = int(v["statistics"].get("viewCount", 0))
        results.append({
            "id": v["id"],
            "title": v["snippet"]["title"],
            "channel": v["snippet"]["channelTitle"],
            "views": views,
            "date": v["snippet"]["publishedAt"][:10],
            "lang": v["snippet"].get("defaultAudioLanguage", v["snippet"].get("defaultLanguage", "?")),
        })
    results.sort(key=lambda x: x["views"], reverse=True)
    return results

def fetch_transcript(video_id, languages=None):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt_api = YouTubeTranscriptApi()
        if languages is None:
            languages = ["en", "es", "fr", "de", "pt"]
        transcript = ytt_api.fetch(video_id, languages=languages)
        return " ".join([snippet.text for snippet in transcript])
    except Exception as e:
        return None

def main():
    parser = argparse.ArgumentParser(description="Search YouTube Shorts by views")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max", type=int, default=10, help="Max results")
    parser.add_argument("--order", default="viewCount", help="Sort order: viewCount, date, relevance")
    parser.add_argument("--lang", default=None, help="Relevance language (en, es, fr, de, etc.)")
    parser.add_argument("--duration", default="short", help="Video duration: short, medium, long")
    parser.add_argument("--min-views", type=int, default=100000, help="Min view count to display")
    parser.add_argument("--transcripts", action="store_true", help="Attempt to fetch transcripts for top results")
    parser.add_argument("--transcript-langs", default="en,es,fr,de,pt", help="Comma-separated transcript languages to try")
    args = parser.parse_args()

    api_key = load_api_key()
    
    print(f"Searching: '{args.query}' | order={args.order} | min_views={args.min_views}")
    ids = search_videos(api_key, args.query, args.max, args.order, args.lang, args.duration)
    videos = get_video_stats(api_key, ids)
    
    if not videos:
        print("No results found.")
        return
    
    print(f"\n{'Views':>12} | {'Date':>10} | {'Lang':>4} | {'Channel':>25} | Title")
    print("-" * 100)
    for v in videos:
        if v["views"] >= args.min_views:
            print(f"{v['views']:>12,} | {v['date']:>10} | {v['lang']:>4} | {v['channel'][:25]:>25} | {v['title']}")
    
    if args.transcripts:
        langs = args.transcript_langs.split(",")
        print(f"\n--- Fetching transcripts (langs={langs}) ---")
        for v in videos[:5]:
            if v["views"] < args.min_views:
                continue
            text = fetch_transcript(v["id"], langs)
            if text:
                print(f"\n✅ {v['id']} ({v['views']:,} views): {v['title']}")
                print(f"   {text[:500]}")
            else:
                print(f"\n❌ {v['id']} ({v['views']:,} views): No transcript available")

if __name__ == "__main__":
    main()