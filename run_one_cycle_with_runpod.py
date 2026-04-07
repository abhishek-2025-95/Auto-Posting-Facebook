#!/usr/bin/env python3
"""
One-command run: ensure RunPod image server is up, open SSH tunnel so your PC
can reach it at localhost:5000, then run one post cycle. Works from Windows even
when RunPod Direct TCP is not reachable from your network.
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
    local_port = 5000

    # 1) Ensure server is running on the pod
    print("Step 1/3: Ensuring RunPod image server is running...")
    r = subprocess.run([sys.executable, str(PROJECT_ROOT / "ensure_runpod_server.py")], cwd=str(PROJECT_ROOT), timeout=120)
    if r.returncode != 0:
        print("Failed to ensure RunPod server. Run: python setup_runpod.py")
        return 1

    # 2) Start SSH tunnel (local port -> pod's 5000)
    print("Step 2/3: Opening SSH tunnel (localhost:5000 -> RunPod:5000)...")
    tunnel_cmd = [
        "ssh", "-T", "-i", key_path,
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=15",
        "-N", "-L", f"{local_port}:127.0.0.1:5000",
        ssh_target
    ]
    tunnel = subprocess.Popen(tunnel_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    if tunnel.poll() is not None:
        print("SSH tunnel failed to start. Check SSH key and RUNPOD_SSH_USER.")
        return 1

    try:
        # 3) Warmup: trigger model load on first request (avoids connection reset during real cycle)
        api_url = f"http://127.0.0.1:{local_port}"
        try:
            import urllib.request
            urllib.request.urlopen(api_url + "/health", timeout=5)
        except Exception:
            pass
        print("Warming up RunPod server (first request may load model, 1-2 min)...")
        try:
            import urllib.request
            import json
            req = urllib.request.Request(api_url + "/generate", data=json.dumps({"prompt": "a red apple", "width": 256, "height": 256}).encode(), headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=300)
        except Exception as e:
            print(f"Warmup note: {e}")
        print("Step 3/3: Running one post cycle (image via tunnel)...")
        env = os.environ.copy()
        env["RUNPOD_IMAGE_API_URL"] = api_url
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "run_one_cycle.py")],
            cwd=str(PROJECT_ROOT),
            env=env,
            timeout=900
        )
        return r.returncode
    finally:
        tunnel.terminate()
        try:
            tunnel.wait(timeout=5)
        except subprocess.TimeoutExpired:
            tunnel.kill()

if __name__ == "__main__":
    sys.exit(main() or 0)
