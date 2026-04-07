#!/usr/bin/env python3
"""
Run from project folder to verify RunPod deployment: directory, process, and recent log.
Usage: set RUNPOD_SSH_USER=... then python check_runpod_health.py
"""
import os
import subprocess
import sys
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
        print("Set RUNPOD_SSH_USER in .env (or in the shell)")
        return 1
    key_path = os.environ.get("RUNPOD_SSH_KEY", "").strip() or os.path.expanduser("~/.ssh/id_ed25519")
    if not os.path.isfile(key_path):
        print(f"SSH key not found: {key_path}")
        return 1
    ssh_target = f"{ssh_user}@ssh.runpod.io"
    workdir = "/workspace/auto-posting-facebook"

    args_base = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15", ssh_target]

    def run(cmd):
        r = subprocess.run(args_base + [cmd], capture_output=True, text=True, timeout=30)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()

    print("RunPod health check")
    print("=" * 60)

    # 1) Directory exists and has key files
    code, out, err = run(f"ls -la {workdir}/ 2>/dev/null || echo 'DIR_MISSING'")
    if "DIR_MISSING" in out or code != 0:
        print("[FAIL] Project directory missing or inaccessible.")
        if out and "DIR_MISSING" not in out:
            print(out)
        return 1
    print("[OK] Project directory exists.")
    if "run_continuous_posts.py" in out:
        print("      run_continuous_posts.py present")
    if "runpod.log" in out:
        print("      runpod.log present")

    # 2) Process running (start_runpod.py or run_continuous_posts.py)
    code, out, err = run(f"ps aux | grep -E 'start_runpod|run_continuous_posts' | grep -v grep || true")
    if code != 0:
        print("[WARN] Could not list processes.")
    elif "start_runpod" in out or "run_continuous" in out:
        print("[OK] Pipeline process is running.")
    else:
        print("[FAIL] Pipeline process not found (start_runpod.py / run_continuous_posts).")

    # 3) Crash log if present
    code, crash_out, _ = run(f"cat {workdir}/runpod_crash.log 2>/dev/null || true")
    for bad in ("Error: Your SSH client doesn't support PTY",):
        crash_out = crash_out.replace(bad, "").strip()
    if crash_out.strip():
        print("[WARN] runpod_crash.log (last startup error):")
        print("-" * 40)
        for line in crash_out.splitlines()[-30:]:
            if line.strip():
                print("  ", line)
        print("-" * 40)

    # 4) Recent log (ignore RunPod PTY message on stdout)
    code, out, err = run(f"tail -n 50 {workdir}/runpod.log 2>/dev/null || echo 'LOG_MISSING'")
    for bad in ("Error: Your SSH client doesn't support PTY", "LOG_MISSING"):
        out = out.replace(bad, "").strip()
    if not out:
        print("[WARN] No log file or empty (pipeline may have exited right after start).")
    else:
        print("[OK] Recent log (last 50 lines):")
        print("-" * 40)
        for line in out.splitlines():
            if line.strip():
                print("  ", line)
        print("-" * 40)

    print("=" * 60)
    print("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
