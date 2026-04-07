#!/usr/bin/env python3
"""
Ensure the RunPod image server is running. SSHs to the pod, checks /health,
and starts the server in the background (nohup) if not running.
Use this before run_one_cycle when using RunPod for images.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def load_dotenv():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k and v and k not in os.environ:
                    os.environ[k] = v

def main():
    load_dotenv()
    ssh_user = os.environ.get("RUNPOD_SSH_USER", "").strip()
    if not ssh_user:
        print("Set RUNPOD_SSH_USER in .env")
        return 1
    key_path = os.environ.get("RUNPOD_SSH_KEY", "").strip() or os.path.expanduser("~/.ssh/id_ed25519")
    if not os.path.isfile(key_path):
        print(f"SSH key not found: {key_path}")
        return 1

    ssh_target = f"{ssh_user}@ssh.runpod.io"
    workdir = "/workspace/auto-posting-facebook"

    def ssh(cmd, check=True):
        args = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15", ssh_target, cmd]
        r = subprocess.run(args, capture_output=True, text=True, timeout=60, stderr=subprocess.DEVNULL)
        if check and r.returncode != 0:
            raise SystemExit(r.returncode)
        return r

    # Check if server process is running
    r = ssh(f"pgrep -f runpod_image_server >/dev/null && echo 1 || echo 0", check=False)
    if (r.stdout or "").strip() == "1":
        r2 = ssh("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/health 2>/dev/null || echo '000'", check=False)
        if (r2.stdout or "").strip() == "200":
            print("RunPod image server is already running (health OK).")
            return 0

    # Start server in background (nohup bash so venv is active)
    print("Starting RunPod image server in background...")
    ssh(f"cd {workdir} && nohup bash -c 'source .venv/bin/activate && exec python runpod_image_server.py' >> server.log 2>&1 &", check=False)

    # Wait up to 30s for server to respond (fewer SSH round-trips)
    print("Waiting for server (up to 30s)...")
    for i in range(6):
        time.sleep(5)
        r = ssh("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/health 2>/dev/null || echo '000'", check=False)
        if (r.stdout or "").strip() == "200":
            print("RunPod image server is ready.")
            return 0
    print("Server not ready yet. Tunnel will open; if image fails, run the script again in 1 min.")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
