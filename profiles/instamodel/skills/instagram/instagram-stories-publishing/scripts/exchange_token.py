#!/usr/bin/env python3
"""
Exchange short-lived Facebook Page Access Token for long-lived (60 days).
Usage: python3 exchange_token.py <short-lived-token>
"""
import sys, urllib.request, json, os

PROFILE_DIR = os.path.expanduser("~/.hermes/profiles/instamodel")
TOKEN_FILE=*** ".page_token.txt")

APP_ID = "908058175688398"
APP_SECRET=*** = "v18.0"

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <short-lived-token>")
        print("Get short-lived token from: https://developers.facebook.com/tools/explorer")
        sys.exit(1)
    
    short_token = sys.argv[1]
    url = (
        f"https://graph.facebook.com/{API_VERSION}/oauth/access_token"
        f"?grant_type=fb_exchange_token"
        f"&client_id={APP_ID}"
        f"&client_secret={APP_SECRET}"
        f"&fb_exchange_token={short_token}"
    )
    
    print("Exchanging token...")
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    
    if "access_token" not in data:
        print("❌ Exchange failed:", json.dumps(data, indent=2))
        sys.exit(1)
    
    long_token = data["access_token"]
    expires_in = data.get("expires_in", "unknown")
    
    # Save
    os.makedirs(PROFILE_DIR, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(long_token)
    
    print(f"✅ Long-lived token saved to {TOKEN_FILE}")
    print(f"   Expires in: {expires_in} seconds (~{expires_in//86400} days)")
    print(f"   Token preview: {long_token[:20]}...{long_token[-10:]}")

if __name__ == "__main__":
    main()
