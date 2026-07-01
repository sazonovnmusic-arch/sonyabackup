#!/usr/bin/env python3
"""
Instagram Story Auto-Publisher for @kiraliluna
Publishes next photo from stories_queue/ via Graph API
"""
import os, sys, json, time, subprocess, re, urllib.request, ssl, shutil

# Config
PROFILE_DIR = os.path.expanduser("~/.hermes/profiles/instamodel")
QUEUE_DIR = os.path.join(PROFILE_DIR, "stories_queue")
PUBLISHED_DIR = os.path.join(PROFILE_DIR, "stories_published")
TOKEN_FILE = os.path.join(PROFILE_DIR, ".page_token.txt")
IG_ID = "17841463208388373"
API_VERSION = "v18.0"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def get_token():
    if not os.path.exists(TOKEN_FILE):
        log("❌ ERROR: Token file not found!")
        log("   Get fresh Page Access Token from:")
        log("   https://developers.facebook.com/tools/explorer")
        log("   Select: SonyaHermes app → Page → Kirakira luna")
        log("   Permissions: instagram_content_publish, instagram_basic")
        log("   Save token to: " + TOKEN_FILE)
        sys.exit(1)
    with open(TOKEN_FILE) as f:
        return f.read().strip()

def get_next_photo():
    files = sorted([f for f in os.listdir(QUEUE_DIR) if f.endswith(('.jpg','.jpeg','.png','.webp'))])
    if not files:
        return None
    return os.path.join(QUEUE_DIR, files[0])

def start_tunnel(photo_path):
    """Start HTTP server + cloudflared, return HTTPS URL"""
    # Copy photo to webroot
    webroot = "/tmp/ig_webroot"
    os.makedirs(webroot, exist_ok=True)
    shutil.copy(photo_path, os.path.join(webroot, "story.jpg"))

    # Start HTTP server
    srv = subprocess.Popen(
        ["python3", "-m", "http.server", "8000", "--bind", "0.0.0.0"],
        cwd=webroot,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(2)

    # Start cloudflared
    cf = subprocess.Popen(
        ["/tmp/cloudflared", "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True
    )

    # Parse URL from output
    url = None
    start_time = time.time()
    while time.time() - start_time < 45:
        line = cf.stdout.readline()
        if not line:
            time.sleep(0.5)
            continue
        match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
        if match:
            url = match.group(0) + "/story.jpg"
            break

    if not url:
        srv.kill()
        cf.kill()
        log("❌ Failed to get cloudflared URL")
        return None, None, None

    # Wait for tunnel to be reachable
    log(f"🌐 Tunnel URL: {url}")
    log("Waiting for tunnel to stabilize...")
    time.sleep(5)

    # Verify URL is accessible
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, method="HEAD",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            log(f"✅ Tunnel reachable: HTTP {resp.status}")
            break
        except Exception as e:
            log(f"  Tunnel check {attempt+1}/5 failed: {e}")
            time.sleep(3)
    else:
        log("⚠️ Tunnel may be unstable, proceeding anyway...")

    return url, srv, cf

def api_call(endpoint, data=None, token=None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = f"https://graph.facebook.com/{API_VERSION}/{endpoint}"
    if data:
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers={"Accept": "application/json"},
                                  method="POST" if data else "GET")
    try:
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())

def publish_story(photo_path):
    token = get_token()
    filename = os.path.basename(photo_path)
    log(f"📤 Publishing: {filename}")
    
    # Start tunnel
    url, srv, cf = start_tunnel(photo_path)
    if not url:
        return False
    
    try:
        # Step 1: Create container
        log("Creating story container...")
        result = api_call(f"{IG_ID}/media", {
            "image_url": url,
            "media_type": "STORIES",
            "access_token": token
        })
        
        if "id" not in result:
            log(f"❌ Container creation failed: {json.dumps(result)}")
            return False
        
        container_id = result["id"]
        log(f"✅ Container: {container_id}")
        
        # Wait for Instagram to process
        time.sleep(8)
        
        # Step 2: Publish
        log("Publishing...")
        pub = api_call(f"{IG_ID}/media_publish", {
            "creation_id": container_id,
            "access_token": token
        })
        
        if "id" not in pub:
            log(f"❌ Publish failed: {json.dumps(pub)}")
            return False
        
        media_id = pub["id"]
        log(f"✅ Story published! Media ID: {media_id}")
        
        # Move to published
        os.makedirs(PUBLISHED_DIR, exist_ok=True)
        shutil.move(photo_path, os.path.join(PUBLISHED_DIR, filename))
        log(f"📁 Moved to published/{filename}")
        
        # Save log
        with open(os.path.join(PROFILE_DIR, "stories_log.txt"), "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {media_id} | {filename}\n")
        
        return True
        
    finally:
        # Cleanup
        srv.kill()
        cf.kill()
        srv.wait()
        cf.wait()
        log("🧹 Tunnel closed")

def main():
    log("=" * 50)
    log("Instagram Story Auto-Publisher")
    log("=" * 50)
    
    # Check queue
    photo = get_next_photo()
    if not photo:
        log("📭 Queue is empty! No photos to publish.")
        log(f"   Add photos to: {QUEUE_DIR}")
        sys.exit(0)
    
    log(f"📸 Next in queue: {os.path.basename(photo)}")
    log(f"📊 Remaining: {len([f for f in os.listdir(QUEUE_DIR) if f.endswith(('.jpg','.jpeg','.png','.webp'))])} photos")
    
    # Publish
    success = publish_story(photo)
    
    if success:
        remaining = len([f for f in os.listdir(QUEUE_DIR) if f.endswith(('.jpg','.jpeg','.png','.webp'))])
        log(f"📦 Remaining in queue: {remaining}")
        log("✅ Done!")
        sys.exit(0)
    else:
        log("❌ Publication failed. Will retry on next run.")
        sys.exit(1)

if __name__ == "__main__":
    main()
