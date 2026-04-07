#!/usr/bin/env python3
"""
Deploy the full project to RunPod and run the pipeline there (everything on RunPod GPU only).
No VPS, no RUNPOD_IMAGE_API_URL, no image server — one pod runs news, caption, image (Z-Image-Turbo), overlay, post.

Usage:
  Set RUNPOD_SSH_USER in .env (and RUNPOD_SSH_KEY if needed). Optionally GIT_CLONE_URL for clone; else project is uploaded as tarball.
  Set RUNPOD_SINGLE_CONNECTION=1 to run the full deploy in one SSH session and then drop into a shell in the same container (avoids proxy load-balancing landing you elsewhere).
  python setup_runpod_full.py
"""
import base64
import io
import os
import subprocess
import sys
import tarfile
import tempfile
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
    ssh_host = os.environ.get("RUNPOD_SSH_HOST", "").strip()  # Direct TCP IP (e.g. from Connect tab)
    ssh_port = os.environ.get("RUNPOD_SSH_PORT", "").strip()   # Direct TCP port (e.g. 44718)
    use_direct_tcp = bool(ssh_host)
    if use_direct_tcp:
        if not ssh_port:
            ssh_port = "22"
        ssh_target = f"root@{ssh_host}"
        print(f"Using Direct TCP: {ssh_target} port {ssh_port}")
    else:
        if not ssh_user:
            print("Set RUNPOD_SSH_USER in .env (or RUNPOD_SSH_HOST + RUNPOD_SSH_PORT for Direct TCP)")
            return 1
        ssh_target = f"{ssh_user}@ssh.runpod.io"
    key_path = os.environ.get("RUNPOD_SSH_KEY", "").strip() or os.path.expanduser("~/.ssh/id_ed25519")
    if not os.path.isfile(key_path):
        print(f"SSH key not found: {key_path}")
        return 1
    git_url = os.environ.get("GIT_CLONE_URL", "").strip()
    single_conn = os.environ.get("RUNPOD_SINGLE_CONNECTION", "").strip().lower() in ("1", "true", "yes")
    workdir = "/workspace/auto-posting-facebook"

    def ssh(cmd, stdin=None, timeout=300):
        args = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15"]
        if use_direct_tcp:
            args.extend(["-p", ssh_port])
        args.extend([ssh_target, cmd])
        kwargs = {"timeout": timeout, "capture_output": True, "text": True}
        # Use input= for string data so Windows doesn't get stdin=str (str has no fileno)
        if stdin is not None:
            kwargs["input"] = stdin
        r = subprocess.run(args, **kwargs)
        if r.returncode != 0:
            if r.stderr:
                for line in r.stderr.strip().splitlines():
                    if "PTY" not in line and "doesn't support" not in line:
                        print(line)
            if not r.stderr or "PTY" in r.stderr:
                print("SSH failed (exit %s). Check: pod running, RUNPOD_SSH_USER in .env matches Connect tab, key at RUNPOD_SSH_KEY." % r.returncode)
            raise subprocess.CalledProcessError(r.returncode, args, r.stdout, r.stderr)
        return r

    # Single-connection deploy: one SSH session does everything then drops to shell (same container).
    if single_conn and not git_url:
        print("Single-connection deploy (RUNPOD_SINGLE_CONNECTION=1): one SSH session, then shell in same container.")
        ALLOWED = {
            "run_continuous_posts.py", "start_runpod.py", "config.py", "content_generator.py", "runpod_image.py", "windows_memory_errors.py", "image_gen_preflight.py",
            "ollama_client.py", "ai_label.py", "text_removal.py", "facebook_api.py",
            "enhanced_news_diversity.py", "news_fetcher.py", "reddit_news_fetcher.py", "google_news_fetcher.py", "reputed_rss_fetcher.py",
            "minimal_overlay.py", "sensational_overlay.py", "vintage_newspaper.py",
            "design_config.py", "design_agent.py", "design_utils.py",
            "requirements.txt", ".env.example", "download_fonts.py",
            "assets", "fonts",
        }
        def _filter(ti):
            if not ti.isfile():
                return ti
            name = ti.name.replace("\\", "/")
            if "assets/" in name and not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                return None
            if "fonts/" in name and not name.lower().endswith((".ttf", ".otf", ".md")):
                return None
            return ti
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            for p in PROJECT_ROOT.iterdir():
                if p.name not in ALLOWED:
                    continue
                tar.add(p, arcname=p.name, filter=_filter)
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode()
        env_path = PROJECT_ROOT / ".env"
        env_lines = []
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith("RUNPOD_IMAGE_API_URL="):
                    continue
                env_lines.append(line)
        if not env_lines:
            env_lines = ["# Add GEMINI_API_KEY, PAGE_ID, PAGE_ACCESS_TOKEN, NEWS_API_KEY (optional)\n"]
        env_content = "\n".join(env_lines) + "\n"
        # Inner script: reads from stdin ---B64--- ... ---END---, ---ENV--- ... ---ENVEND---, then install and start
        inner_template = r"""set -e
workdir="/workspace/auto-posting-facebook"
mkdir -p "$workdir"
while IFS= read -r line; do [ "$line" = "---B64---" ] && break; done
while IFS= read -r line; do [ "$line" = "---END---" ] && break; printf '%%s\n' "$line"; done | base64 -d | tar xzf - -C "$workdir"
while IFS= read -r line; do [ "$line" = "---ENV---" ] && break; done
while IFS= read -r line; do [ "$line" = "---ENVEND---" ] && break; printf '%%s\n' "$line"; done > "$workdir/.env"
cd "$workdir" && python3 -m venv .venv && . .venv/bin/activate && pip install -q --upgrade pip && pip install -q -r requirements.txt && pip install -q git+https://github.com/huggingface/diffusers && pip install -q --force-reinstall 'huggingface-hub>=0.24.0,<1.0' && pip install -q 'transformers>=4.52.0'
pkill -f 'start_runpod|run_continuous_posts' 2>/dev/null || true
sleep 2
printf '#!/bin/bash\ncd "%s" || exit 1\n. .venv/bin/activate\nexport RUNPOD=1\nexec python -u start_runpod.py >> runpod.log 2>&1\n' "$workdir" > "$workdir/start.sh" && chmod +x "$workdir/start.sh"
nohup setsid bash "$workdir/start.sh" </dev/null &
echo "Deploy done. Pipeline started in background. SSH in and run: cd \$workdir && . .venv/bin/activate && RUNPOD=1 python -u start_runpod.py"
"""
        # Only the printf for start.sh needs workdir substituted
        inner = inner_template % (workdir,)
        # Outer script: skip until ---SCRIPT---, write inner to /tmp/deploy.sh until ---SCRIPTEND---, then run it
        outer = r"""set -e
while IFS= read -r line; do [ "$line" = "---SCRIPT---" ] && break; done
while IFS= read -r line; do [ "$line" = "---SCRIPTEND---" ] && break; printf '%%s\n' "$line"; done > /tmp/deploy.sh
bash /tmp/deploy.sh
"""
        payload = "---SCRIPT---\n" + inner + "\n---SCRIPTEND---\n---B64---\n" + b64 + "\n---END---\n---ENV---\n" + env_content + "\n---ENVEND---\n"
        # Use -T when piping stdin (no PTY); deploy completes without interactive shell
        args = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15"]
        if use_direct_tcp:
            args.extend(["-p", ssh_port])
        args.extend([ssh_target, "bash -s"])
        print("Running full deploy in one SSH session, then dropping into shell...")
        r = subprocess.run(args, input=outer + payload, timeout=900, text=True)
        return r.returncode if r.returncode != 0 else 0
    elif single_conn and git_url:
        print("RUNPOD_SINGLE_CONNECTION=1 is not supported with GIT_CLONE_URL; use normal deploy or unset GIT_CLONE_URL.")
        return 1

    print("1/5 Creating directory on RunPod...")
    ssh(f"mkdir -p {workdir}")

    if git_url:
        print("2/5 Cloning project from git...")
        ssh(f"cd {workdir} && git clone {git_url} . 2>/dev/null || (rm -rf ./* ./.??* 2>/dev/null; git clone {git_url} .)")
    else:
        print("2/5 Building and uploading project tarball...")
        # Only files/dirs required for RunPod workflow: news -> caption -> image (Z-Image) -> overlay -> post
        ALLOWED = {
            "run_continuous_posts.py", "start_runpod.py", "config.py", "content_generator.py", "runpod_image.py", "windows_memory_errors.py", "image_gen_preflight.py",
            "ollama_client.py", "ai_label.py", "text_removal.py", "facebook_api.py",
            "enhanced_news_diversity.py", "news_fetcher.py", "reddit_news_fetcher.py", "google_news_fetcher.py", "reputed_rss_fetcher.py",
            "minimal_overlay.py", "sensational_overlay.py", "vintage_newspaper.py",
            "design_config.py", "design_agent.py", "design_utils.py",
            "requirements.txt", ".env.example", "download_fonts.py",
            "assets", "fonts",
        }

        def _filter(ti):
            # Allow all directories; inside assets/ and fonts/ only include expected file types
            if not ti.isfile():
                return ti
            name = ti.name.replace("\\", "/")
            if "assets/" in name and not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                return None
            if "fonts/" in name and not name.lower().endswith((".ttf", ".otf", ".md")):
                return None
            return ti

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            for p in PROJECT_ROOT.iterdir():
                if p.name not in ALLOWED:
                    continue
                tar.add(p, arcname=p.name, filter=_filter)
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode()
        # Chunk the payload; pass via stdin to avoid Windows command-line length limits and quoting issues
        chunk_size = 6000
        total_chunks = (len(b64) + chunk_size - 1) // chunk_size
        for idx, i in enumerate(range(0, len(b64), chunk_size), start=1):
            print(f"  Uploading chunk {idx}/{total_chunks}...", flush=True)
            chunk = b64[i:i+chunk_size]
            ssh("cat >> /tmp/proj_b64.txt", stdin=chunk, timeout=120)
        print("  Extracting on RunPod...", flush=True)
        ssh(f"base64 -d /tmp/proj_b64.txt | tar xzf - -C {workdir} && rm -f /tmp/proj_b64.txt", timeout=120)

    print("3/5 Uploading .env (without RUNPOD_IMAGE_API_URL for full-pod mode)...")
    env_path = PROJECT_ROOT / ".env"
    env_lines = []
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("RUNPOD_IMAGE_API_URL="):
                continue
            env_lines.append(line)
    if not env_lines:
        env_lines = ["# Add GEMINI_API_KEY, PAGE_ID, PAGE_ACCESS_TOKEN, NEWS_API_KEY (optional)\n"]
    env_content = "\n".join(env_lines) + "\n"
    env_ssh = ["ssh", "-T", "-i", key_path, "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=15"]
    if use_direct_tcp:
        env_ssh.extend(["-p", ssh_port])
    env_ssh.extend([ssh_target, f"cat > {workdir}/.env"])
    r = subprocess.run(env_ssh, input=env_content.encode(), timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        print("Warning: .env upload failed; create .env on the pod manually.")

    print("4/5 Installing dependencies on RunPod (venv + pip)...")
    install_cmd = (
        f"cd {workdir} && python3 -m venv .venv && source .venv/bin/activate && "
        "pip install -q --upgrade pip && pip install -q -r requirements.txt && "
        "pip install -q git+https://github.com/huggingface/diffusers && "
        "pip install -q --force-reinstall 'huggingface-hub>=0.24.0,<1.0' && "
        "pip install -q 'transformers>=4.52.0'"
    )
    ssh(install_cmd, timeout=600)

    print("5/5 Stopping any existing pipeline and starting new one (RUNPOD=1)...")
    # Kill existing pipeline so the new code runs (otherwise the old process keeps running)
    ssh(f"pkill -f 'start_runpod|run_continuous_posts' 2>/dev/null || true; sleep 2", timeout=15)
    # Write start script via stdin so it runs in correct dir and survives SSH disconnect
    start_sh = f"""#!/bin/bash
cd {workdir} || exit 1
source .venv/bin/activate
export RUNPOD=1
echo "[start.sh] started at $(date)" >> runpod.log
exec python -u start_runpod.py >> runpod.log 2>&1
"""
    ssh(f"cat > {workdir}/start.sh && chmod +x {workdir}/start.sh", stdin=start_sh)
    # Start pipeline in background (setsid so it survives SSH disconnect)
    ssh(f"cd {workdir} && nohup setsid bash start.sh </dev/null &", timeout=15)

    ssh_connect = "ssh -t -i \"{}\" ".format(key_path) + ("-p {} ".format(ssh_port) if use_direct_tcp else "") + ssh_target
    print("")
    print("Done. Pipeline started on RunPod (news -> caption -> image on GPU -> overlay -> post).")
    if not use_direct_tcp:
        print("If the Pod was migrated, update RUNPOD_SSH_USER in .env from the Connect tab and redeploy.")
        print("If you SSH in and /workspace/auto-posting-facebook is missing, RunPod may be routing you to a different container. Use Direct TCP (RUNPOD_SSH_HOST + RUNPOD_SSH_PORT in .env, add your key in RunPod account settings) and redeploy so you land in the same container.")
    print("")
    print("Verify (use -t for interactive so tail -f works):")
    print("  {} \"tail -f {}/runpod.log\"".format(ssh_connect, workdir))
    print("To stop:  {} \"pkill -f run_continuous_posts\"".format(ssh_connect.replace(" -t", "")))
    print("")
    print("If the process exits, SSH in and run manually to see the error:")
    print("  {}".format(ssh_connect))
    print("  Then:  cd {} && source .venv/bin/activate && RUNPOD=1 python -u start_runpod.py".format(workdir))
    return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
