#!/usr/bin/env python3
"""
Do everything: setup RunPod server, wait for model to load (or surface error), run one post cycle via tunnel.
Run from project folder: python run_runpod_full_cycle.py
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

    def ssh(cmd, timeout=60):
        args = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15", ssh_target, cmd]
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, stderr=subprocess.DEVNULL)

    # 1) Setup: upload server and start in background
    print("Step 1/4: Setting up RunPod (upload + start server)...")
    r = subprocess.run([sys.executable, str(PROJECT_ROOT / "setup_runpod.py")], cwd=str(PROJECT_ROOT), timeout=60, capture_output=True)
    if r.returncode != 0:
        print(r.stderr or r.stdout or "Setup failed")
        return 1

    # 2) Wait for server to be ready (model load can take 2-4 min)
    print("Step 2/4: Waiting for server (model load 2-4 min)...")
    for i in range(15):
        time.sleep(20)
        r = ssh(f"tail -100 {workdir}/server.log 2>/dev/null || true", timeout=30)
        log = (r.stdout or "") + (r.stderr or "")
        if "Model load FAILED" in log:
            print("Model failed to load on RunPod. Last 40 lines of server.log:")
            print("---")
            for line in log.splitlines()[-40:]:
                print(line)
            print("---")
            return 1
        if "Model loaded." in log and ("Starting Flask" in log or "Running on" in log):
            print("Server ready.")
            break
        if (i + 1) % 2 == 0:
            print(f"  ... waiting ({(i+1)*20}s)")
    else:
        print("Server did not become ready in 5 min. Check server.log on pod. Running cycle anyway...")

    # 3) Run one cycle (tunnel + run_one_cycle)
    print("Step 3/4: Running one post cycle (tunnel + image via RunPod)...")
    r = subprocess.run([sys.executable, str(PROJECT_ROOT / "run_one_cycle_with_runpod.py")], cwd=str(PROJECT_ROOT), timeout=900)
    return r.returncode

if __name__ == "__main__":
    sys.exit(main() or 0)
