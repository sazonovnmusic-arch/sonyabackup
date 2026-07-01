import os
import sys
import shutil
import subprocess
import glob
import time
from pathlib import Path
from datetime import datetime, timedelta

# Ensure we run with psutil available (Hermes venv has it)
try:
    import psutil
except ImportError:
    venv_python = "/usr/local/lib/hermes-agent/venv/bin/python3"
    if sys.executable != venv_python:
        os.execv(venv_python, [venv_python, __file__])
    raise

def run(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    except:
        return None

def kill_zombies():
    """Kill zombie processes (safe — they're dead anyway)"""
    killed = 0
    for proc in psutil.process_iter(['pid', 'ppid', 'status', 'name']):
        try:
            if proc.info['status'] == 'zombie':
                os.kill(proc.info['pid'], 9)
                killed += 1
        except (psutil.NoSuchProcess, PermissionError, ProcessLookupError):
            pass
    return killed

def clean_orphaned_screens():
    """Clean screen sessions that are not managed by systemd"""
    cleaned = 0
    try:
        result = subprocess.run(['screen', '-ls'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            if '.' in line and '(' in line:
                parts = line.split('.')[0].strip()
                if parts.isdigit():
                    sess_id = line.split()[0]
                    # Check if it's an orphaned manual screen (not a gateway)
                    screen_pid = int(parts)
                    try:
                        proc = psutil.Process(screen_pid)
                        cmdline = ' '.join(proc.cmdline())
                        if 'hermes' not in cmdline.lower() and proc.create_time() < (time.time() - 3600):
                            subprocess.run(['screen', '-S', sess_id, '-X', 'quit'], timeout=5)
                            cleaned += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
    except Exception:
        pass
    return cleaned

def rotate_old_logs(days=30):
    """Compress logs older than N days, not delete"""
    rotated = 0
    log_paths = [
        '/root/.hermes/logs/*.log',
        '/root/.hermes/profiles/*/logs/*.log',
    ]
    cutoff = time.time() - (days * 86400)
    archive_dir = Path('/root/.hermes/log_archive')
    archive_dir.mkdir(parents=True, exist_ok=True)

    for pattern in log_paths:
        for logfile in glob.glob(pattern):
            lp = Path(logfile)
            if not lp.exists():
                continue
            try:
                # Don't rotate gateway.log (active), only bg logs and old rotated
                if lp.name == 'gateway.log' or lp.stat().st_mtime > cutoff:
                    continue
                # Compress to archive
                dest = archive_dir / f"{lp.stem}_{lp.stat().st_mtime:.0f}.gz"
                subprocess.run(['gzip', '-c', str(lp)], stdout=open(dest, 'wb'), timeout=30)
                lp.unlink()
                rotated += 1
            except Exception:
                pass
    return rotated

def clean_temp_files():
    """Clean temp files older than 7 days (only our known patterns)"""
    cleaned = 0
    cutoff = time.time() - (7 * 86400)
    patterns = [
        '/tmp/locks-*/**/*',
        '/tmp/hermes-snap-*',
        '/tmp/hermes-cwd-*',
    ]
    for pattern in patterns:
        for path in glob.glob(pattern):
            try:
                p = Path(path)
                if p.exists() and p.stat().st_mtime < cutoff:
                    if p.is_file():
                        p.unlink()
                        cleaned += 1
                    elif p.is_dir() and pattern.startswith('/tmp/locks'):
                        # Only clean empty lock dirs
                        try:
                            p.rmdir()
                            cleaned += 1
                        except OSError:
                            pass
            except Exception:
                pass
    return cleaned

def check_disk():
    total, used, free = shutil.disk_usage("/")
    percent_used = (used / total) * 100
    gb_free = free / (2**30)
    return percent_used, gb_free

def check_gateways():
    services = [
        'hermes-gateway',
        'hermes-gateway-youtube',
        'hermes-gateway-coding',
        'hermes-gateway-traffic',
    ]
    statuses = {}
    for svc in services:
        result = run(f'systemctl is-active {svc}.service 2>/dev/null')
        statuses[svc] = result.stdout.strip() if result else 'unknown'
    return statuses

def check_server_health():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [f"📊 Server Health — {now}", "─" * 30]

    # Disk
    pct_used, gb_free = check_disk()
    if pct_used > 90:
        lines.append(f"🚨 DISK CRITICAL: {pct_used:.1f}% used, {gb_free:.1f} GB free")
    elif pct_used > 80:
        lines.append(f"⚠️ DISK WARNING: {pct_used:.1f}% used, {gb_free:.1f} GB free")
    else:
        lines.append(f"💾 Disk OK: {gb_free:.1f} GB free ({pct_used:.1f}% used)")

    # Gateways
    gw_status = check_gateways()
    all_ok = all(v == 'active' for v in gw_status.values())
    if all_ok:
        lines.append(f"🟢 All 4 gateways active")
    else:
        for svc, st in gw_status.items():
            emoji = "🟢" if st == 'active' else "🔴"
            lines.append(f"{emoji} {svc}: {st}")

    # Maintenance actions
    zombies = kill_zombies()
    orphans = clean_orphaned_screens()
    rotated = rotate_old_logs(days=30)
    temp_cleaned = clean_temp_files()

    actions = []
    if zombies: actions.append(f"killed {zombies} zombies")
    if orphans: actions.append(f"closed {orphans} orphaned screens")
    if rotated: actions.append(f"archived {rotated} old logs")
    if temp_cleaned: actions.append(f"cleaned {temp_cleaned} temp files")

    if actions:
        lines.append(f"🧹 Maintenance: {', '.join(actions)}")
    else:
        lines.append("🧹 Maintenance: nothing to do")

    # Resources
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    if cpu > 90:
        lines.append(f"🔥 CPU: {cpu}%")
    else:
        lines.append(f"🌡️ CPU: {cpu}%")

    if mem.percent > 90:
        lines.append(f"🧠 RAM: {mem.percent}% (CRITICAL)")
    elif mem.percent > 80:
        lines.append(f"🧠 RAM: {mem.percent}% (warning)")
    else:
        lines.append(f"🧠 RAM: {mem.percent}%")

    if swap.percent > 50:
        lines.append(f"💿 Swap: {swap.percent}%")

    lines.append("─" * 30)
    if all_ok and pct_used < 85 and mem.percent < 90:
        lines.append("✅ Overall: STABLE")
    else:
        lines.append("⚠️ Overall: CHECK NEEDED")

    print("\n".join(lines))

if __name__ == "__main__":
    try:
        check_server_health()
    except Exception as e:
        print(f"❌ Monitor error: {e}")
