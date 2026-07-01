import psutil
import shutil
import os

def check_server_health():
    issues = []
    
    # 1. Disk usage (10% threshold)
    total, used, free = shutil.disk_usage("/")
    percent_free = (free / total) * 100
    if percent_free < 10:
        issues.append(f"⚠️ Low disk space: {percent_free:.1f}% remaining ({free // (2**30)} GB)")
    
    # 2. CPU usage (90% threshold)
    cpu_usage = psutil.cpu_percent(interval=5)
    if cpu_usage > 90:
        issues.append(f"🔥 High CPU usage: {cpu_usage}%")
        
    # 3. RAM usage (90% threshold)
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        issues.append(f"🧠 Low memory: {memory.percent}% used")

    if issues:
        print("\n".join(issues))
    else:
        # Silent on success (watchdog pattern)
        pass

if __name__ == "__main__":
    check_server_health()
