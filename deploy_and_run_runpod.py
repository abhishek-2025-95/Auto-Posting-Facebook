#!/usr/bin/env python3
"""
Do everything: create a RunPod GPU pod (if needed) and deploy + run the full pipeline there.
No manual SSH or console steps if you have RUNPOD_API_KEY (and optionally runpodctl).

Usage:
  Option A – You already have a pod: set RUNPOD_SSH_USER in .env, then:
    python deploy_and_run_runpod.py

  Option B – Create pod automatically: set RUNPOD_API_KEY in .env (and add your SSH public key
    in RunPod account settings). Optionally install runpodctl so the script can get the SSH user
    without opening the console. Then:
    python deploy_and_run_runpod.py

  If you don't have runpodctl: the script will create the pod, then ask you to copy
  RUNPOD_SSH_USER from the pod's Connect tab into .env and run the script again.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

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

def runpod_create_pod(api_key: str, gpu_type_id: str, image_name: str, name: str, ports: list):
    """Create a pod via RunPod REST API. Returns pod id or None."""
    try:
        import requests
    except ImportError:
        print("Install requests: pip install requests")
        return None
    url = "https://rest.runpod.io/v1/pods"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "cloudType": "SECURE",
        "computeType": "GPU",
        "gpuTypeIds": [gpu_type_id],
        "imageName": image_name,
        "name": name,
        "containerDiskInGb": 50,
        "volumeInGb": 20,
        "ports": ports,
    }
    r = requests.post(url, json=payload, headers=headers, timeout=60)
    if r.status_code != 201:
        print(f"RunPod API create failed: {r.status_code} {r.text[:500]}")
        return None
    data = r.json()
    return data.get("id")

def runpod_get_pod(api_key: str, pod_id: str):
    """GET single pod. Returns dict or None."""
    try:
        import requests
    except ImportError:
        return None
    url = f"https://rest.runpod.io/v1/pods/{pod_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        return None
    return r.json()

def runpod_wait_running(api_key: str, pod_id: str, max_wait_sec: int = 600, poll_interval: int = 15):
    """Poll until pod desiredStatus is RUNNING. Returns True when ready."""
    start = time.monotonic()
    while (time.monotonic() - start) < max_wait_sec:
        pod = runpod_get_pod(api_key, pod_id)
        if not pod:
            time.sleep(poll_interval)
            continue
        status = pod.get("desiredStatus") or pod.get("runtime", {}).get("desiredStatus")
        if status == "RUNNING":
            return True
        time.sleep(poll_interval)
    return False

def get_ssh_user_via_runpodctl(pod_id: str) -> Optional[str]:
    """Run 'runpodctl ssh info <pod_id>' and parse SSH user (e.g. xyz-6441103b). Returns None if not found."""
    try:
        out = subprocess.run(
            ["runpodctl", "ssh", "info", pod_id],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        if out.returncode != 0:
            return None
        # Expect something like: ssh 8y5rumuyb50m78-6441103b@ssh.runpod.io -i ...
        m = re.search(r"ssh\s+([a-zA-Z0-9_-]+)@ssh\.runpod\.io", out.stdout or out.stderr or "")
        if m:
            return m.group(1).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None

def append_runpod_ssh_user_to_env(ssh_user: str):
    """Append RUNPOD_SSH_USER to .env if not already set."""
    env_path = PROJECT_ROOT / ".env"
    content = env_path.read_text(encoding="utf-8", errors="ignore") if env_path.exists() else ""
    if "RUNPOD_SSH_USER=" in content and not re.search(r"RUNPOD_SSH_USER=\s*$", content):
        # Already has a value; don't overwrite
        return
    line = f"RUNPOD_SSH_USER={ssh_user}\n"
    if "RUNPOD_SSH_USER=" not in content:
        content = content.rstrip() + "\n" + line
    else:
        content = re.sub(r"RUNPOD_SSH_USER=.*", line.strip(), content) + "\n"
    env_path.write_text(content, encoding="utf-8")

def main():
    load_dotenv()
    ssh_user = os.environ.get("RUNPOD_SSH_USER", "").strip()
    ssh_host = os.environ.get("RUNPOD_SSH_HOST", "").strip()
    api_key = os.environ.get("RUNPOD_API_KEY", "").strip()
    key_path = os.environ.get("RUNPOD_SSH_KEY", "").strip() or os.path.expanduser("~/.ssh/id_ed25519")

    # If we have proxy user or Direct TCP (host+port), run the full setup
    if ssh_user or ssh_host:
        if not os.path.isfile(key_path):
            print(f"SSH key not found: {key_path}")
            return 1
        setup_timeout = int(os.environ.get("RUNPOD_SETUP_TIMEOUT", "1800"))  # 30 min default (upload can be slow)
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "setup_runpod_full.py")],
            cwd=str(PROJECT_ROOT),
            env=os.environ,
            timeout=setup_timeout,
        )
        return r.returncode

    # No SSH user: try to create pod via API and get SSH user
    if not api_key:
        print("Set either RUNPOD_SSH_USER (existing pod) or RUNPOD_API_KEY (create pod) in .env")
        return 1
    if not os.path.isfile(key_path):
        print(f"SSH key not found: {key_path}. Add your public key in RunPod account settings.")
        return 1

    gpu_type = os.environ.get("RUNPOD_GPU_TYPE", "NVIDIA RTX 2000 Ada Generation")
    image = os.environ.get("RUNPOD_IMAGE", "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04")
    name = os.environ.get("RUNPOD_POD_NAME", "auto-posting-facebook")
    ports = ["8888/http", "22/tcp"]

    print("Creating RunPod GPU pod via API...")
    pod_id = runpod_create_pod(api_key, gpu_type, image, name, ports)
    if not pod_id:
        return 1
    print(f"Pod created: {pod_id}. Waiting for RUNNING...")
    if not runpod_wait_running(api_key, pod_id):
        print("Pod did not become RUNNING in time. Check console.runpod.io")
        return 1
    print("Pod is RUNNING.")

    ssh_user = get_ssh_user_via_runpodctl(pod_id)
    if ssh_user:
        append_runpod_ssh_user_to_env(ssh_user)
        os.environ["RUNPOD_SSH_USER"] = ssh_user
        print(f"Got SSH user from runpodctl: {ssh_user}. Running full setup...")
        setup_timeout = int(os.environ.get("RUNPOD_SETUP_TIMEOUT", "1800"))
        r = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "setup_runpod_full.py")],
            cwd=str(PROJECT_ROOT),
            env=os.environ,
            timeout=setup_timeout,
        )
        return r.returncode

    print("")
    print("Pod is ready but runpodctl is not installed, so the script could not get the SSH user.")
    print("1. Open https://console.runpod.io/pods and select this pod.")
    print("2. Open the Connect tab and copy the SSH username (e.g. xxxxx-6441103b) from the SSH command.")
    print("3. Add to .env: RUNPOD_SSH_USER=<that-username>")
    print("4. Run again: python deploy_and_run_runpod.py")
    print("")
    print(f"Pod ID: {pod_id}")
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
