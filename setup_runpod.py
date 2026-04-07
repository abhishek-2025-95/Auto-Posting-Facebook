#!/usr/bin/env python3
"""
One-shot RunPod image-server setup from your PC.
Run this script on Windows (from the project folder); it will SSH into your RunPod,
create the dir, upload runpod_image_server.py, install deps, and start the server in the background.

Requirements:
  - RunPod pod running; SSH key added in RunPod Connect.
  - Set RUNPOD_SSH_USER in .env (e.g. t4yp4bdgfbei8h-64410ea3) or pass as first argument.
  - SSH key at ~/.ssh/id_ed25519 or set RUNPOD_SSH_KEY in .env.

Usage:
  python setup_runpod.py
  python setup_runpod.py t4yp4bdgfbei8h-64410ea3
"""
import os
import subprocess
import sys
from pathlib import Path

# Project root (directory containing this script)
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
    ssh_user = (sys.argv[1] if len(sys.argv) > 1 else None) or os.environ.get("RUNPOD_SSH_USER", "").strip()
    if not ssh_user:
        print("Set RUNPOD_SSH_USER in .env or run: python setup_runpod.py <pod-username>")
        print("Example: python setup_runpod.py t4yp4bdgfbei8h-64410ea3")
        sys.exit(1)

    key_path = os.environ.get("RUNPOD_SSH_KEY", "").strip() or os.path.expanduser("~/.ssh/id_ed25519")
    if not os.path.isfile(key_path):
        print(f"SSH key not found: {key_path}")
        print("Set RUNPOD_SSH_KEY in .env or create ~/.ssh/id_ed25519")
        sys.exit(1)

    server_file = PROJECT_ROOT / "runpod_image_server.py"
    if not server_file.is_file():
        print(f"Not found: {server_file}")
        sys.exit(1)

    ssh_target = f"{ssh_user}@ssh.runpod.io"
    workdir = "/workspace/auto-posting-facebook"

    def run_ssh(cmd, stdin=None, check=True):
        args = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15", ssh_target, cmd]
        return subprocess.run(args, stdin=stdin, check=check, timeout=300, stderr=subprocess.DEVNULL)

    print("1/4 Creating directory on RunPod...")
    run_ssh(f"mkdir -p {workdir}")

    print("2/4 Uploading runpod_image_server.py...")
    with open(server_file, "rb") as f:
        run_ssh(f"cat > {workdir}/runpod_image_server.py", stdin=f)

    print("3/4 Starting background setup (venv + pip install + server)...")
    # Single nohup so it survives SSH disconnect; pip install can take 5–10 min
    setup_cmd = (
        f"cd {workdir} && "
        "nohup bash -c '"
        "python3 -m venv .venv && "
        "source .venv/bin/activate && "
        "pip install -q --upgrade pip && "
        "pip install -q --ignore-installed blinker flask torch diffusers transformers accelerate safetensors && "
        "exec python runpod_image_server.py"
        "' > server.log 2>&1 &"
    )
    run_ssh(setup_cmd)

    print("4/4 Done. Server is starting in the background on the pod.")
    print("")
    print("To watch progress on the pod:")
    print(f"  ssh -i \"{key_path}\" {ssh_target} \"tail -f {workdir}/server.log\"")
    print("")
    print("When you see 'Model loaded.' and 'Running on http://0.0.0.0:5000', set on your VPS .env:")
    print("  RUNPOD_IMAGE_API_URL=http://<RUNPOD_PUBLIC_IP>:5000")
    print("(Get <RUNPOD_PUBLIC_IP> from RunPod Connect -> Direct TCP ports or pod details.)")

if __name__ == "__main__":
    main()
