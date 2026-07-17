import os
import sys
import time
import socket
import psutil
import requests
import platform

# Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://127.0.0.1:8000/api/vm')
INTERVAL = 30  # seconds

def get_system_info():
    """Gathers system information for registration."""
    hostname = socket.gethostname()
    
    # Try to get the primary IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except Exception:
        ip_address = socket.gethostbyname(hostname)
        
    os_name = f"{platform.system()} {platform.release()}"
    cpu_count = psutil.cpu_count(logical=True)
    total_ram = round(psutil.virtual_memory().total / (1024**3), 2) # in GB
    total_disk = round(psutil.disk_usage('/').total / (1024**3), 2) # in GB

    return {
        "hostname": hostname,
        "ip_address": ip_address,
        "operating_system": os_name,
        "cpu_count": cpu_count,
        "total_ram": total_ram,
        "total_disk": total_disk
    }

def get_metrics():
    """Gathers current resource usage metrics."""
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent
    
    return {
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "disk_usage": disk_usage
    }

def register_vm():
    """Registers the VM and returns the auth token."""
    url = f"{API_BASE_URL}/register/"
    data = get_system_info()
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        print(f"[*] Registered successfully. VM ID: {result.get('id')}")
        return result.get("token")
    except Exception as e:
        print(f"[!] Error registering VM: {e}")
        return None

def send_metrics(token):
    """Sends metrics to the server."""
    url = f"{API_BASE_URL}/metrics/"
    headers = {"Authorization": f"Token {token}"}
    data = get_metrics()
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"[*] Sent metrics: CPU={data['cpu_usage']}% RAM={data['ram_usage']}% Disk={data['disk_usage']}%")
    except Exception as e:
        print(f"[!] Error sending metrics: {e}")

def send_heartbeat(token):
    """Sends a heartbeat to the server (Optional as metrics update last_seen)."""
    url = f"{API_BASE_URL}/heartbeat/"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("[*] Sent heartbeat")
    except Exception as e:
        print(f"[!] Error sending heartbeat: {e}")

if __name__ == "__main__":
    print("[*] Starting VM Monitoring Agent...")
    print(f"[*] API Server: {API_BASE_URL}")
    
    token = None
    while not token:
        token = register_vm()
        if not token:
            print("[*] Retrying registration in 10 seconds...")
            time.sleep(10)
            
    print("[*] VM Agent is active. Sending metrics every 30 seconds.")
    
    # Main loop
    while True:
        send_metrics(token)
        # Note: send_metrics already acts as a heartbeat because the Django API updates last_seen.
        # If you only wanted to send heartbeat, you'd use send_heartbeat(token).
        time.sleep(INTERVAL - 1) # psutil.cpu_percent takes 1 second
