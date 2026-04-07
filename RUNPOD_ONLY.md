# Run everything on RunPod GPU only

Use **one RunPod pod** for the full pipeline. No VPS, no split setup, no image API URL.

**On the pod:** news → caption → image (Z-Image-Turbo on GPU) → overlay → post to Facebook.

---

## One-command setup from your PC (do everything)

From the project folder:

```powershell
python deploy_and_run_runpod.py
```

- **If you already have a pod:** set `RUNPOD_SSH_USER` in `.env` (from the pod’s **Connect** tab — use the *current* SSH user; it can change after a migration). The script will upload the project, install deps, and start the pipeline. No manual SSH needed.
- **If you don’t have a pod:** set `RUNPOD_API_KEY` in `.env` (from RunPod → Settings → API Keys) and add your SSH public key in RunPod account settings. The script will create a GPU pod, wait until it’s running, then do the same setup. If you have [runpodctl](https://github.com/runpod/runpodctl) installed, it will get the SSH user automatically; otherwise it will ask you to copy `RUNPOD_SSH_USER` from the Connect tab and run again.

Either way, the script: creates the project dir on the pod, uploads the project (tarball or `GIT_CLONE_URL`), uploads `.env` (no `RUNPOD_IMAGE_API_URL`), installs dependencies, and starts `run_continuous_posts.py` with `RUNPOD=1`. For deploy-only on an existing pod you can still run `python setup_runpod_full.py`.

---

## Manual setup (on the pod)

### 1. Deploy a pod

- [Deploy RTX 2000 Ada + PyTorch](https://console.runpod.io/deploy?type=GPU&gpu=RTX+2000+Ada&count=1&template=runpod-torch-v240)
- **Recommended image** (when choosing a template or using API): `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` — PyTorch 2.4, Python 3.11, CUDA 12.4; matches our Z-Image-Turbo / diffusers stack.
- Add your **SSH public key** in the pod **Connect** tab
- Note the **SSH** command (e.g. `ssh USER@ssh.runpod.io -i ~/.ssh/id_ed25519`). For real SSH (SCP/IDE), see [RunPod: True SSH](https://www.runpod.io/blog/how-to-achieve-true-ssh-in-runpod).

---

## 2. On the pod: clone, venv, install

```bash
cd /workspace
git clone https://github.com/YOUR_USERNAME/auto-posting-facebook.git
cd auto-posting-facebook

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If the template has no PyTorch/CUDA:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

---

## 3. On the pod: configure .env

```bash
cp .env.example .env
nano .env
```

Set (do **not** set `RUNPOD_IMAGE_API_URL`):

- `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey)
- `PAGE_ID` — Facebook Page ID
- `PAGE_ACCESS_TOKEN` — Facebook Page token
- `NEWS_API_KEY` — optional ([newsdata.io](https://newsdata.io/))

---

## 4. On the pod: run

**One post (test):**
```bash
export RUNPOD=1
python run_one_cycle.py
```

**24/7:**
```bash
export RUNPOD=1
nohup python run_continuous_posts.py > runpod.log 2>&1 &
tail -f runpod.log
```

**Cron (e.g. every 6 hours):**
```bash
crontab -e
# add:
0 */6 * * * cd /workspace/auto-posting-facebook && RUNPOD=1 .venv/bin/python run_one_cycle.py >> /workspace/runpod.log 2>&1
```

---

## Same container every time (avoid “directory not found”)

The **proxy** (`USER@ssh.runpod.io`) can send each SSH connection to a **different** container. So the deploy may finish on container A, but when you run `ssh USER@ssh.runpod.io` you sometimes land on container B where `/workspace/auto-posting-facebook` doesn’t exist.

**Fix: use Direct TCP** so every connection hits the same container:

1. In the RunPod **Connect** tab, copy the **Direct TCP** address (e.g. `root@194.26.196.139 -p 27090`).
2. In `.env` set:
   ```env
   RUNPOD_SSH_HOST=194.26.196.139
   RUNPOD_SSH_PORT=27090
   ```
   (Use your actual IP and port.)
3. In RunPod **account** settings (not the pod), add your **SSH public key**. Direct TCP uses that key; the pod may need a restart for it to apply.
4. Deploy from your PC:
   ```powershell
   python setup_runpod_full.py
   ```
5. SSH in with the same host/port:
   ```powershell
   ssh -i $env:USERPROFILE\.ssh\id_ed25519 -p 27090 root@194.26.196.139
   ```
   You’ll be on the same container that received the deploy.

---

## Bootstrap in the container you’re in (no Direct TCP)

If you’re already in a shell where `/workspace/auto-posting-facebook` is missing and you don’t want to switch to Direct TCP, you can install the project **in this container** (e.g. from a public Git repo).

**If the project is on GitHub**, paste this in your RunPod shell (replace the URL with your repo):

```bash
cd /workspace && git clone https://github.com/YOUR_USERNAME/auto-posting-facebook.git && cd auto-posting-facebook && python3 -m venv .venv && . .venv/bin/activate && pip install -q --upgrade pip && pip install -q -r requirements.txt && pip install -q git+https://github.com/huggingface/diffusers
```

Then create `.env` (e.g. `cp .env.example .env` and edit with your keys) and run:

```bash
export RUNPOD=1 && python -u start_runpod.py
```

If you don’t have a public repo, use **Direct TCP** above so deploy and SSH hit the same container.

---

## Pod migration (new Pod ID / SSH user / URLs)

RunPod can **migrate** your Pod to another machine (e.g. when the GPU is no longer available on the current host). Migration gives you a **new Pod ID**, new IP/URLs, and a **new SSH user** — so anything hardcoded (old Pod ID, proxy URL, or SSH host string) will break.

**What to do:**

1. **Refresh connection details**  
   Open the Pod in the [RunPod Console](https://console.runpod.io/), go to the **Connect** tab, and copy the **current** SSH command. The username (e.g. `xxxxx-64411fd7`) is your new `RUNPOD_SSH_USER`. Update `.env` with this value and redeploy:
   ```powershell
   # In .env set:
   RUNPOD_SSH_USER=<current-ssh-user-from-Connect-tab>
   ```
   Then run `python deploy_and_run_runpod.py` again.

2. **Use the current SSH user for logs**  
   If you use:
   ```bash
   ssh -t -i "C:\Users\user\.ssh\id_ed25519" <pod-ssh-user>@ssh.runpod.io "tail -f /workspace/auto-posting-facebook/runpod.log"
   ```
   make sure `<pod-ssh-user>` is the one shown in the Console for this Pod (not an old one from before migration).

3. **If the Pod shows 0 GPUs / migration prompt**  
   - Wait and retry later (GPU may free up), or  
   - Start Pod with CPUs only for temporary access, or  
   - Accept migration (you get a new Pod ID and must update `RUNPOD_SSH_USER` and redeploy).

**To avoid migration pain:** attach a **Network Volume** to the Pod and put project data (or `/workspace`) on it so it persists across migration/termination. See [RunPod Network Volumes](https://docs.runpod.io/). After migration, reattach the same volume to the new Pod and redeploy; your data stays.

---

## Pipeline exits after deploy (see the error)

If the deploy finishes but the pipeline process doesn’t stay running:

1. **SSH in with a TTY** (required so `tail -f` works):
   ```bash
   ssh -t -i "C:\Users\user\.ssh\id_ed25519" YOUR_RUNPOD_SSH_USER@ssh.runpod.io
   ```
2. **Run the pipeline in the foreground** to see the traceback or Facebook/env error:
   ```bash
   cd /workspace/auto-posting-facebook && source .venv/bin/activate && export RUNPOD=1 && python -u start_runpod.py
   ```
3. **Fix what it reports:** e.g. add `PAGE_ID` and `PAGE_ACCESS_TOKEN` (or `FACEBOOK_PAGE_ID` and `FACEBOOK_ACCESS_TOKEN`) to `.env` on your PC and redeploy, or fix the reported import/API error.
4. **Start in background** from the pod:
   ```bash
   cd /workspace/auto-posting-facebook && nohup bash start.sh </dev/null >> runpod.log 2>&1 &
   tail -f runpod.log
   ```

---

## If Z-Image-Turbo doesn't load on RunPod

1. **Use the public model**  
   Default is `Tongyi-MAI/Z-Image-Turbo`. If you set `Z_IMAGE_TURBO_MODEL=aiorbust/z-image-turbo` in `.env`, that repo may be private (401); remove it or log in with `huggingface-cli login` on the pod.

2. **Install diffusers from source**  
   Z-Image needs `ZImagePipeline`, which is in the latest diffusers. On the pod run:
   ```bash
   pip install git+https://github.com/huggingface/diffusers
   ```
   The one-command setup (`deploy_and_run_runpod.py`) does this automatically.

3. **Check the real error**  
   Run one cycle and read the traceback:
   ```bash
   RUNPOD=1 python run_one_cycle.py
   ```
   You’ll see whether it’s 401/404 (model/repo), `ZImagePipeline` missing (install diffusers from git), or OOM (try smaller image size or CPU offload).

---

You only need the RunPod GPU; everything else runs on the same pod.
