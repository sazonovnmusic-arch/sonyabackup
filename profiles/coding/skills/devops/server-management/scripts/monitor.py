import psutil
import shutil
import os

def check_server_health():
    issues = []
    
    # Disk Usage
    total, used, free = shutil.disk_usage("/")
    percent_free = (free / total) * 100
    if percent_free < 10:
        issues.append(f"⚠️ Low disk space: {percent_free:.1f}% left")
    
    # CPU Load
    cpu_usage = psutil.cpu_percent(interval=5)
    if cpu_usage > 90:
        issues.append(f"🔥 High CPU usage: {cpu_usage}%")
        
    # Memory
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        issues.append(f"🧠 High RAM usage: {memory.percent}%")

    if issues:
        print("\n".join(issues))
    else:
        # Default behavior: stay silent or provide a brief OK status
        print(f"✅ Server OK. Disk: {100-((used/total)*100):.1f}%, CPU: {cpu_usage}%, RAM: {memory.percent}%")

if __name__ == "__main__":
    check_server_health()
